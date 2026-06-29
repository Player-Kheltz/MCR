"""Ver diagnostic engine."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
print('Metodos:', [m for m in dir(DiagnosticEngine) if not m.startswith('_')])
