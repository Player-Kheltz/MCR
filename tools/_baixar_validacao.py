"""tools/_baixar_validacao.py — Baixa Tatoeba + Open Multilingual WordNet em lote.

Valida a descoberta fundamental do MCR: descobre sinonimia跨-idioma sozinho
via co-ocorrencia de tokens raros (cognatos, termos cientificos)?

Fontes (baixaveis em lote, sem rate limit de API):
  1. Tatoeba (sentences.tar.bz2 + links.tar.bz2) — ~30MB
     - Sentencas paralelas alinhadas em 400+ idiomas
     - Cada par alinhado = mesmo significado em 2 idiomas
     - URL: https://downloads.tatoeba.org/exports/sentences.tar.bz2
  2. Open Multilingual WordNet (omw-1.4.zip) — 26MB
     - Sinonimia跨-idioma ANOTADA (ground truth)
     - PT/ES/FR/CAT/GLG/EUS + mais
     - URL: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/omw-1.4.zip
  3. Princeton WordNet (wordnet.zip) — 10MB
     - Ingles (synset source — OMW alinha com PWN offsets)
     - URL: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip

Estrategia MCR:
  - Tatoeba: ingerir sentencas com acao="trad:{id_grupo}" (mesmo significado)
  - WordNet: ground truth (casa=house anotado = TRUE)
  - Testar: MCR descobre casa~house sozinho via Tatoeba? WordNet confirma?

Uso:
    python tools/_baixar_validacao.py
"""
import urllib.request
import urllib.parse
import os
import sys
import tarfile
import bz2
import io
import csv
import time
import json
import zipfile
import random
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'validacao')
os.makedirs(CACHE_DIR, exist_ok=True)

# Tatoeba: ISO 639-3 codes
TATOEBA_ALVO = {'por', 'eng', 'spa', 'fra', 'deu'}
TATOEBA_LABEL = {'por': 'pt', 'eng': 'en', 'spa': 'es', 'fra': 'fr', 'deu': 'de'}

# OMW 1.4: diretorios por idioma (ISO 639-3)
OMW_ALVO = {
    'por': 'pt',
    'spa': 'es',
    'fra': 'fr',
    'cat': 'ca',  # catalao
    'glg': 'gl',  # galego
    'eus': 'eu',  # basco
    'ita': 'it',
}

TATOEBA_SENTENCES_URL = 'https://downloads.tatoeba.org/exports/sentences.tar.bz2'
TATOEBA_LINKS_URL = 'https://downloads.tatoeba.org/exports/links.tar.bz2'
OMW_URL = 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/omw-1.4.zip'
WORDNET_URL = 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip'


def baixar_arquivo(url, destino, descricao):
    """Baixa um arquivo com progresso."""
    if os.path.exists(destino):
        tamanho = os.path.getsize(destino)
        print(f'  [cache] {descricao}: {tamanho//1024}KB')
        return destino

    print(f'  Baixando {descricao}...')
    print(f'    URL: {url}')

    req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            total_mb = total / (1024 * 1024) if total else 0
            print(f'    Tamanho: {total_mb:.1f}MB')

            baixado = 0
            chunks = []
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
                baixado += len(chunk)
                if total > 0:
                    pct = baixado * 100 / total
                    print(f'\r    {pct:.0f}% ({baixado//(1024*1024)}MB)', end='', flush=True)

            print()

            with open(destino, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)

        print(f'  OK: {destino}')
        return destino

    except Exception as e:
        print(f'  ERRO: {e}')
        return None


def baixar_tatoeba():
    """Baixa sentences.tar.bz2 + links.tar.bz2 da Tatoeba."""
    print('\n=== TATOEBA ===')

    sent_file = os.path.join(CACHE_DIR, 'sentences.tar.bz2')
    link_file = os.path.join(CACHE_DIR, 'links.tar.bz2')

    baixar_arquivo(TATOEBA_SENTENCES_URL, sent_file, 'sentences.tar.bz2')
    baixar_arquivo(TATOEBA_LINKS_URL, link_file, 'links.tar.bz2')

    return sent_file, link_file


def baixar_omw_wordnet():
    """Baixa OMW 1.4 + Princeton WordNet."""
    print('\n=== OMW + PRINCETON WORDNET ===')

    omw_file = os.path.join(CACHE_DIR, 'omw-1.4.zip')
    wn_file = os.path.join(CACHE_DIR, 'wordnet.zip')

    baixar_arquivo(OMW_URL, omw_file, 'omw-1.4.zip')
    baixar_arquivo(WORDNET_URL, wn_file, 'wordnet.zip')

    return omw_file, wn_file


