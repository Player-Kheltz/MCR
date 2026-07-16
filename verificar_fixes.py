"""Verifica se os fixes do Conselho estao funcionando."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from mcr.conselho_multi import Conselho, _carregar_contexto, _ROUTER, _PESO_PARA_MODELO

print("=== ROUTER COMPLETO ===")
for k, v in sorted(_ROUTER.items()):
    modelo = _PESO_PARA_MODELO.get(v, "?")
    print(f"  {k:<20} -> {v:<10} -> {modelo}")

print("\n=== CONTEXTO DINAMICO ===")
ctx = _carregar_contexto()
print(ctx[:600])
print("..." if len(ctx) > 600 else "")

print("\n=== CLASSIFICACAO ===")
c = Conselho()
tests = [
    "crie um NPC ferreiro para tibia",
    "revise este codigo python para performance",
    "explique como funciona Markov Chain",
    "implementar sistema de spells em lua",
]
for t in tests:
    cls = c._classificar(t)
    print(f'  "{t}" -> {cls}')

print("\n=== TESTE RAPIDO CONSELHO ===")
r = c.deliberar("Qual a diferenca entre SQLite e MySQL para jogos?")
print(f"Tipo: {r.get('tipo')}")
print(f"Arquetipos: {r.get('honorarios_criados', [])}")
print(f"Veredito: {r.get('veredito','')[:300]}")
print(f"Nota: {r.get('nomes_proprios', 0)} nomes proprios")
print(f"Tempo: {r.get('tempo_total', '?')}s")
