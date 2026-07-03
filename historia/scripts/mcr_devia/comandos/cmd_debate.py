"""Comando: debate - Debate: 2 sub-agentes discutem antes de entregar."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "debate",
        "desc": "Debate: 2 sub-agentes discutem antes de entregar.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Debate: 2 sub-agentes discutem antes de entregar.
    Uso: python mcr_devia.py debate <tema>"""
    tema = " ".join(args)
    subprocess.run([sys.executable, os.path.join(_SANDBOX, 'debate_protocol.py'), tema])
    return True
