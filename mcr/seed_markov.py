#!/usr/bin/env python3
"""seed_markov.py — Seed inicial para o MarkovDecider.

Fornece exemplos basicos para que o roteador funcione desde o inicio.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devia', 'kernel'))

from mcr_devia_v2 import MarkovDecider

SEEDS = [
    # explicar_conceito
    ("explique o que e spa", "explicar_conceito"),
    ("o que significa mcr", "explicar_conceito"),
    ("como funciona o sistema de progressao", "explicar_conceito"),
    ("o que e o motor cognitivo", "explicar_conceito"),
    ("me explique a entropia de shannon", "explicar_conceito"),
    ("o que e cadeia de markov", "explicar_conceito"),
    ("como funciona o knowledge graph", "explicar_conceito"),
    ("explique o conceito de jaccard", "explicar_conceito"),
    ("o que sao estados compostos", "explicar_conceito"),
    ("como funciona a bridge api", "explicar_conceito"),

    # criar_npc
    ("crie um npc ferreiro", "criar_npc"),
    ("gere um npc mestre de magias", "criar_npc"),
    ("criar npc vendedor de pocoes", "criar_npc"),
    ("preciso de um npc guarda para cidade", "criar_npc"),
    ("criar npc barkeep em eridanus", "criar_npc"),

    # criar_codigo
    ("crie um script lua para quest", "criar_codigo"),
    ("gere codigo para um sistema de missao", "criar_codigo"),
    ("criar funcao lua de teleporte", "criar_codigo"),
    ("implemente um sistema de loot", "criar_codigo"),

    # criar_quest
    ("crie uma quest de coleta", "criar_quest"),
    ("gere uma missao de entrega", "criar_quest"),
    ("criar quest de kill monstros", "criar_quest"),

    # busca_informacao
    ("como configurar o canary server", "busca_informacao"),
    ("onde fica o arquivo de configuracao", "busca_informacao"),
    ("qual a porta padrao do servidor", "busca_informacao"),

    # criar_sql
    ("crie uma tabela de usuarios", "criar_sql"),
    ("gere uma query sql para selecionar dados", "criar_sql"),
    ("criar tabela de produtos no banco", "criar_sql"),
    ("preciso de um select com join", "criar_sql"),
    ("criar banco de dados para ecommerce", "criar_sql"),
    ("gere insert into para a tabela pedidos", "criar_sql"),
    ("crie uma query sql para relatorio", "criar_sql"),
    ("preciso criar uma tabela de log de eventos", "criar_sql"),

    # conversa
    ("ola tudo bem", "conversa"),
    ("bom dia", "conversa"),
    ("quem e voce", "conversa"),
    ("como voce funciona", "conversa"),
]

md = MarkovDecider()
count = 0
for pergunta, classe in SEEDS:
    md.aprender(pergunta, classe)
    count += 1

md._salvar()
print(f"[Seed] MarkovDecider treinado com {count} exemplos")
print(f"[Seed] Classes: {set(c for _, c in SEEDS)}")
