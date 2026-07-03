#!/usr/bin/env python3
"""MCR descobre sequencias por PADRAO TEXTUAL das transicoes.

O MCR nao sabe o que sao numeros.
Ele ve TEXTO: '1', '10', '11', '100'...
O padrao esta nas TRANSFORMACOES TEXTUAIS:
  - comprimento da string aumenta?
  - conjunto de caracteres muda?
  - primeiro caractere se mantem?
  - ultimo caractere alterna?

O MCR aprende o padrao destas TRANSFORMACOES e aplica.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from collections import Counter
from MCR import *

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13, 21], 'prox': 34},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49, 64], 'prox': 81},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17, 19], 'prox': 23},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64, 128], 'prox': 256},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111, 1000], 'prox': 1001},
]

def extrair_transformacoes(elementos):
    """Extrai as TRANSFORMACOES TEXTUAIS entre elementos consecutivos.
    
    Cada transformacao e um dict com propriedades visiveis em bytes.
    """
    transfs = []
    for i in range(len(elementos) - 1):
        a = str(elementos[i])
        b = str(elementos[i + 1])
        transfs.append({
            'a': a,
            'b': b,
            'len_a': len(a),
            'len_b': len(b),
            'diferenca_len': len(b) - len(a),
            'primeiro_a': a[0] if a else '',
            'primeiro_b': b[0] if b else '',
            'ultimo_a': a[-1] if a else '',
            'ultimo_b': b[-1] if b else '',
            'chars_a': set(a),
            'chars_b': set(b),
            'jaccard_transicao': MCRByteUtils.jaccard_bytes(a, b),
        })
    return transfs

def prever_proximo(transfs, ultimo_elemento, elementos_conhecidos):
    """Preve o proximo elemento baseado nas transformacoes anteriores.
    
    1. Analisa o padrao das transformacoes
    2. Gera candidatos por extrapolacao dos padroes
    3. Escolhe o candidato MAIS CONSISTENTE com as transformacoes anteriores
    """
    ultimo = str(ultimo_elemento)
    candidatos = []

    # Padrao 1: comprimento medio das strings
    comprimentos = [t['len_b'] for t in transfs]
    comp_medio = sum(comprimentos) / max(len(comprimentos), 1)

    # Padrao 2: primeiros caracteres
    primeiros = [t['primeiro_b'] for t in transfs]
    primeiro_mais_comum = Counter(primeiros).most_common(1)[0][0]

    # Padrao 3: ultimos caracteres  
    ultimos = [t['ultimo_b'] for t in transfs]
    ultimo_mais_comum = Counter(ultimos).most_common(1)[0][0]

    # Padrao 4: caracteres usados
    todos_chars = set()
    for t in transfs:
        todos_chars.update(t['chars_b'])

    # Padrao 5: diferenca de comprimento
    diffs = [t['diferenca_len'] for t in transfs]
    diff_mais_comum = Counter(diffs).most_common(1)[0][0] if diffs else 0

    # Analisa padrao do ULTIMO caractere (alternancia?)
    ultimos = [t['ultimo_b'] for t in transfs]
    # Verifica se ha alternancia (0,1,0,1,0,1...)
    alterna = True
    for i in range(1, len(ultimos)):
        if ultimos[i] == ultimos[i-1]:
            alterna = False
            break
    
    # Preve o proximo ultimo caractere por alternancia ou moda
    if alterna and len(ultimos) >= 2:
        ultimo_previsto = ultimos[0] if len(ultimos) % 2 == 0 else ultimos[1]
    else:
        ultimo_previsto = ultimo_mais_comum
    
    # Analisa padrao de COMPRIMENTO (quando adiciona digito?)
    diffs = [t['diferenca_len'] for t in transfs]
    diff_mais_comum = Counter(diffs).most_common(1)[0][0] if diffs else 0

    # Verifica se ha padrao ciclico nos comprimentos
    len_atual = len(ultimo)
    len_previsto = len_atual + diff_mais_comum
    
    # Se diffs alternam entre +1 e 0, preve o proximo
    diffs_sem_zero = [d for d in diffs if d != 0]
    if diffs_sem_zero:
        # Tenta detectar periodicidade: a cada quantos passos adiciona digito?
        ultimo_digito_adicionado = -1
        for i, d in enumerate(diffs):
            if d > 0:
                ultimo_digito_adicionado = i
        
        if ultimo_digito_adicionado >= 0:
            passos_desde = len(diffs) - 1 - ultimo_digito_adicionado
            if passos_desde >= 3:  # ja passaram 3+ passos sem adicionar
                len_previsto = len_atual + 1

    for cand_num in range(1, 5000):
        cand = str(cand_num)
        if cand in [str(x) for x in elementos_conhecidos]:
            continue  # exclui elementos ja vistos
        
        score = 0.0
        
        # Primeiro caractere consistente?
        if len(cand) > 0 and cand[0] == primeiro_mais_comum:
            score += 3.0
        
        # Comprimento previsto?
        if len(cand) == len_previsto:
            score += 3.0
        elif abs(len(cand) - len_previsto) <= 1:
            score += 1.0
        
        # Caracteres dentro do conjunto observado?
        if set(cand).issubset(todos_chars):
            score += 2.0
        
        # Ultimo caractere previsto (alternancia)?
        if len(cand) > 0 and cand[-1] == ultimo_previsto:
            score += 2.0
        
        # Proximidade de byte com o ultimo elemento
        j = MCRByteUtils.jaccard_bytes(ultimo, cand)
        score += j * 2.0
        
        if score > 0:
            candidatos.append((round(score, 2), cand_num))
    
    if not candidatos:
        return 0, 0

    candidatos.sort(key=lambda x: -x[0])
    return candidatos[0][1], candidatos[0][0]

def main():
    print("=" * 70)
    print("  MCR DESCOBRE SEQUENCIAS POR TRANSFORMACOES TEXTUAIS")
    print("  0 matematica. 0 numeros. So padroes de TEXTO.")
    print()
    print("  O MCR ve elementos como STRINGS, nao como numeros.")
    print("  '1000' e '1001' sao diferentes comprimentos, chars, primeiro/ultimo.")
    print("=" * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        esperado_str = str(seq_data['prox'])

        conhecidos = seq[:7]
        oculto = seq[7]

        transforms = extrair_transformacoes(conhecidos)

        palpite, confianca = prever_proximo(transforms, conhecidos[-1], conhecidos)
        palpite_str = str(palpite)
        esperado_str = str(oculto)

        acertou = palpite == oculto

        print(f"  [{nome:12s}]")
        print(f"    Conhecidos: {' '.join(str(x) for x in conhecidos)}")
        print(f"    Esperado:   {esperado_str}")
        print(f"    MCR disse:  {palpite_str} (conf={confianca}) {'SIM!' if acertou else 'NAO'}")
        
        # Mostra as transformacoes detectadas
        print(f"    Transformacoes:")
        for t in transforms:
            d = '+' if t['diferenca_len'] >= 0 else ''
            print(f"      {t['a']:4s} -> {t['b']:4s} (len:{d}{t['diferenca_len']} 1o:{t['primeiro_b']} ult:{t['ultimo_b']})")
        
        print()
        if acertou:
            acertos += 1

    print("=" * 70)
    print(f"  RESULTADO: {acertos}/{len(SEQUENCIAS)}")
    print()
    if acertos >= 3:
        print("  O MCR descobriu as sequencias por PADRAO TEXTUAL!")
    elif acertos >= 1:
        print("  O MCR descobriu algumas. As TRANSFORMACOES TEXTUAIS funcionam.")
    else:
        print("  Mesmo por transformacoes textuais, o MCR nao acertou nenhuma.")
        print("  O padrao nao esta em primeiro/ultimo caractere ou comprimento.")
    print()
    return 0

if __name__ == '__main__':
    sys.exit(main())
