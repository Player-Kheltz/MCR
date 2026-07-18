"""Experimento v6: Testar se o problema e do embedding ou do MCR.

v5 mostrou: cosine oracle delta=0.04 FAIL para sinonimos跨-idioma.
Hipotese: nomic-embed-text nao alinha PT/EN (e monolingue).

Teste: sinonimos EN-EN vs nao-relacionados EN-EN.
Se cosine oracle PASS para EN-EN: o problema e跨-idioma, nao do MCR.
Se cosine oracle FAIL para EN-EN: o embedding nao captura sinonimia.
"""
import sys, math, json, time, urllib.request, random
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling

OLLAMA_URL = 'http://localhost:11434/api/embeddings'
MODEL = 'nomic-embed-text'

def embed(texto):
    data = json.dumps({'model': MODEL, 'prompt': texto}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())['embedding']

def dim_label(dim):
    s = ''
    dim += 1
    while dim > 0:
        dim -= 1
        s = chr(97 + dim % 26) + s
        dim //= 26
    return s

# Sinonimos EN-EN e nao-relacionados EN-EN
pares_sin_en = [
    ('dog','puppy'),('cat','kitten'),('horse','stallion'),
    ('happy','joyful'),('sad','unhappy'),('angry','furious'),
    ('big','large'),('small','little'),('fast','quick'),('smart','clever'),
    ('beautiful','pretty'),('strong','powerful'),('hot','scorching'),
    ('cold','freezing'),('begin','start'),('end','finish'),
    ('help','assist'),('buy','purchase'),('eat','consume'),('walk','stroll'),
]

pares_nao_en = [
    ('dog','table'),('cat','fire'),('happy','chair'),('sad','water'),
    ('big','red'),('small','love'),('fast','earth'),('smart','door'),
    ('beautiful','cold'),('strong','sad'),('hot','walk'),('cold','buy'),
    ('begin','cat'),('end','dog'),('help','fire'),('buy','sad'),
    ('eat','happy'),('walk','angry'),('dog','begin'),('cat','end'),
]

todas_en = list(set(a for a,b in pares_sin_en+pares_nao_en) | set(b for a,b in pares_sin_en+pares_nao_en))
print(f"=== Teste EN-EN: {len(todas_en)} palavras, {len(pares_sin_en)} sinonimos, {len(pares_nao_en)} nao-rel ===", flush=True)

# Gerar embeddings
print("Gerando embeddings...", flush=True)
matriz = {}
for i, w in enumerate(todas_en):
    matriz[w] = embed(w)
    if (i+1) % 10 == 0:
        print(f"  {i+1}/{len(todas_en)}", flush=True)
    time.sleep(0.05)

dims = len(matriz[todas_en[0]])
print(f"Embeddings: {len(matriz)} x {dims}D", flush=True)

# Cosine oracle EN-EN
print("\n=== Cosine oracle EN-EN ===", flush=True)
sin_cos, nao_cos = [], []
for a, b in pares_sin_en:
    va, vb = matriz[a], matriz[b]
    cos = sum(va[i]*vb[i] for i in range(dims)) / (
        math.sqrt(sum(x*x for x in va)) * math.sqrt(sum(x*x for x in vb)))
    sin_cos.append(cos)
for a, b in pares_nao_en:
    va, vb = matriz[a], matriz[b]
    cos = sum(va[i]*vb[i] for i in range(dims)) / (
        math.sqrt(sum(x*x for x in va)) * math.sqrt(sum(x*x for x in vb)))
    nao_cos.append(cos)
s_c = sum(sin_cos)/len(sin_cos)
n_c = sum(nao_cos)/len(nao_cos)
d_c = s_c - n_c
v_c = "PASS" if d_c > 0.15 else ("FRACO" if d_c > 0.05 else "FAIL")
print(f"  Sinonimos:    {s_c:.4f}", flush=True)
print(f"  Nao-relac:    {n_c:.4f}", flush=True)
print(f"  Delta:        {d_c:.4f} [{v_c}]", flush=True)

