#!/usr/bin/env python3
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.lessons_buffer import LessonsBuffer

class FakeKG:
    def __init__(self):
        self.lessons = []
    def aprender(self, erro, causa, solucao, ctx):
        self.lessons.append({'erro': erro, 'ctx': ctx, 'solucao': solucao[:50]})

kg = FakeKG()
buf = LessonsBuffer(kg)

# Adiciona contradicoes
buf.adicionar('Logger', 'fonte A', 'Classe que registra eventos do servidor', 'conhecimento', 'codigo')
buf.adicionar('Logger', 'fonte B', 'Funcao matematica para calculo de logaritmo', 'conhecimento', 'codigo')
buf.adicionar('_WIN32', 'fonte C', 'Define para Windows', 'conhecimento', 'codigo')
buf.adicionar('_WIN32', 'fonte D', 'Classe para numeros 32 bits', 'conhecimento', 'codigo')

buf.verificar_contradicoes()
print('Contradicoes detectadas. Resolvendo...')
resolvidas = buf.resolver_contradicoes()
print(f'Resolvidas: {resolvidas}')

comitadas = buf.comitar()
print(f'Comitadas: {comitadas}')
print(f'KG:')
for l in kg.lessons:
    print(f'  {l["erro"]}: {l["solucao"]}')
