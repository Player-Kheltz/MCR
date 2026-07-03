"""Comando: system - SystemAware: le o computador inteiro (read-only)."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "system",
        "desc": "SystemAware: le o computador inteiro (read-only).",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    subprocess.run([sys.executable, os.path.join(_SANDBOX, 'system_aware.py')])
    return True
