"""Orquestrador Universal - Motor de prompts com template + injecao de contexto.

ESTRATEGIA: Em vez de gerar prompts do zero (que falha com modelos leves),
usamos TEMPLATES fixos de alta qualidade (iguais aos originais) e INJETAMOS
contexto enriquecido por FAST + ContextCrew + ContextInfinity + KG.

GARANTIAS:
  - Template garante qualidade MINIMA igual ao original
  - Contexto so ENRIQUECE, nunca degrada
  - Cache LRU elimina regeneracao desnecessaria
  - 4 tieres de fallback (nunca retorna vazio)
  - Validacao keyword-based + AI como fallback

Como usar:
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg, ia, ctx_crew)
    resultado = orq.executar("lore", {"topico": "Eridanus", "tipo": "local"})
"""
import sys, os, json, time, hashlib, threading
from collections import OrderedDict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast as _fast, gerar as _gerar

# ============================================================
# PROMPT CACHE LRU
# ============================================================
class PromptCache:
    """Cache LRU de prompts/snippets por (intencao, params_hash)."""
    
    def __init__(self, max_size=64):
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def _chave(self, intencao, params, consulta):
        raw = f"{intencao}|{json.dumps(params, sort_keys=True, ensure_ascii=False)}|{consulta}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def get(self, intencao, params, consulta=""):
        return self._cache.get(self._chave(intencao, params, consulta))
    
    def set(self, intencao, params, consulta, valor):
        chave = self._chave(intencao, params, consulta)
        if chave in self._cache:
            self._cache.move_to_end(chave)
        self._cache[chave] = valor
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
    
    def limpar(self):
        self._cache.clear()

_CACHE = PromptCache()

