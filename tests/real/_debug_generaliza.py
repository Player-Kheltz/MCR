import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
from mcr.semantic_router import similaridade as ngram_sim
c = MCRCoupling()
corpus = [('criar monstro','criar'),('gerar npc','criar'),('fazer item','criar'),('editar script','editar'),('modificar codigo','editar'),('alterar texto','editar'),('buscar funcao','buscar'),('encontrar arquivo','buscar'),('procurar palavra','buscar'),('aprender licao','aprender'),('estudar materia','aprender'),('memorizar regra','aprender')]
for t,a in corpus: c.alimentar(t,a)
novas = ['gere','produza','construa','mude','troque','ensine','estude','procure','crie','edite','localize','ache','construir']
known = list(c._palavra_acao.keys())
print('Palavras conhecidas:', known)
print()
for nova in novas:
    sims = [(k, ngram_sim(nova, k)) for k in known]
    sims.sort(key=lambda x: -x[1])
    top = sims[0]
    if top[1] > 0.3:
        herdada = c._assinatura_palavra(top[0])
        acoes = [k.replace('acao:','') for k in herdada.keys() if k.startswith('acao:')]
        label = top[0] + ' (' + str(round(top[1],3)) + ')'
        print(nova.ljust(12), '-> top='.ljust(0), label.ljust(25), 'herdado=', acoes)
    else:
        print(nova.ljust(12), '-> sem vizinho (top=' + top[0] + ', sim=' + str(round(top[1],3)) + ')')
