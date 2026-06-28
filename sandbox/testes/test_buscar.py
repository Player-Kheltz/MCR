"""Testar busca no KG"""
import sys, json
sys.path.insert(0, "E:\\Projeto MCR\\scripts\\mcr_devia")
from mcr_devia import KnowledgeGraph

kg = KnowledgeGraph()
resultados = kg.buscar("SHC", max_r=5)
print(f"Resultados: {len(resultados)}")
for r in resultados:
    print(f"  {r.get('id','?')}: {r.get('solucao','')[:100]}")
