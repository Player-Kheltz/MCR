"""Testar diagnostico completo."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA
de = DiagnosticEngine(IA(), None, None)
p = de.diagnosticar()
print(de.gerar_relatorio(p))
print(f'\nTotal: {len(p)} problemas')
