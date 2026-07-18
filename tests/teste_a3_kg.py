"""Teste A3: KG cresce com execucoes."""
import sys, json
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR
from mcr.paths import KG_DIR

mcr = MCR()

# Conta padroes antes (usa o arquivo MAIS RECENTE)
kg_files = sorted(KG_DIR.glob('patterns_*.json'))
n_antes = 0
if kg_files:
    with open(kg_files[-1], 'r', encoding='utf-8') as f:
        n_antes = len(json.load(f).get('padroes', []))
print(f'Padroes ANTES: {n_antes} (arquivo: {kg_files[-1].name if kg_files else "none"})')

# Roda 5 execucoes
for i in range(5):
    r = mcr.processar(f'Gere um monstro tipo {i}')
    codigo = str(r['resultado'].get('codigo', ''))
    print(f'  {r["acao"]} nota={r["nota"]} codigo_len={len(codigo)}')

# Conta padroes depois (arquivo mais recente)
kg_files = sorted(KG_DIR.glob('patterns_*.json'))
n_depois = 0
if kg_files:
    with open(kg_files[-1], 'r', encoding='utf-8') as f:
        n_depois = len(json.load(f).get('padroes', []))
print(f'Padroes DEPOIS: {n_depois} (arquivo: {kg_files[-1].name if kg_files else "none"})')
print(f'KG cresceu: {n_depois > n_antes} ({n_antes} -> {n_depois})')
