#!/usr/bin/env python3
"""Geracao de quest completa: NPC + ActionID + verificacao SPA + recompensa.
Testa capacidade do MCR-DevIA de manter contexto multi-arquivo."""
import sys, os, time, re, json
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm, _decider, _validator

# ─── 1. Classifica a tarefa ───────────────────────────────────
pergunta_base = "Crie uma quest completa para o Projeto MCR: O Guardiao da Floresta"
classe, conf = _decider.classificar(pergunta_base)
print(f'[CLASSIFICACAO] {classe} ({conf:.2f})')

# ─── 2. Le um exemplo real de quest action do Canary ──────────
# Procura um action real
acoes_dir = r'E:\Projeto MCR\Canary\data-canary\scripts\actions'
exemplo_action = ""
for f in os.listdir(acoes_dir):
    for raiz, _, arquivos in os.walk(acoes_dir):
        for f2 in arquivos:
            if not f2.endswith('.lua'):
                continue
            caminho = os.path.join(raiz, f2)
            with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                conteudo = fh.read()
            if 'onUse' in conteudo and 'item' in conteudo and 'Action' in conteudo:
                exemplo_action = conteudo[:1500]
                break
        if exemplo_action:
            break
    break

# ─── 3. Prompt unificado para quest completa ─────────────────
prompt = (
    # Contexto do projeto
    "PROJETO MCR: servidor Tibia customizado. SPA = Sistema de Progressao do Aventureiro.\n"
    "getNivelPorAfinidade(afinidade) retorna nivel 0-20. "
    "adicionarAfinidade(player, dominioId, pts) concede afinidade.\n"
    "IDs: Sobrevivencia=400, Natureza=4.\n\n"
    
    "REGRAS SPA:\n"
    "- NUNCA use function manual em efeito. Use APENAS efeitoConfig.\n"
    "- Para verificar nivel de dominio: player:getDominioAfinidade(dominioId)\n"
    "- Para conceder afinidade: adicionarAfinidade(player, dominioId, pts)\n"
    "- msg.addString() SEMPRE com toLatin1() antes.\n\n"
    
    "CRIE UMA QUEST COMPLETA chamada 'O Artefato Perdido':\n\n"
    
    "=== ARQUIVO 1: NPC (MCR/Quest/guardiao_floresta.lua) ===\n"
    "Nome: Guardiao da Floresta\n"
    "Personalidade: Sabio, protetor da natureza.\n"
    "Objetivo: Oferece a quest, verifica requisito SPA, recebe item, da recompensa.\n"
    "- Usar NpcUtils.getTratamento(player) para pronome\n"
    "- Usar c('{texto}', COR.MISSAO_COLETAR) para missoes\n"
    "- Usar c('{texto}', COR.NPC_ITEM) para itens\n"
    "- Usar COR.NPC_DIALOGO para narrativa\n"
    "- Usar COR.SUCESSO_CURA para recompensa\n"
    "- Estrutura Canary: keywordHandler, NpcHandler, creatureSayCallback\n"
    "- Verificar se player tem level 5 em Sobrevivencia (400): "
    "getNivelPorAfinidade(player:getDominioAfinidade(400)) >= 5\n"
    "- Recompensa: adicionarAfinidade(player, 400, 100) + enviarMsgColorida\n"
    "- Salvar progresso em storage = 60000\n\n"
    
    "=== ARQUIVO 2: Action (actions/quest_artefato.lua) ===\n"
    "ActionID do bau: 50001\n"
    "- Verificar storage 60000 == 1 (aceitou quest)\n"
    "- Verificar se player tem o item Artefato (id 12345)\n"
    "- Se sim: remover item, setar storage 60000 = 2, enviar msg\n"
    "- Usar Action() padrao do Canary\n\n"
    
    "Exemplo de Action do Canary:\n" + (exemplo_action[:800] if exemplo_action else "") + "\n\n"
    
    "Responda EXATAMENTE no formato abaixo, com os dois blocos separados por '---ARQUIVO 2---':\n"
    "=== ARQUIVO 1 ===\n[CODIGO NPC]\n---ARQUIVO 2---\n=== ARQUIVO 2 ===\n[CODIGO ACTION]\n"
)

t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.3)
t = time.time() - t0

print(f'\n[TEMPO] {t:.1f}s')
print(f'[TAMANHO] {len(resp)} chars')

# ─── 4. Separa os arquivos gerados ────────────────────────────
arquivo1, arquivo2 = "", ""
if '=== ARQUIVO 2 ===' in resp or '---ARQUIVO 2---' in resp:
    separador = '=== ARQUIVO 2 ===' if '=== ARQUIVO 2 ===' in resp else '---ARQUIVO 2---'
    partes = resp.split(separador, 1)
    if len(partes) >= 2:
        arquivo1 = partes[0][:2500]
        arquivo2 = '=== ARQUIVO 2 ===\n' + partes[1][:2500]
else:
    # Fallback: tenta encontrar HABILIDADES ou Action
    if 'Action' in resp or 'onUse' in resp:
        arquivo2 = resp
    else:
        arquivo1 = resp

print(f'\n[ARQUIVO 1 - NPC] {len(arquivo1)} chars')
print(arquivo1[:1500])
print(f'\n[ARQUIVO 2 - ACTION] {len(arquivo2)} chars')
print(arquivo2[:1500])

# ─── 5. Valida contra requisitos ──────────────────────────────
checks = [
    ('NpcHandler', 'npcHandler' in arquivo1 or 'NpcHandler' in resp),
    ('Pronome (getTratamento)', 'getTratamento' in arquivo1 or 'getTratamento' in resp),
    ('COR.*', 'COR.' in resp),
    ('c() com chaves', 'c(' in resp and '{' in resp),
    ('Verificacao SPA (Sobrevivencia 400)', '400' in resp and ('getDominioAfinidade' in resp or 'getNivel' in resp)),
    ('Storage 60000', '60000' in resp),
    ('adicionarAfinidade', 'adicionarAfinidade' in resp),
    ('Action (onUse)', 'Action' in arquivo2 or 'onUse' in resp or 'action' in resp.lower()),
    ('Item ID 12345', '12345' in resp),
    ('Recompensa XP', 'adicionarAfinidade' in resp or 'reward' in resp.lower() or 'xp' in resp.lower()),
]
ok = sum(1 for _, v in checks if v)
print(f'\n[CHECKS] {ok}/{len(checks)}')
for nome, v in checks:
    print(f'  {"OK" if v else "X"} {nome}')

# ─── 6. Salva os arquivos ────────────────────────────────────
if arquivo1 and len(arquivo1) > 200:
    caminho1 = r'E:\Projeto MCR\scripts\generated\quest_guardiao_npc.lua'
    os.makedirs(os.path.dirname(caminho1), exist_ok=True)
    with open(caminho1, 'w', encoding='utf-8') as f:
        f.write(arquivo1)
    print(f'\n[SAVE] NPC -> {caminho1}')

if arquivo2 and len(arquivo2) > 200:
    caminho2 = r'E:\Projeto MCR\scripts\generated\quest_guardiao_action.lua'
    os.makedirs(os.path.dirname(caminho2), exist_ok=True)
    with open(caminho2, 'w', encoding='utf-8') as f:
        f.write(arquivo2)
    print(f'[SAVE] Action -> {caminho2}')

print(f'\n[VEREDITO] {"Quest completa gerada!" if ok >= 7 else "Precisa melhorar"} ({ok}/{len(checks)})')
