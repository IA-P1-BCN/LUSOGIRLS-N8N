"""PF-10 en el laboratorio: contratos F10 contra el simulador (API de la tienda y Telegram) y PF-08.
Ejecutar con: python3 tests/n8n/lab.py 10 (antes, python3 tests/n8n/lab.py 08)."""
import json
import time
import uuid
from lab import ROOT, STATE, login, prepare_credentials, request, sql, fixture_flow, invoke, message_count, execution_data
from test_08 import activate, executions

path = ROOT / 'workflows/10-saldo-telegram.json'
SIM = 'http://127.0.0.1:18080'
MAIL = 'http://127.0.0.1:18025'
TELEGRAM = '/bot<token>/sendMessage'
YO = 555000111
CONTACTO = 'Calle Mayor 3'
DERIVAR = f'No puedo mostrarte estos datos por aquí. Habla con {CONTACTO} y lo revisamos.'
NO_ENCONTRADO = f'No encuentro apartados pendientes con tu número. Si crees que es un error, habla con {CONTACTO}.'
FALLO = 'Ahora mismo no puedo consultar tu saldo. Inténtalo más tarde o habla con {}.'

def quoted(value):
    return "'" + str(value).replace("'", "''") + "'"

def set_config(key, value):
    sql('DELETE FROM pf_config WHERE clave=' + quoted(key))
    if value is not None:
        sql('INSERT INTO pf_config VALUES(' + quoted(key) + ',' + quoted(value) + ')')

def credencial_telegram():
    # Token ficticio; la Base URL lleva los envíos al simulador.
    existentes = [c for c in request('/rest/credentials')['data'] if c['type'] == 'telegramApi' and c['name'] == 'PF · Telegram']
    cred = existentes[0] if existentes else request('/rest/credentials', {'name': 'PF · Telegram', 'type': 'telegramApi',
        'data': {'accessToken': '000000000:PRUEBA-FICTICIA', 'baseUrl': 'http://simulador:8080'}})['data']
    saved = json.loads((STATE / 'credentials.json').read_text())
    saved['telegramApi'] = {'id': cred['id'], 'name': cred['name']}
    (STATE / 'credentials.json').write_text(json.dumps(saved))

def copia(guardar='all', cambio=None):
    # El laboratorio guarda las ejecuciones correctas para tener su ID; F10-20 usa los settings exportados.
    flow = json.loads(path.read_text())
    if guardar: flow['settings']['saveDataSuccessExecution'] = guardar
    if cambio: cambio(flow)
    file = STATE / (uuid.uuid4().hex + '.json'); file.write_text(json.dumps(flow))
    return file

def update(chat_type='private', chat_id=YO, **message):
    m = {'message_id': 7, 'date': 0, 'chat': {'id': chat_id, 'type': chat_type}, 'from': {'id': YO, 'is_bot': False, 'first_name': 'Prueba'}, **message}
    return {'update_id': 100001, 'message': m}

SIN_USER_ID = object()
def contacto(phone, user_id=YO, **extra):
    c = {'phone_number': phone, 'first_name': 'Prueba'}
    if user_id is not SIN_USER_ID: c['user_id'] = user_id
    return update(contact=c, **extra)

def ap(id, cliente, telefono, **extra):
    return {'id': id, 'fecha': '2026-09-02', 'cliente': cliente, 'telefono': telefono, 'email': None, 'producto': 'Botín piel marrón',
            'talla': '38', 'precio': 89.9, 'fecha_limite': '2030-12-01', 'estado': 'activo', 'abonado': 10.0, 'pendiente': 79.9, **extra}

def llamadas():
    return request('/__calls', base=SIM)

def gets_apartados(calls):
    return [c for c in calls if c['method'] == 'GET' and c['path'] == '/api/apartados']

def posts_negocio(calls):
    return [c for c in calls if c['method'] == 'POST' and c['path'].startswith('/api/')]

def envios(calls):
    return [c['body'] for c in calls if c['path'] == TELEGRAM]

def error_de(run):
    return execution_data(run['id'])['resultData']['error']['message']

def ultimo_correo():
    m = request('/api/v1/messages', base=MAIL)['messages'][0]
    return request('/api/v1/message/' + m['ID'], base=MAIL)['Text']

def correo_pf08(antes):
    # Un correo nuevo de PF-08 que nombra el flujo y el paso, y no lleva el teléfono del caso.
    assert message_count() == antes + 1, (message_count(), antes)
    texto = ultimo_correo()
    assert 'Saldo por Telegram' in texto and 'Paso: Detener por fallo de consulta' in texto, texto
    assert '612345001' not in texto, texto

def ejecutar(flow, hook, entrada, apartados=(), api_status=None):
    fixture = {'apartados': list(apartados)}
    if api_status: fixture['apartados_response'] = {'status': api_status}
    request('/__fixture', fixture, base=SIM)
    antes = message_count()
    run = invoke(flow, hook, entrada)
    return run, llamadas(), antes

