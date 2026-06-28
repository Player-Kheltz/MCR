#!/usr/bin/env python
"""Cria mais comandos modulares para o kernel."""
import os

COMANDOS_DIR = r'E:\Projeto MCR\scripts\mcr_devia\comandos'
BASE = r'E:\Projeto MCR'
SANDBOX = os.path.join(BASE, 'sandbox')

# Template para comandos que precisam do mcr_devia.py como fallback
TEMPLATE_SUBPROCESS = '''"""Comando: {name} - Delega para mcr_devia.py (elif chain)."""
import sys, os

_DEVIA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mcr_devia.py')

def register():
    return {{
        "name": "{name}",
        "desc": "{desc}",
        "handler": execute,
        "args": [],
        "categoria": "delegado",
    }}

def execute(kg, ia, args, ctx_crew=None):
    """Executa via subprocess (sem risco de loop: kernel nao esta no caminho)."""
    import subprocess
    cmd = [sys.executable, _DEVIA, "{name}"] + args
    subprocess.run(cmd)
    return True
'''

# Comandos para criar como subprocess delegates (seguros, sem loop pois kernel é separado)
comandos_subprocess = [
    ("edit", "Edita arquivo por linha. Uso: edit <path> <linha> <novo>"),
    ("patch", "Edita arquivo com IA (substitui funcao)"),
    ("analisar", "Analisa codigo com IA (AST + linha numerada)"),
    ("extract", "Extrai dados de XML, JSON, CSV, Lua, C++"),
    ("review", "Revisa registros em lote"),
    ("gerar", "Gera NPC, monster, quest, item, spell"),
    ("lore", "Gera lore de RPG"),
    ("compilar", "Compila Canary (VS2022) ou OTClient (VS2026)"),
    ("system", "Info de CPU, RAM, GPU"),
    ("bugfinder", "Escaneia logs por bugs"),
    ("plan", "Planejamento multi-abordagem"),
    ("debate", "2 sub-agentes discutem"),
    ("loop", "Loop OODA continuo"),
    ("intencao", "Interpreta intencao do usuario"),
    ("task", "Task runner"),
    ("question", "Pergunta ao usuario"),
    ("conectar", "Conexoes entre dominios no KG"),
    ("estrategia", "Estrategista"),
    ("builderx", "Builder por blocos"),
    ("system_scan", "Escaneia linguagens"),
    ("webfetch", "Baixa pagina web"),
    ("proativo", "Modo proativo"),
    ("revisar", "Revisao com criterio"),
    ("processar", "Processa entrada (fragmenta + IA + monta)"),
    ("glob", "Busca arquivos por nome (auto-adiciona *)"),
    ("todo", "Task list manager"),
]

criados = 0
pulados = 0

for name, desc in comandos_subprocess:
    fpath = os.path.join(COMANDOS_DIR, f'cmd_{name}.py')
    if os.path.exists(fpath):
        pulados += 1
        continue
    
    codigo = TEMPLATE_SUBPROCESS.format(name=name, desc=desc)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(codigo)
    criados += 1
    print(f'  CRIADO cmd_{name}.py')

print(f'\nResumo: {criados} criados, {pulados} ja existiam')
print(f'Total em comandos/: {len([f for f in os.listdir(COMANDOS_DIR) if f.endswith(".py")])} arquivos')
