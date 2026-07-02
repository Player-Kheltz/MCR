#!/usr/bin/env python3
"""Verifica configuracao Git e prepara repo MCR."""
import subprocess, os, sys

def cmd(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

# 1. Verificar git
user, _ = cmd('git', 'config', '--global', 'user.name')
email, _ = cmd('git', 'config', '--global', 'user.email')
print(f'Git user: {user or "nao configurado"}')
print(f'Git email: {email or "nao configurado"}')

# 2. Verificar token GitHub
token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if token:
    print(f'GitHub token: encontrado ({token[:8]}...)')
else:
    # Verificar arquivos de configuracao
    gh_config = os.path.expanduser('~/.config/gh/hosts.yml')
    if os.path.exists(gh_config):
        with open(gh_config) as f:
            print('gh config found:')
            for line in f:
                if 'oauth_token' in line or 'token' in line:
                    print(f'  {line.strip()[:30]}...')
                    break
    else:
        print('GitHub token: nao encontrado')
        print()
        print('Para criar o repositorio, voce precisa:')
        print('  1. Ir em github.com/settings/tokens')
        print('  2. Criar um token com escopo "repo"')
        print('  3. Exportar: set GH_TOKEN=seu_token')
        print()
        print('Ou instalar gh CLI:')
        print('  winget install GitHub.cli')
        print('  gh auth login')
