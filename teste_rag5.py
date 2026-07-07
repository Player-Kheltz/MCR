import sys, os, time, urllib.request, json
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()
print(f'Chunks: {rag.collection.count()}')

pergunta = 'o que e o sistema de progressao do aventureiro SPA'
ctx = rag.contexto_para_prompt(pergunta, k=2)

print('CONTEXTO RAG:')
print(ctx[:400])
print()

prompt = ctx + '\nINSTRUCAO: Responda usando SOMENTE o contexto acima. PERGUNTA: ' + pergunta
payload = json.dumps({'model': 'qwen2.5-coder:7b', 'prompt': prompt, 'stream': False,
                      'options': {'num_predict': 256, 'temperature': 0.1}}).encode()
req = urllib.request.Request('http://localhost:11434/api/generate', data=payload,
                             headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=60) as r:
    resp = json.loads(r.read()).get('response', '')
t = time.time() - t0
print(f'LLM ({t:.1f}s):')
print(resp[:300])
if 'Progressao' in resp or 'Aventureiro' in resp or 'vocacao' in resp.lower():
    print('\nACERTOU')
else:
    print('\nAINDA ERRANDO')
