"""Contrato bancario contra API real aislada; IA simulada o OpenRouter elegido."""
from pathlib import Path
from email import policy
from email.parser import BytesParser
import json,uuid,subprocess,time,os
from lab import ROOT,STATE,SECRET,ENV,login,prepare_credentials,fixture_flow,invoke,sql,request,message_count,install,export,execution_data
from test_08 import activate

root=Path(__file__).resolve().parents[2]
live=os.environ.get('PF_TEST_OPENROUTER')=='1'
login();prepare_credentials()
if live:
    assert 'PF · Modelo extracción' in json.loads((STATE/'credentials.json').read_text()),'Falta credencial del modelo'
prefix='qa-pagos-'+uuid.uuid4().hex
override=STATE/'tienda-pagos.json'
override.write_text(json.dumps({'services':{'tienda':{'environment':{'DB_PATH':'/data/'+prefix+'.db'},'volumes':[str(root/'backend')+':/srv/backend:ro',str(root/'frontend')+':/srv/frontend:ro']}}}))
compose=['docker','compose','--env-file',str(ROOT/'tests/n8n/.env.local'),'-f',str(ROOT/'tests/n8n/compose.yml')]
subprocess.run(compose+['-f',str(override),'up','-d','tienda'],check=True,capture_output=True)
for attempt in range(50):
    try:request('/api/apartados',base='http://127.0.0.1:18000',headers={'X-API-Key':SECRET});break
    except Exception:time.sleep(.3)
sql((root/'infra/03-pagos.sql').read_text())
sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
sql("UPDATE pf_config SET valor='"+prefix+"' WHERE clave='CUENTA_BUZON'")
error_id=(STATE/'error-id.txt').read_text();activate(request('/rest/workflows/'+error_id)['data'])
flow,endpoint=fixture_flow(root/'workflows/03-abonos-distancia.json',error_id,model_mock=not live)
fixtures=[
    (1,'CARMEN RUIZ GARCIA',10,'zuecos','bizum',None,1),
    (2,'JORGE M.',20,'apartado 2 bota','bizum',2,2),
    (3,'LUCIA GOMEZ PEREZ',12,'Liquidar mocasines','transferencia',None,3),
    (4,'LAURA O.',15,'deportivas','bizum',None,None),
    (5,'ROMERO D.',10,None,'bizum',None,None),
    (6,'PAULA RAMOS LEON',20,'zapatillas running perdón por el retraso','bizum',None,None),
    (7,'ANTONIO FERNANDEZ SOTO',25,'botas','transferencia',None,None),
    (8,None,None,None,None,None,None),
    (9,'SILVIA CORTES',5,'abono sandalias','bizum',None,24),
]
evidence=[]
def api(path):return request(path,base='http://127.0.0.1:18000',headers={'X-API-Key':SECRET})
def extract(f):return dict(zip(['es_pago','ordenante','importe','concepto','medio','apartado_id'],[f[0]!=8,*f[1:6]]))
def payload(file):
    mail=BytesParser(policy=policy.default).parsebytes(file.read_bytes())
    text=mail.get_payload(decode=True).decode(mail.get_content_charset() or 'utf-8')
    return {'subject':str(mail['subject']),'textPlain':text,'metadata':{'message-id':'<'+file.stem+'@pruebas.example.test>'}}
try:
    for f in fixtures:
        file=next((ROOT/'data/correos').glob(f'{f[0]:02d}_*.eml'));mail=payload(file)
        # Extraídos esperados para el doble IA, definidos antes de ejecutar el flujo.
        request('/__fixture',{'extraction':extract(f)},base='http://127.0.0.1:18080')
        before=api('/api/abonos');before_messages=message_count()
        run=invoke(flow,endpoint,mail)
        assert run['status']=='success',(f[0],run['id'],execution_data(run['id']).get('resultData',{}).get('lastNodeExecuted'))
        after=api('/api/abonos');new=[a for a in after if a['id'] not in {b['id'] for b in before}]
        if f[6]:
            assert len(new)==1 and new[0]['apartado_id']==f[6] and new[0]['importe']==f[2] and new[0]['forma_pago']==f[4],new
            if f[0]==3:assert api('/api/apartados/3')['estado']=='liquidado'
        else:
            assert not new
            assert message_count()==before_messages+(0 if f[0]==8 else 1)
        evidence.append({'caso':f'F03-{f[0]:02d}','ejecucion':run['id'],'abonos_nuevos':len(new),'modelo':'OpenRouter real' if live else 'doble IA','resultado':'PASS'});print(json.dumps(evidence[-1]),flush=True)
        if live:time.sleep(3)
    before=api('/api/abonos')
    mail=payload(next((ROOT/'data/correos').glob('01_*.eml')))
    request('/__fixture',{'extraction':extract(fixtures[0])},base='http://127.0.0.1:18080')
    run=invoke(flow,endpoint,mail)
    assert run['status']=='success' and api('/api/abonos')==before
    evidence.append({'caso':'F03-10 repetición','ejecucion':run['id'],'resultado':'PASS'});print(json.dumps(evidence[-1]),flush=True)
    if not live:
        mail['metadata']['message-id']='<invalid-json@pruebas.example.test>'
        request('/__fixture',{'llm_content':'No es JSON'},base='http://127.0.0.1:18080')
        run=invoke(flow,endpoint,mail)
        assert run['status']=='error' and api('/api/abonos')==before
        evidence.append({'caso':'F03-11 IA inválida','ejecucion':run['id'],'resultado':'PASS'});print(json.dumps(evidence[-1]),flush=True)
        new=request('/api/apartados',{'cliente':'Cliente Prueba','producto':'Prueba','precio':20,'abono_inicial':5},base='http://127.0.0.1:18000',headers={'X-API-Key':SECRET})
        amount={'es_pago':True,'ordenante':'CLIENTE PRUEBA','importe':1,'concepto':'apartado '+str(new['id']),'medio':'bizum','apartado_id':new['id']}
        mail={'subject':'Bizum recibido','textPlain':'Importe: 1,00 EUR\nOrdenante: CLIENTE PRUEBA\nConcepto: apartado '+str(new['id']),'metadata':{'message-id':'<timeout@pruebas.example.test>'}}
        request('/__fixture',{'extraction':amount,'proxy_tienda':True,'timeout_after_post':True},base='http://127.0.0.1:18080')
        sql("UPDATE pf_config SET valor='http://simulador:8080' WHERE clave='API_BASE_URL'")
        run=invoke(flow,endpoint,mail)
        assert run['status']=='error'
        assert len(api('/api/apartados/'+str(new['id']))['abonos'])==2
        repeat=invoke(flow,endpoint,mail)
        assert repeat['status']=='success' and len(api('/api/apartados/'+str(new['id']))['abonos'])==2
        assert sql('SELECT count(*) FROM pf_bloqueos_apartado WHERE apartado_id='+str(new['id']))=='1'
        evidence.append({'caso':'Timeout después de POST','ejecucion':run['id'],'repeticion':repeat['id'],'abonos_nuevos':1,'resultado':'PASS'});print(json.dumps(evidence[-1]),flush=True)
    original=install(root/'workflows/03-abonos-distancia.json',error_id);export(original['id'],root/'workflows/03-abonos-distancia.json')
    (STATE/('03-live-evidencia.json' if live else '03-evidencia.json')).write_text(json.dumps(evidence,indent=2))
finally:
    request('/rest/workflows/'+flow['id']+'/deactivate',{})
    request('/rest/workflows/'+error_id+'/deactivate',{})
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    subprocess.run(compose+['up','-d','tienda'],check=True,capture_output=True)
