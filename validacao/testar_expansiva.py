"""Teste da MCRSignatureExpansiva."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

print('=== MCRSignatureExpansiva ===')
print()

# 1. Dimensionalidade ideal para diferentes dados
textos = [
    'a a a a a a a a a a a a a a a',                    # repetitivo
    '100 200 300 400 500 600 700 800 900 1000',         # sequencial
    'SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra',  # texto natural
]

for t in textos:
    dim = MCRSignatureExpansiva.dimensionalidade_ideal(t)
    fp = MCRSignatureExpansiva.fingerprint_texto(t, dim)
    h = MCRSignatureExpansiva.entropia_fingerprint(fp)
    print(f'  [{t[:40]:40s}] dim_ideal={dim:3d} entropia_fp={h:.3f}')

print()

# 2. Niveis ideais
motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado', 'shc')

niveis = MCRSignatureExpansiva.niveis_ideais(motor, 'Explique o que e SPA')
print(f'Niveis ideais: {niveis}')

print()

# 3. Autoavaliacao expansiva vs classica
for texto in ['SPA e o sistema', 'SHC tem 5 camadas', 'Crie um NPC ferreiro']:
    seq = motor.gerar_por_assinatura(texto, 6)
    nota_ex, det_ex = motor._autoavaliar_expansivo(seq,
        motor.topicos['spa']['texto'], motor.topicos['shc']['texto'])
    nota_cl, det_cl = motor._autoavaliar(seq,
        motor.topicos['spa']['texto'], motor.topicos['shc']['texto'], 'conteudo_compartilhado')
    print(f'  [{texto:30s}] expansiva={nota_ex:.1f}(dim={det_ex["dimensao_ideal"]}) classica={nota_cl:.1f}')

print()

# 4. Paradoxo: 100 200 300 → 400
seq_numeros = '100 200 300'
dim_num = MCRSignatureExpansiva.dimensionalidade_ideal(seq_numeros)
fp_num = MCRSignatureExpansiva.fingerprint_texto(seq_numeros, dim_num)
h_num = MCRSignatureExpansiva.entropia_fingerprint(fp_num)
print(f'Paradoxo numerico:')
print(f'  Sequencia: {seq_numeros}')
print(f'  Dim ideal: {dim_num}')
print(f'  Entropia fp: {h_num:.3f}')
print(f'  Fingerprint: {[round(v, 2) for v in fp_num[:8]]}')

# Se o padrao e auto-similar, o fingerprint de 100 200 300
# deve ser similar ao de 200 300 400
fp_123 = MCRSignatureExpansiva.fingerprint_texto('100 200 300', dim_num)
fp_234 = MCRSignatureExpansiva.fingerprint_texto('200 300 400', dim_num)
sim = MCRSignatureExpansiva.similaridade(fp_123, fp_234)
print(f'  Auto-similaridade (123 vs 234): {sim:.3f}')
print(f'  Se > 0.8, o padrao e previsivel em escala')

print()
print('OK!')