def un_envio(calls, chat_id=YO, teclado=True):
    # Comprobaciones comunes: un solo mensaje, HTML, sin atribución, sin undefined/null, teclado solo en privado.
    e = envios(calls)
    assert len(e) == 1, e
    body = e[0]
    assert body['chat_id'] == chat_id and body.get('parse_mode') == 'HTML', body
    assert 'n8n' not in body['text'].lower() and 'undefined' not in body['text'] and 'null' not in body['text'], body['text']
    if teclado:
        assert body['reply_markup']['keyboard'][0][0]['request_contact'] is True, body
    else:
        assert 'reply_markup' not in body, body
    assert posts_negocio(calls) == [], posts_negocio(calls)
    return body['text']

evidence = []
def registrar(caso, run, **extra):
    evidence.append({'caso': caso, 'ejecucion': run['id'] if run else None, **extra, 'resultado': 'PASS'}); print(json.dumps(evidence[-1], ensure_ascii=False))

login(); prepare_credentials(); credencial_telegram()
error_id = (STATE / 'error-id.txt').read_text()
error = request('/rest/workflows/' + error_id)['data']; activate(error)
saved = json.loads(sql("SELECT coalesce(jsonb_object_agg(clave,valor),'{}'::jsonb) FROM pf_config WHERE clave IN ('API_BASE_URL','CONTACTO_TIENDA')"))
instalados = []
def instalar(file):
    flow, hook = fixture_flow(file, error_id); instalados.append(flow); return flow, hook
