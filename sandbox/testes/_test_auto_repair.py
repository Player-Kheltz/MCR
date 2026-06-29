"""Teste do AutoRepair + Geracao Consciente."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')
from modulos.auto_repair import AutoRepair
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator

ia = IA()
tools = ToolOrchestrator()
reparador = AutoRepair(ia)

print("=== Teste AutoRepair ===\n")

# Codigo JS com erro (linha 1: variavel sem declaracao em modo estrito)
codigo_js = "'use strict';\nconst x = 1\nconsole.log(x)"

print(f"1. Codigo JS valido: {codigo_js[:50]}...")
r = tools.executar('validar_codigo', {'codigo': codigo_js})
print(f"   Valido: {r.get('resultado', {}).get('valido')}")

# Codigo JS com erro (falta fechar)
codigo_js_erro = "const x = 1\nconsole.log(x"
print(f"\n2. Codigo JS com erro: {codigo_js_erro[:50]}...")
r = tools.executar('validar_codigo', {'codigo': codigo_js_erro})
print(f"   Valido: {r.get('resultado', {}).get('valido')}")
erros = r.get('resultado', {}).get('erros', [f"Erro detectado"])

# Tenta reparar
print(f"\n3. AutoRepair...")
codigo_reparado, sucesso = reparador.reparar_e_validar(
    codigo_js_erro, erros, 'javascript', tools
)
print(f"   Reparado: {sucesso}")
print(f"   Codigo reparado: {codigo_reparado[:80]}...")

# Codigo Python com erro
codigo_py_erro = "def soma(a, b)\n    return a + b"
print(f"\n4. Python com erro: {codigo_py_erro[:50]}...")
r = tools.executar('validar_codigo', {'codigo': codigo_py_erro})
print(f"   Valido: {r.get('resultado', {}).get('valido')}")
erros_py = r.get('resultado', {}).get('erros', [f"SintaxError detectado"])

codigo_reparado_py, sucesso_py = reparador.reparar_e_validar(
    codigo_py_erro, erros_py, 'python', tools
)
print(f"   Reparado: {sucesso_py}")
print(f"   Codigo: {codigo_reparado_py[:80]}...")

print("\n=== FIM ===")
