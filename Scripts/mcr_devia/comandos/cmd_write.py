"""Comando: write - Escreve conteudo em arquivo.
Uso: write <path> <conteudo>
     (para conteudo complexo, use --json)
"""
import os

def register():
    return {
        "name": "write",
        "desc": "Escreve conteudo em arquivo. Para conteudo complexo, usar --json",
        "handler": execute,
        "args": [
            {"name": "path", "type": "str", "required": True},
            {"name": "conteudo", "type": "str", "required": True},
        ],
        "categoria": "arquivo",
    }

def execute(kg, ia, args, ctx_crew=None):
    if len(args) < 2:
        print('[Write] Uso: write <path> <conteudo>')
        return True
    
    path = args[0]
    # Se nao for absoluto, resolve relativo ao BASE
    if not os.path.isabs(path):
        BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        path = os.path.join(BASE, path)
    
    # Junta args restantes como conteudo (permite espacos sem aspas no --json)
    conteudo = " ".join(args[1:])
    
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f'[Write] {os.path.relpath(path, BASE if not os.path.isabs(args[0]) else os.path.dirname(path))} ({len(conteudo)} bytes)')
    except Exception as e:
        print(f'[Write] ERRO: {e}')
    
    return True