# ============================================================
# TEMPLATES DE PROMPT (alta qualidade, mesmos dos originais)
# ============================================================
_TEMPLATES = {
    "lore_npc": """Crie lore para NPC '{nome}'.
{contexto_extra}
HISTORIA: (2 frases sobre o passado)
PERSONALIDADE: (3 adjetivos que definem)
SAUDACAO: (fala tipica)
SEGREDO: (algo que ninguem sabe)
Use nomes proprios em portugues. Responda em PT-BR.""",

    "lore_item": """Crie lore para item '{nome}'.
{contexto_extra}
ORIGEM: (de onde veio, quem criou)
PODER: (o que faz, efeitos)
LENDA: (o que dizem sobre ele)
Use nomes proprios em portugues. Responda em PT-BR.""",

    "lore_local": """Crie lore para local '{nome}'.
{contexto_extra}
APARENCIA: (como parece, ambiente)
HISTORIA: (o que aconteceu ali)
PERIGO: (o que espreita os visitantes)
Use nomes proprios em portugues. Responda em PT-BR.""",

    "lore": """Crie uma lore detalhada sobre {topico}.
{contexto_extra}
Inclua nomes proprios em portugues, lugares, personagens e eventos.
Seja especifico e evite generalizacoes.
Contexto: MCR = servidor de Tibia (Canary). SPA = Sistema de Progressao do Aventureiro.
Responda em PT-BR.""",

    "analisar_codigo": """{estrutura}

Descricao: {descricao}

Para cada problema encontrado, responda:
LINHA X: tipo - descricao

{contexto_extra}
Use nomes de funcoes e linhas reais do codigo acima.
Responda em PT-BR.""",

    "analisar_texto": """{estrutura}

Descricao: {descricao}

Para cada problema encontrado, responda:
LINHA X: tipo do problema - descricao

{contexto_extra}
Responda em PT-BR.""",

    "review": """Revise os dados extraidos abaixo.
{few_shot}
{itens}

{contexto_extra}
Para cada ITEM com erro, responda: ITEM X: ERRO - descricao
Para itens corretos: ITEM X: OK
Responda em PT-BR.""",

    "conceito": """O projeto MCR e um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ).
SPA = Sistema de Progressao do Aventureiro, SHC = Sistema de Habilidades Contextuais.

Analise o CODIGO e a DOCUMENTACAO abaixo e extraia conhecimento CONCEITUAL sobre '{conceito}'.
{contexto_extra}
NAO use significados genericos da sigla.
Explique o CONCEITO - o que e, como funciona, para que serve.
Inclua detalhes tecnicos e especificos da documentacao.

Contexto:
{contexto}

Produza um paragrafo conciso (3-5 frases).""",

    "perguntar": """Pergunta: {pergunta}
{contexto_extra}
Responda de forma util e especifica com base no contexto do projeto MCR.
MCR = servidor de Tibia (Canary). SPA = Sistema de Progressao do Aventureiro.
Responda em PT-BR.""",

    "componentes_personagens": """Crie 3 personagens para uma historia sobre {tema} em Tibia.
{contexto_extra}
Cada um com: nome proprio, funcao, personalidade.
Formato: Nome: [nome] | Funcao: [funcao] | Personalidade: [personalidade]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "componentes_locais": """Crie 2 locais para uma historia sobre {tema} em Tibia.
{contexto_extra}
Cada um com: nome do local, descricao, significado.
Formato: Local: [nome] | Descricao: [descricao]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "componentes_artefatos": """Crie 2 artefatos ou eventos importantes para uma historia sobre {tema} em Tibia.
{contexto_extra}
Cada um com: nome, descricao, poder/significado.
Formato: Artefato: [nome] | Descricao: [descricao]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "revisar": """Arquivo: {arquivo}
Mudanca: {descricao}
Codigo atual ({linhas} linhas):
{conteudo}

{contexto_extra}
Risco ALTO, MEDIO ou BAIXO? Responda so o nivel.
Se tiver ALTO risco, explique por que.""",

    "classificar_nomes": """Classifique cada item em UMA palavra: gerenciador, dados, servico, controle, modelo, util, outro.
{contexto_extra}
{itens}""",

    # Templates do Conselho Infinito V10 (arquetipos)
    "conselho_analista": """{mcr}
Contexto do ContextCrew: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}
ContextInfinity: {ctx_infinity}
{contexto_extra}
ANALISTA - Dados e fatos concretos do projeto MCR (Tibia).
Numeros, versoes, metricas. Seja especifico. 2-3 frases curtas.""",

    "conselho_critico": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
CRITICO - Riscos e problemas especificos do projeto MCR (Tibia).
Nada generico. 2-3 frases curtas com riscos concretos.""",

    "conselho_estrategista": """{mcr}
Contexto do ContextCrew: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}
{contexto_extra}
ESTRATEGISTA - Visao geral, planejamento curto/medio/longo prazo.
Recomendacao concreta para o projeto MCR. 2-3 frases curtas.""",

    "conselho_arquiteto": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
ARQUITETO - Design de sistemas. Componentes, relacoes, padroes.
Problemas estruturais e solucoes. 2-3 frases curtas.""",

    "conselho_contador_historias": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Inspiracao KG: {kg}
Pergunta: {pergunta}
{contexto_extra}
CONTADOR DE HISTORIAS - Crie LORE RICA em PT-BR.
Nomes proprios de personagens, lugares, artefatos.
Historia vivida: fundacao, era de ouro, declinio, situacao atual.
Nomes UNICOS e ORIGINAIS. 3-4 frases descritivas.""",

    "conselho_psicologo": """{mcr}
Pergunta sendo discutida: {pergunta}
{contexto_extra}
PSICOLOGO DO CONSELHO - Analise APENAS o PROCESSO, nao responda:
1) Ha algum VIES na pergunta?
2) O conselho esta alinhado com os valores do projeto?
3) Ha risco de GROUPTHINK?
4) Precisa de mais informacoes?
2-3 frases sobre o PROCESSO apenas.""",

    "conselho_revisor_codigo": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
REVISOR DE CODIGO - Seguranca e boas praticas.
Bugs, seguranca, performance. Problemas especificos com sugestoes.
2-3 frases curtas.""",

    "conselho_tecnico": """{mcr}
