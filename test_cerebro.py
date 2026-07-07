import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

t0 = time.time()
r = processar('explique o que e SPA no Projeto MCR')
t = time.time() - t0
resp = r.get('resposta', '')

print(f'Tempo: {t:.1f}s')
print(f'Classe: {r.get("classe")}')
ok = 'Progressao' in resp
print(f'Acertou: {ok}')
print(f'Resposta: {resp[:150]}')
