"""demo_conversa_mcr — Converse com o MCR. Sem LLM. Sem GPU."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.chat import MCRChat

print("=" * 60)
print("MCR CHAT — Conversa 100% Markov + Entropia")
print("=" * 60)

chat = MCRChat(temperatura=0.75)

print("\n[Alimentando corpus de NPCs...]")
with open(os.path.join(os.path.dirname(__file__), '..', '..',
                       'cache', 'npc_knowledge.json'), 'r', encoding='utf-8') as f:
    dados = json.load(f)
pares = []
for dialogos_lista in dados.get('dialogos', {}).values():
    for item in dialogos_lista:
        texto = str(item[0]) if item[0] else ''
        npc = str(item[1]) if len(item) > 1 else 'desconhecido'
        if len(texto) >= 10:
            pares.append((texto, npc))
chat.alimentar_corpus(pares)
est = chat.estado()
print("  %d observacoes, %d palavras" % (est['observacoes'], est['palavras']))

print("\n" + "=" * 60)
print("COMECE A CONVERSAR (digite 'sair' para encerrar)")
print("=" * 60)

entradas_teste = [
    "Ola, quem e voce?",
    "O que voce vende?",
    "Preciso de uma arma",
    "Quanto custa uma espada?",
    "Voce conhece magia?",
    "Me fale sobre dragoes",
    "Onde posso encontrar um mago?",
    "Preciso de pocoes de cura",
    "Ha algum perigo por aqui?",
    "Como chego na cidade?",
]

for entrada in entradas_teste:
    resposta = chat.perguntar(entrada, max_tokens=20)
    print("\n  Voce: %s" % entrada)
    print("  MCR:  %s" % resposta)

print("\n" + "=" * 60)
print("ESTADO FINAL:")
est = chat.estado()
print("  Observacoes: %d" % est['observacoes'])
print("  Palavras:    %d" % est['palavras'])
print("  Interacoes:  %d" % est['interacoes'])
print("=" * 60)
