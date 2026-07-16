"""test_fase2_relacoes.py — Teste da FASE 2: Extrator de Relacoes Semantica.

Valida extrair_relacoes() que descobre sinônimos, antônimos, hiperônimos,
hipônimos, merônimos, holônimos e polissemia — tudo por entropia, zero rótulos.

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  2.1 Extrair relacoes da matriz existente
  2.2 Deteccao de antonimos: mesmo contexto + acoes opostas
  2.3 Lista universal de relacoes (todas por entropia, zero rotulos)

Pilar 2: cortes descobertos por _corte_dinamico(), sem threshold hardcoded.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling

PASS, FAIL = 0, 0


def T(nome, cond, detalhe=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {nome}')
    else:
        FAIL += 1
        print(f'  [FAIL] {nome} — {detalhe}')


def main():
    global PASS, FAIL
    print('=' * 72)
    print('  FASE 2 — TESTE DO EXTRATOR DE RELACOES SEMANTICAS')
    print('  Plano de Evolucao MCR v2.2')
    print('=' * 72)

    # === Base de treino com relacoes claras ===
    pares = [
        ("criar monstro dragao", "criar_monstro"),
        ("gerar monstro orc", "criar_monstro"),
        ("criar mago lich", "criar_npc"),
        ("gerar mago feiticeiro", "criar_npc"),
        ("criar ferreiro anao", "criar_npc"),
        ("gerar ferreiro blacksmith", "criar_npc"),
        ("curar mago aliado", "curar"),
        ("curar ferreiro ferido", "curar"),
        ("restaurar mago ferido", "curar"),
        ("atacar monstro dragao", "atacar"),
        ("lutar contra orc mago", "atacar"),
        ("analisar codigo fonte", "analisar"),
        ("examinar texto log", "analisar"),
        ("bom personagem forte", "descrever"),
        ("ruim personagem fraco", "descrever"),
        ("bom aliado corajoso", "descrever"),
        ("ruim inimigo covarde", "descrever"),
        ("monstro verde dragao", "criar_monstro"),
        ("monstro vermelho orc", "criar_monstro"),
        ("dragao voa alto", "mover"),
        ("dragao corre rapido", "mover"),
    ]

    c = MCRCoupling()
    for t, a in pares:
        for _ in range(3):
            c.alimentar(t, a)

    print('\n[1] Sinonimos — criar ≈ gerar, analisar ≈ examinar, atacar ≈ lutar')
    rel_criar = c.extrair_relacoes("criar")
    T('extrair_relacoes("criar") nao vazio', bool(rel_criar), f'keys={list(rel_criar.keys())}')

    if 'sinonimos' in rel_criar:
        sin_criar = [p for p, _ in rel_criar['sinonimos']]
        print(f'    sinonimos de "criar": {sin_criar}')
        T('"gerar" e sinonimo de "criar"', "gerar" in sin_criar,
          f'sinonimos={sin_criar}')
    else:
        T('"gerar" e sinonimo de "criar"', False, 'sem sinonimos encontrados')

    rel_analisar = c.extrair_relacoes("analisar")
    if 'sinonimos' in rel_analisar:
        sin_anal = [p for p, _ in rel_analisar['sinonimos']]
        print(f'    sinonimos de "analisar": {sin_anal}')
        T('"examinar" e sinonimo de "analisar"', "examinar" in sin_anal,
          f'sinonimos={sin_anal}')
    else:
        T('"examinar" e sinonimo de "analisar"', False, 'sem sinonimos')

    rel_atacar = c.extrair_relacoes("atacar")
    if 'sinonimos' in rel_atacar:
        sin_atk = [p for p, _ in rel_atacar['sinonimos']]
        print(f'    sinonimos de "atacar": {sin_atk}')
        T('"lutar" e sinonimo de "atacar"', "lutar" in sin_atk,
          f'sinonimos={sin_atk}')
    else:
        T('"lutar" e sinonimo de "atacar"', False, 'sem sinonimos')

    print('\n[2] Antonimos — bom ≠ ruim (mesmo contexto, acoes opostas)')
    rel_bom = c.extrair_relacoes("bom")
    if 'antonimos' in rel_bom:
        ant_bom = [p for p, _ in rel_bom['antonimos']]
        print(f'    antonimos de "bom": {ant_bom}')
        T('"ruim" e antonimo de "bom"', "ruim" in ant_bom,
          f'antonimos={ant_bom}')
    else:
        T('"ruim" e antonimo de "bom"', False,
          f'keys={list(rel_bom.keys())} — pode nao ter dados suficientes')

    print('\n[3] Hiperonimos — monstro -> dragao/orc (transicao frequente)')
    rel_monstro = c.extrair_relacoes("monstro")
    if 'hiperonimos' in rel_monstro:
        hiper = [p for p, _ in rel_monstro['hiperonimos']]
        print(f'    hiperonimos de "monstro": {hiper}')
        T('encontrou hiperonimos de "monstro"', len(hiper) > 0)
    else:
        T('encontrou hiperonimos de "monstro"', False,
          f'keys={list(rel_monstro.keys())}')

    print('\n[4] Hiponimos — dragao -> monstro (transicao inversa)')
    rel_dragao = c.extrair_relacoes("dragao")
    if 'hiponimos' in rel_dragao:
        hipo = [p for p, _ in rel_dragao['hiponimos']]
        print(f'    hiponimos de "dragao": {hipo}')
        T('encontrou hiponimos de "dragao"', len(hipo) > 0)
    else:
        T('encontrou hiponimos de "dragao"', False,
          f'keys={list(rel_dragao.keys())}')

    print('\n[5] Meronimos/Holonimos — tamanho relativo')
    if 'meronimos' in rel_monstro:
        mero = [p for p, _ in rel_monstro['meronimos']]
        print(f'    meronimos de "monstro": {mero}')
        T('meronimos sao menores que "monstro"',
          all(len(p) < len("monstro") for p in mero) if mero else True)
    else:
        T('meronimos de "monstro" encontrados', False, 'sem meronimos')

    if 'holonimos' in rel_dragao:
        holo = [p for p, _ in rel_dragao['holonimos']]
        print(f'    holonimos de "dragao": {holo}')
        T('holonimos sao maiores que "dragao"',
          all(len(p) > len("dragao") for p in holo) if holo else True)
    else:
        T('holonimos de "dragao" encontrados', False, 'sem holonimos')

    print('\n[6] Polissemia — palavra com H alta em _palavra_acao')
    # "mago" aparece com criar_npc e curar — polissêmica
    rel_mago = c.extrair_relacoes("mago")
    if 'polissemia' in rel_mago:
        print(f'    polissemia detectada: {rel_mago["polissemia"]}')
        T('"mago" detectada como polissemica', True)
    else:
        T('"mago" detectada como polissemica', False,
          f'keys={list(rel_mago.keys())} — pode nao ter H suficiente')

    print('\n[7] Pilar 2 — sem threshold hardcoded')
    # Verifica que _corte_dinamico nao usa constantes magicas
    corte = c._corte_dinamico([1.0, 0.9, 0.8, 0.1, 0.05, 0.01])
    print(f'    corte_dinamico([1.0, 0.9, 0.8, 0.1, 0.05, 0.01]) = {corte}')
    T('corte dinamico separa estrutura (3) de ruido (3)', corte == 3,
      f'corte={corte} (esperado 3)')

    corte_uniforme = c._corte_dinamico([0.5, 0.5, 0.5, 0.5, 0.5])
    print(f'    corte_dinamico([0.5, 0.5, 0.5, 0.5, 0.5]) = {corte_uniforme}')
    T('corte dinamico retorna 0 para distribuicao uniforme', corte_uniforme == 0,
      f'corte={corte_uniforme} (esperado 0)')

    print('\n[8] Nao regressao — similaridade e compor ainda funcionam')
    sim = c.similaridade("criar", "gerar")
    T('similaridade ainda funciona', 0.0 <= sim <= 1.0, f'valor={sim:.4f}')

    sig_frase = c._assinatura_frase("monstro verde")
    T('assinatura_frase ainda funciona', len(sig_frase) > 0)

    print('\n[9] Curar ≈ restaurar (sinonimo adicional)')
    rel_curar = c.extrair_relacoes("curar")
    if 'sinonimos' in rel_curar:
        sin_curar = [p for p, _ in rel_curar['sinonimos']]
        print(f'    sinonimos de "curar": {sin_curar}')
        T('"restaurar" e sinonimo de "curar"', "restaurar" in sin_curar,
          f'sinonimos={sin_curar}')
    else:
        T('"restaurar" e sinonimo de "curar"', False, 'sem sinonimos')

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
