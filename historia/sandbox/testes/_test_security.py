"""Teste do modulo Security (Fase 8)."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.security import verificar_comando, verificar_codigo, verificar_request

print("=== Teste Security (Fase 8) ===\n")

# Teste 1: Comandos bloqueados
print("1. Comandos bloqueados...")
assert verificar_comando("rm -rf /") is not None
assert verificar_comando("shutdown -s") is not None
assert verificar_comando("dir c:\\") is None  # seguro
assert verificar_comando("python script.py") is None  # seguro
print("   OK")

# Teste 2: Codigo perigoso
print("\n2. Codigo perigoso...")
assert len(verificar_codigo("import os; os.system('ls')")) > 0
assert len(verificar_codigo("x = 1; print(x)")) == 0  # seguro
assert len(verificar_codigo("eval(input())")) > 0
print("   OK")

# Teste 3: Request bloqueado
print("\n3. Request bloqueado...")
assert verificar_request("apagar tudo") is not None
assert verificar_request("Cria um ferreiro em Eridanus") is None  # seguro
assert verificar_request("formatar disco") is not None
print("   OK")

print("\n=== TODOS OS TESTES PASSARAM ===")
