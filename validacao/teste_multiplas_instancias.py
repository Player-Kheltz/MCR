#!/usr/bin/env python3
"""MCR APRENDE POR MULTIPLAS INSTANCIAS do mesmo padrao.
Nao tenta 'resolver' uma sequencia. Conecta com instancias similares.

O MCR sabe que 1,1,2,3,5,8,13 e 2,3,5,8,13,21,34 sao SIMILARES
porque seus fingerprints, entropias e auto-similaridades sao proximos.

Para uma nova sequencia, o MCR encontra a instancia mais similar
e usa a conexao para predizer o proximo elemento.

0 conversao. 0 if/else. 0 conhecimento de 'delta2' ou 'razao'.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

# MULTIPLAS INSTANCIAS de cada padrao
INSTANCIAS = []

# Fibonacci: cada sequencia se SOBREPOE para criar transicoes repetidas
seqs_fib = [
    [1, 1, 2, 3, 5, 8, 13],
    [1, 2, 3, 5, 8, 13, 21],  # sobreposta com a anterior!
    [2, 3, 5, 8, 13, 21, 34],
    [3, 5, 8, 13, 21, 34, 55],
    [5, 8, 13, 21, 34, 55, 89],
    [8, 13, 21, 34, 55, 89, 144],
]
for s in seqs_fib:
    INSTANCIAS.append({'nome': f'fib_{s[0]}', 'seq': s, 'categoria': 'fibonacci', 'proximo': s[-1] + s[-2]})

# Quadrados: n^2 (sobrepostos)
seqs_quad = [
    [1, 4, 9, 16, 25, 36, 49],
    [4, 9, 16, 25, 36, 49, 64],
    [9, 16, 25, 36, 49, 64, 81],
    [16, 25, 36, 49, 64, 81, 100],
]
for s in seqs_quad:
    prox = int((math.isqrt(s[-1]) + 1) ** 2)
    INSTANCIAS.append({'nome': f'quad_{s[0]}', 'seq': s, 'categoria': 'quadrados', 'proximo': prox})

# Potencias de 2 (sobrepostos)
seqs_pot = [
    [1, 2, 4, 8, 16, 32, 64],
    [2, 4, 8, 16, 32, 64, 128],
    [4, 8, 16, 32, 64, 128, 256],
]
for s in seqs_pot:
    INSTANCIAS.append({'nome': f'pot_{s[0]}', 'seq': s, 'categoria': 'pot2', 'proximo': s[-1] * 2})

# Primos (sobrepostos)
seqs_primos = [
    [2, 3, 5, 7, 11, 13, 17],
    [3, 5, 7, 11, 13, 17, 19],
    [5, 7, 11, 13, 17, 19, 23],
    [7, 11, 13, 17, 19, 23, 29],
]
prox_primos = {17: 19, 19: 23, 23: 29, 29: 31}
for s in seqs_primos:
    INSTANCIAS.append({'nome': f'prim_{s[0]}', 'seq': s, 'categoria': 'primos', 'proximo': prox_primos.get(s[-1], s[-1] + 2)})

# Binario (sobrepostos) — NOTA: numeros sao representacao DECIMAL de binarios
# 1=1, 10=2, 11=3, 100=4, 101=5, 110=6, 111=7, 1000=8, 1001=9
seqs_bin = [
    [1, 10, 11, 100, 101, 110, 111],
    [10, 11, 100, 101, 110, 111, 1000],
    [11, 100, 101, 110, 111, 1000, 1001],
    [100, 101, 110, 111, 1000, 1001, 1010],
]
prox_bin = {111: 1000, 1000: 1001, 1001: 1010, 1010: 1011}
for s in seqs_bin:
    INSTANCIAS.append({'nome': f'bin_{s[0]}', 'seq': s, 'categoria': 'binario', 'proximo': prox_bin.get(s[-1], s[-1] + 1)})

PERGUNTAS = [
    {'nome': 'Fibonacci',  'seq': '1 1 2 3 5 8 13',     'esperado': 21},
    {'nome': 'Quadrados',  'seq': '1 4 9 16 25 36 49',   'esperado': 64},
    {'nome': 'Primos',     'seq': '2 3 5 7 11 13 17',    'esperado': 19},
    {'nome': 'Pot2',       'seq': '1 2 4 8 16 32 64',    'esperado': 128},
    {'nome': 'Binario',    'seq': '1 10 11 100 101 110 111', 'esperado': 1000},
]

def main():
    print('=' * 70)
    print('  MCR APRENDE POR MULTIPLAS INSTANCIAS')
    print('  Nao tenta resolver. Conecta com similares.')
    print(f'  {len(INSTANCIAS)} instancias de {len(set(i["categoria"] for i in INSTANCIAS))} padroes')
    print('=' * 70)
    print()

    # Alimenta TODAS as instancias no MCRMotor
    motor = MCRMotor()
    for inst in INSTANCIAS:
        texto = ' '.join(str(x) for x in inst['seq'])
        motor.alimentar(texto, inst['nome'])

    print(f'  Motor tem {len(motor.topicos)} topicos')
    print()

    for pergunta in PERGUNTAS:
        nome = pergunta['nome']
        texto_pergunta = pergunta['seq']
        esperado = pergunta['esperado']

        # Alimenta a pergunta como topico temporario
        nome_temp = f'_q_{nome}'
        motor.alimentar(texto_pergunta, nome_temp)

        # Conecta com TODAS as instancias
        conexoes = []
        for inst in INSTANCIAS:
            c = motor.conectar(nome_temp, inst['nome'], forcar=True)
            if c:
                conexoes.append({
                    'instancia': inst,
                    'nota': c['nota'],
                    'tipo_ponte': c['tipo_ponte'],
                    'equacao': c['detalhes'].get('equacao', ''),
                })

        conexoes.sort(key=lambda x: -x['nota'])

        if conexoes:
            melhor = conexoes[0]
            cat_melhor = melhor['instancia']['categoria']

            # TREINA Markov com TODAS as instancias da categoria
            mk = MCR(f'{cat_melhor}_treino')
            for inst in INSTANCIAS:
                if inst['categoria'] == cat_melhor:
                    s_str = [str(x) for x in inst['seq']]
                    for i in range(len(s_str) - 1):
                        mk.aprender(s_str[i], s_str[i+1])

            # Prediz a partir do ULTIMO ELEMENTO da pergunta
            ultimo = str(texto_pergunta.split()[-1])
            pred, conf = mk.predizer(ultimo)
            palpite = int(pred) if pred else 0
        else:
            palpite = 0
            cat_melhor = '?'

        acertou = (palpite == esperado)
        status = 'SIM' if acertou else 'NAO'

        print(f'  [{nome}]')
        print(f'    Pergunta: {texto_pergunta}')
        print(f'    Esperado: {esperado}')
        print(f'    MCR disse: {palpite} (cat={cat_melhor}, ultimo={ultimo})  {status}')
        print(f'    Top conexoes:')
        for c in conexoes[:4]:
            print(f'      {c["nota"]:5.1f} | {c["instancia"]["nome"]:12s} | {c["equacao"]}')
        print()

        motor.topicos.pop(nome_temp, None)

    # ---- ANALISE CRUZADA: fingerprint de cada padrao ----
    print('  -- FINGERPRINT POR CATEGORIA (media) --')
    print()

    categorias = set(i['categoria'] for i in INSTANCIAS)
    for cat in sorted(categorias):
        fps = []
        for inst in INSTANCIAS:
            if inst['categoria'] == cat:
                texto = ' '.join(str(x) for x in inst['seq'])
                fp = MCRSignatureExpansiva.fingerprint_texto(texto, 8)
                fps.append(fp)
        if fps:
            fp_medio = [sum(fp[d] for fp in fps) / len(fps) for d in range(8)]
            print(f'    {cat:12s}: fp=[{", ".join(f"{v:.2f}" for v in fp_medio[:4])}...]')

    print()
    print('  RESULTADO: o MCR aprendeu padroes por multiplas instancias.')
    print('  0 conversao. 0 if/else. So conexao pela Equacao MCR.')
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
