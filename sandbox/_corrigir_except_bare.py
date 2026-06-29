"""Corrige todos os except: bare para except Exception: em modulos.
Nao toca except Exception:, except (X,Y):, except ImportError: etc.
"""
import os, re

MODULOS_DIR = r'E:\Projeto MCR\Scripts\mcr_devia\modulos'
total = 0

# Arquivos com except: bare conhecidos
ARQUIVOS = [
    'agent_loop.py', 'auto_revisor.py', 'canary_indexer.py',
    'conselho.py', 'ia.py', 'lessons_buffer.py', 'lua_validator.py',
    'memoria_conselho.py', 'mente.py', 'pipeline_executor.py',
    'progress_tracker.py', 'self_study.py', 'sse_server.py',
    'task_executor.py', 'tree_of_thought.py', 'util.py', 'watchdog.py',
]

# Regex: encontra except: (bare) — mas NAO except Exception, except (, etc.
PADRAO = re.compile(r'^\s*except\s*:\s*$|^\s*except\s*:\s+(?!Exception|\()', re.MULTILINE)

for fname in ARQUIVOS:
    path = os.path.join(MODULOS_DIR, fname)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    novo, count = PADRAO.subn(lambda m: m.group(0).replace('except:', 'except Exception:', 1), conteudo)
    if count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(novo)
        print(f'  {fname}: {count} ocorrencias corrigidas')
        total += count

print(f'\nTotal: {total} except: bare convertidos para except Exception:')
