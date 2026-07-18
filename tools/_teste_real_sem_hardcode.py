"""tools/_teste_real_sem_hardcode.py — Teste real do MCR SEM hardcode.

Pergunta: o que o MCR de HOJE responde SOZINHO, sem os 80 fatos hardcoded
do AutoConhecimento, sem o template de identidade do AutoReferencia?

Fluxo:
  1. Carregar motor do disco (167K obs, Wikipedia+Rosetta+Tatoeba)
  2. Criar MCRChat SEM chamar inicializar_conhecimento() — BC vazio
  3. Forcar coldstart a pular direto pra CHAT (sem perguntas)
  4. Fazer perguntas reais
  5. Ver o que o MCR responde sozinho

Sem template. Sem ingerir 80 fatos. Sem AutoReferencia.identidade().
So P(b|a) nos 167K obs + GeradorCoerente se acao nao for chat.

O que o MCR diz quando pergunta "o que e MCR" sem ter ingerido
"eu sou o MCR — motor cognitivo universal baseado em markov"?
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling
from mcr.chat import MCRChat
from mcr.coldstart import Coldstart


def main():
    print('=' * 60)
    print('TESTE REAL — MCR sem hardcode (sem 80 fatos, sem template)')
    print('=' * 60)

    # 1. Carregar motor do disco
    c = MCRCoupling()
    caminho = os.path.join('cache', 'coupling_MCRCoupling_backup_preB2c.json')
    if not os.path.exists(caminho):
        print(f'ERRO: {caminho} nao existe')
        return
    if not c.load(caminho):
        print('ERRO: falha ao carregar motor')
        return

    print(f'\nMotor carregado:')
    print(f'  Total observacoes: {c._total}')
    print(f'  Vocabulario: {len(c._transicao_palavra)} palavras')
    print(f'  Acoes: {len(c._freq_acao)}')

    # 2. Criar MCRChat SEM inicializar_conhecimento()
    # BC fica vazio. Sem 80 fatos hardcoded. Sem template de identidade.
    chat = MCRChat(c)

    # 3. Forcar coldstart a pular direto pra CHAT
    chat._coldstart._estado = Coldstart.CHAT
    c.ativar_contexto()

    # Verificar que BC esta vazio (sem AutoConhecimento)
    bc = chat._get_base_conhecimento()
    n_fatos = len(bc._fatos) if bc else 0
    print(f'\nBaseConhecimento: {n_fatos} fatos (deve ser 0 sem hardcode)')
    if n_fatos > 0:
        print('  AVISO: BC nao esta vazio — AutoConhecimento foi ingerido em sessao anterior')
        print('  Limpando BC para teste real...')
        if bc:
            bc._fatos = []
            bc._index = {}
            n_fatos = 0
            print(f'  BC limpo: {len(bc._fatos)} fatos')

    # 4. Fazer perguntas reais
    perguntas = [
        "o que e mcr",
        "quem e voce",
        "o que voce e",
        "o que e cognicao",
        "o que e markov",
        "o que e entropia",
        "o que significa mcr",
        "voce esta vivo",
        "o que voce sabe",
        "quem sou eu",
        "o que e pensar",
        "o que e realidade",
    ]

    print('\n' + '=' * 60)
    print('PERGUNTAS AO MCR (sem hardcode, sem template, so P(b|a))')
    print('=' * 60)

    for pergunta in perguntas:
        print(f'\nvoce: {pergunta}')
        t0 = time.time()
        try:
            resp = chat.interagir(pergunta)
            dt = time.time() - t0
            print(f'MCR ({dt:.2f}s): {resp}')
        except Exception as e:
            print(f'ERRO: {e}')
            import traceback
            traceback.print_exc()

    # 5. Tambem testar diretamente o GeradorCoerente
    # Pode revelar o que o MCR "sabe" sem BC
    print('\n' + '=' * 60)
    print('GERADOR COERENTE direto (sem BC, sem fluxo de chat)')
    print('=' * 60)

    try:
        gen = chat._get_gerador()
        sementes = [
            "eu sou",
            "mcr e",
            "cognicao e",
            "markov e",
            "entropia e",
            "realidade e",
            "pensamento e",
            "eu penso",
        ]
        for semente in sementes:
            print(f'\nsemente: "{semente}"')
            t0 = time.time()
            try:
                texto = gen.gerar(semente, max_tokens=30)
                dt = time.time() - t0
                print(f'gerado ({dt:.2f}s): {texto}')
            except Exception as e:
                print(f'ERRO: {e}')
    except Exception as e:
        print(f'ERRO ao init gerador: {e}')

    print('\n' + '=' * 60)
    print('FIM — o que o MCR revelou sozinho, sem hardcode?')
    print('=' * 60)


if __name__ == '__main__':
    main()
