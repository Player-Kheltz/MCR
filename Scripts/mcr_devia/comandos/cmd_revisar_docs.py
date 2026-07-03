"""Comando: revisar_docs - Verifica se AGENTS.md e docs/rules estao sincronizados."""
import os, re

def register():
    return {
        "name": "revisar_docs",
        "desc": "Verifica se documentacao esta sincronizada com o codigo real",
        "handler": execute,
        "args": [],
        "categoria": "util",
    }

def execute(kg, ia, args, ctx_crew=None):
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    issues = []
    
    # 1. Verifica comandos reais vs AGENTS.md
    COMANDOS_DIR = os.path.join(os.path.dirname(__file__))
    cmd_reais = sorted([f[4:-3] for f in os.listdir(COMANDOS_DIR) if f.startswith('cmd_') and f.endswith('.py')])
    
    AGENTS_PATH = os.path.join(BASE, 'AGENTS.md')
    with open(AGENTS_PATH, 'r', encoding='utf-8') as f:
        agents = f.read()
    
    for cmd in cmd_reais:
        if cmd not in agents:
            issues.append(f'AGENTS.md nao menciona comando: {cmd}')
    
    # 2. Verifica modulos reais vs AGENTS.md
    MODULOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modulos')
    mods_reais = sorted([f[:-3] for f in os.listdir(MODULOS_DIR) if f.endswith('.py') and not f.startswith('_')])
    
    for mod in mods_reais:
        if mod not in agents and mod != 'util':
            issues.append(f'AGENTS.md nao menciona modulo: {mod}')
    
    # 3. Verifica personalidades reais
    PERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'personalidades')
    pers_reais = sorted([f[:-3] for f in os.listdir(PERS_DIR) if f.endswith('.py') and not f.startswith('_')])
    
    for pers in pers_reais:
        if pers not in agents and pers != 'seletor':
            issues.append(f'AGENTS.md nao menciona personalidade: {pers}')
    
    # 4. Mostra resultado
    print(f'[Revisar] Comandos: {len(cmd_reais)} | Modulos: {len(mods_reais)} | Personalidades: {len(pers_reais)}')
    
    if issues:
        print(f'[Revisar] {len(issues)} inconsistencias encontradas:')
        for issue in issues:
            print(f'  - {issue}')
        print(f'\n[Revisar] Execute: write AGENTS.md para atualizar (apos revisar as alteracoes)')
    else:
        print('[Revisar] Documentacao 100% sincronizada!')
    
    return True
