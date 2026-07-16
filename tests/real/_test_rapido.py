import json, time, sys
sys.path.insert(0,'E:/MCR')
from mcr.coupling import MCRCoupling

caminho = 'E:/MCR/cache/npc_knowledge.json'
print('Carregando JSON...')
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

print('Alimentando 1000 amostras...')
c = MCRCoupling()
t0 = time.time()
c.alimentar_lote(pares[:1000])
print('  %.2fs' % (time.time()-t0))
est = c.estatisticas()
print('  tokens=%d features_nd=%d acao_features=%d' % (est['palavras'], est['features_nd'], len(c._acao_features)))

print('\nComparacoes semanticas (NOVA abordagem contextual):')
for a,b,desc in [
    ('criar','gerar','sinonimos'),
    ('criar','produzir','sinonimo parcial'),
    ('criar','matar','verbos diferentes'),
    ('criar','curar','verbos diferentes'),
    ('falar','dizer','sinonimos'),
    ('falar','matar','diferentes'),
    ('comprar','vender','transacao'),
    ('mago','druida','entidades magicas'),
    ('orc','goblin','entidades hostis'),
    ('mago','computador','distantes'),
]:
    t0=time.time()
    s=c.similaridade(a,b)
    print('  %s~%s = %.4f  (%s, %.1fms)' % (a,b,s,desc,(time.time()-t0)*1000))

print('\nPalavras similares a "criar":')
sim = c.palavras_similares('criar', threshold=0.05, max_resultados=10)
for p,s in sim:
    print('  %s (%.4f)' % (p,s))
