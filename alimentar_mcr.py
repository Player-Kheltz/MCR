#!/usr/bin/env python3
"""Alimenta MCRSystem com docs do projeto + lore_base + PERSONALIDADE.md.
Depois testa MCRPergunta."""
import sys, os, time, re

sys.path.insert(0, r'E:\MCR')
os.chdir(r'E:\MCR')

import MCR as _MCR
if not hasattr(_MCR, 'MCRBridge'):
    class MCRBridge:
        def __init__(self): self._descobriu = True
        def descobrir(self): return {'modulos': 48, 'comandos': 52}
    _MCR.MCRBridge = MCRBridge

from MCR import MCRSystem, MCRBufferKG, MCRPergunta

print('='*55)
print('  ALIMENTANDO MCRSystem + MCRPergunta')
print('='*55)

cerebro = MCRSystem()
if cerebro.kg is None:
    cerebro.kg = MCRBufferKG()
if not hasattr(cerebro.kg, '_lessons_cache'):
    cerebro.kg._lessons_cache = []

print('  KG: %s' % type(cerebro.kg).__name__)

t0 = time.time()

# Alimenta MK palavras com docs do projeto
docs_dir = r'E:\Projeto MCR'
lidos = 0

for root, dirs, files in os.walk(docs_dir):
    dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg', 'node_modules'))]
    for f in files:
        if not f.endswith(('.md', '.lua', '.py', '.txt', '.json')):
            continue
        fp = os.path.join(root, f)
        if os.path.getsize(fp) > 200000:
            continue
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                texto = fh.read()
        except:
            continue
        
        # Alimenta MK palavras (bigramas)
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', texto.lower())
        if len(palavras) < 5:
            continue
        for i in range(len(palavras)-1):
            try:
                cerebro.mk_palavra.aprender(palavras[i], palavras[i+1])
            except: pass
        
        # Alimenta KG com conceitos (extrai termos relevantes)
        for termo in ['spa', 'shc', 'sqh', 'mcr', 'eridanus', 'pyros', 'ignis',
                      'aventureiro', 'dominio', 'progressao', 'habilidade',
                      'fogo', 'gelo', 'terra', 'energia']:
            if termo in texto.lower():
                contexto = re.findall(r'.{0,60}%s.{0,60}' % termo, texto.lower(), re.IGNORECASE)
                if contexto:
                    cerebro.kg._lessons_cache.append({
                        'erro': termo,
                        'solucao': contexto[0][:200],
                        'ctx': os.path.basename(fp)
                    })
        
        lidos += 1
        if lidos % 100 == 0:
            print('  Lidos: %d arquivos' % lidos)

t1 = time.time()
print('  Arquivos processados: %d' % lidos)
print('  Tempo: %.1fs' % (t1-t0))
print('  Lessons no cache: %d' % len(getattr(cerebro.kg, '_lessons_cache', [])))

# Teste MCRPergunta
print('\n--- Teste: MCRPergunta ---')
try:
    p = MCRPergunta(kg=cerebro.kg)
    t2 = time.time()
    resp = p.perguntar('O que e SPA no Projeto MCR?')
    t3 = time.time()
    if resp:
        print('  Resposta: %s' % str(resp)[:300])
        if isinstance(resp, dict):
            print('  Nota: %s' % resp.get('nota', 'N/A'))
        print('  Tempo: %.3fs' % (t3-t2))
    else:
        print('  Sem resposta')
except Exception as e:
    print('  Erro: %s' % e)

# Teste Markov direto
print('\n--- Teste: Markov direto ---')
for termo in ['spa', 'mcr', 'eridanus', 'aventureiro']:
    pred, conf = cerebro.mk_palavra.predizer(termo)
    print('  %s -> %s (conf=%.2f)' % (termo, pred, conf))

print('\nPronto!')
