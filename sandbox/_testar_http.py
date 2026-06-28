#!/usr/bin/env python3
"""Teste minimo do servidor HTTP."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # silencia logs

print('Servidor teste na porta 8765...')
HTTPServer(('', 8765), Handler).serve_forever()
