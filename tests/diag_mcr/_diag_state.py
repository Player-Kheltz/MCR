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

print('_palavra_acao keys:', list(c._palavra_acao.keys())[:10])
print()
print('assinatura_palavra(fazer):', c._assinatura_palavra('fazer'))
print()
print('assinatura_palavra(criar):', c._assinatura_palavra('criar'))