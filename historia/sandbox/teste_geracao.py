#!/usr/bin/env python3
"""Teste de geracao de texto com Top-K sampling + filtro lore."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRPergunta, MCRCadeia

print("=" * 60)
print("TESTE 1: Top-K sampling (antes era greedy, ciclava)")
print("=" * 60)

# Cria cadeia com dados de teste
from modulos.MCR import MCRConector
conector = MCRConector()

# Alimenta com texto narrativo real
textos_teste = [
    "O aventureiro parte em uma jornada pelo reino de Eridanus em busca de conhecimento ancestral",
    "As terras de Eridanus guardam segredos antigos que poucos ousam explorar em sua totalidade",
    "O sistema de progressao SPA permite que cada aventureiro desenvolva suas habilidades elementais",
    "O fogo e o gelo sao forcas opostas mas complementares na jornada do heroi",
    "O templo ancestral esconde runas de poder que concedem sabedoria aos dignos",
    "A floresta sombria guarda criaturas magicas e desafios para os corajosos",
    "Os dominios elementais sao areas de conhecimento que o aventureiro deve dominar",
]

for i, txt in enumerate(textos_teste[:4]):
    conector.alimentar(txt, f"teste_{i}")

cadeia = MCRCadeia(conector)

# 3 geracoes com top_k=3 (diversidade)
print("\nGeracoes com top_k=3:")
for j in range(3):
    r = cadeia.gerar('O', n_tokens=15, top_k=3)
    print(f"  [{j+1}] {r['texto']}  (nota={r['nota']}, loops={r['loops_detectados']})")

# 3 geracoes com top_k=1 (greedy, igual ao original)
print("\nGeracoes com top_k=1 (greedy):")
for j in range(3):
    r = cadeia.gerar('O', n_tokens=15, top_k=1)
    print(f"  [{j+1}] {r['texto']}  (nota={r['nota']}, loops={r['loops_detectados']})")

print()
print("=" * 60)
print("TESTE 2: Filtro lore no MCRPergunta")
print("=" * 60)

# Testa o filtro lore
from modulos.MCR import MCRPergunta

lessons_teste = [
    {'solucao': 'Para compilar o servidor, execute cmake e make no diretorio build', 'ctx': 'compilacao'},
    {'solucao': 'O aventureiro explora a floresta encantada em busca do artefato lendario', 'ctx': 'lore'},
    {'solucao': 'A cidade de Eridanus e o ponto de partida de todos os aventureiros', 'ctx': 'lore'},
    {'solucao': 'Para configurar o banco de dados, edite o arquivo config.lua', 'ctx': 'config'},
]

filtradas = MCRPergunta._preferir_lore(lessons_teste)
print("\nRankeamento por lore:")
for i, l in enumerate(filtradas):
    sol = l.get('solucao', '')
    print(f"  #{i+1}: {sol[:60]}...")

print("\nOK - Testes concluidos")
