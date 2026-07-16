"""Conselho V10 - CONSELHO INFINITO. Personalidades sob demanda com ContextCrew + ContextInfinity.
- Zero arquivos de personalidade fixas
- Arquetipos gerados dinamicamente via FAST + contexto do ContextCrew
- Router de modelos por arquétipo (cada um usa o melhor modelo)
- Validação anti-alucinacao + auto-revisao + traducao PT-BR
- + TreeOfThought (G1), PromptCache (G5), TermosCriticos (G7), ValidacaoRelevancia (G6)
  (fundido do enricher.py)"""
import sys, os, time, json, threading, re
from collections import OrderedDict
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ─── Ollama API direto (sem dependencia de mcr.util) ───────────
try:
    import requests as _requests
except ImportError:
    import urllib.request as _urllib
    _requests = None

_OLLAMA_URL = "http://localhost:11434/api/generate"

# Mapeamento de "peso" -> modelo real (ATUALIZADO Jul 2026)
_PESO_PARA_MODELO = {
    "leve":      "phi4-mini:latest",       # 2.5GB, 45 tok/s, qual 9.1
    "code":      "qwen2.5-coder:14b",      # 9GB, 23 tok/s, qual 10/10 em codigo
    "analisar":  "mistral:7b",             # 4.4GB, 57 tok/s, qual 9.4
    "texto":     "gemma4:12b",             # 9.6GB, 41 tok/s, qual 9.4, 262K ctx
    "criativo":  "phi4-mini:latest",       # leve com temperatura alta
}

def _llm(prompt, temp=0.3, peso="leve", max_tokens=512):
    """Chama Ollama com o modelo mapeado pelo peso."""
    modelo = _PESO_PARA_MODELO.get(peso, "phi4-mini:latest")
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temp,
            "num_predict": max_tokens,
            "num_gpu": 999,
        },
    }
    try:
        if _requests is not None:
            r = _requests.post(_OLLAMA_URL, json=payload, timeout=120)
            return r.json().get("response", "")
        body = json.dumps(payload).encode()
        req = _urllib.Request(_OLLAMA_URL, data=body,
            headers={"Content-Type": "application/json"})
        with _urllib.urlopen(req, timeout=120) as f:
            return json.loads(f.read()).get("response", "")
    except Exception as e:
        return f"[ERRO LLM] {e}"

_fast = _llm  # alias para compatibilidade
_gerar = _llm  # alias para compatibilidade

# ─── Tradutor (fallback silencioso se nao existir) ─────────────
try:
    from mcr.tradutor import traduzir as _traduzir
except ImportError:
    def _traduzir(t, **kw):
        return t

# ─── Memoria (fallback) ───────────────────────────────────────
try:
    from modulos import memoria_conselho as _memoria
except ImportError:
    class _MemoriaFake:
        @staticmethod
        def resumo_para_prompt(*a, **kw): return ""
        @staticmethod
        def salvar(*a, **kw): pass
    _memoria = _MemoriaFake()

# ─── Decider / IA (fallback) ──────────────────────────────────
# NOTA: decider.py nao existe (o arquivo real eh decisor.py, sem classe Decider)
# Usamos _llm para classificacao, que funciona de verdade
class Decider:
    def __init__(self, **kw): pass
    def classificar(self, texto, categorias=None, instrucao="", exemplos=None):
        cat_list = categorias or ['codigo', 'factual', 'opiniao', 'procedimental', 'ambientacao']
        ex = (
            "Exemplos:\n"
            "'crie um NPC ferreiro' -> ambientacao\n"
            "'revise este codigo' -> codigo\n"
            "'explique o que e Markov' -> factual\n"
            "'como configurar o servidor' -> procedimental\n"
            "'qual a melhor linguagem' -> opiniao\n"
        )
        prompt = (
            f"Classifique a frase em UMA categoria: {', '.join(cat_list)}\n"
            f"{ex}\n"
            f"Frase: '{texto}'\n"
            f"Categoria:"
        )
        r = _llm(prompt, 0.1, "analisar", 20)
        r = r.strip().lower().rstrip('.')
        for cat in cat_list:
            if cat == r:
                return cat
        # fallback: verifica se alguma categoria aparece na resposta
        for cat in cat_list:
            if cat in r:
                return cat
        return "desconhecido"

try:
    from mcr.ia import IA
except ImportError:
    class IA:
        pass

