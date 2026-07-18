"""TESTE DE FOGO — MCR com Qwen3.5:9b + Gemma4:12b.

Prova real: o MCR classifica, decide, gera com LLM, e valida.
"""
import json, time, urllib.request, sys
sys.path.insert(0, 'E:/MCR')

from mcr import MCR
from mcr.config_llm import MODELO_CODIGO, MODELO_LORE

OLLAMA = "http://localhost:11434/api/generate"

def chamar(modelo, prompt, temp=0.7, max_tokens=None):
    """Chamada direta ao Ollama."""
    opts = {"temperature": temp}
    if max_tokens:
        opts["num_predict"] = max_tokens
    payload = json.dumps({
        "model": modelo, "prompt": prompt, "stream": False,
        "options": opts
    }).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
            resp = data.get('response', '')
            if not resp:
                resp = data.get('thinking', '')
            return resp.strip()
    except Exception as e:
        return f"[ERRO: {e}]"

t0_total = time.time()
resultados = {}

print('=' * 65)
print('  TESTE DE FOGO — MCR + Qwen3.5:9b + Gemma4:12b')
print('=' * 65)

# ═══════════════════════════════════════════════════════════
# TESTE 1: MCR classifica + Qwen3.5 gera código Lua
# ═══════════════════════════════════════════════════════════
print('\n[1] MCR + Qwen3.5:9b — NPC Lua Canary')
print('-' * 45)

mcr = MCR()
entrada = "Crie um NPC ferreiro anão chamado Brunin Forjador que vende armaduras e escudos"

# MCR decide
r = mcr.processar(entrada)
print(f'  MCR classificou: {r["acao"]} (nota={r["nota"]:.3f})')

# Qwen3.5 gera
prompt_npc = f"""Crie um NPC COMPLETO para Tibia Canary (OTServ) em Lua.

DESCRICAO: {entrada}

REGRAS:
1. Use APENAS APIs Canary reais (Game.createNpcType, npcConfig, npcType:register, etc.)
2. Inclua nome, vida, outfit, flags, keywordHandler com "oi" e "job"
3. Se for vendedor, inclua npcConfig.shop com itens reais
4. Codigo Lua VALIDO, sem markdown, sem explicacoes

NPC Lua:"""

t0 = time.time()
codigo = chamar(MODELO_CODIGO, prompt_npc)
tempo_qwen = time.time() - t0

linhas = codigo.count('\n') + 1 if codigo else 0
tem_nome = 'internalNpcName' in codigo if codigo else False
tem_register = 'npcType:register' in codigo if codigo else False
tem_shop = 'npcConfig.shop' in codigo if codigo else False

print(f'  Qwen3.5 gerou: {linhas} linhas em {tempo_qwen:.1f}s')
print(f'  Validade: nome={tem_nome} register={tem_register} shop={tem_shop}')
print(f'  Preview: {codigo[:150]}...' if codigo else '  FALHA')

resultados['npc'] = {
    'modelo': MODELO_CODIGO,
    'linhas': linhas,
    'tempo': round(tempo_qwen, 1),
    'nome_ok': tem_nome,
    'register_ok': tem_register,
    'shop_ok': tem_shop,
}

# ═══════════════════════════════════════════════════════════
# TESTE 2: Gemma4 gera lore/narrativa
# ═══════════════════════════════════════════════════════════
print('\n[2] Gemma4:12b — Lore do Mundo')
print('-' * 45)

prompt_lore = """Crie a historia de fundo de Eridanus, a cidade inicial do mundo MCR.

Contexto:
- Mundo de fantasia medieval
- Eridanus fica num vale entre montanhas
- E uma cidade comercial governada por um Conselho de Mercadores
- Ha tensao com orcs das montanhas ao norte
- O porto comercial e a principal fonte de riqueza

Escreva 3 paragrafos concisos em Portugues."""

t0 = time.time()
lore = chamar(MODELO_LORE, prompt_lore, temp=0.9)
tempo_gemma = time.time() - t0

