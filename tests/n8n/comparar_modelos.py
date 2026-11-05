"""Compara extracción mínima con dos modelos gratuitos, sin nodos de cobro.

Usa los nueve correos ficticios originales, el mismo prompt/esquema/parámetros y
la credencial nativa de n8n. Conserva fallos y métricas; no modifica PF-03.
"""
from email import policy
from email.parser import BytesParser
import copy
import hashlib
import json
import subprocess
import time
import unicodedata
import uuid

from lab import ROOT, STATE, SECRET, client, request, prepare_credentials, install, execution_data
from test_08 import activate, executions, finished, webhook

MODELS = ['dots-studio/dots-3-note-preview:free', 'liquid/lfm-2.5-2.6b:free']
EXPECTED = [
    (True, 'CARMEN RUIZ GARCIA', 10, 'zuecos', 'bizum', None),
    (True, 'JORGE M.', 20, 'apartado 2 bota', 'bizum', 2),
    (True, 'LUCIA GOMEZ PEREZ', 12, 'Liquidar mocasines', 'transferencia', None),
    (True, 'LAURA O.', 15, 'deportivas', 'bizum', None),
    (True, 'ROMERO D.', 10, None, 'bizum', None),
    (True, 'PAULA RAMOS LEON', 20, 'zapatillas running perdón por el retraso', 'bizum', None),
    (True, 'ANTONIO FERNANDEZ SOTO', 25, 'botas', 'transferencia', None),
    (False, None, None, None, None, None),
    (True, 'SILVIA CORTES', 5, 'abono sandalias', 'bizum', None),
]
FIELDS = ['es_pago', 'ordenante', 'importe', 'concepto', 'medio', 'apartado_id']


def norm(value):
    return ''.join(c.lower() for c in unicodedata.normalize('NFD', str(value or ''))
                   if c.isalnum())


def main():
    # curl usa el almacén de certificados del sistema, también en Python de macOS.
    response = subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                                       '--max-time', '30', 'https://openrouter.ai/api/v1/models'])
    catalog = {m['id']: m for m in json.loads(response)['data']}
    for model in MODELS:
        info = catalog[model]
        assert all(float(info['pricing'][key]) == 0 for key in ('prompt', 'completion'))
        assert 'response_format' in info['supported_parameters']
    original_open = client.open

    def admin(req, *args, **kwargs):
        if req.full_url.startswith('http://127.0.0.1:15678/rest/'):
            kwargs['timeout'] = 180
        return original_open(req, *args, **kwargs)

    client.open = admin
    request('/rest/login', {'emailOrLdapLoginId': 'qa@example.test', 'password': SECRET + 'Aa1!'})
    assert not any(w.get('active') for w in request('/rest/workflows')['data']), 'Laboratorio ocupado'
    assert 'PF · Modelo extracción' in prepare_credentials()
    source_path = ROOT / 'workflows/03-abonos-distancia.json'
    source = json.loads(source_path.read_text())
    rows, flows = [], []
    report = {'fecha': time.strftime('%Y-%m-%d'), 'modelos': MODELS,
              'fuente_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'casos': rows, 'coste_catalogo': 0, 'flujos_desactivados': False}
    result_path = STATE / ('comparativa-' + uuid.uuid4().hex + '.json')
    try:
        for model in MODELS:
            trigger = webhook('Recibir correo ficticio', 'qa-modelo-' + uuid.uuid4().hex)
            unwrap = {'id': str(uuid.uuid4()), 'name': 'Preparar extracción',
                      'type': 'n8n-nodes-base.code', 'typeVersion': 2, 'position': [200, 0],
                      'parameters': {'jsCode': 'return [{json:$input.first().json.body}];'}}
            nodes = [trigger, unwrap] + [copy.deepcopy(next(n for n in source['nodes'] if n['name'] == name))
                    for name in ('Preparar petición IA', 'Extraer pago')]
            code = nodes[2]['parameters']['jsCode']
            assert code.count('model:"openrouter/free"') == 1
            nodes[2]['parameters']['jsCode'] = code.replace('model:"openrouter/free"', 'model:' + json.dumps(model))
            flow = {'name': 'Prueba de extracción · ' + model, 'nodes': nodes,
                    'connections': {a['name']: {'main': [[{'node': b['name'], 'type': 'main', 'index': 0}]]}
                                    for a, b in zip(nodes, nodes[1:])},
                    'settings': {'executionOrder': 'v1', 'timezone': 'Europe/Madrid'},
                    'active': False, 'pinData': {}}
            path = STATE / ('modelo-' + uuid.uuid4().hex + '.json')
            path.write_text(json.dumps(flow, ensure_ascii=False))
            installed = install(path); flows.append(installed); activate(installed)
            for number, expected in enumerate(EXPECTED, 1):
                file = next((ROOT / 'data/correos').glob(f'{number:02d}_*.eml'))
                message = BytesParser(policy=policy.default).parsebytes(file.read_bytes())
                payload = {'subject': str(message['subject']),
                           'text': message.get_payload(decode=True).decode(message.get_content_charset() or 'utf-8')}
                previous = [r['id'] for r in executions(installed['id'])]
                request('/webhook/' + trigger['parameters']['path'], payload)
                run = finished(installed['id'], previous, timeout=150)
                data = execution_data(run['id'])['resultData']
                node = data.get('runData', {}).get('Extraer pago', [{}])[0]
                row = {'modelo': model, 'caso': f'F03-{number:02d}', 'ejecucion': run['id'],
                       'latencia_modelo_ms': node.get('executionTime'), 'resultado': 'FAIL'}
                if run['status'] == 'success':
                    response = node['data']['main'][0][0]['json']
                    row['modelo_reportado'] = response.get('model')
                    row['coste_reportado'] = response.get('usage', {}).get('cost')
                    row['tokens'] = response.get('usage', {}).get('total_tokens')
                    try:
                        parsed = json.loads(response['choices'][0]['message']['content'])
                        assert set(parsed) == set(FIELDS)
                        differences = [field for field, value in zip(FIELDS, expected)
                                       if (norm(parsed[field]) != norm(value) if field in ('ordenante', 'concepto')
                                           else type(parsed[field]) is not type(value) or parsed[field] != value)
                                       and not (field == 'importe' and isinstance(parsed[field], (int, float))
                                                and not isinstance(parsed[field], bool) and parsed[field] == value)]
                        row.update(campos_distintos=differences, resultado='PASS' if not differences else 'FAIL')
                    except (AssertionError, ValueError, TypeError, KeyError):
                        row['motivo'] = 'JSON o esquema inválido'
                else:
                    error = data.get('error', {})
                    row['motivo'] = 'Fallo técnico del proveedor; no es resultado de extracción'
                    row['codigo_http'] = str(error.get('httpCode', 'no indicado'))
                rows.append(row)
                result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
                print(json.dumps(row, ensure_ascii=False), flush=True)
                time.sleep(4)
            request('/rest/workflows/' + installed['id'] + '/deactivate', {})
        report['comparacion_completa'] = len(rows) == len(MODELS) * len(EXPECTED)
    finally:
        failures = []
        for flow in reversed(flows):
            try: request('/rest/workflows/' + flow['id'] + '/deactivate', {})
            except Exception as error: failures.append(type(error).__name__)
        report['flujos_desactivados'] = not failures
        result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        client.open = original_open
        print('Evidencia:', result_path, flush=True)
        assert not failures, failures


if __name__ == '__main__':
    main()
