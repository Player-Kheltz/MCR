#!/usr/bin/env python3
"""Teste HTTP - inicia servidor em thread e testa."""
import sys, os, threading, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}, ensure_ascii=False).encode('utf-8'))
    def log_message(self, *a): pass

server = HTTPServer(('', 8765), Handler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
time.sleep(1)

import urllib.request
resp = urllib.request.urlopen('http://localhost:8765', timeout=5)
print('RESPOSTA:', resp.read().decode())

server.shutdown()
print('OK - servidor HTTP funciona')
