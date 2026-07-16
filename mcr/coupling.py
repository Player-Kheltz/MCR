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
import re, math


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
        """Information Mutua Normalizada - implementacao MCR pura.

        MCR: duas entidades sao similares SE combinadas reduzem a
        incerteza sobre o proximo estado da cadeia markoviana.

        I(a;b) = H(a) + H(b) - H(a,b)
        sim(a,b) = I(a;b) / max(H(a), H(b))  IN [0, 1]

        Nao usa cosseno, SVD, distancia - so Markov+Entropia.
        Retorna 0 se nao ha informacao compartilhada.
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

        sig_a = self._assinatura_palavra(a)
        sig_b = self._assinatura_palavra(b)

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
