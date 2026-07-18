import urllib.request, urllib.parse, json, time

# Testar search para "agua" em PT
for idioma, titulo in [('pt', 'agua'), ('en', 'water'), ('es', 'agua')]:
    # 1. Tentar titulo direto
    params = urllib.parse.urlencode({
        'action': 'query',
        'titles': titulo,
        'prop': 'extracts',
        'explaintext': '1',
        'format': 'json',
        'redirects': '1',
    })
    url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            paginas = dados.get('query', {}).get('pages', {})
            for pid, pagina in paginas.items():
                extract = pagina.get('extract', '')
                print(f'{idioma}/{titulo} direto: pid={pid} len={len(extract)} title={pagina.get("title","")}')
    except Exception as e:
        print(f'{idioma}/{titulo} direto ERRO: {e}')

    # 2. Tentar search
    time.sleep(0.5)
    params = urllib.parse.urlencode({
        'action': 'query',
        'list': 'search',
        'srsearch': titulo,
        'srlimit': '3',
        'format': 'json',
    })
    url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            print(f'  search: {len(resultados)} resultados')
            for r in resultados[:3]:
                print(f'    {r.get("title")} (snippet: {r.get("snippet","")[:50]})')
    except Exception as e:
        print(f'  search ERRO: {e}')
    print()
