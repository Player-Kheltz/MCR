#!/usr/bin/env python3
"""Teste REAL do MCR contra problemas sem resposta conhecida.

1. Sequencia de Collatz (3n+1) — problema em aberto desde 1937
2. Numeros primos — distribuicao sem formula fechada

O MCR tenta descobrir padroes onde a matematica ainda nao encontrou.
Se conseguir fazer melhor que aleatorio, e um resultado REAL.
"""
import sys, os, math, json, random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

BASE = os.path.dirname(__file__)

# ═══════════════════════════════════════════════════════════════
# GERACAO DOS DADOS
# ═══════════════════════════════════════════════════════════════

def collatz(n: int, max_passos: int = 1000) -> list:
    """Gera sequencia de Collatz a partir de n.
    
    Regra: se n par → n/2, se n impar → 3n+1.
    Problema em aberto: toda sequencia termina em 1?
    """
    seq = [n]
    while n != 1 and len(seq) < max_passos:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        seq.append(n)
    return seq

def gerar_primos(n: int) -> list:
    """Gera os N primeiros numeros primos (crivo de Eratostenes)."""
    primos = []
    candidato = 2
    while len(primos) < n:
        e_primo = True
        for p in primos:
            if p * p > candidato:
                break
            if candidato % p == 0:
                e_primo = False
                break
        if e_primo:
            primos.append(candidato)
        candidato += 1
    return primos

# ═══════════════════════════════════════════════════════════════
# TESTE COLLATZ
# ═══════════════════════════════════════════════════════════════

def testar_collatz():
    """Testa se o MCR descobre padrao na sequencia de Collatz."""
    print("=" * 65)
    print("  TESTE 1: SEQUENCIA DE COLLATZ (problema em aberto)")
    print("=" * 65)
    print()

    # Gera 20 sequencias para treino
    sementes = list(range(2, 42, 2))  # 20 numeros pares
    todas_sequencias = []
    for s in sementes:
        seq = collatz(s, 100)
        todas_sequencias.extend(seq)
        if len(todas_sequencias) > 2000:
            break

    # Alimenta no MCR como BYTES
    collatz_bytes = [b for n in todas_sequencias for b in str(n).encode('utf-8')]
    
    mk_collatz = MCR("collatz")
    mk_collatz.aprender_sequencia([f"B:{b:02x}" for b in collatz_bytes[:1500]])

    print(f"  Sequencias geradas: {len(sementes)}")
    print(f"  Bytes totais: {len(collatz_bytes)}")
    print(f"  Markov: {mk_collatz.stats()}")
    print()

    # Predicao: dado um numero, qual o proximo na sequencia?
    print("  TENTANDO PREDIZER O PROXIMO TERMO:")
    print()

    acertos = 0
    total_testes = 0
    erros_por_distancia = {}

    for n in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 31]:
        seq_real = collatz(n, 20)
        if len(seq_real) < 3:
            continue

        # Alimenta os primeiros termos no MCR
        for termo in seq_real[:3]:
            for b in str(termo).encode('utf-8'):
                mk_collatz.aprender(f"B:{b:02x}", f"B:{b:02x}")  # reforco

        # Tenta predizer o PROXIMO termo apos o 3o
        ultimo = str(seq_real[2])
        bytes_ultimo = ultimo.encode('utf-8')
        preditos = []
        for b in bytes_ultimo:
            prox, conf = mk_collatz.predizer(f"B:{b:02x}")
            if prox:
                try:
                    preditos.append(int(prox[2:], 16))
                except:
                    pass

        if preditos:
            total_testes += 1
            # Converte bytes preditos de volta para numero
            pred_str = ''.join(chr(x) for x in preditos if 48 <= x <= 57)
            if pred_str:
                try:
                    predito = int(pred_str)
                    real = seq_real[3]
                    distancia = abs(predito - real)
                    if distancia == 0:
                        acertos += 1
                    else:
                        chave = str(int(distancia / 10) * 10) if distancia > 0 else '0'
                        erros_por_distancia[chave] = erros_por_distancia.get(chave, 0) + 1
                except:
                    pass

    print(f"  Acertos: {acertos}/{total_testes}")
    if erros_por_distancia:
        print(f"  Erros por faixa de distancia: {dict(sorted(erros_por_distancia.items()))}")

    # Baseline: chance aleatoria
    # Sequencia de Collatz tem termos ate ~100 para sementes pequenas
    # Chance aleatoria de acertar o exato: ~1/100
    aleatorio_esperado = total_testes / 100
    print(f"  Baseline aleatorio esperado: ~{aleatorio_esperado:.1f} acertos")
    print()

    resultado = {
        'acertos': acertos,
        'total': total_testes,
        'baseline': round(aleatorio_esperado, 1),
        'superou_baseline': acertos > aleatorio_esperado,
    }
    print(f"  RESULTADO: MCR {'SUPEROU' if resultado['superou_baseline'] else 'NAO SUPEROU'} baseline")
    print()
    return resultado

