"""Check KG for test results."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.kg import KnowledgeGraph
from collections import Counter

kg = KnowledgeGraph()
licoes = kg._get_licoes()

print(f"Total lessons: {len(licoes)}")
print()

# Find inception and criacao_teste lessons
for l in licoes:
    ctx = l.get('ctx', '')
    if ctx in ('inception_aprendizado', 'criacao_teste'):
        err = l.get('erro', '')[:80]
        sol = l.get('solucao', '')[:150]
        fp = bool(l.get('fingerprint'))
        print(f"ctx={ctx}")
        print(f"  erro: {err}")
        print(f"  solucao: {sol}")
        print(f"  fingerprint: {fp}")
        print()

# Count by ctx
ctxs = Counter(l.get('ctx', '?') for l in licoes)
print("Top 10 ctxs:")
for ctx, n in ctxs.most_common(10):
    print(f"  {ctx}: {n}")
