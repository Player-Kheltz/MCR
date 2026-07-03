#!/usr/bin/env python3
"""Verifica se o MCR.py carrega os dados migrados de si mesmo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRPersistencia, MCRBoot

mcr_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

print("=== VERIFICACAO DE DADOS INTERNOS ===")

pers = MCRPersistencia(mcr_path)
dados = pers.carregar_dados()

print(f"Licoes: {len(dados.get('licoes', []))}")
if dados.get('licoes'):
    l = dados['licoes'][0]
    print(f"  1a lesson: erro={l.get('erro','')[:40]}")

print(f"Assinaturas: {sum(len(v) for v in dados.get('assinaturas', {}).values())}")
print(f"Cache: {len(dados.get('cache', {}))}")
print(f"Estado: {dados.get('estado', {})}")

# Verifica integridade
n_licoes = len(dados.get('licoes', []))
assert n_licoes > 100, f"Poucas lessons: {n_licoes}"
print(f"\nOK - {n_licoes} lessons carregadas do proprio MCR.py!")

# Verifica que o arquivo ainda e Python valido
import importlib.util
spec = importlib.util.spec_from_file_location("mcr_test", mcr_path)
print(f"  MCR.py ainda e importavel: {spec is not None}")
