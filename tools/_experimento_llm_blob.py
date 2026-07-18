"""Experimento v5: MCR le embeddings REAIS com tokens validos.

v4 tinha bug: "d0alto" era quebrado pelo regex [a-zà-ÿ]{3,} em "alto".
Todas as dims com bin "alto" viravam o mesmo token — nao discriminava.

v5 usa codificacao por letras: dim0→xa, dim1→xb, ..., dim25→xz, dim26→xba...
Assim cada dim+bin e um token unico de letras continuas.

Tambem testamos com mais palavras (80) para melhor distribuicao.
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
    """Codifica dim como letras continuas: 0→a, 1→b, ..., 25→z, 26→aa, 27→ab..."""
    s = ''
    dim += 1
    while dim > 0:
        dim -= 1
        s = chr(97 + dim % 26) + s
        dim //= 26
    return s

# 40 palavras: 20 PT + 20 EN, 5 dominios
PALAVRAS = {
    'animal': ['cachorro','gato','cavalo','peixe','dog','cat','horse','fish'],
    'cor':    ['vermelho','azul','verde','amarelo','red','blue','green','yellow'],
    'emocao': ['amor','alegria','tristeza','medo','love','joy','sadness','fear'],
    'elem':   ['agua','fogo','terra','luz','water','fire','earth','light'],
    'objeto': ['cadeira','mesa','porta','janela','chair','table','door','window'],
}

DESC_PT = {
    'cachorro':'animal domestico que late tem quatro patas','gato':'animal domestico que mia tem quatro patas',
    'cavalo':'animal forte que galopa tem quatro patas','peixe':'animal aquatico que nada tem escamas',
    'vermelho':'cor forte associada a sangue e paixao','azul':'cor associada ao ceu e ao mar',
    'verde':'cor associada a plantas e natureza','amarelo':'cor associada ao sol e ao ouro',
    'amor':'sentimento forte associado a carinho e afeto','alegria':'sentimento bom associado a felicidade',
    'tristeza':'sentimento ruim associado a chorar','medo':'sentimento associado a perigo e ansiedade',
    'agua':'liquido essencial a vida que e molhado','fogo':'combustao que produz calor e luz',
    'terra':'solo solido do planeta terra','luz':'energia visivel que ilumina o ambiente',
    'cadeira':'movel com quatro pernas feito de madeira para sentar','mesa':'movel com tampo liso para apoiar objetos',
    'porta':'entrada feita de madeira que abre e fecha','janela':'abertura com vidro que deixa entrar luz',
}
DESC_EN = {
    'dog':'domestic animal that barks has four legs','cat':'domestic animal that meows has four legs',
    'horse':'strong animal that gallops has four legs','fish':'aquatic animal that swims has scales',
    'red':'strong color associated with blood and passion','blue':'color associated with sky and sea',
    'green':'color associated with plants and nature','yellow':'color associated with sun and gold',
    'love':'strong feeling associated with care and affection','joy':'good feeling associated with happiness',
    'sadness':'bad feeling associated with crying','fear':'feeling associated with danger and anxiety',
    'water':'liquid essential to life that is wet','fire':'combustion that produces heat and light',
    'earth':'solid soil of the planet earth','light':'visible energy that illuminates the environment',
    'chair':'furniture with four legs made of wood for sitting','table':'furniture with flat top for supporting objects',
    'door':'entrance made of wood that opens and closes','window':'opening with glass that lets in light',
}

def get_desc(w):
    return DESC_PT.get(w, DESC_EN.get(w, ''))

todas = []
for v in PALAVRAS.values():
    todas.extend(v)

print(f"=== Experimento: Embeddings REAIS nomic-embed-text (768D) ===", flush=True)
print(f"Palavras: {len(todas)} (20 PT + 20 EN, 5 dominios)", flush=True)

# 1. Gerar embeddings reais
print("\nGerando embeddings via Ollama...", flush=True)
matriz = {}
for i, w in enumerate(todas):
    matriz[w] = embed(w)
    if (i+1) % 10 == 0:
        print(f"  {i+1}/{len(todas)}", flush=True)
    time.sleep(0.05)

dims = len(matriz[todas[0]])
print(f"Embeddings: {len(matriz)} x {dims}D", flush=True)

# 2. Discretizacao emergente (tercis)
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

# Debug: verificar tokenizacao
teste_tok = f"cachorro {dim_label(0)}alto {dim_label(1)}baixo"
import re
toks = re.findall(r'[a-zà-ÿ]{3,}', teste_tok.lower())
print(f"\nDebug tokenizacao: '{teste_tok}' -> {toks}", flush=True)

# 3. Pares
pares_sin = [
    ('cachorro','dog'),('gato','cat'),('cavalo','horse'),('peixe','fish'),
    ('vermelho','red'),('azul','blue'),('verde','green'),('amarelo','yellow'),
    ('amor','love'),('alegria','joy'),('tristeza','sadness'),('medo','fear'),
    ('agua','water'),('fogo','fire'),('terra','earth'),('luz','light'),
    ('cadeira','chair'),('mesa','table'),('porta','door'),('janela','window'),
]
pares_nao = [
    ('cachorro','vermelho'),('gato','agua'),('amor','cadeira'),('fogo','tristeza'),
    ('agua','azul'),('cachorro','amor'),('verde','medo'),('porta','alegria'),
    ('peixe','fear'),('terra','vermelho'),('cavalo','azul'),('mesa','fogo'),
    ('dog','red'),('cat','water'),('love','chair'),('fear','green'),
    ('blue','sadness'),('fire','joy'),('horse','yellow'),('door','love'),
]

def testar(c, label):
    sin_nmi, nao_nmi = [], []
    for a, b in pares_sin:
        sa = c._assinatura_palavra(a); sb = c._assinatura_palavra(b)
        if sa and sb:
            sin_nmi.append(c._nmi_semantico(sa, sb))
    for a, b in pares_nao:
        sa = c._assinatura_palavra(a); sb = c._assinatura_palavra(b)
        if sa and sb:
            nao_nmi.append(c._nmi_semantico(sa, sb))
    if not sin_nmi or not nao_nmi:
        print(f"  {label:25s}: SEM DADOS (sin={len(sin_nmi)} nao={len(nao_nmi)})", flush=True)
        return 0, 0, 0
    s = sum(sin_nmi)/len(sin_nmi)
    n = sum(nao_nmi)/len(nao_nmi)
    d = s - n
    v = "PASS" if d > 0.15 else ("FRACO" if d > 0.05 else "FAIL")
    print(f"  {label:25s}: Sin={s:.4f} Nao={n:.4f} Delta={d:.4f} [{v}]", flush=True)
    return s, n, d

N_EPOCHS = 3
random.seed(42)

# === TESTE A: SO BLOB ===
# Cada dim+bin vira uma observacao de 2 palavras: "cachorro aalto"
# Assim _transicao_palavra["cachorro"]["aalto"] = count — captura TODOS os dims
print(f"\n=== TESTE A: SO BLOB (embeddings reais, obs de 2 palavras) ===", flush=True)
c_blob = MCRCoupling()
lote = []
for epoch in range(N_EPOCHS):
    for w, emb in matriz.items():
        for dim in range(dims):
            val = emb[dim] + random.gauss(0, abs(emb[dim])*0.05)
            tok = f"{dim_label(dim)}{binarizar(val, dim)}"
            lote.append((f"{w} {tok}", w))
print(f"  {len(lote)} obs, ingerindo...", flush=True)
c_blob.alimentar_lote(lote)
print(f"  palavras={len(c_blob._palavra_acao)}", flush=True)
sig_test = c_blob._assinatura_palavra('cachorro')
sig_test2 = c_blob._assinatura_palavra('dog')
ctx_c = {k for k in sig_test if k.startswith('ctx:')}
ctx_d = {k for k in sig_test2 if k.startswith('ctx:')}
print(f"  cachorro ctx={len(ctx_c)} dog ctx={len(ctx_d)} overlap={len(ctx_c & ctx_d)}", flush=True)
testar(c_blob, "So blob (768D real)")

# === TESTE B: SO DESCRICAO ===
print(f"\n=== TESTE B: SO DESCRICAO ===", flush=True)
c_desc = MCRCoupling()
lote_desc = []
for w in todas:
    for _ in range(N_EPOCHS):
        lote_desc.append((f"{w} e {get_desc(w)}", w))
c_desc.alimentar_lote(lote_desc)
testar(c_desc, "So descricao PT/EN")

# === TESTE C: BLOB + DESCRICAO ===
print(f"\n=== TESTE C: BLOB + DESCRICAO ===", flush=True)
c_bd = MCRCoupling()
lote_bd = []
for epoch in range(N_EPOCHS):
    for w, emb in matriz.items():
        for dim in range(dims):
            val = emb[dim] + random.gauss(0, abs(emb[dim])*0.05)
            tok = f"{dim_label(dim)}{binarizar(val, dim)}"
            lote_bd.append((f"{w} {tok}", w))
for w in todas:
    for _ in range(3):
        lote_bd.append((f"{w} e {get_desc(w)}", w))
c_bd.alimentar_lote(lote_bd)
testar(c_bd, "Blob + descricao")

# === TESTE D: COSINE ORACLE ===
print(f"\n=== TESTE D: Cosine direto (oracle) ===", flush=True)
sin_cos, nao_cos = [], []
for a, b in pares_sin:
    va, vb = matriz[a], matriz[b]
    cos = sum(va[i]*vb[i] for i in range(dims)) / (
        math.sqrt(sum(x*x for x in va)) * math.sqrt(sum(x*x for x in vb)))
    sin_cos.append(cos)
for a, b in pares_nao:
    va, vb = matriz[a], matriz[b]
    cos = sum(va[i]*vb[i] for i in range(dims)) / (
        math.sqrt(sum(x*x for x in va)) * math.sqrt(sum(x*x for x in vb)))
    nao_cos.append(cos)
s_c = sum(sin_cos)/len(sin_cos)
n_c = sum(nao_cos)/len(nao_cos)
d_c = s_c - n_c
v_c = "PASS" if d_c > 0.15 else "FAIL"
print(f"  Cosine oracle: Sin={s_c:.4f} Nao={n_c:.4f} Delta={d_c:.4f} [{v_c}]", flush=True)

# === extrair_relacoes ===
print(f"\n=== extrair_relacoes (blob+desc) ===", flush=True)
for w in ['cachorro','vermelho','amor','agua','cadeira','dog','red','love']:
    r = c_bd.extrair_relacoes(w, top_n=5)
    sin = r.get('sinonimos', [])
    print(f"  {w:12s} sin: {[(s2,round(v,3)) for s2,v in sin[:5]]}", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"RESUMO: Embeddings REAIS nomic-embed-text (768D, 40 palavras)", flush=True)
print(f"  Cosine oracle:  Delta={d_c:.4f} [{v_c}] (este e o teto do embedding)", flush=True)
print(f"  Se cosine oracle FAIL: o embedding NAO discrimina sinonimia", flush=True)
print(f"  Se MCR >= cosine: MCR extrai tudo que o embedding tem", flush=True)
print(f"{'='*60}", flush=True)
