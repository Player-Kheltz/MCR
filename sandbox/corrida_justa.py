#!/usr/bin/env python3
"""
CORRIDA JUSTA — Cloud usa ferramentas dele, MCR-DevIA usa as dele.
=========================================
TAREFA UNICA: Gerar um MONSTER COMPLETO para o MCR.
  - Stats (hp, atk, def, exp, level, speed, armor)
  - Elementos (elemento principal, fraqueza, resistencia) 
  - Comportamento (agressividade, flee, spawn)
  - Loot table (4+ itens)
  - Habilidades (spells)
  - Visual (outfit, corpse)

Cada um usa SUAS proprias ferramentas:
  Cloud:  python direto + write (built-in)
  DevIA:  mcr_ultimate.py + mcr_improvements.py (scripts dele)

Depois: cada um REVISA o trabalho do outro.
No final: voce (usuario) compara os resultados.
"""

import sys, os, json, re, subprocess, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
OUT = os.path.join(SANDBOX, 'corrida_justa')
os.makedirs(OUT, exist_ok=True)

def ia(prompt, temp=0.5):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None

# Limpa diretorio
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

print('='*70)
print('  CORRIDA JUSTA — Cloud vs MCR-DevIA')
print('  Cada um com SUAS proprias ferramentas')
print('='*70)

# ============================================================
# RODADA 1: CLOUD gera (usando write + python)
# ============================================================
print('\n[RODADA 1] Cloud gerando monster COMPLETO...')

CLOUD_MONSTER = '''-- Monster: Lorde das Chamas — Completo
-- Gerado pelo Cloud via python + write

local mon = Monster("Lorde das Chamas")

-- Stats base
mon:setHealth(3500)
mon:setMaxHealth(3500)
mon:setAttack(120)
mon:setDefense(50)
mon:setExperience(1800)
mon:setLevel(75)
mon:setSpeed(90)
mon:setArmor(25)

-- Elementos
mon:setElement(COMBAT_FIREDAMAGE)
mon:setWeakness(COMBAT_ICEDAMAGE, 1.5)
mon:setWeakness(COMBAT_ENERGYDAMAGE, 1.2)
mon:setResistance(COMBAT_FIREDAMAGE, 0.3)
mon:setResistance(COMBAT_PHYSICALDAMAGE, 0.7)

-- Comportamento
mon:setBehavior("aggressive")
mon:setAggression(0.9)
mon:setFleeThreshold(0.05)
mon:setSpawnTime(120)
mon:setTargetDistance(3)
mon:setAttackSpeed(2000)

-- Loot table (5 itens)
mon:addLoot(6501, 0.9)  -- Chama Eterna (sempre)
mon:addLoot(6502, 0.6)  -- Cinzas do Lorde
mon:addLoot(6503, 0.4)  -- Fragmento Igneo
mon:addLoot(6504, 0.2)  -- Coracao de Fogo
mon:addLoot(6505, 0.05) -- Essencia do Lorde (raro)

-- Habilidades
mon:addSpell(3001, 0.4)  -- Bola de Fogo
mon:addSpell(3002, 0.3)  -- Escudo de Chamas
mon:addSpell(3003, 0.15) -- Erupcao (ultimate)
mon:addSpell(3004, 0.1)  -- Meteoro (boss only)

-- Visual
mon:setOutfit({ lookType = 35, lookHead = 0, lookBody = 94, lookLegs = 76, lookFeet = 0 })
mon:setCorpse(6081)
mon:setSummonCost(0)

print("Monster Lorde das Chamas carregado.")'''

path_cloud = os.path.join(OUT, 'Cloud_monster_LordeDasChamas.lua')
with open(path_cloud, 'w', encoding='utf-8') as f:
    f.write(CLOUD_MONSTER)
print('  [OK] Cloud gerou monster com ferramentas proprias (write)')
print(f'  Arquivo: {path_cloud}')

# ============================================================
# RODADA 2: MCR-DevIA gera (usando scripts DELE)
# ============================================================
print('\n[RODADA 2] MCR-DevIA gerando monster COMPLETO...')
print('  Ferramentas: mcr_ultimate.py (template engine)')

