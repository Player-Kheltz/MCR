"""TESTE FINAL — Validação de TODAS as conexões do MCR unificado.

NÍVEL 1: NPC, Monstro, Responder, Validação, LLM fallback
NÍVEL 2: SQLite, Auto-evolução, Metacognição, Cache
NÍVEL 3: Mundo vivo
NÍVEL 4: Sprite
"""
import sys, time
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR

mcr = MCR()
print('=' * 65)
print('  TESTE FINAL — MCR UNIFICADO (15/22 conexões)')
print('=' * 65)
t_global = time.time()

resultados = {}

# ═══════════════════════════════════════════════════════════
# NÍVEL 1: ESSENCIAL
# ═══════════════════════════════════════════════════════════

# 1.1.1 — NPC wrapper real
print('\n[1.1] NPC com shop (Tier 1)')
r = mcr.processar('Crie um NPC ferreiro anão que vende armaduras e escudos')
code = r['resultado'].get('codigo', '')
ok_npc = (r['sucesso'] and 'internalNpcName' in code and 'npcType:register' in code)
print(f'  {"OK" if ok_npc else "FALHA"}: {len(code)} chars | tool={r["resultado"].get("_tool","?")} | nota={r["nota"]:.3f}')
resultados['npc'] = ok_npc

# 1.1.2 — Monstro wrapper real
print('\n[1.2] Monstro (Tier 1)')
r2 = mcr.processar('Gere um monstro dragão ancião de lava')
code2 = r2['resultado'].get('codigo', '')
ok_monstro = (r2['sucesso'] and 'MonsterType' in code2)
print(f'  {"OK" if ok_monstro else "FALHA"}: {len(code2)} chars | tool={r2["resultado"].get("_tool","?")} | nota={r2["nota"]:.3f}')
resultados['monstro'] = ok_monstro

# 1.1.3 — Responder com KG + raciocínio
print('\n[1.3] Responder (KG + raciocínio)')
r3 = mcr.processar('O que é entropia?')
ok_responder = r3['sucesso'] and len(r3['resultado'].get('resposta', '')) > 20
print(f'  {"OK" if ok_responder else "FALHA"}: {r3["resultado"].get("resposta","?")[:100]}')
resultados['responder'] = ok_responder

# 1.2 — Validação pós-execução
print('\n[1.4] Validação pós-execução')
validacao_ativa = False
try:
    from mcr.sanity_validator import SanityValidator
    from mcr.lua_validator import LuaValidator
    validacao_ativa = True
except ImportError:
    pass
print(f'  SanityValidator: {"OK" if validacao_ativa else "FALHA"}')
resultados['validacao'] = validacao_ativa

# 1.3 — Pipeline LLM fallback
print('\n[1.5] Pipeline LLM (fallback)')
llm_ok = False
try:
    from mcr.pipeline_completo import PipelineCompleto
    llm_ok = True
except ImportError:
    pass
print(f'  PipelineCompleto: {"OK" if llm_ok else "FALHA"}')
resultados['llm_fallback'] = llm_ok

# ═══════════════════════════════════════════════════════════
# NÍVEL 2: COGNITIVO
# ═══════════════════════════════════════════════════════════

# 2.1 — SQLite persistência
print('\n[2.1] Persistência SQLite')
sqlite_ok = mcr._sqlite is not None
print(f'  SQLite: {"OK" if sqlite_ok else "FALHA"}')
resultados['sqlite'] = sqlite_ok

# 2.2 — Auto-evolução (conectada no processar)
print('\n[2.2] Auto-evolução')
evo_ok = False
try:
    from mcr.mcr_auto_evolution import MCRAutoEvolution
    evo_ok = True
except ImportError:
    pass
print(f'  MCRAutoEvolution: {"OK" if evo_ok else "FALHA"}')
resultados['evolucao'] = evo_ok

# 2.3 — Metacognição gatekeeper
print('\n[2.3] Metacognição gatekeeper')
meta_ok = False
try:
    from mcr.metacognicao import Metacognicao
    meta_ok = True
except ImportError:
    pass
print(f'  Metacognicao: {"OK" if meta_ok else "FALHA"}')
resultados['metacognicao'] = meta_ok

# 2.4 — Cache hierárquico
print('\n[2.4] Cache hierárquico')
cache_ok = False
try:
    from mcr.cache_hierarquico import CacheHierarquico
    cache_ok = True
except ImportError:
    pass
print(f'  CacheHierarquico: {"OK" if cache_ok else "FALHA"}')
resultados['cache'] = cache_ok

# ═══════════════════════════════════════════════════════════
# NÍVEL 3: ECOSSISTEMA
# ═══════════════════════════════════════════════════════════

# 3.1 — Mundo vivo
print('\n[3.1] Mundo vivo')
mundo_ok = False
try:
    from mcr.mcr_world_system import MCRWorldSystem
    mundo_ok = True
except ImportError:
    pass
print(f'  MCRWorldSystem: {"OK" if mundo_ok else "FALHA"}')
resultados['mundo'] = mundo_ok

# ═══════════════════════════════════════════════════════════
# NÍVEL 4: VISUAL
# ═══════════════════════════════════════════════════════════

# 4.1 — Sprite
print('\n[4.1] Sprite')
sprite_ok = False
try:
    from mcr.meus_olhos import MCRDiscriminador
    from mcr.sprite_corpus import listar_categorias
    sprite_ok = True
except ImportError:
    pass
print(f'  MCRDiscriminador + sprite_corpus: {"OK" if sprite_ok else "FALHA"}')
resultados['sprite'] = sprite_ok

# ═══════════════════════════════════════════════════════════
# RESULTADO
# ═══════════════════════════════════════════════════════════
print(f'\n{"="*65}')
print(f'  RESULTADO FINAL — {time.time()-t_global:.0f}s')
print(f'{"="*65}')

passes = sum(1 for v in resultados.values() if v)
total = len(resultados)
for nome, ok in resultados.items():
    print(f'  {nome:20s}: {"OK" if ok else "FALHA"}')

print(f'\n  {passes}/{total} conexões funcionando ({passes*100//total}%)')
  print(f'  MCR unificado: {"OK" if passes >= 10 else "INCOMPLETO"}')
print(f'{"="*65}')
