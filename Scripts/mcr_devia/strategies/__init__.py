# EXPERIMENTAL — Use agent_loop como pipeline principal.
# Estrategias foram construidas como sistema paralelo de
# preenchimento de lacunas. A correcao de ~30 linhas em
# agent_loop.py + npc_generator.py (passar exemplos do
# Indexer para o Generator) resolve o problema de forma
# mais simples. Mantido como referencia arquitetural.
# Veja docs/PLANO_REFATORACAO.md.
"""Strategies — Estrategias de preenchimento de lacunas.

Ordem de qualidade:
  A: Indexer (NPCs reais)
  B: items.xml (itens catalogados)
  C: Web (weblearn + validacao)
  D: LLM (Ollama)
  E: Humano (pergunta ao usuario)
"""
