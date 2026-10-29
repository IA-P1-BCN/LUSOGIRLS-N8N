from datetime import datetime
import json
import sqlite3
from unittest.mock import MagicMock

import config
import database
from models import apartado
from services import n8n

NUEVO = {'cliente':'Cliente ficticio','producto':'Zapatos demo','email':'cliente@example.test','precio':60,'abono_inicial':10}


def test_consentimiento_omitido_es_false_y_no_se_deduce_del_email(cliente):
    r = cliente.post('/api/apartados', json=NUEVO)
    assert r.status_code == 201
    a = r.json()
    assert a['consentimiento_notificaciones'] is False
    assert a['consentimiento_actualizado'] is None
    assert apartado.obtener(a['id'])['consentimiento_notificaciones'] is False


def test_permiso_explicito_revocable_sin_alterar_pagos(cliente, anonimo):
    a = cliente.post('/api/apartados',json=NUEVO | {'consentimiento_notificaciones':True}).json()
    assert a['consentimiento_notificaciones'] is True
    assert datetime.fromisoformat(a['consentimiento_actualizado'].replace('Z','+00:00')).tzinfo
    assert apartado.obtener(a['id'])['consentimiento_notificaciones'] is True
    path = f"/api/apartados/{a['id']}/consentimiento"
    assert anonimo.get(path).status_code == 401
    assert anonimo.patch(path,json={'consentimiento_notificaciones':False}).status_code == 401
    before=cliente.get(f"/api/apartados/{a['id']}").json()
    revoked=cliente.patch(path,json={'consentimiento_notificaciones':False}).json()
    assert revoked['consentimiento_notificaciones'] is False
    assert set(cliente.get(path).json())=={'apartado_id','consentimiento_notificaciones','consentimiento_actualizado'}
    after=cliente.get(f"/api/apartados/{a['id']}").json()
    for k in ['abonos','estado','precio','abonado','pendiente','fecha_limite']:
        assert before[k]==after[k]


def test_permiso_requiere_booleano_explicito_y_apartado_existente(cliente):
    for value in ['true','sí',1,None]:
        assert cliente.post('/api/apartados',json=NUEVO | {'consentimiento_notificaciones':value}).status_code==422
    assert cliente.patch('/api/apartados/999999/consentimiento',json={'consentimiento_notificaciones':True}).status_code==404


def test_migracion_aditiva_no_atribuye_permiso(tmp_path, monkeypatch):
    path=tmp_path/'antigua.db'
    # Representa el esquema anterior; se crea solo en una base temporal del test.
    with sqlite3.connect(path) as con:
        con.execute('CREATE TABLE apartados (id INTEGER PRIMARY KEY, cliente TEXT NOT NULL)')
        con.execute("INSERT INTO apartados(id,cliente) VALUES(1,'Registro previo')")
    monkeypatch.setattr(config,'DB_PATH',str(path))
    database.crear_tablas();database.crear_tablas()
    row=database.consultar('SELECT * FROM apartados')[0]
    assert row=={'id':1,'cliente':'Registro previo','consentimiento_notificaciones':0,'consentimiento_actualizado':None}


def test_emisor_exige_clave_y_no_expone_errores(monkeypatch, caplog):
    monkeypatch.setattr(config,'N8N_WEBHOOK_URL','http://n8n:5678/webhook/tienda')
    monkeypatch.setattr(config,'N8N_WEBHOOK_KEY','')
    send=MagicMock()
    monkeypatch.setattr(n8n._cliente_http,'open',send)
    n8n.avisar('apartado.creado',{'id':1})
    send.assert_not_called()
    monkeypatch.setattr(config,'N8N_WEBHOOK_KEY','CLAVE_FICTICIA_WEBHOOK')
    n8n.avisar('apartado.creado',{'id':1})
    req=send.call_args.args[0]
    assert req.get_header('X-pf-webhook-key')=='CLAVE_FICTICIA_WEBHOOK'
    assert json.loads(req.data)=={'evento':'apartado.creado','datos':{'id':1}}
    assert send.call_args.kwargs['timeout']==5
    send.side_effect=RuntimeError('CLAVE_FICTICIA_WEBHOOK privado@example.test')
    n8n.avisar('apartado.creado',{'id':1})
    assert 'CLAVE_FICTICIA_WEBHOOK' not in caplog.text and 'privado@' not in caplog.text
    assert n8n._SinRedirecciones().redirect_request(None,None,302,'',{},'http://otro.example') is None
