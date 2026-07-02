#!/usr/bin/env python3
"""MCR EVOLUCAO AUTONOMA — Loop continuo ate encontrar equilibrio otimo.
Roda sozinho, testa variacoes, salva a melhor, repete.

Objetivo: maximizar fitness = discriminacao * magnitude
  discriminacao: desvio padrao entre notas (quanto mais espalhado, melhor)
  magnitude: media das notas (quanto mais alto, melhor)
  equilibrio: discriminacao * magnitude (ambos precisam ser bons)

Uso: python evoluir_autonomo.py
"""
import sys, os, json, math, random as _rand

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MCR import *
from MCR import _EQUACAO_ATUAL, MCRMotor, MCRByteUtils, MCRSignatureExpansiva

MCR_PATH = os.path.join(os.path.dirname(__file__), 'MCR.py')
CACHE_PATH = os.path.join(os.path.dirname(__file__), 'cache', 'evolucao.json')

def _carregar_motor():
    """Cria motor com dados de TEXTO E NUMERICOS para testar variacoes."""
    m = MCRMotor()

    # Textos
    m.alimentar(
        'SPA e o sistema de progressao do aventureiro com dominios '
        'elementais Fogo Gelo Terra Energia e Sagrado cada dominio tem '
        '25 niveis de habilidade que o jogador pode evoluir', 'spa')
    m.alimentar(
        'SHC e o sistema de habilidades contextuais com 5 camadas postura '
        'nivel sinergia estado e condicao as sinergias combinam dominios '
        'elementais para criar efeitos unicos', 'shc')
    m.alimentar(
        'O NPC ferreiro em Eridanus se chama Bruno Ferro Forte ele vende '
        'armaduras de ferro e aco espadas basicas e escudos na praca '
        'central ao lado da forja', 'npc')
    m.alimentar(
        'A arvore de Natal do servidor MCR fica na praca central de '
        'Eridanus com luzes magicas que os jogadores acendem resolvendo '
        'desafios durante o evento de fim de ano', 'natal')
    m.alimentar(
        'Eridanus e a cidade inicial do projeto MCR construida as margens '
        'do Lago Cristalino possui porto praca central templo forja e '
        'mercado a marinha de Eridanus patrulha o lago', 'eridanus')

    # Sequencias numericas SOBREPOSTAS
    seqs_fib = [
        [1, 1, 2, 3, 5, 8, 13],
        [1, 2, 3, 5, 8, 13, 21],
        [2, 3, 5, 8, 13, 21, 34],
        [3, 5, 8, 13, 21, 34, 55],
        [5, 8, 13, 21, 34, 55, 89],
    ]
    for i, s in enumerate(seqs_fib):
        m.alimentar(' '.join(str(x) for x in s), f'fib_{i}')

    seqs_quad = [
        [1, 4, 9, 16, 25, 36, 49],
        [4, 9, 16, 25, 36, 49, 64],
        [9, 16, 25, 36, 49, 64, 81],
    ]
    for i, s in enumerate(seqs_quad):
        m.alimentar(' '.join(str(x) for x in s), f'quad_{i}')

    seqs_pot = [
        [1, 2, 4, 8, 16, 32, 64],
        [2, 4, 8, 16, 32, 64, 128],
        [4, 8, 16, 32, 64, 128, 256],
    ]
    for i, s in enumerate(seqs_pot):
        m.alimentar(' '.join(str(x) for x in s), f'pot_{i}')

    return m

def _testar_equacao(motor, formula):
    """Testa uma formula e retorna metricas de qualidade."""
    _EQUACAO_ATUAL['formula'] = formula

    pares = [
        # Textos
        ('spa', 'shc'), ('spa', 'npc'), ('spa', 'natal'),
        ('spa', 'eridanus'), ('shc', 'npc'), ('shc', 'natal'),
        ('shc', 'eridanus'), ('npc', 'natal'), ('npc', 'eridanus'),
        ('natal', 'eridanus'),
        # Numericos (sobrepostos)
        ('fib_0', 'fib_1'), ('fib_1', 'fib_2'),
        ('fib_2', 'fib_3'), ('fib_3', 'fib_4'),
        ('quad_0', 'quad_1'), ('quad_1', 'quad_2'),
        ('pot_0', 'pot_1'), ('pot_1', 'pot_2'),
        # Misto
        ('fib_0', 'spa'), ('quad_0', 'shc'), ('pot_0', 'npc'),
    ]

    notas = []
    for a, b in pares:
        if a in motor.topicos and b in motor.topicos:
            c = motor.conectar(a, b, forcar=True)
            if c:
                notas.append(c['nota'])

    if not notas:
        return 0, 0, 0

    media = sum(notas) / len(notas)
    variancia = sum((n - media) ** 2 for n in notas) / len(notas)
    discriminacao = math.sqrt(variancia)

    fitness = discriminacao * media
    return round(fitness, 4), round(media, 2), round(discriminacao, 3)

