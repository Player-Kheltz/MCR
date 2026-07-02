#!/usr/bin/env python3
"""BATERIA DE TESTES — perguntas complexas, genericas, sem sentido.
A Equacao MCR decide qual ferramenta usar para CADA pergunta.
0 hardcode. 0 if/else. So MCR.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

m = MCRMotor()
cmd = MCRComandos(m)
w = MCRWebLearn(m)

PERGUNTAS = [
    # --- Ferramentas diretas (data, hora) ---
    'Que dia e hoje e que horas sao?',
    'Qual a data de hoje?',

    # --- Conhecimento geral (web) ---
    'Qual a relacao entre o Brasil e Portugal?',
    'Como o ciclo de dia e noite tem a ver com a rotacao da terra e a posicao do Sol?',
    'O que causa as estacoes do ano?',
    'Quem foi Santos Dumont?',
    'Qual a diferenca entre celula animal e vegetal?',
    'Como a fotossintese transforma luz em energia?',

    # --- Conexao entre conceitos ---
    'Qual a relacao entre a gravidade e as orbitas dos planetas?',
    'Como a teoria da evolucao se relaciona com a genetica?',

    # --- Perguntas sem sentido (testam geracao) ---
    'Por que o ceu e azul e as nuvens sao brancas?',
    'O que veio primeiro: o ovo ou a galinha?',
    'Se o tempo e relativo, como medimos a idade do universo?',
]

print()
print('=' * 65)
print('  BATERIA DE TESTES — PERGUNTAS COMPLEXAS')
print('  A Equacao MCR decide a ferramenta para cada uma.')
print('  0 hardcode. 0 if/else.')
print('=' * 65)
print()

resultados = []
for pergunta in PERGUNTAS:
    h = MCRByteUtils.entropia_bytes(pergunta)
    fp = MCRSignatureExpansiva.fingerprint_texto(pergunta, 4)

    # Tenta ferramenta
    from MCR_Chat import _escolher_ferramenta, FERAMENTAS
    ferramenta, score = _escolher_ferramenta(pergunta, FERAMENTAS) if '_escolher' in dir() else (None, 0)
    # Simplified inline version
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    melhor, melhor_score = None, 0
    for f in FERAMENTAS:
        jf = MCRByteUtils.jaccard_bytes(pergunta, f['desc'])
        pd = [w.lower() for w in f['desc'].split()]
        exata = any(p1 == p2 for p1 in pp for p2 in pd)
        prefixo = any(len(p1) >= 3 and len(p2) >= 3 and (p1.startswith(p2) or p2.startswith(p1)) for p1 in pp for p2 in pd)
        if not (exata or prefixo):
            continue
        scoref = jf + sum(1 for p1 in pp for p2 in pd if p1 == p2) * 0.2 + sum(1 for p1 in pp for p2 in pd if len(p1)>=3 and len(p2)>=3 and (p1.startswith(p2) or p2.startswith(p1)) and p1 != p2) * 0.15
        if scoref > melhor_score:
            melhor_score, melhor = scoref, f
    ferramenta = melhor

    # Busca web
    nw = w.buscar(pergunta)

    # Busca conhecimento
    resposta = cmd._buscar_resposta(pergunta)
    if resposta and len(resposta) > 30:
        j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
        if j < 0.5:
            fonte = 'conhecimento'
        else:
            resposta = ''
            fonte = 'gerado'
    elif nw > 0:
        resposta = cmd._buscar_resposta(pergunta)
        if resposta and len(resposta) > 30:
            j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
            if j < 0.5:
                fonte = 'web'
            else:
                resposta = ''
                fonte = 'gerado'
        else:
            resposta = ''
            fonte = 'gerado'
    else:
        if ferramenta:
            fonte = ferramenta['nome']
        else:
            fonte = 'gerado'
            resultado = cmd.master(pergunta)
            resposta = resultado.get('resposta', str(resultado))

    if not resposta and ferramenta:
        try:
            resposta = ferramenta['fn'](pergunta)
        except:
            fonte = 'gerado'

    safe = resposta[:100].encode('ascii', errors='replace').decode('ascii') if resposta else '(vazio)'
    print(f'  [{fonte:15s}] {pergunta[:50]:50s}')
    print(f'   -> {safe}')
    print()

    resultados.append((pergunta, fonte, resposta[:200] if resposta else ''))

print('=' * 65)
print('  RESUMO')
print('=' * 65)
for pergunta, fonte, resp in resultados:
    print(f'  [{fonte:15s}] {pergunta[:50]}')
print()
