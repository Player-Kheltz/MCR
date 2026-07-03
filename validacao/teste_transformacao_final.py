#!/usr/bin/env python3
"""MCR descobre proximo elemento por CONSISTENCIA DA TRANSFORMACAO.

Nao Markov. Nao jaccard direto.
Cada par (a,b) tem um delta de fingerprint.
A sequencia de deltas tem uma assinatura.
O proximo elemento e o que produz o delta MAIS CONSISTENTE
com a assinatura dos deltas anteriores.
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

def delta_fingerprint(a, b, dim=16):
    """Calcula a TRANSFORMACAO entre duas strings como delta de fingerprint."""
    fp_a = MCRSignatureExpansiva.fingerprint_texto(str(a), dim)
    fp_b = MCRSignatureExpansiva.fingerprint_texto(str(b), dim)
    return [fp_b[i] - fp_a[i] for i in range(dim)]

def magnitude(delta):
    return math.sqrt(sum(d*d for d in delta))

def similaridade_delta(d1, d2):
    """Similaridade entre dois deltas (cosseno)."""
    mag1 = magnitude(d1)
    mag2 = magnitude(d2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    dot = sum(d1[i] * d2[i] for i in range(len(d1)))
    return dot / (mag1 * mag2)

def main():
    print("=" * 70)
    print("  MCR: CONSISTENCIA DA TRANSFORMACAO")
    print("  Cada par (a,b) tem um delta de fingerprint.")
    print("  A sequencia de deltas tem uma assinatura.")
    print("  O melhor candidato e o que mantem essa assinatura.")
    print("=" * 70)
    print()

    acertos = 0

    for seq in SEQUENCIAS:
        nome = seq['nome']
        elementos = seq['seq']
        resposta = seq['resposta']

        # Calcula deltas entre todos os pares consecutivos
        deltas = []
        for i in range(len(elementos) - 1):
            d = delta_fingerprint(elementos[i], elementos[i+1])
            deltas.append(d)

        # Media dos deltas (assinatura media da transformacao)
        n_dims = len(deltas[0]) if deltas else 16
        delta_medio = [sum(d[i] for d in deltas) / len(deltas) for i in range(n_dims)]
        mag_media = magnitude(delta_medio)

        # Proximo delta previsto = delta medio
        # (a transformacao media e o que esperamos ver novamente)

        # Testa candidatos de 1 a 2000 para ver qual produz
        # o delta mais consistente com o delta medio
        ultimo = str(elementos[-1])
        melhores = []

        for cand in range(1, 2001):
            d_cand = delta_fingerprint(ultimo, str(cand))
            sim = similaridade_delta(d_cand, delta_medio) if mag_media > 0 else 0
            mag_cand = magnitude(d_cand)

            # Penalidade se a magnitude do candidato for muito diferente
            # da magnitude media dos deltas
            if mag_media > 0 and mag_cand > 0:
                razao_mag = min(mag_cand, mag_media) / max(mag_cand, mag_media)
                score = sim * razao_mag
            else:
                score = sim

            if score > 0:
                melhores.append((round(score, 4), cand))

        melhores.sort(key=lambda x: -x[0])

        palpite = melhores[0][1] if melhores else 0
        confianca = melhores[0][0] if melhores else 0
        acertou = palpite == resposta

        print(f"  [{nome:12s}]")
        print(f"    Sequencia: {' '.join(str(x) for x in elementos)}")
        print(f"    Resposta:  {resposta}")
        print(f"    MCR disse: {palpite} (conf={confianca:.4f}) {'SIM!' if acertou else 'NAO'}")

        # Mostra os deltas
        print(f"    Deltas (mag): {[round(magnitude(d), 2) for d in deltas]}")
        print(f"    Delta medio: {[round(v, 2) for v in delta_medio[:6]]}... (mag={round(mag_media, 2)})")
        
        if melhores and len(melhores) >= 3:
            print(f"    Top 3: {[(c, s) for s, c in melhores[:3]]}")
        
        # Mostra a semelhanca entre o palpite e respostas conhecidas
        j = MCRByteUtils.jaccard_bytes(str(ultimo), str(palpite))
        print(f"    Jaccard({ultimo}, {palpite}) = {j:.3f}")
        print()

        if acertou:
            acertos += 1

    print("=" * 70)
    print(f"  RESULTADO: {acertos}/{len(SEQUENCIAS)}")
    print()
    if acertos >= 3:
        print("  O MCR descobriu as sequencias por consistencia de transformacao!")
    elif acertos >= 1:
        print("  O MCR descobriu algumas. A abordagem de delta fingerprint funciona.")
    else:
        print("  Nenhuma acertou. A transformacao media nao capta o padrao.")
        print("  A assinatura da transformacao e mais sutil que a media dos deltas.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
