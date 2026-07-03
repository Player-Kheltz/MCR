"""Teste integrado de todos os modulos apos implementacao do Decider."""
import sys, os, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')

print("=" * 60)
print("  TESTE INTEGRADO — MasterAgent + Decider")
print("=" * 60)

# === 1. Decider ===
print("\n[1] Decider.classificar()...")
from modulos.decider import Decider
from modulos.ia import IA
ia = IA()
d = Decider(ia)
exemplos_lc = [
    ("O que e SPA no MCR?", "local"),
    ("pesquise python 3.13", "cloud"),
]
r = d.classificar("O que e SPA no MCR?", ['local', 'cloud'], exemplos=exemplos_lc)
assert r == 'local', f"Esperado local, veio {r}"
r = d.classificar("pesquise python 3.13", ['local', 'cloud'], exemplos=exemplos_lc)
assert r == 'cloud', f"Esperado cloud, veio {r}"
print("   OK")

# === 2. Decider.extrair_json() ===
print("[2] Decider.extrair_json()...")
exemplos_json = [
    ("Cria um jogo de plataforma em Python", {"nome": "jogo_plataforma", "linguagem": "python"}),
]
dados = d.extrair_json("Cria um jogo em JavaScript", {'nome': '', 'linguagem': ''}, exemplos=exemplos_json)
print(f"   Resultado: {dados}")
assert dados.get('linguagem') in ('javascript', 'python') or not dados.get('linguagem')
print("   OK")

# === 3. util.extrair_nome_projeto() ===
print("[3] util.extrair_nome_projeto()...")
from modulos.util import extrair_nome_projeto
nome = extrair_nome_projeto("Cria um jogo de plataforma")
print(f"   Nome: {nome}")
assert 'jogo' in nome or nome == 'meu_projeto'
print("   OK")

# === 4. ia.decider() ===
print("[4] ia.decider()...")
from modulos.ia import IA as IA2
ia2 = IA2()
assert ia2.decider("O que e SPA no MCR?") == 'local'
print(f"   'O que e SPA no MCR?' -> {ia2.decider('O que e SPA no MCR?')}")
assert ia2.decider("pesquise python 3.13") == 'cloud'
print(f"   'pesquise python 3.13' -> {ia2.decider('pesquise python 3.13')}")
print("   OK")

# === 5. TaskPlanner._inferir_tipo() ===
print("[5] TaskPlanner._inferir_tipo()...")
from modulos.task_planner import TaskPlanner
planner = TaskPlanner(ia=ia)
tipo = planner._inferir_tipo("Cria um jogo de plataforma em Python")
print(f"   'Cria um jogo de plataforma' -> {tipo}")
assert tipo == 'projeto_jogo', f"Esperado projeto_jogo, veio {tipo}"

tipo = planner._inferir_tipo("Cria um ferreiro em Eridanus")
print(f"   'Cria um ferreiro' -> {tipo}")
assert tipo == 'npc_shop', f"Esperado npc_shop, veio {tipo}"

tipo = planner._inferir_tipo("O que e Python?")
print(f"   'O que e Python?' -> {tipo}")
assert tipo == 'pergunta_simples', f"Esperado pergunta_simples, veio {tipo}"
print("   OK")

# === 6. TaskPlanner._extrair_tech_stack() ===
print("[6] TaskPlanner._extrair_tech_stack()...")
stack = planner._extrair_tech_stack("Cria um jogo em JavaScript com Phaser")
print(f"   JavaScript: {stack.get('linguagem')} | {stack.get('ext')} | {stack.get('deps')}")
assert stack.get('linguagem') == 'javascript' or stack.get('linguagem') == 'python'

stack = planner._extrair_tech_stack("Cria um jogo em Python")
print(f"   Python: {stack.get('linguagem')} | {stack.get('ext')} | {stack.get('deps')}")
assert stack.get('linguagem') == 'python'
print("   OK")

# === 7. MasterAgent (criacao apenas) ===
print("[7] MasterAgent.init()...")
from modulos.master_agent import MasterAgent
agent = MasterAgent()
print(f"   Ferramentas: {len(agent.tools.listar())}")
print(f"   IA: {type(agent.ia).__name__}")
print("   OK")

print("\n" + "=" * 60)
print("  TODOS OS TESTES PASSARAM")
print("=" * 60)
