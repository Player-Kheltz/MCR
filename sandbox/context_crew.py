"""
CONTEXT CREW — Sistema de Contexto Sob Demanda v1.0
====================================================
Uma crew de 4 IAs que pesquisa, filtra e compacta contexto
em tempo real para o MCR-DevIA.

Arquitetura:
  Pergunta
     |
  Analisador (llama3.1:8b)
     |  Decide: fontes, termos, tipo
     v
  Pesquisador (Python + grep)
     |  Busca: KG, Weblearn (1084 frags), Docs, Codigo
     v
  Filtrador (Python rules)
     |  Remove duplicatas, baixa qualidade, limita tokens
     v
  Compactador (coder:7b ou Python)
     |  Sintetiza contexto final
     v
  Contexto PRONTO para o modelo responder

Uso:
    from context_crew import ContextCrew
    crew = ContextCrew()
    contexto = crew.executar("O que e SHC?")
    print(contexto)
"""

import json, os, re, sys, time, urllib.request
from typing import List, Dict, Optional, Tuple

# ============================================================
# CONFIG
# ============================================================
OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = os.path.join(BASE, 'sandbox')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
WEBLEARN_DIR = r'E:\Modelos IA\weblearn\fragments'
DOCS_DIR = os.path.join(BASE, 'docs')

# ============================================================
# HELPERS
# ============================================================

def _ollama(prompt: str, modelo: str = "qwen2.5-coder:7b",
            ctx: int = 2048, temp: float = 0.1) -> Optional[str]:
    """Chamada direta ao Ollama."""
    try:
        d = json.dumps({'model': modelo, 'prompt': prompt, 'stream': False,
            'options': {'temperature': temp, 'num_ctx': ctx}}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(r, timeout=60).read()).get('response', '')
    except Exception as e:
        return None


STOP_WORDS = {
    'que', 'para', 'com', 'como', 'mais', 'mas', 'por', 'dos', 'das',
    'era', 'sao', 'isso', 'entre', 'sobre', 'antes', 'depois', 'tem',
    'ser', 'seu', 'sua', 'todo', 'pode', 'muito', 'pouco', 'quando',
    'onde', 'assim', 'apos', 'ate', 'sem', 'sob', 'fazer', 'ter',
    'estar', 'ficar', 'ainda', 'bem', 'ja', 'nao', 'sim', 'vai', 'foi',
    'em', 'e', 'o', 'a', 'de', 'da', 'do', 'no', 'na', 'um', 'uma',
    'voce', 'ele', 'ela', 'nos', 'vos', 'eles', 'elas', 'meu', 'seu',
    'esta', 'esse', 'aquele', 'mesmo', 'forma', 'parte', 'cada', 'maior',
    'menor', 'melhor', 'outro', 'novo', 'grande', 'pequeno', 'durante',
    'atraves', 'todos', 'entao', 'tambem', 'apenas', 'agora', 'sempre',
    'nunca', 'talvez', 'quase', 'dentro', 'fora', 'cima', 'baixo',
    'leia', 'arquivo', 'sobre', 'tudo', 'vai', 'foi', 'era', 'sao'
}


def extrair_termos(texto: str, max_termos: int = 10) -> List[str]:
    """Extrai palavras-chave de um texto, removendo stop words."""
    palavras = re.findall(r'\b[a-zA-Z_]{3,}\b', texto.lower())
    termos = [p for p in palavras if p not in STOP_WORDS]
    # Remove duplicatas mantendo ordem
    vistos = set()
    unicos = []
    for t in termos:
        if t not in vistos:
            vistos.add(t)
            unicos.append(t)
    return unicos[:max_termos]


# ============================================================
# 1. ANALISADOR
# ============================================================

