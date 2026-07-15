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
from mcr.util import gerar as _gerar, fast as _fast
from mcr.tradutor import traduzir as _traduzir
from modulos import memoria_conselho as _memoria  # Memoria individual por membro
from mcr.decider import Decider  # G1, G6, G7
from mcr.ia import IA

# Orquestrador (template engine) — opcional, legado movido para /Legado
_Orquestrador = None
_ORQ_TEMPLATES = {}
try:
    from mcr.orquestrador import Orquestrador as _Orquestrador, _TEMPLATES as _ORQ_TEMPLATES
except ImportError:
    pass

_MCR_IDENTITY = """CONTEXTO DO PROJETO MCR (leia antes de responder):
- MCR = Projeto MCR, um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)
- SPA = Sistema de Progressao do Aventureiro para evolucao em dominios elementais
- SHC = Sistema de Habilidades Contextuais (5 camadas)
- Canary = Servidor de Tibia personalizado (OTServ) usado no MCR
- OTClient = Cliente customizado de Tibia usado com o servidor
- Dominios = areas de conhecimento do SPA: Fogo, Gelo, Terra, Energia
- Eridanus = Cidade inicial do projeto MCR, ponto de partida dos aventureiros
- Projeto MCR = servidor customizado de Tibia, parte da comunidade OTServ"""

# Router: mapeia cada arquétipo ao melhor modelo para aquela tarefa
_ROUTER = {
    "analista": "leve",             # qwen2.5-coder (rapido, dados)
    "critico": "analisar",          # deepseek-r1 (analise profunda)
    "estrategista": "pesado",       # qwen2.5-coder (completo)
    "arquiteto": "pesado",          # qwen2.5-coder (completo)
    "contador_historias": "texto",  # llama3.1 (PT-BR natural)
    "revisor_codigo": "review",     # deepseek-r1 (codigo, raw:False)
    "psicologo": "texto",           # llama3.1 (PT-BR natural)
    "tecnico": "code",              # qwen2.5-coder (codigo)
    "especialista": "pesado",       # qwen2.5-coder (completo)
    "criativo": "leve",             # qwen2.5-coder (rapido, temp alta para criatividade)
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
# G1 — TREE OF THOUGHT (fundido do enricher.py)
# ============================================================
_CAMINHOS_TOT = {
    "analitico": "Pense como um ANALISTA. Foque em dados, fatos, numeros, versoes, metricas e detalhes tecnicos. Seja especifico e preciso.",
    "criativo": "Pense como um CONTADOR DE HISTORIAS. Use exemplos concretos, analogias, cenarios praticos e aplicacoes reais.",
    "critico": "Pense como um CRITICO. Questione suposicoes, aponte limitacoes, riscos, pontos cegos. Nao aceite nada pelo valor nominal.",
    "filosofico": "Pense como um FILOSOFO. Busque a essencia do problema. Qual o padrao universal? O que emerge quando isolamos as variaveis? Qual o eixo entre Nirvana e Caos? Nao se contente com a superficie.",  # NOVO
    "pragmatico": "Pense como um PRAGMATICO. O que funciona na pratica? Qual a acao mais simples que resolve? Ignore teoria, foque no resultado concreto.",  # NOVO
}

def tree_of_thought(ia, prompt_base):
    """Gera 3 perspectivas (analitico, criativo, critico) e sintetiza.
    
    [Conselho 2.0] Usa FAST em vez de 14b — contexto externo compensa.
    """
    perspectivas = {}
    for nome, instrucao in _CAMINHOS_TOT.items():
        prompt = f"{instrucao}\n\nResponda EXATAMENTE a pergunta abaixo:\n{prompt_base}"
        resp = ia.fast(prompt, 0.3, 'leve')  # FAST em vez de 14b
        if resp:
            perspectivas[nome] = resp.strip()
    if len(perspectivas) < 2:
        return prompt_base
    prompt_sintese = (
        f"Perspectiva ANALITICA:\n{perspectivas.get('analitico', '')}\n"
        f"Perspectiva CRIATIVA:\n{perspectivas.get('criativo', '')}\n"
        f"Perspectiva CRITICA:\n{perspectivas.get('critico', '')}\n"
        f"Sintetize em resposta UNICA, focando na pergunta original."
    )
    sintese = ia.fast(prompt_sintese, 0.3, 'leve')  # FAST em vez de 14b
    return sintese or prompt_base


# ============================================================
# G5 — PROMPT CACHE LRU (re-export de orquestrador.py)
# ============================================================
from mcr.modules.orquestrador import PromptCache


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
        detect = _fast(
            f"{_MCR_IDENTITY}\n\n"
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
                    orq = _Orquestrador(kg=self.kg, ia=self.ia, ctx_crew=self.ctx_crew)
                    params = {
                        "mcr": _MCR_IDENTITY,
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
                prompt = prompt_t.format(
                    mcr=_MCR_IDENTITY,
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

        # 4. DEBATE PROTOCOL (opcional, refinamento)
        debate_ctx = ""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                            '..', '..', 'sandbox'))
            from debate_protocol import Debate
            def _gerar_debate(p, t=0.5):
                return _gerar(p, t, "conceito")
            d = Debate(f"{pergunta} | {ctx_crew_txt}", gerar=_gerar_debate)
            debate_result = d.executar(pergunta, rodadas=1)
            if debate_result and len(debate_result) > 50:
                debate_ctx = f"\n\nDebate (propositor + critico + conector):\n{debate_result}\n"
                print(f'  [Debate] Refinamento obtido ({len(debate_result)} chars)')
        except Exception as e:
            print(f'  [Debate] ERRO: {e}')

        # 5. VEREDITO FINAL
        db = f"{_MCR_IDENTITY}\n\n"
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
                f"{_MCR_IDENTITY}\n\n"
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
                    f"{_MCR_IDENTITY}\n\n"
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

        # 7. AUTO-REVISAO
        gaps = []
        nomes = len(set(_re.findall(r'\b[A-Z][a-z]{2,}\b', v)))
        if nomes < 8:
            gaps.append(f"Apenas {nomes} nomes proprios. Adicione mais detalhes.")
        if len(v) < 500:
            gaps.append("Resposta muito curta. Expanda.")

        avaliacao_generico = _fast(
            f"Texto: {v}\n\nEste texto e GENERICO (responda apenas SIM ou NAO):", 0.2, "leve") or ""
        if 'SIM' in avaliacao_generico.upper() and 'NAO' not in avaliacao_generico.upper():
            gaps.append("Conteudo generico.")

        if gaps:
            for g in gaps:
                print(f'  [Auto-revisao] Gap: {g}')
            v = _gerar(f"Melhore corrigindo:\n" + '\n'.join(f"- {g}" for g in gaps) +
                       f"\n\nTexto:\n{v}\n\nTexto MELHORADO (mais detalhado, especifico):",
                       0.4, "conceito") or v

        # 8. TRADUCAO PT-BR
        v_original = v
        v = _traduzir(v, temp=0.3)
        if not v or v == v_original:
            v = v_original
        else:
            print(f'  [Tradutor] Veredito traduzido para PT-BR ({len(v)} chars)')

        r = {
            "veredito": v,
            "opinioes": opinioes,
            "psicologo": avaliacao_psicologo,
            "tempo_total": round(time.time() - t0, 1),
            "honorarios_criados": arquetipos,
            "tipo": tipo,
            "nomes_proprios": nomes,
        }
        print(f'  [Veredito] ({r["tempo_total"]:.1f}s) {len(v)} chars, {nomes} nomes, '
              f'{len(opinioes)} arquetipos')
        return r
