import urllib.request, json

try:
    r = urllib.request.urlopen('http://localhost:11434/api/tags')
    d = json.loads(r.read())
    models = d.get('models', [])
    if models:
        print('Modelos disponiveis:')
        for m in models:
            print(f'  {m["name"]}')
    else:
        print('Nenhum modelo baixado')
except Exception as e:
    print(f'Erro: {e}')
