"""PF-09 en el laboratorio: contratos F09 sin escrituras y carga idempotente contra la tienda aislada.
Ejecutar con: python3 tests/n8n/lab.py 09 (antes, python3 tests/n8n/lab.py 08)."""
import csv
import io
import json
from decimal import Decimal
from lab import ROOT, STATE, login, prepare_credentials, install, invoke, sql, request, message_count, execution_data, SECRET
from test_08 import activate

path = ROOT / 'workflows/09-migracion.json'
SIM = 'http://127.0.0.1:18080'
TIENDA = 'http://127.0.0.1:18000'
API = {'X-API-Key': SECRET}

def quoted(value):
    return "'" + str(value).replace("'", "''") + "'"

def set_config(key, value):
    sql('DELETE FROM pf_config WHERE clave=' + quoted(key))
    if value is not None:
        sql('INSERT INTO pf_config VALUES(' + quoted(key) + ',' + quoted(value) + ')')

def csv_text(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return out.getvalue()

def salida(run, nodo):
    data = execution_data(run['id'])['resultData']['runData']
    assert nodo in data, (nodo, list(data))
    return data[nodo][0]['data']['main'][0][0]['json']

def asunto_ultimo():
    return request('/api/v1/messages', base='http://127.0.0.1:18025')['messages'][0]['Subject']

def posts_simulador():
    return [c for c in request('/__calls', base=SIM) if c['method'] == 'POST']

def ventas_tienda():
    return request('/api/ventas?desde=2026-10-01&hasta=2026-10-06', base=TIENDA, headers=API)

def documentos_migracion():
    filas = sql("SELECT clave || '|' || estado || '|' || documento::text FROM pf_registro WHERE clave LIKE 'migracion:%' ORDER BY clave")
    return {f.split('|', 2)[0]: (f.split('|', 2)[1], json.loads(f.split('|', 2)[2])) for f in filas.splitlines() if f}

login(); prepare_credentials()
error_id = (STATE / 'error-id.txt').read_text()
error = request('/rest/workflows/' + error_id)['data']; activate(error)
saved = json.loads(sql("SELECT coalesce(jsonb_object_agg(clave,valor),'{}'::jsonb) FROM pf_config WHERE clave IN ('API_BASE_URL','MIGRACION_CARGA_PERMITIDA')"))
apartados_csv = (ROOT / 'data/excel_actual_apartados.csv').read_text(encoding='utf-8')
ventas_csv = (ROOT / 'data/excel_actual_ventas.csv').read_text(encoding='utf-8')
lote = lambda **extra: {'modo': 'carga', 'autorizada': True, 'csv_apartados': apartados_csv, 'csv_ventas': ventas_csv, **extra}
evidence = []
flow = install(path, error_id, retain_test_execution=True); activate(flow)
try:
    # 1. Contratos F09: con la carga permitida y autorizada, ninguna fila llega a la API (post_count 0).
    set_config('API_BASE_URL', 'http://simulador:8080'); set_config('MIGRACION_CARGA_PERMITIDA', 'si')
    cases = [c for c in json.loads((ROOT / 'data/pruebas/contratos.json').read_text())['cases'] if c['flow'] == 'PF-09']
    for case in cases:
        row, expected = case['input']['row'], case['expected']
        es_venta = 'concepto' in row
        payload = {'modo': 'carga', 'autorizada': True,
                   'csv_apartados': '' if es_venta else csv_text([row]),
                   'csv_ventas': csv_text([row]) if es_venta else ''}
        request('/__fixture', {}, base=SIM)
        before = message_count()
        run = invoke(flow, 'migracion', payload)
        assert run['status'] == 'success', run
        analisis = salida(run, 'Agrupar y revisar')
        assert analisis['resumen']['post_count'] == expected['post_count'] == 0
        assert posts_simulador() == [] and message_count() == before + 1
        if 'ignored_as' in expected:
            assert analisis['ignoradas'][0]['ignorada_como'] == expected['ignored_as']
        else:
            grupo = analisis['grupos'][0]
            assert expected['needs_review'] in grupo['motivos'], grupo['motivos']
            if 'normalized' in expected: assert grupo['normalizado'] == expected['normalized'], grupo['normalizado']
            if 'hold_related_rows' in expected: assert grupo['hold_related_rows'] is expected['hold_related_rows']
        evidence.append({'caso': case['id'], 'ejecucion': run['id'], 'resultado': 'PASS'}); print(json.dumps(evidence[-1]))

    # 2. Bloqueo: sin MIGRACION_CARGA_PERMITIDA, una carga autorizada solo produce el informe de análisis.
    set_config('MIGRACION_CARGA_PERMITIDA', None)
    request('/__fixture', {}, base=SIM)
    run = invoke(flow, 'migracion', lote())
    assert run['status'] == 'success', run
    assert salida(run, 'Agrupar y revisar')['resumen']['post_count'] == 8
    assert posts_simulador() == [] and 'Migración del Excel' in asunto_ultimo()
    assert sql("SELECT count(*) FROM pf_registro WHERE ejecucion=" + quoted(run['id'])) == '0'
    evidence.append({'caso': 'bloqueo sin MIGRACION_CARGA_PERMITIDA', 'ejecucion': run['id'], 'resultado': 'PASS'}); print(json.dumps(evidence[-1]))

    # 3. Carga real contra la tienda aislada (sin webhook) y repetición sin duplicados.
    set_config('API_BASE_URL', 'http://tienda:8000'); set_config('MIGRACION_CARGA_PERMITIDA', 'si')
    sql("DELETE FROM pf_registro WHERE clave LIKE 'migracion:%'")
    ventas_antes = len(ventas_tienda())
    run = invoke(flow, 'migracion', lote())
    assert run['status'] == 'success', run
    resumen = salida(run, 'Redactar resultado')['resumen_carga']
    assert resumen == {'creadas': 8, 'ya_estaban': 0, 'revision': 0, 'pendientes': 0, 'sin_reservar': 0}, resumen
    plan = {o['clave']: o for o in salida(run, 'Agrupar y revisar')['plan_carga']}
    docs = documentos_migracion()
    assert set(docs) == set(plan) and all(estado == 'confirmado' for estado, _ in docs.values())
    ventas = {v['id']: v for v in ventas_tienda()}
    for clave, (_, doc) in docs.items():
        esperado, creado = plan[clave]['payload'], doc['resultado']
        if plan[clave]['tipo'] == 'apartado':
            real = request('/api/apartados/' + str(creado['id']), base=TIENDA, headers=API)
            assert real['fecha'] == esperado['fecha'] and Decimal(str(real['precio'])) == Decimal(str(esperado['precio']))
            assert [(a['importe'], a['forma_pago'], a['fecha']) for a in real['abonos']] == [(esperado['abono_inicial'], esperado['forma_pago'], esperado['fecha'])]
        else:
            real = ventas[creado['id']]
            assert (real['fecha'], Decimal(str(real['importe'])), real['forma_pago']) == (esperado['fecha'], Decimal(str(esperado['importe'])), esperado['forma_pago'])
    assert len(ventas) == ventas_antes + 6
    evidence.append({'caso': 'carga lote completo', 'ejecucion': run['id'], 'resumen': resumen, 'resultado': 'PASS'}); print(json.dumps(evidence[-1]))

    run = invoke(flow, 'migracion', lote())
    resumen = salida(run, 'Redactar resultado')['resumen_carga']
    assert run['status'] == 'success' and resumen == {'creadas': 0, 'ya_estaban': 8, 'revision': 0, 'pendientes': 0, 'sin_reservar': 0}, resumen
    assert len(ventas_tienda()) == ventas_antes + 6 and documentos_migracion() == docs
    evidence.append({'caso': 'segunda carga sin duplicados', 'ejecucion': run['id'], 'resumen': resumen, 'resultado': 'PASS'}); print(json.dumps(evidence[-1]))

    # 4. Abono enlazado a su apartado: Marisa da la forma de pago de Carmen (filas 2 y 5).
    lineas = apartados_csv.strip().split('\n')
    lineas = [l + ',forma_pago' if i == 0 else l + (',efectivo' if 'armen' in l.split(',')[1] else ',') for i, l in enumerate(lineas)]
    run = invoke(flow, 'migracion', lote(csv_apartados='\n'.join(lineas) + '\n'))
    resumen = salida(run, 'Redactar resultado')['resumen_carga']
    assert run['status'] == 'success' and resumen == {'creadas': 2, 'ya_estaban': 8, 'revision': 0, 'pendientes': 0, 'sin_reservar': 0}, resumen
    estado, doc = documentos_migracion()['migracion:apartados:2']
    carmen = request('/api/apartados/' + str(doc['resultado']['id']), base=TIENDA, headers=API)
    assert [(a['fecha'], a['importe']) for a in carmen['abonos']] == [('2026-09-02', 10.0), ('2026-09-05', 20.0)]
    assert Decimal(str(carmen['pendiente'])) == Decimal('59.9')
    evidence.append({'caso': 'abono enlazado a su apartado', 'ejecucion': run['id'], 'resumen': resumen, 'resultado': 'PASS'}); print(json.dumps(evidence[-1]))
    (STATE / '09-evidencia.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
finally:
    request('/rest/workflows/' + flow['id'] + '/deactivate', {})
    request('/rest/workflows/' + error_id + '/deactivate', {})
    for key in ('API_BASE_URL', 'MIGRACION_CARGA_PERMITIDA'):
        set_config(key, saved.get(key))
