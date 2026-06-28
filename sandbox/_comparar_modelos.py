#!/usr/bin/env python3
"""Teste comparativo: diferentes modelos/abordagens para a mesma pergunta."""
import sys, os, time
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.util import fast, gerar
from kernel import MCRKernel
from modulos.conselho import Conselho
import context_crew

k = MCRKernel(); k.inicializar()
ctx_crew = context_crew.ContextCrew()

PERGUNTA = "Crie uma historia original sobre a cidade de Eridanus no universo MCR"

resultados = []

# === TESTE 1: Pipeline completo ===
print('[Teste 1] Pipeline V3 (qwen2.5-coder:7b)')
from modulos.pipeline import Pipeline
p = Pipeline(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew)
t0 = time.time()
r1 = p.executar(PERGUNTA)
t1 = time.time() - t0
resultados.append(('Pipeline V3 (7B)', r1, t1))

# === TESTE 2: Gerar direto com temperatura alta ===
print('\n[Teste 2] Gerar direto (llama3.1:8b - PT-BR)')
import urllib.request, json
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
t0 = time.time()
try:
    d = json.dumps({'model': 'llama3.1:8b', 'prompt': 
        f'Crie uma historia ORIGINAL sobre Eridanus, um lugar magico em um universo de fantasia. '
        f'Seja detalhado e criativo. Nao use ficcao cientifica.\n\n{PREGUNTA}\n\nHistoria:',
        'stream': False, 'options': {'temperature': 0.7, 'num_ctx': 4096}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type': 'application/json'})
    r2 = json.loads(urllib.request.urlopen(req, timeout=120).read()).get('response', '') or ''
except:
    r2 = ''
t2 = time.time() - t0
resultados.append(('Gerar llama3.1:8b', r2, t2))

# === TESTE 3: Conselho V8 ===
print('\n[Teste 3] Conselho V8 (qwen2.5-coder:7b)')
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew)
t0 = time.time()
r3 = c.deliberar(PERGUNTA)
t3 = time.time() - t0
r3_texto = r3.get('veredito', '')
resultados.append(('Conselho V8 (7B)', r3_texto, t3))

# === COMPARACAO ===
print(f'\n{"="*80}')
print('COMPARACAO REAL')
print(f'{"="*80}')
print(f'Pergunta: {PERGUNTA}')
print()

import re
for nome, texto, tempo in resultados:
    chars = len(texto)
    nomes = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', texto)))
    linhas = texto.count('\n') + 1
    
    # Detecta ficcao cientifica vs fantasia
    scifi = any(w in texto.lower() for w in ['nave', 'espaco', 'estelar', 'cosmica', 'astronave', 'orbita'])
    fantasia = any(w in texto.lower() for w in ['magia', 'reino', 'dragao', 'castelo', 'elfo', 'encantado'])
    
    print(f'{nome}:')
    print(f'  Tamanho: {chars} chars | {linhas} linhas')
    print(f'  Nomes proprios: {nomes}')
    print(f'  Sci-fi: {"SIM" if scifi else "nao"} | Fantasia: {"SIM" if fantasia else "nao"}')
    print(f'  Tempo: {tempo:.0f}s')
    print(f'  Amostra: {texto[:120]}...')
    print()
