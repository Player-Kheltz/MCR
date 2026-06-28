"""Enricher — Sistema de Enriquecimento Dinamico de Prompts.

Elimina respostas genericas combinando:
- G1: Tree of Thought (multiplas perspectivas)
- G2: Anti-alucinacao (validacao de termos reais)
- G3: MCR_Identity (contexto do projeto)
- G4: Traducao PT-BR (gera em ingles, traduz depois)
- G5: PromptCache LRU (evita regeneracao)
- G6: Validacao de relevancia (contexto util?)
- G7: Termos criticos (extracao melhorada)
- G8: Router de modelos (cada tipo usa melhor modelo)

Fluxo:
1. [G7] Extrair termos criticos da pergunta
2. [G5] Verificar PromptCache (se ja tem, reusa)
3. [G3] Injetar MCR_Identity + [G8] Router de modelos
4. AnalisadorDeContexto: FAST decide COMO enriquecer
5. ColetorDeContexto: Busca nas fontes certas
6. [G6] Validar se contexto coletado e relevante
7. [G1] TreeOfThought: 3 perspectivas + sintese
8. MontadorDePrompt: Gera o prompt enriquecido
9. [G2] Anti-alucinacao pos-geracao
10. [G4] Traducao PT-BR

Uso:
    enricher = Enricher(ia, kg, ctx_cache)
    prompt_final = enricher.enriquecer("O que e SessionCache no MCR?")
    resposta = ia.gerar(prompt_final, 0.4, 'pesado')
"""
import os, sys, json, re, time
from collections import OrderedDict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.decider import Decider
from modulos.ia import IA


# ============================================================
# G3 — MCR_IDENTITY (injetada em todo prompt enriquecido)
# ============================================================
_MCR_IDENTITY = """CONTEXTO DO PROJETO MCR (USE para responder):
- MCR = servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)
- SPA = Sistema de Progressao do Aventureiro
- SHC = Sistema de Habilidades Contextuais (5 camadas)
- SessionCache = cache de sessao que absorve tudo sem limite, pesca sob demanda
- MasterAgent = orquestrador universal que faz QUALQUER coisa
- Decider = classificador universal via FAST model
- KG = Knowledge Graph com 1937+ licoes aprendidas
- EpisodicMemory = memoria de experiencias com embeddings
- ToolOrchestrator = 22 ferramentas executaveis
- Validador Universal = valida codigo em 6 linguagens"""


# ============================================================
# G8 — ROUTER DE MODELOS (melhor modelo para cada tarefa)
# ============================================================
_ROUTER = {
    'conceito_local': 'pesado',
    'conceito_geral': 'texto',
    'codigo': 'code',
    'explicacao': 'texto',
    'analise': 'analisar',
    'lore': 'texto',
    'comparacao': 'pesado',
    'rapido': 'leve',
    'tutorial': 'texto',
}


# ============================================================
# G5 — PROMPT CACHE LRU
# ============================================================
class PromptCache:
    """Cache LRU de prompts enriquecidos."""
    
    def __init__(self, max_size=64):
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def get(self, pergunta):
        key = hash(pergunta) % 1000000
        return self._cache.get(key)
    
    def set(self, pergunta, prompt):
        key = hash(pergunta) % 1000000
        self._cache[key] = prompt
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
    
    def limpar(self):
        self._cache.clear()


# ============================================================
# G7 — TERMOS CRITICOS (extracao melhorada)
# ============================================================
def _extrair_termos_criticos(texto):
    """Extrai termos relevantes incluindo siglas e extensoes (.lua, .py)."""
    if not texto:
        return []
    # Extrai termos de 2+ chars, incluindo com pontos
    termos = re.findall(r'\b[a-zA-Z.]{2,}\b', texto.lower())
    stop = {'de','para','que','com','uma','era','mais','como','por',
            'seu','sua','tem','ela','ele','voce','me','te','se','nos',
            'lhe','das','dos','nas','nem','mas','sobre','isto','isso',
            'aquele','este','essa','em','no','na','um','uns','umas',
            'a','o','as','os','do','da','e'}
    return [t for t in termos if t not in stop][:15]


# ============================================================
# CLASSES PRINCIPAIS
# ============================================================

