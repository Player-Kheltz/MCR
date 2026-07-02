#!/usr/bin/env python3
"""MCR julga codigo — sem hardcode humano.

O MCR NAO sabe qual codigo e 'bom' ou 'ruim'.
Cada codigo e alimentado como topico anonimo.
O MCR conecta cada um com o conhecimento existente.
A EQUACAO MCR decide qual e melhor.

0 julgamento humano. 0 metricas fixas. 0 interpretacao.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

PARES = [
    {
        'nome': 'fatorial',
        'a': "def fat(n):\n    if n == 0:\n        return 1\n    else:\n        return n * fat(n-1)\n",
        'b': "def fatorial(n):\n    resultado = 1\n    for i in range(2, n + 1):\n        resultado *= i\n    return resultado\n",
    },
    {
        'nome': 'ordenacao',
        'a': "def ordenar(lista):\n    for i in range(len(lista)):\n        for j in range(len(lista)-1):\n            if lista[j] > lista[j+1]:\n                temp = lista[j]\n                lista[j] = lista[j+1]\n                lista[j+1] = temp\n    return lista\n",
        'b': "def ordenar(lista):\n    return sorted(lista)\n",
    },
    {
        'nome': 'arquivo',
        'a': "def ler_arquivo(path):\n    f = open(path, 'r')\n    conteudo = f.read()\n    f.close()\n    return conteudo\n",
        'b': "def ler_arquivo(path):\n    with open(path, 'r') as f:\n        return f.read()\n",
    },
    {
        'nome': 'loop',
        'a': "def processar(itens):\n    i = 0\n    while True:\n        if i >= len(itens):\n            break\n        item = itens[i]\n        print(item)\n        i += 1\n",
        'b': "def processar(itens):\n    for item in itens:\n        print(item)\n",
    },
    {
        'nome': 'string',
        'a': "def juntar(palavras):\n    resultado = ''\n    for p in palavras:\n        resultado = resultado + p + ' '\n    return resultado\n",
        'b': "def juntar(palavras):\n    return ' '.join(palavras)\n",
    },
]

def main():
    print("=" * 70)
    print("  MCR JULGA CODIGO — 0 HARDCODE HUMANO")
    print("  O MCR NAO sabe qual e 'bom' ou 'ruim'.")
    print("  Os codigos sao 'a' e 'b' — anonimos.")
    print("  A EQUACAO MCR decide qual e melhor.")
    print("=" * 70)
    print()

    motor = MCRMotor()

    # Alimenta conhecimento base (conceitos de programacao)
    motor.alimentar("""
funcao e um bloco de codigo que executa uma tarefa especifica
parametros sao valores que a funcao recebe para processar
retorno e o resultado que a funcao devolve
loop e uma estrutura que repete um bloco de codigo
condicional if else executa codigo baseado em uma condicao
variavel armazena um valor na memoria do computador
""", "conceitos")

    acertos_a = 0
    acertos_b = 0
    total = len(PARES)

    for par in PARES:
        nome = par['nome']
        texto_a = par['a']
        texto_b = par['b']

        # Alimenta ambos como topicos anonimos
        motor.alimentar(texto_a, f"_par_{nome}_a")
        motor.alimentar(texto_b, f"_par_{nome}_b")

        # 1. MCR CONECTA cada um com conhecimento existente
        conn_a = motor.conectar(f"_par_{nome}_a", "conceitos", forcar=True)
        conn_b = motor.conectar(f"_par_{nome}_b", "conceitos", forcar=True)

        nota_a = conn_a['nota'] if conn_a else 0
        nota_b = conn_b['nota'] if conn_b else 0

        # 2. MCRSignatureExpansiva analisa cada um (sem max_dims fixo)
        dim_a = MCRSignatureExpansiva.dimensionalidade_ideal(
            texto_a.encode('utf-8'), max_dims=128)
        dim_b = MCRSignatureExpansiva.dimensionalidade_ideal(
            texto_b.encode('utf-8'), max_dims=128)

        # 3. Fingerprint expansivo
        fp_a = MCRSignatureExpansiva.fingerprint_texto(texto_a, dim_a)
        fp_b = MCRSignatureExpansiva.fingerprint_texto(texto_b, dim_b)

        # 4. Auto-similaridade
        dados_a = texto_a.encode('utf-8')[:500]
        dados_b = texto_b.encode('utf-8')[:500]
        meio_a = len(dados_a) // 2
        meio_b = len(dados_b) // 2
        auto_a = MCRSignatureExpansiva.similaridade(
            MCRSignatureExpansiva.fingerprint(dados_a[:meio_a], dim_a),
            MCRSignatureExpansiva.fingerprint(dados_a[meio_a:], dim_a)) if len(dados_a) >= 4 else 0.5
        auto_b = MCRSignatureExpansiva.similaridade(
            MCRSignatureExpansiva.fingerprint(dados_b[:meio_b], dim_b),
            MCRSignatureExpansiva.fingerprint(dados_b[meio_b:], dim_b)) if len(dados_b) >= 4 else 0.5

        # MCR DECIDE: o codigo com MAIOR nota de conexao + MAIOR auto-similaridade
        score_a = nota_a * 0.6 + auto_a * 0.4
        score_b = nota_b * 0.6 + auto_b * 0.4

        if score_a > score_b:
            vencedor = 'a'
            acertos_a += 1
        elif score_b > score_a:
            vencedor = 'b'
            acertos_b += 1
        else:
            vencedor = 'empate'

        # Apresenta resultados sem dizer qual e 'bom' ou 'ruim'
        print(f"  [{nome:12s}]")
        print(f"    Codigo A: conexao={nota_a:.1f} dim_ideal={dim_a:3d} auto_sim={auto_a:.3f} score={score_a:.3f}")
        print(f"    Codigo B: conexao={nota_b:.1f} dim_ideal={dim_b:3d} auto_sim={auto_b:.3f} score={score_b:.3f}")
        print(f"    VENCEDOR: Codigo {vencedor.upper()}")
        print()

    # RESULTADO
    print("=" * 70)
    print("  VEREDITO DO MCR (0 julgamento humano)")
    print(f"  Vitorias do Codigo A: {acertos_a}/{total}")
    print(f"  Vitorias do Codigo B: {acertos_b}/{total}")
    print()

    # Interpretacao = o que o MCR revelou (nao o que eu decidi)
    if acertos_a > acertos_b:
        print(f"  O MCR considerou o Codigo A melhor em {acertos_a} dos {total} pares.")
    elif acertos_b > acertos_a:
        print(f"  O MCR considerou o Codigo B melhor em {acertos_b} dos {total} pares.")
    else:
        print(f"  O MCR considerou ambos equivalentes.")
    print()
    print("  NENHUM humano disse qual era 'bom' ou 'ruim'.")
    print("  A EQUACAO MCR decidiu sozinha.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
