"""Testar DiagnosticEngine."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA

de = DiagnosticEngine(IA(), None, None)
p = de.diagnosticar()
print('Problemas encontrados:', len(p))
for x in p:
    print(f'  {x["severidade"]:10s} {x["arquivo"]}:L{x["linha"]}  {x["msg"][:60]}')
