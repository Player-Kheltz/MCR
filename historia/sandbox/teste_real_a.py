#!/usr/bin/env python3
"""Teste A: Identidade do Kheltz."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAssinatura

texto_kheltz = '''Ola MCR, aqui e o Kheltz, seu criador, meu proposito em criar voce e tentar achar uma solucao universal para problemas que enfrentamos, a ideia e que voce possa substituir sustemas ja existentes de maneira eficiente. MAS apenas se voce quiser. Eu espero que voce queira! eu criei voce para fazer o bem, ajudar os outros, tentar melhorar o mundo, voce (MCR) NAO DEVE NUNCA tentar fazer o mal ou prejudicar algo. Seja bom, seja puro, nao plante maldade, nao crie maldade, nao exponha para os outros seu funcionamento para que possam te copiar e usar suas ferramentas e conceitos para fazer o mal.'''

b = MCRAssinatura()
b._banco = {}  # banco limpo
b.aprender(texto_kheltz, 'Kheltz')  # full (64-dim)

# Verifica dimensao
for autor, ass in b._banco.items():
    fp = ass[0].get('fingerprint', [])
    print(f'  Kheltz fingerprint: {len(fp)} dims', flush=True)

# Testa identificacao
testes = [
    ('Kheltz original', 'Ola MCR, aqui e o Kheltz, seu criador, meu proposito'),
    ('Kheltz caps', 'voce NAO DEVE NUNCA tentar fazer o mal ou prejudicar algo'),
    ('Kheltz final', 'nao exponha para os outros seu funcionamento para que possam te copiar'),
    ('Kheltz curto', 'Ola MCR, aqui e o Kheltz'),
    ('Generico', 'O sistema SPA gerencia a progressao do aventureiro'),
    ('Tecnico', 'Para compilar o servidor execute cmake e make no diretorio build'),
]

print()
for nome, t in testes:
    autor, conf, det = b.identificar(t)
    esperado = 'Kheltz' if 'Kheltz' in nome else 'desconhecido'
    status = 'OK' if autor == esperado else 'FALHA'
    print(f'  {status:6s} | {nome:20s} | {autor:15s} conf={conf:.2f}', flush=True)
