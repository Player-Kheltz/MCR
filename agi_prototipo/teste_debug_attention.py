#!/usr/bin/env python3
"""Debug: entenda porque o MCRAttention nao funciona com 418 topicos."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import CerebroAGI, MCRByteUtils
from prototipo_mcr_attention import MCRAttention

c = CerebroAGI()

# Carrega dados
base = r"E:\Projeto MCR"
if not os.path.exists(base):
    base = os.path.dirname(os.path.dirname(__file__))
n = 0
for ext in ["py", "md", "txt", "lua"]:
    for f in sorted(glob.glob(os.path.join(base, f"**/*.{ext}"), recursive=True))[:200]:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fp:
                txt = fp.read(1000)
            if len(txt) > 50:
                c.alimentar(txt[:500], os.path.basename(f)[:20])
                n += 1
        except: pass

print(f"{n} arquivos, {len(c.topicos)} topicos")
print()

# Debug: predizer_n para "SPA"
print('predizer_n("SPA"):')
preds = c.mk_palavra.predizer_n("SPA", 10)
for tok, conf in preds:
    print(f'  {tok}: {conf:.4f}')
if not preds:
    print('  (nenhum candidato — SPA nao esta no modelo)')
    # Verifica se SPA esta no modelo
    print(f'  "SPA" in mk_palavra.freq: {"SPA" in c.mk_palavra.freq}')
    if "SPA" in c.mk_palavra.freq:
        print(f'  transicoes de SPA: {dict(list(c.mk_palavra.transicoes.get("SPA", {}).items())[:5])}')
print()

# Debug: _topico_relevante
print('_topico_relevante("explique o sistema SPA"):')
topico = MCRAttention._topico_relevante(c, "explique o sistema SPA")
if topico:
    nome, texto, score = topico
    print(f'  Topico: {nome} (score={score:.3f})')
    print(f'  Texto: {texto[:80]}')
else:
    print('  Nenhum topico relevante encontrado')
print()

# Debug: _candidatos_do_topico
if topico:
    print('_candidatos_do_topico(..., "SPA", 10):')
    cands = MCRAttention._candidatos_do_topico(texto, "SPA", 10)
    for tok, conf in cands:
        print(f'  {tok}: {conf:.4f}')
    if not cands:
        print('  (SPA nao encontrado no texto do topico)')
        print(f'  "SPA" in texto: {"SPA" in texto}')
print()

# Debug: qual topico tem "SPA"?
print('Topicos que contem "SPA":')
for nome, dados in c.topicos.items():
    if "SPA" in dados.get("texto", ""):
        print(f'  {nome}: {dados["texto"][:60]}')
