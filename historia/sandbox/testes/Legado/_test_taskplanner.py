"""Teste do TaskPlanner + PlanValidator (Fase 3)."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.task_planner import TaskPlanner, PlanValidator, PLANOS_CONHECIDOS
from modulos.tool_orchestrator import ToolOrchestrator

tools = ToolOrchestrator()
planner = TaskPlanner(tools_orchestrator=tools)

print("=== Teste TaskPlanner + PlanValidator ===\n")

# Teste 1: NPC conhecido usa template
print("1. NPC template...")
plano = planner.planejar("Cria um ferreiro em Eridanus", "npc_shop")
print(f"   Passos: {len(plano)}")
for p in plano:
    print(f"   - [{p['id']}] {p['acao']} -> {p['ferramenta']} (dep: {p['depende_de']})")
assert len(plano) == 5
assert plano[0]['acao'] == 'buscar_exemplos'

# Teste 2: Request com palavras-chave infere tipo
print("\n2. Inferencia de tipo...")
plano = planner.planejar("Cria um script Python que imprime hello")
print(f"   Passos: {len(plano)}")
assert len(plano) == 4
assert plano[0]['ferramenta'] is not None
print("   OK - criou_codigo template usado")

# Teste 3: Pergunta simples
print("\n3. Pergunta simples...")
plano = planner.planejar("O que e SPA no MCR?")
print(f"   Passos: {len(plano)}")
assert len(plano) == 2
assert plano[0]['acao'] == 'buscar_contexto'
print("   OK - pergunta_simples template usado")

# Teste 4: PlanValidator
print("\n4. PlanValidator...")
val = PlanValidator(tools)

# Plano valido
plano_valido = [{'id': 1, 'acao': 'perguntar_ia', 'ferramenta': 'perguntar_ia', 'depende_de': []}]
valido, erros = val.validar(plano_valido)
print(f"   Plano valido: {valido} (erros: {erros})")
assert valido == True

# Plano vazio
valido, erros = val.validar([])
print(f"   Plano vazio: {valido} (erros: {erros})")
assert valido == False

# Plano com ferramenta inexistente
plano_invalido = [{'id': 1, 'acao': 'teste', 'ferramenta': 'nao_existe', 'depende_de': []}]
valido, erros = val.validar(plano_invalido)
print(f"   Ferramenta inexistente: {valido} (erros: {erros})")
assert valido == False

# Plano com dependencia inexistente
plano_loop = [
    {'id': 2, 'acao': 'teste', 'ferramenta': 'perguntar_ia', 'depende_de': [5]},
]
valido, erros = val.validar(plano_loop)
print(f"   Dependencia inexistente: {valido} (erros: {erros})")
assert valido == False

print("\n=== TODOS OS TESTES PASSARAM ===")
