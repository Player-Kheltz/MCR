#!/usr/bin/env python3
"""BATERIA INTENSIVA — testa ferramentas e respostas."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *
from MCR import _EQUACAO_ATUAL

# Mesma logica do MCR_Chat
def _escolher_ferramenta(pergunta, FERAMENTAS):
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    melhor, melhor_score = None, 0
    for f in FERAMENTAS:
        j = MCRByteUtils.jaccard_bytes(pergunta, f['desc'])
        pd = [w.lower() for w in f['desc'].split()]
        exata = any(p1 == p2 for p1 in pp for p2 in pd)
        prefixo = any(len(p1) >= 3 and len(p2) >= 3 and (p1.startswith(p2) or p2.startswith(p1)) for p1 in pp for p2 in pd)
        if not (exata or prefixo):
            continue
        score = j + sum(1 for p1 in pp for p2 in pd if p1 == p2) * 0.2 + sum(1 for p1 in pp for p2 in pd if len(p1)>=3 and len(p2)>=3 and (p1.startswith(p2) or p2.startswith(p1)) and p1 != p2) * 0.15
        if score > melhor_score:
            melhor_score, melhor = score, f
    return melhor if melhor_score > 0.2 else None, round(melhor_score, 3) if melhor else 0

FERAMENTAS = [
    {'nome': 'data', 'desc': 'responder data hoje dia mes ano calendario'},
    {'nome': 'hora', 'desc': 'responder hora atual minuto segundo relogio'},
    {'nome': 'lista_arquivos', 'desc': 'enumerar listar mostrar arquivos pasta diretorio'},
    {'nome': 'buscar_texto', 'desc': 'encontrar achar localizar palavra texto arquivos'},
]

TESTES = [
    ('que dia e hoje',      'data'),
    ('que horas sao',       'hora'),
    ('qual a data de hoje', 'data'),
    ('me diga as horas',    'hora'),
    ('qual a hora atual',   'hora'),
    ('me diga a data',      'data'),
    ('que dia e hoje?',     'data'),
    ('que horas sao agora', 'hora'),
]

print()
print('= ' * 35)
print('  BATERIA INTENSIVA DE TESTES')
print('= ' * 35)
print()

acertos = 0
for pergunta, esperado in TESTES:
    ferramenta, score = _escolher_ferramenta(pergunta, FERAMENTAS)
    nome_ferr = ferramenta['nome'] if ferramenta else 'nenhuma'
    acertou = nome_ferr == esperado
    status = 'PASSOU' if acertou else 'FALHOU'
    marcador = '+' if acertou else '-'
    if acertou:
        acertos += 1
    print(f'  [{marcador}] {pergunta:30s} -> {nome_ferr:10s} (score={score:.3f}) {status}')

print()
print(f'  RESULTADO: {acertos}/{len(TESTES)}')
print()

# Diagnostico de matching
print('  DIAGNOSTICO DETALHADO:')
print()
for pergunta in ['que horas sao', 'me diga as horas', 'qual a hora', 'o horario', 'que dia e hoje', 'me diga a data']:
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    print(f'  "{pergunta}":')
    for f in FERAMENTAS:
        j = MCRByteUtils.jaccard_bytes(pergunta, f['desc'])
        pd = [w.lower() for w in f['desc'].split()]
        exata = any(p1 == p2 for p1 in pp for p2 in pd)
        prefixo = any(len(p1) >= 3 and len(p2) >= 3 and (p1.startswith(p2) or p2.startswith(p1)) for p1 in pp for p2 in pd)
        if exata or prefixo:
            score = j + sum(1 for p1 in pp for p2 in pd if p1 == p2) * 0.2 + sum(1 for p1 in pp for p2 in pd if len(p1)>=3 and len(p2)>=3 and (p1.startswith(p2) or p2.startswith(p1)) and p1 != p2) * 0.15
            print(f'    {f["nome"]:12s} j={j:.3f} exata={exata} prefixo={prefixo} score={score:.3f}')
    print()
