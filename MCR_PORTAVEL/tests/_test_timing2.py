import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR

mcr = MCR()
print('MCR init done')

# Pre-warm
for inp in ['Gere um orc', 'Gere um knight', 'Qual a diferenca?']:
    t0 = time.time()
    r = mcr.processar(inp)
    print(f'Warmup: {time.time()-t0:.1f}s acao={r["acao"]}')

# Time 10 calls
times = []
for i in range(10):
    t0 = time.time()
    r = mcr.processar('Gere um dragao de fogo')
    elapsed = time.time() - t0
    times.append(elapsed)
    print(f'  Call {i+1}: {elapsed:.2f}s | acao={r["acao"]} | nota={r.get("nota")}')

avg = sum(times) / len(times)
print(f'Average: {avg:.2f}s per call')
print(f'Estimated 480 calls: {480 * avg / 60:.1f} min')
