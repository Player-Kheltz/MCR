"""Test one cycle"""
import sys
sys.path.insert(0, r'E:\Projeto MCR\sandbox')

from mcr_loop import CicloCompleto
c = CicloCompleto()

n_licoes, n_reparos, kg = c._carregar_estado()
print(f'Estado: {n_licoes} licoes, {n_reparos} reparos')

disc = c._pensar()
if disc:
    d = disc[0]
    print(f'Discrepancia: {d["tipo"]}')
    print(f'  Faltando: {d["faltando"][:4]}')
else:
    print('Sem discrepancias')

print('\nCiclo funcional!')