def extrair_tatoeba(sent_file, link_file):
    """Extrai sentencas e links da Tatoeba.

    Retorna:
      sentencas: dict {id: (idioma, texto)}
      pares: lista de (id_src, id_dst) — traducoes alinhadas
    """
    print('\n=== EXTRAINDO TATOEBA ===')

    cache_json = os.path.join(CACHE_DIR, 'tatoeba_extraido.json')
    if os.path.exists(cache_json):
        print('  [cache] tatoeba_extraido.json')
        with open(cache_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return dados['sentencas'], dados['pares']

    # 1. Extrair sentencas
    sentencas = {}
    print('  Extraindo sentencas...')
    if not os.path.exists(sent_file):
        print('  ERRO: sentences.tar.bz2 nao baixado')
        return {}, []
    with bz2.open(sent_file, 'rb') as f:
        text = f.read().decode('utf-8')
    for linha in text.strip().split('\n'):
        partes = linha.split('\t')
        if len(partes) >= 3:
            sid, idioma, texto = partes[0], partes[1], partes[2]
            if idioma in TATOEBA_ALVO and len(texto) > 10:
                sentencas[sid] = (idioma, texto)

    print(f'  {len(sentencas)} sentencas (PT/EN/ES/FR/DE)')

    # 2. Extrair links (pares de traducao)
    pares = []
    print('  Extraindo links...')
    if not os.path.exists(link_file):
        print('  ERRO: links.tar.bz2 nao baixado')
        return sentencas, []
    with bz2.open(link_file, 'rb') as f:
        text = f.read().decode('utf-8')
    for linha in text.strip().split('\n'):
        partes = linha.split('\t')
        if len(partes) >= 2:
            id_src, id_dst = partes[0], partes[1]
            if id_src in sentencas and id_dst in sentencas:
                lang_src = sentencas[id_src][0]
                lang_dst = sentencas[id_dst][0]
                if lang_src != lang_dst:
                    pares.append((id_src, id_dst))

    print(f'  {len(pares)} pares跨-idioma alinhados')

    with open(cache_json, 'w', encoding='utf-8') as f:
        json.dump({'sentencas': sentencas, 'pares': pares}, f, ensure_ascii=False)

    return sentencas, pares


def extrair_omw_wordnet(omw_file, wn_file):
    """Extrai sinonimia跨-idioma do OMW + Princeton WordNet.

    Retorna:
      synsets: dict {synset_id: [(idioma, palavra), ...]}
    """
    print('\n=== EXTRAINDO OMW + WORDNET ===')

    cache_json = os.path.join(CACHE_DIR, 'omw_wn_extraido.json')
    if os.path.exists(cache_json):
        print('  [cache] omw_wn_extraido.json')
        with open(cache_json, 'r', encoding='utf-8') as f:
            return json.load(f)

    synsets = defaultdict(list)

    # 1. Princeton WordNet (ingles) — formato data.{noun,verb,adj,adv}
    print('  Extraindo Princeton WordNet (EN)...')
    if os.path.exists(wn_file):
        z = zipfile.ZipFile(wn_file)
        ss_type_map = {'noun': 'n', 'verb': 'v', 'adj': 'a', 'adv': 'r'}
        count = 0
        for fname, ss_type in ss_type_map.items():
            path = f'wordnet/data.{fname}'
            if path not in z.namelist():
                continue
            content = z.read(path).decode('latin-1')
            # Pular cabecalho de licenca (primeiras 29 linhas)
            linhas = content.strip().split('\n')
            for linha in linhas:
                if not linha or not linha[0].isdigit():
                    continue
                partes = linha.split()
                if len(partes) < 5:
                    continue
                # Validar ss_type (n/v/a/r) — filtra linhas de copyright
                ss_t = partes[2]
                if ss_t not in ('n', 'v', 'a', 'r'):
                    continue
                offset = partes[0]
                w_cnt = int(partes[3], 16)
                if w_cnt < 1 or w_cnt > 100:
                    continue
                # Palavras: posicoes 4 ate 4+2*w_cnt (word lex_id pares)
                for i in range(w_cnt):
                    idx = 4 + i * 2
                    if idx < len(partes):
                        palavra = partes[idx].lower().replace('_', ' ')
                        synset_id = f'{offset}-{ss_t}'
                        synsets[synset_id].append(('en', palavra))
                        count += 1
        print(f'    EN: {count} lemmas')

    # 2. OMW 1.4 — formato .tab
    print('  Extraindo OMW 1.4 (PT/ES/FR/...)...')
    if os.path.exists(omw_file):
        z = zipfile.ZipFile(omw_file)
        for nome in z.namelist():
            if not nome.endswith('.tab'):
                continue
            # Identificar idioma pelo nome do arquivo
            # Formato: omw-1.4/{lang}/wn-data-{lang}.tab
            partes_nome = nome.split('/')
            if len(partes_nome) < 3:
                continue
            lang_dir = partes_nome[1]
            if lang_dir not in OMW_ALVO:
                continue
            lang_label = OMW_ALVO[lang_dir]

            # Tentar UTF-8 primeiro, depois latin-1
            content = z.read(nome)
            text = None
            for enc in ['utf-8', 'latin-1']:
                try:
                    text = content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            if text is None:
                continue

            count = 0
            for linha in text.strip().split('\n'):
                if linha.startswith('#'):
                    continue
                partes = linha.split('\t')
                if len(partes) < 3:
                    continue
                synset_id = partes[0]
                tipo = partes[1]
                palavra = partes[2]
                # Tipo pode ser "lemma" ou "lang:lemma" (ex: fra:lemma)
                if 'lemma' in tipo and len(palavra) > 1:
                    palavra = palavra.lower().replace('_', ' ')
                    synsets[synset_id].append((lang_label, palavra))
                    count += 1
            print(f'    {lang_label} ({lang_dir}): {count} lemmas')

    # Filtrar synsets com 2+ idiomas
    synsets_cross = {}
    for sid, pares in synsets.items():
        langs = set(l for l, _ in pares)
        if len(langs) >= 2:
            synsets_cross[sid] = pares

    print(f'  {len(synsets_cross)} synsets com 2+ idiomas (ground truth跨-idioma)')

    with open(cache_json, 'w', encoding='utf-8') as f:
        json.dump(synsets_cross, f, ensure_ascii=False)

    return synsets_cross


def gerar_corpus_mcr(sentencas, pares, synsets):
    """Gera corpus para o MCR + pares de teste (ground truth).

    Retorna:
      observacoes: lista de (texto, acao) para alimentar()
      pares_teste: lista de (palavra_src, idioma_src, palavra_dst, idioma_dst, relacionado: bool)
    """
    print('\n=== GERANDO CORPUS MCR ===')

    cache_obs = os.path.join(CACHE_DIR, 'corpus_validacao.json')
    cache_test = os.path.join(CACHE_DIR, 'pares_teste.json')

    if os.path.exists(cache_obs) and os.path.exists(cache_test):
        print('  [cache] corpus_validacao.json + pares_teste.json')
        with open(cache_obs, 'r', encoding='utf-8') as f:
            obs = json.load(f)
        with open(cache_test, 'r', encoding='utf-8') as f:
            testes = json.load(f)
        return [(t, a) for t, a in obs], [(a, b, c, d, e) for a, b, c, d, e in testes]

    observacoes = []
    pares_teste = []

    # 1. Tatoeba: sentencas paralelas como observacoes
    print('  Gerando observacoes Tatoeba...')
    pares_por_id = defaultdict(set)
    for id_src, id_dst in pares:
        pares_por_id[id_src].add(id_dst)
        pares_por_id[id_dst].add(id_src)

    # Agrupar por componente conexa (traducoes em cadeia)
    visitados = set()
    grupo_id = 0
    grupos = {}
    for sid in sentencas:
        if sid in visitados:
            continue
        fila = [sid]
        componente = set()
        while fila:
            atual = fila.pop()
            if atual in visitados:
                continue
            visitados.add(atual)
            componente.add(atual)
            for viz in pares_por_id.get(atual, []):
                if viz not in visitados:
                    fila.append(viz)

        if len(componente) >= 2:
            for cid in componente:
                grupos[cid] = grupo_id
            grupo_id += 1

    print(f'  {grupo_id} grupos de traducao (componentes conexas)')

    count_obs = 0
    for sid, (idioma, texto) in sentencas.items():
        if sid in grupos:
            gid = grupos[sid]
            acao = f'trad:{gid}'
            observacoes.append((texto.lower(), acao))
            count_obs += 1

    print(f'  {count_obs} observacoes Tatoeba')

    # 2. WordNet: ground truth de sinonimia跨-idioma
    print('  Gerando pares de teste WordNet...')
    pares_rel = []
    synset_por_palavra = defaultdict(list)

    for sid, pares_lang in synsets.items():
        palavras_por_lang = defaultdict(list)
        for lang, palavra in pares_lang:
            palavras_por_lang[lang].append(palavra)
            synset_por_palavra[(palavra, lang)].append(sid)

        # Pares跨-idioma do mesmo synset (relacionados = TRUE)
        langs = list(palavras_por_lang.keys())
        for i in range(len(langs)):
            for j in range(i + 1, len(langs)):
                for p1 in palavras_por_lang[langs[i]]:
                    for p2 in palavras_por_lang[langs[j]]:
                        pares_rel.append((p1, langs[i], p2, langs[j], True))

    # Pares nao-relacionados: palavras de synsets diferentes
    print(f'  Gerando pares nao-relacionados...')
    random.seed(42)
    todas_palavras_lang = list(synset_por_palavra.keys())
    pares_nao_rel = []
    tentativas = 0
    max_tentativas = len(pares_rel) * 5

    while len(pares_nao_rel) < len(pares_rel) and tentativas < max_tentativas:
        tentativas += 1
        i = random.randint(0, len(todas_palavras_lang) - 1)
        j = random.randint(0, len(todas_palavras_lang) - 1)
        p1, lang1 = todas_palavras_lang[i]
        p2, lang2 = todas_palavras_lang[j]
        if lang1 == lang2 or p1 == p2:
            continue
        s1 = synset_por_palavra[(p1, lang1)]
        s2 = synset_por_palavra[(p2, lang2)]
        if set(s1).isdisjoint(set(s2)):
            pares_nao_rel.append((p1, lang1, p2, lang2, False))

    pares_teste = pares_rel + pares_nao_rel
    print(f'  {len(pares_rel)} pares relacionados (WordNet ground truth)')
    print(f'  {len(pares_nao_rel)} pares nao-relacionados (controle)')
    print(f'  {len(pares_teste)} pares de teste total')

    with open(cache_obs, 'w', encoding='utf-8') as f:
        json.dump(observacoes, f, ensure_ascii=False)
    with open(cache_test, 'w', encoding='utf-8') as f:
        json.dump(pares_teste, f, ensure_ascii=False)

    return observacoes, pares_teste


def main():
    print('=' * 70)
    print('BAIXAR DATASETS DE VALIDACAO (Tatoeba + WordNet)')
    print('Valida: MCR descobre sinonimia跨-idioma sozinho?')
    print('=' * 70)

    # 1. Baixar
    sent_file, link_file = baixar_tatoeba()
    omw_file, wn_file = baixar_omw_wordnet()

    # 2. Extrair
    sentencas, pares = extrair_tatoeba(sent_file, link_file)
    synsets = extrair_omw_wordnet(omw_file, wn_file)

    # 3. Gerar corpus MCR
    observacoes, pares_teste = gerar_corpus_mcr(sentencas, pares, synsets)

    # 4. Resumo
    print('\n=== RESUMO ===')
    print(f'Observacoes para MCR: {len(observacoes)}')
    print(f'Pares de teste: {len(pares_teste)}')

    print('\nExemplos de pares RELACIONADOS (WordNet ground truth):')
    rel = [p for p in pares_teste if p[4]]
    for p in rel[:15]:
        print(f'  {p[1]}:{p[0]} ~ {p[3]}:{p[2]}')

    print('\nExemplos de pares NAO-RELACIONADOS (controle):')
    nao_rel = [p for p in pares_teste if not p[4]]
    for p in nao_rel[:15]:
        print(f'  {p[1]}:{p[0]} ~ {p[3]}:{p[2]}')

    # Estatisticas por par de idiomas
    print('\nDistribuicao por par de idiomas (relacionados):')
    dist = defaultdict(int)
    for p in rel:
        par_lang = tuple(sorted([p[1], p[3]]))
        dist[par_lang] += 1
    for par, n in sorted(dist.items(), key=lambda x: -x[1])[:15]:
        print(f'  {par[0]}-{par[1]}: {n}')

    print(f'\nCache salvo em: {CACHE_DIR}')
    print('\nProximo passo: rodar tools/_validar_descoberta.py')


if __name__ == '__main__':
    main()