class AnalisadorDeContexto:
    """Analisa a pergunta e decide DINAMICAMENTE como enriquecer.
    
    [G7] Usa termos criticos como entrada
    """

    def __init__(self, ia=None):
        self.ia = ia or IA()
        self.decider = Decider(self.ia)

    def analisar(self, pergunta, termos_extraidos=None):
        """Retorna plano de enriquecimento para esta pergunta.
        
        Args:
            pergunta: Texto original
            termos_extraidos: Lista de termos do G7 (opcional)
        
        Returns:
            dict com tipo, fontes, profundidade, formato, contexto_extra
        """
        # Enriquece a entrada com termos criticos
        entrada = pergunta
        if termos_extraidos:
            entrada = f"{pergunta}\nTermos-chave: {', '.join(termos_extraidos[:8])}"
        
        try:
            dados = self.decider.extrair_json(
                entrada,
                {
                    'tipo': '',
                    'fontes': [],
                    'profundidade': '',
                    'formato': '',
                    'contexto_extra': '',
                },
                exemplos=[
                    ("O que e SessionCache no MCR?",
                     {"tipo": "conceito_local", "fontes": ["kg", "codigo"],
                      "profundidade": "media", "formato": "explicacao",
                      "contexto_extra": "SessionCache, absorver, pescar, fragmentos"}),
                    ("Como fazer um loop em Python?",
                     {"tipo": "codigo", "fontes": ["codigo", "web"],
                      "profundidade": "baixa", "formato": "exemplo",
                      "contexto_extra": "for, while, list comprehension"}),
                    ("O que e AGI?",
                     {"tipo": "conceito_geral", "fontes": ["web", "kg"],
                      "profundidade": "media", "formato": "explicacao",
                      "contexto_extra": "AGI, desafios, metacognicao"}),
                    ("Crie um conto sobre Eridanus",
                     {"tipo": "lore", "fontes": ["kg", "codigo"],
                      "profundidade": "alta", "formato": "criativo",
                      "contexto_extra": "Eridanus, cidade, Tibia, MCR"}),
                ],
                instrucao=(
                    "Analise a pergunta e decida o melhor enriquecimento.\n"
                    "Se perguntar sobre o MCR ou seus componentes, use fontes locais.\n"
                    "Se for conhecimento geral, use web.\n"
                    "Se for codigo, use exemplos.\n"
                    "Se for criativo (lore, historia), use formato 'criativo'."
                )
            )
            if not dados.get('fontes'):
                dados['fontes'] = ['kg']
            if not dados.get('profundidade'):
                dados['profundidade'] = 'media'
            if not dados.get('formato'):
                dados['formato'] = 'explicacao'
            return dados
        except Exception as e:
            print(f"[Enricher] Erro ao analisar: {e}")
            return {'tipo': 'conceito_geral', 'fontes': ['kg'],
                    'profundidade': 'media', 'formato': 'explicacao', 'contexto_extra': ''}


class ColetorDeContexto:
    """Coleta conhecimento das fontes que o analisador pediu."""

    def __init__(self, ia=None, kg=None, ctx_cache=None):
        self.ia = ia or IA()
        self.kg = kg
        self.ctx = ctx_cache

    def coletar(self, plano, request):
        conhecimento = []
        fontes = plano.get('fontes', ['kg'])
        visto = set()

        def _add(fonte, texto, limite=300):
            t = str(texto)[:limite]
            if t and t not in visto:
                visto.add(t)
                conhecimento.append((fonte, t))

        for fonte in fontes:
            if fonte == 'kg' and self.kg:
                try:
                    for l in self.kg.buscar(request, max_r=5):
                        _add('KG', l.get('solucao', ''))
                except Exception:
                    pass
                try:
                    if hasattr(self.kg, 'buscar_por_embedding'):
                        for l in self.kg.buscar_por_embedding(request, n=3):
                            _add('KG-sem', l.get('solucao', ''))
                except Exception:
                    pass

            elif fonte == 'codigo':
                try:
                    from context_crew import ContextCrew
                    for texto, f in ContextCrew().buscar(request, max_r=3):
                        _add('Codigo', texto)
                except Exception:
                    pass

            elif fonte == 'cache' and self.ctx:
                try:
                    for frag in self.ctx.pescar(pergunta=request, tipos=['contexto'],
                                                 n=3, max_tokens=500):
                        _add('Cache', frag.conteudo)
                except Exception:
                    pass

            elif fonte == 'web':
                try:
                    web = self.ia.buscar_web(request, max_resultados=3)
                    if web:
                        _add('Web', web, 500)
                except Exception:
                    pass

        return conhecimento


