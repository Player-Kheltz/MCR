"""Comando: revisar - Revisor por pares com Orquestrador Universal."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "revisar",
        "desc": "Revisor por pares: valida mudancas antes de aplicar (Orquestrador Universal)",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Revisor por pares: valida mudancas antes de aplicar.
    Uso: python mcr_devia.py revisar <arquivo> <descricao>"""
    arquivo = args[0]
    descricao = " ".join(args[1:])
    path = os.path.join(_SANDBOX, arquivo) if not os.path.exists(arquivo) else arquivo
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            conteudo = f.read()
        linhas = len(conteudo.splitlines())
        
        # Orquestrador Universal para avaliar risco
        if ia and hasattr(ia, 'orquestrar'):
            r = ia.orquestrar("revisar", {
                "arquivo": arquivo,
                "descricao": descricao,
                "linhas": linhas,
                "conteudo": conteudo[:500],
            }, consulta=f"revisar {arquivo}", temp=0.1)
            if r:
                resp = r
            else:
                resp = None
        else:
            resp = None
        
        # Fallback: prompt direto
        if not resp:
            prompt = f'Arquivo: {arquivo}\nMudanca: {descricao}\nCodigo atual ({linhas} linhas):\n{conteudo[:500]}\nRisco ALTO, MEDIO ou BAIXO? Responda so o nivel.'
            resp = fast(prompt)
        
        if resp and 'ALTO' not in resp:
            print(f'[Revisor] APROVADO (risco {resp[:30]})')
        else:
            print(f'[Revisor] REJEITADO - risco ALTO detectado: {resp[:80] if resp else "sem resposta"}')
    else:
        print(f'[Revisor] Arquivo nao encontrado: {arquivo}')
    return True
