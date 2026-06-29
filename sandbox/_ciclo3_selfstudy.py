"""Ciclo 3: Self-Study apos todas as refatoracoes."""
import sys, time
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
ma = MasterAgent()
print('Iniciando Self-Study...')
t0 = time.time()
ma.self_study.executar()
print('Concluido em', round(time.time()-t0, 1), 's')
