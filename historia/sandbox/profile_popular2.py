#!/usr/bin/env python3
"""Profile auto_popular interno."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t0 = time.time()
from modulos.MCR import MCRAssinatura, MCRSignature

# Carrega banco
banco = MCRAssinatura()
print(f'init: {time.time()-t0:.1f}s', flush=True)

# Le o jsonl e conta
t1 = time.time()
conv_path = os.path.join(banco._base, 'sandbox', '.mcr_conversa.jsonl')
with open(conv_path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()
print(f'ler jsonl {len(linhas)} linhas: {time.time()-t1:.1f}s', flush=True)

# Testa rapido vs full num subconjunto
testes = []
for linha in linhas[:50]:
    try:
        import json
        entry = json.loads(linha.strip())
        msg = entry.get('msg', '')
        if msg and len(msg) >= 20:
            testes.append(msg)
    except: pass

print(f'{len(testes)} mensagens validas nas primeiras 50 linhas', flush=True)

t1 = time.time()
for msg in testes:
    MCRSignature.extrair(msg, rapido=True)
print(f'rapido x{len(testes)}: {time.time()-t1:.1f}s', flush=True)

t1 = time.time()
for msg in testes:
    MCRSignature.extrair(msg)
print(f'full x{len(testes)}: {time.time()-t1:.1f}s', flush=True)

# Testa aprender
t1 = time.time()
for msg in testes[:10]:
    banco.aprender(msg, 'teste', rapido=True)
print(f'aprender rapido x10: {time.time()-t1:.1f}s', flush=True)

t1 = time.time()
for msg in testes[:10]:
    banco.aprender(msg, 'teste')
print(f'aprender full x10: {time.time()-t1:.1f}s', flush=True)
