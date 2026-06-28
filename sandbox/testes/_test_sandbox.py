"""Teste do SandboxExecutor (Fase 4)."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.sandbox_executor import SandboxExecutor

print("=== Teste SandboxExecutor (Fase 4) ===\n")
sandbox = SandboxExecutor()

# Teste 1: Python OK
print("1. Python basico...")
r = sandbox.executar_python("print('hello world')")
print(f"   Resultado: sucesso={r['sucesso']}, stdout={r['stdout'][:50].strip()!r}")
assert r['sucesso'] == True
assert 'hello world' in r['stdout']

# Teste 2: Python com erro
print("\n2. Python com erro...")
r = sandbox.executar_python("x = 1/0")
print(f"   Resultado: sucesso={r['sucesso']}, stderr={r['stderr'][:80]}")
assert r['sucesso'] == False
assert 'ZeroDivisionError' in r['stderr']

# Teste 3: Python com timeout
print("\n3. Python com timeout...")
r = sandbox.executar_python("import time; time.sleep(30)")
print(f"   Resultado: sucesso={r['sucesso']}, stderr={r['stderr'][:80]}")
assert r['sucesso'] == False
assert 'excedido' in r['stderr'] or 'Timeout' in r['stderr']

# Teste 4: Codigo perigoso bloqueado
print("\n4. Codigo perigoso bloqueado...")
r = sandbox.executar_python("import os; os.system('rm -rf /')")
print(f"   Resultado: sucesso={r['sucesso']}, stderr={r['stderr']}")
assert r['sucesso'] == False
assert 'bloqueado' in r['stderr']

# Teste 5: Sintaxe invalida
print("\n5. Sintaxe invalida...")
r = sandbox.executar_python("x = ")
print(f"   Resultado: sucesso={r['sucesso']}, stderr={r['stderr'][:80]}")
assert r['sucesso'] == False
assert 'sintaxe' in r['stderr'].lower()

# Teste 6: Lua (fallback validação basica)
print("\n6. Lua (sem luac, validacao basica)...")
r = sandbox.compilar_lua("local x = 1\nprint(x)")
print(f"   Resultado: sucesso={r['sucesso']}, aviso={r.get('aviso','')}")
assert r['sucesso'] == True

# Teste 7: Metricas
print("\n7. Metricas...")
metrics = sandbox.metricas()
print(f"   Total: {metrics['total']}, Taxa sucesso: {metrics['taxa_sucesso']}")
assert metrics['total'] >= 6, f"Esperado >=6, tem {metrics['total']}"

print("\n=== TODOS OS TESTES PASSARAM ===")
