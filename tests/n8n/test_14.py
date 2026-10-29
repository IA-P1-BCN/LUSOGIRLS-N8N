"""HU-14: API real → webhooks autenticados → consentimiento actual → Mailpit.

Solo laboratorio: bases, volumen, credenciales y rutas propios por corrida.
Los clientes son ficticios; el permiso se declara explícitamente en cada caso.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import secrets
import subprocess
import time
import urllib.error
import uuid

from lab import ROOT, STATE, SECRET, client, request, prepare_credentials, install, fixture_flow, invoke, execution_data
from test_08 import activate, executions


def docker(*args):
    return subprocess.run(['docker', *args], check=True, capture_output=True, text=True).stdout.strip()


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def main():
    original_open = client.open
    def admin_timeout(req, *args, **kwargs):
        if req.full_url.startswith('http://127.0.0.1:15678/rest/'):
            kwargs['timeout'] = 180
        return original_open(req, *args, **kwargs)
    client.open = admin_timeout
    request('/rest/login', {'emailOrLdapLoginId':'qa@example.test','password':SECRET+'Aa1!'})
    assert not [w for w in request('/rest/workflows')['data'] if w.get('active')], 'Laboratorio ocupado'
    prepare_credentials()
    token = uuid.uuid4().hex
    database = 'qa_privacidad_' + token
    directory = STATE/database
    directory.mkdir()
    webhook_key = secrets.token_urlsafe(32)
    store = database+'_tienda'
    paths = {'00':'qa-privacidad-'+token, '09':'qa-migracion-'+token}
    compose = ['compose','--env-file',str(ROOT/'tests/n8n/.env.local'),'-f',str(ROOT/'tests/n8n/compose.yml')]
    def sql(query, db=database):
        return docker(*compose,'exec','-T','registro','psql','-U','n8n','-d',db,'-At','-v','ON_ERROR_STOP=1','-c',query)
    def config(key, value):
        sql('INSERT INTO pf_config VALUES('+quote(key)+','+quote(value)+') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor')
    def api(path, data=None, method=None):
        return request('/api'+path,data,method=method,base='http://127.0.0.1:28000',headers={'X-API-Key':SECRET})
    def shared():
        info=json.loads(docker('inspect','lusogirls-pruebas-tienda-1'))[0]
        return {k:info[k] for k in ('Id','Mounts','State')}
    before_shared=shared()
    sql('CREATE DATABASE '+database,'automatizaciones')
    sql((ROOT/'infra/registro.sql').read_text())
    config('API_BASE_URL','http://'+store+':8000')
    pg=request('/rest/credentials',{'name':'PF · Registro auxiliar · '+database,'type':'postgres','data':{
        'host':'registro','port':5432,'database':database,'user':'n8n','password':SECRET,'ssl':'disable','sshTunnel':False}})['data']
    hook=request('/rest/credentials',{'name':'PF · Webhook tienda · '+database,'type':'httpHeaderAuth',
        'data':{'name':'X-PF-Webhook-Key','value':webhook_key}})['data']
    env=directory/'.env.local';env.touch(mode=0o600)
    env.write_text('API_KEY='+SECRET+'\nDB_PATH=/data/tienda.db\nSEED=0\nTZ=Europe/Madrid\nN8N_WEBHOOK_KEY='+webhook_key+
                   '\nN8N_WEBHOOK_URL=http://n8n:5678/webhook/'+paths['00']+'\n')
    def local_flow(number):
        source=next((ROOT/'workflows').glob(number+'-*.json'))
        flow=json.loads(source.read_text())
        # Evidencia ficticia solo en copias de prueba; el entregable no guarda cabeceras.
        flow['settings'].update(saveDataSuccessExecution='all',saveDataErrorExecution='all')
        for n in flow['nodes']:
            if 'postgres' in n.get('credentials',{}):n['credentials']['postgres']={'id':pg['id'],'name':pg['name']}
            if n.get('credentials',{}).get('httpHeaderAuth',{}).get('name')=='PF · Webhook tienda':
                n['credentials']['httpHeaderAuth']={'id':hook['id'],'name':hook['name']}
            if n['type'].endswith('.webhook'):
                n['parameters']['path']=paths[number];n['webhookId']=str(uuid.uuid4())
        target=directory/source.name;target.write_text(json.dumps(flow,ensure_ascii=False))
        return target
    def messages():
        return request('/api/v1/messages?limit=500',base='http://127.0.0.1:18025')['messages']
    def wait_run(flow, prior, expected='success'):
        end=time.monotonic()+90
        while time.monotonic()<end:
            runs=[r for r in executions(flow['id']) if r['id'] not in prior and r['status'] in ('success','error','crashed')]
            if runs:
                r=runs[0]
                if r['status']!=expected:
                    d=execution_data(r['id']).get('resultData',{})
                    print(json.dumps({'ejecucion':r['id'],'paso':d.get('lastNodeExecuted'),'estado':r['status']}),flush=True)
                assert r['status']==expected
                return r
            time.sleep(.3)
        raise AssertionError('No terminó el flujo esperado')
    def ids(flow):return {r['id'] for r in executions(flow['id'])}
    report={'registro':database,'casos':[],'restaurado':False}
    def save(name, **values):
        row={'caso':name,'resultado':'PASS',**values};report['casos'].append(row)
        (directory/'evidencia.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps(row,ensure_ascii=False),flush=True)
    flows=[];started=False
    try:
        error=install(local_flow('08'));flows.append(error);activate(error)
        children={}
        for number in ('01','02','06'):
            f=install(local_flow(number),error['id']);flows.append(f);activate(f)
            config('PF'+number+'_WORKFLOW_ID',f['id']);children[number]=f
        router=install(local_flow('00'),error['id']);flows.append(router);activate(router)
        migration=install(local_flow('09'),error['id']);flows.append(migration);activate(migration)
        for number,flow in [('00',router),('09',migration)]:
            prior=ids(flow)
            for headers in ({},{'X-PF-Webhook-Key':'clave-ficticia-incorrecta'}):
                try:request('/webhook/'+paths[number],{},headers=headers)
                except urllib.error.HTTPError as e:assert e.code in (401,403)
                else:raise AssertionError('Webhook aceptó una petición no autenticada')
            assert ids(flow)==prior
            save('PF-'+number+' rechaza clave ausente e incorrecta sin ejecutar')

        # Con clave correcta, PF-09 analiza un CSV vacío, sin cargar datos.
        prior=ids(migration)
        request('/webhook/'+paths['09'],{'modo':'analisis','csv_apartados':'','csv_ventas':''},headers={'X-PF-Webhook-Key':webhook_key})
        run=wait_run(migration,prior);save('PF-09 autenticado en modo análisis',ejecucion=run['id'])
        docker('run','-d','--name',store,'--network','lusogirls-pruebas_default','-p','127.0.0.1:28000:8000',
               '--env-file',str(env),'-v',database+'_tienda:/data','-v',str(ROOT/'backend')+':/srv/backend:ro',
               '-v',str(ROOT/'frontend')+':/srv/frontend:ro','paso-firme-tienda:latest')
        started=True
        for attempt in range(60):
            try:api('/apartados');break
            except Exception:time.sleep(.5)
        else:raise AssertionError('La tienda no arrancó')

        today=datetime.now(ZoneInfo('Europe/Madrid')).date()
        def check_mail(before, expected):
            fresh=[m for m in messages() if m['ID'] not in before]
            assert sorted(r['Address'] for m in fresh for r in m['To'])==sorted(expected), 'Destinatarios inesperados'
            return fresh
        def create(name, consent=None, age=0):
            data={'cliente':name,'email':name+'@example.test','producto':'Zapatos demo','talla':'38',
                  'precio':50,'abono_inicial':5,'forma_pago':'efectivo','fecha':str(today-timedelta(days=age))}
            if consent is not None:data['consentimiento_notificaciones']=consent
            before={m['ID'] for m in messages()};prior=ids(children['01']);rprior=ids(router)
            a=api('/apartados',data);run=wait_run(children['01'],prior);r=wait_run(router,rprior)
            check_mail(before,[data['email'] if consent is True else 'marisa@example.test'])
            save('Alta '+name,ejecucion_pf00=r['id'],ejecucion_pf01=run['id'],cliente_recibe=consent is True)
            return a
        a=create('sin-permiso')
        b=create('autorizado',True)
        assert not a['consentimiento_notificaciones'] and b['consentimiento_notificaciones']
        before={m['ID'] for m in messages()};prior=ids(children['02'])
        api('/apartados/'+str(b['id'])+'/abonos',{'importe':5,'forma_pago':'tarjeta'})
        run=wait_run(children['02'],prior);check_mail(before,[b['email']])
        save('Recibo con permiso vigente',ejecucion=run['id'])
        api('/apartados/'+str(b['id'])+'/consentimiento',{'consentimiento_notificaciones':False},'PATCH')
        before={m['ID'] for m in messages()};prior=ids(children['02'])
        current=api('/apartados/'+str(b['id'])+'/abonos',{'importe':5,'forma_pago':'tarjeta'})
        run=wait_run(children['02'],prior);check_mail(before,['marisa@example.test'])
        save('Abono tras revocar: aviso solo a tienda',ejecucion=run['id'])

        # Evento antiguo: dice true, pero la consulta actual a la API responde false.
        before={m['ID'] for m in messages()};prior=ids(children['02'])
        stale={**current,'consentimiento_notificaciones':True,'importe':1}
        request('/webhook/'+paths['00'],{'evento':'abono.registrado','datos':stale},headers={'X-PF-Webhook-Key':webhook_key})
        run=wait_run(children['02'],prior);check_mail(before,['marisa@example.test'])
        data=execution_data(run['id'])['resultData']['runData']
        assert 'Aplicar consentimiento actual' in data
        save('Evento atrasado con permiso retirado: no envía al cliente',ejecucion=run['id'])

        # La caída de la fuente de consentimiento impide el correo al cliente.
        c=create('fuente-inaccesible',True)
        config('API_BASE_URL','http://'+store+':1')
        before={m['ID'] for m in messages()};prior=ids(children['02']);errors=ids(error)
        request('/webhook/'+paths['00'],{'evento':'abono.registrado','datos':{**c,'importe':1}},headers={'X-PF-Webhook-Key':webhook_key})
        run=wait_run(children['02'],prior,'error');wait_run(error,errors)
        assert all(r['Address']=='marisa@example.test' for m in messages() if m['ID'] not in before for r in m['To'])
        save('API de consentimiento inaccesible: falla cerrado con PF-08',ejecucion=run['id'])
        config('API_BASE_URL','http://'+store+':8000')

        create('recordatorio-si',True,83);create('recordatorio-no',False,89)
        create('vale-si',True,91);create('vale-no',False,91)
        # Sustituir solo el calendario por disparador de prueba; la lógica es la exportada.
        calendar,endpoint=fixture_flow(local_flow('06'),error['id']);flows.append(calendar)
        before={m['ID'] for m in messages()}
        run=invoke(calendar,endpoint,{},timeout=90)
        assert run['status']=='success', {'ejecucion':run['id'],'paso':execution_data(run['id']).get('resultData',{}).get('lastNodeExecuted')}
        time.sleep(2)
        fresh=check_mail(before,['recordatorio-si@example.test','marisa@example.test','vale-si@example.test','marisa@example.test','marisa@example.test'])
        assert len(api('/vales'))==2
        save('PF-06 recordatorios y vales con/sin permiso',ejecucion=run['id'],correos=len(fresh),vales=2)
        before={m['ID'] for m in messages()}
        repeat=invoke(calendar,endpoint,{},timeout=90)
        assert repeat['status']=='success';check_mail(before,[])
        save('PF-06 repetido: sin duplicados',ejecucion=repeat['id'])
        report['resultado']='PASS'
    finally:
        cleanup=[]
        for f in reversed(flows):
            try:request('/rest/workflows/'+f['id']+'/deactivate',{})
            except Exception as e:cleanup.append(type(e).__name__)
        if started:docker('stop',store)
        report['restaurado']=not cleanup and shared()==before_shared
        (directory/'evidencia.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        client.open=original_open
        print('Evidencia:',directory/'evidencia.json',flush=True)
        assert report['restaurado'],'No se confirmó la restauración del laboratorio'


if __name__=='__main__':main()