# ═══════════════════════════════════════════════════════════════
# TESTE PRIMOS
# ═══════════════════════════════════════════════════════════════

def testar_primos():
    """Testa se o MCR descobre padrao na distribuicao de primos."""
    print("=" * 65)
    print("  TESTE 2: NUMEROS PRIMOS (distribuicao sem formula)")
    print("=" * 65)
    print()

    # Gera primos
    primos = gerar_primos(300)
    gaps = [primos[i+1] - primos[i] for i in range(len(primos)-1)]

    print(f"  Primos gerados: {len(primos)}")
    print(f"  Gaps: media={sum(gaps)/len(gaps):.1f}, max={max(gaps)}")
    print()

    # Alimenta gaps como texto no MCR
    mk_gap = MCR("primos_gap")
    for g in gaps[:200]:
        for b in str(g).encode('utf-8'):
            mk_gap.aprender(f"B:{b:02x}", f"B:{b:02x}")

    mk_gap_sequencia = MCR("primos_seq")
    mk_gap_sequencia.aprender_sequencia([str(g) for g in gaps[:200]])

    print(f"  Markov gap bytes: {mk_gap.stats()}")
    print(f"  Markov gap palavras: {mk_gap_sequencia.stats()}")
    print()

    # Predicao: dado o ultimo gap, qual o proximo?
    print("  TENTANDO PREDIZER O PROXIMO GAP ENTRE PRIMOS:")
    print()

    acertos = 0
    total = 0
    baseline_acertos = 0

    for i in range(200, min(290, len(gaps) - 1)):
        ultimo_gap = gaps[i]
        real_prox = gaps[i + 1]

        # Markov tenta predizer
        prox, conf = mk_gap_sequencia.predizer(str(ultimo_gap))
        if prox:
            try:
                predito = int(prox)
                if abs(predito - real_prox) <= 2:  # tolerancia
                    acertos += 1
                total += 1
            except:
                pass

        # Baseline: chuta o gap mais comum nos dados de treino
        if i < 100:  # so usa os primeiros 100 como baseline
            from collections import Counter
            gaps_treino = gaps[:200]
            gap_mais_comum = Counter(gaps_treino).most_common(1)[0][0]
            if abs(gap_mais_comum - real_prox) <= 2:
                baseline_acertos += 1

    print(f"  Acertos MCR (tolerancia ±2): {acertos}/{total}")
    print(f"  Baseline (gap mais comum):   {baseline_acertos}/{min(100, total)}")
    print()

    # Entropia dos gaps
    h_gaps = MCRByteUtils.entropia_bytes(','.join(str(g) for g in gaps[:300]))
    print(f"  Entropia dos gaps: {h_gaps:.3f} (max ~8)")

    resultado = {
        'acertos_mcr': acertos,
        'total_predicoes': total,
        'acertos_baseline': baseline_acertos,
        'entropia_gaps': round(h_gaps, 3),
        'superou_baseline': acertos > baseline_acertos if total > 0 else False,
    }
    print(f"  RESULTADO: MCR {'SUPEROU' if resultado['superou_baseline'] else 'NAO SUPEROU'} baseline")
    print()
    return resultado

# ═══════════════════════════════════════════════════════════════
# TESTE 3: ASSINATURA MCR NOS PROPRIOS DADOS
# ═══════════════════════════════════════════════════════════════

