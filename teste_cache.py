import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

pergunta = 'traduza hello world para PT-BR'

print('1a chamada (sem cache):')
t0 = time.time()
r1 = processar(pergunta)
t1 = time.time() - t0
print(f'  tempo: {t1:.2f}s')
print(f'  resposta: {r1["resposta"][:60]}')

print('\n2a chamada (com cache L1):')
t0 = time.time()
r2 = processar(pergunta)
t2 = time.time() - t0
print(f'  tempo: {t2:.2f}s')
print(f'  resposta: {r2["resposta"][:60]}')
print(f'  fonte: {r2["acoes"]}')

print(f'\nGanho: {t1/t2:.0f}x mais rapido')
