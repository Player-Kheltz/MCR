import sys, os, re
sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
c = MCRCoupling()
corpus = [('criar monstro','criar'),('gerar npc','criar'),('fazer item','criar'),('editar script','editar'),('modificar codigo','editar'),('alterar texto','editar'),('buscar funcao','buscar'),('encontrar arquivo','buscar'),('procurar palavra','buscar'),('aprender licao','aprender'),('estudar materia','aprender'),('memorizar regra','aprender')]
for t,a in corpus: c.alimentar(t,a)
print('Vocabulario:', sorted(c._palavra_acao.keys()))
print()
casos = ['gere um orc forte','produza um dragao verde','construa uma espada','mude o nome do npc','troque a cor do monstro','ache a funcao de combate','localize o arquivo de magia','ensine como fazer item','estude o sistema de npc','crie um gato que voa','edite o look do orc','procure o npc vendedor']
for f in casos:
    palavras = re.findall(r'[a-zà-ÿ]{3,}', f.lower())
    novas = [p for p in palavras if p not in c._palavra_acao]
    conhecidas = [p for p in palavras if p in c._palavra_acao]
    print(f'{f:<40} novas={novas} conhecidas={conhecidas}')
