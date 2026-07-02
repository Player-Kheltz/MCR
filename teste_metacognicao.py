#!/usr/bin/env python3
"""Teste da metacognicao: confianca pela distribuicao das notas."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MCR_AGI import *

print("=== TESTE METACOGNICAO ===")
print()

c = CerebroAGI()
c.alimentar("O modelo de 8572MB e o maior com 579 tensores.", "modelo_grande")
c.alimentar("O modelo de 262MB e o menor para embeddings.", "modelo_pequeno")
c.alimentar("worm custa 1 moedas vendido por Ahmet", "item_worm")
c.alimentar("sword custa 85 moedas vendido por Baltim", "item_sword")

MCRExpansor.registrar("modelos", lambda p: [
    {"assinatura": d.get("texto",""), "meta": {"topico": n}}
    for n, d in list(c.topicos.items())
])

print("1. Teste: confianca alta (deve responder)")
print("-" * 40)
for p in ["worm", "qual o maior modelo", "sword"]:
    r = MCRExpansor.responder(p, cerebro=c)
    safe = r.encode("ascii", errors="replace").decode("ascii")[:150]
    print(f"  '{p}' -> {safe}")
print()

print("2. Teste: confianca baixa (deve re-alimentar)")
print("-" * 40)
for p in ["que horas sao", "que dia e hoje", "explique o MCR"]:
    r = MCRExpansor.responder(p, cerebro=c)
    safe = r.encode("ascii", errors="replace").decode("ascii")[:150]
    print(f"  '{p}' -> {safe}")
print()

print("3. Teste: confianca do MCRExpansor._confianca")
print("-" * 40)
cenarios = [
    ([0.91, 0.42, 0.38, 0.35], "sabe a resposta"),
    ([0.15, 0.14, 0.13, 0.12], "nao sabe"),
    ([0.80, 0.30, 0.28, 0.25], "sabe parcialmente"),
    ([0.50, 0.49, 0.48, 0.47], "todas ruins igualmente"),
]
for notas, desc in cenarios:
    resultados = [{"nota": n} for n in notas]
    conf, confiante = MCRExpansor._confianca(resultados)
    print(f"  {desc}: {conf:.4f} -> confiante={confiante}")

print()
print("=== TESTE CONCLUIDO ===")
