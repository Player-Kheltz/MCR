import sys, time, os; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000)
print(f"Corpus: {len(corpus)} frases")

c = MCRCoupling()
t0 = time.time()
for i, (texto, acao) in enumerate(corpus):
    c.alimentar(texto, acao)
    if (i+1) % 10000 == 0:
        print(f"  {i+1}/{len(corpus)} ({time.time()-t0:.1f}s)")
print(f"Ingestao: {c._total} obs em {time.time()-t0:.1f}s")
print(f"Palavras: {len(c._palavra_acao)}")

c.save("cache/coupling_wiki_teste.json")
print("Motor salvo")
