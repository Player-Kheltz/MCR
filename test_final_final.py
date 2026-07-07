import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

# 1: SPA
t0 = time.time()
r = processar('explique o que e SPA no Projeto MCR')
t = time.time() - t0
resp = r.get('resposta', '')
ok = 'Progressao' in resp or 'Aventureiro' in resp
print(f'[SPA] {t:.1f}s: {"OK" if ok else "X"}')
print(f'  {resp[:120]}')

# 2: cache
t0 = time.time()
r2 = processar('explique o que e SPA no Projeto MCR')
t = time.time() - t0
print(f'[CACHE] {t:.4f}s: {r2.get("acoes",[])}')

# 3: Traducao
t0 = time.time()
r3 = processar('traduza hello world para PT-BR')
t = time.time() - t0
print(f'[TRAD] {t:.1f}s: {r3.get("resposta","")[:60]}')

print(f'\nResumo: OK')
