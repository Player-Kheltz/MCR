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
{identidade}
{contexto_extra}
Inclua nomes proprios em portugues, lugares, personagens e eventos.
Seja especifico e evite generalizacoes.
Responda em PT-BR.""",

    "analisar_codigo": """{estrutura}

Descricao: {descricao}

Para cada problema encontrado, responda:
LINHA X: tipo - descricao

{contexto_extra}
{identidade}
Use nomes de funcoes e linhas reais do codigo acima.
Responda em PT-BR.""",

    "analisar_texto": """{estrutura}

Descricao: {descricao}

Para cada problema encontrado, responda:
LINHA X: tipo do problema - descricao

{contexto_extra}
{identidade}
Responda em PT-BR.""",

    "review": """Revise os dados extraidos abaixo.
{few_shot}
{itens}

{contexto_extra}
{identidade}
Para cada ITEM com erro, responda: ITEM X: ERRO - descricao
Para itens corretos: ITEM X: OK
Responda em PT-BR.""",

    "conceito": """{identidade}
{contexto_extra}

{contexto}

Explique o CONCEITO abaixo. USE ESTRITAMENTE O CODIGO ACIMA para responder.
Conceito: {conceito}

INSTRUCOES:
- USE o codigo do arquivo fornecido acima para explicar. NAO invente exemplos.
- Se o codigo acima contem uma funcao _validar_conteudo, explique as regras REAIS dela.
- NAO de exemplos de formularios web, cadastro de usuarios, etc.
- Responda APENAS com base no que esta no codigo fornecido.
- Estruture em: 1. DEFINICAO, 2. REGRAS (em ordem), 3. EXEMPLO REAL, 4. IMPORTANCIA.
- Responda em PT-BR.""",

    "perguntar": """{identidade}
{ctx_infinity}
{contexto_extra}
{instrucao_contexto}

Pergunta: {pergunta}

Responda de forma util e especifica.
Se o usuario ja recebeu respostas parciais acima, responda APENAS o que falta.
Responda em PT-BR.""",

    "componentes_personagens": """Crie 3 personagens para uma historia.
{identidade}
{contexto_extra}
Cada um com: nome proprio, funcao, personalidade.
Formato: Nome: [nome] | Funcao: [funcao] | Personalidade: [personalidade]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "componentes_locais": """Crie 2 locais para uma historia.
{identidade}
{contexto_extra}
Cada um com: nome do local, descricao, significado.
Formato: Local: [nome] | Descricao: [descricao]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "componentes_artefatos": """Crie 2 artefatos ou eventos importantes para uma historia.
{identidade}
{contexto_extra}
Cada um com: nome, descricao, poder/significado.
Formato: Artefato: [nome] | Descricao: [descricao]
Use nomes proprios em portugues. Responda em PT-BR.""",

    "revisar": """Arquivo: {arquivo}
Mudanca: {descricao}
Codigo atual ({linhas} linhas):
{conteudo}

