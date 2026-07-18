import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia
import cProfile, pstats, io

corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000, cache_only=True)

# Profile 2000 frases para ver onde o tempo vai
c = MCRCoupling()
pr = cProfile.Profile()
pr.enable()
c.alimentar_lote(corpus[:2000])
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
