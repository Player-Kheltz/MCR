"""Comando: plan - Planeja antes de executar: intencao -> plan -> intencao -> build."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "plan",
        "desc": "Planeja antes de executar: intencao -> plan -> intencao -> build.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Planeja antes de executar: intencao -> plan -> intencao -> build.
    Uso: python mcr_devia.py plan <request>"""
    request = " ".join(args)
    subprocess.run([sys.executable, os.path.join(_SANDBOX, 'builder_infinito.py'), f'PLAN: {request[:200]}'])
    return True
