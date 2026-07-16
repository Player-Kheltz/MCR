#!/usr/bin/env python3
"""
test_fase2_treinamento.py — Testes da FASE 2: Treinamento.

Testa:
  1. MCRSQLite conversa populado (>10K estados)
  2. MCRSQLite codigo populado (>1K estados)
  3. Predicoes de conversa funcionam
  4. Predicoes de codigo funcionam
  5. Entropia media dentro do esperado
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mcr.mcr_sqlite import MCRSQLite
from pathlib import Path

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

PASS, FAIL, ERROR = 0, 0, 0

def testar(nome, condicao, detalhe=''):
    global PASS, FAIL, ERROR
    if condicao is True:
        PASS += 1
        print(f'  [PASS] {nome}')
    elif condicao is False:
        FAIL += 1
        print(f'  [FAIL] {nome}' + (f' - {detalhe}' if detalhe else ''))
    else:
        ERROR += 1
        print(f'  [ERROR] {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERROR
    print('=' * 60)
    print('  TESTE FASE 2 — Treinamento Completo')
    print('=' * 60)

    # ─── 1. Conversa ────────────────────────────────
    print('\n[1] MCRSQLite — Conversa')
    db_conv = Path(os.path.join(_BASE, 'cache', 'mcr_conversa.db'))
    testar('DB conversa existe', db_conv.exists())
    if db_conv.exists():
        size = db_conv.stat().st_size / 1024
        testar(f'DB conversa >10KB', size > 10, f'{size:.0f}KB')

        mcr_conv = MCRSQLite(str(db_conv), n_max=5, identidade='conversa')
        estados = mcr_conv.conn.execute('SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
        trans = mcr_conv.conn.execute('SELECT COUNT(*) FROM trans').fetchone()[0]
        h = mcr_conv.entropia_media()

        testar('>10.000 estados', estados > 10000, f'{estados}')
        testar('>50.000 transicoes', trans > 50000, f'{trans}')
        testar('Entropia baixa (<0.5 = previsivel)', h < 0.5, f'H={h:.4f}')

        # Predictions should exist for common words
        acertos = 0
        for w in ['you', 'hello', 'welcome', 'mission', 'yes', 'orcs']:
            p, _ = mcr_conv.predizer(w)
            if p:
                acertos += 1
        testar('Predicoes para palavras comuns', acertos >= 4, f'{acertos}/6')
        mcr_conv.conn.close()

    # ─── 2. Codigo ─────────────────────────────────
    print('\n[2] MCRSQLite — Codigo')
    db_cod = Path(os.path.join(_BASE, 'cache', 'mcr_codigo.db'))
    testar('DB codigo existe', db_cod.exists())
    if db_cod.exists():
        mcr_cod = MCRSQLite(str(db_cod), n_max=10, identidade='codigo')
        estados = mcr_cod.conn.execute('SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
        trans = mcr_cod.conn.execute('SELECT COUNT(*) FROM trans').fetchone()[0]
        h = mcr_cod.entropia_media()

        testar('>1.000 estados codigo', estados > 1000, f'{estados}')
        testar('Entropia codigo (<0.5)', h < 0.5, f'H={h:.4f}')

        # Code predictions should be valid
        acertos = 0
        for w in ['function', 'local', 'Game', 'return', 'end', 'if']:
            p, _ = mcr_cod.predizer(w)
            if p:
                acertos += 1
        testar('Predicoes de codigo', acertos >= 4, f'{acertos}/6')

        # Game. should predict createMonsterType or createNpcType
        p, _ = mcr_cod.predizer('Game')
        testar('Game -> . (member access)', p in ('.', ':', 'createMonsterType'),
               f'Game -> "{p}"' if p else 'sem predicao')
        mcr_cod.conn.close()

    # ─── 3. Geracao Markoviana ──────────────────────
    print('\n[3] Geracao de texto via MCR')
    if db_conv.exists():
        mcr_conv = MCRSQLite(str(db_conv), n_max=5, identidade='conversa')
        cadeia = mcr_conv.gerar('hello', passos=5)
        testar('Geracao de cadeia', len(cadeia) >= 2, f'{len(cadeia)} tokens: {cadeia}')
        mcr_conv.conn.close()

    if db_cod.exists():
        mcr_cod = MCRSQLite(str(db_cod), n_max=10, identidade='codigo')
        cadeia_cod = mcr_cod.gerar('function', passos=5)
        testar('Geracao de cadeia codigo', len(cadeia_cod) >= 2,
               f'{len(cadeia_cod)} tokens: {" ".join(map(str,cadeia_cod))[:80]}')
        mcr_cod.conn.close()

    # ─── Resumo ─────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERROR
    print(f'  Resultado: {PASS}/{total} pass, {FAIL} fail, {ERROR} error')
    print('=' * 60)
    return FAIL == 0 and ERROR == 0

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
