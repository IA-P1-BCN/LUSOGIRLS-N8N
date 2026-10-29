"""Comprueba retención desactivada y exporta los JSON de HU-14 desde n8n.

Ejecutar después de test_14.py: reutiliza solo su registro auxiliar ficticio,
sin arrancar la tienda ni conceder permisos a clientes.
"""
import hashlib
import json
import time
import uuid

from lab import ROOT, STATE, SECRET, WEBHOOK_SECRET, client, request, prepare_credentials, install, export
from test_08 import activate, executions


def main():
    original_open=client.open
    def admin_timeout(req,*args,**kwargs):
        if req.full_url.startswith('http://127.0.0.1:15678/rest/'):kwargs['timeout']=180
        return original_open(req,*args,**kwargs)
    client.open=admin_timeout
    request('/rest/login',{'emailOrLdapLoginId':'qa@example.test','password':SECRET+'Aa1!'})
    assert not [w for w in request('/rest/workflows')['data'] if w.get('active')],'Laboratorio ocupado'
    prepare_credentials()
    reports=sorted(STATE.glob('qa_privacidad_*/evidencia.json'),key=lambda p:p.stat().st_mtime,reverse=True)
    report=json.loads(next(p for p in reports if json.loads(p.read_text()).get('resultado')=='PASS').read_text())
    pg=next(c for c in request('/rest/credentials')['data'] if c['name']=='PF · Registro auxiliar · '+report['registro'])
    evidence={'registro':report['registro'],'retencion':[],'exportados':[]}
    flows=[]
    def source(number):return next((ROOT/'workflows').glob(number+'-*.json'))
    def test_source(number):
        f=json.loads(source(number).read_text())
        for n in f['nodes']:
            if 'postgres' in n.get('credentials',{}):n['credentials']['postgres']={'id':pg['id'],'name':pg['name']}
            if n['type'].endswith('.webhook'):
                n['parameters']['path']='qa-retencion-'+uuid.uuid4().hex;n['webhookId']=str(uuid.uuid4())
        out=STATE/('retencion-'+number+'.json');out.write_text(json.dumps(f,ensure_ascii=False));return out
    def mails():return request('/api/v1/messages?limit=500',base='http://127.0.0.1:18025')['messages']
    def wait_mail(prior):
        end=time.monotonic()+180
        while time.monotonic()<end:
            fresh=[m for m in mails() if m['ID'] not in prior]
            if fresh:
                assert all(r['Address']=='marisa@example.test' for m in fresh for r in m['To'])
                time.sleep(2);return
            time.sleep(.5)
        raise AssertionError('No llegó el aviso ficticio')
    try:
        error=install(test_source('08'));flows.append(error);activate(error)
        for number in ('00','09'):
            f=install(test_source(number),error['id']);flows.append(f);activate(f)
            endpoint='/webhook/'+next(n for n in f['nodes'] if n['type'].endswith('.webhook'))['parameters']['path']
            payload={'modo':'analisis','csv_apartados':'','csv_ventas':''} if number=='09' else {
                'evento':'apartado.creado','datos':{'id':int(uuid.uuid4().hex[:7],16),'cliente':'Demo retención',
                'email':'demo-retencion@example.test','producto':'Zapatos demo','talla':'38','precio':50,
                'abonado':5,'pendiente':45,'estado':'activo','fecha_limite':'2027-01-27',
                'consentimiento_notificaciones':False}}
            prior={m['ID'] for m in mails()}
            request(endpoint,payload,headers={'X-PF-Webhook-Key':WEBHOOK_SECRET});wait_mail(prior)
            assert executions(f['id'])==[],'Se conservó la ejecución del webhook'
            evidence['retencion'].append({'flujo':'PF-'+number,'workflow_id':f['id'],'historial_guardado':False,'resultado':'PASS'})
            if number=='00':
                prior={m['ID'] for m in mails()}
                request(endpoint,{'evento':'desconocido','datos':{}},headers={'X-PF-Webhook-Key':WEBHOOK_SECRET});wait_mail(prior)
                assert executions(f['id'])==[],'Se conservó la ejecución fallida del webhook'
                evidence['retencion'].append({'flujo':'PF-00 error','historial_guardado':False,'resultado':'PASS'})
            request('/rest/workflows/'+f['id']+'/deactivate',{})
        for number in ('00','01','02','03','06','08','09'):
            path=source(number);expected=json.loads(path.read_text())
            f=install(path);flows.append(f)
            export(f['id'],path);actual=json.loads(path.read_text())
            # SMTP obtiene webhookId de metadatos al importar; no cambia parámetros/lógica.
            def nodes(value):return [{k:v for k,v in n.items() if k!='webhookId'} for n in value['nodes']]
            assert nodes(actual)==nodes(expected) and actual['connections']==expected['connections']
            assert actual['settings']==expected['settings'] and not actual['active'] and not actual['pinData']
            assert not any('id' in c for n in actual['nodes'] for c in n.get('credentials',{}).values())
            evidence['exportados'].append({'flujo':'PF-'+number,'id':f['id'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        evidence['resultado']='PASS'
    finally:
        for f in reversed(flows):
            try:request('/rest/workflows/'+f['id']+'/deactivate',{})
            except Exception:pass
        client.open=original_open
        path=STATE/'14-retencion-exportacion.json';path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
        print(json.dumps(evidence,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