# ============================================================
# G6 — VALIDACAO DE RELEVANCIA
# ============================================================
def _validar_relevancia(ia, pergunta, contexto):
    """FAST valida se o contexto coletado e relevante para a pergunta."""
    if not contexto:
        return False
    textos = ' '.join(t for _, t in contexto[:3])
    if not textos.strip():
        return False
    if len(textos) < 20:
        return False
    try:
        prompt = (
            f"Contexto: {textos[:500]}\n"
            f"Pergunta: {pergunta}\n"
            f"Este contexto ajuda a responder? Responda apenas 'sim' ou 'nao'."
        )
        resp = ia.fast(prompt, 0.1, 'leve').strip().lower()
        return resp.startswith('sim')
    except Exception:
        return True


# ============================================================
# G1 — TREE OF THOUGHT (multiplas perspectivas)
# ============================================================
_CAMINHOS_TOT = {
    "analitico": "Pense como um ANALISTA. Foque em dados, fatos, numeros, versoes, metricas e detalhes tecnicos. Seja especifico e preciso.",
    "criativo": "Pense como um CONTADOR DE HISTORIAS. Use exemplos concretos, analogias, cenarios praticos e aplicacoes reais. Torne o conceito vivido.",
    "critico": "Pense como um CRITICO. Questione suposicoes, aponte limitacoes, riscos, pontos cegos. Nao aceite nada pelo valor nominal.",
}

def _aplicar_tree_of_thought(ia, prompt_base):
    """Gera 3 perspectivas (analitico, criativo, critico) e sintetiza."""
    perspectivas = {}
    for nome, instrucao in _CAMINHOS_TOT.items():
        prompt = f"{instrucao}\n\n{prompt_base}"
        resp = ia.gerar(prompt, 0.4, 'pesado')
        if resp:
            perspectivas[nome] = resp.strip()
    
    if len(perspectivas) < 2:
        return prompt_base  # fallback se nao gerou pelo menos 2
    
    prompt_sintese = (
        f"Sintetize as perspectivas abaixo em uma resposta UNICA e COESA.\n\n"
        f"Perspectiva ANALITICA:\n{perspectivas.get('analitico', '')[:1500]}\n\n"
        f"Perspectiva CRIATIVA:\n{perspectivas.get('criativo', '')[:1500]}\n\n"
        f"Perspectiva CRITICA:\n{perspectivas.get('critico', '')[:1500]}\n\n"
        f"Responda de forma completa, incorporando o melhor de cada perspectiva."
    )
    sintese = ia.gerar(prompt_sintese, 0.3, 'pesado')
    return sintese or prompt_base


# ============================================================
# G2 — ANTI-ALUCINACAO POS-GERACAO
# ============================================================
def _revisar_alucinacoes(resposta, kg):
    """Verifica se a resposta contem termos/classes que nao existem no projeto."""
    if not resposta or not kg:
        return resposta
    
    # Extrai possiveis classes/termos inventados (CamelCase compostos)
    invencoes = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', resposta)
    if not invencoes:
        return resposta
    
    problemas = []
    for invencao in invencoes:
        # Verifica no KG
        lessons = kg.buscar(invencao, max_r=1)
        if not lessons:
            # Tenta embedding
            try:
                if hasattr(kg, 'buscar_por_embedding'):
                    lessons_emb = kg.buscar_por_embedding(invencao, n=1)
                    if not lessons_emb:
                        problemas.append(invencao)
            except Exception:
                problemas.append(invencao)
    
    if problemas:
        msg = f"\n[AVISO: Termos nao encontrados no projeto: {', '.join(problemas[:3])}]"
        return resposta + msg
    return resposta


# ============================================================
# G4 — TRADUCAO PT-BR
# ============================================================
def _gerar_com_traducao(ia, prompt, temp=0.4, tarefa='pesado'):
    """Gera em ingles (mais preciso) e traduz para PT-BR."""
    prompt_en = f"Answer in English with technical precision. Use specific terms and examples.\n\n{prompt}"
    resposta_en = ia.gerar(prompt_en, temp, tarefa)
    if not resposta_en:
        return None
    
    try:
        from modulos.tradutor import traduzir
        traducao = traduzir(resposta_en, ia)
        if traducao and len(traducao) > 20:
            return traducao
    except Exception:
        pass
    return resposta_en


