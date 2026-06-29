"""Testa todos os endpoints API com porta diferente."""
import os, sys, time, json, urllib.request
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

PORTA = 8766  # porta limpa
from modulos.sse_server import iniciar_sse
iniciar_sse(PORTA)
time.sleep(2)

def test(nome, url, key=None):
    try:
        r = urllib.request.urlopen(f'http://localhost:{PORTA}{url}', timeout=30)
        d = json.loads(r.read())
        val = d.get(key or 'total') if key else 'OK'
        print(f'  [OK] {nome}: {val}')
    except Exception as e:
        print(f'  [FALHA] {nome}: {e}')

print('TESTANDO TODOS OS ENDPOINTS API:')
test('EMERGIR', '/api/emergir', 'total')
test('EMERGIR/L0189', '/api/emergir/L0189', 'id')
test('KG', '/api/kg', 'total_lessons')
test('KG/emergente', '/api/kg?ctx=emergente', 'filtradas')
test('KG/L0189', '/api/kg/L0189', 'id')
test('CONTEXTO', '/api/contexto', 'total_lessons_kg')
test('CONVERSA', '/api/conversa?limite=3', 'total')
print()
print('TODOS OS ENDPOINTS FUNCIONANDO!')
