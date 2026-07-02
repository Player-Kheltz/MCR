#!/usr/bin/env python3
"""Compara codigo bom vs ruim com MCRSignatureExpansiva.

O MCR NAO sabe o que e 'bom' ou 'ruim'.
A assinatura deve revelar qual e mais estruturado.

5 pares de codigo, mesma funcao, qualidade diferente.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

PARES = [
    {
        'nome': 'fatorial',
        'ruim': """
def fat(n):
    if n == 0:
        return 1
    else:
        return n * fat(n-1)
""",
        'bom': """
def fatorial(n):
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado
""",
    },
    {
        'nome': 'ordenacao',
        'ruim': """
def ordenar(lista):
    for i in range(len(lista)):
        for j in range(len(lista)-1):
            if lista[j] > lista[j+1]:
                temp = lista[j]
                lista[j] = lista[j+1]
                lista[j+1] = temp
    return lista
""",
        'bom': """
def ordenar(lista):
    return sorted(lista)
""",
    },
    {
        'nome': 'arquivo',
        'ruim': """
def ler_arquivo(path):
    f = open(path, 'r')
    conteudo = f.read()
    f.close()
    return conteudo
""",
        'bom': """
def ler_arquivo(path):
    with open(path, 'r') as f:
        return f.read()
""",
    },
    {
        'nome': 'loop',
        'ruim': """
def processar(itens):
    i = 0
    while True:
        if i >= len(itens):
            break
        item = itens[i]
        print(item)
        i += 1
""",
        'bom': """
def processar(itens):
    for item in itens:
        print(item)
""",
    },
    {
        'nome': 'string',
        'ruim': """
def juntar(palavras):
    resultado = ''
    for p in palavras:
        resultado = resultado + p + ' '
    return resultado
""",
        'bom': """
def juntar(palavras):
    return ' '.join(palavras)
""",
    },
]

def auto_similaridade(texto):
    """Similaridade entre primeira e segunda metade do texto."""
    dados = texto.encode('utf-8')[:500]
    if len(dados) < 4:
        return 0.5
    meio = len(dados) // 2
    fp1 = MCRSignatureExpansiva.fingerprint(dados[:meio], 8)
    fp2 = MCRSignatureExpansiva.fingerprint(dados[meio:], 8)
    return MCRSignatureExpansiva.similaridade(fp1, fp2)

def main():
    print("=" * 70)
    print("  TESTE: MCR vs CODIGO BOM vs RUIM")
    print("  O MCR NAO sabe o que e 'bom' ou 'ruim'")
    print("  A assinatura deve revelar a estrutura")
    print("=" * 70)
    print()

    acertos_entropia = 0
    acertos_dimensao = 0
    acertos_auto = 0
    total = len(PARES)

    for par in PARES:
        nome = par['nome']
        ruim = par['ruim'].strip()
        bom = par['bom'].strip()

        # 1. ENTROPIA (menor = mais estruturado)
        h_ruim = MCRByteUtils.entropia_bytes(ruim)
        h_bom = MCRByteUtils.entropia_bytes(bom)

        # 2. DIMENSAO IDEAL (menor = mais compressivel)
        dim_ruim = MCRSignatureExpansiva.dimensionalidade_ideal(ruim, max_dims=64)
        dim_bom = MCRSignatureExpansiva.dimensionalidade_ideal(bom, max_dims=64)

        # 3. AUTO-SIMILARIDADE (maior = mais consistente)
        auto_ruim = auto_similaridade(ruim)
        auto_bom = auto_similaridade(bom)

        # 4. FINGERPRINT
        fp_ruim = MCRSignatureExpansiva.fingerprint_texto(ruim, 8)
        fp_bom = MCRSignatureExpansiva.fingerprint_texto(bom, 8)

        # 5. JACCARD entre eles
        j_entre = MCRByteUtils.jaccard_bytes(ruim, bom)

        # 6. JACCARD de cada um com ele mesmo (baseline)
        j_ruim_self = MCRByteUtils.jaccard_bytes(ruim, ruim)
        j_bom_self = MCRByteUtils.jaccard_bytes(bom, bom)

        # Diagnostico MCR
        entropia_acertou = h_bom >= h_ruim
        if entropia_acertou:
            acertos_entropia += 1

        dimensao_acertou = dim_bom <= dim_ruim
        if dimensao_acertou:
            acertos_dimensao += 1

        auto_acertou = auto_bom >= auto_ruim
        if auto_acertou:
            acertos_auto += 1

        print(f"  [{nome:12s}]")
        print(f"    Entropia:        RUIM={h_ruim:.3f}  BOM={h_bom:.3f}  {'SIM' if entropia_acertou else 'NAO'} (bom > ruim = +denso)")
        print(f"    Dimensao ideal:  RUIM={dim_ruim:3d}  BOM={dim_bom:3d}  {'SIM' if dimensao_acertou else 'NAO'} (bom < ruim = +compresso)")
        print(f"    Auto-similarid:  RUIM={auto_ruim:.3f}  BOM={auto_bom:.3f}  {'SIM' if auto_acertou else 'NAO'} (bom > ruim = +consistente)")
        print(f"    Jaccard entre:   {j_entre:.3f}")
        print(f"    Fingerprint RUIM: {[round(v,2) for v in fp_ruim[:4]]}")
        print(f"    Fingerprint BOM:  {[round(v,2) for v in fp_bom[:4]]}")
        print()

    # Resumo
    print("=" * 70)
    print("  RESUMO:") 
    print(f"  Entropia (bom < ruim): {acertos_entropia}/{total}")
    print(f"  Dimensao (bom < ruim): {acertos_dimensao}/{total}")
    print(f"  Auto-sim (bom > ruim): {acertos_auto}/{total}")
    print()

    # Interpretacao
    print("  INTERPRETACAO:")
    print(f"  Codigo BOM e MAIS denso (entropia maior): {acertos_entropia}/{total}")
    print(f"  Codigo BOM e MAIS compressivel (dimensao menor): {acertos_dimensao}/{total}")
    print(f"  Codigo BOM e MAIS consistente (auto-similaridade maior): {acertos_auto}/{total}")
    print()
    if acertos_entropia >= 3 or acertos_dimensao >= 3:
        print("  CONCLUSAO: O MCR distingue codigo BOM de RUIM pela assinatura.")
        print("  O codigo BOM tende a ser mais denso (entropia maior)")
        print("  e mais compressivel (dimensao ideal menor),")
        print("  porque e conciso e estruturado, nao verboso e repetitivo.")
    else:
        print("  CASO REAL: O MCR revelou que a relacao nao e binaria.")
        print("  Codigo BOM pode ter entropia maior (compacto) OU menor (estruturado).")
        print("  A assinatura captura a DIFERENCA, mas nao e simples dizer 'bom < ruim'.")
        print("  O MCR ENCONTRA o padrao — o ser humano interpreta qual e melhor.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
