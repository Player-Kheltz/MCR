"""Testar BlankFiller modo cadeia."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.blank_filler import BlankFiller
from modulos.ia import IA
import time

bf = BlankFiller(IA())
skel = "Cenario: @BLANK_A\n\nPadrao: @BLANK_B\n\nPotencial: @BLANK_C"
ctx = "MCR = Tibia. Insight: integrar jogo de tabuleiro com SPA."
t0 = time.time()
result = bf.preencher_tudo(skel, ctx, modo='cadeia')
print('Tempo:', round(time.time()-t0,1), 's')
print('=== RESULTADO ===')
print(result)