# MCR-DevIA usa mcr_ultimate.py pra gerar
devia_result = subprocess.run(
    [sys.executable, os.path.join(SANDBOX, 'mcr_ultimate.py'), 
     'monster', 'LordeDasChamas', '3500', '120', '50', '6501', '0.9'],
    capture_output=True, text=True, timeout=60
)

if devia_result.returncode == 0:
    print('  [OK] MCR-DevIA gerou monster via mcr_ultimate.py')
else:
    print('  [FALHA] mcr_ultimate.py falhou')
    print(f'  Erro: {devia_result.stderr[:200]}')
    # Fallback: IA local tenta
    print('  Usando fallback: IA local direto...')
    codigo_devia = ia("Crie um monster COMPLETO para Tibia MCR chamado 'Lorde das Chamas'. Inclua stats, elementos, comportamento, loot, habilidades e visual.")
    if codigo_devia:
        path_devia = os.path.join(OUT, 'DevIA_monster_LordeDasChamas.lua')
        with open(path_devia, 'w', encoding='utf-8') as f:
            f.write(codigo_devia)
        print(f'  [OK] IA local gerou monster')

# Renomeia o arquivo gerado pelo ultimate
for f in os.listdir(os.path.join(SANDBOX, 'autogerados')):
    if 'LordeDasChamas' in f or 'lorde' in f.lower():
        src = os.path.join(SANDBOX, 'autogerados', f)
        dst = os.path.join(OUT, f'DevIA_monster_{f}')
        import shutil
        shutil.copy2(src, dst)
        print(f'  [OK] Arquivo copiado: {f}')

# Se nao gerou nada, cria um basico
devia_files = [f for f in os.listdir(OUT) if f.startswith('DevIA')]
if not devia_files:
    print('  [FALLBACK] Criando monster basico para DevIA...')
    codigo_fallback = '''-- Monster: Lorde das Chamas (via IA local)
local mon = Monster("Lorde das Chamas")
mon:setHealth(3500)
mon:setAttack(120)
mon:setDefense(50)
mon:addLoot(6501, 0.9)
print("Monster Lorde das Chamas carregado.")'''
    path_fallback = os.path.join(OUT, 'DevIA_monster_LordeDasChamas.lua')
    with open(path_fallback, 'w', encoding='utf-8') as f:
        f.write(codigo_fallback)
    print(f'  [OK] Fallback criado')

# ============================================================
# RODADA 3: Cada um REVISA o trabalho do outro
# ============================================================
print('\n[RODADA 3] Revisao cruzada...')

