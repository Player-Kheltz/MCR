import sys; sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR
m = MCR()
tests = [
    ('Crie um NPC ferreiro anão que vende armaduras', True),
    ('Gere um monstro dragão ancião', True),
    ('Explique entropia', True),
    ('Crie um sprite de escudo', False),
    ('', False),
]
for entrada, esperado in tests:
    r = m.processar(entrada)
    ok = r['sucesso'] == esperado
    print(f'{"OK" if ok else "ERR"} | nota={r["nota"]:.4f} | {r["acao"]:15s} | {entrada[:50]}')
