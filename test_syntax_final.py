import sys, time
sys.path.insert(0, r'E:\MCR')

# Limpa cache e importa fresh
import mcr_devia
mcr_devia._CACHE_L1.clear()
mcr_devia._CACHE_L2.clear()

# Query unica pra evitar cache
ts = str(time.time())[-6:]
pergunta = f'crie uma habilidade de raio chamada RaioCeleste{ts} para o dominio Energia 26'
print(f'Pergunta: {pergunta}')

t0 = time.time()
r = mcr_devia.processar(pergunta)
t = time.time() - t0

sv = r.get('sintaxe_valida')
st = r.get('tentativas_sintaxe')
resp = r.get('resposta', '')

print(f'Tempo: {t:.1f}s')
print(f'Sintaxe valida: {sv}')
print(f'Tentativas: {st}')
print(f'Tamanho: {len(resp)}')
print()
if resp:
    print(resp[:300])
else:
    print('(vazio)')
