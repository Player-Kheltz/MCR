#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste rapido do prototipo AGI completo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import *

c = CerebroAGI()

# Teste 1: World aprende causalidade
print('=== TESTE 1: APRENDIZADO CAUSAL ===')
e1 = EstadoMundo.criar_simples()
e2 = MotorFisica.executar(e1, 'andar_dir')
c.aprender_causal(e1, 'andar_dir', e2)
acao = c.world.predizer_acao(e1, e2)
print(f'Predizer acao (esperado=andar_dir): {acao}')

# Teste 2: Coupling
print()
print('=== TESTE 2: COUPLING ===')
c.coupling.alimentar_transicao('byte', 'palavra', 'B:41', 'Fogo')
c.coupling.alimentar_transicao('byte', 'palavra', 'B:42', 'Agua')
c.coupling.recalcular_pesos()
print(f'Peso byte->palavra: {c.coupling.peso("byte", "palavra"):.3f}')

# Teste 3: Planner com mais dados
print()
print('=== TESTE 3: PLANEJAMENTO ===')
for _ in range(3):
    ea = EstadoMundo.criar_simples()
    eb = MotorFisica.executar(ea, 'andar_dir')
    c.aprender_causal(ea, 'andar_dir', eb)
    ec = MotorFisica.executar(eb, 'atacar')
    c.aprender_causal(eb, 'atacar', ec)

plan = c.planejar('monstro morto', EstadoMundo.criar_simples())
print(f'Plano: {plan["plano"][:5]}... (nota={plan["nota"]})')

# Teste 4: SelfModify
print()
print('=== TESTE 4: SELF-MODIFY ===')
sm = c.self_modify
hc = sm.escanear()
print(f'Hardcodes detectados: {len(hc)}')
if hc:
    pior = hc[0]
    print(f'Pior hardcode: L{pior["linha"]} score={pior["score"]} -> {pior["codigo"][:50]}')

# Teste 5: Geracao
print()
print('=== TESTE 5: GERACAO COM COUPLING ===')
c.alimentar('Fogo queima Gelo congela Terra treme', 'elementos')
print(f'Gerado: {c.gerar("Fogo", 4)}')
print(f'Gerado: {c.gerar("Eridanus", 4)}')

# Teste 6: Relatorio final
print()
print('=== TESTE 6: RELATORIO ===')
print(c.relatorio())

print()
print('TODOS OS TESTES CONCLUIDOS')
