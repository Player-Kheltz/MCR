import sys, time, cProfile, pstats, io; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

print("=== Debug Wikipedia — profile por fase ===")

t0 = time.time()
corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                 cache_only=True)
t_corpus = time.time() - t0
print(f"Corpus (cache_only): {len(corpus)} frases em {t_corpus:.1f}s")

print(f"\nIngerindo {len(corpus)} frases com alimentar_lote (profile)...")
c = MCRCoupling()

pr = cProfile.Profile()
pr.enable()
t0 = time.time()
c.alimentar_lote(corpus)
t_ing = time.time() - t0
pr.disable()

print(f"Ingestao: {c._total} obs em {t_ing:.1f}s ({t_ing*1000/len(corpus):.1f}ms/frase)")
print(f"Palavras: {len(c._palavra_acao)}")

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print("\n=== PROFILE INGESTAO ===")
print(s.getvalue())
