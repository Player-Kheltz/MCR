"""Modulo: Util - Funcoes compartilhadas entre comandos modulares."""
import os, json, urllib.request, sys, re

# Paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')

def fast(prompt, temp=0.1, tarefa="fast"):
    """Chamada rapida ao Ollama."""
    cfg = _get_modelo(tarefa)
    try:
        opts = {'temperature': temp, 'num_ctx': cfg["ctx"], 'num_predict': cfg.get("num_predict", 2048)}
        # Passa parametros extras do cfg para options (main_gpu, num_gpu, raw, etc)
        for extra_key in ['raw', 'main_gpu', 'num_gpu']:
            if extra_key in cfg:
                opts[extra_key] = cfg[extra_key]
        d = json.dumps({'model': cfg["modelo"], 'prompt': prompt, 'stream': False,
            'options': opts}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(r, timeout=30).read()).get('response', '')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")

def gerar(prompt, temp=0.7, tarefa="code"):
    """Chamada completa ao Ollama."""
    cfg = _get_modelo(tarefa)
    try:
        opts = {'temperature': temp, 'num_ctx': cfg["ctx"], 'num_predict': cfg.get("num_predict", 4096)}
        # Passa parametros extras do cfg para options (main_gpu, num_gpu, raw, etc)
        for extra_key in ['raw', 'main_gpu', 'num_gpu']:
            if extra_key in cfg:
                opts[extra_key] = cfg[extra_key]
        d = json.dumps({'model': cfg["modelo"], 'prompt': prompt, 'stream': False,
            'options': opts}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(r, timeout=120).read()).get('response', '')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")

def _get_modelo(tarefa):
    """Retorna config de modelo para a tarefa."""
    modelos = {
        "fast":       {"modelo": "qwen2.5-coder:7b",  "ctx": 4096, "num_predict": 2048},
        "code":       {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "leve":       {"modelo": "qwen2.5-coder:7b",  "ctx": 2048, "num_predict": 1024},
        "pesado":     {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "analisar":   {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "revisor":    {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "planejador": {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "conceito":   {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                       "main_gpu": 0, "num_gpu": 99},
        "texto":      {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 2048,
                       "main_gpu": 0, "num_gpu": 99},
        "review":     {"modelo": "qwen2.5-coder:14b", "ctx": 8192, "num_predict": 8192,
                       "main_gpu": 0, "num_gpu": 99},
    }
    return modelos.get(tarefa, modelos["fast"])

def extrair_codigo(resposta):
    """Extrai codigo de ``` ... ``` blocks."""
    m = re.search(r'```(?:python)?\s*\n(.+?)```', resposta, re.DOTALL)
    if m: return m.group(1).strip()
    return re.sub(r'```\w*\n?', '', resposta).strip()


def extrair_codigo_puro(resposta):
    """Extrai o primeiro bloco ```python ... ```, ignorando texto explicativo."""
    # Se nao tem ```, ja e codigo puro
    if '```' not in resposta:
        return resposta.strip()
    # Tenta bloco ```python
    m = re.search(r'```python\s*\n(.+?)```', resposta, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: qualquer bloco ```
    m = re.search(r'```\s*\n(.+?)```', resposta, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback extremo: remove linhas de explicacao (comecam com Clarao/Aqui/Primeiro)
    linhas = []
    for l in resposta.split('\n'):
        ls = l.strip()
        if not ls or ls.startswith('Claro') or ls.startswith('Aqui') \
           or ls.startswith('Primeiro') or ls.startswith('Primeira') \
           or '```' in ls:
            continue
        linhas.append(l)
    return '\n'.join(linhas).strip()


def extrair_nome_projeto(request):
    """Extrai nome do projeto do request (ex: 'jogo_plataforma', 'meu_projeto').

    Usa Decider.extrair_json() como metodo principal.
    Fallback para regex se Decider nao estiver disponivel ou falhar.
    """
    try:
        from modulos.decider import Decider
        from modulos.ia import IA
        decider = Decider(IA())
        exemplos = [
            ("Cria um jogo de plataforma em Python", {"nome": "jogo_plataforma"}),
            ("Cria um site em JavaScript", {"nome": "site"}),
        ]
        dados = decider.extrair_json(request, {'nome': ''},
                                     exemplos=exemplos,
                                     instrucao="Extraia o nome do projeto")
        if dados.get('nome'):
            return dados['nome']
    except Exception:
        pass
    # Fallback: regex
    m = re.search(r'jogo\s+(?:de\s+)?(\w+)', request.lower())
    if m:
        return f"jogo_{m.group(1)}"
    m = re.search(r'(?:projeto|app|site|sistema)\s+(\w+)', request.lower())
    if m:
        return m.group(1)
    # Fallback: pega a primeira palavra significativa
    palavras = re.findall(r'\b[a-z]{4,}\b', request.lower())
    stop = {'com', 'para', 'que', 'como', 'mais', 'mas', 'por', 'sao', 'esta',
            'pode', 'ser', 'tem', 'seu', 'sua', 'entre', 'sobre', 'quando',
            'onde', 'quem', 'qual', 'cada', 'todo', 'apos', 'isso', 'esse',
            'num', 'sem', 'sob', 'ate', 'vai', 'era', 'foi'}
    for p in palavras:
        if p not in stop:
            return p
    return "meu_projeto"

def webfetch(url, timeout=15):
    """Busca conteudo de uma URL. Retorna texto ou None."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=timeout)
        content = resp.read()
        # Tenta detectar encoding
        try:
            return content.decode('utf-8')
        except:
            try:
                return content.decode('latin-1')
            except:
                return content.decode('utf-8', errors='replace')
    except Exception as e:
        return f'[Erro] {e}'
