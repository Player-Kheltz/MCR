import json, sys, os
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

# Suprime stdout
import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        from mcr_devia import KnowledgeGraph
        kg = KnowledgeGraph()
    finally:
        sys.stdout = old

topicos = {
    "Rust": "Rust String str",
    "Go": "Go goroutines channels",
    "TypeScript": "TypeScript types generics",
    "Python": "Python type hints dataclasses",
}

for nome, busca in topicos.items():
    results = kg.buscar(busca, max_r=3)
    print(f"{nome}: {len(results)} lessons")
    for l in results:
        erro = l.get('erro', 'sem titulo')[:80]
        sol = l.get('solucao', '')[:120]
        print(f"  - {erro}")
        print(f"    {sol}")
    print()
