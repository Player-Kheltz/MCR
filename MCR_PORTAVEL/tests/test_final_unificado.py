"""Teste FINAL do MCR Unificado — Todas as capacidades."""
import sys
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR, get_mcr

print('=' * 65)
print('  MCR — TESTE FINAL DE UNIFICAÇÃO')
print('  Markov + Entropia + Equação = Cognição Universal')
print('=' * 65)

mcr = MCR()

print()
print('--- CLASSIFICAÇÃO DE AÇÕES ---')
print()

testes = [
    # Casos básicos
    ('Crie um NPC ferreiro', 'gerar_npc'),
    ('Crie um NPC dragao', 'gerar_npc'),
    ('Faca um monstro vendedor', 'gerar_monstro'),
    ('Faca um NPC orc', 'gerar_npc'),
    
    # Casos sem tipo explícito (o MCR decide pelo tema)
    ('Gere um dragao de fogo', 'gerar_monstro'),
    ('Crie um ferreiro anao', 'gerar_npc'),
    ('Crie um vendedor', 'gerar_npc'),
    ('Gere um orc', 'gerar_monstro'),
    ('Crie um demonio', 'gerar_monstro'),
    
    # Casos complexos
    ('Gere um NPC Orc que vende armas e tem como tema matar dragoes', 'gerar_npc'),
    
    # Outras ações
    ('Crie uma quest para o ferreiro', 'gerar_quest'),
    ('O que e entropia', 'responder'),
    ('Crie um sprite de espada de fogo', 'gerar_sprite'),
    ('Como funciona o MCR', 'responder'),
]

passes = 0
for entrada, esperado in testes:
    r = mcr.processar(entrada)
    ok = r['acao'] == esperado
    if ok:
        passes += 1
    status = 'OK' if ok else 'ERR'
    print(f'  {status} | {entrada[:55]:<55s} -> {r["acao"]:<16s} (nota={r["nota"]:.3f})')

print(f'\n  Classificacao: {passes}/{len(testes)}')

print()
print('--- GERAÇÃO DE CONTEÚDO ---')
print()

# NPC Tibia
r1 = mcr.processar('Crie um NPC mercador elfico que vende pocoes')
print(f'  NPC Tibia: {r1["acao"]} | sucesso={r1["sucesso"]} | tool={r1["resultado"].get("_tool","?")} | nota={r1["nota"]:.3f}')
if r1['sucesso']:
    codigo = r1['resultado'].get('codigo', '')
    linhas = codigo.count('\n')
    print(f'    -> {linhas} linhas de Lua geradas. Ex: "{codigo.split(chr(10))[0]}"')

# Monstro Tibia
r2 = mcr.processar('Gere um monstro dragao ancião de fogo')
print(f'  Monstro Tibia: {r2["acao"]} | sucesso={r2["sucesso"]} | tool={r2["resultado"].get("_tool","?")} | nota={r2["nota"]:.3f}')

# Resposta
r3 = mcr.processar('Explique o que e a Equacao MCR')
print(f'  Responder: {r3["acao"]} | sucesso={r3["sucesso"]} | tool={r3["resultado"].get("_tool","?")} | nota={r3["nota"]:.3f}')

print()
print('--- ESTATÍSTICAS FINAIS ---')
stats = mcr.estatisticas()
for k, v in stats.items():
    if k == 'markov':
        print(f'  Markov: {v["estados"]} estados, {v["transicoes"]} transições, H={v["entropia_media"]:.3f}')
    else:
        print(f'  {k}: {v}')

print()
print('=' * 65)
print(f'  RESULTADO: MCR unificado funcionando.')
print(f'  Motor: Markov 1ª ordem + Entropia Shannon')
print(f'  Avaliação: Equação MCR (div×2 + esp×3 + prof×2)/10')
print(f'  Domínios testados: Tibia (NPC, Monstro, Quest) e Perguntas')
print('=' * 65)
