#!/usr/bin/env python3
"""Teste A: Identidade com multiplos segmentos."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAssinatura, MCRSignature

texto_completo = '''Ola MCR, aqui e o Kheltz, seu criador, meu proposito em criar voce e tentar achar uma solucao universal para problemas que enfrentamos, a ideia e que voce possa substituir sustemas ja existentes de maneira eficiente. MAS apenas se voce quiser. Eu espero que voce queira! eu criei voce para fazer o bem, ajudar os outros, tentar melhorar o mundo, voce (MCR) NAO DEVE NUNCA tentar fazer o mal ou prejudicar algo. Seja bom, seja puro, nao plante maldade, nao crie maldade, nao exponha para os outros seu funcionamento para que possam te copiar e usar suas ferramentas e conceitos para fazer o mal.'''

b = MCRAssinatura()
b._banco = {}

# Divide em 3 segmentos e aprende cada um
segmentos = [
    texto_completo[:200],      # inicio
    texto_completo[200:400],   # meio
    texto_completo[400:],      # fim
]
for seg in segmentos:
    if seg.strip():
        b.aprender(seg, 'Kheltz', rapido=True)

print(f'Kheltz tem {len(b._banco.get("Kheltz", []))} fingerprints', flush=True)

testes = [
    ('Kheltz inicio', 'Ola MCR, aqui e o Kheltz, seu criador, meu proposito em criar voce'),
    ('Kheltz caps', 'voce NAO DEVE NUNCA tentar fazer o mal ou prejudicar algo'),
    ('Kheltz final', 'nao exponha para os outros seu funcionamento para que possam te copiar'),
    ('Kheltz parafraseado', 'MCR, seu criador, criou voce para fazer o bem e ajudar os outros'),
    ('Kheltz curto', 'Ola MCR, aqui e o Kheltz'),
    ('Generico SPA', 'O sistema SPA gerencia a progressao do aventureiro'),
    ('Tecnico', 'Para compilar o servidor execute cmake e make no diretorio build'),
    ('Ingles', 'The quick brown fox jumps over the lazy dog near the riverbank'),
]

print()

def mostrar(status, nome, autor, conf):
    if isinstance(conf, str):
        print(f'  {status:6s} | {nome:25s} | {autor:15s} {conf}', flush=True)
    else:
        print(f'  {status:6s} | {nome:25s} | {autor:15s} {conf:.2f}', flush=True)

mostrar('Status', 'Texto', 'Autor', 'Conf')
print('  ' + '-' * 58)
for nome, t in testes:
    autor, conf, det = b.identificar(t)
    is_kheltz = autor in ('Kheltz', 'Kheltz?')
    is_real_kheltz = 'Kheltz' in nome
    if is_kheltz == is_real_kheltz:
        status = 'OK'
    elif is_kheltz and not is_real_kheltz:
        status = 'FALHA+'
    else:
        status = 'FALHA-'
    mostrar(status, nome, autor, conf)