# ============================================================
# MONTADOR DE PROMPT (com G3, G4, G8)
# ============================================================
class MontadorDePrompt:
    """Gera o prompt IDEAL com identidade do projeto + router de modelos."""

    def __init__(self, ia=None):
        self.ia = ia or IA()
        self.decider = Decider(self.ia)
        self._cache = PromptCache()

    def montar(self, pergunta, contexto, plano):
        """Monta prompt enriquecido com [G3] MCR_Identity + [G8] Router."""
        
        # [G5] Verificar cache
        cached = self._cache.get(pergunta)
        if cached:
            return cached
        
        if not contexto:
            return pergunta

        conhecimento = '\n'.join(f"[{f}] {t}" for f, t in contexto[:5])

        # [G3] MCR_Identity
        identidade = _MCR_IDENTITY if plano.get('tipo', '').endswith('_local') else ''
        
        prompt_base = (
            f"{identidade}\n\n" if identidade else ""
        )
        prompt_base += (
            f"Contexto coletado:\n{conhecimento}\n\n"
            f"Profundidade: {plano.get('profundidade', 'media')}\n"
            f"Formato: {plano.get('formato', 'explicacao')}\n"
            f"Pergunta original: {pergunta}\n\n"
            f"Com base no contexto ACIMA, responda a pergunta de forma "
            f"ESPECIFICA, usando exemplos e detalhes do contexto. "
            f"Nao seja generico — use o conhecimento fornecido."
        )

        # Tenta otimizar via FAST
        try:
            r = self.decider.extrair_json(
                prompt_base,
                {'prompt': ''},
                instrucao="Retorne APENAS o prompt enriquecido para o LLM."
            )
            prompt_otimizado = r.get('prompt', '')
            if prompt_otimizado and len(prompt_otimizado) > len(pergunta):
                self._cache.set(pergunta, prompt_otimizado)
                return prompt_otimizado
        except Exception:
            pass

        self._cache.set(pergunta, prompt_base)
        return prompt_base
    
    def escolher_modelo(self, tipo):
        """[G8] Router: escolhe melhor modelo para o tipo de tarefa."""
        return _ROUTER.get(tipo, 'pesado')


class Enricher:
    """Sistema completo de enriquecimento — orquestra G1 a G8.
    
    Fluxo:
    1. [G7] Extrair termos criticos
    2. [G5] Verificar cache
    3. Analisar → Coletar → [G6] Validar
    4. [G1] TreeOfThought (3 perspectivas)
    5. Montar prompt com [G3] Identity
    6. [G2] Anti-alucinacao
    7. [G4] Traducao PT-BR
    """

    def __init__(self, ia=None, kg=None, ctx_cache=None):
        self.ia = ia or IA()
        self.kg = kg
        self.ctx = ctx_cache
        self.analisador = AnalisadorDeContexto(self.ia)
        self.coletor = ColetorDeContexto(self.ia, self.kg, self.ctx)
        self.montador = MontadorDePrompt(self.ia)

    def enriquecer(self, pergunta, usar_tot=True, usar_traducao=False):
        """Enriquece uma pergunta com todo o ecossistema.
        
        Args:
            pergunta: String da pergunta
            usar_tot: Se True, aplica TreeOfThought (melhor qualidade, +2x tempo)
            usar_traducao: Se True, gera em ingles e traduz
        
        Returns:
            String com resposta enriquecida (nao so o prompt)
        """
        try:
            # [G7] Termos criticos
            termos = _extrair_termos_criticos(pergunta)
            
            # Analisar
            plano = self.analisador.analisar(pergunta, termos)
            
            # Coletar
            contexto = self.coletor.coletar(plano, pergunta)
            
            # [G6] Validar relevancia
            if contexto and not _validar_relevancia(self.ia, pergunta, contexto):
                contexto = []  # contexto irrelevante, ignora
            
            # Montar prompt base
            prompt = self.montador.montar(pergunta, contexto, plano)
            
            # [G1] TreeOfThought (se ativado)
            if usar_tot:
                prompt = _aplicar_tree_of_thought(self.ia, prompt)
            
            # [G8] Escolher modelo
            modelo = self.montador.escolher_modelo(plano.get('tipo', ''))
            
            # [G4] Gerar (com ou sem traducao)
            if usar_traducao:
                resposta = _gerar_com_traducao(self.ia, prompt, 0.4, modelo)
            else:
                resposta = self.ia.gerar(prompt, 0.4, modelo)
            
            if not resposta:
                return "Nao foi possivel gerar resposta."
            
            # [G2] Anti-alucinacao
            resposta = _revisar_alucinacoes(resposta, self.kg)
            
            return resposta
            
        except Exception as e:
            print(f"[Enricher] Erro: {e}")
            # Fallback: pergunta direta
            return self.ia.gerar(pergunta, 0.4, 'pesado') or pergunta
