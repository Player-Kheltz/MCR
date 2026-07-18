"""tools/wikipedia_corpus.py — Buscar artigos da Wikipedia multi-idioma.

Busca artigos da Wikipedia em PT, EN e ES para os 70 conceitos do corpus
multi-idioma. Extrai frases e retorna como observacoes para o MCR.

MCR puro: o corpus e DADOS (texto da Wikipedia ingerido), nao codigo do motor.
Usa apenas urllib (standard library) — zero dependencias externas.

Uso:
    from tools.wikipedia_corpus import buscar_corpus_wikipedia
    corpus = buscar_corpus_wikipedia(max_conceitos=70, max_frases_por_artigo=500)
    for texto, acao in corpus:
        coupling.alimentar(texto, acao)
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
import os
import sys

# Garantir que o diretorio raiz esta no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.corpus_multilingue import CONCEITOS


def _buscar_extract(titulo: str, idioma: str, timeout: int = 15,
                    max_retries: int = 3) -> str:
    """Busca o texto de um artigo da Wikipedia via API REST.

    Se o titulo direto falhar, tenta buscar via API de search.
    Inclui retry com backoff exponencial para HTTP 429 (rate limit).

    Returns: texto do artigo em texto plano, ou string vazia se falhar.
    """
    def _fetch(tit, retry=0):
        params = urllib.parse.urlencode({
            'action': 'query',
            'titles': tit,
            'prop': 'extracts',
            'explaintext': '1',
            'format': 'json',
            'redirects': '1',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
                paginas = dados.get('query', {}).get('pages', {})
                for pid, pagina in paginas.items():
                    if pid == '-1':
                        return ''
                    return pagina.get('extract', '')
        except urllib.error.HTTPError as e:
            if e.code == 429 and retry < max_retries:
                wait = 5 * (retry + 1)  # 5s, 10s, 15s
                time.sleep(wait)
                return _fetch(tit, retry + 1)
            return ''
        except Exception:
            return ''
        return ''

    # Tentar titulo direto
    result = _fetch(titulo)
    if result:
        return result

    time.sleep(2)  # respeitar rate limit

    # Se falhar, buscar via search
    try:
        params = urllib.parse.urlencode({
            'action': 'query',
            'list': 'search',
            'srsearch': titulo,
            'srlimit': '1',
            'format': 'json',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            if resultados:
                titulo_real = resultados[0].get('title', '')
                if titulo_real:
                    time.sleep(2)
                    return _fetch(titulo_real)
    except Exception:
        pass

    return ''


def _extrair_frases(texto: str, min_pal: int = 5, max_pal: int = 50) -> list:
    """Extrai frases do texto (split por pontuacao).

    Filtra frases com 5-50 palavras para evitar fragments curtos e paragrafos.
    Remove referencias [1], [2], etc.
    """
    # Remover referencias [1], [see 2], etc.
    texto = re.sub(r'\[[^\]]*\]', '', texto)
    # Split por pontuacao de fim de frase
    frases = re.split(r'[.\n;!]+', texto)
    resultado = []
    for f in frases:
        f = f.strip()
        if not f:
            continue
        palavras = f.split()
        if min_pal <= len(palavras) <= max_pal:
            resultado.append(f.lower())
    return resultado


def buscar_corpus_wikipedia(max_conceitos: int = 70,
                            max_frases_por_artigo: int = 500,
                            cache_dir: str = None,
                            cache_only: bool = False) -> list:
    """Busca artigos da Wikipedia em PT/EN/ES para os conceitos do corpus.

    Args:
        cache_only: se True, so usa artigos ja em cache (sem fetch HTTP).
                    Artigos faltantes sao pulados silenciosamente.
    Returns: List[Tuple[str, str]] — (frase, acao) para coupling.alimentar()
    """
    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'wiki')

    os.makedirs(cache_dir, exist_ok=True)

    corpus = []
    n_conceitos = 0

    for dominio, conceitos in CONCEITOS.items():
        for cid, dados in conceitos.items():
            if n_conceitos >= max_conceitos:
                break

            for idioma in ['pt', 'en', 'es']:
                titulo = dados[idioma]
                cache_file = os.path.join(cache_dir, f'{idioma}_{titulo}.txt')

                # Tentar carregar do cache
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        frases = [line.strip() for line in f if line.strip()]
                elif cache_only:
                    # Modo cache_only: pular artigos nao cacheados
                    continue
                else:
                    # Buscar da Wikipedia
                    extract = _buscar_extract(titulo, idioma)
                    if not extract:
                        continue
                    frases = _extrair_frases(extract)
                    if not frases:
                        continue
                    # Salvar no cache
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        for fr in frases:
                            f.write(fr + '\n')
                    time.sleep(2)  # respeitar rate limit da Wikipedia

                # Limitar frases por artigo
                if len(frases) > max_frases_por_artigo:
                    frases = frases[:max_frases_por_artigo]

                for fr in frases:
                    corpus.append((fr, cid))

            n_conceitos += 1
            print(f'  {n_conceitos}/{max_conceitos}: {cid} '
                  f'({dados["pt"]}/{dados["en"]}/{dados["es"]})')

        if n_conceitos >= max_conceitos:
            break

    return corpus


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print('Buscando artigos da Wikipedia (PT/EN/ES)...')
    corpus = buscar_corpus_wikipedia(max_conceitos=5, max_frases_por_artigo=100)
    print(f'\nCorpus: {len(corpus)} frases')
    for texto, acao in corpus[:5]:
        print(f'  [{acao}] {texto[:80]}...')
