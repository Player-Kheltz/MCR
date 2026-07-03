"""Comando: system_scan - system_scan"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "system_scan",
        "desc": "system_scan",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    '''Escaneia o sistema por linguagens e bibliotecas.'''
    import subprocess as sp_scan
    for cmd in ['python','lua','node','gcc','java']:
        sr = sp_scan.run(['where', cmd], capture_output=True, text=True, timeout=5)
        status = 'INSTALADO' if sr.returncode == 0 else 'AUSENTE'
        print(f'  {cmd}: {status}')
    return True
