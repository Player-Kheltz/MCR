#!/usr/bin/env python3
"""Remove banner de ativacao e adiciona --chat mode."""
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove everything between 'ATIVACAO' and 'KG com ~760' (inclusive)
import re
pattern = r"    # ============================================================\n    # ATIVACAO:.*?\n    except: pass\n"
content = re.sub(pattern, '', content, flags=re.DOTALL)

# Also remove the second '    except: pass' that might remain
content = content.replace('\n    except: pass\n', '\n')

# Add simple context for cloud
simple_banner = """    # Contexto para Cloud (suprimido se --chat)
    if '--chat' not in sys.argv:
        print(f'[Cloud] ** LEMBRE-SE: MCR-DevIA e parte da equipe **')
    else:
        pass  # No banner for chat mode

"""
content = content.replace(
    '    # Processa --json antes de tudo\n    if main_json():',
    simple_banner + '    # Processa --json antes de tudo\n    if main_json():'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
