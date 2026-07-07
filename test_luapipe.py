import sys, time, json
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

t0 = time.time()
r = processar('crie uma habilidade de gelo chamada Lanca Glacial')
t = time.time() - t0

resp = r.get('resposta', '')
sintaxe = r.get('sintaxe_valida', 'N/A')
tentativas = r.get('tentativas_sintaxe', 'N/A')
print(f'Tempo: {t:.1f}s')
print(f'Tamanho resposta: {len(resp)}')
print(f'Sintaxe valida: {sintaxe}')
print(f'Tentativas: {tentativas}')
print()
print('Resposta:')
print(resp[:400])
