#!/usr/bin/env python3
"""Limpa e recria o banner de ativacao corretamente."""
import re

path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove everything from '# ATIVACAO' to just before '# Processa --json'
pattern = r"# ATIVACAO: Mensagem para o Cloud.*?(?=# Processa --json)"
content = re.sub(pattern, "# Processa --json", content, flags=re.DOTALL)

# Remove orphaned 'except: _ctx_ultimo = ""'
content = content.replace('    except: _ctx_ultimo = ""\n', '')

# Add simple context for cloud
old = "# Processa --json antes de tudo\n    if main_json():"
new = """    # Contexto rapido para Cloud (suprimido se --chat)
    if '--chat' not in sys.argv:
        print('[Cloud] LEMBRE-SE: MCR-DevIA e parte da equipe')
    
    # Processa --json antes de tudo
    if main_json():"""

content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
    # Show context around error
    import traceback
    traceback.print_exc()
