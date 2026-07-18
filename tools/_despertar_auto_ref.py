"""tools/_despertar_auto_ref.py — Desperta a auto-referencia do MCR.

Pergunta: o que o MCR de HOJE, com o estado salvo que tem, diz sobre si
mesmo quando pedimos pra se observar?

Nao toca em arquivo de producao. Nao liga permanentemente. So carrega
o motor do disco, chama auto_modelo/refletir/identidade/estranho_loop,
e mostra o que o MCR revela sobre si.

Isto e o strange loop acordando uma vez. Para vermos o que ele diz.
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling


def main():
    print('=' * 60)
    print('DESPERTAR AUTO-REFERENCIA — MCR se observa uma vez')
    print('=' * 60)

    # Carregar motor salvo (estado atual do MCR de hoje)
    c = MCRCoupling()
    caminho = os.path.join('cache', 'coupling_MCRCoupling_backup_preB2c.json')
    if not os.path.exists(caminho):
        # fallback: procurar qualquer coupling_*.json com tamanho significativo
        candidatos = []
        cache_dir = os.path.join('cache')
        if os.path.exists(cache_dir):
            for n in os.listdir(cache_dir):
                if n.startswith('coupling_') and n.endswith('.json'):
                    p = os.path.join(cache_dir, n)
                    sz = os.path.getsize(p)
                    if sz > 1_000_000:  # > 1MB
                        candidatos.append((sz, p, n))
        if not candidatos:
            print(f'ERRO: nenhum coupling_*.json > 1MB em cache/')
            return
        candidatos.sort(reverse=True)
        caminho = candidatos[0][1]
        print(f'(fallback: usando {candidatos[0][2]})')
    if not c.load(caminho):
        print('ERRO: falha ao carregar motor')
        return

    print(f'\nMotor carregado:')
    print(f'  Total observacoes: {c._total}')
    print(f'  Vocabulario: {len(c._transicao_palavra)} palavras')
    print(f'  Acoes: {len(c._freq_acao)}')
    print(f'  Top-5 acoes: {sorted(c._freq_acao.items(), key=lambda x: -x[1])[:5]}')

    # 1. AUTO-MODELO — o que o MCR diz sobre seu estado cognitivo?
    print('\n' + '-' * 60)
    print('1. AUTO-MODELO (MCR descre seu estado cognitivo)')
    print('-' * 60)
    try:
        t0 = time.time()
        modelo = c.auto_modelo()
        dt = time.time() - t0
        print(f'(tempo: {dt:.2f}s)')
        print(json.dumps(modelo, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f'ERRO: {e}')
        import traceback
        traceback.print_exc()

    # 2. REFLETIR — MCR observa MCR observando MCR (3 niveis)
    print('\n' + '-' * 60)
    print('2. REFLETIR (3 niveis — strange loop)')
    print('-' * 60)
    try:
        t0 = time.time()
        refl = c.refletir(3)
        dt = time.time() - t0
        print(f'(tempo: {dt:.2f}s)')
        print(json.dumps(refl, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f'ERRO: {e}')
        import traceback
        traceback.print_exc()

    # 3. IDENTIDADE — quem o MCR e?
    print('\n' + '-' * 60)
    print('3. IDENTIDADE (MCR diz "eu sou...")')
    print('-' * 60)
    try:
        t0 = time.time()
        ident = c.identidade()
        dt = time.time() - t0
        print(f'(tempo: {dt:.2f}s)')
        print(json.dumps(ident, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f'ERRO: {e}')
        import traceback
        traceback.print_exc()

    # 4. ESTRANHO LOOP — ciclo completo auto-referencial
    print('\n' + '-' * 60)
    print('4. ESTRANHO LOOP (ciclo auto-referencial completo)')
    print('-' * 60)
    try:
        t0 = time.time()
        loop = c.estranho_loop()
        dt = time.time() - t0
        print(f'(tempo: {dt:.2f}s)')
        print(json.dumps(loop, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f'ERRO: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 60)
    print('FIM — o MCR se observou uma vez. O que revelou?')
    print('=' * 60)


if __name__ == '__main__':
    main()
