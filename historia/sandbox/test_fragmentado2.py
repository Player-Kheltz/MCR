"""Teste fragmentacao + pipeline multi-intencao."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.pipeline_executor import PipelineExecutor
from modulos.kg import KnowledgeGraph
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator

# Test 1: fragmentacao
print("=== TESTE FRAGMENTACAO ===")
pe = PatternEngine()
frags = pe.tokenizar_fragmentado("Explique o sistema SPA do MCR. Crie um NPC guia em Eridanus.")
print(f"Fragmentos: {len(frags)}")
for f in frags:
    print(f"  '{f['fragmento'][:60]}' -> tipos: {f['tipos'][:5]}")

print()

# Test 2: pipeline completo
print("=== TESTE PIPELINE ===")
r_key = 'rota'
kg = KnowledgeGraph()
ia = IA()
tools = ToolOrchestrator()
pipe = PipelineExecutor(kg=kg, ia=ia, tool_orchestrator=tools)

resp, meta = pipe.executar(
    "Explique o sistema SPA do MCR. Crie um NPC guia em Eridanus.",
    modo_ia='auto'
)
print(f"Rota: {meta.get(r_key)}")
print(f"Fragments: {meta.get('ciclos')}")
print(f"Tamanho: {meta.get('tamanho')}")
print(f"Nota: {meta.get('nota')}")
print()
print("Resposta:")
print(resp[:600])