# Orquestrador (template engine) — opcional
_Orquestrador = None
_ORQ_TEMPLATES = {}
try:
    from mcr.orquestrador import Orquestrador as _Orquestrador, _TEMPLATES as _ORQ_TEMPLATES
except ImportError:
    pass

_MCR_IDENTITY = None  # carregado sob demanda via _carregar_contexto()

def _carregar_contexto():
    """Carrega contexto real do codigo fonte do MCR em vez de textos genericos."""
    ctx = []
    base = os.path.dirname(__file__)
    
    # Arquivos principais do MCR (os mais importantes)
    arquivos_chave = [
        ("mcr.py", 30),       # pipeline principal
        ("engine.py", 20),    # motor markov
        ("equacao_mcr.py", 15), # equacao
        ("coupling.py", 15),  # acoplamento
        ("signature.py", 15), # assinatura
    ]
    for nome, linhas in arquivos_chave:
        path = os.path.join(base, nome)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    conteudo = ''.join(f.readlines()[:linhas])
                    ctx.append(f"# {nome}\n{conteudo}")
            except:
                pass
    
    # config_llm.py (modelos ativos)
    config_path = os.path.join(base, 'config_llm.py')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                ctx.append(f"# Modelos\n{f.read()}")
        except:
            pass
    
    return "\n\n".join(ctx) if ctx else "Projeto MCR."

_CONTEXTO_CACHE = None

def _ctx():
    global _CONTEXTO_CACHE
    if _CONTEXTO_CACHE is None:
        _CONTEXTO_CACHE = _carregar_contexto()
    return _CONTEXTO_CACHE

# Router: mapeia cada arquétipo ao melhor modelo ATUAL (Jul 2026)
# Baseado no benchmark: mistral:7b (qual 9.4, 57 tok/s) é o melhor custo-beneficio
_ROUTER = {
    "analista":             "analisar",  # mistral:7b — dados e fatos
    "critico":              "analisar",  # mistral:7b — analise critica
    "estrategista":         "analisar",  # mistral:7b — visao geral
    "arquiteto":            "code",      # qwen2.5-coder:14b — design de sistemas
    "contador_historias":   "analisar",  # mistral:7b — lore, 57 tok/s, qualidade 9.4
    "revisor_codigo":       "code",      # qwen2.5-coder:14b — qualidade 10/10
    "psicologo":            "leve",      # phi4-mini — rapido, so analisa processo
    "tecnico":              "code",      # qwen2.5-coder:14b — implementacao
    "especialista":         "code",      # qwen2.5-coder:14b — conhecimento profundo
    "filosofo":             "analisar",  # mistral:7b — reflexao
    "criativo":             "criativo",  # phi4-mini (temp alta) — ideias novas
}

# Prompts adaptativos para cada arquétipo (com placeholders)
_PROMPTS = {
    "analista": """{mcr}
Contexto do ContextCrew: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}
ContextInfinity (historico recente): {ctx_infinity}

ANALISTA - Dados e fatos concretos. Numeros, versoes, metricas.
Responda com FATOS CONCRETOS do projeto MCR (Tibia).
Seja especifico. 2-3 frases curtas:""",

    "critico": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}

CRITICO - Riscos e problemas. Nada generico.
O que pode dar ERRADO? Riscos especificos.
2-3 frases curtas com riscos concretos:""",

    "estrategista": """{mcr}
Contexto do ContextCrew: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}

ESTRATEGISTA - Visao geral e planejamento.
Qual a melhor direcao? Curto, medio e longo prazo.
Recomendacao concreta. 2-3 frases curtas:""",

    "arquiteto": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}

ARQUITETO - Design de sistemas e componentes.
Como os componentes se relacionam? Padroes de design?
Problemas estruturais e solucoes. 2-3 frases curtas:""",

    "contador_historias": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Inspiracao KG: {kg}
Pergunta: {pergunta}

CONTADOR DE HISTORIAS - Crie LORE RICA em portugues brasileiro.
Nomes proprios de personagens, lugares, artefatos.
Historia vivida com: fundacao, era de ouro, declinio, situacao atual.
Nomes UNICOS e ORIGINAIS. 3-4 frases descritivas:""",

    "revisor_codigo": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}

REVISOR DE CODIGO - Seguranca e boas praticas.
Analise tecnica: bugs, seguranca, performance.
Problemas especificos com sugestoes de correcao.
2-3 frases curtas:""",

    "psicologo": """{mcr}
Pergunta sendo discutida: {pergunta}

PSICOLOGO DO CONSELHO - Voce NAO responde a pergunta.
Analise o PROCESSO:
1) Ha algum VIES na pergunta?
2) O conselho esta alinhado com os valores do projeto?
3) Ha risco de GROUPTHINK?
4) Precisa de mais informacoes?
Responda SOMENTE sobre o PROCESSO. 2-3 frases:""",

    "tecnico": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}

