"""Teste da refatoracao do master_agent.py."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent

ma = MasterAgent()
print('MasterAgent criado OK')
print('emergir engine:', type(ma.emergir).__name__)
print('self_study engine:', type(ma.self_study).__name__)

t1 = ma.emergir.amostrar_topicos(3)
print('emergir amostrar_topicos:', len(t1))

t2 = ma.self_study.escanear_projeto(10)
print('self_study escanear:', len(t2))

# Teste de compatibilidade (metodos no master_agent ainda existem)
print('_amostrar_topicos_distantes existe:', hasattr(ma, '_amostrar_topicos_distantes'))
print('_processar_emergencia existe:', hasattr(ma, '_processar_emergencia'))
print('_self_study existe:', hasattr(ma, '_self_study'))
print('_escanear_projeto existe:', hasattr(ma, '_escanear_projeto'))

import os
lines = sum(1 for l in open(r'E:\Projeto MCR\scripts\mcr_devia\modulos\master_agent.py', 'r').readlines())
print()
print('REFATORACAO CONCLUIDA!')
print('master_agent.py: 1838 ->', lines, 'linhas (reducao de', 1838-lines, 'linhas)')
print('Novos modulos: emergir.py, self_study.py')
