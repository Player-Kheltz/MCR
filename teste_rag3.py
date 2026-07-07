import sys, os, time
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()
print(f'Collection: {rag.collection.count()} chunks')

testes = [
    'o que e SPA no Projeto MCR',
    'como funciona a propagacao 4:2:1',
    'encoding de arquivos lua',
    'pilares permanentes do projeto',
]
for pergunta in testes:
    print(f'\n--- {pergunta} ---')
    docs = rag.buscar_hibrido(pergunta, k=2)
    print(f'  {len(docs)} resultados')
    for d in docs:
        nome = os.path.basename(d.get('fonte', '?'))
        score = d.get('score', 0)
        print(f'  [{nome} score={score:.2f}] {d["texto"][:80]}')
    
    ctx = rag.contexto_para_prompt(pergunta, k=2)
    print(f'  contexto: {len(ctx)} chars')

print('\n--- TESTE LLM COM RAG ---')
import urllib.request, json

pergunta = 'explique o que e SPA no contexto do Projeto MCR'
ctx = rag.contexto_para_prompt(pergunta, k=3)

prompt = (
    ctx + '\n'
    'INSTRUCAO: Responda usando SOMENTE o contexto acima. '
    'Se o contexto nao tiver a resposta, diga: NAO ENCONTRADO NO CONTEXTO.\n'
    'PERGUNTA: ' + pergunta
)

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
    print(f'\nRESPOSTA LLM ({t:.1f}s):')
    print(resp[:400])
    if 'Progressao' in resp or 'Aventureiro' in resp:
        print('\nACERTOU - SPA como Sistema de Progressao')
    elif 'Single' in resp or 'Page' in resp:
        print('\nALUCINOU - Single Page Application')
    else:
        print('\nOUTRO')
except Exception as e:
    print(f'Erro: {e}')
