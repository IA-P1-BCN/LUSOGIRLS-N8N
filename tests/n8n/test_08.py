"""Ejecuta PF-08 y su Error Trigger real solo en lusogirls-pruebas."""
import copy
import json
import time
import uuid
from lab import ROOT, STATE, request, login, prepare_credentials, install, export, sql, fixture_flow, invoke, message_count

def webhook(name,path):
    return {'id':str(uuid.uuid4()),'name':name,'webhookId':str(uuid.uuid4()),'type':'n8n-nodes-base.webhook','typeVersion':2.2,'position':[0,0],'parameters':{'httpMethod':'POST','path':path,'responseMode':'onReceived','options':{}}}

def activate(flow):
    result=request('/rest/workflows/'+flow['id']+'/activate',{'versionId':flow['versionId']})
    time.sleep(1)
    return result

def executions(flow_id):
    from urllib.parse import quote
    return request('/rest/executions?filter='+quote(json.dumps({'workflowId':flow_id}))+'&limit=20')['data']['results']

def finished(flow_id, previous=None):
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        results=executions(flow_id)
        found=next((e for e in results if e['id'] not in (previous or []) and e.get('status') in ('success','error','crashed')),None)
        if found: return found
        time.sleep(.3)
    raise AssertionError('No terminó la ejecución de prueba')

if __name__=='__main__':
    login(); prepare_credentials()
    path=ROOT/'workflows/08-errores.json'
    error=install(path)
    activate(error)
    (STATE/'error-id.txt').write_text(error['id'])
    emitter={'name':'PF-05 · Cierre diario · prueba error','nodes':[webhook('Recibir prueba','pf-error-'+uuid.uuid4().hex),{'id':str(uuid.uuid4()),'name':'Fallo controlado de prueba','type':'n8n-nodes-base.code','typeVersion':2,'position':[240,0],'parameters':{'jsCode':'throw new Error("Authorization: CREDENCIAL_FICTICIA; correo privado@example.test");'}}],'connections':{'Recibir prueba':{'main':[[{'node':'Fallo controlado de prueba','type':'main','index':0}]]}},'settings':{'executionOrder':'v1','errorWorkflow':error['id']},'active':False}
    emitter=request('/rest/workflows',emitter)['data']
    try:
        activate(emitter)
        request('/webhook/'+emitter['nodes'][0]['parameters']['path'],{})
        failed=finished(emitter['id']); handled=finished(error['id'])
        assert failed['status']=='error', failed['status']
        assert handled['status']=='success', handled['status']
        messages=request('/api/v1/messages',base='http://127.0.0.1:18025')['messages']
        mail=request('/api/v1/message/'+messages[0]['ID'],base='http://127.0.0.1:18025')
        body=mail['Text']
        assert 'Fallo controlado de prueba' in body and 'PF-05' in body
        assert 'CREDENCIAL_FICTICIA' not in body and 'privado@' not in body and 'Authorization' not in body
        print(json.dumps({'prueba':'Error Trigger automático real','emisor':failed['id'],'aviso':handled['id'],'resultado':'PASS','correo':messages[0]['ID']},ensure_ascii=False))
        fixture,endpoint=fixture_flow(path)
        cases=[c for c in json.loads((ROOT/'data/pruebas/contratos.json').read_text())['cases'] if c['flow']=='PF-08']
        sql("DELETE FROM pf_registro WHERE clave LIKE 'error:demo-workflow:%'")
        try:
            for case in cases:
                before=message_count()
                run=invoke(fixture,endpoint,case['input']['error_payload'])
                assert run['status']=='success',run
                assert message_count()==before+1
                messages=request('/api/v1/messages',base='http://127.0.0.1:18025')['messages']
                text=request('/api/v1/message/'+messages[0]['ID'],base='http://127.0.0.1:18025')['Text']
                assert all(secret not in text for secret in case['expected'].get('must_not_contain',[]))
                if 'summary' in case['expected']: assert case['expected']['summary'] in text
                else: assert 'Paso: no disponible' in text and 'Ejecución: no disponible' in text
                duplicate=invoke(fixture,endpoint,case['input']['error_payload'])
                assert duplicate['status']=='success' and message_count()==before+1
                print(json.dumps({'caso':case['id'],'ejecucion':run['id'],'duplicado':duplicate['id'],'resultado':'PASS'}))
            creds=json.loads((STATE/'credentials.json').read_text())
            smtp_id=creds['smtp']['id']
            request('/rest/credentials/'+smtp_id,{'name':'PF · Notificaciones','type':'smtp','data':{'host':'correo','port':1,'secure':False,'disableStartTls':True}},method='PATCH')
            payload=copy.deepcopy(cases[0]['input']['error_payload'])
            payload['execution']['id']='fallo-canal-'+uuid.uuid4().hex
            before=message_count()
            run=invoke(fixture,endpoint,payload)
            assert run['status']=='error' and message_count()==before
            assert sql("SELECT estado FROM pf_registro WHERE clave='error:demo-workflow:"+payload['execution']['id']+"'")=='reservado'
            assert not fixture['settings'].get('errorWorkflow')
            print(json.dumps({'caso':'fallo SMTP sin recursión','ejecucion':run['id'],'resultado':'PASS'}))
        finally:
            request('/rest/workflows/'+fixture['id']+'/deactivate',{})
            if 'smtp_id' in locals():
                request('/rest/credentials/'+smtp_id,{'name':'PF · Notificaciones','type':'smtp','data':{'host':'correo','port':1025,'secure':False,'disableStartTls':True}},method='PATCH')
        export(error['id'],path)
    finally:
        request('/rest/workflows/'+emitter['id']+'/deactivate',{})
        request('/rest/workflows/'+error['id']+'/deactivate',{})