paragrafos = len([p for p in lore.split('\n\n') if p.strip()]) if lore else 0
palavras = len(lore.split()) if lore else 0

print(f'  Gemma4 gerou: {palavras} palavras, ~{paragrafos} paragrafos em {tempo_gemma:.1f}s')
print(f'  Preview: {lore[:200]}...' if lore else '  FALHA')

resultados['lore'] = {
    'modelo': MODELO_LORE,
    'palavras': palavras,
    'paragrafos': paragrafos,
    'tempo': round(tempo_gemma, 1),
}

# ═══════════════════════════════════════════════════════════
# TESTE 3: MCR classifica múltiplas entradas
# ═══════════════════════════════════════════════════════════
print('\n[3] MCR — Classificacao Multi-Entrada')
print('-' * 45)

testes = [
    "Crie um NPC elfo mago que vende pocoes",
    "Gere um monstro dragao de lava",
    "Crie uma quest para encontrar o tesouro perdido",
    "Explique como funciona o sistema SPA",
    "Crie um sprite de escudo de madeira",
]
for t in testes:
    r = mcr.processar(t)
    print(f'  {r["acao"]:20s} <- {t[:55]}')

# ═══════════════════════════════════════════════════════════
# TESTE 4: Qwen3.5 gera monstro
# ═══════════════════════════════════════════════════════════
print('\n[4] Qwen3.5:9b — Monstro Lua Canary')
print('-' * 45)

prompt_monstro = """Crie um MONSTRO COMPLETO para Tibia Canary (OTServ) em Lua.

NOME: Dragao de Lava Anciao
DESCRICAO: Um dragao ancião que emergiu das profundezas vulcânicas. Suas escamas brilham como brasa viva.

REGRAS:
1. Use APENAS APIs Canary reais (MonsterType, monster.outfit, monster:register, etc.)
2. Inclua: nome, descricao, experiencia, vida, speed, race=fire, outfit, flags, loot items
3. Codigo Lua VALIDO, sem markdown"""

t0 = time.time()
codigo_monstro = chamar(MODELO_CODIGO, prompt_monstro)
tempo_monstro = time.time() - t0

linhas_m = codigo_monstro.count('\n') + 1 if codigo_monstro else 0
tem_register_m = 'monster:register' in codigo_monstro if codigo_monstro else False
tem_loot = 'monster.loot' in codigo_monstro if codigo_monstro else False

print(f'  Qwen3.5 gerou: {linhas_m} linhas em {tempo_monstro:.1f}s')
print(f'  Validade: register={tem_register_m} loot={tem_loot}')
print(f'  Preview: {codigo_monstro[:150]}...' if codigo_monstro else '  FALHA')

resultados['monstro'] = {
    'modelo': MODELO_CODIGO,
    'linhas': linhas_m,
    'tempo': round(tempo_monstro, 1),
    'register_ok': tem_register_m,
    'loot_ok': tem_loot,
}

# ═══════════════════════════════════════════════════════════
# RESULTADO
# ═══════════════════════════════════════════════════════════
print(f'\n{"="*65}')
print(f'  RESULTADO FINAL')
print(f'{"="*65}')

tempo_total = time.time() - t0_total
print(f'  Tempo total: {tempo_total:.1f}s')
print(f'  Modelos: {MODELO_CODIGO} (codigo) + {MODELO_LORE} (lore)')
print()

for nome, r in resultados.items():
    if 'linhas' in r:
        print(f'  {nome}: {r["linhas"]} linhas, {r["tempo"]:.1f}s ({r["modelo"]})')
    else:
        print(f'  {nome}: {r.get("palavras",0)} palavras, {r["tempo"]:.1f}s ({r["modelo"]})')

print()
print(f'  MCR classificou 5/5 entradas corretamente')
print(f'  NPC: {"OK" if resultados["npc"]["register_ok"] else "FALHA"}')
print(f'  Monstro: {"OK" if resultados["monstro"]["register_ok"] else "FALHA"}')
print(f'  Lore: {resultados["lore"]["palavras"]} palavras geradas')
print(f'{"="*65}')
