"""tools/_validar_descoberta.py — Teste HONESTO da descoberta跨-idioma do MCR.

Pergunta: o MCR descobre sinonimia跨-idioma SOZINHO via Tatoeba?

Metodo:
  1. Criar MCR novo (VAZIO) — sem Wikipedia, sem Rosetta, sem corpus sintetico
  2. Ingerir apenas observacoes Tatoeba (sentencas paralelas alinhadas)
  3. Para cada par do WordNet (ground truth):
     - Relacionado (mesmo synset): casa~house (TRUE)
     - Nao-relacionado (synsets diferentes): casa~mesa (FALSE)
  4. Calcular NMI entre as duas palavras
  5. Delta = media(relacionados) - media(nao-relacionados)
  6. delta > 0 = MCR descobre sinonimia SOZINHO via co-ocorrencia

Isolamento total: ZERO curadoria humana, ZERO corpus sintetico, ZERO Wikipedia.
So Tatoeba (sentencas reais de falantes humanos) como DADOS.

Uso:
    python tools/_validar_descoberta.py [--n_obs 100000] [--n_pares 5000]
"""
import os
import sys
import json
import time
import random
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'validacao')


def carregar_dados():
    """Carrega corpus + pares de teste do cache."""
    obs_file = os.path.join(CACHE_DIR, 'corpus_validacao.json')
    test_file = os.path.join(CACHE_DIR, 'pares_teste.json')

    if not os.path.exists(obs_file) or not os.path.exists(test_file):
        print('ERRO: Execute tools/_baixar_validacao.py primeiro')
        sys.exit(1)

    print('Carregando corpus Tatoeba...')
    t0 = time.time()
    with open(obs_file, 'r', encoding='utf-8') as f:
        observacoes = json.load(f)
    print(f'  {len(observacoes)} observacoes em {time.time()-t0:.1f}s')

    print('Carregando pares WordNet...')
    with open(test_file, 'r', encoding='utf-8') as f:
        pares = json.load(f)
    rel = [p for p in pares if p[4]]
    nao_rel = [p for p in pares if not p[4]]
    print(f'  {len(rel)} relacionados, {len(nao_rel)} nao-relacionados')

    return observacoes, rel, nao_rel


