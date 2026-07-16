"""TESTE DE FOGO — MCR com pipeline REAL.

Usa golden examples do KG + contexto do mundo + LLM sem limite de tokens.
"""
import sys, json, time, urllib.request
sys.path.insert(0, 'E:/MCR')
sys.path.insert(0, 'E:/MCR/devia/kernel')

from mcr.config_llm import MODELO

OLLAMA = "http://localhost:11434/api/generate"
t_global = time.time()

print('=' * 65)
print('  TESTE DE FOGO — MCR Pipeline REAL')
print(f'  Modelo: {MODELO}')
print('=' * 65)

def chamar(prompt, temp=0.3):
    """Chamada sem num_predict (modelo decide o tamanho)."""
    payload = json.dumps({
        "model": MODELO, "prompt": prompt, "stream": False,
        "options": {"temperature": temp, "num_ctx": 32768}
    }).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
            resp = data.get('response', '')
            think = data.get('thinking', '')
            return resp.strip() if resp else think.strip()
    except Exception as e:
        return f"[ERRO: {e}]"

# ─── CARREGAR GOLDEN EXAMPLES DO KG ────────────────────────
print('\n[0] Carregando Golden Examples + Contexto')
print('-' * 45)

from mcr.paths import KG_DIR, CANARY_NPC_DIR, CANARY_MONSTER_DIR
from mcr.encoding import read_file
import os

# Busca exemplos no KG
golden_npc = []
golden_monstro = []
for f in sorted(KG_DIR.glob('patterns_*.json')):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            dados = json.load(fh)
        for p in dados.get('padroes', []):
            arquivo = p.get('arquivo', '')
            tipo = p.get('tipo', '')
            if tipo == 'npc' and arquivo and os.path.exists(arquivo):
                golden_npc.append(arquivo)
            elif tipo in ('monster', 'monstro') and arquivo and os.path.exists(arquivo):
                golden_monstro.append(arquivo)
    except Exception:
        pass

# Se não achou no KG, busca direto nos diretórios
if not golden_npc:
    for f in sorted(CANARY_NPC_DIR.glob('*.lua'))[:5]:
        if f.stat().st_size < 10000:
            golden_npc.append(str(f))
if not golden_monstro:
    for f in sorted(CANARY_MONSTER_DIR.glob('*.lua'))[:5]:
        if f.stat().st_size < 10000:
            golden_monstro.append(str(f))

print(f'  Golden NPCs: {len(golden_npc)} exemplos')
print(f'  Golden Monstros: {len(golden_monstro)} exemplos')

# ─── CARREGAR EXEMPLOS ─────────────────────────────────────
exemplo_npc = ""
for path in golden_npc[:3]:
    try:
        code = read_file(path)
        exemplo_npc += f"\n--- EXEMPLO: {os.path.basename(path)} ---\n{code[:1200]}\n"
    except Exception:
        pass

exemplo_monstro = ""
for path in golden_monstro[:3]:
    try:
        code = read_file(path)
        exemplo_monstro += f"\n--- EXEMPLO: {os.path.basename(path)} ---\n{code[:1200]}\n"
    except Exception:
        pass

print(f'  Exemplo NPC: {len(exemplo_npc)} chars')
print(f'  Exemplo Monstro: {len(exemplo_monstro)} chars')

# ─── TESTE 1: NPC COM GOLDEN EXAMPLES ──────────────────────
print('\n[1] NPC — Qwen3.5 + Golden Examples + SanityValidator')
print('-' * 45)

prompt_npc = f"""Voce e um gerador de scripts Lua para o servidor Tibia Canary (OTServ).

REGRAS ABSOLUTAS:
1. Use APENAS APIs Canary reais mostradas nos exemplos abaixo
2. NAO invente APIs. Se nao sabe, copie o padrao dos exemplos
3. Estrutura obrigatoria: internalNpcName, Game.createNpcType, npcConfig, npcType:register
4. Para NPCs vendedores: npcConfig.shop = {{...}} com itens reais

GOLDEN EXAMPLES (use estes como template EXATO):
{exemplo_npc[:3000]}

TAREFA: Crie um NPC ferreiro anão chamado Brunin Forjador que vende armaduras.
Use o MESMO formato dos exemplos acima."""

t0 = time.time()
codigo_npc = chamar(prompt_npc, temp=0.3)
tempo_npc = time.time() - t0

