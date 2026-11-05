"""Crea ejemplos ficticios por API local; conserva el registro y no reintenta POST."""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='API local de pruebas, sin /api al final')
    parser.add_argument('--registro', type=Path, default=Path('tests/n8n/.estado/demo-presentacion.json'))
    args = parser.parse_args()
    url = args.url.rstrip('/')
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1')
            or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        parser.error('Usar una dirección HTTP local de pruebas sin ruta ni credenciales')
    key = os.environ.get('PF_DEMO_API_KEY')
    if not key:
        parser.error('Falta PF_DEMO_API_KEY en el entorno; no pasar la clave como argumento')
    if args.registro.exists():
        parser.error('El registro ya existe: consultar sus IDs por API; no repetir la carga')

    class NoRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    client = urllib.request.build_opener(NoRedirects())
    report = {'url': url, 'estado': 'iniciando', 'operaciones': []}
    args.registro.parent.mkdir(parents=True, exist_ok=True)
    with args.registro.open('x') as file:
        file.write(json.dumps(report))
    args.registro.chmod(0o600)

    def save():
        args.registro.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    def request(path, payload=None):
        operation = {'ruta': path, 'metodo': 'POST' if payload is not None else 'GET'}
        if payload is not None:
            operation.update(estado='pendiente_de_conciliar',datos_ficticios=payload)
            report['operaciones'].append(operation)
            save()  # Persistir el intento ANTES del efecto; un timeout no permite repetirlo.
        req = urllib.request.Request(url + '/api' + path,
                data=json.dumps(payload).encode() if payload is not None else None,
                headers={'Content-Type':'application/json','X-API-Key':key})
        with client.open(req, timeout=15) as response:
            data=json.load(response)
        if payload is not None:
            operation.update(estado='confirmada',respuesta=data)
            save()
        return data

    today = datetime.now(ZoneInfo('Europe/Madrid')).date()
    common = {'producto':'Zapatos demo', 'talla':'38', 'forma_pago':'efectivo',
              'consentimiento_notificaciones':False}
    try:
        request('/apartados')  # Autenticación antes de crear ejemplos.
        active=request('/apartados',common|{'cliente':'Demo · Apartado activo',
            'email':'demo.activo@example.test','precio':60,'abono_inicial':20})
        paid=request('/apartados',common|{'cliente':'Demo · Apartado liquidado',
            'email':'demo.liquidado@example.test','precio':40,'abono_inicial':10})
        request(f"/apartados/{paid['id']}/abonos",{'importe':30,'forma_pago':'tarjeta'})
        expired=request('/apartados',common|{'cliente':'Demo · Apartado vencido',
            'email':'demo.vencido@example.test','precio':80,'abono_inicial':20,
            'fecha':str(today-timedelta(days=91))})
        request(f"/apartados/{expired['id']}/vencer",{})
        sale=request('/ventas',{'concepto':'Demo · Venta directa','importe':25,'forma_pago':'efectivo'})
        results=[]
        for item, state, paid_amount, pending in [(active,'activo',20,40),(paid,'liquidado',40,0),(expired,'vencido',20,60)]:
            detail=request(f"/apartados/{item['id']}")
            assert (detail['estado'],detail['abonado'],detail['pendiente'])==(state,paid_amount,pending)
            assert detail['fecha_limite']==str(datetime.fromisoformat(detail['fecha']).date()+timedelta(days=90))
            if state=='vencido':assert detail['vale']['importe']==20
            results.append({'id':detail['id'],'estado':state,'abonado':detail['abonado'],
                            'pendiente':detail['pendiente'],'vale':detail['vale']})
        report.update(estado='completado',apartados=results,venta_id=sale['id'])
        save()
        print(json.dumps({'registro':str(args.registro),'apartados':results,'venta_id':sale['id']},ensure_ascii=False))
    except Exception as error:
        report['estado']='requiere_revision';report['error_tipo']=type(error).__name__;save()
        raise SystemExit('Carga detenida. Consultar el registro y conciliar por API antes de cualquier nueva carga.') from None


if __name__=='__main__':
    main()
