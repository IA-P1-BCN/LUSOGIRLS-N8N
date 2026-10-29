"""Comprueba que el adaptador IMAP procesa cada item, incluso un lote de correos."""
import json,uuid,time,urllib.error
from pathlib import Path
from lab import ROOT,STATE,login,prepare_credentials,request,install,sql
from test_08 import activate,webhook,executions

root=Path(__file__).resolve().parents[2]
login();prepare_credentials()
flow=json.loads((root/'workflows/03-abonos-distancia.json').read_text())
# Solo se reemplazan la entrada IMAP y el proveedor externo para esta prueba de lote.
for index,n in enumerate(flow['nodes']):
    if n['type']=='n8n-nodes-base.emailReadImap':
        hook=webhook(n['name'],'qa-lote-'+uuid.uuid4().hex);flow['nodes'][index]=hook
    if n['name']=='Extraer pago':
        n['parameters']['url']='http://simulador:8080/chat/completions'
        n['parameters'].pop('authentication',None);n['parameters'].pop('genericAuthType',None);n['parameters'].pop('nodeCredentialType',None);n.pop('credentials',None)
unpack={'id':str(uuid.uuid4()),'name':'Desempaquetar lote ficticio','type':'n8n-nodes-base.code','typeVersion':2,'position':[0,0],'parameters':{'jsCode':'return $input.first().json.body.correos.map(json=>({json}));'}}
flow['nodes'].append(unpack)
flow['connections'][hook['name']]={'main':[[{'node':unpack['name'],'type':'main','index':0}]]}
flow['connections'][unpack['name']]={'main':[[{'node':'Procesar cada correo del lote','type':'main','index':0}]]}
file=STATE/'03-lote.json';file.write_text(json.dumps(flow))
installed=install(file);activate(installed)
try:
    request('/__fixture',{'extraction':{'es_pago':False}},base='http://127.0.0.1:18080')
    emails=[{'subject':'Publicidad','textPlain':'Promoción ficticia, ningún pago','metadata':{'message-id':f'<lote-{i}@example.test>'}} for i in range(2)]
    for attempt in range(5):
        try:
            request('/webhook/'+hook['parameters']['path'],{'correos':emails});break
        except urllib.error.HTTPError as error:
            if error.code!=404 or attempt==4:raise
            time.sleep(2)  # 404: el webhook todavía no se registró; no hubo ejecución.
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        runs=executions(installed['id'])
        if len(runs)>=3 and all(r['status']=='success' for r in runs):break
        if any(r['status']=='error' for r in runs):break
        time.sleep(.3)
    assert len(runs)==3 and all(r['status']=='success' for r in runs),[(r['id'],r['status']) for r in runs]
    calls=request('/__calls',base='http://127.0.0.1:18080')
    assert len([c for c in calls if c['path']=='/chat/completions'])==2
    print(json.dumps({'caso':'Lote de dos correos','ejecuciones':[r['id'] for r in runs],'extracciones':2,'resultado':'PASS'}))
finally:request('/rest/workflows/'+installed['id']+'/deactivate',{})
