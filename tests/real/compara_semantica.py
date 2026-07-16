"""Comparacao REAL: versao ANTERIOR (cosseno+2-hop) vs versão NOVA (NMI/Equacao)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['MCR_QUIET'] = '1'
import warnings, logging, math
logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore')

from mcr.coupling import MCRCoupling

# === BASE TREINO ===
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
c = MCRCoupling()
for t, a in exemplos:
    for _ in range(3):
        c.alimentar(t, a)

# === NMI (NOVO - Equacao MCR) ===
def nmi(a, b):
    """Versao Nova: Informacao Mutua Normalizada - puramente MCR."""
    da = c._palavra_acao.get(a, {})
    db = c._palavra_acao.get(b, {})
    if not da or not db: return 0.0
    if a == b: return 1.0
    todas = set(da) | set(db)
    ta = sum(da.values()) or 1
    tb = sum(db.values()) or 1
    tab = ta + tb
    def H(d, tot):
        h = 0.0
        for k in todas:
            p = d.get(k,0) / tot
            if p > 0: h -= p * math.log2(p)
        return h
    ha = H(da, ta); hb = H(db, tb)
    hab = 0.0
    for k in todas:
        p = (da.get(k,0) + db.get(k,0)) / tab
        if p > 0: hab -= p * math.log2(p)
    mi = ha + hb - hab
    maxh = max(ha, hb)
    if maxh <= 0: return 0.0
    return max(0.0, min(1.0, mi/maxh))

# === ANTERIOR (cosseno sobre transicao palavra↔palavra) ===
def cosseno_2hop(a, b):
    """Versao anterior: 2-hop via transicao palavra↔palavra."""
    t1 = c._transicao_palavra.get(a, {})
    t2 = c._transicao_palavra.get(b, {})
    if not t1 or not t2: return 0.0
    todas = set(t1) | set(t2)
    def H_VEC(d):
        tot = sum(d.values()) or 1
        h = 0.0
        for k in todas:
            p = d.get(k,0)/tot
            if p > 0: h -= p * math.log2(p)
        return h
    a_arr = sum(t1.get(k,0)*t1.get(k,0) for k in todas) ** 0.5
    b_arr = sum(t2.get(k,0)*t2.get(k,0) for k in todas) ** 0.5
    if a_arr == 0 or b_arr == 0: return 0.0
    dot = sum(t1.get(k,0)*t2.get(k,0) for k in todas)
    return dot / (a_arr * b_arr)

# === TESTES ===
testes = [
    ("criar", "gerar", "SINONIMOS verbos (devem ser similares)"),
    ("criar", "curar", "verbos diferentes (deveriam ser MENOS similares)"),
    ("gerar", "curar", "verbos diferentes (deveriam ser MENOS similares)"),
    ("criar", "analisar", "verbos distantes"),
    ("analisar", "curar", "verbos distantes"),
    ("mago", "ferreiro", "entidades sinonimas"),
    ("mago", "monstro", "entidades co-ocorrentes"),
    ("mago", "dragao", "entidades relacionadas"),
    ("dragao", "orc", "entidades NAO relacionadas (especies distintas)"),
    ("criar", "mago", "verbo vs entidade"),
    ("criar", "criar", "igual"),
    ("codigo", "mago", "totalmente distantes"),
]

print("=" * 88)
print(f"{'DESCRICAO':40} {'ANTIGO (2-hop)':15} {'NOVO (NMI+Eq)':15}")
print("=" * 88)
for a, b, label in testes:
    antigo = round(cosseno_2hop(a, b), 4)
    novo = round(c.similaridade(a, b), 4)
    sinal = ""
    if "SINONIMOS" in label:
        sinal = " <-- sinonimo real"
        if novo >= 0.5 and (novo > antigo or antigo < 0.3):
            sinal += " [MELHOR]"
        elif novo < 0.3:
            sinal += " [AMBOS FALHAM]"
    elif "MENOS" in label and "SINONIMOS" not in label:
        if novo < antigo:
            sinal += " [NMI melhor discriminacao]"
    print(f"{label:40} A~{a}~B  {antigo:8.4f}     {novo:8.4f}{sinal}")

print()
print("DISTINCAO CHAVE (sinonimos vs nao-sinonimos):")
cg = c.similaridade("criar","gerar"); cc = c.similaridade("criar","curar")
print(f"  NOVO: criar≈gerar={cg:.4f}, criar≈curar={cc:.4f}, gap={(cg-cc):+.4f}")

cg2 = cosseno_2hop("criar","gerar"); cc2 = cosseno_2hop("criar","curar")
print(f"  ANT: criar≈gerar={cg2:.4f}, criar≈curar={cc2:.4f}, gap={(cg2-cc2):+.4f}")

am = c.similaridade("mago","ferreiro"); amm = c.similaridade("dragao","orc")
print(f"  NOVO: mago≈ferreiro={am:.4f} (sin), dragao≈orc={amm:.4f} (nao)")
am2 = cosseno_2hop("mago","ferreiro"); amm2 = cosseno_2hop("dragao","orc")
print(f"  ANT: mago≈ferreiro={am2:.4f} (sin), dragao≈orc={amm2:.4f} (nao)")
