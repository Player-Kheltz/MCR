#!/usr/bin/env python3
"""
TESTE FINAL — MCRUnificado (FASE 8).

Executa todos os testes das fases 1-8 e reporta metricas.
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

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
    t0 = time.time()
    print('=' * 60)
    print('  TESTE FINAL — MCRUnificado (FASE 8)')
    print('=' * 60)

    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()

    # ─── 1. Status ────────────────────────────────
    print('\n[1] Status dos modulos')
    s = mcr.status()
    for nome in ['emergir', 'npc', 'codigo', 'raciocinio']:
        testar(f'{nome} carregado', s.get(nome) != 'FALHA' and s.get(nome) is not None)

    # ─── 2. Saudacao ──────────────────────────────
    print('\n[2] Saudacao')
    r = mcr.processar('Ola!')
    testar('Classificada como saudacao', r['intencao'] == 'saudacao',
           r['intencao'])
    testar('Resposta nao vazia', len(r['resposta']) > 2)

    # ─── 3. Conversa ──────────────────────────────
    print('\n[3] Conversa')
    r = mcr.processar('Me fale sobre espadas magicas')
    testar('Classificada como conversa ou criacao',
           r['intencao'] in ('conversa', 'criar_ideia'),
           r['intencao'])
    testar('Resposta nao vazia', len(r['resposta']) > 10)

    # ─── 4. Criar NPC ─────────────────────────────
    print('\n[4] Criar NPC')
    r = mcr.processar('Crie um NPC ferreiro')
    testar('Classificada como criar_npc', r['intencao'] == 'criar_npc',
           r['intencao'])
    testar('Gerou codigo', '```lua' in r['resposta'] or 'NPC' in r['resposta'])

    # ─── 5. Criar codigo ──────────────────────────
    print('\n[5] Criar codigo')
    r = mcr.processar('Crie um script lua')
    testar('Classificada como criar_codigo', r['intencao'] == 'criar_codigo',
           r['intencao'])

    # ─── 6. Raciocinio ────────────────────────────
    print('\n[6] Raciocinio')
    r = mcr.processar('Quanto e 15 + 27?')
    testar('Classificada como raciocinio', r['intencao'] == 'raciocinio',
           r['intencao'])

    # ─── 7. Criatividade ──────────────────────────
    print('\n[7] Criatividade (Emergir)')
    r = mcr.processar('Crie uma ideia nova')
    testar('Classificada como criar_ideia', r['intencao'] == 'criar_ideia',
           r['intencao'])

    # ─── 8. Analise ───────────────────────────────
    print('\n[8] Analise de texto')
    r = mcr.processar('Analise: O MCR e um sistema Markoviano')
    testar('Classificada como analise', r['intencao'] == 'analise',
           r['intencao'])

    # ─── 9. Multi-turno ───────────────────────────
    print('\n[9] Conversa multi-turno')
    respostas = []
    for msg in ['Ola!', 'O que voce vende?', 'Qual o melhor item?',
                'Quanto custa?', 'Obrigado, ate mais!']:
        r = mcr.processar(msg)
        respostas.append(r['resposta'])
    testar('5 turnos processados', len(respostas) == 5)
    testar('Respostas variadas', len(set(r[:30] for r in respostas)) >= 3,
           f'{len(set(respostas))} unicas')

    # ─── 10. Latencia ─────────────────────────────
    print('\n[10] Latencia')
    tempos = []
    for msg in ['Ola!', 'Crie um NPC', 'Quanto e 3 + 5?',
                'Analise: teste', 'Crie uma ideia']:
        r = mcr.processar(msg)
        tempos.append(r['tempo'])

    media = sum(tempos) / len(tempos)
    maximo = max(tempos)
    testar('Latencia media < 0.01s', media < 0.01, f'{media*1000:.2f}ms')
    testar('Latencia maxima < 0.05s', maximo < 0.05, f'{maximo*1000:.2f}ms')

    # ─── 11. Todas as intencoes ────────────────────
    print('\n[11] Cobertura de intencoes')
    intencoes = {'saudacao', 'conversa', 'criar_npc', 'criar_codigo',
                 'criar_ideia', 'raciocinio', 'analise'}
    testadas = set()
    for msg, esperada in [
        ('Ola!', 'saudacao'),
        ('Como vai?', 'conversa'),
        ('Crie um NPC guarda', 'criar_npc'),
        ('Crie um script', 'criar_codigo'),
        ('Crie uma ideia', 'criar_ideia'),
        ('Quanto e 5+3?', 'raciocinio'),
        ('Analise este texto', 'analise'),
    ]:
        r = mcr.processar(msg)
        testadas.add(r['intencao'])
    cobertura = len(testadas) / len(intencoes)
    testar(f'Cobertura de intencoes > 80%', cobertura > 0.8,
           f'{len(testadas)}/{len(intencoes)} = {cobertura:.0%}')

    mcr.close()
    tempo_total = time.time() - t0

    print('\n' + '=' * 60)
    total = PASS + FAIL + ERROR
    print(f'  RESULTADO FINAL: {PASS}/{total} pass, {FAIL} fail, {ERROR} error')
    print(f'  Tempo total: {tempo_total:.1f}s')
    print(f'  Interacoes: {mcr.interacoes}')
    print('=' * 60)

    return FAIL == 0 and ERROR == 0

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
