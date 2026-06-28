"""Comando: grep - Busca texto em arquivos."""
import os, re, fnmatch

def register():
    return {
        "name": "grep",
        "desc": "Busca texto em arquivos (--literal, --max, --ctx)",
        "handler": execute,
        "args": [
            {"name": "padrao", "type": "str", "required": True},
            {"name": "--literal", "type": "flag", "desc": "Busca exata"},
            {"name": "--max", "type": "int", "desc": "Max resultados"},
            {"name": "--ctx", "type": "int", "desc": "Linhas de contexto"},
        ],
        "categoria": "busca",
    }

def execute(kg, ia, args, ctx_crew=None):
    print(f'[Comando Grep] Prototipo funcional! Args recebidos: {args[:3]}...')
    return True
