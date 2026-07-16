import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR
mcr = MCR()
t0 = time.time()
r = mcr.processar('Gere um dragao')
elapsed = time.time()-t0
print(f'First call: {elapsed:.1f}s | acao={r["acao"]} | nota={r.get("nota")}')
t0 = time.time()
r2 = mcr.processar('Gere um orc')
elapsed2 = time.time()-t0
print(f'Second call: {elapsed2:.1f}s | acao={r2["acao"]} | nota={r2.get("nota")}')
t0 = time.time()
r3 = mcr.processar('Qual e a diferenca entre knight e paladin?')
elapsed3 = time.time()-t0
print(f'Third call: {elapsed3:.1f}s | acao={r3["acao"]}')
