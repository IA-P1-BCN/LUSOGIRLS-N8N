"""Fuente CSV y proxy de fallos exclusivos del laboratorio HU-13.

No registra cuerpos ni cabeceras; la clave llega por entorno privado del contenedor.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hmac
import json
import os
import urllib.error
import urllib.request

DIRECTORY = Path('/qa')
KEY = os.environ['API_KEY']
STORE = os.environ['STORE_URL']


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, data, kind='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_request(self):
        if not hmac.compare_digest(self.headers.get('X-API-Key', ''), KEY):
            self.respond(401, b'{"detail":"No autorizado"}')
            return
        if self.command == 'GET' and self.path.startswith('/cobros-'):
            self.respond(200, (DIRECTORY / 'cobros.csv').read_bytes(), 'text/csv; charset=utf-8')
            return
        if not self.path.startswith('/api/'):
            self.respond(404, b'{}')
            return
        body = self.rfile.read(int(self.headers.get('Content-Length', '0'))) if self.command == 'POST' else None
        req = urllib.request.Request(STORE + self.path, body, method=self.command,
                                     headers={'X-API-Key': KEY, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status, data = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, data = error.code, error.read()
        if self.command == 'POST':
            with (DIRECTORY / 'posts.jsonl').open('a') as out:
                out.write(json.dumps({'path': self.path, 'status': status}) + '\n')
            if (DIRECTORY / 'respuesta-incierta').exists() and status == 201:
                self.respond(503, b'{"detail":"Fallo de respuesta de prueba"}')
                return
        self.respond(status, data)

    do_GET = handle_request
    do_POST = handle_request


ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
