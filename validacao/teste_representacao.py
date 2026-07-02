#!/usr/bin/env python3
"""MCR descobre a MELHOR REPRESENTACAO de uma sequencia pela ENTROPIA.

Nao ha 'delta2' ou 'razao' fixos. Nao ha conversao.
O MCR gera N representacoes, a de menor entropia vence,
e a predicao e feita nela — diretamente, sem conversao.
"""
import sys, os, math, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13], 'resposta': 21},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49], 'resposta': 64},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17], 'resposta': 19},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64], 'resposta': 128},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111], 'resposta': 1000},
]

def gerar_representacoes(seq):
    """Gera N representacoes diferentes da mesma sequencia.
    
    Cada representacao e um modo diferente de OLHAR os mesmos dados.
    O MCR escolhe a de menor entropia — ponto.
    """
    s = [str(x) for x in seq]
    rep = {}

    # R0: bruta
    rep['bruta'] = ' '.join(s)

    # R1: bruta + deltas (diferencas entre consecutivos)
    if len(seq) >= 2:
        deltas = [seq[i] - seq[i-1] for i in range(1, len(seq))]
        rep['deltas'] = ' '.join(s) + ' | ' + ' '.join(str(d) for d in deltas)

    # R2: deltas + delta2
    if len(seq) >= 3:
        deltas = [seq[i] - seq[i-1] for i in range(1, len(seq))]
        dd = [deltas[i] - deltas[i-1] for i in range(1, len(deltas))]
        rep['deltas2'] = ' '.join(s) + ' | ' + ' '.join(str(d) for d in deltas) + ' | ' + ' '.join(str(d) for d in dd)

    # R3: operacoes (cada transicao como operacao)
    ops = [s[0]]
    for i in range(1, len(seq)):
        diff = seq[i] - seq[i-1]
        if diff >= 0:
            ops.append(f'+{diff}={s[i]}')
        else:
            ops.append(f'{diff}={s[i]}')
    rep['operacoes'] = ' '.join(ops)

    # R6: sequencia linear de operacoes (sem espacos)
    # "1+0=1+1=2+1=3+2=5+3=8+5=13"
    # Tokens sao CARACTERES, nao palavras — + e = se repetem
    linear = s[0]
    for i in range(1, len(seq)):
        diff = seq[i] - seq[i-1]
        if diff >= 0:
            linear += f'+{diff}={s[i]}'
        else:
            linear += f'{diff}={s[i]}'
    rep['linear_ops'] = linear

    # R7: linear de razoes
    # "1x2=2x2=4x2=8x2=16x2=32x2=64"
    if len(seq) >= 2:
        linear_r = s[0]
        for i in range(1, len(seq)):
            if seq[i-1] != 0:
                razao_arred = round(seq[i] / seq[i-1], 1)
                linear_r += f'x{razao_arred}={s[i]}'
        rep['linear_razoes'] = linear_r

    # R4: razoes
    if len(seq) >= 2:
        razoes = []
        for i in range(1, len(seq)):
            if seq[i-1] != 0:
                razoes.append(round(seq[i] / seq[i-1], 2))
        rep['razoes'] = ' '.join(s) + ' | x ' + ' '.join(str(r) for r in razoes)

    # R5: digitos separados
    digitos = []
    for num in s:
        digitos.extend(list(num))
    rep['digitos'] = ' '.join(digitos)

    return rep

def escolher_melhor_representacao(rep, ultimo_valor):
    """Escolhe a representacao que produz a PREDICAO MAIS CONFIANTE.
    
    Treina Markov em cada representacao, tenta predizer o proximo,
    e a que tiver MAIOR confianca na predicao vence.
    Sem if/else. Sem conhecimento humano.
    """
    melhores = []
    for nome, texto in rep.items():
        dados = texto.encode('utf-8')
        h = MCRByteUtils.entropia_bytes(dados)
        fp = MCRSignatureExpansiva.fingerprint(dados, 8)
        
        # Treina Markov
        mk = MCR(nome)
        tokens = texto.split()
        for i in range(len(tokens) - 1):
            mk.aprender(tokens[i], tokens[i+1])
        
        # Tenta predizer
        if not tokens:
            continue
        pred, conf = mk.predizer(tokens[-1])
        
        # Quanto maior confianca, melhor a representacao capta o padrao
        # Entropia baixa e bonus
        score = conf * 10 - h * 0.1
        melhores.append((score, conf, nome, texto, h, pred))

    melhores.sort(key=lambda x: -x[0])
    return melhores[0] if melhores else (0, 0, 'bruta', rep.get('bruta', ''), 0, None)

def prever_da_representacao(texto, nome_rep, ultimo_valor):
    """Faz a predicao DIRETAMENTE na representacao escolhida.
    
    Nao ha conversao. Se a representacao contem '=21' e o padrao
    diz que o proximo e '=34', extrai-se o 34.
    Nao ha if/else. A predicao e Markov puro na representacao.
    """
    mk = MCR(nome_rep)
    tokens = texto.split()
    for i in range(len(tokens) - 1):
        mk.aprender(tokens[i], tokens[i+1])

    if not tokens:
        return 0, 0

    ultimo_token = tokens[-1]
    pred, conf = mk.predizer(ultimo_token)

    if pred is None or conf < 0.01:
        return 0, 0

    # Extrai numero do token previsto (se contem numeros)
    import re as _re
    nums = _re.findall(r'\d+', str(pred))
    if nums:
        palpite = int(nums[-1])
        return palpite, round(conf, 3)

    return 0, 0

def main():
    print('=' * 70)
    print('  MCR: SELECAO NATURAL DE REPRESENTACOES')
    print('  Cada sequencia vira N representacoes.')
    print('  A de MENOR entropia vence.')
    print('  A predicao e feita DIRETAMENTE nela — sem conversao.')
    print('=' * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        resposta = seq_data['resposta']

        rep = gerar_representacoes(seq)

        print(f'  [{nome}]')
        for nome_rep, texto in sorted(rep.items()):
            dados = texto.encode('utf-8')
            h = MCRByteUtils.entropia_bytes(dados)
            fp = MCRSignatureExpansiva.fingerprint(dados, 8)
            h_fp = MCRSignatureExpansiva.entropia_fingerprint(fp)
            print(f'    {nome_rep:15s} H={h:.3f} Hfp={h_fp:.3f} | {texto[:70]}')

        melhor = escolher_melhor_representacao(rep, seq[-1])
        score_total, conf_pred, nome_vencedor, texto_vencedor, h, pred = melhor

        print(f'    VENCEDOR: {nome_vencedor} (conf_pred={conf_pred:.3f}, H={h:.3f})')

        # Prediz DIRETAMENTE na representacao vencedora
        palpite, conf = prever_da_representacao(texto_vencedor, nome_vencedor, seq[-1])
        acertou = (palpite == resposta)
        status = 'SIM' if acertou else 'NAO'
        print(f'    PREDITO: {palpite} (conf={conf})  ESPERADO: {resposta}  {status}')
        print()

        if acertou:
            acertos += 1

    print(f'  RESULTADO: {acertos}/{len(SEQUENCIAS)}')
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
