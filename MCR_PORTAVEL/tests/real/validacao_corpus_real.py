"""validacao_corpus_real — Tese MCR: semantica emerge de dados reais?
Saida em arquivo para evitar travamento do terminal."""
import sys, os, json, math, time
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from mcr.coupling import MCRCoupling

SAIDA = os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'relatorio_validacao.txt')
CORPO = os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'npc_knowledge.json')

def log(msg):
    print(msg)
    with open(SAIDA, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

with open(CORPO, 'r', encoding='utf-8') as f:
    dados = json.load(f)
pares = []
for dialogos_lista in dados.get('dialogos', {}).values():
    for item in dialogos_lista:
        texto = str(item[0]) if item[0] else ''
        npc = str(item[1]) if len(item) > 1 else 'desconhecido'
        if len(texto) >= 10:
            pares.append((texto, npc))

log("=" * 72)
log("[MCR] VALIDACAO SEMANTICA - CORPUS REAL DE NPCS")
log("=" * 72)
log("[1] %d dialogos de %d NPCs" % (len(pares), len(set(a for _, a in pares))))

c = MCRCoupling()
t0 = time.time()
c.alimentar_swarm(pares)
dt = time.time() - t0
est = c.estatisticas()
log("[2] %s | tokens=%d features=%d acoes=%d" % (
    "%.1fs" % dt, est['palavras'], est['features_nd'], len(c._acao_features)))

log("[3] TOP PARES COM MAIOR NMI (= SINONIMOS DESCOBERTOS)")
freq = Counter()
for p, d in c._palavra_acao.items():
    freq[p] = sum(d.values())
top = [p for p, _ in freq.most_common(60) if len(p) >= 3]
nmi_pares = []
for i, a in enumerate(top):
    for b in top[i+1:]:
        s = c.similaridade(a, b)
        if s > 0.999:
            nmi_pares.append((s, a, b))
nmi_pares.sort(reverse=True)
log("  %d pares com NMI > 0.999" % len(nmi_pares))
for s, a, b in nmi_pares[:30]:
    log("    %-20s ~ %-20s  NMI=%.6f" % (a, b, s))

log("[4] PALAVRAS SIMILARES (amostra)")
for palavra in top[:10]:
    sim = c.palavras_similares(palavra, threshold=0.0, max_resultados=10)
    if sim:
        nomes = ", ".join("%s(%.4f)" % (p, s) for p, s in sim)
        log("  %s -> %s" % (palavra, nomes))

log("[5] COMPARACOES DIRETAS (amostra manual)")
testes = [
    ('criar','gerar'), ('criar','produzir'), ('criar','matar'),
    ('falar','dizer'), ('falar','gritar'), ('falar','comprar'),
    ('comprar','vender'), ('comprar','pegar'),
    ('mago','druida'), ('mago','orc'), ('mago','computador'),
    ('guerreiro','cavaleiro'), ('guerreiro','mago'),
    ('missao','quest'), ('missao','batalha'),
    ('pocao','potion'), ('pocao','armacao'),
    ('rei','rainha'), ('rei','soldado'), ('rei','mendigo'),
    ('bom','otimo'), ('bom','ruim'),
]
for a, b in testes:
    s = c.similaridade(a, b)
    log("  %-12s ~ %-12s NMI=%.6f" % (a, b, s))

log("[6] CLUSTERS EMERGENTES")
for th in [0.70, 0.60, 0.50, 0.40]:
    clusters = c.clusterizar_palavras(threshold=th)
    n = len(clusters)
    total = sum(len(m) for m in clusters.values())
    if n == 0:
        log("  threshold=%.2f: 0 clusters" % th)
        continue
    h = c._entropia_shannon(Counter({cid: len(m) for cid, m in clusters.items()}))
    max_h = math.log2(max(n, 2))
    log("  threshold=%.2f: %d clusters, %d tokens, H_norm=%.3f" % (
        th, n, total, h / max_h if max_h > 0 else 0))
    for cid, membros in sorted(clusters.items()):
        if len(membros) <= 2 and n > 5:
            continue
        log("    %s: %s" % (cid, membros))

log("=== FIM ===")
log("Relatorio salvo em: %s" % SAIDA)
