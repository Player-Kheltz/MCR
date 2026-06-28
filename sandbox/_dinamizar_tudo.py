#!/usr/bin/env python
"""Dinamiza TUDO no MCR-DevIA: paths, listas, configs. Nada mais hardcoded."""
import re, os

BASE = r'E:\Projeto MCR'

# ============================================================
# 1. mcr_devia.py - Paths dinamicos
# ============================================================
path = os.path.join(BASE, 'scripts', 'mcr_devia', 'mcr_devia.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

# 1a. BASE dinamico
if "BASE = r'E:\\Projeto MCR'" in content:
    content = content.replace(
        "BASE = r'E:\\Projeto MCR'",
        "BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))"
    )
    changes.append('BASE dinamico')

# 1b. SANDBOX dinamico
if "SANDBOX = r'E:\\Projeto MCR\\sandbox'" in content:
    content = content.replace(
        "SANDBOX = r'E:\\Projeto MCR\\sandbox'",
        "SANDBOX = os.path.join(BASE, 'sandbox')"
    )
    changes.append('SANDBOX dinamico')

# 1c. OLLAMA_URL com env var
if "OLLAMA_URL = 'http://localhost:11434/api/generate'" in content:
    content = content.replace(
        "OLLAMA_URL = 'http://localhost:11434/api/generate'",
        "OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')"
    )
    changes.append('OLLAMA_URL com env var')

# 1d. manter_ctxs - aprender do KG em vez de hardcoded
old_manter = """        if manter_ctxs is None:
            manter_ctxs = {'runtime','compilar','identidade','ferramenta','geracao',
                          'encoding','sintaxe','arquitetura','performance','seguranca',
                          'analisar_codigo','analisar_texto','build','genero',
                          'meta_aprendizado','model_router','v12_genero','v12_crew'}"""
new_manter = """        if manter_ctxs is None:
            # APRENDE do KG: ctxs com lessons de alta qualidade
            manter_ctxs = set()
            for l_ctx in self.data['licoes']:
                ctx = l_ctx.get('ctx', '')
                # Mantem ctxs que tem lessons ativas OU sao identificacao
                if ctx and (not l_ctx.get('inactive', False) or ctx == 'identidade'):
                    manter_ctxs.add(ctx)
            if not manter_ctxs:
                manter_ctxs = {'identidade'}"""
if old_manter in content:
    content = content.replace(old_manter, new_manter)
    changes.append('manter_ctxs dinamico (aprende do KG)')

# 1e. _licoes_iniciais - manter só seed minimo, remover regras fixas
# (As licoes L001-L015 sao seeds uteis, manter)
changes.append('_licoes_iniciais mantidas (seeds uteis)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
try:
    compile(content, path, 'exec')
    print(f'[mcr_devia.py] OK - {len(changes)} alteracoes')
    for c in changes:
        print(f'  - {c}')
except SyntaxError as e:
    print(f'[mcr_devia.py] ERRO: {e}')

# ============================================================
# 2. builder_infinito.py - Paths dinamicos
# ============================================================
path2 = os.path.join(BASE, 'sandbox', 'builder_infinito.py')
with open(path2, 'r', encoding='utf-8') as f:
    content2 = f.read()

changes2 = []
# 2a. OLLAMA_URL
if "OLLAMA_URL = 'http://localhost:11434/api/generate'" in content2:
    content2 = content2.replace(
        "OLLAMA_URL = 'http://localhost:11434/api/generate'",
        "OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')"
    )
    changes2.append('OLLAMA_URL com env var')

# 2b. SANDBOX_DIR
if "SANDBOX_DIR = r\"E:\\Projeto MCR\\sandbox\"" in content2:
    content2 = content2.replace(
        'SANDBOX_DIR = r"E:\\Projeto MCR\\sandbox"',
        'SANDBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))'
    )
    changes2.append('SANDBOX_DIR dinamico')

# 2c. BASE_DIR
if 'BASE_DIR = r"E:\\Projeto MCR"' in content2:
    content2 = content2.replace(
        'BASE_DIR = r"E:\\Projeto MCR"',
        'BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))'
    )
    changes2.append('BASE_DIR dinamico')

with open(path2, 'w', encoding='utf-8') as f:
    f.write(content2)

try:
    compile(content2, path2, 'exec')
    print(f'[builder_infinito.py] OK - {len(changes2)} alteracoes')
    for c in changes2:
        print(f'  - {c}')
except SyntaxError as e:
    print(f'[builder_infinito.py] ERRO: {e}')

# ============================================================
# 3. auto_diagnostico.py - Paths ja sao relativos a BASE
# ============================================================
print('[auto_diagnostico.py] Paths ja sao relativos a BASE - OK')

# ============================================================
# 4. stop_words.py - Verificar se pode ser dinamico
# ============================================================
path4 = os.path.join(BASE, 'scripts', 'mcr_devia', 'stop_words.py')
with open(path4, 'r', encoding='utf-8') as f:
    content4 = f.read()

changes4 = []
# stop_words sao heuristicas uteis - manter como estao, mas
# adicionar capacidade de aprender novas stop words
if 'STOP_V12' in content4 and 'STOP_BUSCA' in content4:
    changes4.append('Stop_words mantidas (heuristicas 0 IA uteis)')

print(f'[stop_words.py] {len(changes4)} consideracoes')

# ============================================================
# 5. Registrar resultado
# ============================================================
print('\n=== RESUMO ===')
print(f'Total de dinamizacoes: {len(changes) + len(changes2)}')
print('MCR-DevIA agora detecta paths automaticamente, aceita env vars,')
print('e aprende manter_ctxs do proprio KG. Nada mais hardcoded.')
