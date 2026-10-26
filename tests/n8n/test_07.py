"""Ejecutar mediante el laboratorio de PF-08; no modifica la tienda habitual."""
from pathlib import Path
import json,copy
from datetime import datetime,timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from lab import ROOT,STATE,login,prepare_credentials,fixture_flow,invoke,sql,request,message_count,install,export,execution_data,SECRET
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
            messages_before=message_count()
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
                assert message_count()==messages_before+1
                assert sql("SELECT estado FROM pf_registro WHERE tipo='informe_mensual'")=='confirmado'
                before=message_count();duplicate=invoke(flow,endpoint,{})
                assert duplicate['status']=='success' and message_count()==before
                calls=request('/__calls',base='http://127.0.0.1:18080')
                assert all(c['method']=='GET' for c in calls)
                period_calls=[c for c in calls if c['path'] in ('/api/ventas','/api/abonos')]
                assert {c['path'] for c in period_calls}=={'/api/ventas','/api/abonos'}
                expected_query={'desde':[case['expected']['periodo_desde']],'hasta':[case['expected']['periodo_hasta']]}
                assert all(c['query']==expected_query for c in period_calls),period_calls
                assert all(not c['query'] for c in calls if c['path'] in ('/api/apartados','/api/vales'))
                assert sql("SELECT count(*) FROM pf_registro WHERE tipo='informe_mensual'")=='1'
            result={'caso':case['id'],'ejecucion':run['id'],'resultado':'PASS'}
            if not case['expected'].get('error'):
                result.update(repeticion=duplicate['id'],consulta=expected_query,estado='confirmado',mensajes=1)
            evidence.append(result);print(json.dumps(result))
        finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    sql("DELETE FROM pf_registro WHERE tipo='informe_mensual'")
    today=datetime.now(ZoneInfo('Europe/Madrid')).date()
    last_day=today.replace(day=1)-timedelta(days=1)
    first_day=last_day.replace(day=1)
    # El reloj se fija para que un cambio de mes durante la prueba no altere el período.
    flow,endpoint=fixture_flow(path,error_id,str(today))
    try:
        run=invoke(flow,endpoint,{})
        assert run['status']=='success',execution_data(run['id']).get('resultData',{}).get('error',{})
        # Referencia independiente: consultas directas a la API, sin reutilizar el cálculo del flujo.
        totals={}
        for kind in ('ventas','abonos'):
            rows=request('/api/'+kind+'?desde='+str(first_day)+'&hasta='+str(last_day),base='http://127.0.0.1:18000',headers={'X-API-Key':SECRET})
            assert all(str(first_day)<=row['fecha']<=str(last_day) for row in rows)
            totals[kind]=sum(int(Decimal(str(row['importe']))*100) for row in rows)
        doc=json.loads(sql("SELECT documento FROM pf_registro WHERE tipo='informe_mensual'"))
        assert doc['periodo_desde']==str(first_day) and doc['periodo_hasta']==str(last_day)
        assert doc['ventas_centimos']==totals['ventas'],(doc['ventas_centimos'],totals['ventas'])
        assert doc['abonos_centimos']==totals['abonos'],(doc['abonos_centimos'],totals['abonos'])
        assert doc['total_centimos']==totals['ventas']+totals['abonos']
        assert sql("SELECT estado FROM pf_registro WHERE tipo='informe_mensual'")=='confirmado'
        evidence.append({'caso':'API real semilla','ejecucion':run['id'],'periodo_desde':str(first_day),'periodo_hasta':str(last_day),'totales_api_centimos':totals,'total_api_centimos':sum(totals.values()),'estado':'confirmado','documento':{k:v for k,v in doc.items() if k not in ('texto','destinatario','remitente','asunto')},'resultado':'PASS'});print(json.dumps(evidence[-1]))
    finally:request('/rest/workflows/'+flow['id']+'/deactivate',{})
    original=install(path,error_id);export(original['id'],path)
    (STATE/'07-evidencia.json').write_text(json.dumps(evidence,indent=2))
finally:
    sql("UPDATE pf_config SET valor='http://tienda:8000' WHERE clave='API_BASE_URL'")
    request('/rest/workflows/'+error_id+'/deactivate',{})
