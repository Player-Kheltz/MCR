#!/usr/bin/env python3
"""Convoca o Conselho para debater o problema de alucinacao."""
import os, sys
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

from modulos.conselho import Conselho

# Silencia stdout
import contextlib
with open(os.devnull, 'w') as devnull:
    old_stdout = sys.stdout
    sys.stdout = devnull
    try:
        from mcr_devia import KnowledgeGraph, IA
        import context_crew as cc
        kg = KnowledgeGraph()
        ia = IA()
        ctx = cc.ContextCrew()
    finally:
        sys.stdout = old_stdout

c = Conselho(ia, kg, ctx_crew=ctx)

print("=" * 60)
print("  CONSELHO DELIBERANDO...")
print("=" * 60)

resultado = c.deliberar(
    "O MCR-DevIA esta usando uma lista branca de classes para anti-alucinacao, "
    "mas ela captura excecoes reais como FileNotFoundError e causa 322s de retry. "
    "Precisamos de uma solucao melhor. O que cada membro recomenda? "
    "Seja CRITICO e especifico. APONTE FALHAS na lista branca."
)

print("\n" + "=" * 60)
print("  VEREDITO DO CONSELHO:")
print("=" * 60)
print(resultado.get('veredito', 'Sem veredito')[:3000])
