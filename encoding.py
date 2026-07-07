"""encoding.py — Funcoes padronizadas de leitura de arquivos.
Projeto MCR: .lua = ISO-8859-1 (Latin-1), .cpp/.cs/.go = UTF-8."""
import os

def ler_lua(path):
    """Le arquivo .lua sempre em ISO-8859-1 (Latin-1)."""
    with open(path, 'r', encoding='latin-1', errors='replace') as f:
        return f.read()

def ler_texto(path):
    """Le arquivo generico em UTF-8 (padrao para .md, .py, .json, .txt, .cpp, .cs)."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def ler_arquivo(path):
    """Detecta encoding automaticamente pela extensao."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.lua':
        return ler_lua(path)
    return ler_texto(path)

def escrever_lua(path, conteudo):
    """Escreve arquivo .lua sempre em Latin-1."""
    with open(path, 'w', encoding='latin-1') as f:
        f.write(conteudo)

def escrever_texto(path, conteudo):
    """Escreve arquivo generico em UTF-8."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(conteudo)
