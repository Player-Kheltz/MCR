"""Teste do RADAR MCR."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis de habilidade que o jogador pode evoluir', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao', 'shc')

# Teste 1: geracao normal vs RADAR
texto_base = 'SPA e o sistema de'
r_normal = motor.gerar_por_assinatura(texto_base, 12)
print('Normal:', r_normal[:120])

radar = MCRRadar(motor)
r_radar = radar.integrar_com_geracao(texto_base, passos=12)
print('RADAR: ', r_radar[:120])

print()

# Teste 2: RADAR puro (varrer)
resultado = radar.varrer('SPA e o sistema de progressao do aventureiro com dominios elementais', 15)
print(f'Radar varredura:')
print(f'  Direcao: {resultado["direcao"][:80]}')
print(f'  Nota: {resultado["nota"]}')
print(f'  Saiu do loop: {resultado["saiu_do_loop"]}')
print(f'  Total pulsos: {resultado["total_pulsos"]}')
print(f'  Threshold: {resultado.get("threshold", 0)}')
for h in resultado['historico'][:5]:
    print(f'  pulso {h["pulso"]}: {h["palavra"]:15s} nota={h["nota"]:.3f}')
if len(resultado['historico']) > 5:
    print(f'  ... +{len(resultado["historico"])-5} pulsos')

print()

# Teste 3: loop detection
radar2 = MCRRadar(motor)
em_loop = radar2.esta_em_loop('a a a a a a a a a a a a a a a a')
print(f'Loop detection (repeticoes): {em_loop}')
em_loop2 = radar2.esta_em_loop('SPA e o sistema de progressao do aventureiro')
print(f'Loop detection (texto normal): {em_loop2}')
