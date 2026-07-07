"""Debug: RAG context injection and LLM response."""
import sys, os, time, urllib.request, json
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()
print(f'RAG chunks: {rag.collection.count()}')

pergunta = 'explique o que e SPA no Projeto MCR'
ctx = rag.contexto_para_prompt(pergunta, k=3)
print(f'\nCONTEXTO RETORNADO ({len(ctx)} chars):')
print(ctx[:500])

# Test with explicit instruction to override bad knowledge
prompts = [
    # Stronger instruction
    ctx + (
        'IMPORTANTE: NO PROJETO MCR, a sigla SPA significa "Sistema de Progressao do Aventureiro". '
        'NUNCA use o significado "Single Page Application".\n'
        f'Responda baseado no contexto acima.\n'
        f'Pergunta: {pergunta}'
    ),
]

for i, prompt in enumerate(prompts):
    print(f'\n--- Teste {i+1} ---')
    payload = json.dumps({
        'model': 'qwen2.5-coder:7b',
        'prompt': prompt,
        'stream': False,
        'options': {'num_predict': 256, 'temperature': 0.1}
    }).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate', data=payload,
                                 headers={'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read()).get('response', '')
        t = time.time() - t0
        print(f'  Tempo: {t:.1f}s')
        print(f'  Resposta: {resp[:200]}')
        is_correct = 'Progressao' in resp or 'Aventureiro' in resp
        is_wrong = 'Single' in resp or 'Page' in resp
        print(f'  Correct: {is_correct}, Wrong: {is_wrong}')
    except Exception as e:
        print(f'  Erro: {e}')

# Also test with llama3.1 for PT-BR
print(f'\n--- Teste com llama3.1:8b (Melhor PT-BR) ---')
prompt = ctx + (
    'IMPORTANTE: A sigla SPA no contexto do Projeto MCR significa '
    '"Sistema de Progressao do Aventureiro". Nao use outro significado.\n'
    f'Pergunta: {pergunta}'
)
payload = json.dumps({
    'model': 'llama3.1:8b',
    'prompt': prompt,
    'stream': False,
    'options': {'num_predict': 256, 'temperature': 0.1}
}).encode()
req = urllib.request.Request('http://localhost:11434/api/generate', data=payload,
                             headers={'Content-Type': 'application/json'})
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read()).get('response', '')
    t = time.time() - t0
    print(f'  Tempo: {t:.1f}s')
    print(f'  Resposta: {resp[:200]}')
    is_correct = 'Progressao' in resp or 'Aventureiro' in resp
    is_wrong = 'Single' in resp or 'Page' in resp
    print(f'  Correct: {is_correct}, Wrong: {is_wrong}')
except Exception as e:
    print(f'  Erro: {e}')
