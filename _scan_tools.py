#!/usr/bin/env python3
"""Extrai ferramentas do tool_registry.py para o catalogo."""
import re, sys
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')

from devia.knowledge.tool_registry import ToolRegistry

tr = ToolRegistry()
print("ToolRegistry: %d ferramentas" % len(tr._ferramentas))
print()

# Agrupar por categoria
cats = {}
for nome, tool in tr._ferramentas.items():
    cat = tool.categoria
    if cat not in cats:
        cats[cat] = []
    cats[cat].append(tool)

for cat, tools in sorted(cats.items()):
    print("### %s (%d ferramentas)" % (cat.upper(), len(tools)))
    for t in sorted(tools, key=lambda x: x.nome):
        params = ', '.join(p.nome for p in t.parametros)
        print("  %-25s | %s | params: %s" % (t.nome, t.descricao[:50], params))
    print()
