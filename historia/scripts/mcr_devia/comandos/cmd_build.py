"""Comando: build - Pipeline Dinamica: gera codigo sob medida."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "build",
        "desc": "Pipeline Dinamica: gera codigo sob medida.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Pipeline Dinamica: gera codigo sob medida.
    Uso: python mcr_devia.py build <descricao>
    Ex:  python mcr_devia.py build "criar script de backup em backup.py"
         python mcr_devia.py build "funcao hello_world em hello.py"
    A pipeline detecta complexidade, extrai nome do arquivo.
    Usa ContextCrew para contexto. So gera o necessario."""
    desc = " ".join(args)
    pipeline_path = os.path.join(_SANDBOX, 'builder_infinito.py')
    subprocess.run([sys.executable, pipeline_path, desc])
    return True
