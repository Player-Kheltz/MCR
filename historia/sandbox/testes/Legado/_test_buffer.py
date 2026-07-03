#!/usr/bin/env python3
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.lessons_buffer import LessonsBuffer

class FakeKG:
    def __init__(self):
        self.lessons = []
    def aprender(self, erro, causa, solucao, ctx):
        self.lessons.append({'erro': erro, 'ctx': ctx, 'solucao': solucao})

kg = FakeKG()
buf = LessonsBuffer(kg)

buf.adicionar('_WIN32', 'Arquivo: win.cpp', 'Macro para Windows', 'conhecimento', 'codigo')
buf.adicionar('_WIN32', 'Arquivo: win2.cpp', 'Macro para Windows', 'conhecimento', 'codigo')
buf.adicionar('_WIN32', 'Arquivo: win3.cpp', 'Define para Windows', 'conhecimento', 'codigo')
buf.adicionar('Logger', 'Arquivo: log.hpp', 'Classe para log', 'conhecimento', 'codigo')
buf.adicionar('Logger', 'Arquivo: log2.hpp', 'Funcao para log', 'conhecimento', 'codigo')

print('Buffer:', json.dumps(buf.estatisticas(), indent=2))

contradicoes = buf.verificar_contradicoes()
print(f'Contradicoes: {len(contradicoes)}')
for l1, l2 in contradicoes:
    print(f'  "{l1["erro"]}": "{l1["solucao"][:30]}" vs "{l2["solucao"][:30]}"')

comitadas = buf.comitar()
print(f'Comitadas: {comitadas}')
print(f'Buffer restante: {buf.estatisticas()["total"]}')
print(f'KG lessons: {len(kg.lessons)}')
print(f'KG: {json.dumps(kg.lessons, indent=2)}')
