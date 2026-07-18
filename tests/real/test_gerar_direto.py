"""
TESTE DIRETO — N-adaptativo gerar() ANTES vs DEPOIS
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mcr.mcr_sqlite import MCRSQLite

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def main():
    print('=' * 60)
    print('TESTE DIRETO: gerar() N-adaptativo')
    print('=' * 60)

    mcr = MCRSQLite(os.path.join(_BASE, 'cache', 'mcr_conversa.db'), n_max=5, identidade='conversa')

    sementes = [
        'hello', 'welcome', 'dragon', 'sword', 'custa', 'you',
        'buy', 'sell', 'magic', 'orcs', 'help', 'quest',
    ]

    print('\nGERACAO COM N-ADAPTATIVO (N=1..5):')
    for s in sementes:
        cadeia = mcr.gerar(s, passos=8)
        n_utilizado = min(len(cadeia), 5)
        texto = ' '.join(cadeia)
        print(f'  "{s}" ({len(cadeia)} tokens): {texto[:100]}')

    # Tambem testar geracao manual com N>1
    print('\n\nGERACAO MANUAL COM N=3 (tokens concatenados):')
    for s in sementes[:6]:
        p1, c1 = mcr.predizer(s)
        if p1:
            ctx2 = f'{s}|{p1}'
            p2, c2 = mcr.predizer(ctx2)
            if p2:
                ctx3 = f'{s}|{p1}|{p2}'
                p3, c3 = mcr.predizer(ctx3)
                print(f'  "{s}" -> N=1:{p1}({c1:.3f}) N=2:{p2}({c2:.3f}) N=3:{p3}({c3:.3f})')

    mcr.conn.close()

if __name__ == '__main__':
    main()
