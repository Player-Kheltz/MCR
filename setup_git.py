#!/usr/bin/env python3
"""Inicializa repo Git do MCR."""
import subprocess, os

os.chdir(r'E:\MCR')

def run(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ERRO: {r.stderr.strip()[:100]}')
    else:
        print(f'  OK: {r.stdout.strip()[:80]}')

print('1. git init...')
run('git', 'init')

print('2. git add...')
run('git', 'add', 'MCR_AGI.py', 'README.md', 'MCR_PLAN.md', 'check_git.py')

print('3. git commit...')
run('git', 'commit', '-m', 'MCR — 1 equation, N levels, 0 GPU')

print()
print('Agora crie o repositorio no GitHub:')
print('  1. github.com/new')
print('  2. Nome: MCR')
print('  3. Private')
print('  4. Nao adicionar README (ja temos)')
print('  5. Criar')
print()
print('Depois execute:')
print('  git remote add origin https://github.com/Player-Kheltz/MCR.git')
print('  git push -u origin main')
