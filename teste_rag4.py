import sys, os, time, re, unicodedata
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

# Reseta e re-indexa
rag = MCRRAG(reset=True)

# So indexa PERSONALIDADE.md
with open(r'E:\Projeto MCR\PERSONALIDADE.md', 'r', encoding='utf-8') as f:
    texto = f.read()
t0 = time.time()
n = rag.adicionar_texto(texto, 'PERSONALIDADE.md')
print(f'Indexados: {n} chunks em {time.time()-t0:.0f}s')

testes = [
    'sistema de progressao do aventureiro',
    'propagacao 4 2 1',
    'arquivos lua encoding',
    'pilares permanentes',
]
for pergunta in testes:
    docs = rag.buscar_hibrido(pergunta, k=2)
    print(f'\n--- {pergunta} ---')
    for d in docs:
        nome = os.path.basename(d.get('fonte', '?'))[:15]
        texto_exibido = d['texto'][:80].replace('\n', ' ')
        print(f'  [{nome}] {texto_exibido}...')

# Teste com LLM
pergunta = 'o que e o sistema de progressao do aventureiro SPA'
ctx = rag.contexto_para_prompt(pergunta, k=2)

import urllib.request, json
prompt = ctx + '\nINSTRUCAO: Responda usando SOMENTE o contexto acima. PERGUNTA: ' + pergunta
payload = json.dumps({'model': 'qwen2.5-coder:7b', 'prompt': prompt, 'stream': False,
                      'options': {'num_predict': 256, 'temperature': 0.1}}).encode()
req = urllib.request.Request('http://localhost:11434/api/generate', data=payload,
                             headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=60) as r:
    resp = json.loads(r.read()).get('response', '')
t = time.time() - t0
print(f'\nLLM com RAG ({t:.1f}s):')
print(resp[:300])
print()
if 'Progressao' in resp or 'Aventureiro' in resp or 'fim das vocacoes' in resp.lower():
    print('ACERTOU')
else:
    print(f'CONTEXTO INJETADO: {ctx[:200]}')
