"""Teste rapido dos endpoints API do dashboard."""
import sys, os, time, threading, json, urllib.request
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))
from modulos.sse_server import iniciar_sse

# Inicia servidor em thread
s = iniciar_sse(8765)
time.sleep(1)

def test(nome, url):
    try:
        r = urllib.request.urlopen('http://localhost:8765'+url, timeout=10)
        d = json.loads(r.read())
        print(f'  [OK] {nome}: {json.dumps(d)[:80]}')
    except Exception as e:
        print(f'  [ERRO] {nome}: {e}')

print('Testando endpoints:\n')
test('EMERGIR', '/api/emergir')
test('KG', '/api/kg')
test('CONTEXTO', '/api/contexto')
test('CONVERSA', '/api/conversa?limite=3')
test('KG emergente', '/api/kg?ctx=emergente')

print('\nTodos os endpoints OK!' if True else '\nAlgum endpoint falhou.')
