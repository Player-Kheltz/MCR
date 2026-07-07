#!/usr/bin/env python3
"""Frente 1 — Gerador de Dialogo NPC com Lore e Padrao Limpo v3.3.
Le a lore_base, formata dialogo com c() e {chaves}."""
import sys, os, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm

# 1. Le a lore existente
lore_dir = r'E:\Projeto MCR\lore_base'
lore_conteudo = ""
for f in sorted(os.listdir(lore_dir)):
    if not f.endswith('.md'):
        continue
    caminho = os.path.join(lore_dir, f)
    with open(caminho, 'r', encoding='utf-8') as fh:
        lore_conteudo += f"--- {f} ---\n{fh.read()}\n\n"

print(f'[LOREBASE] {len(lore_conteudo)} chars carregados')

# 2. Prompt com Padrao Limpo v3.3
prompt = (
    lore_conteudo + "\n\n"
    "Com base na lore acima, crie UM dialogo de NPC completo em Lua "
    "para um Sacerdote do Deus Pyros (Deus do Fogo). "
    "O NPC se chama 'Sumo Sacerdote Ignis' e esta localizado no templo em Vulcanic Wastes.\n\n"
    "REGRAS DE FORMATACAO (Padrao Limpo v3.3):\n"
    "- Maximo 3-4 palavras coloridas por frase.\n"
    "- Use c('{palavra}', COR.NPC_COMANDO) para acoes.\n"
    "- Use c('{item}', COR.NPC_ITEM) para itens.\n"
    "- Use c('{local}', COR.NPC_LOCAL) para locais.\n"
    "- NUNCA usar travessao longo (—). Usar hifen (-).\n"
    "- Formato: [Nome] Frase em Alvo - Efeito.\n"
    "- Texto narrativo em cor NEUTRA (COR.NPC_DIALOGO).\n"
    "- Nomes de siglas: SPA = Sistema de Progressao do Aventureiro.\n\n"
    "O dialogo deve ter:\n"
    "1. Saudacao inicial (com pronome do jogador usando NpcUtils.getTratamento)\n"
    "2. Oferecimento de quest (mencionando {chaves} e COR apropriadas)\n"
    "3. Dialogo de progresso e conclusao\n\n"
    "Use a estrutura do Canary: npcType, npcHandler, creatureSayCallback, "
    "Pronouns, COR, c(), enviarMsgColorida.\n"
    "Responda APENAS com o codigo Lua completo."
)

t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.4)
t = time.time() - t0

print(f'\n[TEMPO] {t:.1f}s')
print(f'[TAMANHO] {len(resp)} chars')
print(resp[:3000])
print()

# 3. Valida contra padrao limpo
checks = [
    ('Usa COR.*', 'COR.' in resp),
    ('Usa c()', 'c(' in resp),
    ('Usa {chaves}', '{' in resp and '}' in resp),
    ('NpcUtils.getTratamento', 'getTratamento' in resp or 'Pronouns' in resp),
    ('NpcHandler', 'npcHandler' in resp),
    ('npcType:register', 'register' in resp),
    ('Nao contem travessao longo', '\u2014' not in resp and '\u2015' not in resp),
    ('Contem hifen', '-' in resp),
    ('Tem saudacao + quest + conclusao', 
     any(p in resp.lower() for p in ['saudac', 'bem-vind', 'ola', 'saudaco']) 
     and any(p in resp.lower() for p in ['quest', 'missao', 'ajudar', 'preciso'])),
    ('EnviarMsgColorida ou sendTextMessage', 'sendTextMessage' in resp or 'enviarMsgColorida' in resp),
]
ok_count = sum(1 for _, ok in checks if ok)
print(f'[CHECKS] {ok_count}/{len(checks)}')
for nome, ok in checks:
    print(f'  {"OK" if ok else "X"} {nome}')
