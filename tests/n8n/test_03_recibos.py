"""SMTP/IMAP → PF-03 → API → PF-00 → PF-02, en servicios locales.

PF_TEST_PF02_PATH permite probar la exportación de la PR dependiente antes de su
merge. PF_TEST_OPENROUTER=1 conserva el proveedor real; en otro caso usa el doble.
Cada corrida conserva su propia base auxiliar y su base de tienda como evidencia.
"""
from email import policy
from email.parser import BytesParser
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import uuid

from lab import (ROOT, STATE, SECRET, login, prepare_credentials, request,
                 install, execution_data)
from imap_lab import imap_flow, deliver
from test_08 import activate, executions


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def api(path):
    return request(path, base='http://127.0.0.1:18000', headers={'X-API-Key': SECRET})


def mail_list():
    return request('/api/v1/messages', base='http://127.0.0.1:18025')['messages']


def wait_runs(flow, previous, count):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        fresh = [r for r in executions(flow['id']) if r['id'] not in previous]
        if len(fresh) >= count and all(r['status'] in ('success', 'error', 'crashed') for r in fresh):
            assert len(fresh) == count, [(r['id'], r['status']) for r in fresh]
            return fresh
        time.sleep(.3)
    raise AssertionError('No terminó la entrega del evento a PF-02')


def ready_store():
    for attempt in range(100):
        try:
            return api('/api/apartados')
        except Exception:
            time.sleep(.3)
    raise AssertionError('La tienda de pruebas no arrancó')


