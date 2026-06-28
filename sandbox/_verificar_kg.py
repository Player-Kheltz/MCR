"""Verifica se o estudo foi registrado no KG."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
ultimas = kg.data['licoes'][-5:]
for l in ultimas:
    print(f"[{l['id']}] ctx={l['ctx']} | erro={l['erro'][:60]}")
    print(f"    solucao={l['solucao'][:100]}")
    print()
