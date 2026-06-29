"""Diagnostico RAPIDO - pega a ultima resposta EMERGIR."""
import os, sys, re
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))
from modulos.master_agent import MasterAgent

ma = MasterAgent()
ma._execution_count = 5

# Patch para capturar resposta
original = ma._gerar_emergencia_fragmentada
_last_response = [None]
def capture(*a, **kw):
    r = original(*a, **kw)
    _last_response[0] = r
    return r
ma._gerar_emergencia_fragmentada = capture

ma._processar_emergencia()

resp = _last_response[0]
if resp:
    out = os.path.join(os.path.dirname(__file__), '.emergir_v3_diag.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(resp)
    print(f'Salvo: {out} ({len(resp)} chars)')
    
    # Procura mencoes a FAST
    fast_lines = [l for l in resp.split('\n') if 'FAST' in l.upper()]
    print(f'\nMencoes a FAST ({len(fast_lines)}):')
    for l in fast_lines[:10]:
        print(f'  {l[:120]}')
    
    spa_lines = [l for l in resp.split('\n') if 'SPA' in l.upper()]
    print(f'\nMencoes a SPA ({len(spa_lines)}):')
    for l in spa_lines[:10]:
        print(f'  {l[:120]}')
else:
    print('Nenhuma resposta capturada (bloqueada antes do fragmentador)')
