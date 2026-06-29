"""Testa todos os endpoints API do dashboard."""
import os, sys, time, json, urllib.request
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))
from modulos.sse_server import iniciar_sse

# Server em thread
iniciar_sse(8765)
time.sleep(2)

def test(name, url, key=None):
    try:
        r = urllib.request.urlopen('http://localhost:8765' + url, timeout=15)
        d = json.loads(r.read())
        val = d.get(key or 'total') if key else 'OK'
        print(f'  [OK] {name}: {val if not isinstance(val, (list,dict)) else len(val)}')
        return d
    except Exception as e:
        print(f'  [FALHA] {name}: {e}')
        return None

print('=== TESTANDO TODOS OS ENDPOINTS API ===')
test('EMERGIR', '/api/emergir', 'total')
test('EMERGIR L0189', '/api/emergir/L0189', 'id')
test('KG', '/api/kg', 'total_lessons')
test('KG emergente', '/api/kg?ctx=emergente', 'filtradas')
test('KG L0189', '/api/kg/L0189', 'id')
test('CONTEXTO', '/api/contexto', 'total_lessons_kg')
test('CONVERSA', '/api/conversa?limite=3', 'total')
print('=== FIM ===')
