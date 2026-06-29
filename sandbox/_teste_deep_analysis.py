"""Teste Self-Study com Deep Analysis."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
import time
ma = MasterAgent()
print('Iniciando Self-Study com Deep Analysis...')
t0 = time.time()
ma.self_study.executar()
print('Concluido em', round(time.time()-t0, 1), 's')
