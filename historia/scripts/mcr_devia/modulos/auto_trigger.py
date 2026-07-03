"""Auto Trigger System — Bridge entre intenção e execução de ferramentas.

Recebe intenções do IntentionEngine e executa as ferramentas apropriadas
ANTES de chamar o LLM. O LLM só vê os resultados.

Fluxo:
  IntentionEngine.detectar(texto)
    ↓
  AutoTriggerSystem.executar(intencoes)
    ↓  (para cada intenção, executa ferramentas)
  Resultados injetados no contexto do prompt
    ↓
  LLM só escreve a resposta baseada nos dados

Uso:
    ats = AutoTriggerSystem(kg=kg, ia=ia, tools=tool_orchestrator)
    contexto = ats.processar("Crie um NPC ferreiro")
    # contexto.dados = [RESULTADO DE buscar_estrategico("npc"), ...]
    # contexto.arquivos_criados = ["data/npc/blacksmith.lua"]
    # contexto.edit_realizada = "docs/TESTE_ERIDANUS.md atualizado"
"""
import os, re, json
from typing import List, Tuple, Dict, Optional, Any

# Cache de resultados de ferramentas (evita re-buscar na mesma sessão)
_CACHE_FERRAMENTAS = {}


class AutoTriggerSystem:
    """Bridge entre intenção detectada e execução de ferramentas."""

    # Mapa: (categoria, tipo) → [(ferramenta, params_template), ...]
    # {param} é substituído pelos parâmetros da intenção
    ROTAS = {
        "EXPLAIN": [
            ("buscar_kg", {"termo": "{termo}"}),
            ("buscar_estrategico", {"termo": "{termo}"}),
        ],
        "SEARCH": [
            ("buscar_estrategico", {"termo": "{termo}"}),
            ("buscar_kg", {"termo": "{termo}"}),
        ],
        "CREATE": {
            "npc": [
                ("buscar_estrategico", {"termo": "NPC"}),
                # Tenta ler 1 NPC exemplo
                ("ler_exemplo_npc", {}),
                ("buscar_estrategico", {"termo": "{assunto}"}),
            ],
            "lore": [
                ("buscar_estrategico", {"termo": "lore"}),
                ("buscar_kg", {"termo": "{termo}"}),
            ],
            "codigo": [
                ("buscar_estrategico", {"termo": "{termo}"}),
                ("ler_arquivo_exemplo", {"termo": "{termo}"}),
            ],
            "conceito": [
                ("buscar_kg", {"termo": "{termo}"}),
                ("buscar_estrategico", {"termo": "{termo}"}),
            ],
            "sistema": [
                ("buscar_kg", {"termo": "{termo}"}),
                ("buscar_estrategico", {"termo": "{termo}"}),
            ],
            "default": [
                ("buscar_estrategico", {"termo": "{termo}"}),
                ("buscar_kg", {"termo": "{termo}"}),
            ],
        },
        "EDIT": [
            ("ler_arquivo", {"path": "{path}"}),
            # A edição em si é feita sem LLM
        ],
        "REVIEW": [
            ("ler_arquivo", {"path": "{path}"}),
            ("buscar_estrategico", {"termo": "padrao"}),
        ],
        "GERAL": [
            ("buscar_kg", {"termo": "{termo}"}),
        ],
    }

    # Fallback: se nenhuma rota específica, tenta buscar_estrategico + KG
    ROTA_FALLBACK = [
        ("buscar_estrategico", {"termo": "{termo_bruto}"}),
        ("buscar_kg", {"termo": "{termo_bruto}"}),
    ]

    def __init__(self, kg=None, ia=None, tools=None):
        self._kg = kg
        self._ia = ia
        self._tools = tools
        # Cache de arquivos lidos na sessão
        self._arquivos_lidos = {}
        # MCR (opcional — se disponível, substitui ROTAS hardcoded)
        self._mcr = None
        try:
            from modulos.MCR import MCR as _MCR
            self._mcr = _MCR()
        except ImportError:
            pass

    def processar(self, intencoes: List[Tuple[str, Dict, float]],
                  texto_original: str = "") -> Dict[str, Any]:
        """Processa intenções e executa ferramentas.

        Args:
            intencoes: lista de (categoria, params, confianca)
            texto_original: texto completo da pergunta (para fallback)

        Returns:
            dict com:
              - 'resultados': lista de strings com resultados das ferramentas
              - 'arquivos_criados': lista de paths criados
              - 'edit_realizada': str ou None
              - 'contexto_completo': str para injetar no prompt
              - 'arquivos_para_extrair': tipos de arquivo que o LLM pode gerar
        """
        contexto = {
            "resultados": [],
            "arquivos_criados": [],
            "edit_realizada": None,
            "contexto_completo": "",
            "arquivos_para_extrair": [],
        }

        for cat, params, conf in intencoes:
            self._processar_intencao(cat, params, conf, texto_original, contexto)

        # Monta string de contexto completa
        partes = []
        for r in contexto["resultados"]:
            if r:
                partes.append(r)
        if contexto["edit_realizada"]:
            partes.append(f"[EDICAO REALIZADA]\n{contexto['edit_realizada']}")
        if contexto["arquivos_criados"]:
            partes.append(f"[ARQUIVOS EXTRAIDOS]\n" + "\n".join(f"- {a}" for a in contexto["arquivos_criados"]))

        contexto["contexto_completo"] = "\n\n".join(partes)

        return contexto

    def _processar_intencao(self, cat: str, params: Dict, conf: float,
                            texto_original: str, contexto: Dict):
        """Executa as ferramentas para uma intenção específica."""
        # Pega a rota
        rota = self._get_rota(cat, params)

        for ferramenta, template in rota:
            # Prepara parâmetros
            params_fer = {}
            for k, v in template.items():
                if isinstance(v, str) and "{" in v:
                    v = self._resolver_template(v, params, texto_original)
                params_fer[k] = v

            if not params_fer.get("termo") and not params_fer.get("path"):
                continue

            # Executa ferramenta
            resultado = self._executar(ferramenta, params_fer)

            if resultado:
                contexto["resultados"].append(
                    f"[RESULTADO DE {ferramenta}({params_fer})]\n{resultado}"
                )

        # Se CREATE, marca que o LLM pode gerar blocos de código
        if cat == "CREATE":
            tipo = params.get("tipo", "default")
            if tipo in ("npc", "codigo"):
                contexto["arquivos_para_extrair"].append("lua")
            if tipo in ("lore", "conceito"):
                contexto["arquivos_para_extrair"].append("md")

    def _get_rota(self, cat: str, params: Dict) -> List[Tuple[str, Dict]]:
        """Obtém a rota de ferramentas para uma intenção.
        
        Se MCR estiver disponível, usa MarkovDecisor para decidir a ação.
        Caso contrário, usa ROTAS hardcoded (fallback legado).
        """
        # CAMINHO MCR: MarkovDecisor decide a ação
        if self._mcr:
            estado = {'intencao': cat, 'ie_conf': 0.7, 'entropia_byte': 0.5}
            acao, conf = self._mcr._decidir(estado)
            if acao and conf > 0.2:
                # Converte ação MCR para ferramenta auto_trigger
                traducao = {
                    'buscar_kg': ('buscar_kg', {'termo': '{termo}'}),
                    'buscar_dados': ('buscar_estrategico', {'termo': '{termo}'}),
                    'buscar_arquivos': ('buscar_estrategico', {'termo': '{termo}'}),
                    'responder': None,  # não precisa de ferramenta
                }
                trad = traducao.get(acao)
                if trad:
                    return [trad]
                return []
        
        # CAMINHO LEGADO: ROTAS hardcoded (fallback)
        if cat in self.ROTAS:
            rota = self.ROTAS[cat]
            if isinstance(rota, dict):
                # Rota específica por tipo
                tipo = params.get("tipo", "default")
                return rota.get(tipo, rota.get("default", self.ROTA_FALLBACK))
            return rota
        return self.ROTA_FALLBACK

    def _resolver_template(self, template: str, params: Dict,
                           texto_original: str) -> str:
        """Resolve template com parâmetros."""
        resultado = template

        # Substitui {termo}
        if "{termo}" in resultado:
            termo = params.get("termo", "")
            if not termo:
                # Tenta extrair do texto original
                termo = self._extrair_termo_bruto(texto_original)
            resultado = resultado.replace("{termo}", termo)

        # Substitui {assunto}
        if "{assunto}" in resultado:
            assunto = params.get("termo", params.get("tipo", ""))
            resultado = resultado.replace("{assunto}", assunto)

        # Substitui {path}
        if "{path}" in resultado:
            path = params.get("path", "")
            if not path:
                path = self._extrair_path(texto_original)
            resultado = resultado.replace("{path}", path)

        # Substitui {tipo}
        if "{tipo}" in resultado:
            resultado = resultado.replace("{tipo}", params.get("tipo", "default"))

        # Substitui {termo_bruto}
        if "{termo_bruto}" in resultado:
            bruto = self._extrair_termo_bruto(texto_original)
            resultado = resultado.replace("{termo_bruto}", bruto)

        return resultado

    def _executar(self, ferramenta: str, params: Dict) -> str:
        """Executa uma ferramenta e retorna o resultado como string."""
        # Cache key
        cache_key = f"{ferramenta}:{json.dumps(params, sort_keys=True, ensure_ascii=False)}"
        if cache_key in _CACHE_FERRAMENTAS:
            return _CACHE_FERRAMENTAS[cache_key]

        resultado = ""
        try:
            if ferramenta == "buscar_kg":
                resultado = self._executar_buscar_kg(params.get("termo", ""))
            elif ferramenta == "buscar_estrategico":
                resultado = self._executar_buscar_estrategico(params.get("termo", ""))
            elif ferramenta == "ler_arquivo":
                resultado = self._executar_ler_arquivo(params.get("path", ""))
            elif ferramenta == "ler_exemplo_npc":
                resultado = self._executar_ler_exemplo("npc")
            elif ferramenta == "ler_arquivo_exemplo":
                resultado = self._executar_ler_exemplo(params.get("termo", ""))
            else:
                resultado = f"(Ferramenta '{ferramenta}' nao implementada no AutoTrigger)"
        except Exception as e:
            resultado = f"(Erro ao executar {ferramenta}: {e})"

        # Cache (limitado a 50 entradas)
        if len(_CACHE_FERRAMENTAS) < 50:
            _CACHE_FERRAMENTAS[cache_key] = resultado

        return resultado

    # ============================================================
    # EXECUTORES ESPECÍFICOS
    # ============================================================

    def _executar_buscar_kg(self, termo: str) -> str:
        """Busca no Knowledge Graph."""
        if not self._kg or not termo:
            return ""
        lessons = self._kg.buscar(termo, max_r=3) or []
        if not lessons:
            return ""
        partes = []
        for l in lessons:
            sol = l.get("solucao", "").strip()
            if sol:
                partes.append(f"- {sol}")
        return "\n".join(partes)

    def _executar_buscar_estrategico(self, termo: str) -> str:
        """Busca estratégica (descobre diretórios, arquivos, funções)."""
        if not self._tools or not termo:
            return ""
        if not hasattr(self._tools, "executar"):
            return ""
        r = self._tools.executar("buscar_estrategico", {"termo": termo})
        if r and r.get("sucesso"):
            txt = str(r.get("resultado", ""))
            if txt and "Nenhum" not in txt and len(txt) > 30:
                return txt
        return ""

    def _executar_ler_arquivo(self, path: str) -> str:
        """Lê um arquivo."""
        if not path:
            return ""
        BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        full_path = os.path.join(BASE, path) if not os.path.isabs(path) else path
        if not os.path.exists(full_path):
            return f"(Arquivo nao encontrado: {path})"
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
                self._arquivos_lidos[path] = conteudo
                return f"({len(conteudo)} chars, {len(conteudo.splitlines())} linhas):\n{conteudo}"
        except Exception as e:
            return f"(Erro ao ler: {e})"

    def _executar_ler_exemplo(self, tipo: str) -> str:
        """Tenta ler um arquivo de exemplo do tipo especificado."""
        # Procura em diretórios conhecidos
        BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        caminhos = []

        if tipo == "npc":
            caminhos = [
                "data/npc/",
                "data-canary/data/npc/",
            ]
        else:
            # Fallback: busca estratégica
            r = self._executar_buscar_estrategico(tipo)
            if not r:
                return ""
            # Tenta extrair o primeiro path do resultado
            linhas = r.split("\n")
            for linha in linhas:
                m = re.search(r'[\w/]+\.\w+', linha)
                if m:
                    path = m.group(0)
                    resultado = self._executar_ler_arquivo(path)
                    if resultado and "nao encontrado" not in resultado.lower():
                        return f"[EXEMPLO DE {tipo.upper()}]\n{resultado}"
            return f"[BUSCA POR {tipo.upper()}]\n{r}"

        for caminho in caminhos:
            full = os.path.join(BASE, caminho)
            if os.path.isdir(full):
                arquivos = [f for f in os.listdir(full) if f.endswith('.lua')]
                if arquivos:
                    exemplo = os.path.join(full, arquivos[0])
                    resultado = self._executar_ler_arquivo(
                        os.path.relpath(exemplo, BASE))
                    if resultado:
                        return f"[EXEMPLO DE {tipo.upper()}]\n{resultado}"

        return ""

    def _extrair_termo_bruto(self, texto: str) -> str:
        """Extrai o primeiro termo relevante do texto."""
        if not texto:
            return ""
        texto_lower = texto.lower()
        # Tenta capturar ALL CAPS
        siglas = re.findall(r'\b[A-Z]{2,}\b', texto)
        if siglas:
            return siglas[0]
        # Tenta capturar palavra após verbos de ação
        padrao = r'(?:explique|defina|o\s*que\s*[eé]\s*|busque|encontre|crie|faça|gere|adicione)\s+[oa]?\s*(\w+)'
        m = re.search(padrao, texto_lower)
        if m:
            return m.group(1)
        # Primeira palavra com 4+ chars
        palavras = re.findall(r'\b[a-zà-ú]{4,}\b', texto_lower)
        return palavras[0] if palavras else ""

    def _extrair_path(self, texto: str) -> str:
        """Extrai path de arquivo do texto."""
        # Procura por padrões de path
        padrao = r'(?:arquivo\s+)?[\"\'`]?([\w/\.-]+\.(?:lua|md|py|json|txt))[\"\'`]?'
        m = re.search(padrao, texto)
        if m:
            path = m.group(1)
            # Remove possíveis prefixos
            if not path.startswith(("data/", "docs/", "sandbox/", "src/")):
                # Tenta encontrar no contexto
                pass
            return path
        # Tenta capturar caminho após "arquivo" ou "em"
        m2 = re.search(r'(?:arquivo|em)\s+[\"\'`]?([\w/\.-]+)', texto)
        if m2:
            return m2.group(1)
        return ""
