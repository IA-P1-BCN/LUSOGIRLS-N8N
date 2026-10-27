"""PF-02 real llamado por PF-00 real, solo en el laboratorio."""
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
    (ROOT / 'data/pruebas/contratos.json').read_text())['cases'] if c['flow'] == 'PF-02'}
config_keys = ['PF02_WORKFLOW_ID']


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



def limpiar():
    # Registro aislado del laboratorio: solo se limpian las claves ficticias de estos casos.
    sql("DELETE FROM pf_registro WHERE clave LIKE 'abono.registrado:90%'")


def variante(case_id, **cambios):
    payload = json.loads(json.dumps(cases[case_id]['input']['payload']))
    payload['datos'].update(cambios)
    return payload


def enviar(router, payload):
    before = message_count()
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
    return run, before


try:
    error = install(root / 'workflows/08-errores.json')
    flows.append(error)
    activate(error)
    child = install(root / 'workflows/02-recibo-abono.json', error['id'])
    flows.append(child)
    activate(child)
    router = install(root / 'workflows/00-entrada-eventos.json', error['id'])
    flows.append(router)
    activate(router)
    # El Webhook publicado tarda ocasionalmente más de un segundo en registrarse.
    time.sleep(2)
    config('PF02_WORKFLOW_ID', child['id'])
    limpiar()
    business_before = business_snapshot()
    marisa = sql("SELECT valor FROM pf_config WHERE clave='CORREO_MARISA'")

    # F02-01: pago parcial. Recibo al cliente con las cifras de la app, sin recogida.
    case = cases['F02-01']
    datos = case['input']['payload']['datos']
    child_before = ids(child)
    before = message_count()
    run = invoke(router, 'tienda', case['input']['payload'])
    assert run['status'] == 'success', {'ejecucion': run['id'], 'estado': run['status']}
    sent = wait_runs(child, child_before, 1)[0]
    assert message_count() == before + case['expected']['customer_messages']
    last = messages()[0]
    assert recipients(last) == [datos['email']]
    text = mail(last)['Text']
    expected_lines = ('Modelo: Botin demo', 'Talla: 38', 'Importe de este abono: 20,00 €',
                      'Total abonado: 30,00 €', 'Pendiente: 59,90 €')
    assert all(line in text for line in expected_lines), text
    assert case['expected']['recogida'] is False and 'recogerlo' not in text
    assert estado('abono.registrado:9001:3000:2000') == 'confirmado'
    assert sql("SELECT count(*) FROM pf_registro WHERE clave LIKE 'abono.registrado:9001%:tienda'") == '0'
    record('F02-01', run, ejecucion_pf02=sent['id'], correos_cliente=1, correos_marisa=0,
           estado='confirmado')

    # F02-02: liquidación. Mensaje de recogida y pendiente cero.
    case = cases['F02-02']
    datos = case['input']['payload']['datos']
    run, before = enviar(router, case['input']['payload'])
    assert message_count() == before + case['expected']['customer_messages']
    last = messages()[0]
    assert recipients(last) == [datos['email']]
    text = mail(last)['Text']
    expected_lines = ('Importe de este abono: 59,90 €', 'Total abonado: 89,90 €', 'Pendiente: 0,00 €')
    assert all(line in text for line in expected_lines), text
    assert case['expected']['recogida'] is True and 'recogerlo' in text
    assert estado('abono.registrado:9001:8990:5990') == 'confirmado'
    record('F02-02', run, correos_cliente=1, recogida=True, estado='confirmado')

    # F02-03: dos pagos iguales con distinto acumulado. Partimos de un registro limpio porque el
    # primer pago coincide con la clave de F02-01.
    limpiar()
    case = cases['F02-03']
    first, second = case['input']['payloads']
    before_all = message_count()
    run1, before = enviar(router, first)
    assert message_count() == before + 1
    text1 = mail(messages()[0])['Text']
    assert 'Total abonado: 30,00 €' in text1 and 'Pendiente: 59,90 €' in text1, text1
    run2, before = enviar(router, second)
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [second['datos']['email']]
    text2 = mail(last)['Text']
    assert 'Total abonado: 50,00 €' in text2 and 'Pendiente: 39,90 €' in text2, text2
    assert 'Importe de este abono: 20,00 €' in text1 and 'Importe de este abono: 20,00 €' in text2
    assert message_count() == before_all + case['expected']['customer_messages']
    assert estado('abono.registrado:9001:3000:2000') == 'confirmado'
    assert estado('abono.registrado:9001:5000:2000') == 'confirmado'
    # Repetir el segundo pago ya confirmado no envía nada.
    repeat, before = enviar(router, second)
    assert message_count() == before
    record('F02-03', run2, ejecucion_primer_pago=run1['id'], repeticion=repeat['id'],
           correos_cliente=2, pendientes=case['expected']['pending_balances'], correos_nuevos_repeticion=0)

    # Sin email: aviso a la tienda, cero envíos al cliente; repetir no duplica.
    limpiar()
    payload = variante('F02-01', id=9005, email=None)
    run, before = enviar(router, payload)
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [marisa]
    text = mail(last)['Text']
    assert 'email_ausente' in text and 'Total abonado: 30,00 €' in text, text
    assert estado('abono.registrado:9005:3000:2000:tienda') == 'confirmado'
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='abono.registrado:9005:3000:2000'") == '0'
    repeat, before = enviar(router, payload)
    assert message_count() == before
    record('Sin email', run, repeticion=repeat['id'], correos_cliente=0, correos_marisa=1,
           motivo='email_ausente')

    # Email con formato no válido: mismo aviso a la tienda con otro motivo.
    payload = variante('F02-01', id=9006, email='sin-arroba')
    run, before = enviar(router, payload)
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [marisa]
    assert 'email_invalido' in mail(last)['Text']
    assert estado('abono.registrado:9006:3000:2000:tienda') == 'confirmado'
    record('Email no válido', run, correos_cliente=0, correos_marisa=1, motivo='email_invalido')

    # Saldo contradictorio: activo con pendiente cero. Sin recibo al cliente ni recogida.
    payload = variante('F02-02', id=9007, estado='activo')
    run, before = enviar(router, payload)
    assert message_count() == before + 1
    last = messages()[0]
    assert recipients(last) == [marisa]
    text = mail(last)['Text']
    assert 'saldo_contradictorio' in text and 'recogerlo' not in text, text
    assert estado('abono.registrado:9007:8990:5990:tienda') == 'confirmado'
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='abono.registrado:9007:8990:5990'") == '0'
    record('Saldo contradictorio', run, correos_cliente=0, correos_marisa=1,
           motivo='saldo_contradictorio')

    # Importe ausente: incidencia por PF-08, sin reserva ni correo al cliente.
    payload = variante('F02-01', id=9012, importe=None)
    before = message_count()
    error_before = ids(error)
    run = invoke(router, 'tienda', payload)
    assert run['status'] == 'error'
    handlers = wait_runs(error, error_before, 2)
    assert all(h['status'] == 'success' for h in handlers)
    assert message_count() == before + 2
    notices = [mail(m)['Text'] for m in messages()[:2]]
    assert any('PF-02' in t and 'Validar abono' in t for t in notices), notices
    assert all(recipients(m) == [marisa] for m in messages()[:2])
    assert sql("SELECT count(*) FROM pf_registro WHERE clave LIKE 'abono.registrado:9012%'") == '0'
    record('Importe ausente', run, incidencias=2, ejecuciones_pf08=[h['id'] for h in handlers])

    # Talla opcional en la app (talla: str | None): el recibo sale con "Talla: no indicada" y un
    # evento repetido no lo duplica.
    for apartado_id, talla in ((9008, None), (9009, '')):
        payload = variante('F02-01', id=apartado_id, talla=talla)
        run, before = enviar(router, payload)
        assert message_count() == before + 1
        last = messages()[0]
        assert recipients(last) == [payload['datos']['email']]
        text = mail(last)['Text']
        assert 'Talla: no indicada' in text and 'Total abonado: 30,00 €' in text, text
        assert estado('abono.registrado:%d:3000:2000' % apartado_id) == 'confirmado'
        assert sql("SELECT count(*) FROM pf_registro WHERE clave='abono.registrado:%d:3000:2000:tienda'" % apartado_id) == '0'
        repeat, before = enviar(router, payload)
        assert message_count() == before
        record('Sin talla (%s)' % ('null' if talla is None else 'vacía'), run, repeticion=repeat['id'],
               correos_cliente=1, talla='no indicada', correos_nuevos_repeticion=0)

    assert business_snapshot() == business_before, 'Las pruebas alteraron la tienda'
    (STATE / '02-evidencia.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
finally:
    for flow in reversed(flows):
        request('/rest/workflows/' + flow['id'] + '/deactivate', {})
    for key in config_keys:
        config(key, saved_config.get(key))
