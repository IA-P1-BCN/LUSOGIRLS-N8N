"""PF-01 real llamado por PF-00 real, solo en el laboratorio."""
from pathlib import Path
import json
import time

from lab import (ROOT, STATE, SECRET, login, prepare_credentials, invoke, sql,
                 request, message_count, install)
from test_08 import activate, executions

root = Path(__file__).resolve().parents[2]
login()
prepare_credentials()
flows = []
evidence = []
cases = {c['id']: c for c in json.loads(
    (ROOT / 'data/pruebas/contratos.json').read_text())['cases'] if c['flow'] == 'PF-01'}
config_keys = ['PF01_WORKFLOW_ID', 'API_BASE_URL']


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


def mail(message):
    return request('/api/v1/message/' + message['ID'], base='http://127.0.0.1:18025')


def recipients(message):
    return [r['Address'] for r in message['To']]


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


def estado(clave):
    return sql('SELECT estado FROM pf_registro WHERE clave=' + quoted(clave))


try:
    error = install(root / 'workflows/08-errores.json')
    flows.append(error)
    activate(error)
    child = install(root / 'workflows/01-confirmacion-apartado.json', error['id'])
    flows.append(child)
    activate(child)
    router = install(root / 'workflows/00-entrada-eventos.json', error['id'], retain_test_execution=True)
    flows.append(router)
    activate(router)
    # El Webhook publicado tarda ocasionalmente más de un segundo en registrarse.
    time.sleep(2)
    config('PF01_WORKFLOW_ID', child['id'])
    # Permisos explícitos de IDs ficticios; no concederlos en la tienda real.
    config('API_BASE_URL', 'http://simulador:8080')
    request('/__fixture', {'consentimientos': {'9001': True, '9011': True, '9013': True}}, base='http://127.0.0.1:18080')
    # Registro aislado del laboratorio: solo se limpian las claves ficticias de estos casos.
    sql("DELETE FROM pf_registro WHERE clave LIKE 'apartado.creado:90%'")
    business_before = business_snapshot()

    # F01-01: confirmación completa al cliente, cifras literales del payload.
    case = cases['F01-01']
    datos = case['input']['payload']['datos']
    before = message_count()
    child_before = ids(child)
    run = invoke(router, 'tienda', case['input']['payload'])
    assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
    sent = wait_runs(child, child_before, 1)[0]
    assert message_count() == before + case['expected']['customer_messages']
    last = messages()[0]
    assert recipients(last) == [datos['email']]
    text = mail(last)['Text']
    expected_lines = ('Modelo: Botin demo', 'Talla: 38', 'Precio: 89,90 €',
                      'Abonado: 10,00 €', 'Pendiente: 79,90 €', 'Fecha límite: 19/01/2027')
    assert all(line in text for line in expected_lines), text
    assert 'recogerlo' not in text
    assert estado('apartado.creado:9001') == 'confirmado'
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='apartado.creado:9001:tienda'") == '0'
    record('F01-01', run, ejecucion_pf01=sent['id'], correos_cliente=1, correos_marisa=0,
           estado='confirmado')

    # F01-03: evento repetido con la confirmación ya registrada.
    case = cases['F01-03']
    for clave in case['input']['confirmed_notifications']:
        assert estado(clave) == 'confirmado'
    before = message_count()
    run = invoke(router, 'tienda', case['input']['payload'])
    assert run['status'] == 'success'
    assert message_count() == before + case['expected']['customer_messages']
    record('F01-03', run, correos_nuevos=0)

    # F01-02: sin email. La clave de tienda es distinta, así que avisa aunque 9001 ya se confirmara.
    case = cases['F01-02']
    before = message_count()
    run = invoke(router, 'tienda', case['input']['payload'])
    assert run['status'] == 'success'
    assert message_count() == before + case['expected']['marisa_messages']
    last = messages()[0]
    marisa = sql("SELECT valor FROM pf_config WHERE clave='CORREO_MARISA'")
    assert recipients(last) == [marisa]
    text = mail(last)['Text']
    assert case['expected']['reason'] in text and 'Pendiente: 79,90 €' in text
    assert estado('apartado.creado:9001:tienda') == 'confirmado'
    repeat = invoke(router, 'tienda', case['input']['payload'])
    assert repeat['status'] == 'success' and message_count() == before + 1
    record('F01-02', run, repeticion=repeat['id'], correos_cliente=0, correos_marisa=1,
           motivo=case['expected']['reason'])

    # Liquidado al crear: indica que puede recogerse.
    payload = json.loads(json.dumps(cases['F01-01']['input']['payload']))
    payload['datos'].update(id=9011, estado='liquidado', abonado=89.9, pendiente=0)
    before = message_count()
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'success' and message_count() == before + 1
    text = mail(messages()[0])['Text']
    assert 'recogerlo' in text and 'Pendiente: 0,00 €' in text
    record('Apartado liquidado', run, recogida=True)

    # Dato financiero ausente: incidencia, sin reserva ni correo al cliente.
    payload = json.loads(json.dumps(cases['F01-01']['input']['payload']))
    payload['datos'].update(id=9012, pendiente=None)
    before = message_count()
    error_before = ids(error)
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'error'
    handlers = wait_runs(error, error_before, 2)
    assert all(h['status'] == 'success' for h in handlers)
    assert message_count() == before + 2
    notices = [mail(m)['Text'] for m in messages()[:2]]
    assert any('PF-01' in t and 'Validar apartado' in t for t in notices)
    assert all(r == [marisa] for r in (recipients(m) for m in messages()[:2]))
    assert sql("SELECT count(*) FROM pf_registro WHERE clave LIKE 'apartado.creado:9012%'") == '0'
    record('Dato financiero ausente', run, incidencias=2,
           ejecuciones_pf08=[h['id'] for h in handlers])

    # Talla opcional en la app (talla: str | None): sin talla, el mensaje dice "no indicada".
    payload = json.loads(json.dumps(cases['F01-01']['input']['payload']))
    payload['datos'].update(id=9013, talla=None)
    before = message_count()
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [payload['datos']['email']]
    text = mail(last)['Text']
    assert 'Talla: no indicada' in text and 'Precio: 89,90 €' in text, text
    assert estado('apartado.creado:9013') == 'confirmado'
    record('Sin talla, con email', run, correos_cliente=1, talla='no indicada')

    payload = json.loads(json.dumps(cases['F01-02']['input']['payload']))
    payload['datos'].update(id=9014, talla='')
    before = message_count()
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [marisa]
    text = mail(last)['Text']
    assert 'Talla: no indicada' in text and 'email_ausente' in text, text
    assert estado('apartado.creado:9014:tienda') == 'confirmado'
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='apartado.creado:9014'") == '0'
    record('Sin talla, sin email', run, correos_cliente=0, correos_marisa=1, talla='no indicada')

    assert business_snapshot() == business_before, 'Las pruebas alteraron la tienda'
    (STATE / '01-evidencia.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
finally:
    for flow in reversed(flows):
        request('/rest/workflows/' + flow['id'] + '/deactivate', {})
    for key in config_keys:
        config(key, saved_config.get(key))
