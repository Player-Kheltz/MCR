"""Inventario honesto: o que e hardcoded vs o que e descoberta real."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling

# Motor: Wikipedia SEM pontes (titulo nativo)
motor = MCRCoupling()
cache_dir = os.path.join('cache', 'corpus_expa', 'wiki_5')

corpus = []
for f in os.listdir(cache_dir):
    if not f.endswith('.txt'):
        continue
    path = os.path.join(cache_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        frases = [line.strip() for line in fh if line.strip()][:500]
    idioma = f[:2]
    titulo = f[3:-4].replace('_', ' ').lower()
    for fr in frases:
        corpus.append((fr, titulo))

motor.alimentar_lote(corpus)
motor._cache_idf_doc = {}
motor._cache_idf_total = len(motor._palavra_acao) or 1
for w in motor._transicao_palavra:
    for ctx_token in motor._transicao_palavra[w]:
        motor._cache_idf_doc[ctx_token] = motor._cache_idf_doc.get(ctx_token, 0) + 1

print(f'Obs: {motor._total}, pal: {len(motor._transicao_palavra)}')

# Diagnostico: por que cachorro~dog=0 mas casa~house=0.615?
def diag(a, b):
    sa = motor._assinatura_palavra(a)
    sb = motor._assinatura_palavra(b)
    if not sa or not sb:
        print(f'  {a:12} ~ {b:12}: MISSING (a={bool(sa)} b={bool(sb)})')
        return
    ctx_a = {k.split(':',1)[1] for k in sa if k.startswith('ctx:')}
    ctx_b = {k.split(':',1)[1] for k in sb if k.startswith('ctx:')}
    shared = ctx_a & ctx_b
    nmi = motor._nmi_semantico(sa, sb)
    print(f'  {a:12} ~ {b:12}: NMI={nmi:.3f}  |ctx_a|={len(ctx_a)} |ctx_b|={len(ctx_b)} shared={len(shared)}')
    if shared:
        top = sorted(shared, key=lambda t: -motor._cache_idf_doc.get(t,1))[:5]
        for t in top:
            df = motor._cache_idf_doc.get(t, 1)
            idf = math.log(motor._cache_idf_total / max(df, 1))
            print(f'    shared: {t:20} IDF={idf:.2f}')

print('\n=== CASO 1: Descobertos (casa~house, agua~water) ===')
for a, b in [('casa', 'house'), ('agua', 'water'), ('luz', 'light'), ('amor', 'love')]:
    diag(a, b)

print('\n=== CASO 2: FALHARAM (cachorro~dog) ===')
for a, b in [('cachorro', 'dog'), ('cachorro', 'perro'), ('cavalo', 'horse')]:
    diag(a, b)

print('\n=== CASO 3: nao-relacionados (devem ser 0) ===')
for a, b in [('cachorro', 'mesa'), ('fogo', 'numero'), ('agua', 'computador')]:
    diag(a, b)

# O que torna um par "descobrivel"?
print('\n=== ANALISE: o que prediz descoberta? ===')
pares = [
    ('casa', 'house', True), ('agua', 'water', True), ('luz', 'light', True),
    ('amor', 'love', True), ('fogo', 'fire', True), ('peixe', 'fish', True),
    ('gato', 'cat', True), ('cachorro', 'dog', True), ('cachorro', 'perro', True),
    ('cavalo', 'horse', True), ('dog', 'perro', True),
]
for a, b, expected in pares:
    sa = motor._assinatura_palavra(a)
    sb = motor._assinatura_palavra(b)
    if not sa or not sb:
        print(f'  {a:12}~{b:12}: MISSING')
        continue
    ctx_a = {k.split(':',1)[1] for k in sa if k.startswith('ctx:')}
    ctx_b = {k.split(':',1)[1] for k in sb if k.startswith('ctx:')}
    shared = ctx_a & ctx_b
    nmi = motor._nmi_semantico(sa, sb)
    # Cognatos: palavras que aparecem em ambos os artigos (cross-language bleed)
    cognatos = [t for t in shared if len(t) > 3 and t not in {'que', 'uma', 'com', 'por', 'para', 'the', 'and', 'for', 'that', 'with'}]
    print(f'  {a:12}~{b:12}: NMI={nmi:.3f} shared={len(shared)} cognatos={cognatos[:5]}')
