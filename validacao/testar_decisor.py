"""Teste MCRDecisorUniversal."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis de habilidade', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao as sinergias combinam dominios elementais', 'shc')
motor.alimentar('O NPC ferreiro em Eridanus se chama Bruno Ferro Forte ele vende armaduras de ferro e aco espadas basicas e escudos na praca central', 'npc')

# DecisorUniversal
params = MCRDecisorUniversal.decidir(motor, 'gerar_npc')
print('Parametros decididos pela Equacao MCR:')
for k, v in params.items():
    print(f'  {k}: {v}')

print()

# Geracao com parametros decididos
for texto in ['SPA e o sistema', 'Crie um NPC ferreiro', 'O SHC tem 5 camadas']:
    r = motor.gerar_por_assinatura(texto)  # sem passos — MCRDecisorUniversal decide
    print(f'  [{texto:30s}] (passos={MCRDecisorUniversal.decidir(motor)["passos"]}) -> {r[:80]}')

print()

# DecisorLen
for teste in ['a', 'ab', 'abc', 'SPA', 'sistema', 'progressao']:
    min_len = MCRDecisorUniversal.decidir_len(motor, 'teste', fallback=3)
    valido = len(teste) >= min_len
    print(f'  len({teste})={len(teste)} >= min_len={min_len} -> {valido}')

print()
print('MCRDecisorUniversal OK!')
