"""Comando: proativo - Varre o sistema e sugere acoes sem ninguem pedir."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "proativo",
        "desc": "Varre o sistema e sugere acoes sem ninguem pedir.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Varre o sistema e sugere acoes sem ninguem pedir."""
    print(f'[Proativo] Oportunidades encontradas:')
    import json as json_proativo
    todo_path = os.path.join(_SANDBOX, '.mcr_todo.json')
    if os.path.exists(todo_path):
        with open(todo_path, encoding='utf-8') as f:
            todos = json_proativo.load(f)
        pendentes = [t for t in todos if not t.get('done')]
        if pendentes:
            print(f'  - {len(pendentes)} tarefas pendentes no todo')
    n_py = len([f for f in os.listdir(_SANDBOX) if f.endswith('.py')])
    if n_py > 30:
        print(f'  - {n_py} scripts .py no sandbox (considerar limpeza)')
    return True
