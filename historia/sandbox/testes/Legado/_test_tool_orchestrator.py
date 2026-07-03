"""Teste do ToolOrchestrator (Fase 2)."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator

print("=== Teste ToolOrchestrator (Fase 2) ===\n")
tools = ToolOrchestrator()

# Teste 1: Listar ferramentas
print("1. Listar ferramentas...")
lista = tools.listar()
print(f"   Total: {len(lista)} ferramentas")
for nome, meta in sorted(lista.items()):
    print(f"   - {nome}: {meta['descricao'][:50]}... params={meta['params']}")
assert len(lista) >= 14, f"Deveria ter 14+ ferramentas, tem {len(lista)}"

# Teste 2: Executar ferramenta
print("\n2. Executar 'validar_python'...")
r = tools.executar('validar_python', {'codigo': 'x = 1; print(x)'})
print(f"   Resultado: {r}")
assert r['sucesso'] == True
assert r['resultado']['valido'] == True

# Teste 3: Ferramenta inexistente
print("\n3. Ferramenta inexistente...")
r = tools.executar('nao_existe', {})
print(f"   Resultado: {r}")
assert 'erro' in r

# Teste 4: Executar com erro de sintaxe Python
print("\n4. Validar Python com erro...")
r = tools.executar('validar_python', {'codigo': 'x = '})
print(f"   Resultado: {r}")
assert r['sucesso'] == True
assert r['resultado']['valido'] == False

# Teste 5: Executar Python real
print("\n5. Executar Python real...")
r = tools.executar('executar_python', {'codigo': 'print(2+2)'})
print(f"   Resultado: {r}")
assert r['sucesso'] == True
assert '4' in r['resultado'].get('stdout', '')

# Teste 6: Parametros invalidos
print("\n6. Parametros invalidos...")
r = tools.executar('validar_python', {})  # sem codigo
print(f"   Resultado: {r}")
assert 'erro' in r  # deve falhar por falta de parametro

# Teste 7: Obter metadata
print("\n7. Obter metadata...")
meta = tools.obter('gerar_codigo')
print(f"   Metadata: {meta['nome']} - {meta['descricao'][:40]}...")
assert meta is not None
assert meta['nome'] == 'gerar_codigo'

print("\n=== TODOS OS TESTES PASSARAM ===")
