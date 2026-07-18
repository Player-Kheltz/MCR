import sys, time; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia

def log(msg):
    print(msg, flush=True); sys.stdout.flush()

log("=== Debug Wikipedia — feedback em tempo real ===")

t0 = time.time()
corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                 cache_only=True)
log(f"[1] Corpus cache_only: {len(corpus)} frases em {time.time()-t0:.1f}s")

if not corpus:
    log("ERRO: corpus vazio"); sys.exit(1)

# Testar com tamanhos crescentes para achar ponto de quebra
for tamanho in [100, 500, 1000, 2000, 5000, 10000, 20000, len(corpus)]:
    if tamanho > len(corpus):
        break
    c = MCRCoupling()
    subset = corpus[:tamanho]
    t0 = time.time()
    for i, (texto, acao) in enumerate(subset):
        c.alimentar(texto, acao)
    dt = time.time() - t0
    log(f"[2] {tamanho:6d} frases: {dt:.2f}s ({dt*1000/tamanho:.2f}ms/frase) "
        f"obs={c._total} pal={len(c._palavra_acao)}")

log("\n[3] Agora profile de 1 chamada extrair_relacoes apos 1000 frases:")
c = MCRCoupling()
c.alimentar_lote(corpus[:1000])
log(f"    Ingerido: {c._total} obs, {len(c._palavra_acao)} palavras")

import cProfile, pstats, io
# Pegar uma palavra que existe
pal_test = None
for p in c._palavra_acao:
    if len(p) >= 4:
        pal_test = p; break
log(f"    Palavra teste: {pal_test}")

pr = cProfile.Profile()
pr.enable()
t0 = time.time()
r = c.extrair_relacoes(pal_test, top_n=5)
dt = time.time() - t0
pr.disable()
log(f"    extrair_relacoes({pal_test}): {dt*1000:.0f}ms, "
    f"candidatos_relatos={list(r.keys())}")

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(15)
print(s.getvalue(), flush=True)

log("\n[4] Profile de _assinatura_frase apos 1000 frases:")
frases_test = ["cachorro late forte", "dog runs fast", "agua molha terra",
               "casa abriga pessoa", "amor une coracao"]
pr2 = cProfile.Profile()
pr2.enable()
t0 = time.time()
for f in frases_test:
    sig = c._assinatura_frase(f)
dt2 = time.time() - t0
pr2.disable()
log(f"    5 _assinatura_frase: {dt2*1000:.0f}ms ({dt2*1000/5:.1f}ms/frase)")

s2 = io.StringIO()
ps2 = pstats.Stats(pr2, stream=s2).sort_stats('cumulative')
ps2.print_stats(15)
print(s2.getvalue(), flush=True)

log("\n[5] DONE")
