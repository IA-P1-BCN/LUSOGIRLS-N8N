"""Cliente del laboratorio aislado. No utiliza la sesión ni claves del n8n habitual."""
import http.cookiejar
import json
from pathlib import Path
import urllib.request
import urllib.error
import subprocess
import uuid
import time

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(__file__).with_name('.estado')
STATE.mkdir(exist_ok=True)
ENV = dict(line.split('=',1) for line in Path(__file__).with_name('.env.local').read_text().splitlines() if '=' in line)
SECRET = ENV['PF_TEST_SECRET']
cookies = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

def request(path, data=None, method=None, base='http://127.0.0.1:15678', headers=None):
    req=urllib.request.Request(base+path, data=None if data is None else json.dumps(data).encode(), method=method, headers={'Content-Type':'application/json',**(headers or {})})
    with client.open(req,timeout=60) as response:
        raw=response.read()
        return json.loads(raw) if raw else None

def login():
    details={'email':'qa@example.test','password':SECRET+'Aa1!'}
    try:
        request('/rest/owner/setup',{**details,'firstName':'Pruebas','lastName':'LUSOGIRLS'})
    except urllib.error.HTTPError as error:
        if error.code not in (400,403): raise
    request('/rest/login',{'emailOrLdapLoginId':details['email'],'password':details['password']})

def prepare_credentials():
    specs={
        'postgres':('PF · Registro auxiliar',{'host':'registro','port':5432,'database':'automatizaciones','user':'n8n','password':SECRET,'ssl':'disable','sshTunnel':False}),
        'smtp':('PF · Notificaciones',{'host':'correo','port':1025,'secure':False,'disableStartTls':True}),
        'httpHeaderAuth':('PF · API tienda',{'name':'X-API-Key','value':SECRET}),
    }
    existing=request('/rest/credentials')['data']
    result={}
    for kind,(name,data) in specs.items():
        found=next((c for c in existing if c['name']==name and c['type']==kind),None)
        if found is None: found=request('/rest/credentials',{'name':name,'type':kind,'data':data})['data']
        result[kind]={'id':found['id'],'name':name}
    (STATE/'credentials.json').write_text(json.dumps(result))
    return result

def install(path, error_id=None):
    flow=json.loads(Path(path).read_text())
    creds=json.loads((STATE/'credentials.json').read_text())
    for node in flow['nodes']:
        for kind in node.get('credentials',{}): node['credentials'][kind]=creds[kind]
    if error_id: flow['settings']['errorWorkflow']=error_id
    flow.pop('id',None)
    return request('/rest/workflows',flow)['data']

def export(flow_id,path):
    flow=request('/rest/workflows/'+flow_id)['data']
    clean={k:flow[k] for k in ('name','nodes','connections','settings')}
    clean.update(active=False,pinData={})
    clean['settings'].pop('errorWorkflow',None)
    for node in clean['nodes']:
        for cred in node.get('credentials',{}).values(): cred.pop('id',None)
    Path(path).write_text(json.dumps(clean,ensure_ascii=False,indent=2)+'\n')

def sql(query):
    command=['docker','compose','--env-file',str(ROOT/'tests/n8n/.env.local'),'-f',str(ROOT/'tests/n8n/compose.yml'),'exec','-T','registro','psql','-U','n8n','-d','automatizaciones','-At','-v','ON_ERROR_STOP=1','-c',query]
    result=subprocess.run(command,check=True,capture_output=True,text=True)
    return result.stdout.strip()

def fixture_flow(path,error_id=None):
    from test_08 import webhook, activate
    flow=json.loads(Path(path).read_text())
    triggers=[n for n in flow['nodes'] if n['type'].split('.')[-1] in ('errorTrigger','scheduleTrigger','executeWorkflowTrigger','manualTrigger','emailReadImap')]
    trigger=triggers[0]
    for other in triggers[1:]:
        flow['nodes'].remove(other); flow['connections'].pop(other['name'],None)
    old_name=trigger['name']; hook=webhook(old_name,'qa-'+uuid.uuid4().hex)
    flow['nodes'][flow['nodes'].index(trigger)]=hook
    unwrap={'id':str(uuid.uuid4()),'name':'Entrada de prueba','type':'n8n-nodes-base.code','typeVersion':2,'position':[120,0],'parameters':{'jsCode':'return [{json:$input.first().json.body}];'}}
    flow['nodes'].append(unwrap)
    flow['connections'][unwrap['name']]=flow['connections'][old_name]
    flow['connections'][old_name]={'main':[[{'node':unwrap['name'],'type':'main','index':0}]]}
    file=STATE/(uuid.uuid4().hex+'.json'); file.write_text(json.dumps(flow))
    installed=install(file,error_id)
    activate(installed)
    return installed,hook['parameters']['path']

def invoke(flow,path,payload):
    from test_08 import executions, finished
    previous=[e['id'] for e in executions(flow['id'])]
    request('/webhook/'+path,payload)
    return finished(flow['id'],previous)

def message_count():
    return request('/api/v1/messages',base='http://127.0.0.1:18025')['total']

if __name__=='__main__':
    import sys
    if len(sys.argv)>1:
        import runpy
        path=Path(sys.argv[1]) if '/' in sys.argv[1] else Path(__file__).with_name('test_'+sys.argv[1]+'.py')
        runpy.run_path(str(path),run_name='__main__')
    else:
        login()
        prepare_credentials()
        print('Acceso al laboratorio y 3 credenciales locales preparados; valores secretos omitidos.')