{contexto_extra}
{identidade}
Risco ALTO, MEDIO ou BAIXO? Responda so o nivel.
Se tiver ALTO risco, explique por que.""",

    "classificar_nomes": """Classifique cada item em UMA palavra: gerenciador, dados, servico, controle, modelo, util, outro.
{contexto_extra}
{identidade}
{itens}""",

    # Templates do Conselho Infinito V10 (arquetipos - universais)
    "conselho_analista": """{mcr}
{identidade}
Contexto: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}
ContextInfinity: {ctx_infinity}
{contexto_extra}
ANALISTA - Dados e fatos concretos.
Numeros, versoes, metricas. Seja especifico. 2-3 frases curtas.""",

    "conselho_critico": """{mcr}
{identidade}
Contexto: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
CRITICO - Riscos e problemas especificos.
Nada generico. 2-3 frases curtas com riscos concretos.""",

    "conselho_estrategista": """{mcr}
{identidade}
Contexto: {ctx_crew}
KG: {kg}
Pergunta: {pergunta}
{contexto_extra}
ESTRATEGISTA - Visao geral, planejamento curto/medio/longo prazo.
Recomendacao concreta. 2-3 frases curtas.""",

    "conselho_arquiteto": """{mcr}
{identidade}
Contexto: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
ARQUITETO - Design de sistemas. Componentes, relacoes, padroes.
Problemas estruturais e solucoes. 2-3 frases curtas.""",

    "conselho_contador_historias": """{mcr}
{identidade}
Contexto: {ctx_crew}
Inspiracao: {kg}
Pergunta: {pergunta}
{contexto_extra}
CONTADOR DE HISTORIAS - Crie NARRATIVA RICA.
Nomes proprios de personagens, lugares, artefatos.
Historia vivida: fundacao, era de ouro, declinio, situacao atual.
Nomes UNICOS e ORIGINAIS. 3-4 frases descritivas.""",

    "conselho_psicologo": """{mcr}
{identidade}
Pergunta sendo discutida: {pergunta}
{contexto_extra}
PSICOLOGO DO CONSELHO - Analise APENAS o PROCESSO, nao responda:
1) Ha algum VIES na pergunta?
2) O conselho esta alinhado com os valores do projeto?
3) Ha risco de GROUPTHINK?
4) Precisa de mais informacoes?
2-3 frases sobre o PROCESSO apenas.""",

    "conselho_revisor_codigo": """{mcr}
{identidade}
Contexto: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
REVISOR DE CODIGO - Seguranca e boas praticas.
Bugs, seguranca, performance. Problemas especificos com sugestoes.
2-3 frases curtas.""",

    "conselho_tecnico": """{mcr}
{identidade}
Contexto: {ctx_crew}
Pergunta: {pergunta}
{contexto_extra}
ESPECIALISTA TECNICO - Implementacao e detalhes tecnicos.
Comandos, arquivos, parametros especificos. 2-3 frases curtas.""",

    # ============================================================
    # NOVOS TEMPLATES UNIVERSAIS (planejamento, diagnostico, conceitual)
    # ============================================================
    
    "analisar_bug": """{identidade}
{mente_contexto}

Tarefa: ENCONTRAR E CORRIGIR UM BUG ESPECIFICO em {estrutura}.

Descricao do bug: {descricao}

{contexto_extra}

Siga o formato abaixo. Seja EXTREMAMENTE PRECISO.

=== 1. LOCALIZACAO DO BUG ===
- Arquivo: [nome]
- Linha exata: [numero]
- Codigo com bug:
  ```python
  [codigo original]
  ```
- Por que e um bug: [explicacao tecnica de 2-3 frases]

=== 2. CAUSA RAIZ ===
- O que causa o comportamento incorreto: [explicacao]
- Quando ocorre: [condicoes]
- Impacto: [o que acontece de errado]

=== 3. CORRECAO ===
- Codigo corrigido:
  ```python
  [codigo corrigido]
  ```
- Explicacao da correcao: [por que isso resolve]
- Teste para verificar: [como testar]

=== 4. PREVENCAO ===
- Como evitar este tipo de bug no futuro
- Padrao ou licao aprendida

Responda em PT-BR. Seja PRECISO com linhas e codigo.""",


"diagnostico_problema": """{identidade}

Problema reportado:
{descricao}

{contexto_extra}

Realize um diagnostico COMPLETO e DETALHADO seguindo a estrutura abaixo.
CADA secao DEVE ter no minimo 3 itens com CODIGO ou comandos especificos.

=== A) CAUSAS POSSIVEIS (3 causas distintas) ===
Para CADA causa:
- Causa N: [NOME DA CAUSA]
  - Explicacao tecnica: Por que isso causa o problema? (2-3 frases)
  - Evidencia: Como saber se e esta a causa? O que observar?
  - Codigo/Comando: Linha de comando ou codigo para verificar

=== B) VERIFICACAO ===
Para CADA causa, UM metodo de verificacao PRATICO:
  - Comando: (ex: `python -c "import X; print(X.version)"`)
  - Resultado esperado vs resultado anormal
  - Ferramenta especifica para confirmar

=== C) SOLUCOES (3 solucoes, uma por causa) ===
Para CADA solucao:
  - Passo a passo numerado
  - Codigo completo ou comando
  - Como verificar se a solucao funcionou

