"""Teste do pipeline fragmentado."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pipeline_executor import PipelineExecutor
from modulos.kg import KnowledgeGraph
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator

r = 'rota'
n = 'nota'
t = 'tamanho'
c = 'ciclos'

print("=== TESTE FRAGMENTADO ===")
kg = KnowledgeGraph()
ia = IA()
tools = ToolOrchestrator()
pipe = PipelineExecutor(kg=kg, ia=ia, tool_orchestrator=tools)

# Pergunta com multiplas intencoes
resposta, meta = pipe.executar(
    "Explique o sistema SPA do MCR. Crie um NPC guia em Eridanus.",
    modo_ia='auto'
)
print(f'Rota: {meta.get(r)}')
print(f'Nota: {meta.get(n)}')
print(f'Tamanho: {meta.get(t)}')
print(f'Ciclos/frags: {meta.get(c)}')
print()
print(f'Resposta ({len(resposta)} chars):')
print(resposta[:500])
print('...')
