import sys, re
sys.path.insert(0,'E:/MCR')
from mcr.agente import MCRLoop
from mcr.chat import MCRChat

agente = MCRLoop(coupling_path='E:/MCR/cache/coupling_npc.json')
c = agente.coupling
chat = MCRChat(coupling=c)

entrada = 'ola tudo bem'
acao, conf = c.decidir(entrada, (None, 0.0))
print('acao=%s conf=%.2f' % (acao, conf))

palavras_chave = re.findall(r'[a-zà-ÿ]{4,}', entrada.lower())
seed = palavras_chave[-1] if palavras_chave else 'responder'
print('seed=%s' % seed)

r1 = chat._gerar_resposta(seed, max_tokens=12, modo='semantico')
print('semantico: [%s] (len=%d)' % (r1, len(r1)))

r2 = chat._gerar_resposta(seed, max_tokens=12, modo='markov')
print('markov:    [%s] (len=%d)' % (r2, len(r2)))

r_agente = agente.perguntar(entrada)
print('agente:    [%s] (len=%d)' % (r_agente, len(r_agente)))
