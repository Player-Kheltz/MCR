"""Inventory of all tools in ToolOrchestrator."""
import re, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.tool_orchestrator import ToolOrchestrator

tools = ToolOrchestrator()
lista = tools.listar()

print(f"Total de ferramentas: {len(lista)}")
print()
print(f"{'Ferramenta':30s} | {'Descricao':60s}")
print(f"{'-'*30} | {'-'*60}")
for item in sorted(lista):
    if isinstance(item, tuple) and len(item) >= 2:
        nome, desc = item[0], item[1]
    elif isinstance(item, dict):
        nome = item.get('name', item.get('nome', '?'))
        desc = item.get('desc', item.get('descricao', ''))
    else:
        nome = str(item)
        desc = ''
    print(f"{str(nome)[:30]:30s} | {str(desc)[:60]:60s}")
