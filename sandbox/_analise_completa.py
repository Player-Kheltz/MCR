#!/usr/bin/env python
"""Analise completa do MCR-DevIA: comandos, capacidades, limites."""
import re, os

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print('='*60)
print('ANALISE COMPLETA DO MCR-DEVIA')
print('='*60)

# 1. Tamanho
print(f'\n## TAMANHO')
print(f'Linhas: {len(lines)}')
print(f'Caracteres: {len(content)}')

# 2. Comandos
print(f'\n## COMANDOS DIRETOS (elif cmd)')
cmds = []
for line in lines:
    m = re.search(r"elif cmd == '(\w+)'", line)
    if m:
        cmds.append(m.group(1))
print(f'Total: {len(cmds)}')
for c in sorted(set(cmds)):
    print(f'  - {c}')

# 3. Classes
print(f'\n## CLASSES')
classes = []
for i, line in enumerate(lines):
    m = re.search(r'^class (\w+)', line)
    if m:
        classes.append((i+1, m.group(1)))
for ln, name in classes:
    print(f'  L{ln}: {name}')

# 4. Funcoes principais
print(f'\n## FUNCOES (def)')
funcs = []
for i, line in enumerate(lines):
    m = re.search(r'^    def (\w+)', line)
    if m:
        funcs.append((i+1, m.group(1)))
for ln, name in funcs:
    print(f'  L{ln}: {name}')

# 5. Imports
print(f'\n## IMPORTS')
for line in lines:
    if line.startswith('import ') or line.startswith('from '):
        print(f'  {line.strip()[:100]}')

# 6. Atalhos (subprocess calls to sandbox scripts)
print(f'\n## ATALHOS (sandbox scripts)')
for line in lines:
    if 'subprocess.run' in line and 'SANDBOX' in line:
        m = re.search(r"SANDBOX.*'([^']+)'", line)
        if m:
            print(f'  {m.group(1)}')
        elif 'os.path.join' in line:
            # Try to extract from context
            for j in range(lines.index(line)-2, lines.index(line)):
                if 'elif cmd' in lines[j]:
                    m2 = re.search(r"cmd == '(\w+)'", lines[j])
                    if m2:
                        print(f'  {m2.group(1)} (atalho)')
                    break

# 7. Gargalos conhecidos
print(f'\n## GARGALOS CONHECIDOS')
gargalos = [
    'Ollama-bound: plan (158s), build (153s), debate (32s)',
    'qwen2.5-coder:7b inconsistente em ~50% dos patches',
    'ContextCrew depende de llama3.1:8b (lento)',
    'YouTube sem legendas em ~15% dos videos (web_learn)',
    'ddgs unico mecanismo de busca (SearXNG descartado, Google bloqueado)',
]
for g in gargalos:
    print(f'  - {g}')

# 8. Capacidades Cloud vs MCR-DevIA
print(f'\n## CAPACIDADES: MCR-DEVIA VS CLOUD')
print(f'  MCR-DevIA tem ~{len(cmds)} comandos + 18 atalhos = ~{len(cmds)+18} capacidades')
print(f'  Cloud (ferramentas): write, read, edit, grep, glob, bash, webfetch, question, skill, task, todowrite')

# 9. Versao
print(f'\n## VERSAO')
m = re.search(r"data\['versoes'\]", content)
print(f'  Ultima versao registrada no KG')

# 10. Comandos que Cloud TEM e MCR nao tem
cloud_only = ['write', 'webfetch', 'bash']
mcr_has = set(cmds)
missing = [c for c in cloud_only if c not in mcr_has]
print(f'\n## COMANDOS QUE SO CLOUD TEM')
for c in missing:
    print(f'  - {c} (MCR-DevIA nao tem)')

print(f'\n{"="*60}')
print('FIM DA ANALISE')
print(f'{"="*60}')