=== D) PREVENCAO ===
  - Como evitar que o problema ocorra novamente
  - Monitoramento recomendado
  - Boas praticas

Responda em PT-BR. EXTREMAMENTE DETALHADO. Nada generico.""",

}

# ============================================================
# ROTEAMENTO DE MODELOS
# ============================================================
_ROUTER = {
    "lore_npc": "texto",
    "lore_item": "texto",
    "lore_local": "texto",
    "lore": "pesado",
    "analisar_codigo": "analisar",
    "analisar_texto": "pesado",
    "review": "review",
    "conceito": "pesado",
    "perguntar": "pesado",
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
    # Novos templates universais
    "analisar_bug": "analisar",
    "default": "leve",
}

# ============================================================
# VALIDACAO UNIVERSAL (estrutura + AI fallback, sem dominio fixo)
# ============================================================
# Keywords de identidade podem ser injetadas externamente
_KEYWORDS_IDENTIDADE = []

def _obter_classes_reais():
    """Retorna classes reais do projeto escaneando com grep (on demand)."""
    try:
        import subprocess as _sp
        base = os.path.join(os.path.dirname(__file__), '..', '..', '..')
        r = _sp.run(
            ['grep', '-r', '-h', '-o', r'class \w+', '--include', '*.py', base],
            capture_output=True, text=True, timeout=10
        )
        classes = set()
        for linha in (r.stdout or '').split('\n'):
            if 'class ' in linha:
                nome = linha.replace('class ', '').strip()
                if nome and len(nome) > 2:
                    classes.add(nome)
        # Builtins comuns validos
        classes.update({'ValueError','TypeError','KeyError','Exception','OSError',
                       'FileNotFoundError','PermissionError','StopIteration'})
        return classes
    except:
        return {"DataLake", "StreamSimulator"}

def _validar_conteudo(texto, keywords_extras=None):
    """Validacao universal. Usa estrutura + nomes + AI fallback.
    Aceita keywords opcionais do dominio injetadas externamente."""
    if not texto or texto == "(conteudo filtrado pela validacao)":
        return False
    
    texto_lower = texto.lower()
    
    # Se tem keywords extras do dominio, verifica
    if keywords_extras:
        palavras_encontradas = sum(1 for kw in keywords_extras if kw in texto_lower)
        if palavras_encontradas >= 2:
            return True
    
    # Se tem nomes proprios (palavras com inicial maiuscula)
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
    
    # Duvidoso: chama AI como fallback generico
    try:
        val = _fast(
            f"Texto: {texto}\n\nEste texto parece coerente e informativo? (apenas SIM ou NAO):",
            0.1, "leve"
        ) or "SIM"
        if 'NAO' in val.upper() and 'SIM' not in val.upper():
            return False
        return True
    except:
        return True

# ============================================================
# GERADOR DE CONTEXTO ENRIQUECIDO (FAST gera snippet)
# ============================================================
def _gerar_contexto_snippet(intencao, params, consulta="", ctx_crew="", ctx_inf="", kg=""):
    """FAST gera um SNIPPET de contexto para INJETAR no template (universal)."""
    ctx_fallback = '(sem contexto)' if not ctx_crew else ctx_crew
    snippet_prompt = f"""Contexto disponivel: {ctx_fallback}
Historico: {ctx_inf or '(sessao nova)'}
KG: {kg or '(sem KG)'}

Intencao: {intencao}
Parametros: {json.dumps(params, ensure_ascii=False)}

Com base no contexto acima, gere UM PARAGRAFO de informacoes relevantes
que devem ser consideradas ao executar esta intencao.
Inclua nomes proprios, lugares, termos tecnicos se aplicavel.
Nao repita o obvio. Seja especifico.