try:
    set_config('API_BASE_URL', 'http://simulador:8080'); set_config('CONTACTO_TIENDA', CONTACTO)
    flow, hook = instalar(copia())
    carmen = ap(1, 'Carmen Ruiz', '612 345 001')

    # F10-01: un activo propio entre otro cliente, un teléfono null y un liquidado propio. Query exacta, sin pagina.
    run, calls, _ = ejecutar(flow, hook, contacto('34612345001'),
        [carmen, ap(2, 'Jorge Martín', '600 000 002'), ap(3, 'Ana Sin Teléfono', None), ap(4, 'Carmen Ruiz', '612 345 001', estado='liquidado', pendiente=0)])
    assert run['status'] == 'success', run
    g = gets_apartados(calls); assert len(g) == 1 and g[0]['query'] == {'estado': ['activo']}, g
    assert un_envio(calls) == f'Tus apartados pendientes:\n- Botín piel marrón (talla 38): te faltan 79,90 €. Fecha límite: 01/12/2030.\nSi tienes dudas, habla con {CONTACTO}.'
    registrar('F10-01', run)

    # F10-02: dos activos en el orden de la API, escape HTML una sola vez, talla null omitida, sin total.
    run, calls, _ = ejecutar(flow, hook, contacto('34612345001'),
        [ap(5, 'Carmen Ruiz', '612345001', producto='Sandalia <verano> & playa', talla=None, fecha_limite='2030-06-15', pendiente=20.0), carmen])
    t = un_envio(calls)
    assert '- Sandalia &lt;verano&gt; &amp; playa: te faltan 20,00 €' in t and t.index('Sandalia') < t.index('Botín'), t
    assert '&amp;lt;' not in t and '99,90' not in t, t
    registrar('F10-02', run)

    # F10-03: plazo pasado (sigue activo hasta que PF-06 lo venza). Fecha de la app y aviso, sin POST /vencer.
    run, calls, _ = ejecutar(flow, hook, contacto('34612345001'), [ap(6, 'Carmen Ruiz', '612 345 001', fecha_limite='2026-01-15', pendiente=15.0)])
    t = un_envio(calls)
    assert f'te faltan 15,00 €. Fecha límite: 15/01/2026. El plazo ya ha pasado: habla con {CONTACTO}.' in t, t
    registrar('F10-03', run)

    for caso, apartados, esperado in [
        ('F10-04', [carmen, ap(7, 'Luis Ruiz', '612 345 001')], DERIVAR),
        ('F10-05', [], NO_ENCONTRADO),
        ('F10-16', [ap(8, 'Carmen Ruiz', '912 345 678')], NO_ENCONTRADO),
    ]:
        entrada = contacto('34912345678') if caso == 'F10-16' else contacto('34612345001')
        run, calls, _ = ejecutar(flow, hook, entrada, apartados)
        assert run['status'] == 'success' and len(gets_apartados(calls)) == 1, (caso, run)
        assert un_envio(calls) == esperado, caso
        registrar(caso, run)

    # Sin llamada a la API: contacto ajeno, sin user_id, grupo, inicio, texto libre y teléfono de Telegram no válido.
    for caso, entrada, inicio, chat_id, teclado in [
        ('F10-06', contacto('34612345001', user_id=555000999), 'Solo puedo consultar tu propio número.', YO, True),
        ('F10-07', contacto('34612345001', user_id=SIN_USER_ID), 'Solo puedo consultar tu propio número.', YO, True),
        ('F10-08', contacto('34612345001', chat_type='group', chat_id=-100123), 'Por privacidad, las consultas de saldo', -100123, False),
        ('F10-09', update(text='/start'), 'Hola. Para ver lo que te falta por pagar', YO, True),
        ('F10-10', update(text='hola, ¿cuánto debo?'), 'No he entendido tu mensaje.', YO, True),
        ('F10-17', contacto('12345'), 'No encuentro apartados pendientes', YO, True),
    ]:
        run, calls, _ = ejecutar(flow, hook, entrada, [carmen])
        assert run['status'] == 'success' and gets_apartados(calls) == [], (caso, run, gets_apartados(calls))
        assert un_envio(calls, chat_id, teclado).startswith(inicio), caso
        registrar(caso, run)

    # F10-11 a F10-15: formatos de teléfono de la app frente al de Telegram.
    for caso, telegram, app in [('F10-11', '+34612345001', '+34 612 345 001'), ('F10-12', '34612345001', '34612345001'),
                                ('F10-13', '34612345001', '0034 612 345 001'), ('F10-14', '34612345001', '612345001'),
                                ('F10-15', '34712345001', '712 345 001')]:
        run, calls, _ = ejecutar(flow, hook, contacto(telegram), [ap(9, 'Carmen Ruiz', app)])
        assert 'te faltan 79,90 €' in un_envio(calls), caso
        registrar(caso, run)

    # F10-18 y F10-19: la API falla. Un solo GET, aviso sin teclado, Stop and Error con origen API y correo de PF-08.
    # La rama principal no emite el item {} de Always Output Data: no hay un segundo envío.
    for caso, status in [('F10-18', 401), ('F10-19', 500)]:
        run, calls, antes = ejecutar(flow, hook, contacto('34612345001'), [carmen], api_status=status)
        assert run['status'] == 'error' and len(gets_apartados(calls)) == 1, (caso, run)
        assert un_envio(calls, teclado=False) == FALLO.format(CONTACTO), caso
        assert error_de(run) == 'Fallo al consultar: API', error_de(run)
        correo_pf08(antes)
        registrar(caso, run, status=status)

    # F10-21: CONTACTO_TIENDA ausente, solo espacios y con caracteres HTML (sale escapado por la consulta).
    for valor, final in [(None, 'habla con la tienda.'), ('   ', 'habla con la tienda.'),
                         ('Calle Mayor 3 <local> & tienda', 'habla con Calle Mayor 3 &lt;local&gt; &amp; tienda.')]:
        set_config('CONTACTO_TIENDA', valor)
        run, calls, _ = ejecutar(flow, hook, update(text='hola'))
        t = un_envio(calls); assert t.endswith(final) and '&amp;lt;' not in t, (valor, t)
        registrar('F10-21', run, contacto=repr(valor))
    set_config('CONTACTO_TIENDA', CONTACTO)

    # F10-22: Leer configuración falla (tabla inexistente en una copia). Sin GET, aviso con «la tienda», origen configuración.
    def romper(f):
        nodos = [n for n in f['nodes'] if n['name'] == 'Leer configuración']
        assert len(nodos) == 1, f'F10-22: se esperaba un nodo «Leer configuración» y hay {len(nodos)}'
        consulta = nodos[0].get('parameters', {}).get('query')
        assert isinstance(consulta, str) and consulta.count('FROM pf_config') == 1, \
            'F10-22: «FROM pf_config» no aparece exactamente una vez en parameters.query de «Leer configuración»'
        nodos[0]['parameters']['query'] = consulta.replace('FROM pf_config', 'FROM tabla_inexistente_pf10', 1)
    roto, hook_roto = instalar(copia(cambio=romper))
    run, calls, antes = ejecutar(roto, hook_roto, contacto('34612345001'), [carmen])
    assert run['status'] == 'error' and gets_apartados(calls) == [], run
    assert un_envio(calls, teclado=False) == FALLO.format('la tienda')
    assert error_de(run) == 'Fallo al consultar: configuración', error_de(run)
    correo_pf08(antes)
    registrar('F10-22', run)

    # F10-20: con los settings exportados (saveDataSuccessExecution: none) la respuesta llega y no queda ejecución correcta.
    exportados = json.loads(path.read_text())['settings']
    assert exportados.get('saveDataSuccessExecution') == 'none' and exportados.get('saveDataErrorExecution') == 'all', exportados
    privado, hook_privado = instalar(copia(guardar=None))
    request('/__fixture', {'apartados': [carmen]}, base=SIM)
    previas = {e['id'] for e in executions(privado['id'])}
    request('/webhook/' + hook_privado, contacto('34612345001'))
    limite = time.monotonic() + 45
    while not envios(llamadas()) and time.monotonic() < limite: time.sleep(.3)
    assert 'te faltan 79,90 €' in un_envio(llamadas())
    time.sleep(2)
    nuevas = [e for e in executions(privado['id']) if e['id'] not in previas]
    assert not [e for e in nuevas if e.get('status') == 'success'], nuevas
    registrar('F10-20', None, ejecuciones_guardadas=len(nuevas))
    (STATE / '10-evidencia.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
finally:
    for f in instalados: request('/rest/workflows/' + f['id'] + '/deactivate', {})
    request('/rest/workflows/' + error_id + '/deactivate', {})
    for key in ('API_BASE_URL', 'CONTACTO_TIENDA'):
        set_config(key, saved.get(key))
