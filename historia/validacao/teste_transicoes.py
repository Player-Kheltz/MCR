#!/usr/bin/env python3
"""TESTE: MCR descobre sequencias por TRANSICOES entre elementos.

O MCR nao olha a sequencia como texto estatico.
Ele aprende as TRANSICOES entre elementos consecutivos.

Para Fibonacci: transicoes sao 1->1, 1->2, 2->3, 3->5, 5->8, 8->13
O MCR aprende estas transicoes e pergunta: 
  "qual a transicao MAIS PROVAVEL a partir de 13?"
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13, 21], 'prox': 34},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49, 64], 'prox': 81},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17, 19], 'prox': 23},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64, 128], 'prox': 256},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111, 1000], 'prox': 1001},
]

def main():
    print("=" * 70)
    print("  MCR DESCOBRE SEQUENCIAS POR TRANSICOES (MARKOV)")
    print("  0 hardcode. 0 matematica. So Equacao MCR.")
    print()
    print("  Fluxo:")
    print("  1. Alimenta transicoes entre elementos consecutivos")
    print("  2. Markov aprende: dado X, qual Y vem depois?")
    print("  3. Prediz o proximo: dado ultimo, qual o PROXIMO?")
    print("=" * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        esperado = seq_data['prox']

        conhecidos = seq[:7]
        oculto = seq[7]

        # Alimenta TRANSICOES no MCR (nao a sequencia inteira)
        mk = MCR(nome)
        for i in range(len(conhecidos) - 1):
            mk.aprender(str(conhecidos[i]), str(conhecidos[i+1]))

        # Prediz: dado o ultimo conhecido, qual o proximo?
        ultimo = str(conhecidos[-1])
        pred, conf = mk.predizer(ultimo)
        palpite = int(pred) if pred else 0

        # Tenta multiplos passos (transicoes em cadeia)
        palpite_extra = palpite
        cadeia = [conhecidos[-1]]
        if conf > 0.1:
            cadeia_completa = mk.gerar(ultimo, passos=3)
            cadeia = [int(x) for x in cadeia_completa if x.isdigit() or (x[0] == '-' and x[1:].isdigit())]
            if len(cadeia) >= 2:
                palpite_extra = cadeia[1] if len(cadeia) > 1 else cadeia[0]

        acertou = (palpite == esperado) or (palpite_extra == esperado)
        
        # Verifica tambem por jaccard entre a transicao prevista e as reais
        # Se a ultima transicao foi conhecidos[-2] -> conhecidos[-1]
        # A proxima deve ser similar
        ultima_transicao = f"{conhecidos[-2]}->{conhecidos[-1]}"
        proxima_transicao_real = f"{conhecidos[-1]}->{oculto}"
        proxima_transicao_predita = f"{conhecidos[-1]}->{palpite}"

        j_transicao = MCRByteUtils.jaccard_bytes(proxima_transicao_predita, 
                                                  proxima_transicao_real)

        print(f"  [{nome:12s}]")
        print(f"    Markov: {mk.stats()}")
        print(f"    Ultimo: {ultimo}")
        print(f"    Predito: {palpite} (conf={conf:.3f})")
        print(f"    Cadeia: {cadeia}")
        print(f"    Esperado: {oculto}")
        print(f"    {'SIM!' if acertou else 'NAO'}")
        
        if acertou:
            acertos += 1
        print()

    print("=" * 70)
    print(f"  RESULTADO: {acertos}/{len(SEQUENCIAS)}")
    print()
    if acertos >= 3:
        print("  MCR DESCOBRIU AS SEQUENCIAS POR TRANSICOES!")
    elif acertos >= 1:
        print("  MCR descobriu algumas.")
    else:
        print("  MCR NAO descobriu. Transicoes simples nao captam regras.")
        print("  A regra nao esta em 'ultimo -> proximo'.")
        print("  Ela esta na relacao entre multiplos elementos anteriores.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
