"""Cliente del laboratorio aislado. No utiliza la sesión ni claves del n8n habitual."""
import http.cookiejar
import json
from pathlib import Path
import urllib.request
import urllib.error
import subprocess
import uuid
import time
import secrets

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(__file__).with_name('.estado')
STATE.mkdir(exist_ok=True)
ENV = dict(line.split('=',1) for line in Path(__file__).with_name('.env.local').read_text().splitlines() if '=' in line)
SECRET = ENV['PF_TEST_SECRET']
# Se conserva solo en el .env ignorado; es distinto de la clave de la API.
if not ENV.get('PF_TEST_WEBHOOK_SECRET'):
    ENV['PF_TEST_WEBHOOK_SECRET'] = secrets.token_urlsafe(32)
    with Path(__file__).with_name('.env.local').open('a') as private:
        private.write('\nPF_TEST_WEBHOOK_SECRET=' + ENV['PF_TEST_WEBHOOK_SECRET'] + '\n')
WEBHOOK_SECRET = ENV['PF_TEST_WEBHOOK_SECRET']
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
    saved=STATE/'credentials.json'
    result=json.loads(saved.read_text()) if saved.exists() else {}
    for kind,(name,data) in specs.items():
        found=next((c for c in existing if c['name']==name and c['type']==kind),None)
        if found is None: found=request('/rest/credentials',{'name':name,'type':kind,'data':data})['data']
        result[kind]={'id':found['id'],'name':name}
    result.pop('PF · Modelo extracción',None)
    for credential in existing:
        if credential['name']=='PF · Modelo extracción' and credential['type']=='openRouterApi':
            result[credential['name']]={'id':credential['id'],'name':credential['name']}
    name='PF · Webhook tienda'
    found=next((c for c in existing if c['name']==name and c['type']=='httpHeaderAuth'),None)
    if found is None:
        found=request('/rest/credentials',{'name':name,'type':'httpHeaderAuth',
            'data':{'name':'X-PF-Webhook-Key','value':WEBHOOK_SECRET}})['data']
    result[name]={'id':found['id'],'name':name}
    (STATE/'credentials.json').write_text(json.dumps(result))
    return result

def install(path, error_id=None, retain_test_execution=False):
    flow=json.loads(Path(path).read_text())
    if retain_test_execution:
        flow['settings'].update(saveDataSuccessExecution='all',saveDataErrorExecution='all')
    creds=json.loads((STATE/'credentials.json').read_text())
    for node in flow['nodes']:
        for kind,reference in node.get('credentials',{}).items():
            fallback=creds.get(kind)
            selected=creds.get(reference['name']) or (fallback if fallback and fallback['name']==reference['name'] else None)
            if selected: node['credentials'][kind]=selected
    if error_id: flow['settings']['errorWorkflow']=error_id
    flow.pop('id',None)
    return request('/rest/workflows',flow)['data']

def export(flow_id,path):
    declared=json.loads(Path(path).read_text()) if Path(path).exists() else {}
    names={(node['name'],kind):cred['name'] for node in declared.get('nodes',[]) for kind,cred in node.get('credentials',{}).items()}
    flow=request('/rest/workflows/'+flow_id)['data']
    clean={k:flow[k] for k in ('name','nodes','connections','settings')}
    clean.update(active=False,pinData={})
    clean['settings'].pop('errorWorkflow',None)
    for node in clean['nodes']:
        for kind,cred in node.get('credentials',{}).items():
            cred.pop('id',None)
            # Mantener los nombres compartidos aunque n8n seleccione una credencial local.
            if (node['name'],kind) in names:cred['name']=names[(node['name'],kind)]
    Path(path).write_text(json.dumps(clean,ensure_ascii=False,indent=2)+'\n')

def sql(query):
    command=['docker','compose','--env-file',str(ROOT/'tests/n8n/.env.local'),'-f',str(ROOT/'tests/n8n/compose.yml'),'exec','-T','registro','psql','-U','n8n','-d','automatizaciones','-At','-v','ON_ERROR_STOP=1','-c',query]
    result=subprocess.run(command,check=True,capture_output=True,text=True)
    return result.stdout.strip()

def fixture_flow(path,error_id=None,clock=None,model_mock=False):
    from test_08 import webhook, activate
    flow=json.loads(Path(path).read_text())
    if model_mock:
        for n in flow['nodes']:
            if n['name']=='Extraer pago':
                n['parameters']['url']='http://simulador:8080/chat/completions'
                n['parameters'].pop('authentication',None)
                n['parameters'].pop('genericAuthType',None)
                n['parameters'].pop('nodeCredentialType',None)
                n.pop('credentials',None)
    if clock:
        from datetime import date
        frozen=date.fromisoformat(clock)
        replacement=f"const hoy=$now.setZone('Europe/Madrid').set({{year:{frozen.year},month:{frozen.month},day:{frozen.day},hour:9,minute:0,second:0}});"
        for n in flow['nodes']:
            if n['name']=='Fijar período':
                n['parameters']['jsCode']=n['parameters']['jsCode'].replace("const hoy=$now.setZone('Europe/Madrid');",replacement)
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

def invoke(flow,path,payload,timeout=45):
    from test_08 import executions, finished
    previous=[e['id'] for e in executions(flow['id'])]
    request('/webhook/'+path,payload,headers={'X-PF-Webhook-Key':WEBHOOK_SECRET})
    return finished(flow['id'],previous,timeout=timeout)

def message_count():
    return request('/api/v1/messages',base='http://127.0.0.1:18025')['total']

def execution_data(execution_id):
    raw=request('/rest/executions/'+execution_id)['data']['data']
    if not isinstance(raw,str): return raw
    values=json.loads(raw); memo={}
    def resolve(index):
        if index in memo:return memo[index]
        value=values[index]
        if isinstance(value,dict):
            out={};memo[index]=out
            out.update({k:resolve(int(v)) if isinstance(v,str) and v.isdigit() else v for k,v in value.items()});return out
        if isinstance(value,list):
            out=[];memo[index]=out
            out.extend(resolve(int(v)) if isinstance(v,str) and v.isdigit() else v for v in value);return out
        return value
    return resolve(0)

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
