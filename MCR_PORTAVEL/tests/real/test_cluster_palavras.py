"""test_cluster_palavras — Prova de que MCR clusteriza palavras por assinatura markoviana.

Sem rotulos humanos. Sem dicionario. Sem IA externa.
Apenas Markov + Entropia + NMI sobre dados observados.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling

def _entropia_shannon(d):
    total = sum(d.values()) or 1
    h = 0.0
    for v in d.values():
        p = v / total
        if p > 0:
            h -= p * math.log2(p)
    return h

# === DADOS: verbos de criacao, entidades magicas, ferramentas ===
pares = [
    # Verbos de CRIACAO — contextualmente similares
    ("criar monstro", "criar_monstro"),
    ("criar mago aliado", "criar_npc"),
    ("criar ferreiro na vila", "criar_npc"),
    ("gerar monstro aleatorio", "criar_monstro"),
    ("gerar dragao", "criar_monstro"),
    ("gerar mago novo", "criar_npc"),
    ("produzir pocao", "produzir_item"),
    ("produzir armadura", "produzir_item"),
    ("produzir ferramenta", "produzir_item"),

    # Verbos de COMBATE — outro cluster
    ("atacar monstro", "atacar"),
    ("atacar dragao", "atacar"),
    ("lutar contra orc", "atacar"),
    ("lutar contra mago", "atacar"),
    ("golpear ferreiro", "atacar"),

    # Verbos de CURAR — outro
    ("curar ferido", "curar"),
    ("curar aliado", "curar"),
    ("restaurar vida", "curar"),
    ("restaurar mago", "curar"),

    # Entidades: ferramentas (outro cluster)
    ("usar martelo", "usar_ferramenta"),
    ("usar espada", "usar_ferramenta"),
    ("usar pocao", "usar_item"),
    ("empunhar espada", "usar_ferramenta"),
    ("empunhar martelo", "usar_ferramenta"),

    # Verbos de ANALISE
    ("analisar monstro", "analisar"),
    ("analisar dragao", "analisar"),
    ("examinar mago", "analisar"),
    ("examinar ferreiro", "analisar"),
]

print("=" * 70)
print("MCR CLUSTERIZACAO DE PALAVRAS POR ASSINATURA MARKOVIANA")
print("=" * 70)

c = MCRCoupling()
c.alimentar_lote(pares)

# Gera clusters
clusters = c.clusterizar_palavras(threshold=0.50)
print("\n=== CLUSTERS DESCOBERTOS (threshold=0.50) ===")
for cid, membros in sorted(clusters.items()):
    print(f"  {cid}: {membros}")

# Analise de cada cluster: entropia das assinaturas internas
print("\n=== ANALISE ENTROPICA DOS CLUSTERS ===")
for cid, membros in sorted(clusters.items()):
    if len(membros) < 2:
        continue
    entropias = {}
    for p in membros:
        d = dict(c._palavra_acao.get(p, {}))
        h = _entropia_shannon(d) if d else 0
        entropias[p] = round(h, 3)
    h_cluster = sum(entropias.values()) / len(entropias)
    print(f"  {cid} (H_media={h_cluster:.3f}): {entropias}")

# Valida a hipotese central da Equacao MCR:
# NMI no cluster INTERNO vs INTER-CLUSTER
print("\n=== VALIDACAO: INTRA vs INTER CLUSTER ===")
print(f"  {'Par':<25} {'Cluster':<15} {'NMI':>8}")
print("  " + "-" * 50)
for cid, membros in sorted(clusters.items()):
    for i, a in enumerate(membros):
        for b in membros[i+1:]:
            from collections import defaultdict
            feat_a = defaultdict(int)
            for k, v in c._palavra_acao.get(a, {}).items():
                feat_a[f"acao:{k}"] += v
            for k, v in c._transicao_palavra.get(a, {}).items():
                feat_a[f"ctx:{k}"] += v
            feat_b = defaultdict(int)
            for k, v in c._palavra_acao.get(b, {}).items():
                feat_b[f"acao:{k}"] += v
            for k, v in c._transicao_palavra.get(b, {}).items():
                feat_b[f"ctx:{k}"] += v
            nmi = c._nmi(dict(feat_a), dict(feat_b))
            print(f"  {a:<10}~{b:<10} {cid:<15} {nmi:>8.4f}")

# Cross-cluster
print("\n  --- CROSS-CLUSTER ---")
ids = sorted(clusters.keys())
for i, cida in enumerate(ids):
    for cidb in ids[i+1:]:
        a = clusters[cida][0]
        b = clusters[cidb][0]
        feat_a = defaultdict(int)
        for k, v in c._palavra_acao.get(a, {}).items():
            feat_a[f"acao:{k}"] += v
        for k, v in c._transicao_palavra.get(a, {}).items():
            feat_a[f"ctx:{k}"] += v
        feat_b = defaultdict(int)
        for k, v in c._palavra_acao.get(b, {}).items():
            feat_b[f"acao:{k}"] += v
        for k, v in c._transicao_palavra.get(b, {}).items():
            feat_b[f"ctx:{k}"] += v
        nmi = c._nmi(dict(feat_a), dict(feat_b))
        print(f"  {a:<10}~{b:<10} {cida:<7}/{cidb:<7} {nmi:>8.4f}")

# TESTE FINAL: aplicar no similaridade()
print("\n=== TESTE: similaridade() com cluster como regularizador ===")
c._word_clusters = clusters
pares_teste = [
    ("criar", "gerar", "verbos de criacao — SINONIMOS DEVERIAM SER ALTOS"),
    ("criar", "produzir", "criacao vs producao — relacionados"),
    ("criar", "atacar", "criacao vs combate — DIFERENTES"),
    ("criar", "curar", "criacao vs cura — DIFERENTES"),
    ("atacar", "lutar", "combate vs combate — SINONIMOS"),
    ("atacar", "golpear", "combate — relacionados"),
    ("curar", "restaurar", "cura — SINONIMOS"),
    ("curar", "analisar", "cura vs analise — DIFERENTES"),
    ("mago", "ferreiro", "entidades via ctx — associados indiretos"),
    ("monstro", "dragao", "entidades de combate — co-ocorrentes"),
    ("usar", "empunhar", "uso de ferramentas — SINONIMOS"),
    ("usar", "analisar", "ferramenta vs analise — DIFERENTES"),
    ("criar", "usar", "criacao vs uso — DIFERENTES"),
]
print(f"  {'Par':<25} {'Score':>8}  {'Esperado'}")
print("  " + "-" * 70)
for a, b, expected in pares_teste:
    score = c.similaridade(a, b)
    print(f"  {a:<10}~{b:<10} {score:>8.4f}  {expected}")


