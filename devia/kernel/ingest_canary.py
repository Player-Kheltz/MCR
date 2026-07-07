#!/usr/bin/env python3
"""ingest_canary.py — Indexa scripts Lua e XML do Canary no ChromaDB.
Chunking por funcoes Lua (function nome() ... end).
Usa a mesma instancia ChromaDB do MCRRAG."""
import os, re, sys, time
sys.path.insert(0, r'E:\MCR')

from rag_mcr import MCRRAG

# Configuracao
CANARY_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server")
LORE_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "lore")

DIRETORIOS_LUA = [
    os.path.join(CANARY_BASE, "data-canary", "scripts", "lib"),
    os.path.join(CANARY_BASE, "data-canary", "scripts", "actions"),
    os.path.join(CANARY_BASE, "data", "npclib"),
    os.path.join(CANARY_BASE, "data-otservbr-global", "npc"),
]

DIRETORIOS_XML = []


def chunk_lua_functions(texto, fonte=""):
    """Quebra Lua por funcoes: function nome() ... end."""
    if not texto:
        return []
    
    chunks = []
    # Regex: function nome() ... end, com suporte a function, method, anonymous
    padrao = re.compile(
        r'(function\s+[\w.:]+\s*\([\s\S]*?end\b)'
        r'|((?:local\s+)?function\s+[\w.:]+\s*\([\s\S]*?end\b)'
        r'|(\w+\s*=\s*function\s*\([\s\S]*?end\b)',
        re.IGNORECASE
    )
    
    for match in padrao.finditer(texto):
        chunk = match.group(0).strip()
        if len(chunk) > 30:
            chunks.append(chunk)
    
    # Se nao encontrou funcoes, envia arquivo inteiro (se pequeno)
    if not chunks and len(texto) < 5000:
        chunks.append(texto)
    
    return chunks


def chunk_lua_configs(texto, fonte=""):
    """Quebra por configs { ... } adicionais (ja tem functions)."""
    if not texto:
        return []
    chunks = []
    padrao = re.compile(r'(local\s+\w+\s*=\s*\{[\s\S]*?\})')
    for match in padrao.finditer(texto):
        chunk = match.group(0).strip()
        if 50 < len(chunk) < 2000:
            chunks.append(chunk)
    return chunks


def indexar_diretorio_lua(rag, diretorio, max_chunks=5000):
    """Indexa .lua com chunking por funcao."""
    if not os.path.isdir(diretorio):
        print(f"[Ingest] Diretorio nao encontrado: {diretorio}")
        return 0
    
    total = 0
    for raiz, _, arquivos in os.walk(diretorio):
        for f in arquivos:
            if not f.endswith('.lua'):
                continue
            if total >= max_chunks:
                break
            caminho = os.path.join(raiz, f)
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                    texto = fh.read()
            except:
                continue
            if len(texto) < 100:
                continue
            
            chunks = chunk_lua_functions(texto, caminho)
            # Adiciona configs que nao foram capturadas
            configs = chunk_lua_configs(texto, caminho)
            for c_chunk in configs:
                if c_chunk not in chunks:
                    chunks.append(c_chunk)
            
            for chunk in chunks:
                try:
                    rag.adicionar_texto(chunk, caminho)
                except:
                    continue
                total += 1
            if total % 100 == 0 and total > 0:
                print(f"  {total} chunks...", flush=True)
        
        if total >= max_chunks:
            break
    
    print(f"  Total: {total} chunks de {diretorio}")
    return total


def indexar_diretorio_xml(rag, diretorio):
    """Indexa .xml como documento unico (monstros sao pequenos)."""
    if not os.path.isdir(diretorio):
        print(f"[Ingest] Diretorio nao encontrado: {diretorio}")
        return 0
    
    total = 0
    for raiz, _, arquivos in os.walk(diretorio):
        for f in arquivos:
            if not f.endswith('.xml'):
                continue
            caminho = os.path.join(raiz, f)
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                    texto = fh.read()
            except:
                continue
            if len(texto) < 50 or len(texto) > 30000:
                continue
            try:
                rag.adicionar_texto(texto, caminho)
                total += 1
            except:
                continue
    print(f"  Total: {total} XMLs de {diretorio}")
    return total


def indexar_lore(rag, diretorio):
    """Indexa arquivos .md e .txt de lore."""
    if not os.path.isdir(diretorio):
        print(f"[Ingest] Pasta lore_base nao encontrada: {diretorio}")
        return 0
    
    total = 0
    for f in os.listdir(diretorio):
        if not (f.endswith('.md') or f.endswith('.txt')):
            continue
        caminho = os.path.join(diretorio, f)
        try:
            with open(caminho, 'r', encoding='utf-8') as fh:
                texto = fh.read()
        except:
            continue
        if len(texto) < 50:
            continue
        try:
            rag.adicionar_texto(texto, caminho)
            total += 1
        except:
            continue
    print(f"  Total: {total} arquivos de lore")
    return total


def main():
    rag = MCRRAG()
    print(f"[Ingest] ChromaDB: {rag.collection.count()} chunks existentes")
    print(f"[Ingest] Iniciando indexacao do Canary e Lore...")
    t0 = time.time()
    
    # Indexa funcoes Lua (lib, actions, npc)
    for diretorio in DIRETORIOS_LUA:
        indexar_diretorio_lua(rag, diretorio)
    
    # Indexa XMLs de monstros
    for diretorio in DIRETORIOS_XML:
        indexar_diretorio_xml(rag, diretorio)
    
    # Indexa lore
    indexar_lore(rag, LORE_BASE)
    
    t = time.time() - t0
    print(f"\n[Ingest] Finalizado em {t:.0f}s. Total: {rag.collection.count()} chunks")


if __name__ == "__main__":
    main()
