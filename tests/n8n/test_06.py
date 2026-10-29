"""PF-06 en el laboratorio aislado: casos F06 con el simulador y pasada real contra la tienda con semilla.
Ejecutar con `python3 tests/n8n/lab.py 06` después de `lab.py 08` (necesita error-id.txt)."""
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from lab import ROOT, STATE, login, prepare_credentials, fixture_flow, invoke, sql, request, message_count, execution_data, SECRET
from test_08 import activate

path = ROOT/'workflows/06-recordatorios-vencimientos.json'
SIM = 'http://127.0.0.1:18080'
MAIL = 'http://127.0.0.1:18025'
TIENDA = 'http://127.0.0.1:18000'


def ok(run):
    assert run['status'] == 'success', execution_data(run['id']).get('resultData', {}).get('error', {})


def nuevos(antes):
    """Correos llegados a Mailpit desde `antes`, con destinatario, asunto y texto."""
    n = message_count() - antes
    if n <= 0:
        return []
    lista = request('/api/v1/messages?limit=' + str(n), base=MAIL)['messages'][:n]
    salida = []
    for m in lista:
        full = request('/api/v1/message/' + m['ID'], base=MAIL)
        salida.append({'to': [t['Address'] for t in full['To']], 'asunto': full['Subject'], 'texto': full['Text']})
    return salida


def estado(clave):
    return sql("SELECT estado FROM pf_registro WHERE clave='" + clave + "'")


def confirmadas():
    filas = sql("SELECT clave FROM pf_registro WHERE estado='confirmado'")
    return set(filas.splitlines()) if filas else set()


def flujo_evento():
    """Copia del workflow con el disparador de PF-00 primero, para que fixture_flow lo sustituya por un Webhook."""
    flow = json.loads(path.read_text())
    ev = next(n for n in flow['nodes'] if n['name'] == 'Recibir vencimiento de PF-00')
    flow['nodes'].remove(ev)
    flow['nodes'].insert(0, ev)
    f = STATE/'06-evento.json'
    f.write_text(json.dumps(flow))
    return f


def tienda(ruta):
    return request(ruta, base=TIENDA, headers={'X-API-Key': SECRET})


