"""Teste rapido do Model Router V2 - so config"""
import sys, json, os
try:
    sys.path.insert(0, "E:\\Projeto MCR\\Scripts\\mcr_devia")
except Exception:
    pass
from mcr_devia import _melhor_modelo

print("=== Model Router V2 ===")
cargos = ["fast", "code", "contexto", "raciocinio", "leve", "revisor", "planejador", "embedding"]
for cargo in cargos:
    cfg = _melhor_modelo(cargo)
    print(f"  {cargo:<12} -> {cfg['modelo']:<25} ctx={cfg['ctx']}")

print()
print("Configuracao correta!")
