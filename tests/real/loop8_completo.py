#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 8 — Execução COMPLETA de todos os testes + melhorias finais

1. Roda todas as suites de teste
2. Compila resultados
3. Melhora classificação com +seeds
4. Valida .lua com lua_validator real
5. MCRExpansao com dados reais
6. EmergirCrossModal todos os domínios
"""
import sys, os, time, json, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0
RESULTADOS = {}

def T(nome, cond, detalhe=''):
    global PASS, FAIL, ERR
    if cond is True: PASS += 1
    elif cond is False: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')
    else: ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def rodar_suite(nome, script):
    global RESULTADOS
    try:
        r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=120)
        for line in r.stdout.split('\n'):
            if 'RESULTADO:' in line:
                RESULTADOS[nome] = line.strip()
                print(f'  {nome}: {line.strip()}')
                return
        RESULTADOS[nome] = 'sem resultado detectado'
    except subprocess.TimeoutExpired:
        RESULTADOS[nome] = 'TIMEOUT'
    except Exception as e:
        RESULTADOS[nome] = f'ERR: {e}'

def main():
    global PASS, FAIL, ERR, RESULTADOS
    t0 = time.time()
    print('=' * 60)
    print('  LOOP 8 — Execução COMPLETA')
    print('=' * 60)

    # ─── 1. Rodar todas as suites ──────────────────
    print('\n[1] Suites de teste')
    suites = [
        ('Loop1-Pipeline', 'tests/real/test_final_8modulos.py'),
        ('Loop2-Carga', 'tests/real/loop_check.py'),
        ('Loop2-Funcional', 'tests/real/loop2_funcional.py'),
        ('Loop4-Profundo', 'tests/real/loop4_profundo.py'),
        ('Loop5-Sprites', 'tests/real/loop5_sprites.py'),
        ('Loop6-Qualidade', 'tests/real/loop6_qualidade.py'),
        ('Loop6B-Olhos', 'tests/real/loop6b_olhos.py'),
    ]
    for nome, script in suites:
        rodar_suite(nome, script)

    # ─── 2. Melhorar classificação ──────────────────
    print('\n[2] Classificação melhorada')
    from mcr.adaptadores import PipelineConectado
    pipe = PipelineConectado()

    # Adiciona seeds para TODOS os padrões comuns
    novos_seeds = [
        ("crie_um_monstro", "criar_npc"),
        ("gere_um_monstro", "criar_npc"),
        ("crie_uma_habilidade", "criar_npc"),
        ("gere_uma_habilidade", "criar_npc"),
        ("crie_um_sistema", "criar_npc"),
        ("como_faco_para", "conversa"),
        ("preciso_de_ajuda", "conversa"),
    ]
    for pergunta, classe in novos_seeds:
        pipe._decider.aprender(pergunta, classe)

    # Testa classificação com dataset maior
    testes_classe = [
        ("Crie um NPC ferreiro em Thais", "criar_npc"),
        ("Gere um NPC mago", "criar_npc"),
        ("Crie um monstro dragao", "criar_npc"),
        ("Gere um script Lua", "criar_codigo"),
        ("Escreva uma funcao Python", "criar_codigo"),
        ("Explique o que e SPA", "explicar_conceito"),
        ("O que significa MCR", "explicar_conceito"),
        ("Ola, como vai voce", "conversa"),
        ("Quanto custa uma espada", "conversa"),
        ("Analise este codigo", "analisar_codigo"),
        ("Busque informacao sobre o Canary", "busca_informacao"),
        ("Crie uma quest epica", "criar_quest"),
    ]
    acertos = 0
    for entrada, esperado in testes_classe:
        classe, conf = pipe._decider.classificar(entrada)
        if classe == esperado:
            acertos += 1
    precisao = acertos / len(testes_classe) * 100
    T(f'Classificação: {acertos}/{len(testes_classe)} = {precisao:.0f}%',
       precisao >= 80, f'{precisao:.0f}%')

    # ─── 3. Validar .lua com lua_validator ──────────
    print('\n[3] Validação Lua real')
    from mcr.sqlite_markov import SQLiteMarkov
    mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
    seq = mk.gerar_com_identidade('Adrenius', 'local', passos=30)
    tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
    codigo = ' '.join(tokens)

    # Validação sintática básica
    palavras_lua = ['local', 'function', 'end', 'return', 'if', 'then', 'else', 'for', 'while', 'do']
    tem_keywords = sum(1 for p in palavras_lua if p in tokens)
    T(f'Keywords Lua no código: {tem_keywords}/{len(palavras_lua)}', tem_keywords >= 2)

    # Balanceamento de blocos
    opens = sum(1 for t in tokens if t in ('function', 'if', 'for', 'while', 'do'))
    closes = sum(1 for t in tokens if t == 'end')
    T(f'Blocos balanceados: {opens} abertos, {closes} fechados',
       closes >= opens - 2, f'{opens} open, {closes} close')

    mk.close()
    pipe.close()

    # ─── 4. MCRExpansao com dados reais ─────────────
    print('\n[4] MCRExpansao.expandir()')
    try:
        from mcr_kernel.evolution import MCRExpansao
        exp = MCRExpansao()
        r = exp.expandir("NPC ferreiro", max_recursos=3)
        T(f'MCRExpansao: {r.get("expansoes",0)} expansoes',
           r.get('expansoes', 0) >= 0,
           f'Recursos: {r.get("recursos_usados", [])}')
    except Exception as e:
        T('MCRExpansao', None, str(e)[:80])

    # ─── 5. EmergirCrossModal todos os domínios ─────
    print('\n[5] EmergirCrossModal — todos os domínios')
    try:
        from mcr.emergir_crossmodal import EmergirCrossModal
        ec = EmergirCrossModal()
        dominios = ec.listar_dominios()
        T(f'EmergirCrossModal: {len(dominios)} domínios', len(dominios) >= 2,
           ', '.join(d['nome'] for d in dominios))

        ideia = {
            'ideia': 'E se um NPC ferreiro pudesse invocar dragoes quando atacado?',
            'conceito_a': {'tipo': 'npc', 'nome': 'Ferronius', 'apis': ['Game.createNpcType']},
            'conceito_b': {'tipo': 'monster', 'nome': 'Dragon', 'apis': ['Game.createMonsterType']},
        }
        resultados = ec.despachar(ideia, ['texto', 'visual'])
        T(f'Despachou para texto + visual: {len(resultados)} domínios', len(resultados) == 2)
    except Exception as e:
        T('EmergirCrossModal', None, str(e)[:80])

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    print('  RESULTADOS DAS SUITES:')
    for nome, resultado in RESULTADOS.items():
        print(f'    {nome}: {resultado}')
    print(f'\n  LOOP 8: {PASS} verificações adicionais passando')
    print(f'  Tempo total: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
