import sys, time; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

def log(msg):
    print(msg, flush=True); sys.stdout.flush()

log("=== Comparacao: alimentar() vs alimentar_lote() ===")
corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                 cache_only=True)
log(f"Corpus: {len(corpus)} frases\n")

for tamanho in [100, 500, 1000, 2000, 5000, 10000, 20000]:
    if tamanho > len(corpus):
        break

    # alimentar() individual (com hierarquia)
    c1 = MCRCoupling()
    t0 = time.time()
    for texto, acao in corpus[:tamanho]:
        c1.alimentar(texto, acao)
    dt1 = time.time() - t0

    # alimentar_lote() (sem hierarquia durante lote)
    c2 = MCRCoupling()
    t0 = time.time()
    c2.alimentar_lote(corpus[:tamanho])
    dt2 = time.time() - t0

    log(f"{tamanho:6d} frases | individual: {dt1:.2f}s ({dt1*1000/tamanho:.2f}ms/f) "
        f"pal={len(c1._palavra_acao)} | lote: {dt2:.2f}s ({dt2*1000/tamanho:.2f}ms/f) "
        f"pal={len(c2._palavra_acao)} | speedup={dt1/dt2:.1f}x")

log("\nDONE")
