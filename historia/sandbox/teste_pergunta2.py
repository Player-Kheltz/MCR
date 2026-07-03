#!/usr/bin/env python3
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

t0 = time.time()
from modulos.MCR import MCRPergunta, MCRSignature
print(f'[{time.time()-t0:.1f}s] Import', flush=True)

p = MCRPergunta(kg=None)
print(f'[{time.time()-t0:.1f}s] Criado', flush=True)

# Test just the helper methods
lessons = []
r = p._ranquear_por_assinatura(lessons, 'explique SPA')
print(f'[{time.time()-t0:.1f}s] _ranquear_por_assinatura(vazia) = {r}', flush=True)

ls = [{'solucao': 'SPA e o sistema de progressao', 'ctx': 'lore'}]
r2 = p._ranquear_por_assinatura(ls, 'explique SPA')
print(f'[{time.time()-t0:.1f}s] _ranquear_por_assinatura(1) = {len(r2)}', flush=True)

# Test filtrar
from modulos.MCR import MarkovUniversal
mk = MarkovUniversal("teste_filtro")
f = p._filtrar_lesson("O aventureiro explora a floresta", mk)
print(f'[{time.time()-t0:.1f}s] _filtrar_lesson = {f}', flush=True)

print(f'[{time.time()-t0:.1f}s] OK', flush=True)
