"""Intention Engine — 3 camadas de detecção de intenção.

Fluxo:
1. PatternEngine: tokeniza → fingerprint → similaridade com exemplares conhecidos
2. Keyword Actions (Léxico V2): match de verbos + domínios
3. FAST 1.5b: fallback semântico
4. Markov: verificação cruzada entre intenção detectada e sequência esperada

Cada camada retorna categoria + confiança. A decisão final é ponderada.

Uso:
    ie = IntentionEngine(pe=PatternEngine(), ia=IA())
    intencoes = ie.detectar("Crie um NPC ferreiro e explique SPA")
    # → [("CREATE", {"tipo": "npc", "alvo": "ferreiro"}, 0.94),
    #    ("EXPLAIN", {"termo": "SPA"}, 0.87)]
"""
import re, math
from typing import List, Tuple, Dict, Optional
from modulos.lexico_v2 import tokenizar_v2, tipos_unicos, verificar_markov, _CATEGORIA_PATTERNS


class IntentionEngine:
    """3 camadas de detecção de intenção com decisão ponderada + Markov."""

    # Categorias de intenção
    CATEGORIAS = ["EXPLAIN", "SEARCH", "CREATE", "EDIT", "REVIEW", "GERAL"]

    # Mapa: categoria → prefixo no léxico v2
    _INTENT_PREFIXOS = {
        "CREATE": "INTENT_CREATE",
        "EXPLAIN": "INTENT_EXPLAIN",
        "SEARCH": "INTENT_SEARCH",
        "EDIT": "INTENT_EDIT",
        "REVIEW": "INTENT_REVIEW",
    }

    # Fingerprints exemplares para Camada 1 (PatternEngine)
    _EXEMPLARES_FP: List[Tuple[str, List[float], float]] = []

    def __init__(self, pe=None, ia=None):
        self._pe = pe
        self._ia = ia

    # ============================================================
    # API PRINCIPAL
    # ============================================================

    def detectar(self, texto: str) -> List[Tuple[str, Dict, float]]:
        """Detecta intenções no texto. Retorna [(categoria, params, confianca), ...]."""
        if not texto or len(texto.strip()) < 5:
            return [("GERAL", {"texto": texto}, 0.3)]

        frases = self._fragmentar(texto)
        resultados = []

        for frase in frases:
            if len(frase.strip()) < 5:
                continue
            cats = self._detectar_frase(frase)
            for cat, params, conf in cats:
                if conf >= 0.3:
                    self._merge(resultados, cat, params, conf)

        if not resultados:
            resultados.append(("GERAL", {"texto": texto}, 0.3))

        return resultados

    # ============================================================
    # CAMADA 1: PatternEngine (shape/fingerprint via v2)
    # ============================================================

    def _camada_pattern(self, frase: str) -> List[Tuple[str, Dict, float]]:
        """Usa PatternEngine para detectar intenção por shape via tokens v2."""
        if not self._pe:
            return []

        try:
            # Usa tokenização v2 para tokens RICOS
            tokens_v2 = tokenizar_v2(frase)
            # Converte para formato que o PatternEngine entende
            tokens_flat = [(t[0], t[1]) for t in tokens_v2 if t[2] >= 0.5]
            
            if not tokens_flat:
                return []
            
            fp = self._pe.fingerprint(tokens_flat)
            padroes = self._pe.extrair_padroes(tokens_flat)
            entropia = padroes.get("entropia", 0.5)
        except Exception:
            return []

        resultados = []
        tipos = [t[0] for t in tokens_flat]
        total = max(len(tipos), 1)
        n_intent = sum(1 for t in tipos if t.startswith("INTENT_"))
        n_dom = sum(1 for t in tipos if t.startswith("DOM_"))

        # Se tem tokens de intenção, a entropia é MAIS REPRESENTATIVA
        if n_intent > 0:
            conf = min(0.6, 0.3 + (n_intent / total) * 0.4)
            # Qual intenção?
            for t in tipos:
                for cat, prefixo in self._INTENT_PREFIXOS.items():
                    if t == prefixo:
                        resultados.append((cat, {}, conf))
                        break
                if resultados:
                    break
        
        # Só DOMÍNIOS sem INTENÇÃO → EXPLAIN ou GERAL
        if n_dom > 0 and n_intent == 0:
            conf = min(0.4, 0.2 + (n_dom / total) * 0.3)
            resultados.append(("EXPLAIN", {}, conf))

        return resultados

    # ============================================================
    # CAMADA 2: Keyword Actions (via Léxico V2)
    # ============================================================

    def _camada_keyword(self, frase: str) -> List[Tuple[str, Dict, float]]:
        """Usa léxico v2 para detectar intenção por keywords + domínios."""
        tokens_v2 = tokenizar_v2(frase)
        if not tokens_v2:
            return []

        tipos = [t[0] for t in tokens_v2]
        palavras = [t[1] for t in tokens_v2]

        # 1. Match de intenção
        cats_detectadas = {}
        for cat, prefixo in self._INTENT_PREFIXOS.items():
            if prefixo in tipos:
                # Conta quantos tokens de intenção
                n = tipos.count(prefixo)
                cats_detectadas[cat] = n

        if not cats_detectadas:
            return []

        # 2. Match de domínios
        dominios = [t for t in tipos if t.startswith("DOM_")]

        # 3. Extrai termo principal
        termo_principal = self._extrair_termo_v2(tokens_v2)

        # 4. Calcula confiança
        melhor_cat = max(cats_detectadas, key=cats_detectadas.get)
        n_intent_matches = cats_detectadas[melhor_cat]

        conf = 0.5  # base
        conf += len(dominios) * 0.1  # +0.1 por domínio encontrado
        conf += (n_intent_matches - 1) * 0.05  # +0.05 por match extra
        conf = min(0.95, conf)

        params = {"termo": termo_principal or ""}
        if dominios:
            params["tipo"] = self._tipo_por_dominio(dominios[0], palavra_extra=palavras[0] if palavras else "")
            if len(dominios) > 1:
                params["subtipos"] = [self._tipo_por_dominio(d) for d in dominios[1:]]

        resultados = [(melhor_cat, params, conf)]

        # Verificação cruzada: Markov valida a intenção
        markov_check = verificar_markov(tokens_v2, melhor_cat, params.get("tipo", "default"))
        if markov_check:
            # Ajusta confiança com Markov
            conf_markov = markov_check.get("taxa_markov", 0) * markov_check.get("peso", 1.0)
            conf_final = (conf * 0.6) + (conf_markov * 0.3) + markov_check.get("bonus", 0) - markov_check.get("penalidade", 0)
            conf_final = max(0.0, min(1.0, conf_final))
            resultados[0] = (melhor_cat, params, round(conf_final, 3))

        return resultados

    # ============================================================
    # CAMADA 3: FAST 1.5b (fallback semântico)
    # ============================================================

    def _camada_fast(self, frase: str) -> List[Tuple[str, Dict, float]]:
        """Usa modelo ultra_leve (1.5b) para classificar intenção."""
        if not self._ia:
            return []
        if not hasattr(self._ia, "fast"):
            return []

        try:
            prompt = (
                f"[INST]\nClassifique a intencao da frase abaixo em UMA categoria:\n"
                f"A = EXPLAIN (explicar, definir, conceito)\n"
                f"B = SEARCH (buscar, encontrar, procurar)\n"
                f"C = CREATE (criar, fazer, gerar, implementar)\n"
                f"D = EDIT (editar, modificar, adicionar)\n"
                f"E = REVIEW (revisar, analisar, avaliar)\n"
                f"F = GERAL (outros)\n\n"
                f"Frase: {frase[:200]}\n"
                f"Responda APENAS com a letra da categoria.\n"
                f"Categoria:[/INST]"
            )
            resp = self._ia.fast(prompt, 0.1, "ultra_leve")
            if not resp:
                return []

            resp = resp.strip().upper()
            mapa = {"A": "EXPLAIN", "B": "SEARCH", "C": "CREATE",
                    "D": "EDIT", "E": "REVIEW", "F": "GERAL"}
            cat = mapa.get(resp[0] if resp else "")
            if cat:
                tokens_v2 = tokenizar_v2(frase)
                termo = self._extrair_termo_v2(tokens_v2)
                return [(cat, {"termo": termo or ""}, 0.75)]
        except Exception:
            pass
        return []

    # ============================================================
    # INTERNO
    # ============================================================

    def _detectar_frase(self, frase: str) -> List[Tuple[str, Dict, float]]:
        """Executa as 3 camadas e combina resultados."""
        # Camada 2 primeiro (mais rápida e precisa)
        kw = self._camada_keyword(frase)
        if kw and kw[0][2] >= 0.8:
            return kw

        # Camada 1: PatternEngine + v2
        pe = self._camada_pattern(frase)

        # Camada 3: FAST (apenas se as outras forem inconclusivas)
        fast = []
        if not kw and not pe:
            fast = self._camada_fast(frase)

        # Ponderação
        pesos = {"keyword": 3, "pattern": 1, "fast": 2}
        votos = {}
        params_por_cat = {}

        for cat, params, conf in (kw or []):
            p = pesos["keyword"] * conf
            votos[cat] = votos.get(cat, 0) + p
            if cat not in params_por_cat:
                params_por_cat[cat] = params

        for cat, params, conf in (pe or []):
            p = pesos["pattern"] * conf
            votos[cat] = votos.get(cat, 0) + p
            if cat not in params_por_cat:
                params_por_cat[cat] = params

        for cat, params, conf in (fast or []):
            p = pesos["fast"] * conf
            votos[cat] = votos.get(cat, 0) + p
            if cat not in params_por_cat:
                params_por_cat[cat] = params

        if not votos:
            return []

        max_peso = max(votos.values())
        total_peso_possivel = sum(pesos.values())
        conf_final = min(0.95, max_peso / total_peso_possivel)

        melhor_cat = max(votos, key=votos.get)
        return [(melhor_cat, params_por_cat.get(melhor_cat, {}), conf_final)]

    def _extrair_termo_v2(self, tokens_v2: List[Tuple[str, str, float]]) -> str:
        """Extrai termo principal dos tokens v2."""
        # PROPER_NOUN primeiro
        for tipo, pal, _ in tokens_v2:
            if tipo == "PROPER_NOUN":
                return pal
        
        # Depois DOM_SYSTEM, DOM_ELEMENT, DOM_SERVER
        for tipo, pal, _ in tokens_v2:
            if tipo in ("DOM_SYSTEM", "DOM_ELEMENT", "DOM_SERVER"):
                return pal
        
        # Último DOM_ que não seja NPC/LORE
        ultimo_dom = ""
        for tipo, pal, _ in reversed(tokens_v2):
            if tipo.startswith("DOM_") and tipo not in ("DOM_NPC", "DOM_LORE"):
                ultimo_dom = pal
        if ultimo_dom:
            return ultimo_dom
        
        # Fallback: primeira palavra com 4+ chars que não seja genérica
        for _, pal, conf in tokens_v2:
            if conf >= 0.5 and len(pal) > 3 and not pal.startswith("INTENT_"):
                return pal
        
        return ""

    def _tipo_por_dominio(self, dominio: str, palavra_extra: str = "") -> str:
        """Mapeia domínio v2 para tipo da intenção."""
        mapa = {
            "DOM_NPC": "npc",
            "DOM_LORE": "lore",
            "DOM_CODE": "codigo",
            "DOM_SYSTEM": "conceito",
            "DOM_SKILL": "habilidade",
            "DOM_ELEMENT": "dominio",
            "DOM_ITEM": "item",
            "DOM_QUEST": "missao",
            "DOM_SERVER": "servidor",
        }
        return mapa.get(dominio, "default")

    def _fragmentar(self, texto: str) -> List[str]:
        frases = re.split(r'[.!?\n]+(?:\s+|$)', texto)
        return [f.strip() for f in frases if f.strip()]

    def _merge(self, resultados, cat, params, conf):
        for i, (c, p, _) in enumerate(resultados):
            if c == cat:
                p.update(params)
                resultados[i] = (cat, p, max(conf, resultados[i][2]))
                return
        resultados.append((cat, params, conf))
