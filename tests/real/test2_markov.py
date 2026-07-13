"""
TESTE 2 — Qualidade REAL da Predicao Markov (N=1 vs contexto)

Testes:
  A. Para palavras de entrada comuns, qual o próximo token?
  B. Quantos estados têm > 1 opção de transição? (= densidade real)
  C. Cadeia de 5 tokens partindo de palavras comuns — faz sentido?
  D. Entropia media REAL vs entropia maxima teorica
"""
import sys, os, sqlite3, math, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

DB = os.path.join(_BASE, 'cache', 'mcr_conversa.db')
IDENTIDADE = 'conversa'

def main():
    conn = sqlite3.connect(DB)

    # ─── A. Top predições ────────────────────────
    print('=' * 60)
    print('A. TOP PREDICOES PARA PALAVRAS COMUNS')
    print('=' * 60)

    palavras = ['you', 'hello', 'welcome', 'mission', 'yes', 'dragon',
                'sword', 'orcs', 'magic', 'buy', 'sell', 'help',
                'custa', 'voc', 'pode', 'para', 'com', 'que', 'nao', 'sim']

    for p in palavras:
        key = f'{IDENTIDADE}|{p}'
        rows = conn.execute(
            "SELECT next, count FROM trans WHERE key=? ORDER BY count DESC LIMIT 3",
            (key,)).fetchall()
        if rows:
            total = sum(r[1] for r in rows)
            preds = ', '.join(f'{r[0]}({r[1]}/{total})' for r in rows)
            print(f'  "{p}" -> {preds}')
        else:
            print(f'  "{p}" -> SEM DADOS')

    # ─── B. Densidade ───────────────────────────
    print('\n' + '=' * 60)
    print('B. DENSIDADE DAS TRANSICOES')
    print('=' * 60)

    # Quantos estados têm > 1 opção?
    rows = conn.execute("""
        SELECT key, COUNT(*) as cnt
        FROM trans
        GROUP BY key
    """).fetchall()

    opcoes = [r[1] for r in rows]
    unicas = sum(1 for o in opcoes if o == 1)
    multiplas = sum(1 for o in opcoes if o > 1)
    muitas = sum(1 for o in opcoes if o >= 5)

    print(f'  Total estados: {len(opcoes)}')
    print(f'  Com 1 opcao: {unicas} ({unicas/len(opcoes)*100:.1f}%)')
    print(f'  Com 2+ opcoes: {multiplas} ({multiplas/len(opcoes)*100:.1f}%)')
    print(f'  Com 5+ opcoes: {muitas} ({muitas/len(opcoes)*100:.1f}%)')
    print(f'  Media opcoes/estado: {sum(opcoes)/len(opcoes):.2f}')

    # ─── C. Contagem máxima ─────────────────────
    print('\n' + '=' * 60)
    print('C. CONTAGEM MAXIMA POR TRANSICAO')
    print('=' * 60)

    rows = conn.execute("""
        SELECT key, next, count
        FROM trans
        ORDER BY count DESC
        LIMIT 20
    """).fetchall()

    for r in rows:
        key_short = r[0].replace(IDENTIDADE + '|', '')
        print(f'  {key_short[:40]:40s} -> {r[1]:20s} ({r[2]}x)')

    # ─── D. Distribuicao de frequencia ──────────
    print('\n' + '=' * 60)
    print('D. DISTRIBUICAO DE FREQUENCIA')
    print('=' * 60)

    freq = [r[1] for r in opcoes]  # reusa opcoes = numero de alternativas
    ranges = [(1, 1), (2, 2), (3, 4), (5, 9), (10, 20), (21, 999)]
    for lo, hi in ranges:
        count = sum(1 for f in freq if lo <= f <= hi)
        label = f'{lo}' if lo == hi else f'{lo}-{hi}'
        print(f'  {label:6s} alternativas: {count:6d} estados ({count/len(freq)*100:5.1f}%)')

    # ─── E. Teste de geração ────────────────────
    print('\n' + '=' * 60)
    print('E. GERACAO DE CADEIA (N=1)')
    print('=' * 60)

    for semente in ['you', 'hello', 'dragon', 'custa', 'yes']:
        atual = semente
        cadeia = [atual]
        for _ in range(8):
            key = f'{IDENTIDADE}|{atual}'
            row = conn.execute(
                "SELECT next FROM trans WHERE key=? ORDER BY count DESC LIMIT 1",
                (key,)).fetchone()
            if row:
                atual = row[0]
                cadeia.append(atual)
            else:
                break
        print(f'  "{semente}" -> {" ".join(cadeia)}')

    conn.close()

if __name__ == '__main__':
    main()