class Analisador:
    """Examina a pergunta e decide: que fontes consultar, quais termos buscar."""

    def analisar(self, pergunta: str) -> Dict:
        """
        Retorna:
            fontes: list[str] — kg, weblearn, docs (NUNCA 'codigo' - nao implementado)
            termos: list[str] — palavras EXTRAIDAS LITERALMENTE da pergunta
            tipo: str — definicao, tutorial, erro, comparacao, geral
        """
        prompt = (
            "Extraia TERMOS LITERAIS da pergunta abaixo. "
            "NAO invente termos novos. NAO traduza para ingles.\n"
            "Regras:\n"
            "- fontes: kg para definicoes, weblearn para docs tecnicos, docs para docs do projeto\n"
            "- NUNCA use 'codigo' como fonte\n"
            "- termos: COPIE palavras da pergunta (acronimos, nomes proprios, conceitos)\n"
            "- tipo: apenas definicao, tutorial, erro, comparacao, ou geral\n\n"
            "Pergunta: " + pergunta + "\n\n"
            "Exemplo valido:\n"
            '{"fontes": ["kg"], "termos": ["shc"], "tipo": "definicao"}\n\n'
            "JSON:"
        )

        r = _ollama(prompt, "llama3.1:8b", temp=0.05)
        if r:
            try:
                # Tenta extrair JSON entre chaves
                json_match = re.search(r'\{[^}]+\}', r, re.DOTALL)
                if json_match:
                    dados = json.loads(json_match.group())
                    # Valida campos obrigatorios
                    if "fontes" in dados and "termos" in dados:
                        return dados
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback seguro: extrai termos da pergunta
        termos = extrair_termos(pergunta, 8)
        return {
            "fontes": ["kg", "weblearn", "docs"],
            "termos": termos if termos else ["mcr", "projeto"],
            "tipo": "geral"
        }


# ============================================================
# 2. PESQUISADOR
# ============================================================