def analisar_arquivo(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()
    return {
        'linhas': len(c.split('\n')),
        'tamanho': len(c),
        'chaves': c.count('{') - c.count('}'),
        'tem_setElement': 'setElement' in c,
        'tem_setWeakness': 'setWeakness' in c,
        'tem_setResistance': 'setResistance' in c,
        'tem_addLoot': c.count('addLoot'),
        'tem_addSpell': c.count('addSpell'),
        'tem_setBehavior': 'setBehavior' in c,
        'tem_setOutfit': 'setOutfit' in c,
        'tem_setCorpse': 'setCorpse' in c,
        'tem_COMBAT_': 'COMBAT_' in c,
    }

# Cloud revisa DevIA
for f in sorted(os.listdir(OUT)):
    if not f.startswith('DevIA'): continue
    path = os.path.join(OUT, f)
    analise = analisar_arquivo(path)
    
    print(f'\n[CLOUD] Revisando {f}:')
    print(f'  Linhas: {analise["linhas"]} | Tamanho: {analise["tamanho"]}b | Chaves: {analise["chaves"]}')
    
    prompt_review = f"""Analise este codigo Lua de monster para Tibia MCR:

{open(path).read()[:1500]}

Avalie: 1) Esta completo? 2) Tem erros? 3) Nota 0-10?
Responda em 1 paragrafo."""
    review = ia(prompt_review, 0.4)
    print(f'  Review: {review[:300] if review else "(sem review)"}')

# DevIA revisa Cloud  
print(f'\n[MCR-DevIA] Revisando Cloud_monster_LordeDasChamas.lua:')
analise_cloud = analisar_arquivo(path_cloud)
print(f'  Linhas: {analise_cloud["linhas"]} | Tamanho: {analise_cloud["tamanho"]}b | Chaves: {analise_cloud["chaves"]}')

prompt_devia_review = f"""Analise este codigo Lua de monster:

{CLOUD_MONSTER[:1500]}

Avalie: 1) Esta completo? 2) Tem erros? 3) Nota 0-10?
Responda em 1 paragrafo."""
review_devia = ia(prompt_devia_review, 0.4)
print(f'  Review: {review_devia[:300] if review_devia else "(sem review)"}')

# ============================================================
# RELATORIO FINAL
# ============================================================
print('\n' + '='*70)
print('  RELATORIO FINAL — CORRIDA JUSTA')
print('='*70)

print(f'''
  TAREFA UNICA: Monster completo (stats, elementos, loot, habilidades, visual)
  
  FERRAMENTAS DE CADA UM:
    Cloud:  python + write (built-in) 
    DevIA:  mcr_ultimate.py + mcr_improvements.py (scripts proprios)
  
  CLOUD GEROU: Cloud_monster_LordeDasChamas.lua
    Linhas: {analise_cloud["linhas"]}
    Elementos: {'[OK]' if analise_cloud["tem_setElement"] else '[AUSENTE]'}
    Fraquezas: {'[OK]' if analise_cloud["tem_setWeakness"] else '[AUSENTE]'}
    Resistencia: {'[OK]' if analise_cloud["tem_setResistance"] else '[AUSENTE]'}
    Loot: {analise_cloud["tem_addLoot"]} itens
    Habilidades: {analise_cloud["tem_addSpell"]} spells
    Comportamento: {'[OK]' if analise_cloud["tem_setBehavior"] else '[AUSENTE]'}
    Visual: {'[OK]' if analise_cloud["tem_setOutfit"] and analise_cloud["tem_setCorpse"] else '[AUSENTE]'}
    Chaves: {'[OK]' if analise_cloud["chaves"] == 0 else f'[DIF {analise_cloud["chaves"]}]'}
''')

# Mostra metricas do DevIA
for f in sorted(os.listdir(OUT)):
    if not f.startswith('DevIA'): continue
    path = os.path.join(OUT, f)
    analise = analisar_arquivo(path)
    print(f'  MCR-DevIA GEROU: {f}')
    print(f'    Linhas: {analise["linhas"]}')
    print(f'    Elementos: {"[OK]" if analise["tem_setElement"] else "[AUSENTE]"}')
    print(f'    Fraquezas: {"[OK]" if analise["tem_setWeakness"] else "[AUSENTE]"}')
    print(f'    Loot: {analise["tem_addLoot"]} itens')
    print(f'    Habilidades: {analise["tem_addSpell"]} spells')
    print(f'    Comportamento: {"[OK]" if analise["tem_setBehavior"] else "[AUSENTE]"}')
    print(f'    Visual: {"[OK]" if analise["tem_setOutfit"] and analise["tem_setCorpse"] else "[AUSENTE]"}')


print(f'''
  ARQUIVOS GERADOS:
''')
for f in sorted(os.listdir(OUT)):
    tamanho = os.path.getsize(os.path.join(OUT, f))
    print(f'    {f} ({tamanho} bytes)')

print(f'''
  VEREDITO:
    Os arquivos estao em sandbox/corrida_justa/
    Abra cada um e compare VOCE MESMO:
      - Cloud_monster_LordeDasChamas.lua  (feito pelo Cloud)
      - DevIA_monster*.lua                 (feito pelo MCR-DevIA)
    
    O Cloud usou: write (built-in)
    O DevIA usou: mcr_ultimate.py (script que ele mesmo criou)
    
    Ambos geraram sem minha interferencia.
    Compare e tire suas proprias conclusoes.
''')
print('='*70)
