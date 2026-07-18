"""tools/_conferir_real.py — Conferir se a descoberta e REAL ou trivial.

Problema: os top-10 NMI sao cognatos ortograficos identicos
(zone~zone, volume~volume, zebra~zebra). Isso NAO e descoberta —
e so reconhecer a mesma string.

Teste honesto:
  1. Filtrar pares onde p1 == p2 (cognato identico)
  2. Filtrar pares onde edit_distance(p1, p2) <= 2 (quase identico)
  3. Recalcular delta SEM esses pares triviais
  4. Se delta cai para ~0 = descoberta era ilusoria
  5. Se delta se mantem = descoberta REAL
"""
import os
import sys
import json
import time
import random
import statistics
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'validacao')


def edit_distance(s1, s2):
    """Distancia de Levenshtein simples."""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = prev[j + 1] + 1
            dele = curr[j] + 1
            sub = prev[j] + (c1 != c2)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def carregar_dados():
    obs_file = os.path.join(CACHE_DIR, 'corpus_validacao.json')
    test_file = os.path.join(CACHE_DIR, 'pares_teste.json')
    with open(obs_file, 'r', encoding='utf-8') as f:
        observacoes = json.load(f)
    with open(test_file, 'r', encoding='utf-8') as f:
        pares = json.load(f)
    rel = [p for p in pares if p[4]]
    nao_rel = [p for p in pares if not p[4]]
    return observacoes, rel, nao_rel


