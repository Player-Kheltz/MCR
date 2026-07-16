"""VALIDAÇÃO COMPLETA: Observador Universal F1-F5."""
import sys, time, json
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR
from mcr.observador import ObservadorUniversal
from mcr.paths import CACHE_DIR

print('=' * 65)
print('  VALIDACAO — OBSERVADOR UNIVERSAL F1-F5')
print('=' * 65)

mcr = MCR()
mcr.ativar_observador()

# ═══════════════════════════════════════════════════════════
# F1+F2: Coleta contínua (cada processar alimenta)
# ═══════════════════════════════════════════════════════════
print('\n[F1+F2] Coletando pares via processar()...')

entradas = [
    "Crie um NPC ferreiro anão", "Crie um NPC mago élfico",
    "Crie um NPC guarda orc", "Crie um NPC vendedor humano",
    "Crie um NPC alquimista", "Crie um NPC druida",
    "Crie um NPC mercador", "Crie um NPC padeiro",
    "Crie um NPC cavaleiro", "Crie um NPC arqueiro",
    "Gere um monstro dragão ancião", "Gere um monstro lobo sombrio",
    "Gere um monstro demônio de fogo", "Gere um monstro orc guerreiro",
    "Gere um monstro esqueleto mago", "Gere um monstro ciclope",
    "Gere um monstro vampiro", "Gere um monstro golem de ferro",
    "Gere um monstro serpente", "Gere um monstro dragão de gelo",
    "Explique o que é entropia", "O que é um NPC",
    "Como funciona o SPA", "Explique a Equação MCR",
    "Crie um sprite de escudo", "Crie um sprite de espada",
    "Crie um NPC ferreiro que vende armaduras",
    "Gere um monstro dragão de lava ancião",
    "Create an NPC blacksmith", "Generate a fire dragon",
    "Explain what entropy is", "Create a wizard NPC",
]

for i, entrada in enumerate(entradas):
    mcr.processar(entrada)

# Treina após coleta
obs = mcr._observador
obs.treinar()

print(f'  Pares coletados: {len(obs._pares)}')
print(f'  Clusters X: {len(set(obs._clusters_x.values()))}')
print(f'  Clusters Y: {len(set(obs._clusters_y.values()))}')

# ═══════════════════════════════════════════════════════════
# F3: Auto-expansão — detecta clusters fracos
# ═══════════════════════════════════════════════════════════
print('\n[F3] Auto-expansão:')
fracos = obs.clusters_fracos()
print(f'  Clusters fracos (H>0.5): {len(fracos)}')
print(f'  Precisa expandir: {obs.precisa_expandir()}')

if obs.precisa_expandir():
    # Gera variações para clusters fracos
    print('  Gerando variações...')
    extra_entradas = [
        "Crie um NPC ferreiro orc que vende escudos",
        "Gere um monstro elemental de fogo ancião",
        "Explique como o MCR aprende padrões",
        "Create an elven archer NPC",
        "Generate an ancient ice demon",
        "What is the MCR equation",
    ]
    for e in extra_entradas:
        mcr.processar(e)
    obs.treinar()
    print(f'  Após expansão: {len(obs._pares)} pares, {len(set(obs._clusters_x.values()))} clustersX')

# ═══════════════════════════════════════════════════════════
# F4: Equação avalia qualidade
# ═══════════════════════════════════════════════════════════
print('\n[F4] Equação avalia observador:')
qual = obs.avaliar_qualidade()
for k, v in qual.items():
    print(f'  {k}: {v}')

# ═══════════════════════════════════════════════════════════
# F5: Validação — predizer entradas novas
# ═══════════════════════════════════════════════════════════
print('\n[F5] Predições para entradas NOVAS:')
testes = [
    ("Crie um NPC lenhador élfico", "gerar_npc"),
    ("Gere um monstro elemental de gelo", "gerar_monstro"),
    ("Explique como funciona Markov", "responder"),
    ("Create a dwarven blacksmith NPC", "gerar_npc"),
    ("Generate a shadow demon lord", "gerar_monstro"),
    ("Explain the Shannon entropy", "responder"),
    ("Crie um NPC cozinheiro real", "gerar_npc"),
    ("Gere um monstro dragão vulcânico", "gerar_monstro"),
]

acertos = 0
for entrada, esperado in testes:
    r = mcr.processar(entrada)
    real = r.get('acao', '?')
    ok = real == esperado
    if ok: acertos += 1

    pred = mcr.predizer_observador(entrada)
    pred_str = f"CY{pred['cluster']}" if pred and pred['cluster'] is not None else "?"

    print(f'  {"OK" if ok else "ERR"} | real={real:15s} esperado={esperado:15s} | obs={pred_str:10s} conf={pred["confianca"] if pred else 0:.2f} | {entrada[:50]}')

print(f'\n  MCR Pipeline: {acertos}/{len(testes)}')
print(f'  dH: {obs.entropia_delta():.4f}')
print(f'  Cobertura: {obs.cobertura():.0%}')
print(f'  Observador pronto: {qual["pronto"]}')

print(f'\n{"="*65}')
print(f'  RESULTADO: {"OK" if qual["pronto"] else "PRECISA DE + DADOS"}')
print(f'{"="*65}')
