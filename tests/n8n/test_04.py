"""PF-04 real y contrato de las cuatro rutas de PF-00, solo en el laboratorio."""
from pathlib import Path
import concurrent.futures
import copy
import json
import time
import uuid

from lab import (ROOT, STATE, SECRET, login, prepare_credentials, invoke, sql,
                 request, message_count, install, export, execution_data)
from test_08 import activate, executions

root = Path(__file__).resolve().parents[2]
login()
prepare_credentials()
flows = []
evidence = []
cases = json.loads((ROOT / 'data/pruebas/contratos.json').read_text())['cases']
sale_cases = [c for c in cases if c['flow'] == 'PF-04']
config_keys = ['PF01_WORKFLOW_ID', 'PF02_WORKFLOW_ID', 'PF04_WORKFLOW_ID',
               'PF06_WORKFLOW_ID', 'UMBRAL_VENTA_GRANDE']


def quoted(value):
    return "'" + str(value).replace("'", "''") + "'"


saved_config = json.loads(sql(
    "SELECT coalesce(jsonb_object_agg(clave,valor),'{}'::jsonb) FROM pf_config "
    "WHERE clave IN (" + ','.join(map(quoted, config_keys)) + ")"))


def config(key, value):
    if value is None:
        sql('DELETE FROM pf_config WHERE clave=' + quoted(key))
    else:
        sql('INSERT INTO pf_config VALUES(' + quoted(key) + ',' + quoted(value) +
            ') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor')


def messages():
    return request('/api/v1/messages', base='http://127.0.0.1:18025')['messages']


def mail_text(message):
    return request('/api/v1/message/' + message['ID'],
                   base='http://127.0.0.1:18025')['Text']


def ids(flow):
    return {e['id'] for e in executions(flow['id'])}


def wait_runs(flow, previous, count):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        runs = [e for e in executions(flow['id']) if e['id'] not in previous]
        if len(runs) >= count and all(e['status'] in ('success', 'error') for e in runs):
            assert len(runs) == count, 'Número inesperado de ejecuciones'
            return runs
        time.sleep(.3)
    raise AssertionError('No terminaron las ejecuciones esperadas')


def record(case, run=None, **details):
    row = {'caso': case, 'resultado': 'PASS', **details}
    if run:
        row['ejecucion_router'] = run['id']
    evidence.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)


def business_snapshot():
    return {resource: request('/api/' + resource, base='http://127.0.0.1:18000',
                             headers={'X-API-Key': SECRET})
            for resource in ('ventas', 'abonos', 'apartados', 'vales')}


def receiver(code):
    """Doble sin correo, API ni registro: devuelve íntegra su entrada."""
    trigger = {'id': str(uuid.uuid4()), 'name': 'Recibir prueba',
               'type': 'n8n-nodes-base.executeWorkflowTrigger', 'typeVersion': 1.1,
               'position': [0, 0], 'parameters': {'inputSource': 'passthrough'}}
    check = {'id': str(uuid.uuid4()), 'name': 'Observar contrato',
             'type': 'n8n-nodes-base.code', 'typeVersion': 2, 'position': [240, 0],
             'parameters': {'jsCode': 'return $input.all().map(i=>({json:{destino:' +
                            json.dumps(code) + ',recibido:i.json}}));'}}
    return request('/rest/workflows', {
        'name': code + ' · Receptor de prueba PF-00', 'nodes': [trigger, check],
        'connections': {'Recibir prueba': {'main': [[{
            'node': 'Observar contrato', 'type': 'main', 'index': 0}]]}},
        'settings': {'executionOrder': 'v1'}, 'active': False})['data']


