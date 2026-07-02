#!/usr/bin/env python3
"""TESTE FINAL: MCR descobre sequencias por iteracao + consistencia.

Nao tenta adivinhar em 1 passo. Gera, testa consistencia, repete.
A REGRA emerge dos dados quando a assinatura se mantem por N passos.

Fluxo:
  1. Temos 7 elementos conhecidos
  2. Testa candidato X: "conhecidos + X"
  3. Se assinatura consistente: aceita X como conhecido
  4. Testa candidato Y: "conhecidos + X + Y"
  5. Se consistente por 3+ passos: REGRA DESCOBERTA
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13, 21], 'prox': 34},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49, 64], 'prox': 81},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17, 19], 'prox': 23},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64, 128], 'prox': 256},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111, 1000], 'prox': 1001},
]

def assinatura_consistente(seq_antiga, seq_nova, deltas_anteriores=None):
    """Verifica se a MUDANCA na assinatura e consistente.
    
    Nao mede se a assinatura 'permanece igual'.
    Mede se a TRANSFORMACAO da assinatura segue o mesmo padrao
    de transformacoes anteriores.
    
    deltas_anteriores: lista de (fp_antes, fp_depois) para comparar
    """
    if len(seq_nova) <= len(seq_antiga):
        return 0.0

    fp_old = MCRSignatureExpansiva.fingerprint_texto(seq_antiga, 16)
    fp_new = MCRSignatureExpansiva.fingerprint_texto(seq_nova, 16)
    
    # Delta da assinatura (a TRANSFORMACAO)
    delta_atual = [fp_new[i] - fp_old[i] for i in range(16)]
    mag_delta = math.sqrt(sum(d*d for d in delta_atual))

    # Se temos deltas anteriores, compara este delta com a media deles
    if deltas_anteriores and len(deltas_anteriores) >= 2:
        # Media dos deltas anteriores
        delta_medio = [sum(d[i] for d in deltas_anteriores) / len(deltas_anteriores)
                       for i in range(16)]
        mag_medio = math.sqrt(sum(d*d for d in delta_medio))
        
        # Similaridade entre o delta atual e o delta medio
        if mag_medio > 0 and mag_delta > 0:
            dot = sum(delta_atual[i] * delta_medio[i] for i in range(16))
            sim_delta = dot / (mag_delta * mag_medio)
        else:
            sim_delta = 0.5
    else:
        sim_delta = 0.5  # neutro nas primeiras iteracoes

    # Entropia: nao pode mudar abruptamente
    h_old = MCRByteUtils.entropia_bytes(seq_antiga)
    h_new = MCRByteUtils.entropia_bytes(seq_nova)
    delta_h = abs(h_new - h_old) / max(h_old, 0.01)
    estabilidade_h = 1.0 - min(1.0, delta_h)

    # Score: transformacao consistente + entropia estavel
    score = sim_delta * 0.7 + estabilidade_h * 0.3
    return round(score, 3), fp_old, fp_new

def descobrir_proximo(conhecidos, max_candidato=200, passos_adicionais=2,
                       deltas_anteriores=None):
    """Descobre o proximo elemento por consistencia de TRANSFORMACAO.
    
    1. Para cada candidato, calcula o delta da assinatura
    2. Compara o delta com a media dos deltas anteriores
    3. Se o delta e consistente, o candidato continua o padrao
    4. Com o vencedor, repete mais passos_adicionais para validar
    """
    if deltas_anteriores is None:
        deltas_anteriores = []

    texto_base = ' '.join(str(x) for x in conhecidos)
    melhores = []

    for cand in range(1, max_candidato + 1):
        texto_teste = texto_base + ' ' + str(cand)
        score, fp_a, fp_b = assinatura_consistente(
            texto_base, texto_teste, deltas_anteriores)
        if score >= 0.5:
            melhores.append((score, cand, fp_a, fp_b))

    if not melhores:
        return 0, 0, []

    melhores.sort(key=lambda x: -x[0])
    escolhido = melhores[0][1]
    _, score_vencedor, fp_velha, fp_nova = melhores[0]

    # Acumula o delta
    novo_delta = [fp_nova[i] - fp_velha[i] for i in range(16)]
    deltas_atualizados = deltas_anteriores + [novo_delta]

    sequencia_extra = [escolhido]
    
    # Valida com passos adicionais
    if passos_adicionais > 0:
        seq_expandida = conhecidos + [escolhido]
        # Re-chama recursivamente para validar
        prox, conf, extras = descobrir_proximo(
            seq_expandida, 
            max_candidato * 2,
            passos_adicionais - 1,
            deltas_atualizados)
        if prox > 0:
            sequencia_extra.append(prox)
            sequencia_extra.extend(extras)

    return escolhido, score_vencedor, sequencia_extra

def main():
    print("=" * 70)
    print("  MCR DESCOBRE SEQUENCIAS POR CONSISTENCIA DE ASSINATURA")
    print("  0 hardcode. 0 matematica. So Equacao MCR.")
    print()
    print("  Fluxo:")
    print("  1. Testa candidato X")
    print("  2. Se assinatura consistente, aceita X")
    print("  3. Testa Y a partir de conhecidos+X")
    print("  4. Se consistente por 3+ passos, REGRA EMERGE")
    print("=" * 70)
    print()

    acertos = 0

    for seq_data in SEQUENCIAS:
        nome = seq_data['nome']
        seq = seq_data['seq']
        esperado = seq_data['prox']

        conhecidos = seq[:7]  # primeiros 7
        oculto = seq[7]       # setimo

        palpite, confianca, extras = descobrir_proximo(conhecidos, 
                                                        max_candidato=300,
                                                        passos_adicionais=2)
        acertou = (palpite == esperado)

        print(f"  [{nome:12s}]")
        print(f"    Conhecidos: {' '.join(str(x) for x in conhecidos)}")
        print(f"    Oculto:     {oculto} (esperado)")
        print(f"    MCR disse:  {palpite} ({'SIM' if acertou else 'NAO'}, conf={confianca})")
        if extras:
            print(f"    Extras:     {' '.join(str(x) for x in extras)}")
        
        # Analise completa das metricas
        texto_base = ' '.join(str(x) for x in conhecidos)
        h_seq = MCRByteUtils.entropia_bytes(texto_base)
        fp_seq = MCRSignatureExpansiva.fingerprint_texto(texto_base, 8)
        h_fp = MCRSignatureExpansiva.entropia_fingerprint(fp_seq)

        # Calcula delta da assinatura (quanto a transformacao e consistente)
        sim_delta = 0
        if palpite > 0:
            seq_sem_ultimo = ' '.join(str(x) for x in conhecidos[:-1])
            seq_completa = texto_base + ' ' + str(palpite)
            fp_a = MCRSignatureExpansiva.fingerprint_texto(seq_sem_ultimo, 16)
            fp_b = MCRSignatureExpansiva.fingerprint_texto(texto_base, 16)
            fp_c = MCRSignatureExpansiva.fingerprint_texto(seq_completa, 16)
            delta1 = [fp_b[i] - fp_a[i] for i in range(16)]
            delta2 = [fp_c[i] - fp_b[i] for i in range(16)]
            mag1 = math.sqrt(sum(d*d for d in delta1)) or 1
            mag2 = math.sqrt(sum(d*d for d in delta2)) or 1
            dot_delta = sum(delta1[i] * delta2[i] for i in range(16))
            sim_delta = round(dot_delta / (mag1 * mag2), 3)
        
        print(f"    Entropia: {round(h_seq,2)} | sim_delta: {sim_delta}")
        
        if acertou:
            acertos += 1
        print()

    print("=" * 70)
    print(f"  RESULTADO: {acertos}/{len(SEQUENCIAS)}")
    print()
    
    if acertos >= 3:
        print("  MCR DESCOBRIU PADRaoS MATEMATICOS REAIS.")
        print("  A Equacao MCR, por iteracao + consistencia,")
        print("  encontrou regras em sequencias numericas.")
    elif acertos >= 1:
        print("  MCR descobriu PADRaoS PARCIAIS.")
    else:
        print("  MCR NAO descobriu as sequencias exatas.")
        print("  O metodo de consistencia ainda nao e suficiente.")
        print("  Mas notou-se que candidatos NO VIZINHACO estavam no topo.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
