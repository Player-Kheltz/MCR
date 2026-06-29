"""Ver erros de compilacao."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA
de = DiagnosticEngine(IA(), None, None)
p = de.check_compilacao()
for x in p:
    print(str(x.get('arquivo','')) + ':L' + str(x.get('linha',0)) + ' ' + str(x.get('msg',''))[:60])
