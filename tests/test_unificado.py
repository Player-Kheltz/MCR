"""Teste do MCR unificado — casos ambíguos."""
import sys
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR

mcr = MCR()

tests = [
    ('Crie um NPC ferreiro', 'gerar_npc'),
    ('Crie um NPC dragao', 'gerar_npc'),
    ('Faca um monstro vendedor', 'gerar_monstro'),
    ('Faca um NPC orc', 'gerar_npc'),
    ('Gere um dragao de fogo', 'gerar_monstro'),
    ('Crie um ferreiro anao', 'gerar_npc'),
    ('Crie um vendedor', 'gerar_npc'),
    ('Gere um orc', 'gerar_monstro'),
    ('Crie uma quest', 'gerar_quest'),
    ('O que e entropia', 'responder'),
    ('Crie um sprite de espada', 'gerar_sprite'),
]

print('=' * 60)
print('  TESTE: MCR Unificado — Classificacao de acoes')
print('=' * 60)

passes = 0
falhas = 0

for entrada, esperado in tests:
    r = mcr.processar(entrada)
    ok = r['acao'] == esperado
    if ok:
        passes += 1
        status = 'OK'
    else:
        falhas += 1
        status = 'ERR'
    print(f'{status} | {entrada:<40s} -> {r["acao"]:<15s} (esperado: {esperado}) | nota={r["nota"]:.3f}')

print()
print(f'Resultado: {passes}/{len(tests)} passaram, {falhas} falharam')
print()
print('Estatisticas:', mcr.estatisticas())
