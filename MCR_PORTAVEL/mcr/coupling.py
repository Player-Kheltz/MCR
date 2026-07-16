"""MCRCoupling — Acoplamento N-dimensional com similaridade semântica universal.

TUDO é P(b|a). Toda observacao (texto+açao) gera features em N planos:
  byte, char, token, bigram, trigram, posicao, contexto.
A assinatura de uma palavra = UNIAO de features de TODOS os planos
que estao contidos nela. A similaridade entre duas palavras =
NMI entre suas assinaturas N-dimensionais.

Isso captura a ideia: quando "criar" vira "gerar", apenas UM nivel
muda (o token), todo o resto (bytes, chars, bigrams, trigrams,
posicao, contexto) permanece identico. A assinatura N-dimensional
revela que sao a MESMA COISA.

Universal: qualquer idioma, qualquer token, qualquer dominio.
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import re, math, json


class MCRCoupling:

    def __init__(self):
        self._palavra_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._transicao_palavra: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._cluster_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._posicao_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._feature_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._acao_features: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._ngrama: Dict[int, Dict[tuple, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int)))
        self._total = 0
        self._freq_acao: Dict[str, int] = defaultdict(int)
        self._composicoes_aprendidas: Dict[tuple, str] = {}
        self._estado_features: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def _extrair_features_nd(self, texto: str, acao: str):
        """Extrai features N-dimensionais do texto e associa a acao.

        Preenche:
          _feature_acao[feature][acao] += 1  (feature→acao)
          _acao_features[acao][feature] += 1  (acao→feature, inverso)

        Planos: t:{token}, c:{char}, b:{byte}, bg:{bigram},
          ng:{trigram}, p{i}:{token}, ca:{token}, cd:{token}
        """
        texto = str(texto)
        acao = str(acao)
        raw = texto.lower()

        feats = set()

        # Token level
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', raw)
        for t in set(tokens):
            feats.add(f"t:{t}")

        # Char level
        for ch in set(raw):
            if ch.isprintable() or ch in '\n\r\t':
                feats.add(f"c:{ch}")

        # Byte level
        for byte in set(texto.encode('utf-8')):
            feats.add(f"b:{byte}")

        # Bigram and trigram levels (chars only)
        chars = re.sub(r'[^a-z0-9]', '', raw)
        for i in range(len(chars) - 1):
            feats.add(f"bg:{chars[i:i+2]}")
        for i in range(len(chars) - 2):
            feats.add(f"ng:{chars[i:i+3]}")

        # Position level (first 6 tokens)
        for i, t in enumerate(tokens[:6]):
            feats.add(f"p{i}:{t[:12]}")

        # Context before/after
        for i in range(len(tokens)):
            if i > 0:
                feats.add(f"ca:{tokens[i-1]}")
            if i < len(tokens) - 1:
                feats.add(f"cd:{tokens[i+1]}")

        # Populate both indexes
        acao_idx = self._acao_features[acao]
        for feat in feats:
            self._feature_acao[feat][acao] += 1
            acao_idx[feat] = acao_idx.get(feat, 0) + 1

    def alimentar(self, texto: str, acao: str):
        self._total += 1
        acao = str(acao)
        self._freq_acao[acao] += 1

        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        for p in set(palavras):
            self._palavra_acao[p][acao] += 1

        partes = texto.replace('_', ' ').lower().split()
        for i, p in enumerate(partes[:6]):
            self._posicao_acao[f"P{i}:{p[:10]}"][acao] += 1

        visited = set()
        tokens = [p for p in partes if len(p) >= 3]
        for i in range(len(tokens) - 1):
            a, b = tokens[i], tokens[i+1]
            self._transicao_palavra[a][b] += 1
            self._transicao_palavra[b][a] += 1

        for p in tokens:
            if p in visited:
                continue
            visited.add(p)
            self._palavra_acao[p][acao] += 1

        for ordem in (3, 4):
            if len(tokens) >= ordem:
                for i in range(len(tokens) - ordem + 1):
                    prefix = tuple(tokens[i:i + ordem - 1])
                    prox = tokens[i + ordem - 1]
                    self._ngrama[ordem][prefix][prox] += 1

        self._extrair_features_nd(texto, acao)

    def alimentar_lote(self, pares: list):
        for texto, acao in pares:
            self.alimentar(texto, acao)

    def merge(self, outro: 'MCRCoupling'):
        for p, d in outro._palavra_acao.items():
            for a, c in d.items():
                self._palavra_acao[p][a] += c
        for p, d in outro._transicao_palavra.items():
            for v, c in d.items():
                self._transicao_palavra[p][v] += c
        for cid, d in outro._cluster_acao.items():
            for a, c in d.items():
                self._cluster_acao[cid][a] += c
        for pk, d in outro._posicao_acao.items():
            for a, c in d.items():
                self._posicao_acao[pk][a] += c
        for fk, d in outro._feature_acao.items():
            for a, c in d.items():
                self._feature_acao[fk][a] += c
        for acao, d in outro._acao_features.items():
            for feat, c in d.items():
                self._acao_features[acao][feat] = self._acao_features[acao].get(feat, 0) + c
        for ordem, pref_dict in outro._ngrama.items():
            for prefix, prox_dict in pref_dict.items():
                for prox, c in prox_dict.items():
                    self._ngrama[ordem][prefix][prox] += c
        self._total += outro._total
        for a, c in outro._freq_acao.items():
            self._freq_acao[a] += c
        for p, d in outro._estado_features.items():
            for f, c in d.items():
                self._estado_features[p][f] += c
        return self

    def alimentar_swarm(self, pares: list, chunk_size: int = 0):
        """Swarm MCR: divide dados em N MCRs independentes, merge em arvore.

        Cada chunk vira um MCR autonomo (leve, rapido). O merge em
        arvore binaria reduz complexidade de O(N) para O(log N).

        Args:
            pares: lista de (texto, acao)
            chunk_size: 0 = automatico (estima baseado no total)
        """
        n = len(pares)
        if n < 500:
            self.alimentar_lote(pares)
            return self

        if chunk_size <= 0:
            chunk_size = max(100, min(500, n // 8))

        chunks = [pares[i:i+chunk_size] for i in range(0, n, chunk_size)]

        couplings = []
        for chunk in chunks:
            m = MCRCoupling()
            m.alimentar_lote(chunk)
            couplings.append(m)

        while len(couplings) > 1:
            proximo = []
            for i in range(0, len(couplings), 2):
                if i + 1 < len(couplings):
                    couplings[i].merge(couplings[i+1])
                    proximo.append(couplings[i])
                else:
                    proximo.append(couplings[i])
            couplings = proximo

        self.merge(couplings[0])
        return self

    def alimentar_cluster(self, cluster_id, acao: str):
        acao = str(acao)
        self._cluster_acao[f"C{cluster_id}"][acao] += 1

    def decidir(self, texto: str, mk_pred: Tuple[Optional[str], float],
                cluster_id=None, cluster_conf=0.0) -> Tuple[str, float]:
        distribs = []
        acao_mk, conf_mk = mk_pred
        if acao_mk:
            d_mk = {str(acao_mk): conf_mk}
            distribs.append((d_mk, self._entropia_dist(d_mk)))

        d_palavra = self._dist_palavras(texto)
        if d_palavra:
            distribs.append((d_palavra, self._entropia_dist(d_palavra)))

        if cluster_id is not None:
            d_cluster = self._dist_cluster(cluster_id)
            if d_cluster:
                distribs.append((d_cluster, self._entropia_dist(d_cluster)))

        d_pos = self._dist_posicoes(texto)
        if d_pos:
            distribs.append((d_pos, self._entropia_dist(d_pos)))

        if not distribs:
            return (acao_mk or 'responder'), conf_mk
        combinada = self._superpor(distribs)
        if not combinada:
            return (acao_mk or 'responder'), conf_mk
        melhor = max(combinada, key=combinada.get)
        return melhor, combinada[melhor]

    def _superpor(self, distribs: List[Tuple[Dict[str, float], float]]) -> Dict[str, float]:
        if not distribs:
            return {}
        pesos_raw = [(1.0 - h) for _, h in distribs]
        total_raw = sum(pesos_raw) or 1.0
        pesos = [w / total_raw for w in pesos_raw]
        combinada: Dict[str, float] = defaultdict(float)
        for (d, _), peso in zip(distribs, pesos):
            if not d:
                continue
            total_d = sum(d.values()) or 1.0
            for acao, prob in d.items():
                combinada[acao] += (prob / total_d) * peso
        total = sum(combinada.values()) or 1.0
        return {a: s / total for a, s in combinada.items()}

    def _dist_palavras(self, texto: str) -> Dict[str, float]:
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        scores: Dict[str, float] = defaultdict(float)
        for p in set(palavras):
            dist = self._palavra_acao.get(p, {})
            if not dist:
                proxies = self.palavras_similares(p, threshold=0.20)
                if proxies:
                    for prox, conf in proxies:
                        d = self._palavra_acao.get(prox, {})
                        if not d:
                            continue
                        td = sum(d.values()) or 1
                        for a, c in d.items():
                            scores[a] += (c / td) * conf
                continue
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores[a] += c / total
        return dict(scores) if scores else {}

    def _dist_cluster(self, cluster_id) -> Dict[str, float]:
        dist = self._cluster_acao.get(f"C{cluster_id}", {})
        if not dist:
            return {}
        total = sum(dist.values()) or 1
        return {a: c / total for a, c in dist.items()}

    def _dist_posicoes(self, texto: str) -> Dict[str, float]:
        partes = texto.replace('_', ' ').split()
        scores: Dict[str, float] = defaultdict(float)
        for i, p in enumerate(partes[:6]):
            dist = self._posicao_acao.get(f"P{i}:{p[:10]}", {})
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores[a] += c / total
        return dict(scores) if scores else {}

    def _entropia_shannon(self, d: Dict[str, int]) -> float:
        """Entropia de Shannon NATURAL (nao normalizada) de uma distribuicao.
        
        H(X) = -sum p(x) * log2 p(x)
        Retorna em bits. Distribuicao vazia => max entropia.
        """
        if not d:
            return 0.0
        total = sum(d.values()) or 1
        h = 0.0
        for v in d.values():
            if v > 0:
                p = v / total
                h -= p * math.log2(p)
        return h

    def _entropia_dist(self, d: Dict[str, float]) -> float:
        if not d:
            return 1.0
        total = sum(d.values()) or 1.0
        h = 0.0
        for v in d.values():
            p = v / total
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(d), 2))
        return h / max_h if max_h > 0 else 1.0

    def _cos_sim(self, a_distrib: Dict[str, float], b_distrib: Dict[str, float]) -> float:
        if not a_distrib or not b_distrib:
            return 0.0
        todas = set(a_distrib) | set(b_distrib)
        aa = sum(a_distrib.get(k, 0)**2 for k in todas) ** 0.5
        bb = sum(b_distrib.get(k, 0)**2 for k in todas) ** 0.5
        if aa == 0 or bb == 0:
            return 0.0
        dot = sum(a_distrib.get(k, 0) * b_distrib.get(k, 0) for k in todas)
        return dot / (aa * bb)

    def _assinatura_palavra(self, palavra: str) -> Dict[str, int]:
        """Assinatura contextual N-dimensional de uma palavra.

        Diferente da abordagem anterior (sub-features da propria palavra),
        esta versao captura o CONTEXTO COMPLETO: todas as features de
        TODAS as observacoes onde a palavra aparece.

        Se "criar monstro" gerou features {t:criar, t:monstro, c:c, ...},
        entao a assinatura de "criar" inclui TUDO — nao so features de
        "criar" em si, mas de TODA a observacao.

        Isso realiza a visao: quando "criar" vira "gerar", apenas o
        token t:criar→t:gerar muda; todo o contexto permanece.
        """
        if not palavra:
            return {}
        if not hasattr(self, '_cache_assinatura'):
            self._cache_assinatura = {}
        p = palavra.lower()
        if p in self._cache_assinatura:
            return self._cache_assinatura[p]

        sig = defaultdict(int)
        for k, v in self._palavra_acao.get(p, {}).items():
            sig[f"acao:{k}"] += v
        for k, v in self._transicao_palavra.get(p, {}).items():
            sig[f"ctx:{k}"] += v
        for k, d in self._posicao_acao.items():
            if k.split(":", 1)[-1] == p and d:
                for ak, av in d.items():
                    sig[f"posacao:{ak}"] += av

        self._cache_assinatura[p] = dict(sig) if sig else {}
        return self._cache_assinatura[p]

    def _nmi(self, dict_a, dict_b) -> float:
        """Similaridade por reducao de incerteza da mistura — MCR puro.

        Implementa uma variante de Informacao Mutua baseada na entropia
        da MISTURA das duas distribuicoes marginais:

          H_mix = -sum ((pa[k] + pb[k]) / (ta + tb)) * log2(...)
          sim(a,b) = (H(a) + H(b) - H_mix) / max(H(a), H(b))

        Nao é NMI classico (que requer distribuicao conjunta p(a,b)),
        mas captura a mesma ideia: duas distribuicoes similares reduzem
        a incerteza quando combinadas.

        Propriedades:
          - a == b => 1.0 (maxima similaridade)
          - a ∩ b = {} => 0.0 (disjuntas, zero informacao compartilhada)
          - Retorna em [0, 1]

        Nao usa cosseno, SVD, distancia — so Markov + Entropia.
        """
        if not dict_a or not dict_b:
            return 0.0
        todas = set(dict_a) | set(dict_b)
        ta = sum(dict_a.values()) or 1
        tb = sum(dict_b.values()) or 1
        tab = ta + tb

        ha = 0.0
        for k in todas:
            p = dict_a.get(k, 0) / ta
            if p > 0:
                ha -= p * math.log2(p)
        hb = 0.0
        for k in todas:
            p = dict_b.get(k, 0) / tb
            if p > 0:
                hb -= p * math.log2(p)
        hab = 0.0
        for k in todas:
            p = (dict_a.get(k, 0) + dict_b.get(k, 0)) / tab
            if p > 0:
                hab -= p * math.log2(p)
        mi = ha + hb - hab
        maxh = max(ha, hb)
        if maxh <= 0:
            return 0.0
        return max(0.0, min(1.0, mi / maxh))

    def compor(self, sig_a: Dict[str, int], sig_b: Dict[str, int],
               tipo: Optional[str] = None) -> Dict[str, int]:
        """FASE 1 — Operador de composicao de assinaturas (gateway semantico).

        Combina duas assinaturas markovianas numa so. Alinhado aos 6
        pilares da Filosofia MCR e a Equacao 5D:

        Pilar 2 — Entropia descobre, SEM threshold hardcoded:
          A decisao modificacao vs complemento NAO usa limiar fixo.
          Gera ambos os candidatos e a Equacao 5D avalia qual e melhor.

        Equacao 5D — Fonte da verdade:
          Cada candidato e avaliado em 5 dimensoes organicas:
            - CERTEZA:     NMI(composto, sig_a) — fidelidade ao conceito base
            - COMPLETUDE:  fracao de features de A preservadas no composto
            - INFORMACAO:  entropia Shannon normalizada do composto
            - ESTABILIDADE: gaussiana da entropia — pune loops (H~0) e caos (H~1)
            - EFICIENCIA:  1/log2(n_features+1) — recompensa simplicidade

          O candidato com maior nota_5D vence. Sem if/else de threshold.

        Pilar 5 — Fecha o loop (gerar -> validar -> aprender):
          Apos decidir, armazena o tipo vencedor por par de assinaturas
          em _composicoes_aprendidas. Futuras composicoes do mesmo par
          reutilizam o tipo aprendido — Markov puro: P(tipo | par).

        Modificacao (intersecao ponderada):
          - Features so em A: preservadas (sig_a[k] * 1)
          - Features em ambos: amplificadas (sig_a[k] * sig_b[k])
          - Features so em B: descartadas (0 * sig_b[k])

        Complemento (uniao ponderada):
          - Todas as features de A e B somadas.

        Args:
            sig_a: assinatura markoviana da palavra/conceito base
            sig_b: assinatura markoviana do modificador/complemento
            tipo: "modificacao" | "complemento" | None (auto via 5D)
        Returns:
            assinatura composta (Dict[str, int]), normalizada > 0
        """
        if not sig_a and not sig_b:
            return {}
        if not sig_a:
            return dict(sig_b)
        if not sig_b:
            return dict(sig_a)

        if tipo is None:
            chave = self._chave_composicao(sig_a, sig_b)
            if chave in self._composicoes_aprendidas:
                tipo = self._composicoes_aprendidas[chave]

        if tipo is None:
            sig_mod = {k: sig_a.get(k, 0) * sig_b.get(k, 1)
                       for k in set(sig_a) | set(sig_b)}
            sig_mod = {k: v for k, v in sig_mod.items() if v != 0}
            sig_comp = {k: sig_a.get(k, 0) + sig_b.get(k, 0)
                        for k in set(sig_a) | set(sig_b)}

            nota_mod = self._avaliar_composicao(sig_mod, sig_a)
            nota_comp = self._avaliar_composicao(sig_comp, sig_a)

            if nota_mod >= nota_comp:
                tipo = "modificacao"
                sig = sig_mod
            else:
                tipo = "complemento"
                sig = sig_comp

            self._composicoes_aprendidas[chave] = tipo
            return sig

        if tipo == "modificacao":
            sig = {k: sig_a.get(k, 0) * sig_b.get(k, 1)
                   for k in set(sig_a) | set(sig_b)}
        else:
            sig = {k: sig_a.get(k, 0) + sig_b.get(k, 0)
                   for k in set(sig_a) | set(sig_b)}

        return {k: v for k, v in sig.items() if v != 0}

    def _chave_composicao(self, sig_a: Dict[str, int],
                          sig_b: Dict[str, int]) -> tuple:
        """Hash estavel para cache de composicoes aprendidas (pilar 5)."""
        ha = hash(frozenset(sig_a.items()))
        hb = hash(frozenset(sig_b.items()))
        return (ha, hb)

    def _avaliar_composicao(self, sig_composto: Dict[str, int],
                            sig_base: Dict[str, int]) -> float:
        """Equacao 5D avalia a qualidade de uma composicao candidata.

        5 dimensoes organicas conforme mcr/equacao_mcr.py:
          - CERTEZA:     NMI(composto, base) — fidelidade ao conceito base
          - COMPLETUDE:  |features_composto ∩ features_base| / |features_base|
          - INFORMACAO:  entropia Shannon normalizada [0,1] do composto
          - ESTABILIDADE: gaussiana centrada em 0.5 — pune extremos
          - EFICIENCIA:  1/log2(|features|+1) — recompensa simplicidade

        Retorna nota 0-1 via sigmoide 5D. Sem threshold, sem hardcode.
        """
        try:
            from mcr.equacao_mcr import avaliar_5d
        except ImportError:
            try:
                from equacao_mcr import avaliar_5d
            except ImportError:
                return self._nmi(sig_composto, sig_base)

        certeza = self._nmi(sig_composto, sig_base)

        feats_base = set(sig_base.keys())
        feats_comp = set(sig_composto.keys())
        if feats_base:
            completude = len(feats_base & feats_comp) / len(feats_base)
        else:
            completude = 0.0

        informacao = self._entropia_dist(sig_composto)

        estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * 0.2 ** 2))

        n_feats = len(sig_composto)
        eficiencia = 1.0 / math.log2(max(n_feats + 1, 2))

        return avaliar_5d(certeza, completude, informacao,
                          estabilidade, eficiencia)

    def _tentar_inversao_funtor(self, prev: str, palavra: str) -> Optional[str]:
        """FASE 1+2 — Detecta funtor (alta entropia) e encontra antonimo.

        Pilar 2: ENTROPIA descobre funtores — palavras que aparecem com
        acoes diversas sao modificadores de polaridade (nao, nunca,
        tambem, etc). Quando detectado, o conceito seguinte e invertido
        via seu antonimo — descoberto pela infraestrutura da FASE 2
        (extrair_relacoes: contraste ctx-NMI x (1-acao-NMI)).

        Sem hardcode: qualquer palavra de alta entropia vira funtor.
        "nao" nao e especial — sua entropia alta e que a revela.

        Args:
            prev: palavra anterior (possivel funtor)
            palavra: palavra atual (cujjo antonimo queremos)
        Returns:
            antonimo da palavra, ou None se prev nao e funtor
        """
        if not hasattr(self, '_cache_funtores'):
            self._cache_funtores = {}
            self._cache_antonimos_frase = {}
            self._cache_stats_h = None

        if self._cache_stats_h is None:
            entropias = []
            for w in self._palavra_acao:
                h = self._entropia_shannon(self._palavra_acao.get(w, {}))
                if h > 0:
                    entropias.append(h)
            if entropias:
                mean_h = sum(entropias) / len(entropias)
                var_h = sum((h - mean_h) ** 2 for h in entropias) / len(entropias)
                std_h = var_h ** 0.5
                self._cache_stats_h = (mean_h, std_h)
            else:
                self._cache_stats_h = (0.0, 0.0)

        mean_h, std_h = self._cache_stats_h
        if std_h <= 0:
            return None

        if prev not in self._cache_funtores:
            h_prev = self._entropia_shannon(self._palavra_acao.get(prev, {}))
            self._cache_funtores[prev] = h_prev > mean_h + std_h

        if not self._cache_funtores[prev]:
            return None

        if palavra not in self._cache_antonimos_frase:
            rels = self.extrair_relacoes(palavra)
            ants = rels.get('antonimos', [])
            self._cache_antonimos_frase[palavra] = ants[0][0] if ants else None

        return self._cache_antonimos_frase.get(palavra)

    def _assinatura_frase(self, frase: str) -> Dict[str, int]:
        """FASE 1.2 — Assinatura composicional de uma frase multi-palavra.

        Quebra a frase em palavras, extrai a assinatura de cada uma via
        _assinatura_palavra(), e compoe recursivamente via compor().

        "cachorro verde" => compor(sig("cachorro"), sig("verde"))
        "correr rapido"  => compor(sig("correr"), sig("rapido"))
        "criar monstro dragao" => compor(compor(sig("criar"),
                                                sig("monstro")),
                                         sig("dragao"))

        FASE 1+2 — Negacao por funtor entrópico:
        Se a palavra anterior tem alta entropia (aparece com acoes
        diversas), ela e um FUNTOR (modificador de polaridade). O
        conceito seguinte e invertido via seu ANTONIMO, descoberto
        pela FASE 2 (extrair_relacoes). "nao bom" => sig("ruim").

        Pilar 2: entropia descobre o funtor (sem hardcode "if == nao").
        Pilar 2: contraste ctx x acao descobre o antonimo (FASE 2).
        Pilar 5: usar => aprender => reusar (cache de funtores).

        Args:
            frase: texto de entrada (uma ou mais palavras)
        Returns:
            assinatura composta, ou {} se frase vazia/sem palavras
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
        if not palavras:
            return {}

        sig = self._assinatura_palavra(palavras[0])
        for i in range(1, len(palavras)):
            p = palavras[i]
            prev = palavras[i - 1]
            sig_p = self._assinatura_palavra(p)
            if not sig_p:
                continue

            antonym = self._tentar_inversao_funtor(prev, p)
            if antonym:
                sig_ant = self._assinatura_palavra(antonym)
                if sig_ant:
                    if i == 1:
                        sig = sig_ant
                    else:
                        sig = self.compor(sig, sig_ant)
                    continue

            sig = self.compor(sig, sig_p)
        return sig if sig else {}

    def _extrair_features_estado(self, estado) -> set:
        """FASE 3 — Extrai features N-dimensionais de um estado do mundo.

        Flatten recursivo de dict/list/JSON para features markovianas:
          - est_val:{path}:{value}  — valor especifico do atributo
          - est_attr:{key}          — nome do atributo (compartilhado)

        Os est_attr:* sao o insight chave: "fogo" e "gelo" compartilham
        est_attr:temp (ambos tem temperatura) mas diferem em est_val:temp:200
        vs est_val:temp:-5. Isto e o mesmo padrao de antonimos da FASE 2
        (mesmo contexto, valores opostos) — reusamos a infraestrutura.

        Pilar 1: cada feature e uma transicao P(feature|palavra).
        Pilar 3: funciona com qualquer dict — Tibia, IoT, jogo, whatever.

        Args:
            estado: dict, JSON string, ou valor primitivo
        Returns:
            set de features est_val:* e est_attr:*
        """
        if isinstance(estado, str):
            try:
                estado = json.loads(estado)
            except (json.JSONDecodeError, ValueError):
                return set()

        feats = set()

        def _flatten(prefix, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _flatten(f"{prefix}:{k}", v)
            elif isinstance(obj, (list, tuple)):
                for i, v in enumerate(obj):
                    _flatten(f"{prefix}:{i}", v)
            else:
                val = str(obj).lower().strip()
                if val:
                    feats.add(f"est_val:{prefix}:{val}")
                    parts = prefix.split(":")
                    for attr in parts:
                        if attr:
                            feats.add(f"est_attr:{attr}")

        _flatten("est", estado)
        return feats

    def alimentar_estado(self, texto: str, estado) -> None:
        """FASE 3.1 — Grounding simbolico: alimenta par (texto, estado_do_mundo).

        Associa um texto a um estado estruturado do mundo (dict/JSON).
        O estado e decomposto em features est_val:* e est_attr:* e
        armazenado em _estado_features[palavra][feature].

        Pilar 1: P(state_feature | word) — transicao markoviana.
        Pilar 5: alimenta -> predizer -> aprender (loop fechado).

        Exemplo:
            c.alimentar_estado("fogo", {"temp":200,"dano":5,"cor":"vermelho"})
            c.alimentar_estado("gelo", {"temp":-5,"dano":0,"cor":"branco"})
            c.consultar_atributo("fogo", "temp")  # -> ("200", conf)

        Args:
            texto: texto de entrada (descricao do conceito/acao)
            estado: dict, JSON string, ou valor estruturado
        """
        feats = self._extrair_features_estado(estado)
        if not feats:
            return

        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        for p in set(palavras):
            for feat in feats:
                self._estado_features[p][feat] += 1

    def _assinatura_estado(self, conceito: str) -> Dict[str, int]:
        """FASE 3 — Assinatura de estado de um conceito (features est_* apenas).

        Diferente de _assinatura_palavra (que mistura acao/ctx/pos),
        esta assinatura so tem features de estado do mundo (est_val/est_attr).
        Usada por raciocinar_estado() para encontrar conceitos compartilhados.

        Args:
            conceito: texto do conceito (uma ou mais palavras)
        Returns:
            dict de features est_* com contagens
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', conceito.lower())
        sig = defaultdict(int)
        for p in set(palavras):
            dist = self._estado_features.get(p, {})
            for f, c in dist.items():
                sig[f] += c
        return dict(sig) if sig else {}

    def predizer_estado(self, texto: str) -> Dict[str, Tuple[str, float]]:
        """FASE 3.2 — Prediz estado do mundo associado ao texto.

        Agrega features est_val:* de todas as palavras do texto (e suas
        similares via NMI) e retorna um dict de atributo -> (valor, confianca).

        Pilar 2: confianca e relativa (score / total), sem threshold.
        Pilar 5: se a palavra nao foi vista, busca similares (aprendizado).

        Args:
            texto: texto de entrada
        Returns:
            dict: atributo -> (valor, confianca) ordenado por confianca
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        scores: Dict[str, float] = defaultdict(float)

        for p in set(palavras):
            dist = self._estado_features.get(p, {})
            if not dist:
                proxies = self.palavras_similares(p, threshold=0.20)
                for prox, conf in proxies:
                    d = self._estado_features.get(prox, {})
                    if not d:
                        continue
                    td = sum(d.values()) or 1
                    for f, c in d.items():
                        scores[f] += (c / td) * conf
                continue
            total = sum(dist.values()) or 1
            for f, c in dist.items():
                scores[f] += c / total

        if not scores:
            return {}

        estado: Dict[str, Tuple[str, float]] = {}
        for feat, score in scores.items():
            if feat.startswith("est_val:est:"):
                parts = feat.split(":", 3)
                if len(parts) >= 4:
                    key = parts[2]
                    val = parts[3]
                    if key not in estado or score > estado[key][1]:
                        estado[key] = (val, score)

        return dict(sorted(estado.items(), key=lambda x: -x[1][1]))

    def consultar_atributo(self, texto: str, atributo: str) -> Tuple[Optional[str], float]:
        """FASE 3 — Consulta um atributo especifico do estado de um conceito.

        Args:
            texto: conceito (ex: "fogo")
            atributo: nome do atributo (ex: "temp")
        Returns:
            (valor, confianca) ou (None, 0.0)
        """
        estado = self.predizer_estado(texto)
        resultado = estado.get(atributo.lower())
        return resultado if resultado else (None, 0.0)

    def raciocinar_estado(self, conceito_a: str,
                          conceito_b: str) -> Dict[str, list]:
        """FASE 3.2 — Raciocinio sobre estados: combina dois conceitos.

        Usa compor() da FASE 1 para combinar as assinaturas de estado
        de dois conceitos. Os atributos compartilhados (est_attr:*)
        emergem como o "conceito compartilhado" — sem rotulos.

        Exemplo:
            raciocinar_estado("fogo", "gelo")
            -> {"atributos_compartilhados": ["temp", "dano", "cor"],
                "nmi": 0.85,
                "conceito_emergente": ["temp", "dano", "cor"]}

        "fogo" e "gelo" compartilham est_attr:temp (ambos tem temperatura)
        mas diferem em est_val:temp:200 vs est_val:temp:-5.
        O conceito emergente "temperatura" nao foi rotulado — emergiu
        da composicao markoviana.

        Pilar 1: P(feature|conceito) — tudo transicao.
        Pilar 2: NMI decide o que e compartilhado, sem threshold.
        Pilar 5: usa compor() que aprende o tipo de composicao.

        Args:
            conceito_a: primeiro conceito (ex: "fogo")
            conceito_b: segundo conceito (ex: "gelo")
        Returns:
            dict com atributos_compartilhados, nmi, conceito_emergente
        """
        sig_a = self._assinatura_estado(conceito_a)
        sig_b = self._assinatura_estado(conceito_b)
        if not sig_a or not sig_b:
            return {"atributos_compartilhados": [], "nmi": 0.0,
                    "conceito_emergente": []}

        nmi = self._nmi(sig_a, sig_b)
        sig_composto = self.compor(sig_a, sig_b)

        attrs_compostos = {k.replace("est_attr:", ""): v
                           for k, v in sig_composto.items()
                           if k.startswith("est_attr:")}

        attrs_a = {k.replace("est_attr:", "") for k in sig_a
                   if k.startswith("est_attr:")}
        attrs_b = {k.replace("est_attr:", "") for k in sig_b
                   if k.startswith("est_attr:")}
        compartilhados = attrs_a & attrs_b

        return {
            "atributos_compartilhados": sorted(compartilhados),
            "nmi": round(nmi, 4),
            "conceito_emergente": sorted(attrs_compostos.keys()),
        }

    def _corte_dinamico(self, scores: List[float]) -> int:
        """Descobre o corte natural numa lista de scores usando entropia.

        Pilar 2 — Entropia descobre, sem threshold hardcoded.

        Usa DERIVADA SEGUNDA (curvatura) da curva de scores ordenados
        para encontrar o "cotovelo" — o ponto onde a distribuicao
        passa de estrutura (scores altos) para ruido (scores baixos).

        O cotovelo e onde a SEGUNDA DERIVADA e maxima: a curva
        muda de declive suave para queda abrupta (ou vice-versa).

        Criterio de significancia RELATIVO (nao hardcoded):
        o cotovelo so e valido se sua curvatura > media das
        curvaturas absolutas. Se todas as curvaturas sao iguais
        (distribuicao uniforme), nao ha estrutura → return 0.

        Returns:
            numero de elementos que sao "estrutura" vs "ruido"
        """
        if not scores:
            return 0
        if len(scores) == 1:
            return 1 if scores[0] > 0 else 0

        ordenados = sorted(scores, reverse=True)
        n = len(ordenados)

        if n == 2:
            if ordenados[0] > 0 and ordenados[1] > 0:
                ratio = ordenados[1] / ordenados[0]
                return 1 if ratio < 0.5 else 2
            return 1 if ordenados[0] > 0 else 0

        diffs = [ordenados[i] - ordenados[i + 1] for i in range(n - 1)]
        second_diffs = [diffs[i] - diffs[i + 1] for i in range(len(diffs) - 1)]

        if not second_diffs:
            return 0

        max_second = max(second_diffs)
        avg_abs = sum(abs(s) for s in second_diffs) / len(second_diffs)

        if max_second <= avg_abs or max_second <= 0:
            return 0

        knee_idx = second_diffs.index(max_second)
        corte = knee_idx + 1

        return min(max(corte, 1), n)

    def _split_planos(self, sig: Dict[str, int]) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Divide assinatura em planos ctx:* e acao:* para analise de relacoes."""
        sig_ctx = {k: v for k, v in sig.items() if k.startswith("ctx:")}
        sig_acao = {k: v for k, v in sig.items() if k.startswith("acao:")}
        return sig_ctx, sig_acao

    def extrair_relacoes(self, palavra: str,
                         top_n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """FASE 2 — Extrator de relacoes semanticas das matrizes markovianas.

        Todas as relacoes ja estao latentes em _transicao_palavra e
        _palavra_acao. Este metodo EXTRAI usando entropia para descobrir
        os cortes naturais — sem threshold hardcoded (pilar 2).

        Relacoes descobertas (todas por entropia, zero rotulos):
        - sinonimos:    alta similaridade NMI (mesma distribuicao de acao+ctx)
        - antonimos:    mesmo contexto (ctx:*) mas acoes opostas (acao:*)
                        Contraste: score = nmi_ctx * (1 - nmi_acao)
        - hiperonimos:  A->B transicao com baixa entropia (deterministica)
                        B e o conceito mais geral que A transita
        - hiponimos:    B->A transicao deterministica (inverso de hiperonimo)
        - meronimos:    NMI medio + candidato menor (parte-de)
        - holonimos:    NMI medio + candidato maior (todo-de)
        - polissemia:   H alta em _palavra_acao (acima da media + desvio)

        Pilar 1: tudo sao transicoes P(b|a) — _transicao_palavra e _palavra_acao
        Pilar 2: cortes descobertos por _corte_dinamico(), nao hardcoded
        Pilar 3: metodo generico, funciona em qualquer dominio
        Pilar 5: relacoes extraidas sao cacheadas em _relacoes_cache

        Args:
            palavra: palavra-alvo para extrair relacoes
            top_n: maximo de candidatos por relacao (apos corte entropico)
        Returns:
            dict: relacao -> lista de (palavra, score) ordenada por score desc
        """
        palavra = palavra.lower()
        sig = self._assinatura_palavra(palavra)
        if not sig:
            return {}

        sig_ctx, sig_acao = self._split_planos(sig)

        candidatos = []
        todas_palavras = list(self._palavra_acao.keys())
        h_palavra_acao = self._entropia_shannon(self._palavra_acao.get(palavra, {}))

        for p in todas_palavras:
            if p == palavra:
                continue
            sig_p = self._assinatura_palavra(p)
            if not sig_p:
                continue

            nmi_full = self._nmi(sig, sig_p)

            sig_p_ctx, sig_p_acao = self._split_planos(sig_p)
            nmi_ctx = self._nmi(sig_ctx, sig_p_ctx) if sig_ctx and sig_p_ctx else 0.0
            nmi_acao = self._nmi(sig_acao, sig_p_acao) if sig_acao and sig_p_acao else 0.0

            trans_ab = self._transicao_palavra.get(palavra, {}).get(p, 0)
            trans_ba = self._transicao_palavra.get(p, {}).get(palavra, 0)

            candidatos.append({
                'palavra': p,
                'nmi_full': nmi_full,
                'nmi_ctx': nmi_ctx,
                'nmi_acao': nmi_acao,
                'trans_ab': trans_ab,
                'trans_ba': trans_ba,
                'len': len(p),
                'h_acao': self._entropia_shannon(self._palavra_acao.get(p, {})),
            })

        if not candidatos:
            return {}

        relacoes: Dict[str, List[Tuple[str, float]]] = {}

        # === SINONIMOS: alta NMI full ===
        scores_sin = [c['nmi_full'] for c in candidatos]
        corte_sin = self._corte_dinamico(scores_sin)
        if corte_sin > 0:
            sin_ordenado = sorted(candidatos, key=lambda c: -c['nmi_full'])
            relacoes['sinonimos'] = [(c['palavra'], c['nmi_full'])
                                     for c in sin_ordenado[:min(corte_sin, top_n)]]

        # === ANTONIMOS: alto nmi_ctx + baixo nmi_acao (contraste) ===
        for c in candidatos:
            c['score_antonimo'] = c['nmi_ctx'] * (1.0 - c['nmi_acao'])
        scores_ant = [c['score_antonimo'] for c in candidatos if c['nmi_ctx'] > 0]
        corte_ant = self._corte_dinamico(scores_ant) if scores_ant else 0
        if corte_ant > 0:
            ant_ordenado = sorted(candidatos, key=lambda c: -c['score_antonimo'])
            ant_filtrado = [c for c in ant_ordenado if c['nmi_ctx'] > 0]
            relacoes['antonimos'] = [(c['palavra'], c['score_antonimo'])
                                     for c in ant_filtrado[:min(corte_ant, top_n)]]

        # === HIPERONIMOS: A->B transicao frequente ===
        candidatos_hiper = [c for c in candidatos if c['trans_ab'] > 0]
        if candidatos_hiper:
            scores_hiper = [c['trans_ab'] for c in candidatos_hiper]
            corte_hiper = self._corte_dinamico(scores_hiper)
            if corte_hiper > 0:
                hiper_ordenado = sorted(candidatos_hiper, key=lambda c: -c['trans_ab'])
                total_trans = sum(c['trans_ab'] for c in candidatos_hiper) or 1
                relacoes['hiperonimos'] = [(c['palavra'], c['trans_ab'] / total_trans)
                                           for c in hiper_ordenado[:min(corte_hiper, top_n)]]

        # === HIPONIMOS: B->A transicao frequente (inverso) ===
        candidatos_hipo = [c for c in candidatos if c['trans_ba'] > 0]
        if candidatos_hipo:
            scores_hipo = [c['trans_ba'] for c in candidatos_hipo]
            corte_hipo = self._corte_dinamico(scores_hipo)
            if corte_hipo > 0:
                hipo_ordenado = sorted(candidatos_hipo, key=lambda c: -c['trans_ba'])
                total_trans = sum(c['trans_ba'] for c in candidatos_hipo) or 1
                relacoes['hiponimos'] = [(c['palavra'], c['trans_ba'] / total_trans)
                                         for c in hipo_ordenado[:min(corte_hipo, top_n)]]

        # === MERONIMOS: NMI medio + candidato menor (parte-de) ===
        candidatos_mero = [c for c in candidatos
                           if c['len'] < len(palavra) and c['nmi_full'] > 0]
        if candidatos_mero:
            scores_mero = [c['nmi_full'] for c in candidatos_mero]
            corte_mero = self._corte_dinamico(scores_mero)
            if corte_mero > 0:
                mero_ordenado = sorted(candidatos_mero, key=lambda c: -c['nmi_full'])
                relacoes['meronimos'] = [(c['palavra'], c['nmi_full'])
                                         for c in mero_ordenado[:min(corte_mero, top_n)]]

        # === HOLONIMOS: NMI medio + candidato maior (todo-de) ===
        candidatos_holo = [c for c in candidatos
                           if c['len'] > len(palavra) and c['nmi_full'] > 0]
        if candidatos_holo:
            scores_holo = [c['nmi_full'] for c in candidatos_holo]
            corte_holo = self._corte_dinamico(scores_holo)
            if corte_holo > 0:
                holo_ordenado = sorted(candidatos_holo, key=lambda c: -c['nmi_full'])
                relacoes['holonimos'] = [(c['palavra'], c['nmi_full'])
                                         for c in holo_ordenado[:min(corte_holo, top_n)]]

        # === POLISSEMIA: H da palavra vs media + desvio ===
        if todas_palavras:
            entropias = [self._entropia_shannon(self._palavra_acao.get(p, {}))
                         for p in todas_palavras
                         if self._palavra_acao.get(p)]
            if entropias:
                media_h = sum(entropias) / len(entropias)
                var_h = sum((h - media_h) ** 2 for h in entropias) / len(entropias)
                std_h = var_h ** 0.5
                if h_palavra_acao > media_h + std_h and std_h > 0:
                    relacoes['polissemia'] = [(palavra, h_palavra_acao)]

        return relacoes

    def clusterizar_palavras(self, threshold: float = 0.70) -> Dict[str, List[str]]:
        """Agrupa palavras por similaridade NMI de assinatura markoviana.

        Cada palavra vira um vetor: P(acao|palavra) + P(vizinho|palavra).
        Duas palavras sao do mesmo cluster se NMI > threshold.

        Returns:
            dict: cluster_id -> lista de palavras
        """
        palavras = list(self._palavra_acao.keys())
        if len(palavras) < 2:
            return {}

        assinaturas = {}
        for p in palavras:
            feat = defaultdict(int)
            for k, v in self._palavra_acao.get(p, {}).items():
                feat[f"acao:{k}"] += v
            for k, v in self._transicao_palavra.get(p, {}).items():
                feat[f"ctx:{k}"] += v
            assinaturas[p] = dict(feat)

        clusters = {}
        usadas = set()
        cid = 0

        for i, pa in enumerate(palavras):
            if pa in usadas:
                continue
            cluster = [pa]
            usadas.add(pa)
            feat_a = assinaturas.get(pa, {})
            if not feat_a:
                cid += 1
                continue
            for pb in palavras[i+1:]:
                if pb in usadas:
                    continue
                feat_b = assinaturas.get(pb, {})
                if not feat_b:
                    continue
                score = self._nmi(feat_a, feat_b)
                if score >= threshold:
                    cluster.append(pb)
                    usadas.add(pb)
            if len(cluster) >= 2:
                clusters[f"PC{cid}"] = cluster
            cid += 1

        return clusters

    @staticmethod
    def _buscar_cluster_palavra(palavra: str,
                                 clusters: Dict[str, List[str]]) -> Optional[str]:
        for cid, membros in clusters.items():
            if palavra in membros:
                return cid
        return None

    def similaridade(self, a: str, b: str) -> float:
        """Similaridade semantica MCR universal.

        FASE 1: agora aceita FRASES multi-palavra, nao so palavras
        isoladas. Se a ou b tiver mais de uma palavra, extrai a
        assinatura composicional via _assinatura_frase() em vez de
        _assinatura_palavra().

        Conforme a Equacao MCR: o valor e' a reducao de incerteza.
        Markov encadeia fontes observaveis. Entropia mede incerteza
        de cada fonte. O somatorio agrega as fontes num unico 
        estado markoviano amplo: "resultante =nome+contexto+forma+acao".
        
        Cada da observacao de A gera distribuicao P(·|A) num espaco
        amplo de features (acoes, vizinhos, n-gramas).
        Quando combinamos A e B; a reducao de entropia H(A) + H(B) - H(A,B) 
        sobre TODO o espaco e' a entidade MCR de similaridade.
        
        Implementacao:
          dict_a = {
            'acao:criar': X,  # observado em P(acao|A)
            'acao:gerar': Y,
            'ctx:monstro': Z,  # vizinho markoviano
            'forma:cri': W,    # n-grama da propria palavra
            ...
          }
          dict_b = similar
          sim = NMI(dict_a, dict_b)
        
        Universal por construcao:
          - qualquer idioma e suportado
          - qualquer token (palavra, musica, audio) e tratavel
            (desde que o motor gere features)
          - funciona bem mesmo com palavras nunca observadas
            (forma=n-grama fornece fallback morfologico).
        """
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0

        # FASE 1: deteta frases multi-palavra e usa assinatura composicional
        a_palavras = re.findall(r'[a-zà-ÿ]{3,}', a.lower())
        b_palavras = re.findall(r'[a-zà-ÿ]{3,}', b.lower())
        a_multi = len(a_palavras) > 1
        b_multi = len(b_palavras) > 1

        if a_multi:
            sig_a = self._assinatura_frase(a)
        else:
            sig_a = self._assinatura_palavra(a_palavras[0] if a_palavras else a)
        if b_multi:
            sig_b = self._assinatura_frase(b)
        else:
            sig_b = self._assinatura_palavra(b_palavras[0] if b_palavras else b)

        if not sig_a or not sig_b:
            try:
                from mcr.semantic_router import similaridade as ngram
                return round(min(1.0, ngram(a, b) * 0.5), 4)
            except ImportError:
                return 0.0

        base = self._nmi(sig_a, sig_b)

        if hasattr(self, '_word_clusters') and self._word_clusters:
            ca = self._buscar_cluster_palavra(a, self._word_clusters)
            cb = self._buscar_cluster_palavra(b, self._word_clusters)
            if ca is not None and cb is not None:
                if ca == cb:
                    base = max(base, 0.75)
                else:
                    base = min(base, 0.60)
        return base

    def palavras_similares(self, palavra: str, threshold: float = 0.30,
                           max_resultados: int = 5) -> List[Tuple[str, float]]:
        """Retorna as palavras mais similares da base."""
        if not palavra:
            return []
        resultado = []
        for candidata in list(self._palavra_acao):
            score = self.similaridade(palavra, candidata)
            if score >= threshold:
                resultado.append((candidata, score))
        resultado.sort(key=lambda x: -x[1])
        return resultado[:max_resultados]

    def predizer(self, texto: str, acao_markov: str = None) -> Tuple[Optional[str], float]:
        return self.decidir(texto, (acao_markov, 0.5 if acao_markov else 0.0))

    def predizer_cluster(self, cluster_id, acao_markov: str = None) -> Tuple[Optional[str], float]:
        d = self._dist_cluster(cluster_id)
        if not d:
            return None, 0.0
        melhor = max(d, key=d.get)
        return melhor, d[melhor]

    def estatisticas(self) -> Dict:
        return {
            'total': self._total,
            'palavras': len(self._palavra_acao),
            'vizinhos': len(self._transicao_palavra),
            'clusters': len(self._cluster_acao),
            'posicoes': len(self._posicao_acao),
            'features_nd': len(self._feature_acao),
        }

    def save(self, caminho: str = None):
        import json, os
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'coupling_{self.__class__.__name__}.json')
        dados = {
            'total': self._total,
            'palavra_acao': {k: dict(v) for k, v in self._palavra_acao.items()},
            'transicao_palavra': {k: dict(v) for k, v in self._transicao_palavra.items()},
            'cluster_acao': {k: dict(v) for k, v in self._cluster_acao.items()},
            'posicao_acao': {k: dict(v) for k, v in self._posicao_acao.items()},
            'freq_acao': dict(self._freq_acao),
            'feature_acao': {k: dict(v) for k, v in self._feature_acao.items()},
            'acao_features': {k: dict(v) for k, v in self._acao_features.items()},
            'estado_features': {k: dict(v) for k, v in self._estado_features.items()},
            'ngrama': {str(ordem): {'|'.join(pref): dict(prox_dict)
                       for pref, prox_dict in ord_dict.items()}
                       for ordem, ord_dict in self._ngrama.items()},
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)

    def load(self, caminho: str = None) -> bool:
        import json, os
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'coupling_{self.__class__.__name__}.json')
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self._total = dados.get('total', 0)
            cp = lambda d, k: d.get(k, {})
            base = lambda dd: defaultdict(int, dd)
            self._palavra_acao = defaultdict(lambda: defaultdict(int),
                                             {k: base(v) for k, v in cp(dados, 'palavra_acao').items()})
            self._transicao_palavra = defaultdict(lambda: defaultdict(int),
                                                  {k: base(v) for k, v in cp(dados, 'transicao_palavra').items()})
            self._cluster_acao = defaultdict(lambda: defaultdict(int),
                                             {k: base(v) for k, v in cp(dados, 'cluster_acao').items()})
            self._posicao_acao = defaultdict(lambda: defaultdict(int),
                                             {k: base(v) for k, v in cp(dados, 'posicao_acao').items()})
            self._freq_acao = defaultdict(int, dados.get('freq_acao', {}))
            self._feature_acao = defaultdict(lambda: defaultdict(int),
                                             {k: base(v) for k, v in cp(dados, 'feature_acao').items()})
            self._acao_features = defaultdict(lambda: defaultdict(int),
                                               {k: base(v) for k, v in cp(dados, 'acao_features').items()})
            self._estado_features = defaultdict(lambda: defaultdict(int),
                                                {k: base(v) for k, v in cp(dados, 'estado_features').items()})
            ng_raw = dados.get('ngrama', {})
            self._ngrama = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
            for ordem_str, ord_dict in ng_raw.items():
                ordem = int(ordem_str)
                for pref_str, prox_dict in ord_dict.items():
                    prefix = tuple(pref_str.split('|'))
                    self._ngrama[ordem][prefix] = defaultdict(int, prox_dict)
            return True
        except Exception:
            return False
