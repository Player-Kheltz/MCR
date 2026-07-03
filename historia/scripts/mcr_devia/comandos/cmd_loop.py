"""Comando: loop - Loop autonomo OODA. Uso: loop [max_ciclos] [modo]"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "loop",
        "desc": "Loop autonomo OODA. Uso: loop [max_ciclos] [modo]",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Loop autonomo OODA. Uso: loop [max_ciclos] [modo]"""
    _run_script('mcr_loop', extra_args=args if args else None)
    return True
