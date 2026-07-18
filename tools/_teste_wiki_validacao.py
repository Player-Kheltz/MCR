import sys, time, os; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia
from tools.corpus_multilingue import sinonimos_teste

print("=== Validacao Wikipedia (cache_only + alimentar_lote) ===")

t0 = time.time()
corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000,
                                 cache_only=True)
print(f"Corpus (cache_only): {len(corpus)} frases em {time.time()-t0:.1f}s")

if not corpus:
    print("ERRO: corpus vazio. Rode buscar_corpus_wikipedia sem cache_only primeiro.")
    sys.exit(1)

print(f"\nIngerindo {len(corpus)} frases com alimentar_lote...")
c = MCRCoupling()
t0 = time.time()
c.alimentar_lote(corpus)
dt = time.time() - t0
print(f"Ingestao: {c._total} obs em {dt:.1f}s ({dt*1000/len(corpus):.1f}ms/frase)")
print(f"Palavras: {len(c._palavra_acao)}")

c.save("cache/coupling_wiki_teste.json")
print("Motor de teste salvo")

# Latencia
print("\n=== Latencia decidir() ===")
testes = ["cachorro late", "dog runs", "perro come", "agua e liquido",
          "water is liquid", "casa abriga pessoas", "house shelters people"]
latencias = []
for t in testes:
    t0 = time.time()
    acao, conf = c.decidir(t, (None, 0.0))
    dt = (time.time() - t0) * 1000
    latencias.append(dt)
    print(f"  decidir({t:30s}) = {acao:15s} conf={conf:.3f} ({dt:.0f}ms)")
print(f"Latencia media: {sum(latencias)/len(latencias):.0f}ms")

# Discriminacao跨-idioma
print("\n=== Discriminacao semantica跨-idioma (Wikipedia) ===")
pares = sinonimos_teste()
t0 = time.time()
sin, mesmo, cross = [], [], []
for a, b, tipo in pares:
    sa = c._assinatura_frase(a); sb = c._assinatura_frase(b)
    if sa and sb:
        nmi = c._nmi_semantico(sa, sb)
        if "sinonimo" in tipo: sin.append(nmi)
        elif "mesmo" in tipo: mesmo.append(nmi)
        else: cross.append(nmi)
dt_val = time.time() - t0

s = sum(sin)/len(sin); m = sum(mesmo)/len(mesmo); x = sum(cross)/len(cross)
print(f"Sinonimos:        {s:.4f} (n={len(sin)})")
print(f"Mesmo dominio:    {m:.4f} (n={len(mesmo)})")
print(f"Cross-dominio:    {x:.4f} (n={len(cross)})")
print(f"Delta sin-mesmo:  {s-m:.4f}")
print(f"Delta sin-cross:  {s-x:.4f}")
v1 = "PASS" if (s-m) > 0.15 else "FAIL"
v2 = "PASS" if (s-(m+x)/2) > 0.15 else "FAIL"
print(f"VEREDITO sin-mesmo: {v1}")
print(f"VEREDITO geral:     {v2}")
print(f"Tempo validacao: {dt_val:.1f}s ({dt_val*1000/len(pares):.1f}ms/par)")

# extrair_relacoes
print("\n=== extrair_relacoes (Wikipedia) ===")
for p in ["cachorro", "agua", "amor", "casa", "arvore"]:
    t0 = time.time()
    r = c.extrair_relacoes(p, top_n=5)
    dt = (time.time() - t0) * 1000
    sin = r.get("sinonimos", [])[:5]
    print(f"{p:12s} sinonimos: {[(s2, round(v,3)) for s2,v in sin]} ({dt:.0f}ms)")

print("\n=== RESUMO ===")
print(f"Ingestao:     {len(corpus)} frases")
print(f"Obs total:    {c._total}")
print(f"Palavras:     {len(c._palavra_acao)}")
print(f"Delta sin-mes: {s-m:.4f} ({v1})")
print(f"Delta sin-cro: {s-x:.4f} ({v2})")