ESPECIALISTA TECNICO - Implementacao e detalhes.
Comandos, arquivos, parametros especificos.
Implementacao concreta. 2-3 frases curtas:""",

    "criativo": """{mcr}
Contexto do ContextCrew: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}

CRIATIVO - Conexoes nao-obvias e inovacao.
Combine conceitos de formas SURPREENDENTES.
Pense em analogias, metaforas, possibilidades.
O objetivo: gerar algo NOVO que nao estava explicito antes.
3-4 frases criativas em PT-BR:""",
}

# Arquétipos base por tipo de pergunta (classificacao 0 IA)
_ARQUETIPOS_POR_TIPO = {
    'factual': ['analista', 'critico'],
    'procedimental': ['analista', 'tecnico', 'critico'],
    'ambientacao': ['contador_historias', 'psicologo', 'estrategista'],
    'opiniao': ['estrategista', 'analista', 'psicologo'],
    'codigo': ['revisor_codigo', 'arquiteto', 'critico'],
    'inovacao': ['criativo', 'estrategista', 'contador_historias'],
    'filosofico': ['filosofo', 'analista', 'estrategista'],  # Modo Offline Turbinado
    'desconhecido': ['analista', 'critico', 'estrategista'],
}


# ============================================================
# G1 — TREE OF THOUGHT (multiplas perspectivas em paralelo)
# ============================================================
_CAMINHOS_TOT = {
    "analitico": "Pense como um ANALISTA. Foque em dados, fatos, numeros, versoes, metricas e detalhes tecnicos. Seja especifico e preciso.",
    "criativo": "Pense como um CONTADOR DE HISTORIAS. Use exemplos concretos, analogias, cenarios praticos e aplicacoes reais.",
    "critico": "Pense como um CRITICO. Questione suposicoes, aponte limitacoes, riscos, pontos cegos. Nao aceite nada pelo valor nominal.",
    "pragmatico": "Pense como um PRAGMATICO. O que funciona na pratica? Qual a acao mais simples que resolve? Ignore teoria, foque no resultado concreto.",
}

def tree_of_thought(prompt_base, temp=0.3):
    """Gera 3+ perspectivas e sintetiza usando _llm direto."""
    perspectivas = {}
    threads = []
    lock = threading.Lock()
    
    def _gerar_perspectiva(nome, instrucao):
        p = f"{instrucao}\n\nResponda EXATAMENTE a pergunta abaixo:\n{prompt_base}"
        r = _llm(p, temp, "analisar", 300)
        with lock:
            perspectivas[nome] = r.strip()
    
    for nome, instrucao in list(_CAMINHOS_TOT.items())[:3]:  # 3 perspectivas
        t = threading.Thread(target=_gerar_perspectiva, args=(nome, instrucao))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    
    if len(perspectivas) < 2:
        return prompt_base
    
    # Sintese com modelo mais forte
    blocos = '\n'.join(f"{n.upper()}:\n{p}" for n, p in perspectivas.items())
    prompt_sintese = (
        f"{blocos}\n"
        f"Sintetize em resposta UNICA, focando na pergunta original:\n{prompt_base}"
    )
    sintese = _llm(prompt_sintese, 0.3, "analisar", 512)
    return sintese or prompt_base


# ============================================================
# G5 — PROMPT CACHE LRU (fallback se modulo nao existir)
# ============================================================
try:
    from mcr.modules.orquestrador import PromptCache
except ImportError:
    from collections import OrderedDict
    class PromptCache:
        def __init__(self, *a, **kw): self._cache = OrderedDict()
        def obter(self, k): return self._cache.get(k)
        def definir(self, k, v): self._cache[k] = v


# ============================================================
# G7 — TERMOS CRITICOS (extracao melhorada)
# ============================================================
def extrair_termos_criticos(texto):
    """Extrai termos relevantes incluindo siglas e extensoes (.lua, .py)."""
    if not texto:
        return []
    termos = re.findall(r'\b[a-zA-Z.]{2,}\b', texto.lower())
    stop = {'de','para','que','com','uma','era','mais','como','por','seu','sua',
            'tem','ela','ele','voce','me','te','se','nos','lhe','das','dos',
            'nas','nem','mas','sobre','isto','isso','aquele','este','essa',
            'em','no','na','um','uns','umas','a','o','as','os','do','da','e'}
    return [t for t in termos if t not in stop]


# ============================================================
# G6 — VALIDACAO DE RELEVANCIA
# ============================================================
def validar_relevancia(ia, pergunta, contexto):
    """FAST valida se o contexto coletado e relevante para a pergunta."""
    if not contexto:
        return False
    textos = ' '.join(t for _, t in contexto)
    if not textos.strip() or len(textos) < 20:
        return False
    try:
        prompt = f"Contexto: {textos}\nPergunta: {pergunta}\nEste contexto ajuda a responder? (sim/nao)"
        resp = ia.fast(prompt, 0.1, 'leve').strip().lower()
        return resp.startswith('sim')
    except Exception:
        return True


class Conselho:
    """Conselho Infinito V10: personalidades sob demanda com ContextCrew + ContextInfinity."""

    def __init__(self, kg=None, ia=None, ctx_crew=None, auto_componentes=True):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew
        self.auto_componentes = auto_componentes
        self._decider = Decider(ia=self.ia) if ia else Decider()

    def _classificar(self, texto):
        """Classifica tipo de pergunta via Decider (FAST model + exemplos)."""
        return self._decider.classificar(
            texto,
            categorias=['codigo', 'ambientacao', 'factual', 'opiniao', 'procedimental', 'desconhecido'],
            instrucao="Classifique o tipo da pergunta do usuario sobre o Projeto MCR.",
            exemplos=[
                ("como implementar um novo NPC em lua", "codigo"),
                ("cria uma funcao em python pra calcular dano", "codigo"),
                ("crie a lore da cidade de Eridanus", "ambientacao"),
                ("conte a historia do heroi Kheltz", "ambientacao"),
                ("o que e SPA", "factual"),
                ("explique como funciona o sistema de habilidades", "factual"),
                ("qual a melhor estrategia para balancear classes", "opiniao"),
                ("o que voce acha de usar FastAPI vs Flask", "opiniao"),
                ("como configurar o OTClient passo a passo", "procedimental"),
                ("como criar um servidor do zero tutorial", "procedimental"),
            ],
        )

    def _ctx_infinity(self):
        """Le as ultimas mensagens do ContextInfinity (arquivo JSONL)."""
        p = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_conversa.jsonl')
        if not os.path.exists(p): return ""
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return '\n'.join(json.loads(l).get('msg', '') for l in f.readlines()[-5:] if l.strip())
        except Exception:
            return ""

    def _ctx_crew_contexto(self, pergunta):
        """Obtem contexto do ContextCrew (5 fontes: KG, WebLearn, Docs, Codigo, Web)."""
        if not self.ctx_crew:
            return ""
        try:
            return self.ctx_crew.executar(pergunta)
        except Exception as e:
            print(f'  [ContextCrew] ERRO: {e}')
            return ""

    def _kg(self, q):
        """Busca lessons relevantes no KG."""
        if not self.kg:
            return ""
        try:
            return '\n'.join(f"- {r.get('solucao', '')}" for r in self.kg.buscar(q, max_r=5))
        except Exception:
            return ""

    def _enriquecer_conselho(self, pergunta):
        """Gera enriquecimento usando Context Enricher (substitui _componentes)."""
        try:
            from mcr.context_enricher import ContextEnricher
            enricher = ContextEnricher(ctx_crew=self.ctx_crew, kg=self.kg)
            resultado = enricher.enriquecer(pergunta, termos=None)
            if resultado.get('valido') and resultado.get('conteudo'):
                print(f'  [Conselho] Enricher OK: {resultado["tipo"]}')
                return resultado['conteudo']
        except Exception as e:
            print(f'  [Conselho] Enricher ERRO: {e}')
        return ""  # fallback: sem enriquecimento
    
    def enriquecer(self, pergunta):
        """Interface publica: enriquece pergunta com KG + ctx_crew.
        
        Usado pelo MasterAgent para enriquecer prompts automaticamente.
        Retorna pergunta enriquecida, ou pergunta original se sem contexto.
        """
        partes = [pergunta]
        
        # KG
        if self.kg:
            try:
                lessons = self.kg.buscar(pergunta, max_r=3)
                if lessons:
                    ctx_kg = '\n'.join(f"KG: {l.get('solucao','')}" for l in lessons)
                    partes.append(ctx_kg)
            except Exception:
                pass
        
        # ContextCrew
        if self.ctx_crew:
            try:
                ctx_crew_txt = self.ctx_crew.executar(pergunta)
                if ctx_crew_txt and len(ctx_crew_txt) > 20:
                    partes.append(f"Contexto: {ctx_crew_txt}")
            except Exception:
                pass
        
        prompt_enriquecido = '\n\n'.join(partes)
        return prompt_enriquecido if prompt_enriquecido != pergunta else pergunta
    
    def _componentes(self, pergunta):
        """Gera componentes (personagens, locais, artefatos) se for pergunta de lore.
        Fallback: usa Enricher primeiro, se falhar usa metodo antigo."""
        if not self.kg or not self.auto_componentes:
            return ""
        
        # Tenta Enricher primeiro (universal, nao so lore)
        enriquecido = self._enriquecer_conselho(pergunta)
        if enriquecido:
            return enriquecido
        
        # Fallback: metodo antigo (só para lore)
        p_lower = pergunta.lower()
        e_factual = any(pergunta.lower().startswith(p) for p in
                        ['o que e', 'o que eh', 'como funciona', 'como usar',
                         'para que serve', 'qual a diferenca', 'explique', 'defina'])
        if e_factual:
            return ""
        quer_lore = any(w in p_lower for w in ['historia', 'lore', 'conto', 'narrativa',
                                                 'personagem', 'npc', 'heroi',
                                                 'local', 'lugar', 'cidade', 'regiao',
                                                 'artefato', 'item', 'arma'])
        if not quer_lore:
            return ""
        resultados = self.kg.buscar(pergunta, max_r=15)
        comps = [r for r in resultados if r.get('ctx') == 'componente_historia']
        if comps:
            return '\n'.join(f"[{c.get('erro', '')}] {c.get('solucao', '')}" for c in comps)
        print('  [Componentes] Gerando...')
        for tipo, prompt_t in [
            ("Personagens", f"Crie 2 personagens DETALHADOS para {pergunta} em Tibia."),
            ("Locais", f"Crie 1 local DETALHADO para {pergunta} em Tibia."),
            ("Artefatos", f"Crie 1 artefato UNICO para {pergunta} em Tibia."),
        ]:
            r = _fast(prompt_t, 0.4, "leve") or ""
            if r:
                self.kg.aprender(f"{tipo}: {pergunta}", "Gerado", r, "componente_historia")
        return self._componentes(pergunta)  # Recursao 1x

    def _detectar_arquetipos(self, pergunta, tipo, ctx_crew_txt):
        """Usa FAST para detectar arquetipos alem dos base."""
        # Arquetipos base pelo tipo
        base = list(_ARQUETIPOS_POR_TIPO.get(tipo, _ARQUETIPOS_POR_TIPO['desconhecido']))

        # FAST: detecta arquetipos adicionais especificos
        ctx = _ctx()
        detect = _fast(
            f"{ctx}\n\n"
            f"Pergunta: {pergunta}\n"
            f"Contexto do ContextCrew: {ctx_crew_txt}\n\n"
            f"Tipo classificado: {tipo}\n"
            f"Arquetipos ja selecionados: {', '.join(base)}\n\n"
            f"Identifique ATE 2 arquetipos ADICIONAIS necessarios para responder "
            f"esta pergunta. Responda APENAS os nomes, separados por virgula.\n"
            f"Opcoes disponiveis: {', '.join(_ROUTER.keys())}\n"
            f"Se nenhum adicional for necessario, responda: nenhum",
            0.2, "leve"
        ) or ""

        extras = [a.strip().lower() for a in detect.split(',') if a.strip().lower() in _ROUTER]
        todos = base + extras
        # Remove duplicatas mantendo ordem
        vistos = set()
        resultado = []
        for a in todos:
            if a not in vistos:
                vistos.add(a)
                resultado.append(a)
        print(f'  [Arquetipos] Base: {base} | Extras: {extras} | Final: {resultado}')
        return resultado

    def deliberar(self, pergunta):
        """Conselho Infinito: delibera sobre a pergunta com personalidades sob demanda."""
        import re as _re
        t0 = time.time()

        # 1. COLETA DE CONTEXTO (paralelizavel)
        tipo = self._classificar(pergunta)
        ctx_infinity = self._ctx_infinity()
        ctx_crew_txt = self._ctx_crew_contexto(pergunta)
        kg = self._kg(pergunta)
        comps = self._componentes(pergunta)
        if comps:
            kg = kg + '\n\nComponentes (USE-OS):\n' + comps

        print(f'[Conselho Infinito V10] Tipo: {tipo} | ContextCrew: {len(ctx_crew_txt)}c | KG: {len(kg)}c')

        # 2. DETECTAR ARQUETIPOS
        arquetipos = self._detectar_arquetipos(pergunta, tipo, ctx_crew_txt)
        if not arquetipos:
            arquetipos = ['analista', 'critico']

        # 3. EXECUTAR ARQUETIPOS EM PARALELO
        resultados = {}
        lock = threading.Lock()

        def executar_arquétipo(nome):
            router = _ROUTER.get(nome, "leve")
            orq_template_key = f"conselho_{nome}"
            
            # CARREGA MEMORIA PESSOAL DO MEMBRO
            memoria_pessoal = _memoria.resumo_para_prompt(nome, max_entradas=10)
            
            # Tenta orquestrador primeiro (template + contexto enriquecido)
            usou_orquestrador = False
            if orq_template_key in _ORQ_TEMPLATES:
                try:
                    ctx_atual = _ctx()
                    orq = _Orquestrador(kg=self.kg, ia=self.ia, ctx_crew=self.ctx_crew)
                    params = {
                        "mcr": ctx_atual,
                        "ctx_crew": ctx_crew_txt,
                        "kg": kg,
                        "pergunta": pergunta,
                        "ctx_infinity": ctx_infinity,
                        "memoria_pessoal": memoria_pessoal,
                    }
                    r = orq.executar(orq_template_key, params, consulta=pergunta, temp=0.4)
                    if r and r.get("sucesso"):
                        opiniao = r.get("resposta", "")
                        with lock:
                            resultados[nome] = opiniao
                        # Salva na memoria pessoal
                        _memoria.salvar(nome, pergunta, opiniao,
                                      padrao=f"deliberou sobre: {pergunta}", categoria="conselho")
                        return
                except Exception:
                    pass
                usou_orquestrador = True
            
            # Fallback: prompt fixo original (com memoria pessoal)
            prompt_t = _PROMPTS.get(nome)
            if not prompt_t:
                with lock:
                    resultados[nome] = f'[ERRO] Arquetipo {nome} desconhecido'
                return
            try:
                ctx_atual = _ctx()
                prompt = prompt_t.format(
                    mcr=ctx_atual,
                    ctx_crew=ctx_crew_txt,
                    kg=kg,
                    pergunta=pergunta,
                    ctx_infinity=ctx_infinity,
                )
                # Injeta memoria pessoal no prompt
                if memoria_pessoal:
                    prompt += f"\n\nSUA MEMORIA PESSOAL:\n{memoria_pessoal}\n"
                
                # [Conselho 2.0] FAST + contexto, sem 14b
                opiniao = _fast(prompt, 0.4, router) or ""
                with lock:
                    resultados[nome] = opiniao
                # Salva na memoria pessoal
                _memoria.salvar(nome, pergunta, opiniao,
                              padrao=f"deliberou sobre: {pergunta}", categoria="conselho")
            except Exception as e:
                with lock:
                    resultados[nome] = f'[ERRO] {e}'

        threads = []
        for nome in arquetipos:
            t = threading.Thread(target=executar_arquétipo, args=(nome,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Separa psicologo do resto
        opinioes = []
        avaliacao_psicologo = ""
        for nome, opiniao in resultados.items():
            if nome == 'psicologo':
                avaliacao_psicologo = opiniao
            elif opiniao:
                opinioes.append((nome, opiniao))

        if not opinioes:
            return {"veredito": "Sem opinioes", "tempo_total": round(time.time() - t0, 1)}

        # 4. DEBATE PROTOCOL (refinamento entre os proprios arquetipos)
        debate_ctx = ""
        if len(opinioes) >= 2:
            try:
                # Pega as 2 opinioes mais divergentes para debater
                nomes = [n for n, _ in opinioes[:2]]
                textos = [t for _, t in opinioes[:2]]
                prompt_debate = (
                    f"Pergunta original: {pergunta}\n\n"
                    f"Opiniao 1 ({nomes[0]}):\n{textos[0]}\n\n"
                    f"Opiniao 2 ({nomes[1]}):\n{textos[1]}\n\n"
                    f"Analise as duas opinioes acima. Aponte concordancias, divergencias "
                    f"e sugira um ponto de equilibrio. Seja conciso (3-5 frases)."
                )
                debate_result = _llm(prompt_debate, 0.3, "analisar", 400)
                if debate_result and len(debate_result) > 50:
                    debate_ctx = f"\n\nDebate entre {nomes[0]} e {nomes[1]}:\n{debate_result}\n"
                    print(f'  [Debate] Refinamento obtido ({len(debate_result)} chars)')
            except Exception as e:
                print(f'  [Debate] ERRO: {e}')

        # 5. VEREDITO FINAL
        ctx_atual = _carregar_contexto()
        db = f"{ctx_atual}\n\n"
        db += f"Pergunta: {pergunta}\n\n"
        if ctx_crew_txt:
            db += f"CONTEXTO DO PROJETO (ContextCrew - 5 fontes):\n{ctx_crew_txt}\n\n"
        if kg:
            db += f"FATOS DO KG:\n{kg}\n\n"
        if ctx_infinity:
            db += f"Historico recente (ContextInfinity):\n{ctx_infinity}\n\n"
        if debate_ctx:
            db += debate_ctx
        for n, o in opinioes:
            db += f"{n}: {o}\n\n"
        if avaliacao_psicologo:
            db += f"Psicologo: {avaliacao_psicologo}\n\n"

        db += ("VEREDITO FINAL - Exijo: RESPOSTA COMPLETA E DETALHADA em portugues brasileiro.\n"
               "Nomes proprios, numeros, descricoes vividas.\n"
               "RESPEITE OS FATOS DO PROJETO listados acima.\n"
               "Nao invente significados para siglas - use os significados do CONTEXTO DO PROJETO MCR.\n"
               "Estruture em paragrafos se necessario.")

        v = _fast(db, 0.4, "leve") or "Sem consenso"  # [Conselho 2.0] FAST em vez de 14b

        # 6. VALIDACAO ANTI-ALUCINACAO
        if kg:
            prompt_val = (
                f"CONTEXTO DO PROJETO:\n"
                f"{ctx_atual}\n\n"
                f"FATOS DO KG:\n{kg}\n\n"
                f"Verifique se o texto ABAIXO esta consistente com o contexto do projeto MCR (Tibia).\n"
                f"Cada afirmacao deve corresponder aos fatos listados acima.\n\n"
                f"Texto:\n{v}\n\n"
                f"Tem ALGUM erro no texto? Responda apenas:\n"
                f"- OK (se tudo correto)\n"
                f"- ERRO: (descreva o erro em 10 palavras)"
            )
            validacao = _fast(prompt_val, 0.1, "leve") or "OK"
            if 'ERRO' in validacao:
                print(f'  [Validador] {validacao}')
                v = _gerar(
                    f"{ctx_atual}\n\n"
                    f"Com base APENAS nos FATOS abaixo, responda em PT-BR:\n\n"
                    f"FATOS DO PROJETO:\n{kg}\n\n"
                    f"Pergunta original: {pergunta}\n\n"
                    f"REGRAS:\n"
                    f"- Use SOMENTE os FATOS listados acima\n"
                    f"- Nao adicione informacoes de fora\n"
                    f"- Nao invente siglas, tecnologias, nomes\n"
                    f"- Seja conciso (3-5 frases)\n"
                    f"- Se nao houver fato suficiente, diga 'Nao ha informacao suficiente no KG'\n\n"
                    f"Resposta:",
                    0.1, "code"
                ) or v
                print(f'  [Validador] Corrigido ({len(v)} chars)')

        # 7. VEREDITO FINAL (sem auto-revisao, sem traducao - os modelos ja respondem em PT-BR)
        r = {
            "veredito": v,
            "opinioes": opinioes,
            "psicologo": avaliacao_psicologo,
            "tempo_total": round(time.time() - t0, 1),
            "honorarios_criados": arquetipos,
            "tipo": tipo,
        }
        nomes = len(set(_re.findall(r'\b[A-Z][a-z]{2,}\b', v)))
        print(f'  [Veredito] ({r["tempo_total"]:.1f}s) {len(v)} chars, {nomes} nomes, '
              f'{len(opinioes)} arquetipos')
        return r
