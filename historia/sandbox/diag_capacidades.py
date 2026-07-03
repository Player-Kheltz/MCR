#!/usr/bin/env python3
"""Diagnostico real das capacidades do MCR."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('=== 1. CACHE ===')
from modulos.MCR import MCRDocIndex
idx = MCRDocIndex()
print(f'MCRDocIndex: existe')
print(f'Cache salvo em: sandbox/.mcr_docs_index.json')
print(f'Cache existe: {os.path.exists("sandbox/.mcr_docs_index.json")}')

print()
print('=== 2. KNOWLEDGE GRAPH ===')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
print(f'KnowledgeGraph: {len(licoes)} lessons')
print(f'Salvo em: sandbox/.mcr_devia/kg/')
kg_files = [f for f in os.listdir("sandbox/.mcr_devia/kg/") if f.endswith(".json")]
print(f'  {len(kg_files)} arquivos JSON')

print()
print('=== 3. HISTORICO / MEMORIA ===')
from modulos.episodic_memory import EpisodicMemory
mem = EpisodicMemory()
print(f'EpisodicMemory: existe')
print(f'Salvo em: sandbox/.mcr_episodios.json')
ep_path = "sandbox/.mcr_episodios.json"
print(f'Cache existe: {os.path.exists(ep_path)}')
if os.path.exists(ep_path):
    sz = os.path.getsize(ep_path)
    print(f'Tamanho: {sz/1024:.0f} KB')

print()
print('=== 4. CONVERSAS ===')
conv_path = "sandbox/.mcr_conversa.jsonl"
print(f'Salvo em: {conv_path}')
print(f'Existe: {os.path.exists(conv_path)}')
if os.path.exists(conv_path):
    with open(conv_path, 'r', encoding='utf-8') as f:
        n = sum(1 for _ in f)
    print(f'  {n} mensagens')

print()
print('=== 5. O QUE ESTA DENTRO DO MCR.py ===')
print('Cache:       SIM (MCRDocIndex em sandbox/.mcr_docs_index.json)')
print('KG:          SIM (KnowledgeGraph em sandbox/.mcr_devia/kg/)')
print('Historico:   NAO (EpisodicMemory em modulos/episodic_memory.py)')
print('Conversas:   NAO (.mcr_conversa.jsonl via comando)')
print('Checkpoint:  NAO (indice_watchdog.json via watchdog)')
print('Web estudar: PARCIAL (cmd_weblearn externo)')
print('Persistencia: SIM (KG + DocIndex em sandbox/)')
print('Auto-retomada: NAO (MCR nao salva estado)')
print('Identificar usuario: PARCIAL (assinatura existe, autoria nao)')

print()
print('=== 6. O QUE FALTA DENTRO DO MCR.py ===')
print('1. EpisodicMemory (347 linhas) — historico de experiencias')
print('2. SessionCache (257 linhas) — checkpoint de sessao')
print('3. Conversas (.jsonl) — historico de conversas')
print('4. Auto-retomada — salvar/carregar estado de execucao')
print('5. Identificacao de usuario — banco de assinaturas')
print('6. Estudo web autonomo — weblearn integrado')