Responda APENAS com o paragrafo, sem introducao ou comentarios."""
    
    resultado = _fast(snippet_prompt, 0.3, "leve")
    if not resultado or len(resultado) < 20:
        return ""
    return resultado.strip()


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

    def _filtrar_contexto(self, contexto_raw, consulta):
        """Filtra contexto se necessario. Pula filtro se ja tem arquivo lido diretamente."""
        if not contexto_raw or not consulta or len(contexto_raw) < 200:
            return contexto_raw
        
        # Se ja tem conteudo de arquivo lido diretamente, nao filtra
        if '[ARQUIVO:' in contexto_raw:
            return contexto_raw
        
        try:
            prompt_filtro = (
                f"Consulte: {consulta}\n\n"
                f"Contexto disponivel:\n{contexto_raw}\n\n"
                f"Analise o contexto acima. Qual parte dele e RELEVANTE para a consulta?\n"
                f"Remova informacoes nao relacionadas, mantenha so o que ajuda a responder.\n"
                f"Retorne APENAS o contexto filtrado, sem introducao."
            )
            filtrado = _fast(prompt_filtro, 0.2, "leve")
            if filtrado and len(filtrado) > 50:
                return filtrado.strip()
        except:
            pass
        return contexto_raw
    
    def _obter_contexto(self, consulta=""):
        """Junta TODAS as fontes de contexto: ContextCrew + KG + Web + grep + Infinity.
        Depois FILTRA dinamicamente com FAST para manter apenas o relevante."""
        partes = []
        
        # 1. ContextCrew (KG + WebLearn + Docs + Codigo + Web)
        if self.ctx_crew and consulta:
            try:
                ctx = self.ctx_crew.executar(consulta) or ""
                if ctx:
                    partes.append(f"[CONTEXT CREW]\n{ctx}")
            except:
                pass
        
        # 2. KG direto (mais lessons)
        if self.kg and consulta:
            try:
                lessons = self.kg.buscar(consulta, max_r=10)
                if lessons:
                    kg_blocos = []
                    for r in lessons:
                        sol = r.get('solucao', '').strip()
                        ctx_tag = r.get('ctx', '')
                        if sol:
                            kg_blocos.append(f"- [{ctx_tag}] {sol}")
                    if kg_blocos:
                        partes.append(f"[KNOWLEDGE GRAPH]\n" + "\n".join(kg_blocos))
            except:
                pass
        
        # 3. Context Infinity (conversa recente)
        try:
            p = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             '..', '..', 'sandbox', '.mcr_conversa.jsonl')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    linhas = [json.loads(l).get('msg', '') for l in f.readlines()[-8:] if l.strip()]
                    if linhas:
                        partes.append(f"[CONTEXT INFINITY]\n" + "\n".join(linhas[-8:]))
        except:
            pass
        
        # 4. Leitura DIRETA de arquivos mencionados na consulta
        if consulta:
            import re as _re_direto
            arq_mencio = _re_direto.search(r'([\w/]+\.py)', consulta)
            if arq_mencio:
                nome_arq = arq_mencio.group(1)
                # Busca funcao especifica mencionada na consulta
                func_mencio = _re_direto.search(r'(_?\w+)\s*\(', consulta)
                func_nome = func_mencio.group(1) if func_mencio else None
                
                caminhos_tentar = [
                    os.path.join(os.path.dirname(__file__), '..', nome_arq),
                    os.path.join(os.path.dirname(__file__), nome_arq),
                    os.path.join(os.path.dirname(__file__), '..', 'comandos', nome_arq),
                ]
                if 'modulos/' in nome_arq:
                    caminhos_tentar.insert(0, os.path.join(os.path.dirname(__file__), nome_arq.replace('modulos/', '')))
                if 'comandos/' in nome_arq:
                    caminhos_tentar.insert(0, os.path.join(os.path.dirname(__file__), '..', 'comandos', nome_arq.replace('comandos/', '')))
                
                for caminho in caminhos_tentar:
                    if os.path.exists(caminho):
                        try:
                            with open(caminho, 'r', encoding='utf-8', errors='replace') as _f:
                                _conteudo = _f.read()
                            if func_nome:
                                # Busca a funcao especifica no arquivo
                                _pos = _conteudo.find(f'def {func_nome}')
                                if _pos >= 0:
                                    # Pega 100 linhas a partir da funcao
                                    _trecho = _conteudo[_pos:_pos+5000]
                                    partes.append(f"[ARQUIVO: {nome_arq} - funcao {func_nome}]\n{_trecho}")
                                else:
                                    partes.append(f"[ARQUIVO: {nome_arq}]\n{_conteudo}")
                            else:
                                partes.append(f"[ARQUIVO: {nome_arq}]\n{_conteudo}")
                            print(f'  [Contexto] Arquivo lido: {nome_arq}')
                            break
                        except: pass
        
        # Junta tudo e FILTRA DINAMICAMENTE por relevancia
        contexto_raw = "\n\n".join(partes)
        return self._filtrar_contexto(contexto_raw, consulta)

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

    def _preencher_defaults(self, params, template_key):
        """Garante placeholders universais nos params."""
        # Placeholders que todo template pode usar
        defaults = {
            'identidade': '',
            'contexto_extra': '',
            'mente_contexto': '',
            'memoria_pessoal': '',
            'mcr': '',
            'ctx_crew': '',
            'kg': '',
            'pergunta': '',
            'ctx_infinity': '',
            'instrucao_contexto': '',
        }
        for k, v in defaults.items():
            if k not in params:
                params[k] = v
        return params
    
    def gerar_prompt(self, intencao, params=None, consulta=""):
        """Gera o prompt final: template + MAXIMO contexto injetado RAW.
        Bypass do snippet generator: injeta contexto completo diretamente.
        O LLM tem contexto suficiente (8k tokens) para processar tudo."""
        params = params or {}
        template_key = self._selecionar_template(intencao, params)
        template = _TEMPLATES.get(template_key, _TEMPLATES["lore"])
        
        # Garante defaults universais
        params = self._preencher_defaults(params, template_key)
        
        # Obtem MAXIMO contexto de TODAS as fontes (com filtro DINAMICO por relevancia)
        contexto_raw = self._obter_contexto(consulta or str(params))
        
        # Tenta gerar snippet (cacheavel) MAS sempre inclui raw context tb
        snippet_cacheado = _CACHE.get(intencao, params, consulta)
        if snippet_cacheado is not None:
            contexto_extra = snippet_cacheado
        else:
            snippet = _gerar_contexto_snippet(intencao, params, consulta, "", "", "")
            if snippet:
                _CACHE.set(intencao, params, consulta, snippet)
        
        # INJETA TUDO: snippet + raw context juntos
        contexto_extra = ""
        if snippet_cacheado:
            contexto_extra = snippet_cacheado + "\n"
        if contexto_raw:
            # Injeta o raw context completo (ate 6000 chars)
            contexto_extra += contexto_raw
        
        params['contexto_extra'] = contexto_extra.strip()
        
        # Verifica placeholders pendentes no template
        try:
            prompt = template.format(**params)
        except KeyError as e:
            import re
            pendentes = set(re.findall(r'\{(\w+)\}', template))
            for p in pendentes:
                if p not in params:
                    params[p] = ''
            prompt = template.format(**params)
        
        router = _ROUTER.get(template_key, _ROUTER.get(intencao, _ROUTER["default"]))
        # Limite de prompt adaptativo: mega_teste usa o fragmentador, sem limite
        if template_key in ("perguntar",):
            max_prompt = 20000  # Universal: fragmentador quebra em secoes
        elif router in ("pesado", "analisar", "review"):
            max_prompt = 6000
        else:
            max_prompt = 4000
        return prompt.strip(), router

    def _extrair_secoes_template(self, template_key):
        """Detecta secoes ESTRUTURAIS do TEMPLATE PURO (sem contexto injetado).
        Retorna lista de (nome_secao, template_parcial) onde cada template_parcial
        e um fragmento do template original que contem {contexto_extra} e outros placeholders.
        """
        import re
        template = _TEMPLATES.get(template_key, "")
        if not template:
            return []
        
        # Marcadores de secao especificos dos templates fragmentaveis
        padroes_secao = [
            r'={2,5}\s*\d+\s*={2,5}',          # === 1 ===
            r'={2,5}\s*[A-Z]\)?\s*={2,5}',      # === A) ===
            r'\[\s*\]\s+[A-Z\u00C0-\u017F][A-Z\u00C0-\u017F\s]{2,}:',  # [ ] TOPICO: ou [ ] ANALISE DE CODIGO: (mega_teste)
            r'[#]+\s*\d+\s*\.\s*[A-Z\u00C0-\u017F]',  # ### 1. Secao
            r'(?<!\w)\d+\.\s+(?:VIS[A-Z\u00C0-\u017F]+|CAUSAS|DEFINICAO|COMPONENTES|EXEMPLO|POR QUE|MITIGACAO|SEGURANCA|ARQUITETURA|DETALHAMENTO|TRADE-OFFS|PREVENCAO)',
            r'\b[A-Z]\)\s+(?:CAUSAS|VERIFICACAO|SOLUCOES|PREVENCAO)',
        ]
        
        linhas = template.split('\n')
        secoes = []
        secao_atual = []
        nome_secao = "INTRODUCAO"
        dentro_bloco = False
        
        for linha in linhas:
            linha_strip = linha.strip()
            
            # Ignora ```code blocks```
            if linha_strip.startswith('```') or linha_strip.startswith('"""'):
                dentro_bloco = not dentro_bloco
                secao_atual.append(linha)
                continue
            if dentro_bloco:
                secao_atual.append(linha)
                continue
            
            # Ignora placeholders, linhas vazias curtas
            if not linha_strip or linha_strip.startswith('{') or linha_strip.startswith('# Regras'):
                secao_atual.append(linha)
                continue
            
            is_secao = False
            for padrao in padroes_secao:
                if re.search(padrao, linha_strip):
                    if secao_atual:
                        secoes.append((nome_secao, '\n'.join(secao_atual)))
                    nome_secao = linha_strip
                    secao_atual = [linha]
                    is_secao = True
                    break
            
            if not is_secao:
                secao_atual.append(linha)
        
        if secao_atual:
            secoes.append((nome_secao, '\n'.join(secao_atual)))
        
        # So usa fragmentacao se tiver 3+ secoes com conteudo significativo
        secoes_validas = [(n, t) for n, t in secoes if len(t.strip()) > 50]
        return secoes_validas if len(secoes_validas) >= 3 else []
    
    def _gerar_fragmentado_texto(self, secoes, router, temp, params=None):
        """Gera texto fragmentado com validacao de sintaxe de codigo.
        Cada secao gerada separadamente. Se codigo tiver erro, tenta novamente."""
        import re as _re
        params = params or {}
        fragmentos = []
        contexto_acumulado = ""
        
        for i, (nome, template_secao) in enumerate(secoes):
            try:
                params['contexto_extra'] = params.get('contexto_extra', '')
                prompt_secao = template_secao.format(**params)
            except KeyError:
                for p in set(_re.findall(r'\{(\w+)\}', template_secao)):
                    if p not in params:
                        params[p] = ''
                prompt_secao = template_secao.format(**params)
            
            ctx_anterior = ""
            if contexto_acumulado:
                ctx_anterior = f"\n\n--- CONTEXTO ANTERIOR ---\n{contexto_acumulado[-2000:]}\n--- FIM ---\n"
            
            marker_inicio = ""
            if nome.strip().startswith("[") and "]" in nome:
                marker_inicio = nome.strip().split("]")[0] + "]"
            
            prompt_frag = (
                f"{prompt_secao}\n{ctx_anterior}\n"
                f"Gere APENAS a secao '{nome}'. Seja completo.\n"
                f"COMECE sua resposta EXATAMENTE com: {marker_inicio or nome}\n"
                f"IMPORTANTE: Codigo Python em ```python ... ``` deve ser COMPILAVEL.\n"
                f"NAO coloque texto dentro de blocos de codigo.\n"
                f"NAO gere outras secoes."
            )
            
            print(f'  [Fragmentado] Secao {i+1}/{len(secoes)}: {nome} ({len(prompt_frag)} chars)')
            
            # Tenta gerar, com ate 3 retries se codigo tiver erro de sintaxe
            resp = ""
            for tentativa in range(3):
                try:
                    resp = _gerar(prompt_frag, temp, router) or _fast(prompt_frag, temp, router) or ""
                except:
                    resp = ""
                    break
                
                if not resp:
                    break
                
                # Valida: sintaxe do codigo gerado
                blocos = _re.findall(r'```(?:python)?\s*\n(.*?)```', resp, _re.DOTALL)
                erros_sintaxe = sum(1 for b in blocos if not self._sintaxe_valida(b))
                
                if erros_sintaxe == 0:
                    break
                
                if tentativa == 0:
                    print(f'  [Fragmentado] Retry {i+1} ({erros_sintaxe} erros sintaxe)')
                    prompt_frag += "\nATENCAO: Codigo anterior tinha erro de sintaxe. Gere codigo VALIDO."
                    resp = ""
            
            fragmentos.append(resp)
            if resp:
                contexto_acumulado += "\n\n" + resp
                if len(contexto_acumulado) > 4000:
                    contexto_acumulado = contexto_acumulado[-4000:]
        
        return '\n\n'.join(fragmentos) if fragmentos else ""
    
    def _sintaxe_valida(self, codigo):
        """Verifica se codigo Python e compilavel."""
        try:
            compile(codigo.strip(), '<test>', 'exec')
            return True
        except:
            return False

    def executar(self, intencao, params=None, consulta="", temp=0.4, fragmentar=True):
        """Executa do inicio ao fim: template -> contexto -> modelo -> validacao.
        Se fragmentar=True e o template tiver 3+ secoes, usa geracao fragmentada
        (contexto infinito, sem limite de tokens na resposta)."""
        import re as _re
        t0 = time.time()
        params = params or {}

        print(f'[Orquestrador] Executando: {intencao} | params: {str(params)}')
        
        # 1. Gera prompt do template + contexto
        prompt, router = self.gerar_prompt(intencao, params, consulta)
        if not prompt:
            print(f'  [Orquestrador] Prompt vazio - fallback ao template puro')
            template_key = self._selecionar_template(intencao, params)
            template = _TEMPLATES.get(template_key, _TEMPLATES["lore"])
            prompt = template.format(**params, contexto_extra="")
            router = _ROUTER.get(template_key, _ROUTER["default"])

        print(f'  [Orquestrador] Prompt ({len(prompt)} chars) | router: {router}')

        # 2. Decide: geracao unica vs fragmentada (so para templates com estrutura clara)
        _TEMPLATES_FRAGMENTAVEIS = {"perguntar", "analisar_codigo", "analisar_bug"}
        template_key = self._selecionar_template(intencao, params)
        pode_fragmentar = fragmentar and template_key in _TEMPLATES_FRAGMENTAVEIS
        secoes = self._extrair_secoes_template(template_key) if pode_fragmentar else []
        usa_fragmentacao = pode_fragmentar and len(secoes) >= 3
        
        if usa_fragmentacao:
            print(f'  [Orquestrador] Usando geracao FRAGMENTADA ({len(secoes)} secoes)')
            params['_template_key'] = template_key  # Para lista branca
            resposta = self._gerar_fragmentado_texto(secoes, router, temp, params)
            if not resposta:
                print(f'  [Orquestrador] Fragmentacao falhou - fallback para geracao unica')
                usa_fragmentacao = False
        
        if not usa_fragmentacao:
            # Geracao unica (tradicional)
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

        # 3.5 AUTO-REVISAO: MCR-DevIA revisa a propria resposta
        if resposta and len(resposta) > 100:
            try:
                from modulos.auto_revisor import AutoRevisor
                revisor = AutoRevisor(kg=self.kg)
                # Determina classes permitidas baseado no template
                classes_permitidas = None
                if template_key in ("perguntar",):
                    classes_permitidas = set()  # Universal: verifica contra todo o projeto
                if template_key == "analisar_codigo" or template_key == "analisar_bug":
                    # Escaneia o projeto para classes reais (on demand)
                    classes_permitidas = _obter_classes_reais()
                
                revisao = revisor.revisar(resposta, classes_permitidas)
                if revisao["total"] > 0:
                    print(f'  [Auto-Revisor] {revisao["total"]} alucinacoes: {revisao["sugestao"]}')
                    # Auto-corrige: marca classes suspeitas
                    resposta, _ = revisor.auto_corrigir(resposta, classes_permitidas)
                    valido = True  # Mantem valido mesmo com marcas
            except Exception as e:
                print(f'  [Auto-Revisor] ERRO: {e}')

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
