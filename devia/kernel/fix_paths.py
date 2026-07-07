#!/usr/bin/env python3
"""FASE 0: Atualiza paths criticos antes da reorganizacao."""
import os

BASE = r'E:\MCR'

def fix_file(relpath, replacements, desc):
    fpath = os.path.join(BASE, relpath)
    if not os.path.exists(fpath):
        print('  SKIP: %s nao encontrado' % fpath)
        return
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print('  [%s] OK: %s' % (desc, old[:60]))
        else:
            print('  [%s] NOT FOUND: %s' % (desc, old[:60]))
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print('=== Atualizando paths ===')

# mcr_devia.py
fix_file('mcr_devia.py', [
    (r'PROJETO = r"E:\Projeto MCR"', r'PROJETO = os.path.dirname(os.path.abspath(__file__))'),
    (r'DEVIA = os.path.join(PROJETO, "historia", "scripts", "mcr_devia")', r'DEVIA = os.path.join(PROJETO, "devia")'),
], 'mcr_devia')

# PipelineExecutor.py
fix_file('PipelineExecutor.py', [
    (r'projeto_base = r"E:\Projeto MCR"', r'projeto_base = os.path.dirname(os.path.abspath(__file__))'),
], 'PipelineExecutor')

# log_watcher.py
fix_file('log_watcher.py', [
    (r'r"E:\Projeto MCR\Canary"', r'os.path.join(os.path.dirname(os.path.abspath(__file__)), "server")'),
    (r'r"E:\Projeto MCR\Canary\log"', r'os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "log")'),
], 'log_watcher')

# alimentar_indexador.py
fix_file('alimentar_indexador.py', [
    (r"sys.path.insert(0, r'E:\Projeto MCR\historia\Scripts\mcr_devia\knowledge')", r"sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devia', 'knowledge'))"),
    (r'PROJETO = r"E:\Projeto MCR"', r'PROJETO = os.path.dirname(os.path.abspath(__file__))'),
], 'alimentar_indexador')

# alimentar_mcr.py
fix_file('alimentar_mcr.py', [
    (r"docs_dir = r'E:\Projeto MCR'", r"docs_dir = os.path.dirname(os.path.abspath(__file__))"),
], 'alimentar_mcr')

# ingest_canary.py
fix_file('ingest_canary.py', [
    (r'CANARY_BASE = r"E:\Projeto MCR\Canary"', r'CANARY_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server")'),
    (r'LORE_BASE = r"E:\Projeto MCR\lore_base"', r'LORE_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "lore")'),
], 'ingest_canary')

# MCR.py (embedded data string, skip if not found)
fix_file('MCR.py', [
    (r'E:/Projeto MCR/', r'E:/MCR/'),
], 'MCR.py')

print('\nPaths atualizados!')
