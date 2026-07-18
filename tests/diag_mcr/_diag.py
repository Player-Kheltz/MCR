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

palavras = list(c._palavra_acao.keys())
print(f"Palavras conhecidas: {len(palavras)}")
print()

# Similaridades "fabrique" com todas
sims = [(p, ngram_sim('fabrique', p)) for p in palavras if p != 'fabrique']
sims.sort(key=lambda x: -x[1])
print("Top 10 similaridades ngram de 'fabrique':")
for p, s in sims[:10]:
    dist = c._palavra_acao.get(p, {})
    top_acao = max(dist, key=dist.get) if dist else '-'
    print(f"  {p:15s} sim={s:.4f} acao={top_acao}")

# Gaps
print("\nGaps relativos:")
for i in range(min(9, len(sims)-1)):
    if sims[i][1] > 0:
        gap = (sims[i][1] - sims[i+1][1]) / sims[i][1]
        print(f"  {sims[i][0]}/{sims[i+1][0]}: gap={gap:.4f}")

# Heranca atual
h = c._heranca_morfologica('fabrique')
print(f"\nHeranca: {h}")

# Outras palavras: "gere", "crie", etc.
for p in ['gere', 'crie', 'edite', 'estude', 'procure', 'encontre']:
    s_max = max((ngram_sim(p, k) for k in palavras if k != p), default=0)
    h2 = c._heranca_morfologica(p)
    acoes = [(k[5:], v) for k, v in h2.items() if k.startswith('acao:') and v > 0]
    acoes.sort(key=lambda x: -x[1])
    print(f"  {p:12s} sim_max={s_max:.4f} heranca={acoes[:2] if acoes else 'VAZIO'}")
