"""Modulo: Util - Funcoes compartilhadas entre comandos modulares."""
import os, json, urllib.request, sys, re

# Threshold MCR
try:
    from modulos.MCR import MCRThreshold
    _TH_UTIL = MCRThreshold("util_sim")
    for v in [0.7, 0.75, 0.8, 0.72, 0.77]:
        _TH_UTIL.observar(v)
except ImportError:
    _TH_UTIL = None

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
    """Retorna config de modelo para a tarefa.
    
    Fonte unica: ia.py (MODELOS). Nao duplicar configs aqui.
    """
    from modulos.ia import MODELOS as _IA_MODELOS
    return _IA_MODELOS.get(tarefa, _IA_MODELOS["fast"])

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
        except Exception:
            try:
                return content.decode('latin-1')
            except Exception:
                return content.decode('utf-8', errors='replace')
    except Exception as e:
        return f'[Erro] {e}'

# ===== Safe I/O com fallback para ToolOrchestrator =====

def safe_ler_arquivo(caminho):
    """Le arquivo usando ToolOrchestrator se disponivel, fallback para open()."""
    try:
        from modulos.tool_orchestrator import ToolOrchestrator
        tools = ToolOrchestrator()
        r = tools.executar('ler_arquivo', {'caminho': caminho})
        if r.get('sucesso'):
            return r['resultado']
    except Exception:
        pass
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def safe_escrever_arquivo(caminho, conteudo):
    """Escreve arquivo usando ToolOrchestrator se disponivel, fallback para open()."""
    try:
        from modulos.tool_orchestrator import ToolOrchestrator
        tools = ToolOrchestrator()
        r = tools.executar('escrever_arquivo', {'caminho': caminho, 'conteudo': conteudo})
        if r.get('sucesso'):
            return True
    except Exception:
        pass
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    return True

def safe_ler_linhas(caminho):
    """Le linhas de um arquivo."""
    try:
        from modulos.tool_orchestrator import ToolOrchestrator
        tools = ToolOrchestrator()
        r = tools.executar('ler_arquivo', {'caminho': caminho})
        if r.get('sucesso'):
            return r['resultado'].splitlines(True)
    except Exception:
        pass
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines()

# ===== PatternEngine Gatekeeper Universal =====

def reparar_com_validacao(codigo_original, funcao_reparo, *args, similaridade_min=0.7):
    """Wrapper universal: repara codigo + valida com PatternEngine.
    
    1. Antes: calcula fingerprint + eixo Nirvana-Caos do codigo original
    2. Executa funcao_reparo(codigo_original, *args)
    3. Depois: calcula fingerprint + eixo do codigo gerado
    4. Gatekeeper: rejeita se similaridade < 0.7 OU eixo caiu OU encolheu
    
    Args:
        codigo_original: str, codigo antes do reparo
        funcao_reparo: callable(codigo, *args) -> str
        similaridade_min: float (0.7 = 70% similar)
    
    Returns:
        str: codigo_novo se aprovado, codigo_original se rejeitado
    """
    if not codigo_original or not callable(funcao_reparo):
        return codigo_original
    
    try:
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        
        # Antes
        tokens_orig = pe.tokenizar(codigo_original, 'codigo')
        fp_orig = pe.fingerprint(tokens_orig)
        eixo_orig = pe.eixo_nirvana_caos(tokens_orig)
        
        # Executa reparo
        codigo_novo = funcao_reparo(codigo_original, *args)
        if codigo_novo == codigo_original or not codigo_novo:
            return codigo_original  # nada mudou
        
        # Depois
        tokens_novo = pe.tokenizar(codigo_novo, 'codigo')
        fp_novo = pe.fingerprint(tokens_novo)
        eixo_novo = pe.eixo_nirvana_caos(tokens_novo)
        sim = pe.similaridade(fp_orig, fp_novo)
        
        # EDGE CASE: codigo muito curto (< 120 chars) — validacao EXTRA rigorosa
        if len(codigo_original) < 120:
            # 1. Contagem de linhas deve ser igual ou ±1
            if abs(codigo_original.count('\n') - codigo_novo.count('\n')) > 1:
                return codigo_original
            # 2. Fallback character-level (SequenceMatcher)
            from difflib import SequenceMatcher
            sim_char = SequenceMatcher(None, codigo_original, codigo_novo).ratio()
            if sim_char < (_TH_UTIL.calcular(1.0) if _TH_UTIL else 0.75):
                return codigo_original  # character-level rejeitou
            # 3. Similaridade mais rigorosa
            similaridade_min = max(similaridade_min, 0.90)
        
        # GATEKEEPER: 3 condicoes para REJEITAR
        if sim < similaridade_min:
            return codigo_original  # mudou DEMAIS (corrompeu)
        if eixo_novo < eixo_orig - 0.1:
            return codigo_original  # PIOROU
        if len(codigo_novo) < len(codigo_original) * 0.5:
            return codigo_original  # encolheu DEMAIS
        
        return codigo_novo  # APROVADO
    
    except Exception:
        # FALLBACK SEGURO: se PatternEngine falhar, preserva original
        return codigo_original
