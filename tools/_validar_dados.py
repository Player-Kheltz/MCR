import sys; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from tools.wikipedia_corpus import buscar_corpus_wikipedia
from tools.corpus_multilingue import sinonimos_teste

corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=2000, cache_only=True)
c = MCRCoupling()
c.alimentar_lote(corpus)
print(f'obs={c._total} pal={len(c._palavra_acao)}')

# 1. Quantas acoes distintas?
acoes = set()
for p, dist in c._palavra_acao.items():
    for a in dist:
        acoes.add(a)
print(f'Acoes distintas: {len(acoes)}')

# 2. Quantas palavras com >1 acao?
multi = sum(1 for p, dist in c._palavra_acao.items() if len(dist) > 1)
print(f'Palavras com >1 acao: {multi} / {len(c._palavra_acao)}')

# 3. Validar TODOS os pares sinonimos vs nao-relacionados (nao so media)
pares = sinonimos_teste()
sin_nmi, mesmo_nmi, cross_nmi = [], [], []
sin_detalhe, mesmo_detalhe, cross_detalhe = [], [], []

for a, b, tipo in pares:
    sa = c._assinatura_frase(a); sb = c._assinatura_frase(b)
    if sa and sb:
        nmi = c._nmi_semantico(sa, sb)
        if 'sinonimo' in tipo:
            sin_nmi.append(nmi)
            sin_detalhe.append((a, b, tipo, nmi))
        elif 'mesmo' in tipo:
            mesmo_nmi.append(nmi)
            mesmo_detalhe.append((a, b, tipo, nmi))
        else:
            cross_nmi.append(nmi)
            cross_detalhe.append((a, b, tipo, nmi))

# 4. Distribuicao — nao so a media
import statistics
def stats(vals, nome):
    if not vals:
        print(f'{nome}: vazio')
        return
    print(f'{nome}: n={len(vals)} min={min(vals):.3f} max={max(vals):.3f} '
          f'med={statistics.median(vals):.3f} media={sum(vals)/len(vals):.3f} '
          f'std={statistics.stdev(vals):.3f}')

stats(sin_nmi, 'Sinonimos  ')
stats(mesmo_nmi, 'Mesmo dom  ')
stats(cross_nmi, 'Cross-dom  ')

# 5. Falsos negativos (sinonimos com NMI baixo)
print('\n=== Falsos negativos (sinonimos com NMI < 0.5) ===')
fn = [(a,b,t,n) for a,b,t,n in sin_detalhe if n < 0.5]
for a,b,t,n in fn[:10]:
    print(f'  {a:15s} vs {b:15s} [{t:20s}] NMI={n:.4f}')
print(f'Total: {len(fn)}/{len(sin_nmi)} sinonimos com NMI<0.5')

# 6. Falsos positivos (nao-relacionados com NMI alto)
print('\n=== Falsos positivos (nao-relacionados com NMI > 0.8) ===')
fp = [(a,b,t,n) for a,b,t,n in mesmo_detalhe + cross_detalhe if n > 0.8]
for a,b,t,n in fp[:10]:
    print(f'  {a:15s} vs {b:15s} [{t:20s}] NMI={n:.4f}')
print(f'Total: {len(fp)} nao-relacionados com NMI>0.8')

# 7. Overlap de planos
print('\n=== Planos por palavra (cachorro/dog/gato/cat) ===')
for p in ['cachorro','dog','perro','gato','cat','agua','water','amor','love']:
    sig = c._assinatura_palavra(p)
    planos = {}
    for k in sig:
        prefixo = k.split(':', 1)[0] if ':' in k else '_sem'
        planos[prefixo] = planos.get(prefixo, 0) + 1
    print(f'  {p:12s}: {planos}')
