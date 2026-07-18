import sys
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling

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

casos = [
    ('gere', 'criar'),
    ('crie', 'criar'),
    ('edite', 'editar'),
    ('estude', 'aprender'),
    ('procure', 'buscar'),
    ('encontre', 'buscar'),
    ('fabrique', 'criar'),
]

acertos = 0
for nova, esp in casos:
    h = c._heranca_morfologica(nova)
    acoes = [(k[len('acao:'):], v) for k, v in h.items() if k.startswith('acao:') and v > 0]
    acoes.sort(key=lambda x: -x[1])
    top = acoes[0][0] if acoes else 'sem heranca'
    ok = top == esp
    if ok: acertos += 1
    print(f'  {nova:<15} esp={esp:<12} top={top:<20}  {"OK" if ok else "X"}')

print(f'\nHeranca acertos: {acertos}/{len(casos)} = {100*acertos/len(casos):.1f}%')