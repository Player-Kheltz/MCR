"""tools/_profile_decidir.py — Onde decidir() trava?

cProfile numa unica chamada. Mostra top-20 funcoes por tempo.
"""
import os, sys, time, cProfile, pstats, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling

c = MCRCoupling()
caminho = os.path.join('cache', 'coupling_MCRCoupling_backup_preB2c.json')
print(f'Carregando...')
t0 = time.time()
c.load(caminho)
print(f'  load: {time.time()-t0:.1f}s')
print(f'  vocab={len(c._transicao_palavra)} acoes={len(c._freq_acao)}')

# Profile de uma chamada
print('\nProfiling decidir("o que e mcr")...')
pr = cProfile.Profile()
pr.enable()
t0 = time.time()
try:
    acao, conf = c.decidir('o que e mcr', (None, 0.0))
    dt = time.time() - t0
    print(f'  tempo: {dt:.2f}s, acao={acao}, conf={conf}')
except Exception as e:
    dt = time.time() - t0
    print(f'  tempo: {dt:.2f}s, ERRO: {e}')
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(30)
print('\n' + s.getvalue())
