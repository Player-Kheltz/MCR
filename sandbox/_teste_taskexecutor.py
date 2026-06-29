"""Verificar TaskExecutor e compilacao."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
ma = MasterAgent()
print('OK')
print('task_executor:', type(ma.task_executor).__name__)
print('_executar_subtarefa existe:', hasattr(ma, '_executar_subtarefa'))
print('_integrar existe:', hasattr(ma, '_integrar'))
print('emergir:', type(ma.emergir).__name__)
print('self_study:', type(ma.self_study).__name__)
import os
lines = sum(1 for l in open(r'E:\Projeto MCR\scripts\mcr_devia\modulos\master_agent.py', 'r').readlines())
print('master_agent.py:', lines, 'linhas')
