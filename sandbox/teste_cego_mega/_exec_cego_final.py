#!/usr/bin/env python3
"""Executa MCR-DevIA para o Teste Cego Final."""
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

prompt = open(r"E:\Projeto MCR\sandbox\teste_cego_mega\_pergunta_cego.txt", "r", encoding="utf-8").read()

print("Executando MCR-DevIA para Teste Cego Final...")
resposta = sup.perguntar(prompt)

path = r"E:\Projeto MCR\sandbox\teste_cego_mega\respostas_mcr\cego_final.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write(resposta or "")

tam = len(resposta or "")
print(f"MCR: {tam} chars salvos em cego_final.txt")
