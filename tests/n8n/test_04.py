"""Contrato PF-04 y recorrido real Webhook PF-00 → subworkflow → SMTP local."""
from pathlib import Path
import json,time,concurrent.futures
from lab import ROOT,STATE,login,prepare_credentials,invoke,sql,request,message_count,install,export,execution_data
from test_08 import activate,executions,finished

root=Path(__file__).resolve().parents[2]
login();prepare_credentials()
error_id=(STATE/'error-id.txt').read_text();activate(request('/rest/workflows/'+error_id)['data'])
child=install(root/'workflows/04-venta-grande.json',error_id);activate(child)
router=install(root/'workflows/00-entrada-eventos.json',error_id);activate(router)
sql("INSERT INTO pf_config VALUES ('PF04_WORKFLOW_ID','"+child['id']+"') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor")
sql("DELETE FROM pf_registro WHERE clave LIKE 'venta.registrada:91%'")
cases=[c for c in json.loads((ROOT/'data/pruebas/contratos.json').read_text())['cases'] if c['flow']=='PF-04']
evidence=[]
try:
    for case in cases:
        threshold=case['input']['variables'].get('UMBRAL_VENTA_GRANDE')
        if threshold is None:sql("DELETE FROM pf_config WHERE clave='UMBRAL_VENTA_GRANDE'")
        else:sql("INSERT INTO pf_config VALUES('UMBRAL_VENTA_GRANDE','"+str(threshold)+"') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor")
        before=message_count();run=invoke(router,'tienda',case['input']['payload'])
        if threshold is None:
            assert run['status']=='error'
            assert sql("SELECT count(*) FROM pf_registro WHERE clave='venta.registrada:9103'")=='0'
        else:
            assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
            assert message_count()==before+case['expected']['marisa_messages']
            before=message_count();repeat=invoke(router,'tienda',case['input']['payload'])
            assert repeat['status']=='success' and message_count()==before
        evidence.append({'caso':case['id'],'ejecucion_router':run['id'],'resultado':'PASS'});print(json.dumps(evidence[-1]))
    # Cambiar solo pf_config hace que la venta de 100 ahora sí avise.
    sql("INSERT INTO pf_config VALUES('UMBRAL_VENTA_GRANDE','99') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor")
    before=message_count();run=invoke(router,'tienda',cases[1]['input']['payload'])
    assert run['status']=='success' and message_count()==before+1
    evidence.append({'caso':'Cambio de variable sin editar nodos','ejecucion_router':run['id'],'resultado':'PASS'});print(json.dumps(evidence[-1]))
    payload=json.loads(json.dumps(cases[0]['input']['payload']));payload['datos']['id']=9199
    before=message_count();previous={e['id'] for e in executions(router['id'])}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _:request('/webhook/tienda',payload),range(2)))
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        runs=[e for e in executions(router['id']) if e['id'] not in previous and e['status']=='success']
        if len(runs)==2:break
        time.sleep(.3)
    assert len(runs)==2 and message_count()==before+1
    assert sql("SELECT count(*) FROM pf_registro WHERE clave='venta.registrada:9199'")=='1'
    evidence.append({'caso':'Dos eventos simultáneos, un aviso','ejecuciones_router':[r['id'] for r in runs],'resultado':'PASS'});print(json.dumps(evidence[-1]))
    before=message_count();run=invoke(router,'tienda',{'evento':'desconocido','datos':{}})
    assert run['status']=='success' and message_count()==before
    export(child['id'],root/'workflows/04-venta-grande.json');export(router['id'],root/'workflows/00-entrada-eventos.json')
    (STATE/'04-evidencia.json').write_text(json.dumps(evidence,indent=2))
finally:
    for flow in (router,child):request('/rest/workflows/'+flow['id']+'/deactivate',{})
    request('/rest/workflows/'+error_id+'/deactivate',{})
