"""PASSO 1: Gerar 50 execuções reais para o experimento da equação."""
import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR

mcr = MCR()
print('=' * 65)
print('  GERANDO 50 EXECUÇÕES PARA EXPERIMENTO')
print('=' * 65)

entradas = [
    # ─── Tier 1: NPCs variados (15) ───
    "Crie um NPC ferreiro anão que vende armaduras e escudos",
    "Crie um NPC mago élfico que vende poções",
    "Crie um NPC arqueiro orc",
    "Crie um NPC mercador humano que vende anéis",
    "Crie um NPC padeiro halfling",
    "Crie um NPC taverneiro anão que vende cerveja",
    "Crie um NPC cavaleiro humano",
    "Crie um NPC artesão gnomo",
    "Crie um NPC bibliotecario élfico",
    "Crie um NPC alquimista que vende poções e ingredientes",
    "Crie um NPC mendigo com historia triste",
    "Crie um NPC mensageiro real",
    "Crie um NPC carpinteiro que vende móveis",
    "Crie um NPC tecelão que vende tecidos",
    "Crie um NPC ferreiro orc que vende armas e escudos",

    # ─── Tier 1: Monstros (5) ───
    "Gere um monstro dragão ancião de lava",
    "Gere um monstro lobo sombrio da floresta",
    "Gere um monstro demônio menor do abismo",
    "Gere um monstro filhote de dragão de gelo",
    "Gere um monstro orc guerreiro elite",

    # ─── Perguntas conceituais (5) ───
    "Explique o que é entropia",
    "O que é um NPC no Tibia?",
    "Como funciona o sistema SPA?",
    "Explique a Equação MCR",
    "Qual a diferença entre Markov e LLM?",

    # ─── Erros propositais (5) ───
    "",
    "xyz abc def",
    "Crie um",
    "Gere coisa nenhuma",
    "asdfghjkl qwerty",

    # ─── Sprites (5) ───
    "Crie um sprite de escudo de madeira",
    "Crie um sprite de espada de fogo",
    "Crie um sprite de poção vermelha",
    "Crie um sprite de armadura de ferro",
    "Crie um sprite de anel dourado",

    # ─── Variações paramétricas (15) ───
    "Crie um NPC guarda que vende escudos",
    "Crie um NPC ferreiro sem loja",
    "Gere um monstro dragão de fogo ancião",
    "Gere um monstro rato gigante",
    "Crie um NPC vendedor ambulante",
    "Crie uma quest para recuperar o tesouro perdido",
    "Gere um monstro esqueleto mago",
    "Crie um NPC druida que vende ervas",
    "Gere um monstro ciclope ancião",
    "Crie um NPC ladrão arrependido",
    "Gere um monstro serpente marinha",
    "Crie um NPC cozinheiro real",
    "Gere um monstro golem de ferro",
    "Crie um NPC minerador anão",
    "Gere um monstro vampiro ancião",
]

sucessos = 0
falhas = 0
t0_total = time.time()

for i, entrada in enumerate(entradas):
    t0 = time.time()
    r = mcr.processar(entrada)
    t = time.time() - t0
    status = 'OK' if r['sucesso'] else 'FAIL'
    if r['sucesso']:
        sucessos += 1
    else:
        falhas += 1
    print(f'  [{i+1:2d}/50] {status} | {r["acao"]:15s} | nota={r["nota"]:.3f} | {t:.1f}s | {entrada[:50]}')

print(f'\n{"="*65}')
print(f'  TOTAL: {sucessos} sucessos, {falhas} falhas em {time.time()-t0_total:.0f}s')
print(f'  Execuções no log: {len(mcr._execucoes)}')
print(f'{"="*65}')
