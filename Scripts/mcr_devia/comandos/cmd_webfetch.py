"""Comando: webfetch - Busca conteudo de uma URL."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "webfetch",
        "desc": "Busca conteudo de uma URL.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Busca conteudo de uma URL.
    Uso: python mcr_devia.py webfetch <url>"""
    url = args[0]
    print(f'[Webfetch] Buscando URL: {url[:80]}...')
    try:
        import urllib.request
        r = urllib.request.urlopen(url, timeout=15)
        conteudo = r.read().decode('utf-8', errors='replace')
        print(f'[Webfetch] Recebidos {len(conteudo)} bytes:')
        print(conteudo[:500])
    except Exception as e:
        print(f'[Webfetch] Erro ao buscar URL: {e}')

# Atalhos para scripts importantes (comandos diretos)
    return True
