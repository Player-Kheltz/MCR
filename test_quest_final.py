import sys, os, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

pergunta = (
    "Crie uma quest completa chamada O Anel Perdido. "
    "O NPC Guarda Real na cidade deve pedir para o jogador encontrar "
    "um anel (item 2133) escondido em um bau (ActionID 5000) e traze-lo de volta. "
    "Se o jogador trouxer, ganha 10000 de experiencia e 500 gold. "
    "Use a estrutura do Canary: quest storage 60001, "
    "npcConfig.shop para recompensa. "
    "Gere o codigo COMPLETO do NPC e da Action. "
    "Separe os arquivos com marcadores: --- NPC.lua --- e --- ACTION.lua ---"
)

print(f'[TESTE] Quest: O Anel Perdido')
print(f'Prompt: {pergunta[:80]}...')
print()

t0 = time.time()
r = processar(pergunta)
t = time.time() - t0

resp = r.get('resposta', '')
cl = r.get('classe', '?')
sv = r.get('sintaxe_valida')
arqs = r.get('arquivos_salvos', [])

print(f'Tempo: {t:.1f}s')
print(f'Classe: {cl}')
print(f'Sintaxe: {sv}')
print(f'Tamanho: {len(resp)}')
print()

# Verifica se tem blocos de codigo
if '```lua' in resp:
    print(f'[EXTRAIDO] Bloco(s) ```lua encontrados')
    import re
    blocos = re.findall(r'```lua\n(.*?)```', resp, re.DOTALL)
    print(f'  -> {len(blocos)} blocos extraidos')
    for i, b in enumerate(blocos):
        print(f'  Bloco {i+1}: {len(b)} chars - {b[:60].strip()}...')

# Verifica palavras-chave da quest
checks = {
    'storage 60001': '60001' in resp,
    'item 2133': '2133' in resp,
    'ActionID 5000': '5000' in resp or 'Action' in resp,
    'recompensa XP': '10000' in resp,
    'NPC Guarda Real': 'Guarda' in resp,
}
print(f'\n[CHECKS QUEST]')
ok = 0
for nome, v in checks.items():
    print(f'  {"OK" if v else "X"} {nome}')
    if v: ok += 1
print(f'  Total: {ok}/{len(checks)}')

# Verifica arquivos salvos
if arqs:
    print(f'\n[ARQUIVOS SALVOS]')
    for a in arqs:
        size = os.path.getsize(a) if os.path.exists(a) else 0
        print(f'  {a} ({size} bytes)' if size else f'  {a}')
