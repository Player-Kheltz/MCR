"""Teste NMI sobre duas matrizes (acao vs transicao palavra)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['MCR_QUIET'] = '1'
import warnings, logging, math
logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore')

from mcr.coupling import MCRCoupling

c = MCRCoupling()
exemplos = [
    ("criar monstro dragao", "criar"),
    ("criar mago lich", "criar"),
    ("criar ferreiro anao", "criar"),
    ("gerar monstro orc", "gerar"),
    ("gerar mago feiticeiro", "gerar"),
    ("gerar ferreiro blacksmith", "gerar"),
    ("curar mago aliado", "curar"),
    ("curar ferreiro ferido", "curar"),
    ("analisar codigo fonte", "analisar"),
    ("analisar texto log", "analisar"),
]
for t, a in exemplos:
    for _ in range(3):
        c.alimentar(t, a)


def nmi(dict_a, dict_b):
    if not dict_a or not dict_b:
        return 0.0
    todas = set(dict_a) | set(dict_b)
    ta = sum(dict_a.values()) or 1
    tb = sum(dict_b.values()) or 1
    tab = ta + tb
    ha = 0.0
    for k in todas:
        p = dict_a.get(k, 0) / ta
        if p > 0:
            ha -= p * math.log2(p)
    hb = 0.0
    for k in todas:
        p = dict_b.get(k, 0) / tb
        if p > 0:
            hb -= p * math.log2(p)
    hab = 0.0
    for k in todas:
        p = (dict_a.get(k, 0) + dict_b.get(k, 0)) / tab
        if p > 0:
            hab -= p * math.log2(p)
    mi = ha + hb - hab
    maxh = max(ha, hb)
    if maxh <= 0:
        return 0.0
    return max(0.0, min(1.0, mi / maxh))


print("TRANSICOES PALAVRA→PALAVRA (contexto markoviano):")
for p in ['criar', 'gerar', 'curar', 'analisar', 'mago', 'ferreiro', 'monstro', 'dragao', 'orc']:
    d = dict(c._transicao_palavra.get(p, {}))
    print(f"  {p:10s} -> {d}")

print()
print("PALAVRA→ACAO:")
for p in ['criar', 'gerar', 'curar', 'analisar', 'mago', 'ferreiro', 'monstro', 'dragao', 'orc']:
    d = dict(c._palavra_acao.get(p, {}))
    print(f"  {p:10s} -> {d}")

print()
testes = [
    ("criar", "gerar", "SINONIMOS"),
    ("criar", "curar", "diferentes"),
    ("criar", "analisar", "distintos"),
    ("gerar", "curar", "diferentes"),
    ("mago", "ferreiro", "entidades"),
    ("mago", "monstro", "co-ocorrentes"),
    ("dragao", "orc", "especies diferentes"),
    ("lich", "feiticeiro", "sub-entidades"),
    ("criar", "mago", "verbo×entidade"),
    ("codigo", "mago", "distantes"),
]

print(f"{'PAR':25}  NMI[acao]  NMI[transicao]")
print("-" * 55)
for a, b, lbl in testes:
    n_acao = nmi(c._palavra_acao.get(a, {}), c._palavra_acao.get(b, {}))
    n_trans = nmi(c._transicao_palavra.get(a, {}), c._transicao_palavra.get(b, {}))
    print(f"{a+'~'+b:25}  {n_acao:8.4f}  {n_trans:8.4f}   [{lbl}]")
