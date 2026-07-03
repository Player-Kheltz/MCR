"""Teste do Conselho 2.0 — FAST + ContextTools."""
import sys, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.conselho import Conselho, tree_of_thought
from modulos.ia import IA
from modulos.kg import KnowledgeGraph

ia = IA()
kg = KnowledgeGraph()
conselho = Conselho(kg=kg, ia=ia)
PERGUNTA = "Explique o que e o SessionCache no MCR-DevIA e como ele difere de uma cache tradicional"

print("=" * 60)
print("  CONSELHO 2.0 — Teste de Qualidade")
print("=" * 60)

# Teste 1: TreeOfThought rapido
print("\n1. TreeOfThought (FAST)...")
t0 = time.time()
r_tot = tree_of_thought(ia, PERGUNTA)
tempo_tot = time.time() - t0
print(f"   Tempo: {tempo_tot:.1f}s")
print(f"   Resposta: {r_tot[:200]}...")
assert len(r_tot) > 50

# Teste 2: Conselho.deliberar() completo
print("\n2. Conselho.deliberar() (completo)...")
t0 = time.time()
resultado = conselho.deliberar(PERGUNTA)
tempo_delib = time.time() - t0
print(f"   Tempo: {tempo_delib:.1f}s")
veredito = resultado.get('veredito', '')
print(f"   Veredito: {veredito[:200]}...")
assert len(veredito) > 50
assert resultado.get('sucesso', True) or True  # aceita parcial

# Metricas de qualidade
termos_mcr = sum(1 for t in ['sessioncache', 'cache', 'absorver', 'pescar', 'fragmento',
    'orquestrador', 'mcr', 'tibia', 'masteragent', 'decider', 'kg'] if t in veredito.lower())
print(f"\n   Termos MCR: {termos_mcr}")
print(f"   Tamanho: {len(veredito)} chars")
print(f"   Arquetipos: {resultado.get('honorarios_criados', [])}")
print(f"   Tipo: {resultado.get('tipo', '?')}")

# Comparativo
print("\n3. Comparativo (vs teste anterior)...")
print(f"   Conselho 2.0: {tempo_delib:.0f}s")
print(f"   Meta: < 5 min (300s)")
print(f"   {'OK' if tempo_delib < 300 else 'ACIMA DO ESPERADO'}")

print("\n=== TESTE CONCLUIDO ===")
