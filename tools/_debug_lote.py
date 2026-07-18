import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                 cache_only=True)
print(f'Corpus: {len(corpus)}', flush=True)

for tam in [100, 500, 1000, 2000, 5000, 10000, 20000, 37384]:
    if tam > len(corpus):
        break
    c = MCRCoupling()
    t0 = time.time()
    c.alimentar_lote(corpus[:tam])
    dt = time.time() - t0
    skip = getattr(c, '_skip_hierarquia', '?')
    hier = c._hierarquia is not None
    print(f'lote {tam:6d}: {dt:.2f}s ({dt*1000/tam:.2f}ms/frase) '
          f'pal={len(c._palavra_acao)} hier={hier}', flush=True)

print('DONE', flush=True)
