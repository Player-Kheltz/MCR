#!/usr/bin/env python3
"""Benchmark: Conselho Completo (4 fixos+honorarios) vs Rapido (2 fixos)."""
import sys, os, re, time, json, threading
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho
from modulos.util import fast as _fast, gerar as _gerar

BASE = r'E:\Projeto MCR'
k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))
PERGUNTA = "Crie a historia de Eridanus em Tibia com origem, fundacao, era de ouro, declinio, nomes proprios."

# 1. COMPLETO
print('[1] COMPLETO (4 fixos + honorarios)...')
t0 = time.time()
r_full = c.deliberar(PERGUNTA)
t_full = time.time() - t0
resp_full = r_full.get('veredito', '')
with open(os.path.join(BASE, 'sandbox', '_resp_full.txt'), 'w', encoding='utf-8') as f:
    f.write(resp_full)
print(f'  OK - {t_full:.0f}s, {len(resp_full)} chars')

# 2. RAPIDO (2 fixos)
print('\n[2] RAPIDO (analista + critico)...')
class Rapido:
    def __init__(self, kg=None):
        self.kg = kg
    def deliberar(self, pergunta):
        t0 = time.time()
        kg = ''
        if self.kg:
            try: kg = '\n'.join(f"- {r.get('solucao','')[:200]}" for r in self.kg.buscar(pergunta, max_r=3))
            except: pass
        res = [None, None]
        def a(): res[0] = _fast(f"ANALISTA: {pergunta}\nKG:{kg[:500]}\nFatos:", 0.15) or ''
        def c_(): res[1] = _fast(f"CRITICO: {pergunta}\nRiscos:", 0.25) or ''
        for fn in [a, c_]:
            t = threading.Thread(target=fn, daemon=True); t.start(); t.join()
        ops = [('Analista', res[0]), ('Critico', res[1])]
        db = f"Pergunta: {pergunta}\n" + '\n'.join(f"{n}: {o[:400]}" for n,o in ops)
        db += "\nVEREDITO: Historia com nomes proprios (2-3 frases):"
        v = _gerar(db, 0.3, 'leve') or _fast(db, 0.3) or ''
        return {'veredito': v, 'tempo_total': round(time.time()-t0, 1)}

r = Rapido(kg=k.contexto.get('kg'))
t0 = time.time()
r_fast = r.deliberar(PERGUNTA)
t_fast = time.time() - t0
resp_fast = r_fast.get('veredito', '')
with open(os.path.join(BASE, 'sandbox', '_resp_fast.txt'), 'w', encoding='utf-8') as f:
    f.write(resp_fast)
print(f'  OK - {t_fast:.0f}s, {len(resp_fast)} chars')

# 3. COMPARACAO
print(f'\n{"="*60}')
print('COMPARACAO')
print(f'{"="*60}')
for nome, resp, tempo in [
    ('COMPLETO (4 fixos + honorarios)', resp_full, t_full),
    ('RAPIDO (analista + critico)', resp_fast, t_fast),
]:
    nm = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', resp)))
    nu = len(re.findall(r'\d+', resp))
    print(f'\n{nome}:')
    print(f'  Tempo: {tempo:.0f}s | Tamanho: {len(resp)} chars | Nomes: {nm} | Numeros: {nu}')

print(f'\nDiferenca: COMPLETO {t_full:.0f}s vs RAPIDO {t_fast:.0f}s')
print(f'RAPIDO e {(1-t_fast/t_full)*100:.0f}% mais rapido')
print(f'RAPIDO perdeu em qualidade? Compare os arquivos:')
print(f'  _resp_full.txt (COMPLETO)')
print(f'  _resp_fast.txt (RAPIDO)')
