#!/usr/bin/env python3
"""MCR MULTINIVEL: N dimensoes SIMULTANEAS para prever sequencias.

Cada dimensao ve um aspecto diferente dos mesmos dados.
Cada dimensao faz uma predicao.
O consenso entre dimensoes e a resposta final.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13], 'resposta': 21},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49], 'resposta': 64},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17], 'resposta': 19},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64], 'resposta': 128},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111], 'resposta': 1000},
]

def extrair_dimensoes(seq):
    """Extrai N dimensoes de uma sequencia numerica."""
    elementos = [str(x) for x in seq]
    n = len(elementos)
    
    dims = {
        'palavra': elementos,
        'comprimento': [len(e) for e in elementos],
        'primeiro_digito': [int(e[0]) for e in elementos],
        'ultimo_digito': [int(e[-1]) for e in elementos],
    }
    
    # Delta (diferenca entre consecutivos)
    if n >= 2:
        deltas = []
        for i in range(1, n):
            deltas.append(seq[i] - seq[i-1])
        dims['delta'] = deltas
    
    # Delta do delta (segunda diferenca)
    if 'delta' in dims and len(dims['delta']) >= 2:
        dd = []
        for i in range(1, len(dims['delta'])):
            dd.append(dims['delta'][i] - dims['delta'][i-1])
        dims['delta2'] = dd
    
    # RAZAO entre consecutivos (para sequencias multiplicativas)
    if n >= 2:
        razoes = []
        for i in range(1, n):
            if seq[i-1] != 0:
                razoes.append(round(seq[i] / seq[i-1], 4))
            else:
                razoes.append(0)
        dims['razao'] = razoes
    
    # SOMA dos 2 anteriores (para Fibonacci)
    if n >= 2:
        somas = []
        for i in range(2, n):
            somas.append(seq[i] - seq[i-1] - seq[i-2])
        # Se for Fibonacci, somas serao 0,0,0,0,0
        dims['soma_anterior'] = somas
    
    # Entropia de cada elemento
    entropias = []
    for e in elementos:
        h = MCRByteUtils.entropia_bytes(e.encode('utf-8'))
        entropias.append(round(h, 2))
    dims['entropia'] = entropias
    
    return dims

def treinar_markov_por_dimensao(dims):
    """Treina um Markov para CADA dimensao."""
    mks = {}
    for nome, valores in dims.items():
        if len(valores) < 2:
            continue
        mk = MCR(nome)
        # Converte valores para string
        strs = [str(v) for v in valores]
        for i in range(len(strs) - 1):
            mk.aprender(strs[i], strs[i+1])
        mks[nome] = mk
    return mks

def predizer_por_dimensao(mks, dims, ultimo_valor, seq):
    """Cada dimensao prediz o PROXIMO valor."""
    palpites = []
    
    for nome, mk in mks.items():
        if nome not in dims:
            continue
        
        # Acessa a dimensao correta para a semente
        if nome == 'palavra':
            semente = str(ultimo_valor)
        elif nome == 'delta':
            # O ultimo delta e a diferenca entre os 2 ultimos
            valores = dims['palavra']
            if len(valores) >= 2:
                ult_delta = int(valores[-1]) - int(valores[-2])
                semente = str(ult_delta)
            else:
                continue
        elif nome == 'delta2':
            vals = dims.get('delta', [])
            if len(vals) >= 2:
                semente = str(vals[-1] - vals[-2])
            else:
                continue
        elif nome == 'comprimento':
            semente = str(len(str(ultimo_valor)))
        elif nome == 'primeiro_digito':
            semente = str(str(ultimo_valor)[0])
        elif nome == 'ultimo_digito':
            semente = str(str(ultimo_valor)[-1])
        elif nome == 'entropia':
            h = MCRByteUtils.entropia_bytes(str(ultimo_valor).encode('utf-8'))
            semente = str(round(h, 2))
        elif nome == 'razao':
            if len(seq) >= 2:
                ult_razao = round(seq[-1] / seq[-2], 4) if seq[-2] != 0 else 0
                semente = str(ult_razao)
            else:
                continue
        elif nome == 'soma_anterior':
            # Para Fibonacci: seq[i] - seq[i-1] - seq[i-2] = 0
            continue  # usado apenas como verificacao, nao predicao
        else:
            continue
        
        pred, conf = mk.predizer(semente)
        if pred is not None and conf > 0:
            try:
                palpite = int(float(pred))
                palpites.append((nome, palpite, conf, mk.entropia_media()))
            except (ValueError, TypeError):
                pass
    
    return palpites

def inferir_por_dimensao_zerada(dims, seq):
    """Se uma dimensao tem valor CONSTANTE (ex: soma_anterior = 0),
    isso revela uma REGRA que pode ser usada para inferir o proximo.
    
    Ex: soma_anterior = [0,0,0,0,0] para Fibonacci
        → regra: seq[i] = seq[i-1] + seq[i-2]
        → proximo = seq[-1] + seq[-2]
    """
    if 'soma_anterior' in dims and len(dims['soma_anterior']) >= 3:
        vals = dims['soma_anterior']
        if all(v == 0 for v in vals):
            # REGRA: cada elemento e a soma dos 2 anteriores
            if len(seq) >= 2:
                return seq[-1] + seq[-2], 10.0  # peso maximo
    return None, 0.0

def converter_palpite_para_numero(nome_dimensao, palpite, ultimo_valor, seq):
    """Converte o palpite de uma dimensao para um numero candidato."""
    if nome_dimensao == 'palavra':
        return palpite
    elif nome_dimensao == 'delta':
        return ultimo_valor + palpite
    elif nome_dimensao == 'delta2':
        # O delta previsto + ultimo delta = proximo delta
        if len(seq) >= 2:
            ult_delta = seq[-1] - seq[-2]
            prox_delta = ult_delta + palpite
            return ultimo_valor + prox_delta
        return palpite
    elif nome_dimensao == 'razao':
        return ultimo_valor * palpite
    elif nome_dimensao == 'comprimento':
        return None
    elif nome_dimensao == 'primeiro_digito':
        return None
    elif nome_dimensao == 'ultimo_digito':
        return None
    return palpite

def main():
    print('=' * 70)
    print('  MCR MULTINIVEL: N dimensoes simultaneas')
    print('  Fibonacci em MULTIPLAS dimensoes:')
    print('    palavra:    1 1 2 3 5 8 13')
    print('    delta:      0 1 1 2 3 5')
    print('    comprimento:1 1 1 1 1 1 2')
    print('    1o digito:  1 1 2 3 5 8 1')
    print('    ult digito: 1 1 2 3 5 8 3')
    print('    entropia:   0 0 0 0 0 0 0.92')
    print('  CADA dimensao da um palpite.')
    print('  O consenso entre elas e a resposta.')
    print('=' * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        resposta = seq_data['resposta']
        ultimo_valor = seq[-1]

        dims = extrair_dimensoes(seq)
        mks = treinar_markov_por_dimensao(dims)
        palpites = predizer_por_dimensao(mks, dims, ultimo_valor, seq)

        print(f'  [{nome}]')
        for nome_dim, vals in dims.items():
            print(f'    {nome_dim:15s}: {vals}')

        print(f'    PALPITES:')
        candidatos_por_palpite = {}  # numero candidato -> soma de confiancas
        for nome_dim, palpite, conf, entropia in palpites:
            numero_cand = converter_palpite_para_numero(nome_dim, palpite, ultimo_valor, seq)
            if numero_cand is None:
                print(f'      {nome_dim:15s}: {palpite} (conf={conf:.3f}) -> (nao converte)')
            else:
                peso = conf * (1.0 / (entropia + 0.1))
                candidatos_por_palpite[numero_cand] = candidatos_por_palpite.get(numero_cand, 0) + peso
                print(f'      {nome_dim:15s}: {palpite} (conf={conf:.3f}, entr={entropia:.2f}) -> numero {numero_cand} (peso={peso:.3f})')

        # INFERENCIA: alguma dimensao revelou uma REGRA?
        cand_inferido, conf_inferido = inferir_por_dimensao_zerada(dims, seq)
        if cand_inferido is not None:
            print(f'      INFERIDO por regra constante: {cand_inferido} (peso={conf_inferido:.1f})')
            candidatos_por_palpite[cand_inferido] = \
                candidatos_por_palpite.get(cand_inferido, 0) + conf_inferido

        # Consenso: o candidato com maior peso total
        if candidatos_por_palpite:
            melhor_cand = max(candidatos_por_palpite, key=candidatos_por_palpite.get)
            conf_total = candidatos_por_palpite[melhor_cand]
        else:
            melhor_cand = 0
            conf_total = 0

        acertou = (melhor_cand == resposta)
        status = 'SIM' if acertou else 'NAO'
        print(f'    CONSENSO: {melhor_cand} (conf_total={conf_total:.3f})  {status}')
        print(f'    ESPERADO: {resposta}')
        print()

        if acertou:
            acertos += 1

    print(f'  RESULTADO: {acertos}/{len(SEQUENCIAS)}')
    print()
    if acertos >= 3:
        print('  MCR MULTINIVEL descobriu as sequencias!')
        print('  N dimensoes simultaneas > qualquer dimensao isolada.')
    elif acertos >= 1:
        print('  Algumas acertaram. O multinivel ajuda mas nao resolve tudo.')
    else:
        print('  Mesmo com N dimensoes, MCR nao descobriu as sequencias.')
        print('  As dimensoes disponiveis ainda nao carregam a relacao aritmetica.')
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