def main():
    source = Path(os.environ.get('PF_TEST_PF02_PATH', ROOT / 'workflows/02-recibo-abono.json'))
    assert source.is_file(), 'Falta la exportación PF-02; indicar PF_TEST_PF02_PATH'
    live = os.environ.get('PF_TEST_OPENROUTER') == '1'
    login()
    assert not [w for w in request('/rest/workflows')['data'] if w.get('active')], 'El laboratorio está ocupado'
    credentials = prepare_credentials()
    if live:
        assert 'PF · Modelo extracción' in credentials, 'Falta la credencial nativa OpenRouter'
    token = uuid.uuid4().hex
    database = 'qa_recibos_' + token
    directory = STATE / database
    directory.mkdir()
    compose = ['docker', 'compose', '--env-file', str(ROOT / 'tests/n8n/.env.local'),
               '-f', str(ROOT / 'tests/n8n/compose.yml')]

    def sql(query, db=database):
        result = subprocess.run(compose + ['exec', '-T', 'registro', 'psql', '-U', 'n8n',
                                '-d', db, '-At', '-v', 'ON_ERROR_STOP=1', '-c', query],
                                check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def config(key, value):
        sql('INSERT INTO pf_config VALUES(' + quote(key) + ',' + quote(value) +
            ') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor')

    # Solo metadatos necesarios para restaurar el servicio; no se imprimen secretos.
    container_id = subprocess.check_output(compose + ['ps', '-q', 'tienda'], text=True).strip()
    container = json.loads(subprocess.check_output(['docker', 'inspect', container_id]))[0]
    original_env = dict(v.split('=', 1) for v in container['Config']['Env'] if '=' in v)
    original_mounts = [m['Source'] + ':' + m['Destination'] + (':ro' if not m['RW'] else '')
                       for m in container['Mounts'] if m['Destination'] in ('/srv/backend', '/srv/frontend')]
    restore_file = directory / 'restaurar-tienda.json'
    restore_file.write_text(json.dumps({'services': {'tienda': {
        'environment': {k: original_env[k] for k in ('DB_PATH', 'N8N_WEBHOOK_URL', 'SEED')},
        'volumes': original_mounts,
    }}}))
    test_file = directory / 'tienda.json'
    test_file.write_text(json.dumps({'services': {'tienda': {
        'environment': {'DB_PATH': '/data/' + database + '.db',
                        'N8N_WEBHOOK_URL': 'http://n8n:5678/webhook/tienda', 'SEED': '1'},
        'volumes': [str(ROOT / 'backend') + ':/srv/backend:ro',
                    str(ROOT / 'frontend') + ':/srv/frontend:ro'],
    }}}))
    before_store = {resource: api('/api/' + resource) for resource in ('apartados', 'abonos', 'ventas', 'vales')}
    sql('CREATE DATABASE ' + database, db='automatizaciones')
    sql((ROOT / 'infra/registro.sql').read_text())
    sql((ROOT / 'infra/03-pagos.sql').read_text())
    config('CUENTA_BUZON', database)
    postgres = request('/rest/credentials', {
        'name': 'PF · Registro auxiliar · ' + database, 'type': 'postgres',
        'data': {'host': 'registro', 'port': 5432, 'database': database,
                 'user': 'n8n', 'password': SECRET, 'ssl': 'disable', 'sshTunnel': False},
    })['data']

    def isolated_source(path):
        flow = json.loads(Path(path).read_text())
        for node in flow['nodes']:
            if 'postgres' in node.get('credentials', {}):
                node['credentials']['postgres'] = {'id': postgres['id'], 'name': postgres['name']}
        target = directory / Path(path).name
        target.write_text(json.dumps(flow, ensure_ascii=False))
        return target

    flows, evidence = [], []
    report = {'modelo': 'OpenRouter real' if live else 'doble IA', 'registro': database,
              'pf02_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'casos': evidence, 'restaurado': False}
    report_file = directory / 'evidencia.json'
    changed_store = False
    try:
        error = install(isolated_source(ROOT / 'workflows/08-errores.json'))
        flows.append(error)
        activate(error)
        child = install(isolated_source(source), error['id'])
        flows.append(child)
        activate(child)
        config('PF02_WORKFLOW_ID', child['id'])
        router = install(isolated_source(ROOT / 'workflows/00-entrada-eventos.json'), error['id'])
        flows.append(router)
        activate(router)
        flow = imap_flow(isolated_source(ROOT / 'workflows/03-abonos-distancia.json'),
                         error['id'], model_mock=not live)
        flows.append(flow)
        changed_store = True
        subprocess.run(compose + ['-f', str(test_file), 'up', '-d', 'tienda'],
                       check=True, capture_output=True)
        ready_store()
        fixtures = [
            (1, 'CARMEN RUIZ GARCIA', 10, 'zuecos', 'bizum', None, 1),
            (2, 'JORGE M.', 20, 'apartado 2 bota', 'bizum', 2, 2),
            (3, 'LUCIA GOMEZ PEREZ', 12, 'Liquidar mocasines', 'transferencia', None, 3),
            (4, 'LAURA O.', 15, 'deportivas', 'bizum', None, None),
            (5, 'ROMERO D.', 10, None, 'bizum', None, None),
            (6, 'PAULA RAMOS LEON', 20, 'zapatillas running perdón por el retraso', 'bizum', None, None),
            (7, 'ANTONIO FERNANDEZ SOTO', 25, 'botas', 'transferencia', None, None),
            (8, None, None, None, None, None, None),
            (9, 'SILVIA CORTES', 5, 'abono sandalias', 'bizum', None, 24),
        ]
        first_mail = None
        for f in fixtures:
            file = next((ROOT / 'data/correos').glob(f'{f[0]:02d}_*.eml'))
            raw = BytesParser(policy=policy.default).parsebytes(file.read_bytes())
            payload = {'subject': str(raw['subject']),
                       'textPlain': raw.get_payload(decode=True).decode(raw.get_content_charset() or 'utf-8'),
                       'metadata': {'message-id': '<' + file.stem + '@pruebas.example.test>'}}
            if first_mail is None:
                first_mail = payload
            if not live:
                extraction = dict(zip(['es_pago', 'ordenante', 'importe', 'concepto', 'medio', 'apartado_id'],
                                      [f[0] != 8, *f[1:6]]))
                request('/__fixture', {'extraction': extraction}, base='http://127.0.0.1:18080')
            before = api('/api/abonos')
            prior_messages = {m['ID'] for m in mail_list()}
            prior_child = {r['id'] for r in executions(child['id'])}
            prior_router = {r['id'] for r in executions(router['id'])}
            run = deliver(flow, payload)
            assert run['status'] == 'success', {'caso': f[0], 'ejecucion': run['id'],
                'paso': execution_data(run['id']).get('resultData', {}).get('lastNodeExecuted')}
            new = [a for a in api('/api/abonos') if a['id'] not in {b['id'] for b in before}]
            row = {'caso': f'F03-{f[0]:02d}', 'pf03': run['id'], 'imap': run['imap_execution']}
            if f[6]:
                assert len(new) == 1 and new[0]['apartado_id'] == f[6] and new[0]['importe'] == f[2] and new[0]['forma_pago'] == f[4], new
                received = wait_runs(child, prior_child, 1)[0]
                routed = wait_runs(router, prior_router, 1)[0]
                assert received['status'] == routed['status'] == 'success', {'pf02': received, 'pf00': routed}
                row.update(pf00=routed['id'], pf02=received['id'])
                detail = api('/api/apartados/' + str(f[6]))
                if f[0] == 3:
                    assert detail['estado'] == 'liquidado' and detail['pendiente'] == 0
            else:
                assert not new
            messages = [m for m in mail_list() if m['ID'] not in prior_messages]
            assert len(messages) == (0 if f[0] == 8 else 1), {'caso': f[0], 'correos': len(messages)}
            if f[6]:
                message = request('/api/v1/message/' + messages[0]['ID'], base='http://127.0.0.1:18025')
                assert [r['Address'] for r in messages[0]['To']] == [detail['email']]
                euros = lambda n: f'{n:.2f}'.replace('.', ',') + ' €'
                for label, amount in [('Importe de este abono', f[2]), ('Total abonado', detail['abonado']), ('Pendiente', detail['pendiente'])]:
                    assert f'{label}: {euros(amount)}' in message['Text'], label
                assert ('recogerlo' in message['Text']) == (detail['estado'] == 'liquidado')
                receipt = f"abono.registrado:{detail['id']}:{round(detail['abonado'] * 100)}:{round(f[2] * 100)}"
                assert sql('SELECT estado FROM pf_registro WHERE clave=' + quote(receipt)) == 'confirmado'
            if f[0] != 8:
                key = 'correo:' + database + ':' + payload['metadata']['message-id']
                saved = json.loads(sql("SELECT jsonb_build_object('estado',estado,'documento',documento) FROM pf_registro WHERE clave=" + quote(key)))
                assert saved['estado'] == ('confirmado' if f[6] else 'revision')
                if not f[6]:
                    expected = {4: 'exceso_sobre_pendiente_del_candidato', 5: 'identidad_insuficiente',
                                6: 'fuera_de_plazo', 7: 'cliente_desconocido'}[f[0]]
                    assert saved['documento']['motivo'] == expected and saved['documento']['aviso_confirmado'] is True
                    assert [r['Address'] for r in messages[0]['To']] == ['marisa@example.test']
            row.update(abonos_nuevos=len(new), correos=len(messages), resultado='PASS')
            evidence.append(row)
            report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if live:
                time.sleep(3)
        before = api('/api/abonos')
        prior_messages = {m['ID'] for m in mail_list()}
        prior_child = {r['id'] for r in executions(child['id'])}
        if not live:
            request('/__fixture', {'extraction': {'es_pago': True, 'ordenante': fixtures[0][1],
                    'importe': 10, 'concepto': 'zuecos', 'medio': 'bizum', 'apartado_id': None}},
                    base='http://127.0.0.1:18080')
        run = deliver(flow, first_mail)
        assert run['status'] == 'success' and api('/api/abonos') == before
        assert {m['ID'] for m in mail_list()} == prior_messages
        assert {r['id'] for r in executions(child['id'])} == prior_child
        row = {'caso': 'F03-10 repetición', 'pf03': run['id'], 'imap': run['imap_execution'],
               'abonos_nuevos': 0, 'recibos_nuevos': 0, 'resultado': 'PASS'}
        evidence.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        report['resultado'] = 'PASS'
    except Exception as error:
        report['resultado'] = 'FAIL'
        report['error_tipo'] = type(error).__name__
        raise
    finally:
        cleanup_errors = []
        if changed_store:
            try:
                subprocess.run(compose + ['-f', str(restore_file), 'up', '-d', 'tienda'],
                               check=True, capture_output=True)
                ready_store()
                assert {resource: api('/api/' + resource) for resource in before_store} == before_store
            except Exception as error:
                cleanup_errors.append(type(error).__name__)
        for flow in reversed(flows):
            try:
                request('/rest/workflows/' + flow['id'] + '/deactivate', {})
            except Exception as error:
                cleanup_errors.append(type(error).__name__)
        report['restaurado'] = not cleanup_errors
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps({'evidencia': str(report_file), 'restaurado': report['restaurado']}), flush=True)
        assert not cleanup_errors, cleanup_errors


if __name__ == '__main__':
    main()
