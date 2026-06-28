"""Testa busca tecnica do Enricher para .lua."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/scripts/mcr_devia')
from modulos.context_enricher import ContextEnricher

# Chama _gerar_tecnico diretamente com timeout maior
import time
t0 = time.time()
enricher = ContextEnricher()
conteudo = enricher._gerar_tecnico(['.lua', 'lua'])
tempo = time.time() - t0
print(f'Tempo: {tempo:.1f}s')
print(f'Tamanho: {len(conteudo)} chars')
if conteudo:
    print(conteudo[:1000])
else:
    print('(vazio)')
    
    # Debug: os diretorios existem?
    base = 'E:/Projeto MCR'
    dirs = [
        os.path.join(base, 'scripts', 'mcr_devia'),
        os.path.join(base, 'Canary', 'src'),
        os.path.join(base, 'OTClient', 'src'),
        os.path.join(base, 'Canary', 'data-canary', 'scripts'),
    ]
    for d in dirs:
        if os.path.exists(d):
            # Conta .py e .lua files
            py = sum(1 for _, _, files in os.walk(d) for f in files if f.endswith('.py'))
            lua = sum(1 for _, _, files in os.walk(d) for f in files if f.endswith('.lua'))
            print(f'  {d.split(os.sep)[-1]}: {py} py, {lua} lua')
        else:
            print(f'  {d}: NAO EXISTE')
