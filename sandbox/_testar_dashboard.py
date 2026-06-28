#!/usr/bin/env python3
"""Testa dashboard."""
import sys, threading, time
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.dashboard import Dashboard

d = Dashboard()
t = threading.Thread(target=d.iniciar, daemon=True)
t.start()
time.sleep(2)
print('Testando...')
import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:8765', timeout=5)
    print('Status:', resp.status)
    print(resp.read()[:200])
except Exception as e:
    print('ERRO:', e)