class Pesquisador:
    """Busca nas fontes determinadas e retorna resultados com score."""

    def __init__(self):
        self.kg = self._carregar_kg()

    def _carregar_kg(self) -> Optional[Dict]:
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None

    def pesquisar(self, fontes: List[str], termos: List[str]) -> List[Dict]:
        """Retorna resultados consolidados e ordenados por score."""
        resultados = []
        termos_validos = [t for t in termos if len(t) >= 3]

        if not termos_validos:
            return []

        if "kg" in fontes and self.kg:
            resultados.extend(self._buscar_kg(termos_validos))

        if "weblearn" in fontes:
            resultados.extend(self._buscar_weblearn(termos_validos))

        if "docs" in fontes:
            resultados.extend(self._buscar_docs(termos_validos))

        # Ordenar por score decrescente
        resultados.sort(key=lambda x: -x.get("score", 0))
        return resultados[:30]  # Limita a 30 resultados

    def _buscar_kg(self, termos: List[str]) -> List[Dict]:
        """Busca no Knowledge Graph."""
        resultados = []
        for l in self.kg.get("licoes", []):
            texto = (
                f'{l.get("erro","")} {l.get("causa","")} '
                f'{l.get("solucao","")} {l.get("ctx","")}'
            ).lower()
            score = sum(1 for t in termos if t.lower() in texto)
            if score > 0:
                # Bonus para definicoes oficiais
                if l.get("ctx") == "identidade":
                    score += 5
                resultados.append({
                    "texto": l.get("solucao", ""),
                    "fonte": f"KG/{l.get('ctx','geral')}",
                    "score": score,
                    "erro": l.get("erro", ""),
                    "id": l.get("id", "")
                })
        return resultados

    def _buscar_weblearn(self, termos: List[str]) -> List[Dict]:
        """Busca nos 1084 fragmentos do weblearn."""
        if not os.path.isdir(WEBLEARN_DIR):
            return []

        resultados = []
        termos_lower = [t.lower() for t in termos if len(t) >= 3]
        if not termos_lower:
            return []

        for fonte_dir in sorted(os.listdir(WEBLEARN_DIR)):
            dir_path = os.path.join(WEBLEARN_DIR, fonte_dir)
            if not os.path.isdir(dir_path):
                continue

            for frag_file in sorted(os.listdir(dir_path)):
                if not frag_file.endswith('.txt'):
                    continue

                path = os.path.join(dir_path, frag_file)
                try:
                    # Le primeiros 1000 chars (cada fragmento tem ~5K)
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read(2000)

                    content_lower = content.lower()
                    score = sum(1 for t in termos_lower if t in content_lower)

                    if score >= max(1, len(termos_lower) // 3):
                        # Extrai trecho com maior densidade de matches
                        texto = content[:600].strip()
                        resultados.append({
                            "texto": texto,
                            "fonte": f"WL/{fonte_dir}",
                            "score": score,
                            "arquivo": f"{fonte_dir}/{frag_file}"
                        })
                except:
                    continue

        return resultados

    def _buscar_docs(self, termos: List[str]) -> List[Dict]:
        """Busca nos documentos .md do projeto."""
        if not os.path.isdir(DOCS_DIR):
            return []

        resultados = []
        termos_lower = [t.lower() for t in termos if len(t) >= 3]

        for root, _dirs, files in os.walk(DOCS_DIR):
            for f in files:
                if not f.endswith('.md'):
                    continue

                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                        content = fh.read(5000)

                    content_lower = content.lower()
                    score = sum(1 for t in termos_lower if t in content_lower)

                    if score > 0:
                        # Pega cabecalho e contexto
                        linhas = content.split('\n')[:12]
                        texto = '\n'.join(linhas).strip()[:500]
                        resultados.append({
                            "texto": texto,
                            "fonte": f"docs/{f}",
                            "score": score
                        })
                except:
                    continue

        return resultados


# ============================================================
# 3. FILTRADOR
# ============================================================

class Filtrador:
    """Remove duplicatas, HTML sujo, baixa qualidade, e limita tamanho."""

    # Padroes que indicam HTML sujo (conteudo inutil)
    _HTML_LIXO = re.compile(r'(<[^>]+>|&[a-z]+;|&#\d+;|svg|path\d|aria-\w+)', re.IGNORECASE)

    def _qualidade_texto(self, texto: str, fonte: str = "") -> float:
        """Avalia qualidade do texto (0.0 a 1.0)."""
        if not texto or len(texto) < 15:
            return 0.0

        # Bonus para KG (conteudo curado, sempre confiavel)
        if fonte.startswith("KG/"):
            # KG pode ter frases curtas, mas sao valiosas
            palavras = re.findall(r'\b[a-zA-Z]{2,}\b', texto)
            if len(palavras) >= 2:
                return 0.9  # KG e sempre relevante
            return 0.3

        # Detecta HTML lixo (para weblearn/docs)
        hits_html = len(self._HTML_LIXO.findall(texto))
        densidade_html = hits_html / max(1, len(texto) // 100)
        if densidade_html > 3:
            return 0.1  # HTML demais = lixo

        # Verifica se tem texto legivel (palavras de 3+ chars)
        palavras = re.findall(r'\b[a-zA-Z]{3,}\b', texto)
        if len(palavras) < 3:
            return 0.1

        return min(1.0, len(palavras) / 50)

    def filtrar(self, resultados: List[Dict],
                max_tokens: int = 1500) -> List[Dict]:
        """
        Pipeline de filtragem:
        1. Remove HTML lixo (conteudo weblearn sujo)
        2. Remove duplicatas por similaridade
        3. Remove resultados com score muito baixo
        4. Prioriza KG sobre weblearn (bonus de score)
        5. Limita por tokens totais
        """
        if not resultados:
            return []

        # 0. Avalia qualidade do texto e filtra lixo
        validos = []
        for r in resultados:
            texto = r.get("texto", "")
            fonte = r.get("fonte", "")
            qualidade = self._qualidade_texto(texto, fonte)
            if qualidade >= 0.3:  # Aceita se tem texto minimamente legivel
                r["score"] = r.get("score", 0) * qualidade
                validos.append(r)

        if not validos:
            return []

        # 1. Remove duplicatas
        vistos = set()
        unicos = []
        for r in validos:
            chave = r.get("texto", "")[:100].strip().lower()
            # Pega palavras significativas para comparacao
            palavras_chave = ' '.join(re.findall(r'\b[a-zA-Z]{4,}\b', chave)[:5])
            if palavras_chave not in vistos and len(palavras_chave) > 5:
                vistos.add(palavras_chave)
                unicos.append(r)

        # 2. Filtra por score minimo (20% do maximo, mais tolerante)
        max_score = max(r.get("score", 0) for r in unicos) if unicos else 1
        min_score = max(0.5, max_score * 0.2)
        unicos = [r for r in unicos if r.get("score", 0) >= min_score]

        # 3. Prioriza KG: ordena com KG primeiro, depois por score
        kg_results = [r for r in unicos if r.get("fonte", "").startswith("KG/")]
        outros = [r for r in unicos if not r.get("fonte", "").startswith("KG/")]
        kg_results.sort(key=lambda x: -x.get("score", 0))
        outros.sort(key=lambda x: -x.get("score", 0))
        ordenados = kg_results + outros

        # 4. Limita por tokens
        tokens = 0
        limitados = []
        for r in ordenados:
            tk = max(1, len(r.get("texto", "")) // 2)
            if tokens + tk <= max_tokens:
                limitados.append(r)
                tokens += tk
            else:
                espaco = max_tokens - tokens
                if espaco > 30:
                    r["texto"] = r.get("texto", "")[:espaco * 2]
                    limitados.append(r)
                break

        return limitados


# ============================================================
# 4. COMPACTADOR
# ============================================================

class Compactador:
    """Sintetiza o contexto final para o modelo alvo."""

    def compactar(self, resultados: List[Dict],
                  pergunta: str = "",
                  modelo_alvo: str = "qwen2.5-coder:7b") -> str:
        """
        Monta o contexto final.
        Se couber no limite, retorna direto (mais rapido).
        Se nao couber, usa IA para compactar.
        """
        if not resultados:
            return ""

        # Monta contexto bruto
        partes = []
        for r in resultados:
            fonte = r.get("fonte", "?")
            texto = r.get("texto", "").strip()
            if texto:
                partes.append(f"[{fonte}] {texto[:800]}")

        if not partes:
            return ""

        contexto_bruto = "\n\n".join(partes)
        ctx_max = 1800  # Margem de seguranca para coder:7b

        # Se coube, retorna direto (sem custo de IA)
        if len(contexto_bruto) // 2 <= ctx_max:
            return contexto_bruto

        # Se nao coube, compacta via IA
        prompt = (
            f"Compacte o contexto abaixo para no maximo {ctx_max} tokens, "
            f"mantendo APENAS as informacoes mais relevantes para responder "
            f"a pergunta. Elimine repeticoes e detalhes secundarios.\n\n"
            f"Pergunta: {pergunta}\n\n"
            f"Contexto:\n{contexto_bruto[:5000]}\n\n"
            f"Contexto compactado (apenas o essencial):"
        )

        r = _ollama(prompt, "qwen2.5-coder:7b", temp=0.15)
        if r and len(r) > 20:
            return r[:ctx_max * 2]

        # Fallback: trunca
        return contexto_bruto[:ctx_max * 2]


# ============================================================
# CREW ORCHESTRATOR
# ============================================================

class ContextCrew:
    """Orquestra os 4 membros da crew: Analisador, Pesquisador, Filtrador, Compactador."""

    def __init__(self):
        self.analisador = Analisador()
        self.pesquisador = Pesquisador()
        self.filtrador = Filtrador()
        self.compactador = Compactador()
        self.stats = {
            "execucoes": 0,
            "total_tokens": 0,
            "fontes_usadas": {},
            "tempo_total": 0.0
        }

    def executar(self, pergunta: str) -> str:
        """
        Pipeline completa:
        1. Analisar: entende a pergunta, decide fontes e termos
        2. Pesquisar: busca nas fontes
        3. Filtrar: remove ruido e duplicatas
        4. Compactar: sintetiza contexto final
        """
        t0 = time.time()

        # 1. ANALISAR
        analise = self.analisador.analisar(pergunta)
        fontes = analise.get("fontes", ["kg"])
        termos = analise.get("termos", [])
        termos_str = ", ".join(termos[:5]) if termos else "(extraidos)"
        print(f'  [ContextCrew] Analisador: fontes={fontes} termos=[{termos_str}]')

        # 2. PESQUISAR
        resultados = self.pesquisador.pesquisar(fontes, termos)
        print(f'  [ContextCrew] Pesquisador: {len(resultados)} resultados brutos')

        # 3. FILTRAR
        filtrados = self.filtrador.filtrar(resultados)
        print(f'  [ContextCrew] Filtrador: {len(filtrados)} resultados apos filtro')

        # 4. COMPACTAR
        contexto = self.compactador.compactar(filtrados, pergunta)
        tokens = len(contexto) // 2 if contexto else 0
        print(f'  [ContextCrew] Compactador: {tokens} tokens finais')

        # Atualiza estatisticas
        dt = time.time() - t0
        self.stats["execucoes"] += 1
        self.stats["total_tokens"] += tokens
        self.stats["tempo_total"] += dt
        for f in fontes:
            self.stats["fontes_usadas"][f] = self.stats["fontes_usadas"].get(f, 0) + 1

        return contexto

    def get_stats(self) -> Dict:
        """Retorna estatisticas de uso."""
        s = dict(self.stats)
        s["media_tokens"] = s["total_tokens"] // max(1, s["execucoes"])
        s["tempo_medio"] = round(s["tempo_total"] / max(1, s["execucoes"]), 2)
        return s


# ============================================================
# MAIN — Teste direto
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  CONTEXT CREW — Teste")
    print("=" * 60)

    crew = ContextCrew()

    perguntas_teste = [
        "O que e SHC?",
        "Como compilar o OTClient?",
        "O que e MCR?",
        "Qual a diferenca entre Canary e TFS?"
    ]

    for pq in perguntas_teste:
        print(f"\n--- Pergunta: {pq} ---")
        ctx = crew.executar(pq)
        if ctx:
            print(f"\nContexto ({len(ctx)} chars):")
            print(ctx[:600])
        else:
            print("  [AVISO] Nenhum contexto encontrado")
        print("-" * 40)

    print("\n=== Estatisticas ===")
    print(json.dumps(crew.get_stats(), indent=2))