login(); prepare_credentials()
error_id = (STATE/'error-id.txt').read_text()
error = request('/rest/workflows/' + error_id)['data']; activate(error)
cases = [c for c in json.loads((ROOT/'data/pruebas/contratos.json').read_text())['cases'] if c['flow'] == 'PF-06']
evidence = []
sql("UPDATE pf_config SET valor='http://simulador:8080' WHERE clave='API_BASE_URL'")
try:
    # ---------- 1. Casos F06-01 a F06-04 con el simulador ----------
    flow, endpoint = fixture_flow(path, error_id)
    evento = None
    try:
        for case in cases:
            src, exp = case['input'], case['expected']
            sql("DELETE FROM pf_registro WHERE clave LIKE '900%' OR clave LIKE 'vale:VALE-090%'")
            for clave in src.get('confirmed_notifications', []):
                sql("INSERT INTO pf_registro(clave,tipo,estado,ejecucion) VALUES ('" + clave + "','recordatorio','confirmado','prueba-" + case['id'] + "')")
            fixture = {'apartados': src['apartados'], 'vales': [], 'detalles': {}}
            if 'vencer_response' in src:
                r = src['vencer_response']
                fixture['detalles'][str(r['apartado']['id'])] = {**r['apartado'], 'abonos': [], 'vale': r['vale']}
            request('/__fixture', fixture, base=SIM)
            antes = message_count()
            run = invoke(flow, endpoint, {'hoy_prueba': src['hoy']}); ok(run)
            calls = request('/__calls', base=SIM)
            lista = [c for c in calls if c['method'] == 'GET' and c['path'] == '/api/apartados']
            assert len(lista) == 1 and lista[0]['query'] == {'estado': ['activo']}, lista
            posts = [c['path'] for c in calls if c['method'] == 'POST']
            assert len(posts) == exp['vencer_post_count'], posts
            a = src['apartados'][0]
            mails = nuevos(antes)

            if exp.get('reminders'):
                assert len(mails) == exp['reminders'], mails
                m = mails[0]
                assert m['to'] == [a['email']], m
                assert f"{exp['days_remaining']} días" in m['texto'] or exp['days_remaining'] == 1
                assert '79,90 €' in m['texto'] and '10,00 €' in m['texto'], m['texto']
                assert '/'.join(reversed(a['fecha_limite'].split('-'))) in m['texto'], m['texto']
                clave = f"{a['id']}:{a['fecha_limite']}:{exp['days_remaining']}:email"
                assert estado(clave) == 'confirmado', clave
            elif 'vale_codigo' in exp:
                assert posts == ['/api/apartados/%d/vencer' % a['id']], posts
                assert len(mails) == exp['customer_messages'] + exp['marisa_messages'], mails
                cliente = [m for m in mails if m['to'] == [a['email']]]
                marisa = [m for m in mails if m['to'] == ['marisa@example.test']]
                assert len(cliente) == exp['customer_messages'] and len(marisa) == exp['marisa_messages'], mails
                importe = f"{exp['vale_importe']:.2f}".replace('.', ',') + ' €'
                assert exp['vale_codigo'] in cliente[0]['texto'] and importe in cliente[0]['texto'], cliente[0]['texto']
                assert f"{a['producto']}, talla {a['talla']}" in marisa[0]['texto'] and exp['vale_codigo'] in marisa[0]['texto'], marisa[0]['texto']
                for tipo in ('cliente', 'marisa'):
                    assert estado(f"vale:{exp['vale_codigo']}:{tipo}") == 'confirmado'
                evento = {'body': {'evento': 'apartado.vencido', 'datos': src['vencer_response']}}
            else:
                assert mails == [], mails
                # F06-02: la clave previa sigue siendo la única; F06-03: no se reserva nada del 9003
                assert sql("SELECT count(*) FROM pf_registro WHERE clave LIKE '" + str(a['id']) + ":%'") == str(len(src.get('confirmed_notifications', [])))
            evidence.append({'caso': case['id'], 'ejecucion': run['id'], 'correos': len(mails), 'posts_vencer': len(posts), 'resultado': 'PASS'})
            print(json.dumps(evidence[-1]))

        # ---------- 2. Conciliación de vales: ventana de 7 días ----------
        sql("DELETE FROM pf_registro WHERE clave LIKE 'vale:VALE-09005:%'")
        request('/__fixture', {'apartados': [], 'vales': [
            {'id': 9200, 'codigo': 'VALE-09006', 'apartado_id': 9006, 'fecha': '2026-09-01', 'importe': 15.0, 'usado': 0},
            {'id': 9202, 'codigo': 'VALE-09005', 'apartado_id': 9005, 'fecha': '2026-10-18', 'importe': 20.0, 'usado': 0}],
            'detalles': {'9005': {'id': 9005, 'fecha': '2026-07-19', 'cliente': 'Cliente Demo', 'telefono': '600000000', 'email': None,
                                  'producto': 'Botin demo', 'talla': '39', 'precio': 89.9, 'fecha_limite': '2026-10-17', 'estado': 'vencido',
                                  'abonado': 20.0, 'pendiente': 69.9, 'abonos': [],
                                  'vale': {'id': 9202, 'codigo': 'VALE-09005', 'apartado_id': 9005, 'fecha': '2026-10-18', 'importe': 20.0, 'usado': 0}}}}, base=SIM)
        antes = message_count()
        run = invoke(flow, endpoint, {'hoy_prueba': '2026-10-21'}); ok(run)
        calls = request('/__calls', base=SIM)
        assert not [c for c in calls if c['path'] == '/api/apartados/9006'], 'El vale fuera de ventana no debe consultarse'
        mails = nuevos(antes)
        assert len(mails) == 1 and mails[0]['to'] == ['marisa@example.test'], mails
        assert 'VALE-09005' in mails[0]['texto'] and '20,00 €' in mails[0]['texto'] and '600000000' in mails[0]['texto'], mails[0]['texto']
        assert estado('vale:VALE-09005:marisa') == 'confirmado' and estado('vale:VALE-09005:cliente') == ''
        evidence.append({'caso': 'Conciliación 7 días y correo ausente', 'ejecucion': run['id'], 'correos': 1, 'resultado': 'PASS'})
        print(json.dumps(evidence[-1]))
    finally:
        request('/rest/workflows/' + flow['id'] + '/deactivate', {})

    # ---------- 3. Evento apartado.vencido desde PF-00 ----------
    flow_ev, endpoint_ev = fixture_flow(flujo_evento(), error_id)
    try:
        # La conciliación anterior sustituyó el fixture; el evento necesita su permiso vigente.
        request('/__fixture', {'consentimientos': {str(evento['body']['datos']['apartado']['id']): True}}, base=SIM)
        antes = message_count()
        run = invoke(flow_ev, endpoint_ev, evento); ok(run)
        assert nuevos(antes) == [], 'El evento del mismo vale no debe repetir avisos'
        evidence.append({'caso': 'Evento tras vencimiento por calendario', 'ejecucion': run['id'], 'correos': 0, 'resultado': 'PASS'})
        print(json.dumps(evidence[-1]))
    finally:
        request('/rest/workflows/' + flow_ev['id'] + '/deactivate', {})

    # ---------- 4. Pasada real contra la tienda aislada con semilla ----------
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    hoy = datetime.now(ZoneInfo('Europe/Madrid')).date()
    activos = tienda('/api/apartados?estado=activo')
    dias = {a['id']: (date.fromisoformat(a['fecha_limite']) - hoy).days for a in activos}
    a_vencer = [a for a in activos if dias[a['id']] < 0]
    limite_hoy = [a for a in activos if dias[a['id']] == 0]
    esperadas = {f"{a['id']}:{a['fecha_limite']}:{dias[a['id']]}:{'email' if a['email'] and a.get('consentimiento_notificaciones') is True else 'marisa'}"
                 for a in activos if dias[a['id']] in (7, 1)}
    previas = confirmadas()
    flow, endpoint = fixture_flow(path, error_id)
    try:
        antes = message_count()
        run = invoke(flow, endpoint, {}); ok(run)
        mails = nuevos(antes)
    finally:
        request('/rest/workflows/' + flow['id'] + '/deactivate', {})
    for a in a_vencer:
        d = tienda('/api/apartados/%d' % a['id'])
        assert d['estado'] == 'vencido' and d['vale'] and d['vale']['importe'] == a['abonado'], d
    for a in limite_hoy:
        assert tienda('/api/apartados/%d' % a['id'])['estado'] == 'activo', 'No se vence en el día límite'
    desde = str(hoy - timedelta(days=7))
    for v in tienda('/api/vales'):
        if desde <= v['fecha'] <= str(hoy):
            d = tienda('/api/apartados/%d' % v['apartado_id'])
            esperadas.add(f"vale:{v['codigo']}:marisa")
            if d['email'] and d.get('consentimiento_notificaciones') is True:
                esperadas.add(f"vale:{v['codigo']}:cliente")
    nuevas = confirmadas() - previas
    assert nuevas == esperadas - previas, (sorted(nuevas), sorted(esperadas - previas))
    assert len(mails) == len(nuevas), (len(mails), len(nuevas))
    evidence.append({'caso': 'API real semilla', 'ejecucion': run['id'], 'vencidos': len(a_vencer), 'avisos_nuevos': len(nuevas), 'resultado': 'PASS'})
    print(json.dumps(evidence[-1]))
    (STATE/'06-evidencia.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
finally:
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    request('/rest/workflows/' + error_id + '/deactivate', {})
