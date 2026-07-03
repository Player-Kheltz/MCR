"""Teste do TaskPlanner v2 com linguagem dinamica."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.task_planner import TaskPlanner

planner = TaskPlanner()

print("=== Teste TaskPlanner v2 — Linguagem Dinamica ===\n")

# Teste 1: Python (padrao)
print("1. 'Cria um jogo de plataforma em Python' -> projeto_jogo (python)...")
plano = planner.planejar("Cria um jogo de plataforma em Python com 3 fases")
assert len(plano) == 14
p_main = [p for p in plano if p['acao'] == 'gerar_modulo_main'][0]
print(f"   Descricao: {p_main['params']['descricao'][:60]}...")
assert '.py' in p_main['params']['descricao']
assert 'linguagem' in p_main['params']
p_req = [p for p in plano if p['acao'] == 'gerar_requirements'][0]
assert 'pygame' in p_req['params']['dependencias']
print("   OK - Python/pygame")

# Teste 2: JavaScript
print("\n2. 'Cria um jogo em JavaScript' -> projeto_jogo (javascript)...")
plano = planner.planejar("Cria um jogo em JavaScript com 3 fases")
assert len(plano) == 14
p_main = [p for p in plano if p['acao'] == 'gerar_modulo_main'][0]
print(f"   Descricao: {p_main['params']['descricao'][:60]}...")
assert '.js' in p_main['params']['descricao']
p_req = [p for p in plano if p['acao'] == 'gerar_requirements'][0]
print(f"   Deps: {p_req['params']['dependencias']}")
assert 'phaser' in p_req['params']['dependencias']
p_run = [p for p in plano if p['acao'] == 'criar_atalho'][0]
print(f"   Comando: {p_run['params']['comando']}")
assert 'node' in p_run['params']['comando']
print("   OK - JavaScript/phaser")

# Teste 3: Lua
print("\n3. 'Cria um jogo em Lua' -> projeto_jogo (lua)...")
plano = planner.planejar("Cria um jogo em Lua com 3 fases")
assert len(plano) == 14
p_main = [p for p in plano if p['acao'] == 'gerar_modulo_main'][0]
assert '.lua' in p_main['params']['descricao']
print(f"   Extensao: .lua (OK)")
p_req = [p for p in plano if p['acao'] == 'gerar_requirements'][0]
assert 'love' in p_req['params']['dependencias']
print("   OK - Lua/love2d")

# Teste 4: Script simples (criar_codigo, nao projeto_jogo)
print("\n4. 'Cria um script python que imprime hello' -> criar_codigo...")
plano = planner.planejar("Cria um script python que imprime hello")
assert len(plano) == 4
print(f"   Passos: {len(plano)} (criar_codigo)")
print("   OK - 4 passos")

# Teste 5: params criar_atalho com JS
print("\n5. criar_atalho params com JavaScript...")
plano = planner.planejar("Cria um jogo em JavaScript", "projeto_jogo")
p_run = [p for p in plano if p['acao'] == 'criar_atalho'][0]
print(f"   Comando: {p_run['params']['comando']}")
assert 'node' in p_run['params']['comando']
print("   OK")

print("\n=== TODOS OS TESTES PASSARAM ===")
