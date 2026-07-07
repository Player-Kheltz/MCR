import sys, os, time
sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', '..', 'Projeto MCR', 'historia', 'scripts', 'mcr_devia'))
from fix_mcr_devia_v2 import MCRDevIARevived

revived = MCRDevIARevived()
print(f'LLM: {revived.llm.disponivel()}')
print(f'Seeds: {revived.decider.total}')

# Traducao
r = revived.processar('traduza hello world para PT-BR')
print(f'[traducao] classe={r.get("classe")} conf={r.get("confianca",0):.2f}')
resp = r.get('resposta', '')
print(f'[traducao] resposta: {resp[:150]}')
print(f'[traducao] tempo: {r.get("tempo",0):.2f}s')

# Teste de aprendizado
classe, conf = revived.decider.classificar('verta good morning para portugues')
print(f'[aprendizado] verta good morning -> {classe} ({conf:.2f})')
revived.decider.aprender('verta good morning para portugues', 'traduzir_texto')
classe, conf = revived.decider.classificar('verta good morning para portugues')
print(f'[aprendizado] apos aprender: {classe} ({conf:.2f})')
