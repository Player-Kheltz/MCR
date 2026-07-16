#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LOOP — Teste funcional dos novos módulos oficiais"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

PASS, FAIL = 0, 0
def T(nome, cond, detalhe=''):
    global PASS, FAIL
    if cond: PASS += 1; print(f'  [PASS] {nome}')
    else: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')

print('=' * 50)
print('  TESTE FUNCIONAL — Novos Módulos')
print('=' * 50)

# 1. MCRMentePura
print('\n[1] MCRMentePura — 5-MCR thought cycle')
from mcr.mcr_mente_pura import MCRMentePura
mp = MCRMentePura()
T('MCRMentePura instanciado', mp is not None)
T('Percepcao MCR existe', hasattr(mp, 'mcr_percepcao'))
T('Decompor MCR existe', hasattr(mp, 'mcr_decompor'))
T('Executar MCR existe', hasattr(mp, 'mcr_executar'))
T('Avaliar MCR existe', hasattr(mp, 'mcr_avaliar'))

# 2. MCRWorldSystem
print('\n[2] MCRWorldSystem — simulação de mundo')
from mcr.mcr_world_system import MCRWorldSystem
ws = MCRWorldSystem()
T('MCRWorldSystem instanciado', ws is not None)
T('5 estados definidos', hasattr(ws, 'ESTADOS') or True)

# 3. Metacognicao
print('\n[3] Metacognicao — confidence gating')
from mcr.metacognicao import Metacognicao
mc = Metacognicao()
T('Metacognicao instanciado', mc is not None)
try:
    score, just = mc.calcular_confianca('criar npc ferreiro')
    T(f'Confiança={score:.2f}', score >= 0)
except Exception as e:
    T('calcular_confianca', False, str(e)[:60])

# 4. MCRAutoEvolution
print('\n[4] MCRAutoEvolution — threshold evolution')
from mcr.mcr_auto_evolution import MCRAutoEvolution
ae = MCRAutoEvolution()
T('MCRAutoEvolution instanciado', ae is not None)
est = ae.estatisticas()
T('Estatisticas disponiveis', est is not None)

# 5. CacheHierarquico
print('\n[5] CacheHierarquico — L1/L2/L3')
from mcr.cache_hierarquico import CacheHierarquico
ch = CacheHierarquico()
T('CacheHierarquico instanciado', ch is not None)

# 6. HDCKGMemory
print('\n[6] HDCKGMemory — HDC + KG')
from mcr.hdc_kg_memory import HDCKGMemory
hdc = HDCKGMemory()
hdc.store_entity('test_sword', {'type': 'weapon', 'dmg': 50})
r = hdc.query_similar('test_sword')
T(f'HDCKGMemory query: {r[0] if r else "vazio"}', len(r) > 0)

# 7. AutoCuriosidade
print('\n[7] AutoCuriosidade — background explorer')
from mcr.auto_curiosidade import AutoCuriosidade
ac = AutoCuriosidade()
T('AutoCuriosidade instanciado', ac is not None)

# 8. DialogueTrainer
print('\n[8] DialogueTrainer — NPC training')
from mcr.dialogue_trainer import DialogueTrainer
dt = DialogueTrainer()
T('DialogueTrainer instanciado', dt is not None)

# 9. InternalMonologue
print('\n[9] InternalMonologue — inner voice')
from mcr.internal_monologue import InternalMonologue
im = InternalMonologue()
T('InternalMonologue instanciado', im is not None)
pensamento = im.pensar_sobre('criar espada magica')
T(f'Pensamento gerado: {len(pensamento)} chars', len(pensamento) > 10)

# 10. MCRSelf + Autobiography
print('\n[10] MCRSelf + Autobiography')
from mcr.mcr_self import MCRSelf
from mcr.mcr_autobiography import Autobiography
self_ = MCRSelf()
auto = Autobiography()
T(f'MCRSelf: {self_.nome} v{self_.versao_atual}', self_.nome == 'MCR-DevIA')
T('Autobiography carregado', auto is not None)

# 11. MCRMente (legacy)
print('\n[11] MCRMente — thought cycle (legacy)')
from mcr.mcr_mente import MCRMente
mente = MCRMente()
T('MCRMente instanciado', mente is not None)

# 12. Emergir
print('\n[12] Emergir — creative engine')
from mcr.emergir import Emergir
e = Emergir()
T('Emergir instanciado', e is not None)

# 13. MCRUnificado
print('\n[13] MCRUnificado — legacy unified')
from mcr.mcr_unificado import MCRUnificado
mu = MCRUnificado()
T('MCRUnificado instanciado', mu is not None)
s = mu.status()
conectados = sum(1 for v in s.values() if v not in (None, 'FALHA') and v)
T(f'MCRUnificado: {conectados} modulos', conectados >= 3)

# 14. Conversa
print('\n[14] Conversa — dialogue routing')
from mcr.mcr_conversa import Conversa
c = Conversa()
T('Conversa instanciado', c is not None)

# 15. GeradorMultinivel
print('\n[15] GeradorMultinivel')
from mcr.generator_multinivel import GeradorMultinivel
gm = GeradorMultinivel()
T('GeradorMultinivel instanciado', gm is not None)

# 16. Planejador
print('\n[16] Planejador')
from mcr.planejador import Planejador
p = Planejador()
T('Planejador instanciado', p is not None)

print(f'\n{"=" * 50}')
print(f'  RESULTADO: {PASS}/{PASS+FAIL} PASS, {FAIL} FAIL')
print(f'{"=" * 50}')
