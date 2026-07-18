import sys, time, os
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

def main():
    corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                     cache_only=True)
    print(f'Corpus: {len(corpus)} frases', flush=True)
    print(f'Cores disponiveis: {os.cpu_count()}', flush=True)

    # Sequencial
    c1 = MCRCoupling()
    t0 = time.time()
    c1.alimentar_lote(corpus)
    dt1 = time.time() - t0
    print(f'Sequencial: {dt1:.2f}s ({dt1*1000/len(corpus):.2f}ms/frase) '
          f'obs={c1._total} pal={len(c1._palavra_acao)}', flush=True)

    # Paralelo
    c2 = MCRCoupling()
    t0 = time.time()
    c2.alimentar_swarm_paralelo(corpus, n_workers=0)
    dt2 = time.time() - t0
    print(f'Paralelo:   {dt2:.2f}s ({dt2*1000/len(corpus):.2f}ms/frase) '
          f'obs={c2._total} pal={len(c2._palavra_acao)}', flush=True)
    print(f'Speedup: {dt1/dt2:.2f}x', flush=True)
    print(f'Consistencia: obs={c1._total==c2._total} '
          f'pal={len(c1._palavra_acao)==len(c2._palavra_acao)}', flush=True)

if __name__ == '__main__':
    main()
