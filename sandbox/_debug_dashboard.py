#!/usr/bin/env python3
import sys, traceback
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')

try:
    print('Importando...')
    from modulos.dashboard import Dashboard
    from kernel import MCRKernel
    print('Criando kernel...')
    k = MCRKernel()
    k.inicializar()
    print('Criando dashboard...')
    d = Dashboard(k)
    print('Iniciando servidor...')
    sys.stdout.flush()
    d.iniciar()
except Exception as e:
    print(f'ERRO: {e}')
    traceback.print_exc()
    sys.stdout.flush()
