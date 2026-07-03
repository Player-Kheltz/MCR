"""Teste das novas ferramentas (tool_orchestrator v2)."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator

print("=== Teste ToolOrchestrator v2 ===\n")
tools = ToolOrchestrator()

# Teste 1: criar diretorio
print("1. criar_diretorio...")
r = tools.executar('criar_diretorio', {'caminho': 'sandbox/_test_proj/src'})
print(f"   {r}")
assert r['sucesso']

# Teste 2: escrever_artefato com marcacao
print("\n2. escrever_artefato com extração de markdown...")
r = tools.executar('escrever_artefato', {
    'codigo': "Explicacao aqui\n```python\nprint('codigo puro')\n```\nmais texto",
    'caminho': 'sandbox/_test_proj/test.py'
})
print(f"   {r}")
assert r['sucesso']

# Verifica se o arquivo tem codigo puro
conteudo = open('E:/Projeto MCR/sandbox/_test_proj/test.py').read()
assert "print('codigo puro')" in conteudo
assert "Explicacao" not in conteudo
print("   Conteudo limpo: OK")

# Teste 3: extrair_codigo
print("\n3. extrair_codigo...")
r = tools.executar('extrair_codigo', {'conteudo': "```python\nx = 1\n```"})
print(f"   Resultado: {r['resultado']}")
assert r['sucesso']
assert r['resultado'] == 'x = 1'

# Teste 4: criar_atalho
print("\n4. criar_atalho...")
r = tools.executar('criar_atalho', {'comando': 'python src/main.py', 'caminho': 'sandbox/_test_proj'})
print(f"   {r}")
assert r['sucesso']

# Teste 5: gerar_requirements
print("\n5. gerar_requirements...")
r = tools.executar('gerar_requirements', {'dependencias': 'pygame>=2.5.0', 'caminho': 'sandbox/_test_proj/requirements.txt'})
print(f"   {r}")
assert r['sucesso']
assert os.path.exists('E:/Projeto MCR/sandbox/_test_proj/requirements.txt')

# Teste 6: limpeza
print("\n6. Limpeza...")
import shutil
shutil.rmtree('E:/Projeto MCR/sandbox/_test_proj', ignore_errors=True)
print("   OK")

print("\n=== TODOS OS TESTES PASSARAM ===")
