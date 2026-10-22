"""Ejecutar mediante el laboratorio de PF-08; no modifica la tienda habitual."""
from pathlib import Path
import json,copy
from lab import ROOT,STATE,login,prepare_credentials,fixture_flow,invoke,sql,request,message_count,install,export,execution_data
from test_08 import activate

path=Path(__file__).resolve().parents[2]/'workflows/07-informe-mensual.json'
login();prepare_credentials()
error_id=(STATE/'error-id.txt').read_text();activate(request('/rest/workflows/'+error_id)['data'])
sql("UPDATE pf_config SET valor='http://simulador:8080' WHERE clave='API_BASE_URL'")
cases=[c for c in json.loads((ROOT/'data/pruebas/contratos.json').read_text())['cases'] if c['flow']=='PF-07']
cases.append({'id':'F07-fallo-fuente','input':{**copy.deepcopy(cases[0]['input']),'vales_response':{'status':503}},'expected':{'error':True}})
evidence=[]
try:
    for case in cases:
        sql("DELETE FROM pf_registro WHERE tipo='informe_mensual'")
        request('/__fixture',case['input'],base='http://127.0.0.1:18080')
        flow,endpoint=fixture_flow(path,error_id,case['input']['hoy'])
        try:
            run=invoke(flow,endpoint,{})
            if case['expected'].get('error'):
                assert run['status']=='error'
                assert sql("SELECT count(*) FROM pf_registro WHERE tipo='informe_mensual'")=='0'
                calls=request('/__calls',base='http://127.0.0.1:18080')
                assert len([c for c in calls if c['path']=='/api/vales'])==3
            else:
                assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
                doc=json.loads(sql("SELECT documento FROM pf_registro WHERE tipo='informe_mensual'"))
                for k,v in case['expected'].items():assert doc[k]==v,(k,doc[k],v)
                assert 'no histórico' in doc['texto'] and case['input']['hoy'] in doc['pendiente_medido_en']
                before=message_count();duplicate=invoke(flow,endpoint,{})
                assert duplicate['status']=='success' and message_count()==before
                calls=request('/__calls',base='http://127.0.0.1:18080')
                assert all(c['method']=='GET' for c in calls)
                assert all(not c['query'] for c in calls if c['path'] in ('/api/apartados','/api/vales'))
                assert sql("SELECT count(*) FROM pf_registro WHERE tipo='informe_mensual'")=='1'
            evidence.append({'caso':case['id'],'ejecucion':run['id'],'resultado':'PASS'});print(json.dumps(evidence[-1]))
        finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    sql("DELETE FROM pf_registro WHERE tipo='informe_mensual'")
    flow,endpoint=fixture_flow(path,error_id)
    try:
        run=invoke(flow,endpoint,{})
        assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
        doc=json.loads(sql("SELECT documento FROM pf_registro WHERE tipo='informe_mensual'"))
        evidence.append({'caso':'API real semilla','ejecucion':run['id'],'documento':{k:v for k,v in doc.items() if k not in ('texto','destinatario','remitente','asunto')},'resultado':'PASS'});print(json.dumps(evidence[-1]))
    finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    original=install(path,error_id);export(original['id'],path)
    (STATE/'07-evidencia.json').write_text(json.dumps(evidence,indent=2))
finally:
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    request('/rest/workflows/'+error_id+'/deactivate',{})
