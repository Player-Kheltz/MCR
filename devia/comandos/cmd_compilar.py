"""Comando: compilar - compilar"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "compilar",
        "desc": "compilar",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    projeto = args[0] if args else 'canary'
    b = Builder(kg, ia)
    b.compilar(projeto)
    return True
