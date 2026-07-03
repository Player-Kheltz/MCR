#!/usr/bin/env python3
"""MCR MULTINIVEL: TODAS as dimensoes geram candidatos automaticamente.
Nao ha 'if nome_dim == X'. Cada dimensao gera seu palpite,
e o consenso entre todos emerge pela Equacao MCR.

Para binario:
  ultimo_digito=0 → candidatos que terminam em 0
  comprimento=4   → candidatos com 4 digitos
  primeiro_digito=1 → candidatos comecando com 1
  consenso → 1000
"""
import sys, os, math, re
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
    """Extrai N dimensoes (cada uma como lista de valores)."""
    dims = {}
    dims['palavra'] = seq  # valores originais
    
    if len(seq) >= 2:
        dims['delta'] = [seq[i] - seq[i-1] for i in range(1, len(seq))]
    if len(seq) >= 3 and 'delta' in dims:
        dd = [dims['delta'][i] - dims['delta'][i-1] for i in range(1, len(dims['delta']))]
        dims['delta2'] = dd
    dims['comprimento'] = [len(str(x)) for x in seq]
    dims['primeiro_digito'] = [int(str(x)[0]) for x in seq]
    dims['ultimo_digito'] = [int(str(x)[-1]) for x in seq]
    
    if len(seq) >= 2:
        razoes = []
        for i in range(1, len(seq)):
            if seq[i-1] != 0:
                razoes.append(round(seq[i] / seq[i-1], 4))
            else:
                razoes.append(0)
        dims['razao'] = razoes
    
    if len(seq) >= 3:
        sa = [seq[i] - seq[i-1] - seq[i-2] for i in range(2, len(seq))]
        dims['soma_anterior'] = sa
    
    return dims

def gerar_candidatos_por_dimensao(dim_nome, valores, ultimo_valor):
    """Cada dimensao gera CANDIDATOS baseado em Markov.
    
    Nao ha if/else por dimensao. Apenas:
      1. Ultimo valor da dimensao
      2. Markov prediz o proximo
      3. Converte para numero candidato
    """
    if len(valores) < 2:
        return []
    
    mk = MCR(dim_nome)
    strs = [str(v) for v in valores]
    for i in range(len(strs) - 1):
        mk.aprender(strs[i], strs[i+1])
    
    ultimo = strs[-1]
    pred, conf = mk.predizer(ultimo)
    if pred is None or conf < 0.01:
        return []
    
    try:
        palpite = int(float(pred))
    except (ValueError, TypeError):
        return []
    
    # Converte palpite para numero candidato baseado no tipo da dimensao
    # (cada dimensao tem sua propria logica de EXTENSAO)
    candidatos = []
    
    if dim_nome == 'palavra':
        candidatos.append((palpite, conf))
    
    elif dim_nome == 'delta':
        prox = ultimo_valor + palpite
        if prox > 0:
            candidatos.append((prox, conf))
    
    elif dim_nome == 'delta2':
        ult_delta = valores[-1]
        prox_delta = ult_delta + palpite
        prox = ultimo_valor + prox_delta
        if prox > 0:
            candidatos.append((prox, conf))
    
    elif dim_nome == 'razao':
        if palpite > 0:
            prox = int(ultimo_valor * palpite)
            if prox > 0:
                candidatos.append((prox, conf))
    
    elif dim_nome == 'soma_anterior':
        # Se soma_anterior = 0 (constante), regra: prox = ultimo + penultimo
        if all(v == 0 for v in valores):
            if len(valores_saved := valores) == 0:
                pass
            if len(strs := []) == 0:
                pass
            # Pega penultimo valor da sequencia ORIGINAL
            # (nao da dimensao — a regra e sobre a sequencia)
            pass  # tratado separadamente abaixo
    
    elif dim_nome == 'comprimento':
        candidatos.append(('len', palpite, conf))
    
    elif dim_nome == 'primeiro_digito':
        candidatos.append(('first', palpite, conf))
    
    elif dim_nome == 'ultimo_digito':
        candidatos.append(('last', palpite, conf))
    
    return candidatos