# Discretizacao
bins_dim = {}
for dim in range(dims):
    vals = sorted(matriz[w][dim] for w in matriz)
    n = len(vals)
    bins_dim[dim] = (vals[n//3], vals[2*n//3])

def binarizar(val, dim):
    t1, t2 = bins_dim[dim]
    if val >= t2: return 'alto'
    elif val >= t1: return 'medio'
    else: return 'baixo'

# MCR so blob
print("\n=== MCR so blob (EN-EN) ===", flush=True)
random.seed(42)
c_blob = MCRCoupling()
lote = []
for epoch in range(3):
    for w, emb in matriz.items():
        for dim in range(dims):
            val = emb[dim] + random.gauss(0, abs(emb[dim])*0.05)
            tok = f"{dim_label(dim)}{binarizar(val, dim)}"
            lote.append((f"{w} {tok}", w))
print(f"  {len(lote)} obs", flush=True)
c_blob.alimentar_lote(lote)

sin_nmi, nao_nmi = [], []
for a, b in pares_sin_en:
    sa = c_blob._assinatura_palavra(a); sb = c_blob._assinatura_palavra(b)
    if sa and sb:
        sin_nmi.append(c_blob._nmi_semantico(sa, sb))
for a, b in pares_nao_en:
    sa = c_blob._assinatura_palavra(a); sb = c_blob._assinatura_palavra(b)
    if sa and sb:
        nao_nmi.append(c_blob._nmi_semantico(sa, sb))
s_m = sum(sin_nmi)/len(sin_nmi) if sin_nmi else 0
n_m = sum(nao_nmi)/len(nao_nmi) if nao_nmi else 0
d_m = s_m - n_m
v_m = "PASS" if d_m > 0.15 else ("FRACO" if d_m > 0.05 else "FAIL")
print(f"  Sinonimos:    {s_m:.4f}", flush=True)
print(f"  Nao-relac:    {n_m:.4f}", flush=True)
print(f"  Delta:        {d_m:.4f} [{v_m}]", flush=True)

# MCR blob + descricao EN
print("\n=== MCR blob + descricao (EN-EN) ===", flush=True)
DESC_EN_EXTRA = {
    'dog':'domestic animal that barks','puppy':'young dog',
    'cat':'domestic animal that meows','kitten':'young cat',
    'horse':'large animal that gallops','stallion':'male horse',
    'happy':'feeling of joy','joyful':'full of happiness',
    'sad':'feeling of sorrow','unhappy':'not happy',
    'angry':'feeling of rage','furious':'very angry',
    'big':'of large size','large':'of great size',
    'small':'of little size','little':'small in size',
    'fast':'moving quickly','quick':'moving with speed',
    'smart':'intelligent','clever':'mentally sharp',
    'beautiful':'very pretty','pretty':'attractive',
    'strong':'having power','powerful':'having strength',
    'hot':'high temperature','scorching':'very hot',
    'cold':'low temperature','freezing':'very cold',
    'begin':'to start','start':'to begin',
    'end':'to finish','finish':'to complete',
    'help':'to assist','assist':'to help',
    'buy':'to purchase','purchase':'to buy',
    'eat':'to consume food','consume':'to ingest',
    'walk':'to stroll','stroll':'to walk',
}

c_bd = MCRCoupling()
lote_bd = []
for epoch in range(3):
    for w, emb in matriz.items():
        for dim in range(dims):
            val = emb[dim] + random.gauss(0, abs(emb[dim])*0.05)
            tok = f"{dim_label(dim)}{binarizar(val, dim)}"
            lote_bd.append((f"{w} {tok}", w))
for w in todas_en:
    desc = DESC_EN_EXTRA.get(w, w)
    for _ in range(5):
        lote_bd.append((f"{w} is {desc}", w))
c_bd.alimentar_lote(lote_bd)

sin_bd, nao_bd = [], []
for a, b in pares_sin_en:
    sa = c_bd._assinatura_palavra(a); sb = c_bd._assinatura_palavra(b)
    if sa and sb:
        sin_bd.append(c_bd._nmi_semantico(sa, sb))
for a, b in pares_nao_en:
    sa = c_bd._assinatura_palavra(a); sb = c_bd._assinatura_palavra(b)
    if sa and sb:
        nao_bd.append(c_bd._nmi_semantico(sa, sb))
s_bd = sum(sin_bd)/len(sin_bd) if sin_bd else 0
n_bd = sum(nao_bd)/len(nao_bd) if nao_bd else 0
d_bd = s_bd - n_bd
v_bd = "PASS" if d_bd > 0.15 else ("FRACO" if d_bd > 0.05 else "FAIL")
print(f"  Sinonimos:    {s_bd:.4f}", flush=True)
print(f"  Nao-relac:    {n_bd:.4f}", flush=True)
print(f"  Delta:        {d_bd:.4f} [{v_bd}]", flush=True)

# Resumo
print(f"\n{'='*60}", flush=True)
print(f"RESUMO EN-EN (nomic-embed-text real)", flush=True)
print(f"  Cosine oracle:  Delta={d_c:.4f} [{v_c}]", flush=True)
print(f"  MCR so blob:    Delta={d_m:.4f} [{v_m}]", flush=True)
print(f"  MCR blob+desc:  Delta={d_bd:.4f} [{v_bd}]", flush=True)
print(f"{'='*60}", flush=True)
if d_c > 0.05:
    print("Cosine PASS: o embedding TEM estrutura semantica", flush=True)
    if d_m > 0.05:
        print("MCR PASS: extraiu a estrutura do blob!", flush=True)
    else:
        print("MCR < cosine: perdeu info na discretizacao", flush=True)
else:
    print("Cosine FAIL: o embedding NAO captura sinonimia em palavra isolada", flush=True)
    print("Proximo passo: embeddings de FRASE ou modelo multilingue", flush=True)