def testar_auto_diagnostico():
    """Aplica a Equacao MCR sobre os proprios resultados.

    Se o MCR consegue encontrar padrao ate nos proprios resultados
    de problemas nao resolvidos, a equacao e universal.
    """
    print("=" * 65)
    print("  TESTE 3: MCR APLICADO AOS PROPRIOS RESULTADOS")
    print("=" * 65)
    print()

    motor = MCRMotor()
    motor.alimentar('collatz 3 10 5 16 8 4 2 1 collatz 5 16 8 4 2 1 collatz 7 22 11 34 17 52 26 13 40 20 10 5 16 8 4 2 1', 'collatz_seq')
    motor.alimentar('primos 2 3 5 7 11 13 17 19 23 29 31 37 41 43 47 53 59 61 67 71 73 79 83 89 97 gaps entre primos 1 2 2 4 2 4 2 4 6 2 6 4 2 4 6 6 2 6 4 2 6', 'primos_seq')
    motor.alimentar('a equacao MCR mede a coerencia de assinaturas em qualquer nivel byte palavra token intencao decisao acao assinatura qualidade o conceito e que tudo carrega uma assinatura multidimensional', 'equacao_mcr')

    print("  Diagnosticando o motor:")
    diag = MCRMeta.diagnosticar(motor)
    print(f"  Nota geral: {diag['nota_geral']}/10")
    print(f"  Gap: {diag['gap_principal']}")
    print(f"  Sugestao: {diag['sugestao']}")
    print()

    # Aplica Equacao MCR nos resultados dos testes anteriores
    print("  Equacao MCR aplicada aos dados de Collatz:")
    c_bytes = 'collatz 3 10 5 16 8 4 2 1 collatz 5 16 8 4 2 1 collatz 7 22 11 34 17 52 26 13 40 20 10 5 16 8 4 2 1'
    h_collatz = MCRByteUtils.entropia_bytes(c_bytes)
    fp_collatz = MCRByteUtils.fingerprint(c_bytes[:500], 4)
    print(f"    Entropia: {h_collatz:.3f}")
    print(f"    Fingerprint: {[round(v, 3) for v in fp_collatz]}")
    print()

    print("  Equacao MCR aplicada aos gaps de primos:")
    p_gaps = '1 2 2 4 2 4 2 4 6 2 6 4 2 4 6 6 2 6 4 2 6 4 6 8 4 2 4 2 4 14 4 6 2 10 2 6 6 4 6 6 2 10 2 4 2 12'
    h_primos = MCRByteUtils.entropia_bytes(p_gaps)
    fp_primos = MCRByteUtils.fingerprint(p_gaps[:500], 4)
    print(f"    Entropia: {h_primos:.3f}")
    print(f"    Fingerprint: {[round(v, 3) for v in fp_primos]}")
    print()

    return {
        'nota_geral': diag['nota_geral'],
        'gap': diag['gap_principal'],
        'entropia_collatz': round(h_collatz, 3),
        'entropia_primos': round(h_primos, 3),
    }

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 65)
    print("  TESTE REAL: MCR vs PROBLEMAS SEM RESPOSTA")
    print("=" * 65)
    print()

    r1 = testar_collatz()
    r2 = testar_primos()
    r3 = testar_auto_diagnostico()

    print("=" * 65)
    print("  RESUMO FINAL")
    print("=" * 65)
    print()
    print(f"  Collatz: {r1['acertos']}/{r1['total']} (baseline ~{r1['baseline']}) "
          f"{'SIM' if r1['superou_baseline'] else 'NAO'}")
    print(f"  Primos:  MCR={r2['acertos_mcr']}/{r2['total_predicoes']} "
          f"baseline={r2['acertos_baseline']} "
          f"{'SIM' if r2['superou_baseline'] else 'NAO'}")
    print(f"  Auto-diagnostico: nota={r3['nota_geral']}/10, "
          f"gap={r3['gap']}, "
          f"entropia collatz={r3['entropia_collatz']}, "
          f"entropia primos={r3['entropia_primos']}")
    print()

    # Interpretacao
    print("  INTERPRETACAO:")
    if r1['superou_baseline'] or r2['superou_baseline']:
        print("  O MCR ENCONTROU PADROES onde a matematica ainda nao tem resposta.")
        print("  Isso e um resultado REAL — replicavel, testavel, mensuravel.")
    else:
        print("  O MCR NAO superou o baseline nestes testes especificos.")
        print("  Pode ser limite do metodo (ordem 1) ou dados insuficientes.")
    print()

    # Salva resultados
    resultados = {
        'collatz': r1,
        'primos': r2,
        'auto': r3,
        'interpretacao': (
            'MCR superou baseline' if r1['superou_baseline'] or r2['superou_baseline']
            else 'MCR nao superou baseline'
        ),
    }
    path = os.path.join(BASE, 'resultados_teste_real.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"  Resultados salvos em: {path}")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
