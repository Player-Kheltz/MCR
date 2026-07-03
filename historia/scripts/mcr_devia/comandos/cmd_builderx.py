"""Comando: builderx - builderx"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "builderx",
        "desc": "builderx",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    '''Builder-X: constroi scripts por blocos. Uso: builderx <descricao>'''
    desc = " ".join(args)
    r = subprocess.run([sys.executable, r'E:\Projeto MCR\sandbox\builder_x.py', desc],
        capture_output=True, text=True, timeout=120)
    print(r.stdout[-1000:] if r.stdout else '')
    return True
