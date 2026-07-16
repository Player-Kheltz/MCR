import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Silencia logs do MCR
os.environ['MCR_QUIET'] = '1'

from mcr.semantic_router import similaridade, termo_mais_similar, palavras_similares
from mcr.coupling import MCRCoupling
import warnings
import logging
logging.disable(logging.CRITICAL)

t0 = time.time()
from mcr.mcr import MCR
print(f'MCR carregado em {time.time()-t0:.1f}s')

mcr = MCR()
mcr.quiet = True  # tenta silenciar mais o mcr

print()
print('=== Teste Real 1: processo conhecido "gerar npc" ===')
r = mcr.processar('gerar npc')
acao = r.get('acao', r.get('intencao', r.get('predicted_action', 'N/A')))
print(f'  acao={acao!r}')

print()
print('=== Teste Real 2: sinonimo verbo "criar npc" ===')
r = mcr.processar('criar npc')
acao = r.get('acao', r.get('intencao', r.get('predicted_action', 'N/A')))
conf = r.get('confianca', r.get('confiança', r.get('score', r.get('confidence', '?'))))
print(f'  acao={acao!r}  conf={conf!r}')

print()
print('=== Teste Real 3: sinonimo flexao "crie um mago" ===')
r = mcr.processar('crie um mago')
acao = r.get('acao', r.get('intencao', r.get('predicted_action', 'N/A')))
conf = r.get('confianca', r.get('confiança', r.get('score', r.get('confidence', '?'))))
print(f'  acao={acao!r}  conf={conf!r}')

print()
print('=== Teste Real 4: entidade nunca vista "criar mago ferreiro" ===')
r = mcr.processar('criar mago ferreiro')
acao = r.get('acao', r.get('intencao', r.get('predicted_action', 'N/A')))
conf = r.get('confianca', r.get('confiança', r.get('score', r.get('confidence', '?'))))
tokens = r.get('tokens', r.get('palavras', []))
estado = r.get('estado', r.get('state', '?'))
print(f'  acao={acao!r}  conf={conf!r}')
print(f'  tokens={tokens}')

print()
print('=== Teste Real 5: semantic_router.similaridade() ===')
print(f'  similaridade("criar", "crie") = {similaridade("criar", "crie")}')
print(f'  melhor match pra "crie": {termo_mais_similar("crie", {"gerar": {}, "npcs": {}})}')

print()
print(f'Total: {time.time()-t0:.1f}s')
print('OK')
