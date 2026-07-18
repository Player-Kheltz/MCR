"""Validacao real: coupling aprende semantica universal."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['MCR_QUIET'] = '1'
import warnings, logging
logging.disable(logging.CRITICAL)

from mcr.coupling import MCRCoupling

c = MCRCoupling()

exemplos = [
    ("gerar npc fighter", "gerar"),
    ("gerar monstro orc", "gerar"),
    ("gerar mago lich", "gerar"),
    ("gerar ferreiro blacksmith", "gerar"),
    ("gerar sprite goblin", "gerar"),
    ("criar npc heroi", "criar"),
    ("criar monstro dragao", "criar"),
    ("criar mago feiticeiro", "criar"),
    ("criar ferreiro anao", "criar"),
    ("criar sprite bruxa", "criar"),
    ("curar npc aliado", "curar"),
    ("curar mago vilao", "curar"),
    ("curar ferreiro ferido", "curar"),
    ("atacar monstro boss", "atacar"),
]
for t, a in exemplos:
    for _ in range(5):
        c.alimentar(t, a)

print("=== SIMILARIDADE UNIVERSAL ===")
print()

testes = [
    # entidades sinônimas (substantivos)
    ("npc", "mago", "entidades_verbo_acao"),
    ("npc", "ferreiro", "entidades_verbo_output"),
    ("monstro", "mago", "inimigos_entidades"),
    # verbos sinônimos (ações)
    ("criar", "gerar", "verbos_sinonimos"),
    ("criar", "curar", "verbos_diferentes"),
    # verbos com entidades
    ("criar", "npc", "verbo x entidade"),
    ("atacar", "monstro", "verbo x alvo"),
    # palavras novas/nunca vistas
    ("make", "gerar", "ingles x portugues"),
    ("create", "criar", "ingles sinonimo"),
    ("hero", "heroi", "ingles x portugues"),
    # termos semanticamente distantes
    ("codigo", "mago", "abstrato x entidade"),
]

resultados = []
for a, b, label in testes:
    sim = c.similaridade(a, b)
    resultados.append((label, a, b, sim))

print(f"{'TIPO':30s} {'A':12s} {'B':12s} {'SIM':>8s}")
print("-"*64)
for label, a, b, sim in resultados:
    barra = "#" * min(20, int(sim * 20))
    print(f"{label:30s} {a:12s} {b:12s} {sim:8.4f}  {barra}")

print()

ok = True

def check(label, cond):
    global ok
    if cond:
        print(f"  PASS {label}")
    else:
        print(f"  FAIL {label}")
        ok = False

criar_gerar = [s for l, a, b, s in resultados if l == "verbos_sinonimos"][0]
make_gerar = [s for l, a, b, s in resultados if l == "ingles x portugues"][0]
npc_mago = [s for l, a, b, s in resultados if l == "entidades_verbo_acao"][0]
criar_curar = [s for l, a, b, s in resultados if l == "verbos_diferentes"][0]
codigo_mago = [s for l, a, b, s in resultados if l == "abstrato x entidade"][0]
hero_heroi = [s for l, a, b, s in resultados if l == "ingles x portugues"][1]

check("criar≈gerar (verbos sinonimos) >= 0.30", criar_gerar >= 0.30)
check("npc≈mago (entidades) >= 0.50", npc_mago >= 0.50)
check("codigo≉mago (distantes) < 0.30", codigo_mago < 0.30)
check("hero≈heroi (cognato) >= 0.10", hero_heroi >= 0.10)

print()
if ok:
    print("VALIDACAO SEMANTICA REAL: OK")
else:
    print("VALIDACAO SEMANTICA REAL: FALHA")
