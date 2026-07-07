import sys, os, time
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG(reset=True)
t0 = time.time()

# PERSONALIDADE.md
path1 = r'E:\Projeto MCR\PERSONALIDADE.md'
if os.path.exists(path1):
    with open(path1, 'r', encoding='utf-8') as f:
        n1 = rag.adicionar_texto(f.read(), 'PERSONALIDADE.md')
    print(f'PERSONALIDADE.md: {n1} chunks')

# Personalidade de Dominios
path2 = r'E:\Projeto MCR\docs\MCR - Instrucoes\[Personalidade] MCR - Personalidade e Identidade de Dominios.txt'
if os.path.exists(path2):
    with open(path2, 'r', encoding='utf-8') as f:
        n2 = rag.adicionar_texto(f.read(), 'Personalidade_Dominios.txt')
    print(f'Personalidade: {n2} chunks')

print(f'Total: {rag.collection.count()} chunks em {time.time()-t0:.0f}s')

print('\n--- BUSCAS ---')
testes = [
    'o que e SPA no Projeto MCR',
    'como funciona a propagacao 4:2:1',
    'encoding de arquivos lua',
    'pilares permanentes do projeto',
]
for pergunta in testes:
    docs = rag.buscar(pergunta, k=2)
    print(f'\n[{pergunta}]')
    print(f'  resultados: {len(docs)}')
    for d in docs:
        print(f'  [{os.path.basename(d["fonte"])}] {d["texto"][:100]}')
    ctx = rag.contexto_para_prompt(pergunta, k=2)
    print(f'  contexto: {len(ctx)} chars')

print('\n--- TESTE LLM ---')
import urllib.request, json
pergunta = 'explique o que e SPA no Projeto MCR'
contexto = rag.contexto_para_prompt(pergunta, k=3)

# Com RAG
prompt = (
    f'{contexto}\n'
    f'INSTRUCAO: Responda usando SOMENTE o contexto acima. '
    f'Nao use seu conhecimento proprio.\n'
    f'PERGUNTA: {pergunta}'
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
with urllib.request.urlopen(req, timeout=60) as r:
    resp = json.loads(r.read()).get('response', '')
t = time.time() - t0

print(f'Resposta LLM com RAG ({t:.1f}s):')
print(resp[:300])
print()
if 'Single' in resp and 'Page' in resp:
    print('AINDA ERROU - alucinou Single Page Application')
elif 'Progressao' in resp or 'Aventureiro' in resp:
    print('ACERTOU - falou de SPA como Sistema de Progressao')
else:
    print(f'Resposta: {resp[:50]}...')
