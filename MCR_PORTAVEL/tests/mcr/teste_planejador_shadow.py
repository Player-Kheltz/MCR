#!/usr/bin/env python3
import os, sys, os
_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'devia', 'kernel'))
sys.path.insert(0, os.path.dirname(__file__))
from mcr.planejador import Planejador
from mcr.shadow_canary import executar_shadow_codigo, _HAS_LUPA
p = Planejador()
print(f'LUPA disponivel: {_HAS_LUPA}')
print()
for tipo in ['ferreiro', 'mago', 'guarda', 'bardo']:
    codigo = p.gerar(tipo)
    print(f'Tipo: {tipo} | {len(codigo)} chars')
    resultado = executar_shadow_codigo(codigo)
    status = resultado.get('status', '?')
    erro = resultado.get('erro', '')[:120]
    if status in ('pass', 'ok'):
        print(f'  OK - ShadowCanary sem crash')
    else:
        print(f'  FALHA: {status} - {erro}')
    print()
