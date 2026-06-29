"""Comando: bugfinder - Escaneia logs e registra erros no KG para aprendizado."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "bugfinder",
        "desc": "Escaneia logs e registra erros no KG para aprendizado.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Escaneia logs e registra erros no KG para aprendizado."""
    print(f'[BugFinder] Escaneando logs...')
    import glob as glob_bf
    logs_dir = os.path.join(_SANDBOX, '.mcr_devia')
    encontrados = 0
    for pattern in ['*.log', '*.err', '*.auto_repair*']:
        for path in glob_bf.glob(os.path.join(logs_dir, pattern)):
            if not os.path.exists(path): continue
            with open(path, encoding='utf-8', errors='ignore') as f:
                for linha in f:
                    if any(p in linha.lower() for p in ['error','fail','traceback','exception']):
                        kg.aprender(f'bugfinder: {linha[:80]}', f'fonte: {os.path.basename(path)}', 'verificar log', 'bugfinder')
                        encontrados += 1
    print(f'  {encontrados} erros registrados')
    return True
