"""tools/_diag_decidir.py — Diagnóstico: onde o decidir() trava?

Carrega motor, chama decidir() uma vez, mede tempo. Sem chat, sem BC,
sem gerador. Só o núcleo.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling

c = MCRCoupling()
caminho = os.path.join('cache', 'coupling_MCRCoupling_backup_preB2c.json')
print(f'Carregando {caminho}...')
t0 = time.time()
c.load(caminho)
print(f'  load: {time.time()-t0:.1f}s')
print(f'  obs={c._total}, vocab={len(c._transicao_palavra)}, acoes={len(c._freq_acao)}')

# Testar decidir uma vez
print('\ndecidir("o que e mcr")...')
t0 = time.time()
acao, conf = c.decidir('o que e mcr', (None, 0.0))
dt = time.time() - t0
print(f'  tempo: {dt:.2f}s')
print(f'  acao={acao}, conf={conf}')

# Testar decidir com texto curto
print('\ndecidir("casa")...')
t0 = time.time()
acao, conf = c.decidir('casa', (None, 0.0))
dt = time.time() - t0
print(f'  tempo: {dt:.2f}s')
print(f'  acao={acao}, conf={conf}')

# Testar _tentar_base_conhecimento diretamente (BC vazio deve ser rapido)
print('\n_nmi_semantico("casa","house")...')
t0 = time.time()
try:
    sig_a = c._assinatura_palavra('casa')
    sig_b = c._assinatura_palavra('house')
    nmi = c._nmi_semantico(sig_a, sig_b)
    dt = time.time() - t0
    print(f'  tempo: {dt:.2f}s, nmi={nmi:.4f}')
except Exception as e:
    dt = time.time() - t0
    print(f'  tempo: {dt:.2f}s, ERRO: {e}')
