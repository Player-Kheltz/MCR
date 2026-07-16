#!/usr/bin/env python3
"""
test_fase3_npc_criativo.py — Testes da FASE 3: NPC Criativo.

Testa:
  1. NPC carrega MCRSQLite treinado
  2. Classificacao de intencoes (saudacao, criacao, pergunta, conversa)
  3. Respostas nao sao sempre o mesmo fallback
  4. Criacao usa EmergirUnificado
  5. Contexto multi-turno (mencionar algo e NPC lembrar)
  6. Latencia < 0.1s por resposta
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mcr.npc_criativo import NPCCriativo

PASS, FAIL, ERROR = 0, 0, 0

def testar(nome, condicao, detalhe=''):
    global PASS, FAIL, ERROR
    if condicao is True:
        PASS += 1; print(f'  [PASS] {nome}')
    elif condicao is False:
        FAIL += 1; print(f'  [FAIL] {nome}' + (f' - {detalhe}' if detalhe else ''))
    else:
        ERROR += 1; print(f'  [ERROR] {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERROR
    print('=' * 60)
    print('  TESTE FASE 3 — NPC Criativo')
    print('=' * 60)

    npc = NPCCriativo('Ferronius', 'ferreiro')

    # ─── 1. Backend ────────────────────────────────
    print('\n[1] Backend treinado')
    r = npc.resumo()
    testar('MCRSQLite carregado', r['estados_treinados'] > 0,
           f'{r["estados_treinados"]} estados')
    testar('EmergirUnificado carregado', r['emergir_modulos']['emergir'],
           f'{sum(1 for v in r["emergir_modulos"].values() if v)}/6 modulos')

    # ─── 2. Classificacao de intencoes ─────────────
    print('\n[2] Classificacao de intencoes')
    testar('Ola -> saudacao', npc._classificar_intencao('ola') == 'saudacao')
    testar('Crie uma espada -> criacao', npc._classificar_intencao('crie uma espada') == 'criacao')
    testar('Quanto custa? -> pergunta', npc._classificar_intencao('quanto custa?') == 'pergunta')
    testar('Voce e ferreiro? -> pergunta', npc._classificar_intencao('voce e ferreiro?') == 'pergunta')
    testar('Quero comprar -> acao', npc._classificar_intencao('quero comprar uma espada') == 'acao')

    # ─── 3. Respostas variadas ─────────────────────
    print('\n[3] Variedade de respostas')
    respostas = set()
    for msg in ['Ola!', 'Como vai?', 'O que voce faz?', 'Me fale sobre espadas',
                'Qual a sua historia?', 'Obrigado!']:
        resp = npc.responder(msg)
        respostas.add(resp[:50])
    testar('>3 respostas unicas', len(respostas) > 3,
           f'{len(respostas)} unicas em 6 perguntas')

    # ─── 4. Criacao ────────────────────────────────
    print('\n[4] Criacao de conteudo')
    resp_criacao = npc.responder('Crie uma historia sobre dragoes')
    testar('Resposta de criacao nao vazia', len(resp_criacao) > 20,
           f'{len(resp_criacao)} caracteres')
    testar('Resposta de criacao menciona conceito',
           any(c in resp_criacao.lower() for c in ['dragao', 'dragon', 'historia', 'story']),
           resp_criacao[:80])

    # ─── 5. Multi-turno ────────────────────────────
    print('\n[5] Contexto multi-turno')
    npc2 = NPCCriativo('Biblios', 'bibliotecario')
    npc2.responder('Eu tenho uma espada antiga')
    r1 = npc2.responder('Voce sabe algo sobre ela?')
    testar('Contexto mantido entre turnos', npc2.turno == 2,
           f'{npc2.turno} turnos')
    testar('Contexto contem palavras anteriores',
           len(npc2.contexto_atual) > 0,
           f'contexto: {npc2.contexto_atual[:5]}')

    # ─── 6. Latencia ───────────────────────────────
    print('\n[6] Latencia')
    tempos = []
    for msg in ['Ola!', 'Como vai?', 'O que voce vende?', 'Ate mais!']:
        t0 = time.time()
        npc.responder(msg)
        tempos.append(time.time() - t0)
    media = sum(tempos) / len(tempos)
    testar('Latencia media < 0.1s', media < 0.1,
           f'{media*1000:.1f}ms media')

    npc.close()
    npc2.close()

    print('\n' + '=' * 60)
    total = PASS + FAIL + ERROR
    print(f'  Resultado: {PASS}/{total} pass, {FAIL} fail, {ERROR} error')
    print('=' * 60)
    return FAIL == 0 and ERROR == 0

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
