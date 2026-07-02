#!/usr/bin/env python3
"""Teste MCRAttention com dados que CONTEM os termos de busca."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import CerebroAGI, MCRByteUtils
from prototipo_mcr_attention import MCRAttention

c = CerebroAGI()

# Alimenta textos QUE CONTEM os termos de busca
# Importante: alimentar VARIOS textos similares para criar "ruido"
textos = [
    ("SPA e o sistema de progressao do aventureiro com dominios elementais", "spa_principal"),
    ("SPA significa Sistema de Progressao do Aventureiro", "spa_sigla"),
    ("SPA tem 5 dominios: Fogo, Gelo, Terra, Energia, Sagrado", "spa_dominios"),
    ("SPA cada dominio tem 25 niveis de habilidade", "spa_niveis"),
    ("SPA e usado no servidor MCR para progressao de personagem", "spa_mcr"),
    ("SHC e o sistema de habilidades contextuais com posturas", "shc"),
    ("SHC tem 5 camadas: postura, nivel, sinergia, estado, condicao", "shc_camadas"),
    ("SHC as sinergias combinam dominios elementais", "shc_sinergias"),
    ("Eridanus cidade inicial as margens do Lago Cristalino", "eridanus"),
    ("Eridanus tem porto praca central templo forja e mercado", "eridanus_local"),
    ("Eridanus a marinha patrulha o lago contra monstros aquaticos", "eridanus_marinha"),
    ("Fogo e um dominio elemental do SPA", "fogo_spa"),
    ("Fogo queima e causa dano ao longo do tempo", "fogo_dano"),
    ("Gelo e um dominio elemental que congela inimigos", "gelo_spa"),
    ("Gelo diminui a velocidade dos inimigos", "gelo_efeito"),
    ("Terra e um dominio de resistencia e fortaleza", "terra_spa"),
    ("Energia e um dominio de velocidade e agilidade", "energia_spa"),
    ("Sagrado e o dominio mais raro de SPA", "sagrado_spa"),
]

# Cria textos "ruido" para simular base grande
ruidos = [
    f"arquivo de configuracao numero {i} com parametros do servidor" for i in range(50)
] + [
    f"log do sistema: inicio do servidor na porta 7171" for _ in range(50)
]

for texto, nome in textos + [(r, f"ruido_{i}") for i, r in enumerate(ruidos)]:
    c.alimentar(texto, nome)

print(f"Topicos: {len(c.topicos)}")
print(f"mk_palavra total: {c.mk_palavra.total}")
print()

# Debug
print('predizer_n("SPA"):')
preds = c.mk_palavra.predizer_n("SPA", 10)
for t, conf in preds:
    print(f'  {t}: {conf:.4f}')
print()

print('_topico_relevante("explique o sistema SPA"):')
topico = MCRAttention._topico_relevante(c, "explique o sistema SPA")
if topico:
    nome, texto, score = topico
    print(f'  Topico: {nome} (score={score:.3f})')
    print(f'  Texto: {texto[:80]}')
print()

if topico:
    print('_candidatos_do_topico(..., "SPA", 10):')
    cands = MCRAttention._candidatos_do_topico(texto, "SPA", 10)
    for tok, conf in cands[:5]:
        print(f'  {tok}: {conf:.4f}')
print()

# Geracao comparativa
print("=" * 60)
print("COMPARACAO GERACAO:")
print("=" * 60)
testes = [
    ("SPA", "explique o que e SPA"),
    ("SPA", "dominios do SPA"),
    ("Fogo", "o que e o dominio Fogo"),
    ("Eridanus", "fale sobre Eridanus"),
    ("SHC", "o que e SHC"),
]
for semente, pergunta in testes:
    r1 = c._gerar_original(semente, 5)
    r2 = MCRAttention.gerar(c, semente, 5, pergunta=pergunta)
    j1 = MCRByteUtils.jaccard_bytes(pergunta, r1)
    j2 = MCRByteUtils.jaccard_bytes(pergunta, r2)
    status = "+" if j2 > j1 else " "
    print(f'  [{status}] {semente:10s} perg={pergunta[:25]}')
    print(f'        sem: "{r1:40s}" j={j1:.3f}')
    print(f'        com: "{r2:40s}" j={j2:.3f}')