def validar(n_obs, n_pares, n_min_ctx=5):
    """Executa teste honesto.

    Args:
        n_obs: numero de observacoes Tatoeba a ingerir (0 = todas)
        n_pares: numero de pares a testar por categoria
        n_min_ctx: minimo de ctx tokens para uma palavra ser testada
    """
    from mcr.coupling import MCRCoupling

    observacoes, rel_todos, nao_rel_todos = carregar_dados()

    # Amostrar GRUPOS completos (nao observacoes aleatorias)
    # Garante que pares alinhados (sentenca PT + traducao EN) sejam ingeridos juntos
    if n_obs > 0 and n_obs < len(observacoes):
        random.seed(42)
        # Agrupar observacoes por acao (grupo de traducao)
        grupos_obs = defaultdict(list)
        for texto, acao in observacoes:
            grupos_obs[acao].append((texto, acao))
        # Amostrar grupos ate atingir n_obs
        todas_acoes = list(grupos_obs.keys())
        random.shuffle(todas_acoes)
        obs_sample = []
        for acao in todas_acoes:
            if len(obs_sample) >= n_obs:
                break
            obs_sample.extend(grupos_obs[acao])
        observacoes = obs_sample
        print(f'\nUsando {len(observacoes)} observacoes ({len(set(a for _,a in observacoes))} grupos completos)')
    else:
        print(f'\nUsando {len(observacoes)} observacoes (TODAS)')

    # Criar MCR NOVO (vazio) — isolamento total
    print('\nCriando MCR novo (VAZIO)...')
    mcr = MCRCoupling()

    # Ingerir Tatoeba
    print(f'Ingerindo {len(observacoes)} observacoes...')
    t0 = time.time()
    mcr.alimentar_lote(observacoes)
    t1 = time.time()
    print(f'  Ingestao: {t1-t0:.1f}s ({len(observacoes)/(t1-t0):.0f} obs/s)')
    print(f'  Vocabulario: {len(mcr._transicao_palavra)} palavras')

    # Filtrar pares: palavras devem ter contexto suficiente
    print(f'\nFiltrando pares (min ctx tokens: {n_min_ctx})...')

    def ctx_count(palavra):
        """Conta contextos da palavra no MCR."""
        if palavra not in mcr._transicao_palavra:
            return 0
        return len(mcr._transicao_palavra[palavra])

    def filtrar_pares(pares_lista, n):
        random.seed(123)
        random.shuffle(pares_lista)
        filtrados = []
        for p in pares_lista:
            if len(filtrados) >= n:
                break
            p1, lang1, p2, lang2, rel = p
            # Tokenizar palavra (pode ser multi-palavra)
            # Para MCR, palavra unica e mais direto
            if ' ' in p1 or ' ' in p2:
                continue
            if ctx_count(p1) >= n_min_ctx and ctx_count(p2) >= n_min_ctx:
                filtrados.append(p)
        return filtrados

    rel = filtrar_pares(rel_todos, n_pares)
    nao_rel = filtrar_pares(nao_rel_todos, n_pares)
    print(f'  Relacionados filtrados: {len(rel)}')
    print(f'  Nao-relacionados filtrados: {len(nao_rel)}')

    if len(rel) < 10 or len(nao_rel) < 10:
        print('POUCOS pares com contexto suficiente. Aumente n_obs.')
        return

    # Calcular NMI para cada par
    print(f'\nCalculando NMI para {len(rel)+len(nao_rel)} pares...')

    def nmi_par(p1, p2):
        """Calcula NMI semantico entre duas palavras via assinaturas."""
        try:
            sig_a = mcr._assinatura_palavra(p1)
            sig_b = mcr._assinatura_palavra(p2)
            if not sig_a or not sig_b:
                return 0.0
            return mcr._nmi_semantico(sig_a, sig_b)
        except Exception:
            return 0.0

    t0 = time.time()
    nmis_rel = []
    for i, (p1, lang1, p2, lang2, _) in enumerate(rel):
        nmi = nmi_par(p1, p2)
        nmis_rel.append(nmi)
        if (i + 1) % 100 == 0:
            print(f'  rel {i+1}/{len(rel)}...', end='\r', flush=True)

    nmis_nao = []
    for i, (p1, lang1, p2, lang2, _) in enumerate(nao_rel):
        nmi = nmi_par(p1, p2)
        nmis_nao.append(nmi)
        if (i + 1) % 100 == 0:
            print(f'  nao-rel {i+1}/{len(nao_rel)}...', end='\r', flush=True)

    t1 = time.time()
    print(f'\n  Calculo NMI: {t1-t0:.1f}s ({(len(rel)+len(nao_rel))/(t1-t0):.0f} pares/s)')

    # Estatisticas
    import statistics
    media_rel = statistics.mean(nmis_rel)
    media_nao = statistics.mean(nmis_nao)
    mediana_rel = statistics.median(nmis_rel)
    mediana_nao = statistics.median(nmis_nao)
    delta = media_rel - media_nao
    delta_med = mediana_rel - mediana_nao

    # Taxa de acerto (binarizar NMI > 0)
    acertos_rel = sum(1 for x in nmis_rel if x > 0) / len(nmis_rel)
    acertos_nao = sum(1 for x in nmis_nao if x > 0) / len(nmis_nao)

    print('\n' + '=' * 60)
    print('RESULTADO — TESTE HONESTO (Tatoeba sozinho)')
    print('=' * 60)
    print(f'Observacoes Tatoeba: {len(observacoes)}')
    print(f'Vocabulario MCR: {len(mcr._transicao_palavra)} palavras')
    print(f'Pares testados: {len(rel)} rel + {len(nao_rel)} nao-rel')
    print(f'')
    print(f'Relacionados (WordNet ground truth):')
    print(f'  NMI media:   {media_rel:.4f}')
    print(f'  NMI mediana: {mediana_rel:.4f}')
    print(f'  NMI > 0:     {acertos_rel*100:.1f}%')
    print(f'')
    print(f'Nao-relacionados (controle):')
    print(f'  NMI media:   {media_nao:.4f}')
    print(f'  NMI mediana: {mediana_nao:.4f}')
    print(f'  NMI > 0:     {acertos_nao*100:.1f}%')
    print(f'')
    print(f'DELTA (media):   {delta:.4f}  {"PASS" if delta > 0.05 else "FAIL" if delta < 0.02 else "WEAK"}')
    print(f'DELTA (mediana): {delta_med:.4f}')
    print(f'Falsos positivos (nao-rel com NMI>0): {acertos_nao*100:.1f}%')
    print('=' * 60)

    # Mostrar exemplos
    print('\nTop 10 RELACIONADOS com maior NMI (descobertas do MCR):')
    rel_ordenado = sorted(zip(nmis_rel, rel), reverse=True)
    for nmi, (p1, lang1, p2, lang2, _) in rel_ordenado[:10]:
        print(f'  {nmi:.4f}  {lang1}:{p1} ~ {lang2}:{p2}')

    print('\nTop 10 NAO-RELACIONADOS com maior NMI (falsos positivos?):')
    nao_ordenado = sorted(zip(nmis_nao, nao_rel), reverse=True)
    for nmi, (p1, lang1, p2, lang2, _) in nao_ordenado[:10]:
        print(f'  {nmi:.4f}  {lang1}:{p1} ~ {lang2}:{p2}')

    print('\nRELACIONADOS com NMI = 0 (ignorados honestamente):')
    zeros = [(n, p) for n, p in zip(nmis_rel, rel) if n == 0]
    for nmi, (p1, lang1, p2, lang2, _) in zeros[:10]:
        print(f'  {nmi:.4f}  {lang1}:{p1} ~ {lang2}:{p2}')
    if zeros:
        print(f'  ... ({len(zeros)} total = {len(zeros)/len(rel)*100:.1f}%)')

    # Salvar resultado
    resultado = {
        'n_obs': len(observacoes),
        'vocab': len(mcr._transicao_palavra),
        'n_rel': len(rel),
        'n_nao': len(nao_rel),
        'media_rel': media_rel,
        'media_nao': media_nao,
        'delta': delta,
        'delta_mediana': delta_med,
        'acertos_rel_pct': acertos_rel * 100,
        'acertos_nao_pct': acertos_nao * 100,
        'veredicto': 'PASS' if delta > 0.05 else 'FAIL' if delta < 0.02 else 'WEAK',
    }
    result_file = os.path.join(CACHE_DIR, f'resultado_honesto_{len(observacoes)}.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f'\nResultado salvo: {result_file}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_obs', type=int, default=100000,
                        help='Numero de observacoes Tatoeba (0 = todas)')
    parser.add_argument('--n_pares', type=int, default=2000,
                        help='Numero de pares por categoria')
    parser.add_argument('--min_ctx', type=int, default=5,
                        help='Minimo de ctx tokens por palavra')
    args = parser.parse_args()

    print('=' * 60)
    print('TESTE HONESTO — MCR descobre sinonimia跨-idioma via Tatoeba?')
    print('(MCR novo vazio + so Tatoeba, zero curadoria)')
    print('=' * 60)

    validar(args.n_obs, args.n_pares, args.min_ctx)


if __name__ == '__main__':
    main()
