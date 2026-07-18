import sys, json, os, random
sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling

CACHE_DIR = 'cache/validacao'
with open(os.path.join(CACHE_DIR, 'corpus_validacao.json'), 'r', encoding='utf-8') as f:
    obs = json.load(f)

random.seed(42)
obs_sample = random.sample(obs, 50000)

mcr = MCRCoupling()
mcr.alimentar_lote(obs_sample)
print('Vocab:', len(mcr._transicao_palavra))

for w in ['casa', 'house', 'maison', 'agua', 'water', 'amor', 'love', 'zone']:
    if w in mcr._transicao_palavra:
        ctx = mcr._transicao_palavra[w]
        print(w, ':', len(ctx), 'ctx tokens')
        # Mostrar acoes (posicao_acao)
        pa = mcr._posicao_acao.get(w, [])
        if isinstance(pa, dict):
            acoes = list(pa.keys())
        elif isinstance(pa, list):
            acoes = pa
        else:
            acoes = []
        print('  acoes count:', len(acoes))
        print('  acoes sample:', acoes[:5])
        print('  ctx sample:', list(ctx.keys())[:8])
    else:
        print(w, ': NAO ENCONTRADO')

# Verificar _assinatura_palavra de 'casa'
print()
print('=== _palavra_acao casa ===')
pa = mcr._palavra_acao.get('casa', {})
print('  acoes:', dict(list(pa.items())[:5]), '... total:', len(pa))

print()
print('=== _palavra_acao house ===')
pa = mcr._palavra_acao.get('house', {})
print('  acoes:', dict(list(pa.items())[:5]), '... total:', len(pa))

print()
print('=== Assinatura casa ===')
sig = mcr._assinatura_palavra('casa')
print('  total keys:', len(sig))
acao_keys = [k for k in sig if k.startswith('acao:')]
ctx_keys = [k for k in sig if k.startswith('ctx:')]
posacao_keys = [k for k in sig if k.startswith('posacao:')]
print('  acao:', len(acao_keys), 'ctx:', len(ctx_keys), 'posacao:', len(posacao_keys))
print('  acao sample:', [(k, sig[k]) for k in acao_keys[:5]])
print('  ctx sample:', [(k, sig[k]) for k in ctx_keys[:5]])

print()
print('=== Assinatura house ===')
sig2 = mcr._assinatura_palavra('house')
print('  total keys:', len(sig2))
acao_keys2 = [k for k in sig2 if k.startswith('acao:')]
ctx_keys2 = [k for k in sig2 if k.startswith('ctx:')]
posacao_keys2 = [k for k in sig2 if k.startswith('posacao:')]
print('  acao:', len(acao_keys2), 'ctx:', len(ctx_keys2), 'posacao:', len(posacao_keys2))
print('  acao sample:', [(k, sig2[k]) for k in acao_keys2[:5]])

# Intersecao de acoes entre casa e house
acoes_casa = set(k for k in sig if k.startswith('acao:'))
acoes_house = set(k for k in sig2 if k.startswith('acao:'))
inter = acoes_casa & acoes_house
print()
print('Intersecao acoes casa & house:', len(inter))
if inter:
    print('  sample:', list(inter)[:5])

# NMI entre casa e house
print()
print('NMI casa~house:', mcr._nmi_semantico('casa', 'house'))
print('NMI casa~mesa:', mcr._nmi_semantico('casa', 'mesa'))
