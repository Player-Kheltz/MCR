"""Teste rapido do pipeline."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pipeline_executor import PipelineExecutor
from modulos.kg import KnowledgeGraph
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator

r_key = 'rota'

kg = KnowledgeGraph()
ia = IA()
tools = ToolOrchestrator()
pipe = PipelineExecutor(kg=kg, ia=ia, tool_orchestrator=tools)

resp, meta = pipe.executar('Explique o SPA', modo_ia='auto')
print(f'ROTA: {meta.get(r_key, "?")}')
print(resp[:300])
