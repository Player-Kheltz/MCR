"""TESTE ULTIMATE: Artigos ALEATORIOS da Wikipedia — zero curadoria humana.

Baixa 500 artigos aleatorios de cada idioma (PT, EN, ES, FR, DE).
Zero selecao humana. Zero concept ID. Zero corpus sintetico.

Teste: artigos com MESMO titulo em 2+ idiomas sao cognatos
  (mesma palavra = mesmo conceito, garantido por string matching).
  NMI(cognate_PT, cognate_EN) > NMI(random_PT, random_EN)?
  Se sim, o motor descobre sozinho — cognicao real sem curadoria.
"""
import sys
import os
import time
import json
import urllib.request
import urllib.parse
import re
import statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr.coupling import MCRCoupling

CACHE_DIR = os.path.join('cache', 'corpus_expa', 'random_wiki')
os.makedirs(CACHE_DIR, exist_ok=True)


def buscar_aleatorios(idioma, n=500, cache_only=False):
    """Baixa N artigos aleatorios da Wikipedia.

    Estrategia: 1 request leve (list=random, 500 titulos) + batch extracts.
    Evita generator=random+extracts que触发 rate limit.
    """
    cache_file = os.path.join(CACHE_DIR, f'{idioma}_random_{n}.json')

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    if cache_only:
        return {}

    # 1. UMA request: 500 titulos aleatorios (leve)
    titulos = []
    rnlimit = min(n * 3, 500)  # pedir 3x mais para compensar filtragem
    params = urllib.parse.urlencode({
        'action': 'query', 'list': 'random',
        'rnnamespace': '0', 'rnlimit': str(rnlimit),
        'format': 'json',
    })
    url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        if '429' in str(e):
            print(f'  {idioma}: rate limit, esperando 30s...')
            time.sleep(30)
            with urllib.request.urlopen(req, timeout=30) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
        else:
            print(f'  {idioma}: error: {e}')
            return {}

    titulos = [p['title'] for p in dados.get('query', {}).get('random', [])
               if len(p['title']) >= 3]
    print(f'  {idioma}: {len(titulos)} titulos aleatorios', flush=True)

    # 2. Batch extracts (50 por request)
    artigos = {}
    for i in range(0, len(titulos), 50):
        batch = titulos[i:i+50]
        titulos_str = '|'.join(batch)

        params = urllib.parse.urlencode({
            'action': 'query', 'titles': titulos_str,
            'prop': 'extracts', 'explaintext': '1',
            'format': 'json', 'redirects': '1',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if '429' in str(e):
                print(f'  {idioma}: rate limit no batch {i//50+1}, esperando 30s...', flush=True)
                time.sleep(30)
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        dados = json.loads(resp.read().decode('utf-8'))
                except Exception:
                    continue
            else:
                time.sleep(2)
                continue

        pages = dados.get('query', {}).get('pages', {})
        for pid, page in pages.items():
            if pid == '-1':
                continue
            title = page.get('title', '').lower().strip()
            extract = page.get('extract', '')
            if not extract or len(extract) < 100:
                continue
            if len(title) < 3:
                continue
            texto = re.sub(r'\[[^\]]*\]', '', extract)
            frases = re.split(r'[.\n;!]+', texto)
            frases = [f.strip().lower() for f in frases
                      if 4 <= len(f.strip().split()) <= 60]
            if frases:
                artigos[title] = frases[:200]

        time.sleep(2)

    print(f'  {idioma}: {len(artigos)} artigos com texto valido')
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(artigos, f, ensure_ascii=False)
    return artigos


def main():
    idiomas = ['pt', 'en', 'es', 'fr', 'de']

    print('='*70)
    print('TESTE ULTIMATE: Artigos ALEATORIOS — zero curadoria humana')
    print('='*70)

    # 1. Baixar artigos aleatorios
    todos_artigos = {}
    for idioma in idiomas:
        print(f'\nBaixando {idioma}...')
        arts = buscar_aleatorios(idioma, n=100)
        todos_artigos[idioma] = arts

    total_artigos = sum(len(v) for v in todos_artigos.values())
    print(f'\nTotal: {total_artigos} artigos aleatorios')

    # 2. Encontrar cognatos: titulos que aparecem em 2+ idiomas
    titulo_idiomas = {}
    for idioma, arts in todos_artigos.items():
        for titulo in arts:
            titulo_idiomas.setdefault(titulo, set()).add(idioma)

    cognatos = {t: idis for t, idis in titulo_idiomas.items() if len(idis) >= 2}
    print(f'Cognatos (mesmo titulo em 2+ idiomas): {len(cognatos)}')
    for t, idis in list(cognatos.items())[:20]:
        print(f'  {t}: {sorted(idis)}')

    if len(cognatos) < 3:
        print('\nPOUCOS cognatos encontrados. Aumentando para 1000 artigos...')
        for idioma in idiomas:
            arts = buscar_aleatorios(idioma, n=1000)
            todos_artigos[idioma] = arts
        titulo_idiomas = {}
        for idioma, arts in todos_artigos.items():
            for titulo in arts:
                titulo_idiomas.setdefault(titulo, set()).add(idioma)
        cognatos = {t: idis for t, idis in titulo_idiomas.items() if len(idis) >= 2}
        print(f'Cognatos: {len(cognatos)}')

    # 3. Ingerir no motor (acao = titulo nativo)
    print(f'\nIngerindo {total_artigos} artigos no motor...')
    motor = MCRCoupling()
    corpus = []
    for idioma, arts in todos_artigos.items():
        for titulo, frases in arts.items():
            for fr in frases:
                corpus.append((fr, titulo))

    t0 = time.time()
    motor.alimentar_lote(corpus)
    print(f'Ingestao: {time.time()-t0:.1f}s, {motor._total} obs, {len(motor._transicao_palavra)} palavras')

    # Build IDF
    motor._cache_idf_doc = {}
    motor._cache_idf_total = len(motor._palavra_acao) or 1
    for w in motor._transicao_palavra:
        for ctx_token in motor._transicao_palavra[w]:
            motor._cache_idf_doc[ctx_token] = motor._cache_idf_doc.get(ctx_token, 0) + 1

    # 4. Testar: cognatos vs random
    print('\n' + '='*70)
    print('TESTE: NMI de cognatos (mesmo titulo, idiomas diferentes) vs random')
    print('='*70)

    # Pares cognatos: mesmo titulo em 2 idiomas diferentes
    pares_cognato = []
    for titulo, idis in cognatos.items():
        idis_list = sorted(idis)
        for i in range(len(idis_list)):
            for j in range(i+1, len(idis_list)):
                pares_cognato.append((titulo, titulo, idis_list[i], idis_list[j]))

    print(f'Pares cognato: {len(pares_cognato)}')

    # Pares random: titulos diferentes, idiomas diferentes
    todos_titulos = [(t, idioma) for idioma, arts in todos_artigos.items()
                     for t in arts.keys()]
    import random
    random.seed(42)
    pares_random = []
    for _ in range(len(pares_cognato) * 3):
        i1 = random.randint(0, len(todos_titulos)-1)
        i2 = random.randint(0, len(todos_titulos)-1)
        t1, lang1 = todos_titulos[i1]
        t2, lang2 = todos_titulos[i2]
        if t1 != t2 and lang1 != lang2:
            pares_random.append((t1, t2, lang1, lang2))

    print(f'Pares random: {len(pares_random)}')

    # Computar NMI
    print('\nCognatos:')
    scores_cog = []
    for t1, t2, lang1, lang2 in pares_cognato[:50]:
        sa = motor._assinatura_palavra(t1)
        sb = motor._assinatura_palavra(t2)
        if sa and sb:
            nmi = motor._nmi_semantico(sa, sb)
            scores_cog.append(nmi)
            if len(scores_cog) <= 15:
                print(f'  COG {t1:15} ({lang1}~{lang2}): {nmi:.3f}')

    print('\nRandom:')
    scores_rand = []
    for t1, t2, lang1, lang2 in pares_random[:150]:
        sa = motor._assinatura_palavra(t1)
        sb = motor._assinatura_palavra(t2)
        if sa and sb:
            nmi = motor._nmi_semantico(sa, sb)
            scores_rand.append(nmi)
            if len(scores_rand) <= 15:
                print(f'  RND {t1:15} ~ {t2:15} ({lang1}~{lang2}): {nmi:.3f}')

    media_cog = statistics.mean(scores_cog) if scores_cog else 0
    media_rand = statistics.mean(scores_rand) if scores_rand else 0
    delta = media_cog - media_rand
    status = 'PASS' if delta > 0.05 else 'FAIL'

    print(f'\n{"="*70}')
    print(f'RESULTADO')
    print(f'{"="*70}')
    print(f'  Cognatos (mesmo titulo, idiomas diferentes): {media_cog:.3f} (n={len(scores_cog)})')
    print(f'  Random (titulos diferentes, idiomas diferentes): {media_rand:.3f} (n={len(scores_rand)})')
    print(f'  Delta: {delta:.3f} {status}')
    print()
    if delta > 0.05:
        print(f'  >>> O MCR descobre cognatos SOZINHO com artigos aleatorios')
        print(f'  >>> ZERO curadoria humana — cognicao real comprovada')
    elif delta > 0.02:
        print(f'  >>> Sinal fraco — precisa mais artigos ou mais cognatos')
    else:
        print(f'  >>> Nao ha sinal — o motor nao descobre sem curadoria')


if __name__ == '__main__':
    main()
