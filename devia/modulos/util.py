"""modulos.util — Funcoes utilitarias.

Redireciona para implementacoes atuais em mcr/.
"""
import os
import re
from pathlib import Path

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
BASE = os.path.normpath(_BASE)
SANDBOX = os.path.join(BASE, 'cache', 'sandbox')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')




def fast(texto, max_len=500):
    """Trunca texto de forma inteligente (preserva palavras inteiras)."""
    if not texto or len(texto) <= max_len:
        return texto
    corte = texto[:max_len].rfind(' ')
    if corte < max_len // 2:
        corte = max_len
    return texto[:corte] + '...'


def gerar(template, contexto=None):
    """Gera texto a partir de template com substituicao simples."""
    if contexto is None:
        contexto = {}
    resultado = template
    for k, v in contexto.items():
        resultado = resultado.replace(f'{{{k}}}', str(v))
    return resultado


def extrair_nome_projeto(texto):
    """Extrai nome de projeto de um texto."""
    match = re.search(r'(?:projeto|project)\s+[`"\']*([a-zA-Z0-9_-]+)', texto, re.I)
    return match.group(1) if match else 'desconhecido'


def extrair_codigo_puro(texto):
    """Extrai bloco de codigo puro de um texto com marcadores markdown."""
    bloco = re.search(r'```(?:\w+)?\n(.*?)```', texto, re.DOTALL)
    if bloco:
        return bloco.group(1).strip()
    return texto


# Alias para compatibilidade com comandos que importam extrair_codigo
extrair_codigo = extrair_codigo_puro


def reparar_com_validacao(codigo, linguagem='lua'):
    """Reparacao basica de codigo (remove whitespace extra)."""
    if not codigo:
        return codigo
    linhas = codigo.split('\n')
    linhas = [l.rstrip() for l in linhas]
    return '\n'.join(linhas)


def _get_modelo(preferido=None):
    """Retorna modelo Ollama disponivel."""
    return preferido or 'llama3.1'
