import sys, os, json, random, math
sys.path.insert(0, 'E:/MCR'); os.chdir('E:/MCR')

from mcr.coupling import MCRCoupling
from mcr.semantic_router import similaridade as ngram_sim

# Corpus de treino EXP2
corpus = [
    ("gato late", "animais"), ("cachorro late", "animais"),
    ("gato mia", "animais"), ("cachorro corre", "animais"),
    ("passaro voa", "animais"), ("peixe nada", "animais"),
    ("carro corre", "veiculos"), ("moto corre", "veiculos"),
    ("caminhao anda", "veiculos"), ("bicicleta anda", "veiculos"),
    ("uva doce", "frutas"), ("maca doce", "frutas"),
    ("limao azedo", "frutas"), ("banana amarela", "frutas"),
    ("fogo queima", "elementos"), ("agua molha", "elementos"),
    ("gelo congela", "elementos"), ("vento sopra", "elementos"),
    ("criar monstro", "criar"), ("gerar npc", "criar"),
    ("fazer item", "criar"), ("editar script", "editar"),
    ("modificar codigo", "editar"), ("alterar texto", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
    ("procurar palavra", "buscar"), ("aprender licao", "aprender"),
    ("estudar materia", "aprender"), ("memorizar regra", "aprender"),
]

c = MCRCoupling()
for txt, act in corpus:
    c.alimentar(txt, act)

print("=== DIAGNÓSTICO EXP2 - Casos de erro ===")
casos_exp2 = [
    ("gere um orc forte", "criar"),
    ("produza um dragao verde", "criar"),
    ("construa uma espada", "criar"),
    ("mude o nome do npc", "editar"),
    ("troque a cor do monstro", "editar"),
    ("ache a funcao de combate", "buscar"),
    ("localize o arquivo de magia", "buscar"),
    ("ensine como fazer item", "aprender"),
    ("estude o sistema de npc", "aprender"),
    ("crie um gato que voa", "criar"),
    ("edite o look do orc", "editar"),
    ("procure o npc vendedor", "buscar"),
]

for frase, esperado in casos_exp2:
    pred, conf = c.decidir(frase, (None, 0.0))
    ok = "OK" if pred == esperado else "X"
    
    # Trace fontes
    partes = frase.replace('_', ' ').lower().split()
    
    # P0
    p0 = partes[0][:10] if partes else ""
    d_p0 = c._posicao_acao.get(f"P0:{p0}", {})
    
    # Palavras
    palavras = set(p for p in partes if len(p) >= 3)
    d_pal = {}
    for p in palavras:
        d = c._palavra_acao.get(p, {})
        if d:
            d_pal[p] = d
    
    print(f"\n{ok} \"{frase}\" | esp={esperado} pred={pred} conf={conf:.3f}")
    print(f"  P0({p0}): {dict(sorted(d_p0.items(), key=lambda x: -x[1])[:3])}")
    for p, d in d_pal.items():
        print(f"  W({p}): {dict(sorted(d.items(), key=lambda x: -x[1])[:3])}")