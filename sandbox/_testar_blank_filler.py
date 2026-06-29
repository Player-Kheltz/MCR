"""Testar BlankFiller com caso real."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.blank_filler import BlankFiller
from modulos.ia import IA

bf = BlankFiller(IA())
skel = bf.gerar_esqueleto(
    'Analise o arquivo kg.py: ele tem varias funcoes que lidam com leitura de arquivos JSON. Identifique problemas de seguranca e tratamento de erros.',
    tipo='analise', max_blanks=3
)
print('=== ESQUELETO ===')
print(skel)
print()
blanks = bf.listar_blanks(skel)
print('=== BLANKS:', blanks)
if blanks:
    for b in blanks:
        print(f'\n--- Preenchendo {b} ---')
        preenchido = bf.preencher_blank(skel, b, 'kg.py seguranca')
        print(preenchido[:200])
