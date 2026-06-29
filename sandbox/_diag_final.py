"""Diagnostico final."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA
de = DiagnosticEngine(IA(), None, None)
p = de.diagnosticar()
print(de.gerar_relatorio(p))
print('Total:', len(p))
print('Compilacao OK:', len(de.check_compilacao()) == 0)
falsos = [x for x in p if x.get('tipo') == 'except_sem_corpo' and 'return None' in x.get('msg', '')]
print('Sem falsos positivos (return None):', len(falsos) == 0)

