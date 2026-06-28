"""Modulo: IA - Interface com modelos Ollama + Router Híbrido (local/cloud)."""
import os, json, urllib.request, re

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')

# --- Router Híbrido ---
# Modos: 'web_search' (grátis, padrão), 'api' (requer key), 'desligado' (só local)
CLOUD_MODE = os.environ.get('MCR_CLOUD_MODE', 'web_search')
CLOUD_API_KEY = os.environ.get('MCR_CLOUD_API_KEY', '')
WEB_SEARCH_TIMEOUT = int(os.environ.get('MCR_WEB_SEARCH_TIMEOUT', '15'))

# Tenta importar ddgs para busca DuckDuckGo
_HAS_DDGS = False
try:
    import ddgs
    DDGS = ddgs.DDGS
    _HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        _HAS_DDGS = True
    except ImportError:
        pass

# Config de modelos — ROUTER DE MODELOS (baseado em testes reais)
# qwen2.5-coder:7b -> MELHOR para GERAR CODIGO (testado: 3/3 cenarios)
# deepseek-r1:7b   -> MELHOR para REVISAR, ANALISAR, PENSAR (chain-of-thought)
#                    NUNCA use para gerar codigo direto (algoritmos errados, typos)
# llama3.1:8b      -> MELHOR para TEXTO PT-BR (lore, traducoes)
# mistral:7b       -> ALTERNATIVO (equilibrio)
# Cada entrada: modelo, ctx (contexto), num_predict, raw (opcional)
MODELOS = {
    # --- GERACAO PESADA (qwen2.5-coder:14b forçado na GPU) ---
    "pesado":     {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    "code":       {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    "leve":       {"modelo": "qwen2.5-coder:7b",  "ctx": 2048, "num_predict": 1024},
    "fast":       {"modelo": "qwen2.5-coder:7b",  "ctx": 4096, "num_predict": 2048},
    # --- REVISAO E ANALISE (qwen14b substitui deepseek - mais preciso, menos falso positivo) ---
    "analisar":   {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    "revisor":    {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    "review":     {"modelo": "qwen2.5-coder:14b", "ctx": 8192, "num_predict": 8192,
                   "main_gpu": 0, "num_gpu": 99},
    # --- CONCEITUAL (qwen14b para explicacoes - acerta nomes das siglas) ---
    "conceito":   {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    "planejador": {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 4096,
                   "main_gpu": 0, "num_gpu": 99},
    # --- TEXTO PT-BR (qwen14b responde sempre; llama se recusa quando nao conhece) ---
    "texto":      {"modelo": "qwen2.5-coder:14b", "ctx": 4096, "num_predict": 2048,
                   "main_gpu": 0, "num_gpu": 99},
    # --- ALTERNATIVO ---
    "alternativo":{"modelo": "mistral:7b",       "ctx": 4096, "num_predict": 4096},
}

def init_module(contexto):
    """Inicializa modulo IA."""
    ia = IA()
    contexto['ia'] = ia
    return 'ia', ia


class IA:
    """Interface para modelos de IA locais (Ollama)."""
    
    def __init__(self):
        self._orquestrador = None
    
    def _get_orquestrador(self):
        if self._orquestrador is None:
            try:
                from modulos.orquestrador import Orquestrador
                self._orquestrador = Orquestrador(ia=self)
            except ImportError:
                pass
        return self._orquestrador
    
    def orquestrar(self, intencao, params=None, consulta="", temp=0.4):
        """Gera texto usando Orquestrador Universal.
        Se nao houver template para a intencao, usa fallback com gerar().
        
        Args:
            intencao: Nome da intencao (ex: 'lore', 'conceito', 'analisar_codigo')
            params: Dict com parametros do template
            consulta: Texto para buscar contexto no ContextCrew/KG
            temp: Temperatura (0.0-1.0)
        Returns:
            String com a resposta, ou None se falhar
        """
        orq = self._get_orquestrador()
        if orq is None:
            return self.gerar(str(params), temp, "leve")
        
        resultado = orq.executar(intencao, params, consulta, temp)
        if resultado and resultado["sucesso"]:
            return resultado["resposta"]
        return None
    
    def fast(self, prompt, temp=0.1, tarefa="fast"):
        """Chamada rapida para classificacoes."""
        cfg = MODELOS.get(tarefa, MODELOS["fast"])
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
    
    def gerar(self, prompt, temp=0.7, tarefa="code"):
        """Chamada completa para geracao de codigo/texto."""
        cfg = MODELOS.get(tarefa, MODELOS["code"])
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
    
    # ============================================================
    # ROUTER HÍBRIDO: decide local vs cloud + busca web estruturada
    # ============================================================
    
    def _get_decider(self):
        """Retorna instancia do Decider (lazy load)."""
        if not hasattr(self, '_decider_inst'):
            from modulos.decider import Decider
            self._decider_inst = Decider(self)
        return self._decider_inst

    def decider(self, consulta, tarefa="code"):
        """Decide se usa LOCAL ou CLOUD (web search) para a consulta.
        
        Usa Decider.classificar() com exemplos como metodo principal.
        Fallback para CLOUD_MODE='desligado' → local.
        
        Args:
            consulta: Texto da pergunta
            tarefa: Tipo de tarefa (code, fast, etc) — nao usado, mantido por compatibilidade
        Returns:
            'local' ou 'cloud'
        """
        if CLOUD_MODE == 'desligado':
            return 'local'

        # Tenta Decider (FAST) primeiro
        try:
            decider = self._get_decider()
            exemplos_local_cloud = [
                ("O que e SPA no MCR?", "local"),
                ("cria um script lua para npc", "local"),
                ("explique o SHC no projeto", "local"),
                ("pesquise python 3.13 na web", "cloud"),
                ("noticias de tecnologia hoje", "cloud"),
                ("quem foi albert einstein?", "cloud"),
            ]
            return decider.classificar(
                consulta, ['local', 'cloud'],
                exemplos=exemplos_local_cloud,
                instrucao="Classifique se a consulta deve usar busca web (cloud) ou " +
                          "conhecimento local (local). Mencao de MCR/Tibia = local."
            )
        except Exception:
            pass

        # Fallback: regex (mantido para robustez)
        if any(p in consulta.lower() for p in ['pesqui', 'busca', 'web', 'noticia', 'quem e', 'o que e']):
            return 'cloud'
        if any(p in consulta.lower() for p in ['mcr', 'spa', 'shc', 'tibia', 'eridanus']):
            return 'local'

        return 'local'
    
    def buscar_web(self, consulta, max_resultados=5):
        """Busca na web, sumariza com fast model, retorna contexto limpo.
        
        Pipeline:
        1. Gera queries inteligentes a partir da consulta
        2. Busca em múltiplas fontes (DuckDuckGo + fallback Wikipedia)
        3. Sumariza resultados com fast model
        4. Retorna texto limpo (máx 4000 chars)
        
        Args:
            consulta: Texto da pergunta
            max_resultados: Máximo de resultados por query
        Returns:
            String com contexto limpo, ou None se falhar
        """
        resultados = self._web_search(consulta, max_resultados)
        if not resultados:
            return None
        
        return self._summarize_web(consulta, resultados)
    
    def _web_search(self, consulta, max_r=5):
        """Busca na web usando DuckDuckGo + fallback Wikipedia."""
        todos = []
        urls_vistas = set()
        
        # Tenta DuckDuckGo primeiro
        if _HAS_DDGS:
            try:
                with DDGS() as ddgs:
                    raw = list(ddgs.text(consulta, max_results=max_r))
                    for r in raw:
                        url = r.get('href', '')
                        if url and url not in urls_vistas:
                            urls_vistas.add(url)
                            todos.append({
                                'titulo': r.get('title', ''),
                                'snippet': r.get('body', ''),
                                'url': url,
                                'fonte': 'DuckDuckGo',
                            })
            except Exception as e:
                print(f"[RouterHibrido] DDGS error: {e}")
        
        # Fallback: busca na Wikipedia via API (sempre funciona, sem API key)
        if len(todos) < 3:
            try:
                import urllib.parse
                termos = urllib.parse.quote(consulta.split('?')[0].strip()[:200])
                url_wiki = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={termos}&format=json&srlimit={max_r}'
                texto = self._fetch_url(url_wiki)
                if texto and '[Erro]' not in texto:
                    import json as _json
                    data = _json.loads(texto)
                    for item in data.get('query', {}).get('search', []):
                        page_title = item.get('title', '')
                        if page_title and page_title not in urls_vistas:
                            urls_vistas.add(page_title)
                            snippet = re.sub(r'<[^>]+>', '', item.get('snippet', ''))
                            todos.append({
                                'titulo': page_title,
                                'snippet': snippet,
                                'url': f'https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}',
                                'fonte': 'Wikipedia',
                            })
            except Exception as e:
                print(f"[RouterHibrido] Wikipedia error: {e}")
        
        return todos if todos else None
    
    def _fetch_url(self, url, timeout=15):
        """Busca conteudo de URL. Retorna texto ou string de erro."""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 MCR-DevIA/1.0'})
            resp = urllib.request.urlopen(req, timeout=timeout)
            content = resp.read()
            try:
                return content.decode('utf-8')
            except:
                try:
                    return content.decode('latin-1')
                except:
                    return content.decode('utf-8', errors='replace')
        except Exception as e:
            return f'[Erro] {e}'
    
    def _summarize_web(self, consulta, resultados):
        """Sumariza resultados web usando fast model (qwen2.5-coder:7b)."""
        if not resultados:
            return None
        
        # Monta resumo dos resultados
        blocos = []
        for i, r in enumerate(resultados[:8], 1):
            blocos.append(f"[{i}] {r['titulo']}\n   {r['snippet']}")
        
        texto_resultados = '\n'.join(blocos)
        
        # Se for muito curto, retorna direto sem sumarizar
        if len(texto_resultados) < 200:
            return texto_resultados[:4000] if texto_resultados else None
        
        prompt = f"""Resuma os resultados de busca abaixo em português, de forma útil e concisa.
        Destaque apenas as informações relevantes para a pergunta. Ignore ruído.
        
        PERGUNTA: {consulta[:300]}
        
        RESULTADOS:
        {texto_resultados[:3000]}
        
        RESUMO (português, máx 500 caracteres):"""
        
        try:
            resumo = self.fast(prompt, temp=0.3, tarefa="fast")
            if resumo:
                return resumo[:4000]
        except Exception as e:
            print(f"[RouterHibrido] Summarize error: {e}")
        
        # Fallback: retorna raw truncado
        return texto_resultados[:4000] if texto_resultados else None
