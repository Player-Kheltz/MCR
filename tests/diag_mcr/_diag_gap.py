import sys, os, json, random, math
sys.path.insert(0, 'E:/MCR'); os.chdir('E:/MCR')

from mcr.coupling import MCRCoupling
from mcr.semantic_router import similaridade as ngram_sim

c = MCRCoupling()
corpus = [
    ("gato late", "animais"), ("cachorro late", "animais"),
    ("gato mia", "animais"), ("cachorro corre", "animais"),
    ("passaro voa", "animais"), ("peixe nada", "animais"),
    ("carro corre", "veiculos"), ("moto corre", "veiculos"),
    ("caminhao anda", "veiculos"), ("bicicleta anda", "veiculos"),
    ("uva doce", "frutas"), ("maca doce", "frutas"),
    ("limao azedo", "frutas"), ("banana amarela", "frutas"),
    ("fogo queima", "elementos"), ("agua molha", "elementos"),
    ("gelo congela", "elementos"), ("vento sopra", "elementos"),
    ("criar monstro", "criar"), ("gerar npc", "criar"),
    ("fazer item", "criar"), ("editar script", "editar"),
    ("modificar codigo", "editar"), ("alterar texto", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
    ("procurar palavra", "buscar"), ("aprender licao", "aprender"),
    ("estudar materia", "aprender"), ("memorizar regra", "aprender"),
]
for txt, act in corpus:
    c.alimentar(txt, act)

# Debug "fabrique" - entender gaps
palavra = "fabrique"
doadores = []
for known in c._palavra_acao.keys():
    if known == palavra: continue
    s = ngram_sim(palavra, known)
    if s <= 0: continue
    sig = c._assinatura_palavra(known)
    if not sig: continue
    doadores.append((s, known, sig))

doadores.sort(key=lambda x: -x[0])
print(f"Doadores para '{palavra}': {len(doadores)}")
for i, (s, known, _) in enumerate(doadores[:15]):
    acoes = c._palavra_acao.get(known, {})
    top = max(acoes, key=acoes.get) if acoes else '-'
    print(f"  {i}: {known:15s} s={s:.4f} acao={top}")

# Calcular gaps
print("\nGaps:")
maior_gap = 0
idx_corte = len(doadores)
for i in range(len(doadores) - 1):
    if doadores[i][0] == 0: continue
    gap = (doadores[i][0] - doadores[i+1][0]) / doadores[i][0]
    if gap > maior_gap:
        maior_gap = gap
        idx_corte = i + 1
    print(f"  {i}: {doadores[i][1]}/{doadores[i+1][1]} gap={gap:.4f}")

print(f"\nMaior gap: {maior_gap:.4f} no índice {idx_corte}")
print(f"Doadores selecionados: {idx_corte}")

# Ver quais doadores são selecionados
selecionados = doadores[:idx_corte]
print(f"\nSelecionados: {[d[1] for d in selecionados]}")

# Acumular herança
from collections import defaultdict
heranca = defaultdict(float)
for s, _, sig in selecionados:
    for k, v in sig.items():
        if k.startswith('acao:'):
            heranca[k] += v * s * s

print(f"\nHerança bruta: {dict(sorted(heranca.items(), key=lambda x: -x[1]))}")
for k, v in heranca.items():
    print(f"  {k}: {v:.6f} -> int(round)={int(round(v))}")