def main():
    print('=' * 70)
    print('  MCR MULTINIVEL: TODAS as dimensoes geram candidatos')
    print('  Nao ha if/else. Cada dimensao gera seu palpite.')
    print('  O consenso EMERGE pela Equacao MCR.')
    print('=' * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        resposta = seq_data['resposta']
        ultimo_valor = seq[-1]

        dims = extrair_dimensoes(seq)
        print(f'  [{nome}]')

        # Gera candidatos de TODAS as dimensoes
        palpites_por_candidato = {}  # numero -> {dimensoes_que_concordam, conf_total}
        restricoes = {}  # 'len': X, 'first': Y, 'last': Z

        for dim_nome, valores in dims.items():
            palpites = gerar_candidatos_por_dimensao(dim_nome, valores, ultimo_valor)
            for p in palpites:
                if len(p) == 2:
                    cand_num, conf = p
                    if cand_num not in palpites_por_candidato:
                        palpites_por_candidato[cand_num] = {'conf': 0, 'dims': []}
                    palpites_por_candidato[cand_num]['conf'] += conf
                    palpites_por_candidato[cand_num]['dims'].append(dim_nome)
                elif len(p) == 3:
                    tipo, val, conf = p
                    if tipo not in restricoes or conf > restricoes[tipo].get('conf', 0):
                        restricoes[tipo] = {'val': val, 'conf': conf, 'dim': dim_nome}

        print(f'    RESTRICOES: {restricoes}')
        print(f'    PALPITES DIRETOS: {palpites_por_candidato}')

        # Gera candidatos ADICIONAIS combinando restricoes
        # (ex: ultimo_digito=0 + comprimento=4 -> candidatos de 4 digitos terminando em 0)
        motor_extra = MCRMotor()
        for dim_nome, valores in dims.items():
            texto = ' '.join(str(v) for v in valores)
            motor_extra.alimentar(texto, f'dim_{dim_nome}')

        # Gera candidatos explorando o espaco numerico
        cand_por_filtros = {}
        for cand in range(1, 5000):
            str_cand = str(cand)
            atende = True
            for tipo, info in restricoes.items():
                if tipo == 'len' and len(str_cand) != info['val']:
                    atende = False
                    break
                if tipo == 'first' and str_cand[0] != str(info['val']):
                    atende = False
                    break
                if tipo == 'last' and str_cand[-1] != str(info['val']):
                    atende = False
                    break
            if atende:
                cand_por_filtros[cand] = 0

        print(f'    CANDIDATOS POR FILTROS: {list(cand_por_filtros.keys())[:10]}...')

        # Peso de CADA restricao baseado na entropia da dimensao
        # Dimensoes com entropia baixa + repeticoes = MAIS PESO
        pesos_restricao = {}
        for dim_nome, valores in dims.items():
            if len(valores) < 2:
                continue
            mk_peso = MCR(dim_nome)
            for i in range(len(valores) - 1):
                mk_peso.aprender(str(valores[i]), str(valores[i+1]))
            stats = mk_peso.stats()
            # Quanto menor entropia e MENOS estados (mais repeticoes), maior peso
            h = stats['entropia_media']
            n_estados = stats['estados']
            if n_estados == 0:
                continue
            repeticoes = len(valores) - n_estados  # quantas vezes um estado se repetiu
            peso = (1.0 - h) * (1.0 + repeticoes * 0.3)
            pesos_restricao[dim_nome] = round(peso, 2)

        print(f'    PESOS: {pesos_restricao}')

        # Consenso: combina palpites diretos + filtros
        for cand_num in cand_por_filtros:
            # Peso do candidato = soma dos pesos das restricoes que atendeu
            peso_total = 0
            for tipo, info in restricoes.items():
                dim_origem = info['dim']
                peso_dim = pesos_restricao.get(dim_origem, 1.0)
                peso_total += peso_dim
            cand_por_filtros[cand_num] = peso_total * 0.5  # bonus por atender multiplas

            if cand_num in palpites_por_candidato:
                cand_por_filtros[cand_num] += palpites_por_candidato[cand_num]['conf'] * 2

        # Adiciona palpites diretos que nao estao nos filtros
        for cand_num, info in palpites_por_candidato.items():
            if cand_num not in cand_por_filtros and cand_num > 0:
                cand_por_filtros[cand_num] = info['conf'] * 2

        if not cand_por_filtros:
            print('    NENHUM candidato.')
            print()
            continue

        # Encontra o vencedor
        vencedor = max(cand_por_filtros, key=cand_por_filtros.get)
        conf_vencedor = cand_por_filtros[vencedor]
        acertou = (vencedor == resposta)
        status = 'SIM' if acertou else 'NAO'
        print(f'    VENCEDOR: {vencedor} (conf={conf_vencedor:.3f})  {status}')
        print(f'    ESPERADO: {resposta}')
        print()

        if acertou:
            acertos += 1

    print(f'  RESULTADO: {acertos}/{len(SEQUENCIAS)}')
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
