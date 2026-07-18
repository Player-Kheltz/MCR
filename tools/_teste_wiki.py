import urllib.request, urllib.parse, json

# API de texto completo (extracts sem exintro)
params = urllib.parse.urlencode({
    'action': 'query',
    'titles': 'Dog',
    'prop': 'extracts',
    'explaintext': '1',
    'format': 'json',
    'redirects': '1',
})
url = f'https://en.wikipedia.org/w/api.php?{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (test)'})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        dados = json.loads(resp.read().decode('utf-8'))
        paginas = dados.get('query', {}).get('pages', {})
        for pid, pagina in paginas.items():
            extract = pagina.get('extract', '')
            print(f"Titulo: {pagina.get('title')}")
            print(f"Tamanho: {len(extract)} chars")
            print(f"Primeiros 400: {extract[:400]}")
            print(f"...")
            print(f"Ultimos 200: {extract[-200:]}")
except Exception as e:
    print(f"Erro: {e}")
