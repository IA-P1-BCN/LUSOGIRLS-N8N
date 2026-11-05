"""Doble HTTP local de las fuentes de prueba; no es una API de producción."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs, parse_qsl
import json
import re
import urllib.request,urllib.error,time

fixture={}
calls=[]
SEND_MESSAGE=re.compile(r'^/bot[^/]+/sendMessage$')
def masked(path):
    # El token de Telegram va en la ruta; nunca se guarda en /__calls.
    return re.sub(r'^/bot[^/?]+','/bot<token>',path)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,status,body,count=None):
        self.send_response(status); self.send_header('Content-Type','application/json')
        if count is not None: self.send_header('X-Total-Count',str(count))
        self.end_headers(); self.wfile.write(json.dumps(body).encode())
    def do_POST(self):
        global fixture,calls
        raw=self.rfile.read(int(self.headers.get('Content-Length',0)))
        tipo=self.headers.get('Content-Type','')
        body=dict(parse_qsl(raw.decode())) if 'x-www-form-urlencoded' in tipo else json.loads(raw or b'{}')
        if self.path=='/__fixture':
            fixture=body;calls=[];return self.reply(200,{'ok':True})
        if SEND_MESSAGE.match(self.path):
            # Doble de Telegram: se registran el cuerpo y su formato.
            calls.append({'method':'POST','path':masked(self.path),'content_type':tipo,'body':body})
            return self.reply(200,{'ok':True,'result':{'message_id':len(calls),'date':0,'chat':{'id':body.get('chat_id')},'text':body.get('text','')}})
        calls.append({'method':'POST','path':masked(self.path)})
        if self.path=='/chat/completions':
            assert body['model']=='openrouter/free' and body['provider']['max_price']=={'prompt':0,'completion':0}
            content=fixture.get('llm_content',json.dumps(fixture.get('extraction',{})))
            return self.reply(200,{'choices':[{'message':{'content':content}}]})
        if fixture.get('proxy_tienda') and self.path.startswith('/api/'):
            req=urllib.request.Request('http://tienda:8000'+self.path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-API-Key':self.headers.get('X-API-Key','')})
            with urllib.request.urlopen(req) as response:data=json.load(response);status=response.status
            if fixture.get('timeout_after_post'):time.sleep(12)
            try:return self.reply(status,data)
            except BrokenPipeError:return
        self.reply(405,{'detail':'No se permiten escrituras de negocio en el simulador'})
    def do_GET(self):
        route=urlsplit(self.path)
        if route.path=='/__calls':return self.reply(200,calls)
        calls.append({'method':'GET','path':masked(route.path),'query':parse_qs(route.query)})
        if fixture.get('proxy_tienda') and route.path.startswith('/api/'):
            req=urllib.request.Request('http://tienda:8000'+self.path,headers={'X-API-Key':self.headers.get('X-API-Key','')})
            with urllib.request.urlopen(req) as response:
                return self.reply(response.status,json.load(response),response.headers.get('X-Total-Count'))
        key=route.path.rsplit('/',1)[-1]
        if key=='consentimiento':
            identifier=route.path.split('/')[-2]
            value=fixture.get('consentimientos',{}).get(identifier)
            if value is None:
                details=fixture.get('detalles',{}).get(identifier) or next((a for a in fixture.get('apartados',[]) if str(a.get('id'))==identifier),None)
                value=details.get('consentimiento_notificaciones') if details else None
            if not isinstance(value,bool):return self.reply(404,{'detail':'Permiso ficticio no configurado'})
            return self.reply(200,{'apartado_id':int(identifier),'consentimiento_notificaciones':value,'consentimiento_actualizado':None})
        if key.isdigit():
            value=fixture.get('detalles',{}).get(key)
            return self.reply(200 if value else 404,value or {'detail':'No encontrado'})
        error=fixture.get(key+'_response')
        if error:return self.reply(error['status'],{'detail':'Fallo ficticio de fuente'})
        data=fixture.get(key,[])
        self.reply(200,data,len(data) if key in ('ventas','apartados') else None)

ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
