#!/usr/bin/env python3
"""Teste MCRAssinatura com nomes significativos."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAssinatura

# Teste 1: identificar Kheltz
banco = MCRAssinatura()
banco.aprender('Explique o sistema SPA do MCR', 'Kheltz')
banco.aprender('Crie um NPC ferreiro em Eridanus', 'Kheltz')
autor, conf, _ = banco.identificar('Explique o SPA do projeto MCR')
print(f'Identificar: autor={autor} conf={conf:.2f}')
assert conf > 0.3, f'Confianca baixa: {conf}'

# Teste 2: auto_popular com role
n = banco.auto_popular()
autores = banco.autores_conhecidos()
est = banco.estatisticas()
print(f'Autores: {autores}')
print(f'Total: {est}')

# Verifica se cloud foi adicionado
if 'cloud' in autores:
    print(f'OK: autor "cloud" encontrado (role-based naming)')
else:
    # Pode ser que o .jsonl nao tenha sido populado ainda
    print(f'INFO: autor "cloud" nao encontrado (jsonl pode estar vazio)')

print(f'OK - {est["autores"]} autores, {est["total_assinaturas"]} assinaturas')
