import sys, time, os; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000)
print(f"Corpus: {len(corpus)} frases")

# Testar velocidade com 1000 frases
c = MCRCoupling()
t0 = time.time()
for i, (texto, acao) in enumerate(corpus[:1000]):
    c.alimentar(texto, acao)
dt = (time.time() - t0) * 1000
print(f"1000 frases: {dt:.0f}ms ({dt/1000:.1f}ms/frase)")
print(f"Estimativa para {len(corpus)}: {dt/1000 * len(corpus) / 1000:.0f}s")
