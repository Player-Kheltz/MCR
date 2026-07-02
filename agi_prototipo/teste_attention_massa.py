#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste MCRAttention com CARGA MASSA do decathlon (2717 topicos)."""
import sys, os, json, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import CerebroAGI, MCRByteUtils
from prototipo_mcr_attention import MCRAttention

print("Carregando cerebro com conhecimento massivo...")
c = CerebroAGI()

# Carrega arquivos do decathlon para ter base grande
base = r"E:\Projeto MCR"
if not os.path.exists(base):
    base = os.path.dirname(os.path.dirname(__file__))

n = 0
for ext in ["py", "md", "txt", "lua"]:
    for f in sorted(glob.glob(os.path.join(base, f"**/*.{ext}"), recursive=True))[:200]:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fp:
                txt = fp.read(1000)
            if len(txt) > 50:
                c.alimentar(txt[:500], os.path.basename(f)[:20])
                n += 1
        except:
            pass

print(f"Carregados {n} arquivos, {len(c.topicos)} topicos, {c.mk_byte.total} bytes, {c.mk_palavra.total} palavras")
print()

# Teste: geracao SEM atencao vs COM atencao
print("=" * 60)
print("COMPARACAO DIRETA: Markov puro vs MCRAttention")
print("=" * 60)

testes = [
    ("SPA", "explique o sistema SPA"),
    ("Eridanus", "fale sobre a cidade de Eridanus"),
    ("Fogo", "dominio de Fogo no SPA"),
    ("NPC", "criar um NPC ferreiro"),
    ("Monstro", "criar um monstro"),
    ("Fibonacci", "sequencia de Fibonacci"),
    ("SHC", "sistema SHC de habilidades"),
    ("MCR", "o que e o projeto MCR"),
    ("habilidade", "habilidades do jogador"),
    ("cidade", "cidades do servidor"),
]

resultados = []
for semente, pergunta in testes:
    r1 = c._gerar_original(semente, 4)
    r2 = MCRAttention.gerar(c, semente, 4, pergunta=pergunta)
    j1 = MCRByteUtils.jaccard_bytes(pergunta, r1)
    j2 = MCRByteUtils.jaccard_bytes(pergunta, r2)
    resultados.append((semente, r1[:35], j1, r2[:35], j2, j2 > j1))

for s, r1, j1, r2, j2, melhor in resultados:
    marc = "+" if melhor else " "
    print(f"  [{marc}] {s:15s}")
    print(f"        sem: \"{r1:35s}\" j={j1:.3f}")
    print(f"        com: \"{r2:35s}\" j={j2:.3f}")

melhoraram = sum(1 for _, _, _, _, _, m in resultados if m)
print(f"\nMelhoraram: {melhoraram}/{len(testes)}")
print()

# Teste de evolucao de pesos
print("=" * 60)
print("EVOLUCAO DE PESOS (5 geracoes)")
print("=" * 60)
t0 = time.time()
ev = MCRAttention.evoluir_pesos(c, geracoes=5)
print(f"  Fitness: {ev['fitness_final']}")
print(f"  Pesos:   {ev['pesos_finais']}")
print(f"  Tempo:   {time.time()-t0:.2f}s")
print()

# Teste final apos evolucao
print("=" * 60)
print("TESTE FINAL APOS EVOLUCAO")
print("=" * 60)
for semente, pergunta in testes[:3]:
    r = MCRAttention.gerar(c, semente, 5, pergunta=pergunta)
    j = MCRByteUtils.jaccard_bytes(pergunta, r)
    print(f"  {semente:15s}: \"{r:45s}\" j={j:.3f}")

print()
print("TESTE CONCLUIDO")