Contexto do ContextCrew: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
ESPECIALISTA TECNICO - Implementacao e detalhes tecnicos.
Comandos, arquivos, parametros especificos. 2-3 frases curtas.""",
}

# ============================================================
# ROTEAMENTO DE MODELOS
# ============================================================
_ROUTER = {
    "lore_npc": "texto",
    "lore_item": "texto",
    "lore_local": "texto",
    "lore": "texto",
    "analisar_codigo": "analisar",
    "analisar_texto": "texto",
    "review": "review",
    "conceito": "pesado",
    "perguntar": "texto",
    "componentes_personagens": "leve",
    "componentes_locais": "leve",
    "componentes_artefatos": "leve",
    "revisar": "leve",
    "classificar_nomes": "leve",
    # Conselho arquetipos
    "conselho_analista": "leve",
    "conselho_critico": "analisar",
    "conselho_estrategista": "pesado",
    "conselho_arquiteto": "pesado",
    "conselho_contador_historias": "texto",
    "conselho_psicologo": "texto",
    "conselho_revisor_codigo": "review",
    "conselho_tecnico": "code",
    "default": "leve",
}

# ============================================================
# VALIDACAO (keyword-based + AI fallback)
# ============================================================
_KEYWORDS_TIBIA = [
    "tibia", "server", "ot", "npc", "player", "monster", "spell", "item",
    "quest", "mapa", "cidade", "dungeon", "boss", "loot", "xp", "level",
    "guild", "war", "pvp", "skill", "magic", "sword", "shield", "armor",
    "helmet", "potion", "rune", "wand", "staff", "bow", "arrow",
    "eridanus", "mcr", "spa", "shc", "canary", "otclient", "otbr",
    "aventureiro", "progressao", "habilidade", "postura", "nivel",
]

def _validar_conteudo(texto):
    """Validacao rapida keyword-based. So chama AI se duvidoso."""
    if not texto or texto == "(conteudo filtrado pela validacao)":
        return False
    
    texto_lower = texto.lower()
    palavras_encontradas = sum(1 for kw in _KEYWORDS_TIBIA if kw in texto_lower)
    
    # Se encontrar 2+ keywords Tibia, aceita direto
    if palavras_encontradas >= 2:
        return True
    
    # Se tem nomes proprios (palavras com inicial maiuscula), pode ser lore valida
    import re
    nomes = re.findall(r'\b[A-Z][a-z]{2,}\b', texto)
    if len(nomes) >= 3:
        return True
    
    # Se tem estrutura de lore (HISTORIA:, PERSONALIDADE:, etc.)
    if any(m in texto for m in ["HISTORIA:", "PERSONALIDADE:", "ORIGEM:", "PODER:", "APARENCIA:"]):
        return True
    
    # Se tem numeros de linha (LINHA X:)
    if re.search(r'LINHA\s+\d+', texto):
        return True
    
    # Duvidoso: chama AI como fallback
    try:
        val = _fast(
            f"Texto: {texto[:400]}\n\nEsse texto e sobre Tibia/OTServ? (apenas SIM ou NAO):",
            0.1, "leve"
        ) or "SIM"
        if 'NAO' in val.upper() and 'SIM' not in val.upper():
            return False
        return True
    except:
        # Se AI falhar, aceita (falso positivo > falso negativo)
        return True

# ============================================================
# GERADOR DE CONTEXTO ENRIQUECIDO (FAST gera snippet)
# ============================================================
def _gerar_contexto_snippet(intencao, params, consulta="", ctx_crew="", ctx_inf="", kg=""):
    """FAST gera um SNIPPET de contexto para INJETAR no template.
    Nao gera o prompt inteiro - so enriquece o template existente.
    """
    snippet_prompt = f"""Contexto do projeto: {ctx_crew[:600] or '(projeto MCR - Tibia/OTServ)'}
