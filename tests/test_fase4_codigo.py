#!/usr/bin/env python3
"""Testes da FASE 4: Geracao de Codigo Multi-Linguagem."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mcr.gerador_codigo import GeradorCodigo

PASS, FAIL = 0, 0

def testar(nome, condicao, detalhe=''):
    global PASS, FAIL
    if condicao is True:
        PASS += 1; print(f'  [PASS] {nome}')
    else:
        FAIL += 1; print(f'  [FAIL] {nome}' + (f' - {detalhe}' if detalhe else ''))

def main():
    global PASS, FAIL
    print('=' * 60)
    print('  TESTE FASE 4 — Geracao de Codigo')
    print('=' * 60)

    g = GeradorCodigo()
    s = g.stats()
    print(f'\n  Backend: {s["estados"]} estados, H={s["entropia"]}')

    # ─── 1. Lua NPC ─────────────────────────────
    print('\n[1] Lua — NPC')
    r = g.gerar_lua(tipo='npc', semente='local')
    testar('Lua NPC gerado com sucesso', len(r['codigo']) > 50)
    testar('Contem Game.createNpcType', 'Game.createNpcType' in r['codigo'])
    testar('Sintaxe balanceada', r['valido'], r.get('erro', ''))

    # ─── 2. Lua Monster ─────────────────────────
    print('\n[2] Lua — Monster')
    r = g.gerar_lua(tipo='monster', semente='local')
    testar('Lua Monster gerado', len(r['codigo']) > 50)
    testar('Contem Game.createMonsterType', 'Game.createMonsterType' in r['codigo'])
    testar('Sintaxe balanceada', r['valido'], r.get('erro', ''))

    # ─── 3. Python ──────────────────────────────
    print('\n[3] Python — Function')
    r = g.gerar_python(tipo='function', semente='def')
    testar('Python gerado', len(r['codigo']) > 10)
    testar('Contem def', 'def ' in r['codigo'])
    testar('Sintaxe valida (ast.parse)', r['valido'], r.get('erro', ''))

    # ─── 4. SQL ─────────────────────────────────
    print('\n[4] SQL — SELECT')
    r = g.gerar_sql(tipo='select', semente='SELECT')
    testar('SQL SELECT gerado', len(r['codigo']) > 5)
    testar('Contem SELECT', 'SELECT' in r['codigo'].upper())

    print('\n[5] SQL — CREATE')
    r = g.gerar_sql(tipo='create', semente='CREATE')
    testar('SQL CREATE gerado', len(r['codigo']) > 5)
    testar('Contem CREATE', 'CREATE' in r['codigo'].upper())

    # ─── 5. Sem template ────────────────────────
    print('\n[6] Geracao livre (sem template)')
    r = g.gerar('lua', 'function', passos=15)
    testar('Geracao livre produz texto', len(r['codigo']) > 10)

    # ─── 6. Taxa de acerto ──────────────────────
    print('\n[7] Taxa de validacao')
    validos = 0
    total = 0
    for i in range(10):
        r = g.gerar_python(tipo='function', semente='def')
        total += 1
        if r['valido']:
            validos += 1
    taxa = validos / max(total, 1)
    testar(f'Taxa de validacao Python > 50%', taxa > 0.5,
           f'{validos}/{total} = {taxa:.0%}')

    g.close()

    print('\n' + '=' * 60)
    total_tests = PASS + FAIL
    print(f'  Resultado: {PASS}/{total_tests} pass, {FAIL} fail')
    print('=' * 60)
    return FAIL == 0

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
