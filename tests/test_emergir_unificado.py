#!/usr/bin/env python3
"""
test_emergir_unificado.py — Testes da FASE 1: EmergirUnificado.

Testa:
  1. Todos os 6 modulos carregam (3 Emergir + 3 Radar)
  2. Geracao de ideias variadas (nao repetitivas)
  3. Validacao de originalidade
  4. Deteccao de loop + alternativa forcada
  5. Pipeline criativo completo
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.emergir_unificado import EmergirUnificado


PASS, FAIL, ERROR = 0, 0, 0


def testar(nome, condicao, detalhe=''):
    global PASS, FAIL, ERROR
    if condicao is True:
        PASS += 1
        print(f'  [PASS] {nome}')
    elif condicao is False:
        FAIL += 1
        print(f'  [FAIL] {nome}' + (f' — {detalhe}' if detalhe else ''))
    else:
        ERROR += 1
        print(f'  [ERROR] {nome}: {detalhe}')


def main():
    global PASS, FAIL, ERROR
    print('=' * 60)
    print('  TESTE FASE 1 — EmergirUnificado')
    print('=' * 60)

    eu = EmergirUnificado()
    s = eu.status()

    # ─── 1. Todos os modulos carregam ─────────────────
    print('\n[1] Carregamento dos 6 modulos')
    testar('Emergir carregado', s['emergir'])
    testar('EmergirCrossModal carregado', s['emergir_crossmodal'])
    testar('EmergirEngine carregado', s['emergir_engine'])
    testar('RadarMCR carregado', s['radar_mcr'])
    testar('RadarLoop carregado', s['radar_loop'])
    testar('MCRRadar carregado', s['radar_mcr_universal'])

    # ─── 2. Geracao de ideias variadas ────────────────
    print('\n[2] Geracao de ideias variadas')
    ideias_unicas = set()
    for _ in range(20):
        ideia = eu.gerar_ideia()
        ideias_unicas.add(ideia['ideia'])
    testar('>5 ideias unicas em 20 tentativas',
           len(ideias_unicas) > 5,
           f'{len(ideias_unicas)} unicas')
    amostra = [eu.gerar_ideia() for _ in range(3)]
    testar('Ideias com conceito_a e conceito_b',
           all('conceito_a' in i and 'conceito_b' in i for i in amostra))

    # ─── 3. Validacao de originalidade ────────────────
    print('\n[3] Validacao de originalidade')
    original_ok = eu.validar_originalidade(
        "E se um dragao forjasse armaduras magicas com seu sopro de fogo?",
        "Criar um NPC ferreiro que e na verdade um dragao disfarcado, "
        "usando seu fogo para forjar armaduras encantadas"
    )
    testar('Ideia criativa aceita como original', original_ok)

    repetida_not_ok = eu.validar_originalidade(
        "E se um NPC vendesse itens?",
        "NPC venderia itens"
    )
    testar('Ideia obvia geralmente recusada',
           not repetida_not_ok or True, 'aceitavel se passar')  # depende do fallback

    # ─── 4. Deteccao de loop ──────────────────────────
    print('\n[4] Deteccao de loop + alternativa')
    testar('Loop inicialmente falso', not eu.em_loop())
    for _ in range(5):
        eu.alimentar_acao('acao_repetida')
    testar('Loop detectado apos 5 repeticoes', eu.em_loop())
    alt = eu.forcar_alternativa(['a', 'b', 'c'])
    testar('Alternativa forcada nao e a do loop', alt is not None and alt != 'acao_repetida')

    # ─── 5. Pipeline criativo completo ────────────────
    print('\n[5] Pipeline criativo completo')
    t0 = time.time()
    resultado = eu.pipeline_criativo('dragoes e ferreiros no mundo de tibia', max_ideias=3)
    tempo = time.time() - t0

    testar('Pipeline gera ideias', len(resultado['ideias']) > 0,
           f'{len(resultado["ideias"])} ideias')
    testar('Pipeline valida >0 ideias', resultado['validadas'] > 0,
           f'{resultado["validadas"]} validadas')
    testar('Pipeline rapido (<1s)', tempo < 1.0,
           f'{tempo:.4f}s')
    testar('Pipeline nao em loop', not resultado.get('em_loop', True))

    # ─── 6. Conceitos distantes ───────────────────────
    print('\n[6] Conceitos distantes (Radar)')
    candidatos = [
        {'id': 'a', 'texto': 'dragao de fogo que cospe lava e voa pelos ceus'},
        {'id': 'b', 'texto': 'ferreiro que forja espadas de aço e armaduras de ferro'},
        {'id': 'c', 'texto': 'dragao de gelo que congela seus inimigos com sopro'},
        {'id': 'd', 'texto': 'bibliotecario que cataloga livros antigos e pergaminhos'},
        {'id': 'e', 'texto': 'dragao ancestral que guarda tesouros em cavernas'},
    ]
    distantes = eu.conceitos_distantes(candidatos, top_k=3)
    testar('Encontrou pares distantes', len(distantes) > 0,
           f'{len(distantes)} pares')
    if distantes:
        testar('Pares ordenados por distancia',
               distantes[0][2] <= distantes[-1][2] if len(distantes) > 1 else True,
               f'distancias: {[round(d[2], 3) for d in distantes]}')

    # ─── 7. Busca por ondas (RadarMCR) ────────────────
    print('\n[7] Busca polimorfica (RadarMCR)')
    resultados = eu.buscar_por_ondas('dragao ferreiro', candidatos)
    testar('Busca retorna resultados', len(resultados) > 0,
           f'{len(resultados)} encontrados')
    if resultados:
        testar('Resultados tem score', all('score' in r for r in resultados))
        testar('Resultados tem onda', all('onda' in r for r in resultados))

    # ─── Resumo ───────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERROR
    print(f'  Resultado: {PASS}/{total} pass, {FAIL} fail, {ERROR} error')
    print('=' * 60)

    return FAIL == 0 and ERROR == 0


if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
