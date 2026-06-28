"""Benchmark de LATENCIA para FAST (classificacao).
Compara: qwen2.5-coder:1.5b vs qwen2.5-coder:7b
"""
import json, urllib.request, time

OLLAMA = 'http://localhost:11434/api/generate'

def chamar(modelo, prompt, temp=0.1, max_tokens=128, timeout=30):
    t0 = time.time()
    try:
        d = json.dumps({
            'model': modelo,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temp,
                'num_ctx': 2048,
                'num_predict': max_tokens,
            }
        }).encode()
        req = urllib.request.Request(OLLAMA, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 3)
        return texto, tempo
    except Exception as e:
        return f'[ERRO] {e}', round(time.time() - t0, 3)

# Cenarios de classificacao que o FAST faz
cenarios = [
    # 1. Classificacao de termos (CR)
    {
        'nome': 'CR: Extrair termos',
        'prompt': 'Quais os termos MAIS IMPORTANTES para buscar contexto? Retorne APENAS os termos separados por espaco: Solicitação: Me conte uma historia sobre .lua que tem a ver com o Brasil.'
    },
    # 2. Validacao de contexto (CR)
    {
        'nome': 'CR: Validar contexto',
        'prompt': 'O contexto abaixo e RELEVANTE para responder a solicitacao? Responda APENAS: SIM ou NAO. Solicitacao: O que e SPA? Contexto: SPA significa Sistema de Progressao do Aventureiro no projeto MCR.'
    },
    # 3. Classificacao de intencao (Supervisor)
    {
        'nome': 'Supervisor: Classificar',
        'prompt': 'Classifique a pergunta em UMA palavra: codigo, factual, lore, opiniao, procedimental. Pergunta: Crie uma lore para a cidade Eridanus.'
    },
    # 4. Classificacao de arquivos
    {
        'nome': 'Router: Roteamento',
        'prompt': 'Qual template usar para esta pergunta? Opcoes: perguntar, analisar_codigo, analisar_bug, conceito, lore. Pergunta: Analise este codigo e encontre bugs.'
    },
    # 5. Geracao rapida de instrucao (CR gerar_instrucao)
    {
        'nome': 'CR: Gerar instrucao',
        'prompt': 'A solicitacao abaixo pode ter termos AMBIGUOS. Gere UMA FRASE CURTA de instrucao para desambiguar. Ex: ".lua refere-se a linguagem de programacao Lua." Solicitacao: O que e SPA no MCR?'
    },
]

modelos = ['qwen2.5-coder:1.5b', 'qwen2.5-coder:7b']

print('BENCHMARK FAST: 1.5b vs 7b')
print('=' * 70)

for modelo in modelos:
    print(f'\n## {modelo}')
    total = 0
    for c in cenarios:
        texto, tempo = chamar(modelo, c['prompt'])
        print(f'  {c["nome"]:30s} {tempo:>6.1f}s  resp: {texto[:60]}')
        total += tempo
    media = total / len(cenarios)
    print(f'  {"MEDIA":30s} {media:>6.1f}s')

print('\n' + '=' * 70)
print('CONCLUSÃO:')
print(' - Se 1.5b < 2s para classificacao: manter 1.5b para FAST')
print(' - Se 1.5b > 3s: considerar upgrade para 7b')
print(' - Se 7b < 1s tambem: usar 7b para FAST')
