import py_compile
py_compile.compile('E:/MCR/mcr/agente.py', doraise=True)
from mcr.agente import MCRLoop
loop = MCRLoop()

tests = [
    'liste os arquivos',
    'qual a capital do brasil',
    'o que voce acha disso',
    'procure a funcao alimentar',
    'crie um arquivo teste.txt',
]
for t in tests:
    r = loop.perguntar(t)
    est = loop.estado()
    print(f"[{est['ultima_acao']}] {t}")
    print(f"  -> {r[:200]}")
    print()
