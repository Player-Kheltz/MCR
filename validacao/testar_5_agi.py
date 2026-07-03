"""Teste dos 5 componentes AGI finais."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

print('=== TESTE DOS 5 COMPONENTES AGI ===')
print()

motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado', 'shc')

# 1. MCRFuel - busca arquivos
fuel = MCRFuel(motor)
n = fuel.buscar_arquivos(r'E:\Projeto MCR\validacao', '*.py', 5)
print(f'1. Fuel: {n} arquivos encontrados (+{len(motor.topicos)} topicos)')

# 2. MCRWebLearn - busca web
web = MCRWebLearn(motor)
nweb = web.buscar('MCR sigla significado')
print(f'2. WebLearn: {nweb} paginas aprendidas (+{len(motor.topicos)} topicos)')

# 3. MCRSelfHeal - detecta problemas
heal = MCRSelfHeal(motor)
avaliacao = heal.avaliar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo', 'Explique o que e SPA')
print(f'3. SelfHeal: saudavel={avaliacao["saudavel"]} nota={avaliacao["nota"]} diag={avaliacao["diagnostico"]}')

avaliacao2 = heal.avaliar('a a a a a a a a a a a a a a', 'Explique o que e SPA')
print(f'   SelfHeal (repetitivo): saudavel={avaliacao2["saudavel"]} nota={avaliacao2["nota"]} diag={avaliacao2["diagnostico"]}')
print(f'   Cura: {avaliacao2["cura"][:60]}')

# 4. MCRFeedback - aprende com usuario
feedback = MCRFeedback(motor)
r1 = feedback.receber('Explique SPA', 'SPA e o sistema de progressao', 9.0)
print(f'4. Feedback (nota 9): gap={r1["gap"]} threshold={r1["threshold_ajustado"]}')
r2 = feedback.receber('Explique SPA', 'coisa tal tal', 2.0)
print(f'   Feedback (nota 2): gap={r2["gap"]} threshold={r2["threshold_ajustado"]}')

# 5. MCRPesoNota - descobre pesos otimos
pesos = MCRPesoNota(motor)
p = pesos.testar_pesos()
print(f'5. PesoNota: pesos={p}')

print()
print('5 COMPONENTES AGI OK!')
