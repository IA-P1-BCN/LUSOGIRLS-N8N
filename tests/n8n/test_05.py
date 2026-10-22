"""Ejecutar mediante tests/n8n/lab.py de la PR de PF-08."""
from pathlib import Path
from datetime import date,timedelta
import json
from lab import ROOT,STATE,login,prepare_credentials,fixture_flow,invoke,sql,request,message_count,install,export,execution_data,SECRET
from test_08 import activate

path=Path(__file__).resolve().parents[2]/'workflows/05-cierre-diario.json'
login();prepare_credentials()
error_id=(STATE/'error-id.txt').read_text()
error=request('/rest/workflows/'+error_id)['data'];activate(error)
sql("UPDATE pf_config SET valor='http://simulador:8080' WHERE clave='API_BASE_URL'")
cases=[c for c in json.loads((ROOT/'data/pruebas/contratos.json').read_text())['cases'] if c['flow']=='PF-05']
evidence=[]
try:
    for case in cases:
        source=case['input'];day=source['fecha_cierre']
        sql("DELETE FROM pf_registro WHERE clave='cierre:"+day+"'")
        request('/__fixture',source,base='http://127.0.0.1:18080')
        flow,endpoint=fixture_flow(path,error_id,str(date.fromisoformat(day)+timedelta(days=1)))
        try:
            run=invoke(flow,endpoint,{})
            if case['id']=='F05-03':
                assert run['status']=='error',run
                assert sql("SELECT count(*) FROM pf_registro WHERE clave='cierre:"+day+"'")=='0'
                calls=request('/__calls',base='http://127.0.0.1:18080')
                assert len([c for c in calls if c['path']=='/api/abonos'])==3
            else:
                assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
                doc=json.loads(sql("SELECT documento FROM pf_registro WHERE clave='cierre:"+day+"'"))
                for key,expected in case['expected'].items():
                    if key not in ('closure_rows','marisa_messages'):assert doc[key]==expected,(key,doc[key],expected)
                assert sql("SELECT estado FROM pf_registro WHERE clave='cierre:"+day+"'")=='confirmado'
                before=message_count();duplicate=invoke(flow,endpoint,{})
                assert duplicate['status']=='success' and message_count()==before
                calls=request('/__calls',base='http://127.0.0.1:18080')
                assert all(c['method']=='GET' and c['query']=={'desde':[day],'hasta':[day]} for c in calls)
                assert sql("SELECT count(*) FROM pf_registro WHERE clave='cierre:"+day+"'")=='1'
            evidence.append({'caso':case['id'],'ejecucion':run['id'],'resultado':'PASS'})
            print(json.dumps(evidence[-1]))
        finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    # Además del doble HTTP, conexión real contra la tienda aislada con semilla.
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    day=str(date.today()-timedelta(days=1));sql("DELETE FROM pf_registro WHERE clave='cierre:"+day+"'")
    flow,endpoint=fixture_flow(path,error_id)
    try:
        run=invoke(flow,endpoint,{})
        assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
        from decimal import Decimal
        totals={}
        for kind in ('ventas','abonos'):
            rows=request('/api/'+kind+'?desde='+day+'&hasta='+day,base='http://127.0.0.1:18000',headers={'X-API-Key':SECRET})
            totals[kind]=sum(int(Decimal(str(r['importe']))*100) for r in rows)
        doc=json.loads(sql("SELECT documento FROM pf_registro WHERE clave='cierre:"+day+"'"))
        assert doc['ventas_centimos']==totals['ventas'] and doc['abonos_centimos']==totals['abonos']
        evidence.append({'caso':'API real semilla','ejecucion':run['id'],'totales':totals,'resultado':'PASS'});print(json.dumps(evidence[-1]))
    finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    original=install(path,error_id);export(original['id'],path)
    (STATE/'05-evidencia.json').write_text(json.dumps(evidence,indent=2))
finally:
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    request('/rest/workflows/'+error_id+'/deactivate',{})
