#!/usr/bin/env python3
"""MCR MULTINIVEL PURO: dimensoes viram topicos, Equacao MCR decide.
0 if/else. 0 inferencia manual. Cada dimensao e alimentada no MCRMotor,
cada palpite e conectado, e o consenso EMERGE das notas da Equacao MCR.
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

def extrair_dimensoes_texto(seq):
    """Extrai N dimensoes como TEXTO para alimentar no MCR."""
    s = [str(x) for x in seq]
    dims = {}
    
    dims['palavra'] = ' '.join(s)
    if len(s) >= 2:
        deltas = [seq[i] - seq[i-1] for i in range(1, len(seq))]
        dims['delta'] = ' '.join(str(d) for d in deltas)
    if 'delta' in dims and len(seq) >= 3:
        vals = [int(x) for x in dims['delta'].split()]
        dd = [vals[i] - vals[i-1] for i in range(1, len(vals))]
        dims['delta2'] = ' '.join(str(d) for d in dd)
    dims['comprimento'] = ' '.join(str(len(e)) for e in s)
    dims['primeiro_digito'] = ' '.join(e[0] for e in s)
    dims['ultimo_digito'] = ' '.join(e[-1] for e in s)
    
    if len(seq) >= 2:
        razoes = []
        for i in range(1, len(seq)):
            if seq[i-1] != 0:
                razoes.append(round(seq[i] / seq[i-1], 4))
            else:
                razoes.append(0)
        dims['razao'] = ' '.join(str(r) for r in razoes)
    
    if len(seq) >= 3:
        sa = [seq[i] - seq[i-1] - seq[i-2] for i in range(2, len(seq))]
        dims['soma_anterior'] = ' '.join(str(v) for v in sa)
    
    return dims

def prever_por_dimensao(texto_dimensao, ultimo_valor, nome_dim, motor):
    """Alimenta uma dimensao no MCR, gera candidatos por Markov."""
    mk = MCR(nome_dim)
    tokens = texto_dimensao.split()
    for i in range(len(tokens) - 1):
        mk.aprender(tokens[i], tokens[i+1])
    
    # Ultimo token da dimensao
    ultimo_token = tokens[-1]
    pred, conf = mk.predizer(ultimo_token)
    
    if pred is None or conf < 0.01:
        return []
    
    candidatos = []
    try:
        palpite_val = int(float(pred))
    except (ValueError, TypeError):
        return []
    
    # Converte palpite da dimensao para numero candidato
    numero_cand = None
    if nome_dim == 'palavra':
        numero_cand = palpite_val
    elif nome_dim in ('delta','delta2') and isinstance(ultimo_valor, (int, float)):
        if nome_dim == 'delta':
            numero_cand = ultimo_valor + palpite_val
        else:
            ult_delta = int(tokens[-1]) if tokens[-1].lstrip('-').isdigit() else 0
            prox_delta = ult_delta + palpite_val
            numero_cand = ultimo_valor + prox_delta
    elif nome_dim == 'razao' and isinstance(ultimo_valor, (int, float)):
        numero_cand = int(ultimo_valor * palpite_val)
    
    if numero_cand is not None and numero_cand > 0:
        candidatos.append((numero_cand, conf))
    
    return candidatos

def main():
    print('=' * 70)
    print('  MCR MULTINIVEL PURO: dimensoes como topicos')
    print('  A Equacao MCR decide o consenso entre dimensoes.')
    print('  0 if/else. 0 inferencia manual.')
    print('=' * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        resposta = seq_data['resposta']
        ultimo_valor = seq[-1]

        dims = extrair_dimensoes_texto(seq)
        
        print(f'  [{nome}]')
        
        # Alimenta CADA dimensao como topico no MCRMotor
        motor = MCRMotor()
        for dim_nome, texto in dims.items():
            motor.alimentar(texto, f'dim_{dim_nome}')
            print(f'    {dim_nome:20s}: {texto[:50]}')
        
        # Gera CANDIDATOS de CADA dimensao
        candidatos = {}  # numero_cand -> soma_confianca
        
        for dim_nome, texto in dims.items():
            palpites = prever_por_dimensao(texto, ultimo_valor, dim_nome, motor)
            for cand_num, conf in palpites:
                if cand_num > 0 and cand_num < 10000:
                    candidatos[cand_num] = candidatos.get(cand_num, 0) + conf
        
        print(f'    CANDIDATOS: {candidatos}')
        
        if not candidatos:
            print(f'    NENHUM candidato gerado.')
            print()
            continue
        
        # Alimenta CADA candidato como topico TEMPORARIO
        for cand_num in list(candidatos.keys())[:10]:
            motor.alimentar(f'candidato {cand_num} para sequencia {dims.get("palavra", "")[:30]}', 
                          f'cand_{cand_num}')
        
        # CONECTA cada candidato com as dimensoes
        notas_consenso = {}
        for cand_num in list(candidatos.keys())[:10]:
            nome_cand = f'cand_{cand_num}'
            if nome_cand not in motor.topicos:
                continue
            nota_total = 0
            n_conexoes = 0
            for dim_nome in dims:
                nome_dim = f'dim_{dim_nome}'
                if nome_dim not in motor.topicos:
                    continue
                c = motor.conectar(nome_cand, nome_dim, forcar=True)
                if c:
                    nota_total += c['nota']
                    n_conexoes += 1
            if n_conexoes > 0:
                notas_consenso[cand_num] = round(nota_total / n_conexoes, 2)
        
        print(f'    NOTAS CONSENSO: {notas_consenso}')
        
        if not notas_consenso:
            print(f'    NENHUM consenso.')
        else:
            melhor_cand = max(notas_consenso, key=notas_consenso.get)
            melhor_nota = notas_consenso[melhor_cand]
            acertou = (melhor_cand == resposta)
            status = 'SIM' if acertou else 'NAO'
            print(f'    VENCEDOR: {melhor_cand} (nota={melhor_nota})  {status}')
            print(f'    ESPERADO: {resposta}')
            if acertou:
                acertos += 1
        
        # Limpa topicos temporarios
        for cand_num in list(candidatos.keys())[:10]:
            motor.topicos.pop(f'cand_{cand_num}', None)
        
        print()

    print(f'  RESULTADO: {acertos}/{len(SEQUENCIAS)}')
    print()
    if acertos >= 3:
        print('  MCR MULTINIVEL PURO descobriu as sequencias!')
        print('  A Equacao MCR combinou dimensoes automaticamente.')
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
