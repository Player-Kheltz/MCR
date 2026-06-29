"""Executa Self-Study e mostra resultado."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
import time

print('Iniciando Self-Study...')
t0 = time.time()
ma = MasterAgent()
ma._self_study()
print('Concluido em', round(time.time()-t0, 1), 's')
