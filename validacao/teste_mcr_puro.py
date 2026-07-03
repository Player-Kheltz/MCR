#!/usr/bin/env python3
"""MCR PURO contra 5 sequencias. Sem pre-formatacao. Sem interpretacao.
A Equacao MCR fala. Eu calo. O que emerge, emerge.

Nao ha 'prever proximo'. Nao ha 'acertou/errou'.
Ha apenas a assinatura revelada.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

SEQUENCIAS = [
    "1 1 2 3 5 8 13",
    "1 4 9 16 25 36 49",
    "2 3 5 7 11 13 17",
    "1 2 4 8 16 32 64",
    "1 10 11 100 101 110 111",
]

def main():
    print("=" * 70)
    print("  MCR PURO: A EQUACAO FALA — EU CALO")
    print("  Nao ha 'prever proximo'. Nao ha 'julgamento'.")
    print("  A assinatura de cada sequencia e revelada.")
    print("=" * 70)
    print()

    for idx, texto in enumerate(SEQUENCIAS):
        nome = ["Fibonacci", "Quadrados", "Primos", "Pot2", "Binario"][idx]
        dados = texto.encode('utf-8')

        # 1. Entropia (pura, sem interpretacao)
        h = MCRByteUtils.entropia_bytes(dados)

        # 2. Dimensionalidade ideal (auto-descoberta)
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(dados, max_dims=64)

        # 3. Fingerprint na dimensao ideal
        fp = MCRSignatureExpansiva.fingerprint(dados, dim)

        # 4. Entropia do fingerprint (distribuicao)
        h_fp = MCRSignatureExpansiva.entropia_fingerprint(fp)

        # 5. Auto-similaridade (metade1 vs metade2)
        meio = len(dados) // 2
        fp1 = MCRSignatureExpansiva.fingerprint(dados[:meio], dim)
        fp2 = MCRSignatureExpansiva.fingerprint(dados[meio:], dim)
        auto_sim = MCRSignatureExpansiva.similaridade(fp1, fp2)

        # 6. Fingerprint compacto (8 dims)
        fp8 = MCRSignatureExpansiva.fingerprint(dados, 8)

        # 7. MCR sobre a sequencia
        m = MCR(nome)
        palavras = texto.split()
        for i in range(len(palavras) - 1):
            m.aprender(palavras[i], palavras[i+1])
        stats = m.stats()

        # 8. Top estado (byte mais frequente)
        mk_byte = MCR(nome + "_byte")
        mk_byte.aprender_sequencia([f"B:{b:02x}" for b in dados])
        top_estados = sorted(mk_byte.freq.items(), key=lambda x: -x[1])[:3]

        print(f"  -- {nome} --")
        print(f"  Texto: {texto}")
        print(f"  Bytes:  {[f'B:{b:02x}' for b in dados[:30]]}...")
        print(f"  Entropia: {h:.3f}")
        print(f"  Dimensao ideal: {dim}")
        print(f"  Entropia do fingerprint: {h_fp:.3f}")
        print(f"  Auto-similaridade: {auto_sim:.3f}")
        print(f"  Marcov: {stats['estados']} estados, {stats['transicoes']} transicoes, H={stats['entropia_media']:.2f}")
        print(f"  Top bytes: {[(e, c) for e, c in top_estados]}")
        print(f"  Fingerprint ({dim}d): {[round(v, 2) for v in fp[:8]]}...")
        print()

    # --- ANALISE CRUZADA (todas as 5 vistas como UMA assinatura) ---
    print("  ── ANALISE CRUZADA (as 5 sequencias como UMA) ──")
    print()

    todas_juntas = ' '.join(SEQUENCIAS)
    dados_total = todas_juntas.encode('utf-8')
    h_total = MCRByteUtils.entropia_bytes(dados_total)
    dim_total = MCRSignatureExpansiva.dimensionalidade_ideal(dados_total, max_dims=64)
    fp_total = MCRSignatureExpansiva.fingerprint(dados_total, dim_total)

    print(f"  Entropia do conjunto: {h_total:.3f}")
    print(f"  Dimensao ideal: {dim_total}")
    print(f"  Fingerprint: {[round(v, 2) for v in fp_total[:8]]}...")
    print()

    # Similaridade entre cada par de sequencias
    print("  ── SIMULARIDADE ENTRE PARES (Jaccard) ──")
    print()
    for i in range(len(SEQUENCIAS)):
        for j in range(i + 1, len(SEQUENCIAS)):
            ja = MCRByteUtils.jaccard_bytes(SEQUENCIAS[i], SEQUENCIAS[j])
            nome_i = ["Fibonacci", "Quadrados", "Primos", "Pot2", "Binario"][i]
            nome_j = ["Fibonacci", "Quadrados", "Primos", "Pot2", "Binario"][j]
            print(f"  {nome_i:12s} vs {nome_j:12s}: J={ja:.4f}")

    print()
    print("  A EQUACAO FALOU. O QUE EMERGE, EMERGE.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