def _gerar_variacoes(formula_atual):
    """Gera variacoes da formula."""
    bases = [
        'by + pa + tk', 'by * pa + tk',
        '(by + pa + tk) / 3', 'max(by, pa, tk)',
        'by + pa', 'pa + tk', 'by + tk',
        'by * pa + tk + h', 'pa + h',
    ]
    variacoes = []
    for f in bases:
        if f != formula_atual:
            variacoes.append(f)

    # Variacoes com pesos nos componentes
    for peso_by in [0.5, 1, 2, 3]:
        for peso_pa in [1, 3, 5, 8, 13]:
            variacoes.append(f'{peso_by}*by + {peso_pa}*pa + tk')
            variacoes.append(f'{peso_by}*by + {peso_pa}*pa')

    _rand.shuffle(variacoes)
    return variacoes[:25]

def main():
    print('')
    print('MCR EVOLUCAO AUTONOMA')
    print('Loop continuo ate encontrar equilibrio otimo.')
    print('')

    # Carrega ou inicia estado
    historico = []
    melhor_fitness = 0
    melhor_formula = _EQUACAO_ATUAL.get('formula', 'by * pa + tk')
    melhores_metricas = (0, 0, 0)

    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r') as f:
                cache = json.load(f)
            historico = cache.get('historico', [])
            melhor_fitness = cache.get('melhor_fitness', 0)
            melhor_formula = cache.get('melhor_formula', 'by * pa + tk')
            print(f'  Retomando de sessao anterior: {len(historico)} geracoes')
            print(f'  Melhor: {melhor_formula} fitness={melhor_fitness}')
            print('')
        except Exception:
            pass

    motor = _carregar_motor()
    geracao = len(historico)
    estagnacao = 0

    try:
        while estagnacao < 8:
            geracao += 1

            # Testa formula atual
            fit_atual, med_atual, disc_atual = _testar_equacao(motor, melhor_formula)

            variacoes = _gerar_variacoes(melhor_formula)
            encontrou_melhor = False

            for formula_var in variacoes:
                fit, med, disc = _testar_equacao(motor, formula_var)

                if fit > melhor_fitness:
                    melhor_fitness = fit
                    melhor_formula = formula_var
                    melhores_metricas = (med, disc, fit)
                    encontrou_melhor = True
                    estagnacao = 0

                    # Salva imediatamente
                    _EQUACAO_ATUAL['formula'] = melhor_formula
                    try:
                        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
                        with open(CACHE_PATH, 'w') as f:
                            json.dump({
                                'melhor_formula': melhor_formula,
                                'melhor_fitness': melhor_fitness,
                                'melhores_metricas': melhores_metricas,
                                'historico': historico[-100:],
                            }, f, indent=2)
                    except Exception:
                        pass

                    print(f'  G{geracao:3d}: NOVO RECORDE! {formula_var[:40]:40s} '
                          f'fit={fit:.4f} med={med:.2f} disc={disc:.3f}')
                    break

            if not encontrou_melhor:
                estagnacao += 1
                if estagnacao == 1 or estagnacao % 2 == 0:
                    print(f'  G{geracao:3d}: estagnado ({estagnacao}/8) '
                          f'melhor={melhor_formula[:30]} fit={melhor_fitness:.4f}')

    except KeyboardInterrupt:
        print('')
        print('  Interrompido pelo usuario.')

    # Relatorio final
    print('')
    print('=' * 65)
    print('  EVOLUCAO CONCLUIDA')
    print('=' * 65)
    print(f'  Geracoes: {geracao}')
    print(f'  Melhor formula: {melhor_formula}')
    print(f'  Fitness: {melhor_fitness}')
    print(f'  Media: {melhores_metricas[0]}')
    print(f'  Discriminacao: {melhores_metricas[1]}')
    print('')
    print('  Aplicando ao MCR.py...')

    # Aplica a melhor formula no MCR.py
    with open(MCR_PATH, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    import re
    conteudo = re.sub(
        r"'formula':\s*'[^']*'",
        f"'formula': '{melhor_formula}'",
        conteudo
    )

    with open(MCR_PATH, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f'  Formula aplicada: {melhor_formula}')
    print('')
    print(f'  Para continuar evoluindo: python evoluir_autonomo.py')
    print('')

if __name__ == '__main__':
    main()