try:
    error = install(root / 'workflows/08-errores.json')
    flows.append(error)
    activate(error)
    child = install(root / 'workflows/04-venta-grande.json', error['id'])
    flows.append(child)
    activate(child)
    router = install(root / 'workflows/00-entrada-eventos.json', error['id'])
    flows.append(router)
    activate(router)
    # El Webhook publicado tarda ocasionalmente más de un segundo en registrarse.
    time.sleep(2)
    config('PF04_WORKFLOW_ID', child['id'])
    sql("DELETE FROM pf_registro WHERE clave LIKE 'venta.registrada:91%'")
    business_before = business_snapshot()

    for case in sale_cases:
        threshold = case['input']['variables'].get('UMBRAL_VENTA_GRANDE')
        config('UMBRAL_VENTA_GRANDE', threshold)
        before = message_count()
        error_before = ids(error)
        run = invoke(router, 'tienda', case['input']['payload'])
        if threshold is None:
            assert run['status'] == 'error'
            handlers = wait_runs(error, error_before, 2)
            assert all(e['status'] == 'success' for e in handlers)
            assert message_count() == before + 2
            notices = [mail_text(m) for m in messages()[:2]]
            assert any('PF-04' in text and 'Validar venta y umbral' in text for text in notices)
            assert any('PF-00' in text for text in notices)
            assert all('Concepto: Venta demo' not in text for text in notices)
            assert sql("SELECT count(*) FROM pf_registro WHERE clave='venta.registrada:9103'") == '0'
            record(case['id'], run, avisos_error=2, avisos_venta=0,
                   ejecuciones_pf08=[h['id'] for h in handlers])
        else:
            assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
            assert message_count() == before + case['expected']['marisa_messages']
            if case['id'] == 'F04-01':
                text = mail_text(messages()[0])
                assert all(value in text for value in
                           ('Concepto: Venta demo', 'Importe: 100.01 EUR',
                            'Fecha: 2026-10-21', 'Medio: tarjeta'))
                assert sql("SELECT estado FROM pf_registro WHERE clave='venta.registrada:9101'") == 'confirmado'
            repeat = invoke(router, 'tienda', case['input']['payload'])
            assert repeat['status'] == 'success'
            assert message_count() == before + case['expected']['marisa_messages']
            record(case['id'], run, repeticion=repeat['id'],
                   avisos=case['expected']['marisa_messages'])

    config('UMBRAL_VENTA_GRANDE', 99)
    before = message_count()
    run = invoke(router, 'tienda', sale_cases[1]['input']['payload'])
    assert run['status'] == 'success' and message_count() == before + 1
    record('Cambio de variable sin editar nodos', run)
    payload = copy.deepcopy(sale_cases[0]['input']['payload'])
    payload['datos']['id'] = 9199
    before = message_count()
    previous = ids(router)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _: request('/webhook/tienda', payload), range(2)))
    runs = wait_runs(router, previous, 2)
    assert all(e['status'] == 'success' for e in runs) and message_count() == before + 1
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='venta.registrada:9199' AND estado='confirmado'") == '1'
    record('Dos eventos simultáneos, un aviso', ejecuciones_router=[r['id'] for r in runs])

    receivers = {}
    for code in ('PF-01', 'PF-02', 'PF-04', 'PF-06'):
        fixture = receiver(code)
        flows.append(fixture)
        activate(fixture)
        receivers[code] = fixture
        config(code.replace('-', '') + '_WORKFLOW_ID', fixture['id'])
    first = next(c for c in cases if c['id'] == 'F00-01')['input']['payload']
    abono = next(c for c in cases if c['id'] == 'F02-01')['input']['payload']
    vencido = copy.deepcopy(first['datos'])
    vencido.update(estado='vencido', fecha='2026-06-01', fecha_limite='2026-08-30')
    routes = [('F00-01', 'PF-01', first),
              ('F00-ruta-abono', 'PF-02', abono),
              ('F00-ruta-venta', 'PF-04', sale_cases[0]['input']['payload']),
              ('F00-ruta-vencido', 'PF-06', {'evento': 'apartado.vencido', 'datos': {
                  'apartado': vencido, 'vale': {'id': 9901, 'apartado_id': vencido['id'],
                                              'fecha': '2026-10-21', 'importe': 10}}})]
    for case_id, code, payload in routes:
        previous = {key: ids(flow) for key, flow in receivers.items()}
        before = message_count()
        run = invoke(router, 'tienda', payload)
        assert run['status'] == 'success'
        received = wait_runs(receivers[code], previous[code], 1)[0]
        assert received['status'] == 'success'
        data = execution_data(received['id'])['resultData']['runData']['Observar contrato'][0]['data']['main'][0]
        assert len(data) == 1
        assert data[0]['json'] == {'destino': code, 'recibido': {
            'body': payload, 'workflow_id': receivers[code]['id']}}
        for other, flow in receivers.items():
            if other != code:
                assert ids(flow) == previous[other], 'Se ejecutó un destino ajeno'
        assert message_count() == before
        record(case_id, run, destino=code, ejecucion_destino=received['id'], body_integro=True)

    # El contrato desconocido y una envoltura incompleta fallan antes de consumidores.
    unknown = next(c for c in cases if c['id'] == 'F00-02')['input']['payload']
    for case_id, payload in [('F00-02', unknown),
                             ('F00-datos-array', {'evento': 'apartado.creado', 'datos': []}),
                             ('F00-destino-ausente', first)]:
        if case_id == 'F00-destino-ausente':
            config('PF01_WORKFLOW_ID', None)
        before = message_count()
        error_before = ids(error)
        previous = {key: ids(flow) for key, flow in receivers.items()}
        run = invoke(router, 'tienda', payload)
        assert run['status'] == 'error'
        handler = wait_runs(error, error_before, 1)[0]
        assert handler['status'] == 'success' and message_count() == before + 1
        text = mail_text(messages()[0])
        assert 'PF-00' in text and 'Validar evento y destino' in text
        for code, flow in receivers.items():
            assert ids(flow) == previous[code]
        record(case_id, run, incidencias=1, consumidores=0, ejecucion_pf08=handler['id'])

    assert business_snapshot() == business_before, 'Las pruebas alteraron la tienda'
    export(child['id'], root / 'workflows/04-venta-grande.json')
    export(router['id'], root / 'workflows/00-entrada-eventos.json')
    export(error['id'], root / 'workflows/08-errores.json')
    (STATE / '04-evidencia.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
finally:
    for flow in reversed(flows):
        request('/rest/workflows/' + flow['id'] + '/deactivate', {})
    for key in config_keys:
        config(key, saved_config.get(key))
