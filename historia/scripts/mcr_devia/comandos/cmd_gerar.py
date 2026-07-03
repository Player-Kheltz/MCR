"""Comando: gerar - gerar"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "gerar",
        "desc": "gerar",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    tipo = args[0]; resto = ' '.join(args[1:])
    g = Gerador(ia, kg)
    g.gerar(tipo, resto)
    return True