def main():
    from mcr.coupling import MCRCoupling

    observacoes, rel_todos, nao_rel_todos = carregar_dados()

    # Amostrar grupos completos
    random.seed(42)
    grupos_obs = defaultdict(list)
    for texto, acao in observacoes:
        grupos_obs[acao].append((texto, acao))
    todas_acoes = list(grupos_obs.keys())
    random.shuffle(todas_acoes)
    n_obs = 500000
    obs_sample = []
    for acao in todas_acoes:
        if len(obs_sample) >= n_obs:
            break
        obs_sample.extend(grupos_obs[acao])

    print(f'Ingerindo {len(obs_sample)} obs ({len(set(a for _,a in obs_sample))} grupos)...')
    mcr = MCRCoupling()
    t0 = time.time()
    mcr.alimentar_lote(obs_sample)
    print(f'  {time.time()-t0:.0f}s, vocab={len(mcr._transicao_palavra)}')

    # Filtrar pares com ctx suficiente
    def ctx_count(palavra):
        return len(mcr._transicao_palavra.get(palavra, {}))

    min_ctx = 5
    random.seed(123)
    random.shuffle(rel_todos)
    random.shuffle(nao_rel_todos)

    def filtrar(pares_lista, n):
        filtrados = []
        for p in pares_lista:
            if len(filtrados) >= n:
                break
            p1, lang1, p2, lang2, rel = p
            if ' ' in p1 or ' ' in p2:
                continue
            if ctx_count(p1) >= min_ctx and ctx_count(p2) >= min_ctx:
                filtrados.append(p)
        return filtrados

    rel = filtrar(rel_todos, 2000)
    nao_rel = filtrar(nao_rel_todos, 2000)

    # Calcular NMI para todos
    def nmi_par(p1, p2):
        try:
            sig_a = mcr._assinatura_palavra(p1)
            sig_b = mcr._assinatura_palavra(p2)
            if not sig_a or not sig_b:
                return 0.0
            return mcr._nmi_semantico(sig_a, sig_b)
        except Exception:
            return 0.0

    print(f'\nCalculando NMI para {len(rel)+len(nao_rel)} pares...')
    t0 = time.time()
    resultados_rel = []
    for i, (p1, lang1, p2, lang2, _) in enumerate(rel):
        nmi = nmi_par(p1, p2)
        ed = edit_distance(p1, p2)
        identico = (p1 == p2)
        quase = (ed <= 2 and not identico)
        resultados_rel.append((nmi, p1, lang1, p2, lang2, ed, identico, quase))
        if (i+1) % 500 == 0:
            print(f'  rel {i+1}/{len(rel)}...', end='\r', flush=True)

    resultados_nao = []
    for i, (p1, lang1, p2, lang2, _) in enumerate(nao_rel):
        nmi = nmi_par(p1, p2)
        ed = edit_distance(p1, p2)
        identico = (p1 == p2)
        quase = (ed <= 2 and not identico)
        resultados_nao.append((nmi, p1, lang1, p2, lang2, ed, identico, quase))
        if (i+1) % 500 == 0:
            print(f'  nao-rel {i+1}/{len(nao_rel)}...', end='\r', flush=True)
    print(f'\n  {time.time()-t0:.1f}s')

    # === ANALISE HONESTA ===
    print('\n' + '=' * 70)
    print('ANALISE HONESTA — descoberta real ou trivial?')
    print('=' * 70)

    # Categoria 1: TODOS os pares
    nmis_rel_all = [r[0] for r in resultados_rel]
    nmis_nao_all = [r[0] for r in resultados_nao]
    delta_all = statistics.mean(nmis_rel_all) - statistics.mean(nmis_nao_all)

    # Categoria 2: SEM cognatos identicos (p1 != p2)
    nmis_rel_noident = [r[0] for r in resultados_rel if not r[6]]
    nmis_nao_noident = [r[0] for r in resultados_nao if not r[6]]
    delta_noident = (statistics.mean(nmis_rel_noident) - statistics.mean(nmis_nao_noident)) if nmis_rel_noident and nmis_nao_noident else 0

    # Categoria 3: SEM cognatos quase-identicos (edit_distance > 2)
    nmis_rel_real = [r[0] for r in resultados_rel if not r[6] and not r[7]]
    nmis_nao_real = [r[0] for r in resultados_nao if not r[6] and not r[7]]
    delta_real = (statistics.mean(nmis_rel_real) - statistics.mean(nmis_nao_real)) if nmis_rel_real and nmis_nao_real else 0

    # Categoria 4: SO cognatos identicos
    nmis_rel_ident = [r[0] for r in resultados_rel if r[6]]
    nmis_nao_ident = [r[0] for r in resultados_nao if r[6]]
    delta_ident = (statistics.mean(nmis_rel_ident) - statistics.mean(nmis_nao_ident)) if nmis_rel_ident and nmis_nao_ident else 0

    print(f'\n1. TODOS os pares:')
    print(f'   rel: n={len(nmis_rel_all)}, media={statistics.mean(nmis_rel_all):.4f}')
    print(f'   nao: n={len(nmis_nao_all)}, media={statistics.mean(nmis_nao_all):.4f}')
    print(f'   delta={delta_all:.4f}  {"PASS" if delta_all > 0.05 else "FAIL"}')

    print(f'\n2. SEM cognatos identicos (p1 != p2):')
    print(f'   rel: n={len(nmis_rel_noident)}, media={statistics.mean(nmis_rel_noident):.4f}')
    print(f'   nao: n={len(nmis_nao_noident)}, media={statistics.mean(nmis_nao_noident):.4f}')
    print(f'   delta={delta_noident:.4f}  {"PASS" if delta_noident > 0.05 else "FAIL"}')

    print(f'\n3. SEM cognatos quase-identicos (edit_distance > 2):')
    print(f'   rel: n={len(nmis_rel_real)}, media={statistics.mean(nmis_rel_real):.4f}')
    print(f'   nao: n={len(nmis_nao_real)}, media={statistics.mean(nmis_nao_real):.4f}')
    print(f'   delta={delta_real:.4f}  {"PASS" if delta_real > 0.05 else "FAIL"}')

    print(f'\n4. SO cognatos identicos (p1 == p2):')
    if nmis_rel_ident:
        print(f'   rel: n={len(nmis_rel_ident)}, media={statistics.mean(nmis_rel_ident):.4f}')
    else:
        print(f'   rel: n=0')
    if nmis_nao_ident:
        print(f'   nao: n={len(nmis_nao_ident)}, media={statistics.mean(nmis_nao_ident):.4f}')
    else:
        print(f'   nao: n=0 (controle nunca tem p1==p2)')

    # Distribuicao de categorias nos relacionados
    n_ident = sum(1 for r in resultados_rel if r[6])
    n_quase = sum(1 for r in resultados_rel if r[7] and not r[6])
    n_real = sum(1 for r in resultados_rel if not r[6] and not r[7])
    print(f'\nDistribuicao dos relacionados:')
    print(f'  identicos (p1==p2): {n_ident} ({n_ident/len(resultados_rel)*100:.1f}%)')
    print(f'  quase (edit<=2):    {n_quase} ({n_quase/len(resultados_rel)*100:.1f}%)')
    print(f'  reais (edit>2):     {n_real} ({n_real/len(resultados_rel)*100:.1f}%)')

    # Top descobertas REAIS (edit_distance > 2)
    print(f'\nTop 15 descobertas REAIS (edit_distance > 2, nao cognatos triviais):')
    rel_real_ordenado = sorted([r for r in resultados_rel if not r[6] and not r[7]],
                               reverse=True)
    for nmi, p1, lang1, p2, lang2, ed, _, _ in rel_real_ordenado[:15]:
        print(f'  {nmi:.4f}  {lang1}:{p1} ~ {lang2}:{p2}  (ed={ed})')

    # Top falsos positivos REAIS
    print(f'\nTop 10 falsos positivos REAIS (edit_distance > 2):')
    nao_real_ordenado = sorted([r for r in resultados_nao if not r[6] and not r[7]],
                               reverse=True)
    for nmi, p1, lang1, p2, lang2, ed, _, _ in nao_real_ordenado[:10]:
        print(f'  {nmi:.4f}  {lang1}:{p1} ~ {lang2}:{p2}  (ed={ed})')

    # Veredicto
    print('\n' + '=' * 70)
    print('VEREDICTO HONESTO:')
    print('=' * 70)
    if delta_real > 0.05:
        print(f'delta_real = {delta_real:.4f} PASS')
        print('O MCR descobre sinonimia跨-idioma REAL (nao-trivial).')
    elif delta_real > 0.02:
        print(f'delta_real = {delta_real:.4f} WEAK')
        print('O MCR tem algum sinal mas fraco.')
    else:
        print(f'delta_real = {delta_real:.4f} FAIL')
        print('O MCR NAO descobre sinonimia跨-idioma nao-trivial.')
        print('A descoberta anterior era dominada por cognatos ortograficos.')
    print('=' * 70)

    # Salvar
    resultado = {
        'n_obs': len(obs_sample),
        'delta_all': delta_all,
        'delta_noident': delta_noident,
        'delta_real': delta_real,
        'delta_ident': delta_ident,
        'n_ident_rel': n_ident,
        'n_quase_rel': n_quase,
        'n_real_rel': n_real,
        'veredicto': 'PASS' if delta_real > 0.05 else 'FAIL' if delta_real < 0.02 else 'WEAK',
    }
    with open(os.path.join(CACHE_DIR, 'resultado_real.json'), 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f'\nSalvo: resultado_real.json')


if __name__ == '__main__':
    main()
