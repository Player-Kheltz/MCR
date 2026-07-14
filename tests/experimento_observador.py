"""EXPERIMENTO: Observador Universal — MCR aprende padrão X→Y.

O MCR observa o PRÓPRIO comportamento como "caixa-preta".
Coleta pares (entrada, saida), aprende associações,
e tenta prever o tipo de saída para entradas novas.

Zero hardcode. Zero conhecimento do domínio.
Apenas fingerprint + cluster + Markov + entropia.
"""
import sys, time, random
sys.path.insert(0, 'E:/MCR')

from mcr.observador import ObservadorUniversal
from mcr.mcr import MCR

print('=' * 65)
print('  EXPERIMENTO — OBSERVADOR UNIVERSAL')
print('  MCR observa seu PRÓPRIO comportamento')
print('=' * 65)

mcr = MCR()
obs = ObservadorUniversal("mcr_auto_obs")

# ═══════════════════════════════════════════════════════════
# FASE 1: COLETAR PARES (X, Y) do MCR pipeline
# ═══════════════════════════════════════════════════════════
print('\n[1] Coletando pares (entrada, saida) do MCR...')

entradas = [
    # NPCs — Português
    "Crie um NPC ferreiro anão", "Crie um NPC mago élfico",
    "Crie um NPC guarda orc", "Crie um NPC vendedor humano",
    "Crie um NPC alquimista", "Crie um NPC druida",
    "Crie um NPC bardo", "Crie um NPC mercador",
    "Crie um NPC padeiro", "Crie um NPC taverneiro",
    "Crie um NPC cavaleiro", "Crie um NPC arqueiro",
    "Crie um NPC ladrão", "Crie um NPC pescador",
    "Crie um NPC ferreiro orc", "Crie um NPC mago sombrio",
    # Monstros
    "Gere um monstro dragão ancião", "Gere um monstro lobo sombrio",
    "Gere um monstro demônio de fogo", "Gere um monstro orc guerreiro",
    "Gere um monstro esqueleto mago", "Gere um monstro ciclope",
    "Gere um monstro vampiro ancião", "Gere um monstro golem de ferro",
    "Gere um monstro serpente marinha", "Gere um monstro dragão de gelo",
    "Gere um monstro rato gigante", "Gere um monstro elfo sombrio",
    # Perguntas
    "Explique o que é entropia", "O que é um NPC no Tibia",
    "Como funciona o sistema SPA", "Explique a Equação MCR",
    "Qual a diferença entre Markov e LLM", "O que é o MCR",
    "Como o MCR aprende padrões", "Explique Shannon",
    # Sprites (espera-se falha — sem dados)
    "Crie um sprite de escudo", "Crie um sprite de espada",
    "Crie um sprite de poção", "Crie um sprite de armadura",
    # Variações paramétricas
    "Crie um NPC ferreiro anão que vende armaduras",
    "Crie um NPC mago que vende poções",
    "Gere um monstro dragão de lava ancião",
    "Gere um monstro orc guerreiro elite",
    # Inglês (cross-idioma)
    "Create an NPC blacksmith", "Create a wizard NPC",
    "Generate a fire dragon", "Generate a shadow wolf",
    "Explain what entropy is", "What is an NPC",
]

pares = []
falhas_coleta = 0
for i, entrada in enumerate(entradas):
    r = mcr.processar(entrada)
    saida_tipo = r.get('acao', '?')
    saida_sucesso = "OK" if r.get('sucesso') else "FAIL"
    saida_texto = f"{saida_tipo}:{saida_sucesso}"
    obs.observar(entrada, saida_texto)
    pares.append((entrada, saida_texto))
    if i % 10 == 0:
        print(f'  [{i+1}/{len(entradas)}] coletados...')

print(f'  Total: {len(pares)} pares coletados ({falhas_coleta} falhas)')

# ═══════════════════════════════════════════════════════════
# FASE 2: TREINAR OBSERVADOR
# ═══════════════════════════════════════════════════════════
print('\n[2] Treinando observador...')
obs.treinar()
stats = obs.estatisticas()
print(f'  Clusters X: {stats["clusters_X"]}')
print(f'  Clusters Y: {stats["clusters_Y"]}')
print(f'  Delta H: {stats["delta_H"]}')
print(f'  Cobertura: {stats["cobertura"]}')
print(f'  Markov: {stats["markov_estados"]} estados, {stats["markov_transicoes"]} transições')

# ═══════════════════════════════════════════════════════════
# FASE 3: VALIDAR PREDIÇÕES
# ═══════════════════════════════════════════════════════════
print('\n[3] Validando predições para entradas NOVAS...')

testes = [
    # Variações NUNCA vistas nos dados de treino
    ("Crie um NPC cozinheiro real", "gerar_npc"),
    ("Gere um monstro dragão vulcânico", "gerar_monstro"),
    ("Explique como funciona Markov", "responder"),
    ("Crie um NPC lenhador élfico", "gerar_npc"),
    ("Gere um monstro elemental de gelo", "gerar_monstro"),
    ("O que é entropia de Shannon", "responder"),
    ("Crie um sprite de anel", "gerar_sprite"),
    ("Create an elven archer NPC", "gerar_npc"),
    ("Generate an ancient ice demon", "gerar_monstro"),
    ("Explain the MCR equation", "responder"),
]

acertos = 0
for entrada, esperado in testes:
    r = mcr.processar(entrada)
    real = r.get('acao', '?')
    ok = real == esperado
    if ok: acertos += 1

    # Predição do observador
    pred, conf, H = obs.predizer_com_confianca(entrada)

    status = "OK" if ok else "ERR"
    pred_str = f"CLUSTER_{pred}" if pred is not None else "?"
    print(f'  {status} | real={real:15s} esperado={esperado:15s} | obs={pred_str:10s} conf={conf:.2f} H={H:.2f} | {entrada[:50]}')

print(f'\n  MCR Pipeline: {acertos}/{len(testes)} classificações corretas')

# ═══════════════════════════════════════════════════════════
# FASE 4: MÉTRICA DE APRENDIZADO
# ═══════════════════════════════════════════════════════════
print('\n[4] Métrica de aprendizado (ΔH):')
delta_H = obs.entropia_delta()
if delta_H < -0.01:
    print(f'  ΔH = {delta_H:.4f} — O OBSERVADOR APRENDEU (entropia reduziu)')
elif delta_H > 0.01:
    print(f'  ΔH = {delta_H:.4f} — Entropia AUMENTOU (mais dados necessários?)')
else:
    print(f'  ΔH = {delta_H:.4f} — Entropia estável (padrão já era determinístico?)')

# ═══════════════════════════════════════════════════════════
# RESULTADO
# ═══════════════════════════════════════════════════════════
print(f'\n{"="*65}')
print(f'  RESULTADO FINAL')
print(f'{"="*65}')
print(f'  Pares observados: {stats["pares_observados"]}')
print(f'  Clusters X/Y: {stats["clusters_X"]}/{stats["clusters_Y"]}')
print(f'  Delta H: {stats["delta_H"]}')
print(f'  MCR classificação: {acertos}/{len(testes)}')
print(f'  Observador cobertura: {stats["cobertura"]:.0%}')
print(f'{"="*65}')