if codigo_npc:
    # Extrai só o código Lua (remove markdown, explicações)
    import re
    blocos = re.findall(r'```lua\n(.*?)```', codigo_npc, re.DOTALL)
    if blocos:
        codigo_npc = blocos[0]
    linhas = codigo_npc.count('\n') + 1
    tem_nome = 'internalNpcName' in codigo_npc
    tem_create = 'Game.createNpcType' in codigo_npc
    tem_register = 'npcType:register' in codigo_npc or ':register()' in codigo_npc
    tem_shop = 'npcConfig.shop' in codigo_npc or 'shop =' in codigo_npc
    
    print(f'  Gerado: {linhas} linhas em {tempo_npc:.1f}s')
    print(f'  Nome={tem_nome} Create={tem_create} Register={tem_register} Shop={tem_shop}')
    print(f'  Preview:')
    for l in codigo_npc.split('\n')[:10]:
        print(f'    {l[:110]}')
    
    # Validação estrutural
    erros = []
    if not tem_nome: erros.append('Falta internalNpcName')
    if not tem_create: erros.append('Falta Game.createNpcType')
    if not tem_register: erros.append('Falta npcType:register')
    if erros:
        print(f'  ERROS: {erros}')
    
    # Validar com SanityValidator
    try:
        from mcr.sanity_validator import SanityValidator
        sv = SanityValidator()
        val = sv.validar_codigo(codigo_npc)
        desconhecidas = val.get('apis_desconhecidas', [])
        if desconhecidas:
            print(f'  APIs desconhecidas: {desconhecidas[:5]}')
        else:
            print(f'  SanityValidator: OK (0 APIs desconhecidas)')
    except Exception as e:
        print(f'  SanityValidator: indisponivel ({e})')
else:
    print(f'  FALHA: resposta vazia')

# ─── TESTE 2: MONSTRO COM GOLDEN EXAMPLES ─────────────────
print('\n[2] Monstro — Qwen3.5 + Golden Examples')
print('-' * 45)

prompt_monstro = f"""Voce e um gerador de scripts Lua para o servidor Tibia Canary (OTServ).

REGRAS ABSOLUTAS:
1. Use APENAS APIs Canary reais mostradas nos exemplos abaixo
2. NAO invente APIs. Copie o padrao EXATO dos exemplos

GOLDEN EXAMPLES (use estes como template EXATO):
{exemplo_monstro[:3000]}

TAREFA: Crie um monstro Dragao de Lava Anciao. Use o MESMO formato dos exemplos."""

t0 = time.time()
codigo_monstro = chamar(prompt_monstro, temp=0.3)
tempo_monstro = time.time() - t0

if codigo_monstro:
    blocos = re.findall(r'```lua\n(.*?)```', codigo_monstro, re.DOTALL)
    if blocos:
        codigo_monstro = blocos[0]
    linhas = codigo_monstro.count('\n') + 1
    tem_mtype = 'MonsterType' in codigo_monstro
    tem_register = 'register' in codigo_monstro.lower()
    tem_loot = 'loot' in codigo_monstro.lower()
    
    print(f'  Gerado: {linhas} linhas em {tempo_monstro:.1f}s')
    print(f'  MonsterType={tem_mtype} Register={tem_register} Loot={tem_loot}')
    print(f'  Preview:')
    for l in codigo_monstro.split('\n')[:8]:
        print(f'    {l[:110]}')
else:
    print(f'  FALHA: resposta vazia')

# ─── TESTE 3: LORE ─────────────────────────────────────────
print('\n[3] Lore — Qwen3.5 geração narrativa')
print('-' * 45)

prompt_lore = """Voce e um narrador de fantasia medieval.

Crie a historia de fundo de Eridanus, a cidade inicial do mundo MCR.
- E um vale entre montanhas
- Cidade comercial governada por Conselho de Mercadores
- Tensao com orcs das montanhas ao norte
- Porto comercial e a principal fonte de riqueza

3 paragrafos concisos em Portugues, tom epico."""

t0 = time.time()
lore = chamar(prompt_lore, temp=0.9)
tempo_lore = time.time() - t0

if lore:
    palavras = len(lore.split())
    paragrafos = len([p for p in lore.split('\n\n') if p.strip()])
    print(f'  Gerado: {palavras} palavras, {paragrafos} paragrafos em {tempo_lore:.1f}s')
    print(f'  Lore:')
    for p in lore.split('\n\n')[:4]:
        if p.strip():
            print(f'    {p.strip()[:150]}')
else:
    print(f'  FALHA: resposta vazia')

# ─── RESULTADO ─────────────────────────────────────────────
print(f'\n{"="*65}')
print(f'  RESULTADO FINAL — {time.time()-t_global:.0f}s')
print(f'  Modelo: {MODELO} ({6.6}GB, 100% GPU)')
print(f'{"="*65}')
print(f'  NPC: {tempo_npc:.0f}s | Monstro: {tempo_monstro:.0f}s | Lore: {tempo_lore:.0f}s')
print(f'{"="*65}')
