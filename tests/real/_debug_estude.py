import sys, re
sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
c = MCRCoupling()
corpus = [('criar monstro','criar'),('gerar npc','criar'),('fazer item','criar'),('editar script','editar'),('modificar codigo','editar'),('alterar texto','editar'),('buscar funcao','buscar'),('encontrar arquivo','buscar'),('procurar palavra','buscar'),('aprender licao','aprender'),('estudar materia','aprender'),('memorizar regra','aprender')]
for t,a in corpus: c.alimentar(t,a)
print('=== estude o sistema de npc ===')
frase = 'estude o sistema de npc'
palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
for p in set(palavras):
    dist = c._palavra_acao.get(p, {})
    print(f'\n[{p}] conhecido={bool(dist)}')
    if dist:
        print(f'  dist={dict(dist)}')
    else:
        h = c._heranca_morfologica(p)
        acoes_h = {k:v for k,v in h.items() if k.startswith('acao:') and v > 0}
        print(f'  heranca_acoes={acoes_h}')
        proxies = c.palavras_similares(p, threshold=0.20)
        print(f'  proxies={proxies}')

print()
print('_dist_palavras:', c._dist_palavras(frase))
print('_dist_posicoes:', c._dist_posicoes(frase))
print('decidir:', c.decidir(frase, (None, 0.0)))
