"""Ver erro de compilacao."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA
de = DiagnosticEngine(IA(), None, None)
p = de.check_compilacao()
for x in p:
    print('Arquivo:', x.get('arquivo'))
    print('Linha:', x.get('linha'))
    print('Msg:', x.get('msg'))
