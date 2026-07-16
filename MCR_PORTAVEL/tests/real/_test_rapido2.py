import json, time, sys
sys.path.insert(0,'E:/MCR')
from mcr.coupling import MCRCoupling

caminho = 'E:/MCR/cache/npc_knowledge.json'
with open(caminho, 'r', encoding='utf-8') as f:
    dados = json.load(f)

pares = []
for dialogos_lista in dados.get('dialogos', {}).values():
    for item in dialogos_lista:
        texto = str(item[0]) if item[0] else ''
        npc = str(item[1]) if len(item) > 1 else 'desconhecido'
        if len(texto) >= 10:
            pares.append((texto, npc))

print('%d dialogos, %d NPCs' % (len(pares), len(set(a for _,a in pares))))

print('Alimentando TUDO em paralelo (4 workers)...')
c = MCRCoupling()
t0 = time.time()
c.alimentar_lote_paralelo(pares, n_workers=4)
dt = time.time() - t0
est = c.estatisticas()
print('  %.1fs | tokens=%d features=%d acoes=%d' % (dt, est['palavras'], est['features_nd'], len(c._acao_features)))

print('\nComparacoes semanticas:')
pares_teste = [
    ('criar','gerar'), ('criar','produzir'), ('criar','matar'),
    ('criar','curar'), ('criar','falar'), ('criar','comprar'),
    ('falar','dizer'), ('falar','gritar'), ('falar','matar'),
    ('comprar','vender'), ('comprar','pegar'), ('comprar','matar'),
    ('mago','druida'), ('mago','orc'), ('mago','computador'),
    ('matar','lutar'), ('matar','curar'),
    ('precisar','precisa'), ('precisar','matar'),
]
for a,b in pares_teste:
    s = c.similaridade(a,b)
    print('  %s~%s = %.4f' % (a,b,s))

print('\nPalavras similares a "criar" (top 15, threshold=0.01):')
sim = c.palavras_similares('criar', threshold=0.01, max_resultados=15)
for p,s in sim:
    print('  %s (%.4f)' % (p,s))

print('\nPalavras similares a "matar":')
sim = c.palavras_similares('matar', threshold=0.01, max_resultados=15)
for p,s in sim:
    print('  %s (%.4f)' % (p,s))

print('\nPalavras similares a "comprar":')
sim = c.palavras_similares('comprar', threshold=0.01, max_resultados=15)
for p,s in sim:
    print('  %s (%.4f)' % (p,s))
