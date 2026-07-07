"""Teste real: MCR-DevIA fazendo tarefas sem interferencia."""
import sys, os, time
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\Projeto MCR\historia\scripts\mcr_devia')
from fix_mcr_devia_v2 import MCRDevIARevived

d = MCRDevIARevived()

tarefas = [
    # Tarefas que o pipeline consegue executar hoje
    ('leia o progresso.md', 'ler_arquivo'),
    ('explique o que e SPA', 'explicar_conceito'),
    ('traduza "hello world" para PT-BR', 'traduzir_texto'),
]

for pergunta, classe_esperada in tarefas:
    print(f'> {pergunta}')
    t0 = time.time()
    r = d.processar(pergunta)
    t = time.time() - t0
    
    classe = r.get('classe', '?')
    acertos = 'OK' if classe == classe_esperada else 'X'
    print(f'  [{acertos}] classe={classe} pipeline={r.get("acoes")} tempo={t:.2f}s')
    
    if r.get('resposta'):
        print(f'  resposta: {r["resposta"][:150]}')
    print()

# Teste de aprendizado
print('--- APRENDIZADO ---')
antes = d.decider.total
d.decider.aprender('crie um monstro de fogo', 'criar_habilidade_spa')
classe, conf = d.decider.classificar('crie um monstro de fogo')
depois = d.decider.total
print(f'  seeds: {antes} -> {depois}')
print(f'  "crie um monstro de fogo" -> {classe} ({conf:.2f})')
