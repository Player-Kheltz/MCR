#!/usr/bin/env python3
"""Executa MCR-DevIA para o Teste Cego do context_crew.py"""
import os, sys
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

from mcr_devia import KnowledgeGraph
from modulos.ia import IA
from modulos.orquestrador import Orquestrador
from modulos.supervisor import Supervisor
import context_crew as cc

import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        kg = KnowledgeGraph()
        ia = IA()
        ctx = cc.ContextCrew()
    finally:
        sys.stdout = old

orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx)

identidade = ""
try:
    with open(r"E:\Projeto MCR\docs\MCR_IDENTITY.md", "r", encoding="utf-8") as f:
        identidade = f.read()[:500].strip()
except:
    pass

sup = Supervisor(ia, kg, ctx_crew=ctx, orquestrador=orq, identidade=identidade)

prompt = "Analise o arquivo context_crew.py. Encontre TODOS os problemas de seguranca, performance e manutencao. Depois crie uma MELHORIA: um novo metodo de busca chamado buscar_priorizando_kg que priorize resultados do Knowledge Graph sobre resultados da Web. Escreva o codigo COMPLETO do metodo."

print("Executando MCR...")
resposta = sup.perguntar(prompt)

path = r"E:\Projeto MCR\sandbox\teste_cego_mega\respostas_mcr\cego_1.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write(resposta or "")
tam = len(resposta or "")
print(f"MCR: {tam} chars salvos")