Historico: {ctx_inf[:300] or '(sessao nova)'}
KG: {kg[:400] or '(sem KG)'}

Intencao: {intencao}
Parametros: {json.dumps(params, ensure_ascii=False)[:300]}

Com base no contexto acima, gere UM PARAGRAFO de informacoes relevantes
que devem ser consideradas ao executar esta intencao.
Inclua nomes proprios, lugares, termos tecnicos se aplicavel.
Nao repita o obvio. Seja especifico.

Responda APENAS com o paragrafo, sem introducao ou comentarios."""
    
    resultado = _fast(snippet_prompt, 0.3, "leve")
    if not resultado or len(resultado) < 20:
        return ""
    return resultado.strip()[:1000]


# ============================================================
# METRICAS (para dashboard)
# ============================================================
_METRICAS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sandbox', '.mcr_metricas.json')
_METRICAS_LOCK = threading.Lock()

def _atualizar_metricas(resultado, intencao):
    """Atualiza metricas do orquestrador para dashboard."""
    try:
        with _METRICAS_LOCK:
            metricas = {"total_calls": 0, "erros": 0, "cache_hits": 0, "cache_misses": 0,
                       "tempo_medio": 0, "templates_usados": {}, "ultimas": []}
            if os.path.exists(_METRICAS_PATH):
                try:
                    with open(_METRICAS_PATH, 'r', encoding='utf-8') as f:
                        metricas = json.load(f)
                except:
                    pass
            
            metricas["total_calls"] = metricas.get("total_calls", 0) + 1
            if not resultado.get("sucesso", False):
                metricas["erros"] = metricas.get("erros", 0) + 1
            
            tempo = resultado.get("tempo", 0)
            total = metricas["total_calls"]
            metricas["tempo_medio"] = round(
                (metricas.get("tempo_medio", 0) * (total - 1) + tempo) / total, 1
            ) if total > 0 else tempo
            
            template = intencao
            templates = metricas.get("templates_usados", {})
            templates[template] = templates.get(template, 0) + 1
            metricas["templates_usados"] = templates
            
            ultimas = metricas.get("ultimas", [])
            ultimas.append({
                "ts": time.time(),
                "intencao": intencao,
                "tempo": tempo,
                "sucesso": resultado.get("sucesso", False),
                "tam": resultado.get("resposta_len", 0),
            })
            metricas["ultimas"] = ultimas[-50:]  # mantem ultimas 50
            
            with open(_METRICAS_PATH, 'w', encoding='utf-8') as f:
                json.dump(metricas, f, ensure_ascii=False, indent=2)
    except:
        pass

# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================
class Orquestrador:
    """Gera prompts usando templates fixos + contexto injetado via FAST."""

    def __init__(self, kg=None, ia=None, ctx_crew=None):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew

    def _obter_contexto(self, consulta=""):
        """Junta ContextCrew + ContextInfinity + KG."""
        ctx_crew_txt = ""
        ctx_inf_txt = ""
        kg_txt = ""

        if self.ctx_crew and consulta:
            try:
                ctx_crew_txt = self.ctx_crew.executar(consulta) or ""
            except:
                pass

        try:
            p = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             '..', '..', 'sandbox', '.mcr_conversa.jsonl')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    linhas = [json.loads(l).get('msg', '') for l in f.readlines()[-5:] if l.strip()]
                    ctx_inf_txt = '\n'.join(linhas)
        except:
            pass

        if self.kg and consulta:
            try:
                lessons = self.kg.buscar(consulta, max_r=5)
                kg_txt = '\n'.join(f"- {r.get('solucao', '')[:300]}" for r in lessons)
            except:
                pass

        return ctx_crew_txt[:1500], ctx_inf_txt[:500], kg_txt[:1000]

    def _selecionar_template(self, intencao, params):
        """Seleciona o template baseado na intencao + params."""
        # Intencoes especificas primeiro
        if intencao == "lore":
            tipo = params.get("tipo", "")
            template_key = f"lore_{tipo}"
            if template_key in _TEMPLATES:
                return template_key
            return "lore"
        
        if intencao.startswith("componentes_"):
            if intencao in _TEMPLATES:
                return intencao
            return f"componentes_{params.get('tipo', 'personagens')}"
        
        if intencao in _TEMPLATES:
            return intencao
        
        # Fallback: tenta match parcial
        for chave in _TEMPLATES:
            if intencao.startswith(chave) or chave.startswith(intencao):
                return chave
        
        return "lore"  # fallback universal

    def gerar_prompt(self, intencao, params=None, consulta=""):
        """Gera o prompt final: template + contexto injetado."""
        params = params or {}
        template_key = self._selecionar_template(intencao, params)
        template = _TEMPLATES.get(template_key, _TEMPLATES["lore"])
        
        # Tenta cache
        snippet_cacheado = _CACHE.get(intencao, params, consulta)
        
        if snippet_cacheado is not None:
            contexto_extra = snippet_cacheado
        else:
            # Gera snippet de contexto via FAST
            ctx_crew, ctx_inf, kg = self._obter_contexto(consulta or str(params)[:100])
            
            # Tenta gerar snippet enriquecido
            snippet = _gerar_contexto_snippet(intencao, params, consulta, ctx_crew, ctx_inf, kg)
            
            if snippet:
                contexto_extra = snippet
                _CACHE.set(intencao, params, consulta, snippet)
            else:
                # Tier 3: template puro (igual ao original)
                contexto_extra = ""
        
        # Formata o template com contexto
        prompt = template.format(
            **params,
            contexto_extra=contexto_extra
        )
        
        router = _ROUTER.get(template_key, _ROUTER.get(intencao, _ROUTER["default"]))
        
        return prompt.strip()[:4000], router

    def executar(self, intencao, params=None, consulta="", temp=0.4):
        """Executa do inicio ao fim: template -> contexto -> modelo -> validacao."""
        import re as _re
        t0 = time.time()
        params = params or {}

        print(f'[Orquestrador] Executando: {intencao} | params: {str(params)[:80]}')
        
        # 1. Gera prompt do template + contexto
        prompt, router = self.gerar_prompt(intencao, params, consulta)
        if not prompt:
            print(f'  [Orquestrador] Prompt vazio - fallback ao template puro')
            template_key = self._selecionar_template(intencao, params)
            template = _TEMPLATES.get(template_key, _TEMPLATES["lore"])
            prompt = template.format(**params, contexto_extra="")
            router = _ROUTER.get(template_key, _ROUTER["default"])

        print(f'  [Orquestrador] Prompt ({len(prompt)} chars) | router: {router}')

        # 2. Executa com o modelo
        try:
            resposta = _gerar(prompt, temp, router) or _fast(prompt, temp, router) or ""
        except Exception as e:
            print(f'  [Orquestrador] ERRO na geracao: {e}')
            return {"sucesso": False, "erro": str(e), "tempo": round(time.time() - t0, 1)}

        # 3. Validacao
        valido = _validar_conteudo(resposta)
        if not valido:
            print(f'  [Orquestrador] Validacao: conteudo rejeitado')
            resposta = "(conteudo rejeitado pela validacao)"

        # 4. Metricas
        nomes = len(set(_re.findall(r'\b[A-Z][a-z]{2,}\b', resposta))) if resposta else 0

        resultado = {
            "sucesso": bool(resposta) and valido,
            "resposta": resposta,
            "router": router,
            "prompt_len": len(prompt),
            "resposta_len": len(resposta),
            "nomes_proprios": nomes,
            "tempo": round(time.time() - t0, 1),
            "template": self._selecionar_template(intencao, params),
        }
        print(f'  [Orquestrador] OK ({resultado["tempo"]}s) {resultado["resposta_len"]} chars, {nomes} nomes')

        # 5. Atualiza metricas para dashboard
        _atualizar_metricas(resultado, intencao)
        
        return resultado
