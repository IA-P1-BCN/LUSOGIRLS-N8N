"""HU-13: CSV HTTP autenticado → PF-12 → API real → Mailpit.

Cada corrida conserva sus bases/volúmenes, apaga sus contenedores y desactiva sus
workflows. No modifica la tienda compartida ni sus datos.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import copy
import csv
import hashlib
import io
import json
import shutil
import subprocess
import time
import uuid

from lab import ROOT, STATE, SECRET, request, client, prepare_credentials, install, export, execution_data
from test_08 import activate, executions, webhook

HEADER = ['terminal_id','operacion_id','fecha','tipo','concepto','importe','moneda','venta_id']
DAY = str(datetime.now(ZoneInfo('Europe/Madrid')).date() - timedelta(days=1))
API = 'http://127.0.0.1:28000'


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def docker(*args):
    result = subprocess.run(['docker', *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def shared_runtime():
    data = json.loads(docker('inspect', 'lusogirls-pruebas-tienda-1'))[0]
    return {'id':data['Id'],'mounts':data['Mounts'],'running':data['State']['Running'],'started':data['State']['StartedAt']}


def api(path, data=None):
    return request(path, data, base=API, headers={'X-API-Key':SECRET})


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
    database = 'qa_datafono_' + token
    directory = STATE / database
    directory.mkdir()
    source_dir = directory / 'fuente'
    source_dir.mkdir()
    shutil.copyfile(Path(__file__).with_name('datafono_source.py'), source_dir/'source.py')
    (source_dir/'cobros.csv').write_text(';'.join(HEADER)+'\n')
    store, source = database+'_tienda', database+'_fuente'
    private_env = directory/'.env.local'
    private_env.touch(mode=0o600)
    private_env.write_text('API_KEY='+SECRET+'\nDB_PATH=/data/tienda.db\nSEED=0\nTZ=Europe/Madrid\nN8N_WEBHOOK_URL=\nSTORE_URL=http://'+store+':8000\n')
    compose = ['compose','--env-file',str(ROOT/'tests/n8n/.env.local'),'-f',str(ROOT/'tests/n8n/compose.yml')]
    def sql(query, db=database):
        return docker(*compose,'exec','-T','registro','psql','-U','n8n','-d',db,'-At','-v','ON_ERROR_STOP=1','-c',query)
    def config(key, value):
        sql('INSERT INTO pf_config VALUES('+quote(key)+','+quote(value)+') ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor')
    before = shared_runtime()
    sql('CREATE DATABASE '+database, 'automatizaciones')
    sql((ROOT/'infra/registro.sql').read_text())
    sql((ROOT/'infra/12-datafono.sql').read_text())
    config('API_BASE_URL','http://'+store+':8000')
    config('DATAFONO_CSV_URL','http://'+source+':8080/cobros-{fecha}.csv')
    pg = request('/rest/credentials',{'name':'PF · Registro auxiliar · '+database,'type':'postgres','data':{
        'host':'registro','port':5432,'database':database,'user':'n8n','password':SECRET,'ssl':'disable','sshTunnel':False}})['data']
    src_cred = request('/rest/credentials',{'name':'PF · Fuente datáfono · '+database,'type':'httpHeaderAuth','data':{'name':'X-API-Key','value':SECRET}})['data']
    def local_flow(path, trigger=False):
        flow = json.loads(Path(path).read_text())
        for n in flow['nodes']:
            if 'postgres' in n.get('credentials',{}):n['credentials']['postgres']={'id':pg['id'],'name':pg['name']}
            if n.get('credentials',{}).get('httpHeaderAuth',{}).get('name')=='PF · Fuente datáfono':
                n['credentials']['httpHeaderAuth']={'id':src_cred['id'],'name':src_cred['name']}
        if trigger:
            for n in list(flow['nodes']):
                if n['type'].split('.')[-1] in ('scheduleTrigger','manualTrigger'):
                    flow['nodes'].remove(n);flow['connections'].pop(n['name'],None)
            flow['nodes'].append(webhook('Recibir prueba', 'qa-datafono-'+token))
            flow['connections']['Recibir prueba']={'main':[[{'node':'Leer configuración','type':'main','index':0}]]}
        target = directory/Path(path).name
        target.write_text(json.dumps(flow,ensure_ascii=False))
        return target
    def wait_run(flow, prior, timeout=90):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            rows=[r for r in executions(flow['id']) if r['id'] not in prior and r['status'] in ('success','error','crashed')]
            if rows:return rows[0]
            time.sleep(.4)
        raise AssertionError('No terminó la ejecución de PF-12')
    def output(run, name):
        return execution_data(run['id'])['resultData']['runData'][name][0]['data']['main'][0][0]['json']
    def write_rows(rows):
        out=io.StringIO();writer=csv.writer(out,delimiter=';',lineterminator='\n')
        writer.writerow(HEADER);writer.writerows(rows)
        (source_dir/'cobros.csv').write_text(out.getvalue())
    def row(op, amount='39,90', kind='venta', concept='Zapatos', sale_id='', currency='EUR'):
        return ['TPV01',op,DAY,kind,concept,amount,currency,str(sale_id)]
    flows, containers, evidence = [], [], []
    report={'fecha':DAY,'registro':database,'casos':evidence,'restaurado':False}
    report_file=directory/'evidencia.json'
    def save(case, run, **extra):
        item={'caso':case,'ejecucion':run['id'],'resultado':'PASS',**extra}
        evidence.append(item);report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps(item,ensure_ascii=False),flush=True)
    try:
        for name, args in [
            (store,['-p','127.0.0.1:28000:8000','-v',database+'_tienda:/data','-v',str(ROOT/'backend')+':/srv/backend:ro','-v',str(ROOT/'frontend')+':/srv/frontend:ro','paso-firme-tienda:latest']),
            (source,['-v',str(source_dir)+':/qa','paso-firme-tienda:latest','python','/qa/source.py']),
        ]:
            docker('run','-d','--name',name,'--network','lusogirls-pruebas_default','--env-file',str(private_env),*args)
            containers.append(name)
        for attempt in range(60):
            try:api('/api/ventas');break
            except Exception:time.sleep(.5)
        else:raise AssertionError('No arrancó la tienda aislada')
        error=install(local_flow(ROOT/'workflows/08-errores.json'));flows.append(error);activate(error)
        flow=install(local_flow(ROOT/'workflows/12-ventas-datafono.json',True),error['id']);flows.append(flow);activate(flow)
        for installed in [error,flow]:
            assert all(n['credentials']['postgres']['id']==pg['id'] for n in installed['nodes'] if 'postgres' in n.get('credentials',{}))
        download=next(n for n in flow['nodes'] if n['name']=='Descargar CSV del datáfono')
        assert download['credentials']['httpHeaderAuth']['id']==src_cred['id']
        endpoint='/webhook/qa-datafono-'+token
        def run_case(rows=None, expected_status='success'):
            if rows is not None:write_rows(rows)
            prior={r['id'] for r in executions(flow['id'])}
            request(endpoint,{})
            run=wait_run(flow,prior)
            if run['status']!=expected_status:
                data=execution_data(run['id'])['resultData']
                print(json.dumps({'ejecucion':run['id'],'ultimo_paso':data.get('lastNodeExecuted'),'error':data.get('error',{}).get('message','')[:250]},ensure_ascii=False),flush=True)
            assert run['status']==expected_status, 'Estado de ejecución inesperado'
            return run

        run=run_case([row('A'),row('B'),row('A')])
        result=output(run,'Redactar resultado del datáfono')['resumen']
        assert (result['nuevas'],result['duplicados'],result['revision'])==(2,1,0),result
        assert len(api('/api/ventas'))==2
        save('dos ventas iguales con referencias distintas y fila repetida',run,resumen=result)

        run=run_case([row('B'),row('A')])
        result=output(run,'Redactar resultado del datáfono')['resumen']
        assert (result['nuevas'],result['existentes'],result['revision'])==(0,2,0),result
        assert len(api('/api/ventas'))==2
        save('segunda importación reordenada sin duplicados',run,resumen=result)

        manual=api('/api/ventas',{'fecha':DAY,'concepto':'Zapatos manuales','importe':25,'forma_pago':'tarjeta'})
        run=run_case([row('C','25',concept='Zapatos manuales')])
        assert output(run,'Redactar resultado del datáfono')['resumen']['revision']==1
        assert len(api('/api/ventas'))==3
        save('posible venta manual: retenida sin crear',run)

        run=run_case([row('C','25',concept='Zapatos manuales',sale_id=manual['id'])])
        result=output(run,'Redactar resultado del datáfono')['resumen']
        assert (result['existentes'],result['revision'])==(1,0),result
        assert len(api('/api/ventas'))==3
        save('venta manual identificada sin duplicar',run)

        run=run_case([row('D','25',concept='Zapatos manuales',sale_id=manual['id'])])
        assert output(run,'Redactar resultado del datáfono')['resumen']['revision']==1
        assert len(api('/api/ventas'))==3
        save('otra referencia no puede reutilizar la misma venta manual',run)

        run=run_case([row('A','40')])
        assert output(run,'Redactar resultado del datáfono')['resumen']['revision']==1
        assert len(api('/api/ventas'))==3
        save('referencia confirmada con importe cambiado: sin escritura',run)

        run=run_case([row('E',kind='abono'),row('F',kind='devolucion'),row('G',currency='USD'),row('H','-1'),row('I','1.842'),row('J'),row('J','99')])
        assert output(run,'Redactar resultado del datáfono')['resumen']['revision']==6
        assert len(api('/api/ventas'))==3
        save('filas inválidas y referencia conflictiva sin escritura',run)

        run=run_case([])
        assert output(run,'Redactar resultado del datáfono')['resumen']['nuevas']==0
        save('CSV vacío válido con informe',run)

        (source_dir/'cobros.csv').write_text('cabecera;incorrecta\n')
        prior_error={r['id'] for r in executions(error['id'])}
        run=run_case(expected_status='error')
        handled=wait_run(error,prior_error)
        assert handled['status']=='success'
        assert len(api('/api/ventas'))==3
        save('cabecera inválida rechazada y avisada por PF-08',run,pf08=handled['id'])

        config('API_BASE_URL','http://'+source+':8080')
        (source_dir/'respuesta-incierta').touch()
        run=run_case([row('K','18,50')])
        assert output(run,'Redactar resultado del datáfono')['resumen']['revision']==1
        assert len(api('/api/ventas'))==4
        assert len((source_dir/'posts.jsonl').read_text().splitlines())==1
        save('respuesta perdida tras crear: revisión, un solo POST',run)
        run=run_case([row('K','18,50')])
        result=output(run,'Redactar resultado del datáfono')['resumen']
        assert (result['existentes'],result['revision'])==(1,0),result
        assert len(api('/api/ventas'))==4
        assert len((source_dir/'posts.jsonl').read_text().splitlines())==1
        save('conciliación por referencia tras respuesta incierta: sin segundo POST',run)

        config('API_BASE_URL','http://'+store+':8000')
        write_rows([row('L','12,50')])
        prior={r['id'] for r in executions(flow['id'])}
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _:request(endpoint,{}),range(2)))
        one=wait_run(flow,prior)
        two=wait_run(flow,prior|{one['id']})
        assert one['status']==two['status']=='success'
        assert len(api('/api/ventas'))==5
        save('dos ejecuciones concurrentes: una sola venta',one,segunda=two['id'])

        # Prueba del Schedule Trigger real con cadencia de un minuto solo en una copia.
        write_rows([row('M','13,50')])
        path=local_flow(ROOT/'workflows/12-ventas-datafono.json')
        timed=json.loads(path.read_text())
        for n in timed['nodes']:
            if n['type'].endswith('.scheduleTrigger'):n['parameters']['rule']['interval'][0]['expression']='* * * * *'
        timed['nodes']=[n for n in timed['nodes'] if not n['type'].endswith('.manualTrigger')]
        timed['connections'].pop('Iniciar comprobación manual',None)
        path.write_text(json.dumps(timed,ensure_ascii=False))
        scheduled=install(path,error['id']);flows.append(scheduled)
        activate(scheduled)
        print('Esperando el Schedule Trigger de la copia de prueba (máximo 90 s).',flush=True)
        run=wait_run(scheduled,set(),timeout=90)
        request('/rest/workflows/'+scheduled['id']+'/deactivate',{})
        assert run['status']=='success' and len(api('/api/ventas'))==6
        save('Schedule Trigger real (cadencia acelerada solo en prueba)',run)

        # Importar/exportar la versión entregable sin alterar sus disparadores ni horario.
        final=install(local_flow(ROOT/'workflows/12-ventas-datafono.json'),error['id']);flows.append(final)
        target=ROOT/'workflows/12-ventas-datafono.json'
        expected=json.loads(target.read_text())
        export(final['id'],target)
        actual=json.loads(target.read_text())
        assert actual['nodes']==expected['nodes'] and actual['connections']==expected['connections']
        assert not actual['active'] and not actual['pinData']
        report['workflow_exportado']={'id':final['id'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    finally:
        for flow in reversed(flows):
            try:request('/rest/workflows/'+flow['id']+'/deactivate',{})
            except Exception:pass
        for name in reversed(containers):docker('stop',name)
        report['restaurado']=before==shared_runtime()
        report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2))
        client.open=original_open
        assert report['restaurado'],'La tienda compartida cambió durante la prueba'
        print('Evidencia:',report_file,flush=True)


if __name__=='__main__':
    main()
