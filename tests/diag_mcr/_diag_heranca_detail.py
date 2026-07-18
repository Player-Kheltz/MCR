import sys, os
sys.path.insert(0, 'E:/MCR'); os.chdir('E:/MCR')
from mcr.coupling import MCRCoupling
from mcr.semantic_router import similaridade as ngram_sim

corpus = [
    ('gato late', 'animais'), ('cachorro late', 'animais'),
    ('gato mia', 'animais'), ('cachorro corre', 'animais'),
    ('passaro voa', 'animais'), ('peixe nada', 'animais'),
    ('carro corre', 'veiculos'), ('moto corre', 'veiculos'),
    ('caminhao anda', 'veiculos'), ('bicicleta anda', 'veiculos'),
    ('uva doce', 'frutas'), ('maca doce', 'frutas'),
    ('limao azedo', 'frutas'), ('banana amarela', 'frutas'),
    ('fogo queima', 'elementos'), ('agua molha', 'elementos'),
    ('gelo congela', 'elementos'), ('vento sopra', 'elementos'),
    ('criar monstro', 'criar'), ('gerar npc', 'criar'),
    ('fazer item', 'criar'), ('editar script', 'editar'),
    ('modificar codigo', 'editar'), ('alterar texto', 'editar'),
    ('buscar funcao', 'buscar'), ('encontrar arquivo', 'buscar'),
    ('procurar palavra', 'buscar'), ('aprender licao', 'aprender'),
    ('estudar materia', 'aprender'), ('memorizar regra', 'aprender'),
]
c = MCRCoupling()
for txt, act in corpus:
    c.alimentar(txt, act)

palavra = 'fabrique'
doadores = []
for known in c._palavra_acao.keys():
    if known == palavra: continue
    s = ngram_sim(palavra, known)
    if s <= 0: continue
    sig = c._assinatura_palavra(known)
    if not sig: continue
    doadores.append((s, known, sig))

doadores.sort(key=lambda x: -x[0])

# Simular exatamente o loop
heranca = {}
for s, known, sig in doadores[:7]:
    print(f'  {known}: s={s:.4f}')
    for k, v in sig.items():
        if k.startswith('acao:'):
            heranca[k] = heranca.get(k, 0.0) + v * s
            print(f'    {k}: +{v} * {s:.4f} = {v*s:.4f} => total={heranca[k]:.4f}')

print()
for k, v in heranca.items():
    print(f'  {k}: {v:.4f} >=0.5={v>=0.5}')