"""Comando: question - Pergunta algo ao usuario e aguarda resposta."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "question",
        "desc": "Pergunta algo ao usuario e aguarda resposta.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Pergunta algo ao usuario e aguarda resposta.
    Uso: python mcr_devia.py question <pergunta>"""
    pergunta = " ".join(args)
    print(f'[Question] Pergunta: {pergunta}')
    try:
        resposta = input('> ')
        print(f'[Question] Resposta recebida: {resposta}')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")
    return True
