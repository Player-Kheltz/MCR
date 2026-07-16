"""test_assinatura_nd — Prova da assinatura N-dimensional.

A ideia de Kosmos: cada observacao é uma STRING MULTIDIMENSIONAL.
Quando "criar" vira "gerar", só UM plano muda (token).
Todos os outros planos (bytes, chars, bigrams, trigrams, posicao,
contexto) permanecem IGUAIS. A assinatura N-dimensional revela
que sao a MESMA COISA.

Nao usa cosseno. Nao usa SVD. Nao usa thesaurus.
So Markov + Entropia + N planos.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling

# === FONTE UNICA: um cenario de jogo ===
# A ideia: TODOS os pares compartilham o MESMO contexto geral.
# A unica variacao é a palavra-alvo (criar vs gerar).
# O MCR deve ver que sao quase identicas.

pares = [
    ("criar monstro ferreiro mago", "criar_monstro"),
    ("criar pocao armadura magica", "criar_item"),
    ("criar aliado ferreiro vila", "criar_npc"),
    ("criar dragao fogo monstro", "criar_monstro"),
    ("gerar monstro aleatorio dragao", "criar_monstro"),
    ("gerar mago novo aliado", "criar_npc"),
    ("gerar pocao curativa magica", "criar_item"),
    ("gerar ferreiro monstro dragao", "criar_npc"),
    ("curar aliado ferido mago", "curar"),
    ("curar monstro ferido dragao", "curar"),
    ("curar ferreiro pocao magica", "curar"),
    ("curar dragao ferido fogo", "curar"),
    ("atacar monstro dragao fogo", "atacar"),
    ("atacar mago aliado vila", "atacar"),
    ("atacar ferreiro monstro pocao", "atacar"),
    ("lutar contra orc mago aliado", "atacar"),
    ("lutar contra dragao ferreiro", "atacar"),
    ("analisar monstro dragao ferreiro", "analisar"),
    ("analisar mago aliado vila", "analisar"),
    ("examinar pocao magica aliado", "analisar"),
    ("examinar monstro ferido fogo", "analisar"),
]

c = MCRCoupling()
c.alimentar_lote(pares)

# Assinatura de "criar" = uniao de features de TODOS os planos
# que estao contidas na string "criar"
sig_criar = c._assinatura_palavra("criar")
sig_gerar = c._assinatura_palavra("gerar")
sig_atacar = c._assinatura_palavra("atacar")
sig_curar = c._assinatura_palavra("curar")
sig_analisar = c._assinatura_palavra("analisar")
sig_examinar = c._assinatura_palavra("examinar")
sig_monstro = c._assinatura_palavra("monstro")
sig_mago = c._assinatura_palavra("mago")
sig_dragao = c._assinatura_palavra("dragao")
sig_ferreiro = c._assinatura_palavra("ferreiro")

print("=" * 72)
print("MCR ASSINATURA N-DIMENSIONAL — PROVA DE CONCEITO")
print("=" * 72)

print("\n--- ANALISE DAS ASSINATURAS ---")
for nome, sig in [("criar", sig_criar), ("gerar", sig_gerar),
                  ("atacar", sig_atacar), ("curar", sig_curar),
                  ("analisar", sig_analisar), ("examinar", sig_examinar),
                  ("monstro", sig_monstro), ("mago", sig_mago),
                  ("dragao", sig_dragao), ("ferreiro", sig_ferreiro)]:
    planos = set()
    for k in sig:
        planos.add(k.split(":")[0])
    print(f"  {nome:<12} dim={len(sig):>4}  planos={sorted(planos)}")

# Analise de overlapping entre criar e gerar
print("\n--- OVERLAPPING N-DIMENSIONAL: criar vs gerar ---")
chaves_criar = set(sig_criar.keys())
chaves_gerar = set(sig_gerar.keys())
so_criar = chaves_criar - chaves_gerar
so_gerar = chaves_gerar - chaves_criar
comum = chaves_criar & chaves_gerar

print(f"  Uniao:        {len(chaves_criar | chaves_gerar)}")
print(f"  Comum:        {len(comum)}")
print(f"  So em criar:  {len(so_criar)}")
print(f"  So em gerar:  {len(so_gerar)}")
print(f"  Sobreposicao: {len(comum)/(len(chaves_criar|chaves_gerar)+1e-9)*100:.1f}%")

# Quais planos diferem?
planos_so_criar = set(k.split(":")[0] for k in so_criar)
planos_so_gerar = set(k.split(":")[0] for k in so_gerar)
print(f"  Planos exclusivos de criar: {sorted(planos_so_criar)}")
print(f"  Planos exclusivos de gerar: {sorted(planos_so_gerar)}")

# NMI entre pares
print("\n--- NMI ENTRE PARES (assinatura N-dimensional) ---")
print(f"  {'Par':<20} {'NMI':>8}  {'Interpretacao'}")
print(f"  " + "-" * 60)

pares_teste = [
    ("criar", "gerar", "mesmo verbo em contextos identicos"),
    ("criar", "curar", "verbos diferentes (criar vs curar)"),
    ("criar", "atacar", "verbos diferentes (criar vs atacar)"),
    ("criar", "analisar", "verbos diferentes (criar vs analisar)"),
    ("curar", "restaurar", "cura — sinonimo nao observado"),
    ("atacar", "lutar", "combate — sinonimo nao observado"),
    ("analisar", "examinar", "analise — sinonimos identicos"),
    ("criar", "produzir", "criacao — sinonimo parcial"),
    ("gerar", "produzir", "geracao — sinonimo parcial"),
    ("monstro", "dragao", "entidades co-ocorrentes"),
    ("monstro", "mago", "entidades co-ocorrentes"),
    ("monstro", "ferreiro", "entidades relacionadas"),
    ("mago", "ferreiro", "entidades relacionadas"),
    ("criar", "monstro", "verbo vs entidade"),
    ("criar", "mago", "verbo vs entidade"),
    ("criar", "codigo", "totalmente distante"),
    ("curar", "atacar", "cura vs combate — diferentes"),
    ("curar", "analisar", "cura vs analise — diferentes"),
]

for a, b, desc in pares_teste:
    sig_a = c._assinatura_palavra(a)
    sig_b = c._assinatura_palavra(b)
    if not sig_a or not sig_b:
        print(f"  {a:<9}~{b:<9} {'N/A':>8}  {desc}")
        continue
    nmi = c._nmi(sig_a, sig_b)
    print(f"  {a:<9}~{b:<9} {nmi:>8.4f}  {desc}")

# Mesmo teste via similaridade() publica
print("\n--- TESTE: similaridade() PUBLICA COM N-DIMENSIONAL ---")
print(f"  {'Par':<20} {'Score':>8}  {'Interpretacao'}")
print(f"  " + "-" * 60)
for a, b, desc in pares_teste:
    score = c.similaridade(a, b)
    print(f"  {a:<9}~{b:<9} {score:>8.4f}  {desc}")


