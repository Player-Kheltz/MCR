"""TESTE FINAL v2 — Todas as conexões possíveis."""
import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR
mcr = MCR()
print('=' * 65)
print('  TESTE FINAL v2 — MCR UNIFICADO')
print('=' * 65)

results = {}

# NÍVEL 1: ESSENCIAL
print('\n[NÍVEL 1] Essencial')
r = mcr.processar('Crie um NPC ferreiro que vende armaduras')
results['npc'] = r['sucesso'] and 'internalNpcName' in r['resultado'].get('codigo','')
print(f'  NPC: {"OK" if results["npc"] else "FALHA"}')

r2 = mcr.processar('Gere um monstro dragao')
results['monstro'] = r2['sucesso']
print(f'  Monstro: {"OK" if results["monstro"] else "FALHA"}')

r3 = mcr.processar('O que e entropia')
results['responder'] = r3['sucesso'] and len(r3['resultado'].get('resposta','')) > 10
print(f'  Responder: {"OK" if results["responder"] else "FALHA"}')

# NÍVEL 1b: VALIDAÇÃO
print('\n[NÍVEL 1b] Validação')
# Gera código e força validação
code = r['resultado'].get('codigo','')
v = mcr._validar_saida(r['resultado'], 'gerar_npc')
checks = v.get('checks',[])
results['sanity'] = any('sanity' in str(c) for c in checks)
results['lua'] = any('lua' in str(c) for c in checks)
results['shadow'] = any('shadow' in str(c) for c in checks)
results['cove'] = any('cove' in str(c) for c in checks)
print(f'  Sanity: {"OK" if results["sanity"] else "FALHA"} | Lua: {"OK" if results["lua"] else "FALHA"}')
print(f'  Shadow: {"OK" if results["shadow"] else "FALHA"} | CoVe: {"OK" if results["cove"] else "FALHA"}')

# NÍVEL 2: COGNITIVO
print('\n[NÍVEL 2] Cognitivo')
results['sqlite'] = mcr._sqlite is not None
try:
    from mcr.mcr_auto_evolution import MCRAutoEvolution
    results['evolucao'] = True
except: results['evolucao'] = False
try:
    from mcr.metacognicao import Metacognicao
    results['metacognicao'] = True
except: results['metacognicao'] = False
try:
    from mcr.cache_hierarquico import CacheHierarquico
    results['cache'] = True
except: results['cache'] = False
try:
    from mcr.pipeline_completo import PipelineCompleto
    results['llm_fallback'] = True
except: results['llm_fallback'] = False
print(f'  SQLite: {"OK" if results["sqlite"] else "FALHA"} | Evo: {"OK" if results["evolucao"] else "FALHA"}')
print(f'  Meta: {"OK" if results["metacognicao"] else "FALHA"} | Cache: {"OK" if results["cache"] else "FALHA"}')
print(f'  LLM fallback: {"OK" if results["llm_fallback"] else "FALHA"}')

# NÍVEL 3: ECOSSISTEMA
print('\n[NÍVEL 3] Ecossistema')
try:
    from mcr.mcr_world_system import MCRWorldSystem
    results['mundo'] = True
except: results['mundo'] = False
try:
    from mcr.npc_server import NPCServer
    results['npc_server'] = True
except: results['npc_server'] = False
try:
    from mcr.world_observer import WorldObserver
    results['observer'] = True
except: results['observer'] = False
print(f'  Mundo: {"OK" if results["mundo"] else "FALHA"} | NPC Server: {"OK" if results["npc_server"] else "FALHA"}')
print(f'  Observer: {"OK" if results["observer"] else "FALHA"}')

# NÍVEL 4: VISUAL
print('\n[NÍVEL 4] Visual')
try:
    from mcr.meus_olhos import MCRDiscriminador
    results['sprite_avaliar'] = True
except: results['sprite_avaliar'] = False
try:
    from mcr.sprite_corpus import listar_categorias
    results['sprite_corpus'] = True
except: results['sprite_corpus'] = False
try:
    from mcr.mcr_sprite_motor import MCRSpriteMotor
    results['sprite_motor'] = True
except: results['sprite_motor'] = False
print(f'  Discriminador: {"OK" if results["sprite_avaliar"] else "FALHA"} | Corpus: {"OK" if results["sprite_corpus"] else "FALHA"}')
print(f'  Motor: {"OK" if results["sprite_motor"] else "FALHA"}')

# RESULTADO
print(f'\n{"="*65}')
passes = sum(1 for v in results.values() if v)
total = len(results)
for nome, ok in results.items():
    print(f'  {nome:20s}: {"OK" if ok else "FALHA"}')
print(f'\n  {passes}/{total} ({passes*100//total}%)')
print(f'{"="*65}')
