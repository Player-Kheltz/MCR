"""Modulo: IA - Interface com modelos Ollama."""
import os, json, urllib.request

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')

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
