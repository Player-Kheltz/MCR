import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

# Uma pergunta nova que NAO esta no cache
pergunta = 'crie uma habilidade de raio chamada Trovoada Arcana para o dominio Energia 26'
print(f'> {pergunta}')
t0 = time.time()
r = processar(pergunta)
t = time.time() - t0

resp = r.get('resposta', '')
print(f'Tempo: {t:.1f}s')
print(f'Sintaxe valida: {r.get("sintaxe_valida")}')
print(f'Tentativas: {r.get("tentativas_sintaxe")}')
print(f'Tamanho: {len(resp)}')
print()
print('Resposta:')
print(resp[:500])
