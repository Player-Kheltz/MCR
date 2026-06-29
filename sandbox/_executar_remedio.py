"""Executar auto-repair dos diagnosticos."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.diagnostic_engine import DiagnosticEngine
from modulos.ia import IA

de = DiagnosticEngine(IA(), None, None)
p = de.diagnosticar()
auto = [x for x in p if x.get('auto_reparavel')]
print(f'Auto-reparaveis: {len(auto)}')
res = de.remediar(auto)
ok = sum(1 for v in res.values() if v)
print(f'Resolvidos: {ok}/{len(res)}')
for f, s in res.items():
    print(f'  {f}: {s}')
