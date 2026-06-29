"""Self-Study com filtro de repeticoes."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
import time

ma = MasterAgent()
print('Iniciando Self-Study...')
t0 = time.time()
ma.self_study.executar()
print('OK em', round(time.time()-t0, 1), 's')
