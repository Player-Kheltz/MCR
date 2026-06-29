"""Teste das correcoes: dependencias nao lineares + descricoes dinâmicas."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.task_planner import TaskPlanner
from modulos.ia import IA

ia = IA()
planner = TaskPlanner(ia=ia)

print("=== Teste Correcoes ===\n")

# Teste 1: Descricoes com JavaScript
print("1. Descricoes dinamicas (JavaScript)...")
plano = planner.planejar("Cria um jogo em JavaScript com Phaser", "projeto_jogo")
for p in plano:
    print(f"   [{p['id']}] {p['descricao'][:70]}")
    if p['acao'] == 'gerar_modulo_main':
        assert '.js' in p['descricao'] or 'javascript' in p['descricao'].lower(), f".js nao encontrado em: {p['descricao']}"
        print("   -> .js OK")
        break

# Teste 2: Dependencias nao lineares
print("\n2. Dependencias inteligentes...")
for p in plano:
    print(f"   [{p['id']}] {p['acao']:30s} depende de: {p['depende_de']}")

# gerar_requirements deve ter dependencia MINIMA ou nenhuma
req = [p for p in plano if p['acao'] == 'gerar_requirements'][0]
print(f"\n   gerar_requirements depende de: {req['depende_de']}")
assert len(req['depende_de']) <= 1, f"gerar_requirements depende de {len(req['depende_de'])} passos (devia ser <=1)"

# validar_codigo depende apenas dos modulos, nao de tudo
val = [p for p in plano if p['acao'] == 'validar_codigo'][0]
print(f"   validar_codigo depende de: {val['depende_de']}")
assert len(val['depende_de']) == 4, f"validar_codigo depende de {len(val['depende_de'])} (devia ser 4 = 4 modulos)"

# testar_execucao depende de validar_codigo
test = [p for p in plano if p['acao'] == 'testar_execucao'][0]
print(f"   testar_execucao depende de: {test['depende_de']}")
assert len(test['depende_de']) == 1, f"testar_execucao devia depender de 1 passo"

print("   OK")

# Teste 3: Descricoes com Python (padrao)
print("\n3. Descricoes Python (padrao)...")
plano = planner.planejar("Cria um jogo de plataforma em Python", "projeto_jogo")
main = [p for p in plano if p['acao'] == 'gerar_modulo_main'][0]
print(f"   Descricao: {main['descricao']}")
assert '.py' in main['descricao'] or 'python' in main['descricao'].lower()
print("   OK")

# Teste 4: Descricoes com Lua
print("\n4. Descricoes Lua...")
plano = planner.planejar("Cria um jogo em Lua com Love2D", "projeto_jogo")
main = [p for p in plano if p['acao'] == 'gerar_modulo_main'][0]
print(f"   Descricao: {main['descricao']}")
assert '.lua' in main['descricao'] or 'lua' in main['descricao'].lower()
req = [p for p in plano if p['acao'] == 'gerar_requirements'][0]
print(f"   Requirements: {req['descricao']}")
assert 'love' in req['descricao'] or 'lua' in req['descricao'].lower()
print("   OK")

print("\n=== TODOS OS TESTES PASSARAM ===")
