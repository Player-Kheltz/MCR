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
from typing import Dict, List, Tuple, Optional, Any
import re, math, json, random, os

# Novas fontes de decisão (FASE 7+)
from mcr.context_buffer import ContextBuffer
from mcr.episodic_gateway import EpisodicGateway

# Janela de cache para estatisticas de entropia (_todas_h_norm_*).
# A janela e ADAPTATIVA: se o vocabulario cresceu muito (novas palavras),
# recalcular imediatamente. Se nao mudou (estavel), pode esperar.
# Sem janela, o cache invalida a cada alimentar() (_total += 1),
# forcando recalculo sobre TODO o vocabulario (62K+ palavras) a cada
# frase — O(P) por frase = O(n²). Com janela, O(P) so a cada JANELA
# frases.
_CACHE_H_JANELA = 200

# Regexes pré-compilados para _extrair_features_nd (chamado a cada alimentar).
# Sem pré-compilação, re.compile() é chamado implicitamente a cada findall.
_RE_TOKENS = re.compile(r'[a-zà-ÿ0-9]{2,}')
_RE_TOKENS_LIMPO = re.compile(r'[a-zà-ÿ]{3,}')
_RE_CHARS = re.compile(r'[^a-z0-9]')


def _worker_ingerir(chunk):
    """Worker top-level para multiprocessing — ingere um chunk e retorna estado.

    Esta função DEVE ser top-level (não método) porque multiprocessing
    no Windows usa spawn, que requiere funções picklable top-level.

    Cria um MCRCoupling temporário, ingere o chunk, e serializa o estado
    para um dict simples (sem defaultdicts — compatível com pickle).
    """
    from mcr.coupling import MCRCoupling
    c = MCRCoupling()
    c.alimentar_lote(chunk)
    return {
        'total': c._total,
        'palavra_acao': {k: dict(v) for k, v in c._palavra_acao.items()},
        'transicao_palavra': {k: dict(v) for k, v in c._transicao_palavra.items()},
        'posicao_acao': {k: dict(v) for k, v in c._posicao_acao.items()},
        'feature_acao': {k: dict(v) for k, v in c._feature_acao.items()},
        'acao_features': {k: dict(v) for k, v in c._acao_features.items()},
        'freq_acao': dict(c._freq_acao),
        'cluster_acao': {k: dict(v) for k, v in c._cluster_acao.items()},
        'estado_features': {k: dict(v) for k, v in c._estado_features.items()},
        'trigrama_acao': {k: dict(v) for k, v in c._trigrama_acao.items()},
        'padrao_acao': {k: dict(v) for k, v in c._padrao_acao.items()},
        'ngrama': {str(ordem): {'|'.join(pref): dict(prox_dict)
                   for pref, prox_dict in ord_dict.items()}
                   for ordem, ord_dict in c._ngrama.items()},
    }


class MCRCoupling:

    _hierarquia_feed_emCurso = False  # anti-recursão (flag de classe)

    def __init__(self):
        self._palavra_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._transicao_palavra: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._cluster_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._posicao_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._feature_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._acao_features: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._ngrama: Dict[int, Dict[tuple, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int)))
        self._trigrama_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._padrao_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._total = 0
        self._freq_acao: Dict[str, int] = defaultdict(int)
        self._composicoes_aprendidas: Dict[tuple, str] = {}
        self._estado_features: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # #19 — Pesos aprendidos por fonte (MCRPesoNota)
        self._pesos_fonte: Dict[str, float] = {}
        # #20 — Threshold adaptativo (MCRThreshold)
        self._threshold_adpt: float = 0.5
        self._confiancas_observadas: List[float] = []
        # #21 — Pesos dinamicos por categoria (MCRPeso)
        self._peso_categoria: Dict[str, Dict[str, float]] = defaultdict(dict)
        # Thresholds entrópicos (aprendidos dos dados, nunca hardcoded)
        self._cache_thresholds: Dict[str, float] = {}
        self._mediana_comp: int = 0  # 0 = sem dados (aprendido em alimentar)
        # === FASE 7+ — Novas fontes de decisão ===
        self._context_buffer: Optional[ContextBuffer] = None
        self._episodic_gateway: Optional[EpisodicGateway] = None
        self._em_branch: bool = False  # anti-recursão no branch search
        self._contexto_ativo: bool = False  # buffer opt-in (conversacional)
        # === FASE 10 — Meta-cognição ===
        self._meta: Optional[Any] = None
        self._meta_ativo: bool = False  # opt-in (não afeta classificação)
        # === FASE 20 — Hierarquia multi-escala ===
        self._hierarquia: Optional[Any] = None  # MCRHierarquico (lazy init)
        self._em_hierarquia: bool = False  # anti-recursão
        # === FASE 20 — Triunvirato (busca ativa) ===
        self._deliberacao: Optional[Any] = None  # Deliberacao (lazy init)

    def _threshold_entropico(self, chave: str, valores: List[float]) -> float:
        """Computa threshold dinâmico via mediana (MCRThreshold).
        Pilar 2: entropia descobre, thresholds nao sao hardcoded."""
        if not valores:
            return self._cache_thresholds.get(chave, 0.5)
        ord_ = sorted(valores)
        mediana = ord_[len(ord_) // 2]
        self._cache_thresholds[chave] = mediana
        return mediana

    def _h_norm_posicao(self, pos: int, palavra: str) -> float:
        """H normalizada de uma palavra numa posicao. Retorna -1 se sem dados."""
        dist = self._posicao_acao.get(f"P{pos}:{palavra[:10]}", {})
        total = sum(dist.values())
        if total < 2:
            return -1.0
        h = 0.0
        for c in dist.values():
            pr = c / total
            if pr > 0: h -= pr * math.log2(pr)
        max_h = math.log2(max(len(dist), 2))
        return h / max_h if max_h > 0 else 0.0

    def _todas_h_norm_p0(self) -> List[float]:
        """Todas as H normalizadas de palavras em P0 com >=2 amostras.

        Cacheado por janela adaptativa (geração + n_palavras).
        Otimizacao: em vez de iterar TODO _posicao_acao com startswith
        para filtrar P0 (O(P) por chamada, 6M startswith em 2K frases),
        mantem um indice _p0_chaves que e so as chaves P0:* reconstruido
        quando _posicao_acao muda de tamanho. O(P0) em vez de O(todas).
        Nao checa n_pos no cache — uma nova chave P0 nao muda a mediana
        significativamente, e checar n_pos invalidava o cache quase
        toda frase com corpus real (62K palavras).
        """
        n_palavras = len(self._palavra_acao)
        n_pos = len(self._posicao_acao)
        gen = self._total // _CACHE_H_JANELA
        # Reconstruir indice de chaves P0 se o tamanho de _posicao_acao mudou
        if (not hasattr(self, '_p0_chaves_npos') or self._p0_chaves_npos != n_pos):
            self._p0_chaves = [k for k in self._posicao_acao if k.startswith('P0:')]
            self._p0_chaves_npos = n_pos
        if (hasattr(self, '_cache_h_p0_gen') and self._cache_h_p0_gen == gen
                and hasattr(self, '_cache_h_p0_npal') and n_palavras == self._cache_h_p0_npal):
            return self._cache_h_p0
        resultados = []
        for chave in self._p0_chaves:
            dist = self._posicao_acao[chave]
            total = sum(dist.values())
            if total < 2:
                continue
            h = 0.0
            for c in dist.values():
                pr = c / total
                if pr > 0: h -= pr * math.log2(pr)
            max_h = math.log2(max(len(dist), 2))
            resultados.append(h / max_h if max_h > 0 else 0.0)
        self._cache_h_p0 = resultados
        self._cache_h_p0_gen = gen
        self._cache_h_p0_npal = n_palavras
        return resultados

    def _todas_h_norm_palavras(self) -> List[float]:
        """Todas as H normalizadas de palavras com >=2 amostras.

        Cacheado por janela adaptativa: so recalcula a cada _CACHE_H_JANELA
        alimentacoes OU se o numero de palavras no vocabulario mudou.
        Para datasets pequenos (449 frases), invalida a cada nova palavra
        (precisao total). Para Wikipedia (37K frases, 62K palavras),
        so recalcula a cada 200 frases (200x mais rapido).
        """
        gen = self._total // _CACHE_H_JANELA
        n_palavras = len(self._palavra_acao)
        if (hasattr(self, '_cache_h_pal_gen') and self._cache_h_pal_gen == gen
                and hasattr(self, '_cache_h_pal_npal') and n_palavras == self._cache_h_pal_npal):
            return self._cache_h_pal
        resultados = []
        for palavra, dist in self._palavra_acao.items():
            total = sum(dist.values())
            if total < 2:
                continue
            h = 0.0
            for c in dist.values():
                pr = c / total
                if pr > 0: h -= pr * math.log2(pr)
            max_h = math.log2(max(len(dist), 2))
            resultados.append(h / max_h if max_h > 0 else 0.0)
        self._cache_h_pal = resultados
        self._cache_h_pal_gen = gen
        self._cache_h_pal_npal = n_palavras
        return resultados

    def _extrair_features_nd(self, texto: str, acao: str):
        """Extrai features N-dimensionais do texto e associa a acao.

        Preenche:
          _feature_acao[feature][acao] += 1  (feature→acao)
          _acao_features[acao][feature] += 1  (acao→feature, inverso)

        Planos (10):
          t:{token}        — palavra inteira
          c:{char}         — caractere
          b:{byte}         — byte
          bg:{bigram}      — bigrama de char
          ng:{trigram}     — trigrama de char
          p{i}:{token}     — posicao no texto (primeiros 6)
          ca:{token}       — contexto ANTES
          cd:{token}       — contexto DEPOIS
          sl:{silaba}      — silaba (separacao por vogais)
          ngp:{bigram_pal} — bigrama de palavras adjacentes
        """
        texto = str(texto)
        acao = str(acao)
        raw = texto.lower()

        feats = set()

        # Token level
        tokens = _RE_TOKENS.findall(raw)
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
        chars = _RE_CHARS.sub('', raw)
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

        # Silaba: separacao por vogais (padrao estatistico de chars, nao regra de dominio)
        vogais = set('aeiouàáéíóúâêôãõ')
        for t in tokens:
            if len(t) < 4:
                continue
            silabas = []
            atual = ''
            for ch in t:
                atual += ch
                if ch in vogais:
                    silabas.append(atual)
                    atual = ''
            if atual:
                silabas.append(atual)
            for sl in silabas:
                if len(sl) >= 2:
                    feats.add(f"sl:{sl}")

        # Bigrama de palavras adjacentes — derivar do primeiro findall
        # (antes era segundo findall redundante com pattern [a-zà-ÿ]{3,})
        tokens_limpos = [t for t in tokens if len(t) >= 3]
        for i in range(len(tokens_limpos) - 1):
            feats.add(f"ngp:{tokens_limpos[i]}+{tokens_limpos[i+1]}")

        # Populate both indexes
        acao_idx = self._acao_features[acao]
        for feat in feats:
            self._feature_acao[feat][acao] += 1
            acao_idx[feat] = acao_idx.get(feat, 0) + 1

    def alimentar(self, texto: str, acao: str):
        self._total += 1
        acao = str(acao)
        self._freq_acao[acao] += 1

        # FASE 7+ — Atualiza buffer de contexto (atenção temporal)
        buf = self._inic_context_buffer()
        buf.adicionar(texto)

        # FASE 20 — Hierarquia: alimenta camadas multi-escala
        # Skip durante alimentar_lote para evitar O(n²): a hierarquia
        # chama _assinatura_frase -> _avaliar_composicao que itera sobre
        # TODO o vocabulario. Reconstruida no final do lote.
        if not MCRCoupling._hierarquia_feed_emCurso and not getattr(self, '_skip_hierarquia', False):
            if self._hierarquia is None:
                from mcr.acoplamento_hierarquico import MCRHierarquico
                self._hierarquia = MCRHierarquico(max_niveis=5, min_delta_h=0.05)
            MCRCoupling._hierarquia_feed_emCurso = True
            try:
                self._hierarquia.alimentar(texto, acao)
            finally:
                MCRCoupling._hierarquia_feed_emCurso = False

        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        for p in set(palavras):
            self._palavra_acao[p][acao] += 1

        partes = texto.replace('_', ' ').lower().split()
        for i, p in enumerate(partes[:6]):
            self._posicao_acao[f"P{i}:{p[:10]}"][acao] += 1
        # Aprender mediana de comprimento das frases (para categorizacao)
        # Otimizacao: reservatório amostral fixo de 200 (em vez de crescer
        # infinitamente). Antes, sorted(_comps_acumulados) era chamado a
        # cada 20 frases sobre uma lista que cresce com _total — O(n² log n)
        # cumulativo. Com reservatório fixo, cada sort é O(200 log 200) = O(1).
        self._comps_acumulados: List[int] = getattr(self, '_comps_acumulados', [])
        self._comps_count: int = getattr(self, '_comps_count', 0)
        self._comps_count += 1
        if len(self._comps_acumulados) < 200:
            self._comps_acumulados.append(len(partes))
        else:
            # Reservatório: substituir posição aleatória com prob decrescente
            idx = random.randint(0, self._comps_count - 1)
            if idx < 200:
                self._comps_acumulados[idx] = len(partes)
        if len(self._comps_acumulados) >= 20 and self._comps_count % 50 == 0:
            comps_ord = sorted(self._comps_acumulados)
            self._mediana_comp = comps_ord[len(comps_ord) // 2]

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

        # Trigramas de chars: P(acao|tri_char) — fonte T
        chars = re.sub(r'[^a-z0-9]', '', texto.lower())
        for i in range(len(chars) - 2):
            tri = chars[i:i+3]
            self._trigrama_acao[tri][acao] += 1

        # Padrao estrutural: P(acao|VCS) — fonte PT
        # Classifica cada posicao por entropia de _posicao_acao:
        #   H baixa = verbo (V), H alta = conector (C), H media = substantivo (S)
        padrao = self._classificar_padrao(partes)
        if padrao:
            self._padrao_acao[padrao][acao] += 1

        self._extrair_features_nd(texto, acao)

        # Invalidar cache do IDF documental (lazy: marca dirty, rebuild
        # so na proxima chamada de _nmi_semantico). Em lotes, alimentar_lote
        # pode adiar a invalidacao para o final.
        if not getattr(self, '_idf_skip_invalidate', False):
            self._cache_idf_doc = None
            self._cache_ctx_index = None
            self._cache_assinatura = {}
            self._posicao_acao_inv = None
            self._transicao_rev_full = None
            if hasattr(self, '_transicao_rev'):
                self._transicao_rev = {}

    def alimentar_lote(self, pares: list, reconstruir_hierarquia: bool = False):
        """Ingere lista de (texto, acao) com invalidacao de cache deferida.

        Otimizacoes vs alimentar() individual:
        1. _cache_idf_doc e _cache_ctx_index: invalidados UMA vez no
           final, nao a cada alimentar() (37K invalidacoes -> 1).
        2. Hierarquia (_hierarquia.alimentar): PULADA durante o lote.
           A hierarquia chama _assinatura_frase -> _avaliar_composicao
           -> _todas_h_norm_palavras que itera sobre TODO o vocabulario.
           Com texto real (62K+ palavras), isso e O(P) por frase = O(n²).
           Apos o lote, a hierarquia pode ser reconstruida explicitamente
           via reconstruir_hierarquia() se necessario.

        O motor funciona normalmente durante o lote — apenas
        _nmi_semantico() e a fonte HRC (hierarquia) podem usar dados
        stale, o que e aceitavel durante ingestao em massa.

        Args:
            pares: lista de (texto, acao)
            reconstruir_hierarquia: se True, re-alimenta a hierarquia
                apos o lote (pode ser lento para lotes grandes)
        """
        self._idf_skip_invalidate = True
        self._skip_hierarquia = True
        try:
            for texto, acao in pares:
                self.alimentar(texto, acao)
        finally:
            self._idf_skip_invalidate = False
            self._skip_hierarquia = False
            self._cache_idf_doc = None
            self._cache_ctx_index = None
            self._cache_assinatura = {}
            self._posicao_acao_inv = None
            self._transicao_rev_full = None

        if reconstruir_hierarquia:
            if self._hierarquia is None:
                from mcr.acoplamento_hierarquico import MCRHierarquico
                self._hierarquia = MCRHierarquico(max_niveis=5, min_delta_h=0.05)
            MCRCoupling._hierarquia_feed_emCurso = True
            try:
                for texto, acao in pares:
                    self._hierarquia.alimentar(texto, acao)
            finally:
                MCRCoupling._hierarquia_feed_emCurso = False

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
            self.alimentar_lote(pares, reconstruir_hierarquia=True)
            return self

        if chunk_size <= 0:
            chunk_size = max(100, min(500, n // 8))

        chunks = [pares[i:i+chunk_size] for i in range(0, n, chunk_size)]

        couplings = []
        for chunk in chunks:
            m = MCRCoupling()
            m.alimentar_lote(chunk, reconstruir_hierarquia=False)
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
        # Reconstruir hierarquia apos merge (MCRs temporarios nao tinham)
        if self._hierarquia is None:
            from mcr.acoplamento_hierarquico import MCRHierarquico
            self._hierarquia = MCRHierarquico(max_niveis=5, min_delta_h=0.05)
        MCRCoupling._hierarquia_feed_emCurso = True
        try:
            for texto, acao in pares:
                self._hierarquia.alimentar(texto, acao)
        finally:
            MCRCoupling._hierarquia_feed_emCurso = False
        return self

    def alimentar_swarm_paralelo(self, pares: list, n_workers: int = 0):
        """Swarm MCR paralelo — MCRzifica a ingestão em larga escala.

        Divide os dados em N chunks, cada um ingerido por um MCR filho
        em um processo SEPARADO (multiprocessing). O MCR pai faz merge()
        dos resultados. Isso paraleliza a ingestão entre cores.

        Auto-detecção de gargalo: se n_workers=0, usa todos os cores
        disponíveis quando o lote > 5000 frases. Para lotes menores,
        usa alimentar_swarm sequencial (overhead de spawn não compensa).

        Pilar 11 — Humano 4D: o MCR adapta-se ao hardware disponível.
        Pilar 10 — Consenso: MCRs filhos chegam a consenso via merge().

        Args:
            pares: lista de (texto, acao)
            n_workers: número de processos paralelos (0 = auto)
        """
        n = len(pares)
        if n < 5000:
            # Para lotes pequenos, overhead de spawn não compensa
            return self.alimentar_swarm(pares)

        if n_workers <= 0:
            n_workers = max(2, min(8, os.cpu_count() or 2))

        chunk_size = max(500, n // n_workers)
        chunks = [pares[i:i+chunk_size] for i in range(0, n, chunk_size)]

        # Usar multiprocessing.Pool para ingerir em paralelo
        import multiprocessing as mp
        try:
            with mp.Pool(min(n_workers, len(chunks))) as pool:
                resultados = pool.map(_worker_ingerir, chunks)
        except Exception:
            # Fallback: sequencial se multiprocessing falhar
            return self.alimentar_swarm(pares)

        # Merge dos resultados em árvore binária
        for estado in resultados:
            filho = MCRCoupling()
            filho._aplicar_estado(estado)
            self.merge(filho)

        # Reconstruir hierarquia
        if self._hierarquia is None:
            from mcr.acoplamento_hierarquico import MCRHierarquico
            self._hierarquia = MCRHierarquico(max_niveis=5, min_delta_h=0.05)
        MCRCoupling._hierarquia_feed_emCurso = True
        try:
            for texto, acao in pares:
                self._hierarquia.alimentar(texto, acao)
        finally:
            MCRCoupling._hierarquia_feed_emCurso = False
        return self

    def _aplicar_estado(self, estado: dict):
        """Aplica estado serializado (de _worker_ingerir) a este MCR."""
        self._total = estado.get('total', 0)
        for k, v in estado.get('palavra_acao', {}).items():
            self._palavra_acao[k] = defaultdict(int, v)
        for k, v in estado.get('transicao_palavra', {}).items():
            self._transicao_palavra[k] = defaultdict(int, v)
        for k, v in estado.get('posicao_acao', {}).items():
            self._posicao_acao[k] = defaultdict(int, v)
        for k, v in estado.get('feature_acao', {}).items():
            self._feature_acao[k] = defaultdict(int, v)
        for k, v in estado.get('acao_features', {}).items():
            self._acao_features[k] = v
        for k, v in estado.get('freq_acao', {}).items():
            self._freq_acao[k] = v
        for k, v in estado.get('cluster_acao', {}).items():
            self._cluster_acao[k] = defaultdict(int, v)
        for k, v in estado.get('estado_features', {}).items():
            self._estado_features[k] = defaultdict(int, v)
        for k, v in estado.get('trigrama_acao', {}).items():
            self._trigrama_acao[k] = defaultdict(int, v)
        for k, v in estado.get('padrao_acao', {}).items():
            self._padrao_acao[k] = defaultdict(int, v)
        for k, v in estado.get('ngrama', {}).items():
            ordem = int(k)
            for pref_str, prox_dict in v.items():
                pref = tuple(pref_str.split('|'))
                for prox, c in prox_dict.items():
                    self._ngrama[ordem][pref][prox] = c

    def alimentar_cluster(self, cluster_id, acao: str):
        acao = str(acao)
        self._cluster_acao[f"C{cluster_id}"][acao] += 1

    def _entropia_ajustada(self, fonte: str, texto: str, h: float) -> float:
        # #19+#21: ajusta entropia pelo peso aprendido da fonte.
        # Se fonte tem peso 2x, entropia reportada e menor (mais certeza).
        ajuste = self._peso_fonte_ajuste(fonte, texto)
        return 1.0 - (1.0 - h) * ajuste

    def decidir(self, texto: str, mk_pred: Tuple[Optional[str], float],
                cluster_id=None, cluster_conf=0.0) -> Tuple[str, float]:
        distribs = []
        acao_mk, conf_mk = mk_pred

        # === Confiança Posicional P0 estendida (FASE 8.1) ===
        # Se a palavra em P0 é conhecida mas nunca foi vista como verbo (pos_count=0),
        # ela é um SUBSTANTIVO na posição de verbo. Fontes sensíveis à identidade
        # da palavra (I, TRN, CMP, E) devem ter confiança reduzida.
        # Se P0 é palavra nova (não em _palavra_acao), confiança média (0.5):
        # não sabemos se é verbo ou substantivo, então não deixar I/E/TRN/CMP
        # dominarem com sinais de substantivos conhecidos da frase.
        p0_conf = 1.0
        partes = texto.replace('_', ' ').lower().split()
        if partes:
            p0 = partes[0][:10]
            pos_data = self._posicao_acao.get(f"P0:{p0}", {})
            pos_count = sum(pos_data.values())
            if pos_count == 0 and p0 in self._palavra_acao:
                p0_conf = 0.0  # substantivo conhecido em posição de verbo
            elif p0 not in self._palavra_acao and len(self._palavra_acao) > 0:
                p0_conf = 0.5  # palavra nova em P0 — confiança média

        if acao_mk:
            d_mk = {str(acao_mk): conf_mk}
            h_mk = self._entropia_ajustada('MK', texto, self._entropia_dist(d_mk))
            distribs.append((d_mk, h_mk))

        d_palavra = self._dist_palavras(texto)
        if d_palavra:
            h_w = self._entropia_ajustada('W', texto, self._entropia_dist(d_palavra))
            distribs.append((d_palavra, h_w))

        if cluster_id is not None:
            d_cluster = self._dist_cluster(cluster_id)
            if d_cluster:
                h_cl = self._entropia_ajustada('C', texto, self._entropia_dist(d_cluster))
                distribs.append((d_cluster, h_cl))

        d_pos = self._dist_posicoes(texto)
        if d_pos:
            # P nao usa entropia real (que mede diversidade posicional,
            # nao confianca). Usa entropia fixa 0.5 (neutro) porque cada
            # posicao ja tem peso exponencial (Pilar 4).
            distribs.append((d_pos, 0.5))

        # Fonte I — Features N-dimensionais (sublexicais)
        # p0_conf: se P0 é substantivo, features do P0 não devem dominar
        d_feat = self._dist_features(texto)
        if d_feat:
            h_i = self._entropia_ajustada('I', texto, self._entropia_dist(d_feat))
            h_i = 1.0 - (1.0 - h_i) * p0_conf  # p0_conf=0 → h=1 (sem confiança)
            distribs.append((d_feat, h_i))

        # #1 — Fonte E: Esfera cross-level
        d_esf = self._dist_esfera(texto)
        if d_esf:
            h_e = self._entropia_ajustada('E', texto, self._entropia_dist(d_esf))
            h_e = 1.0 - (1.0 - h_e) * p0_conf
            distribs.append((d_esf, h_e))

        # #6 — Fonte F: Fingerprint 8D + cosseno
        d_fp = self._dist_fingerprint(texto)
        if d_fp:
            h_f = self._entropia_ajustada('F', texto, self._entropia_dist(d_fp))
            distribs.append((d_fp, h_f))

        # #7 — Fonte J: Jaccard de transicoes
        d_jac = self._dist_jaccard(texto)
        if d_jac:
            h_j = self._entropia_ajustada('J', texto, self._entropia_dist(d_jac))
            distribs.append((d_jac, h_j))

        # === FASE 7+ — Novas fontes de decisão ===

        # Fonte ATN — Contexto temporal (atenção via buffer)
        # Só ativa em modo conversacional (opt-in). Em classificação/batch,
        # o buffer acumula dados de treino irrelevantes à query atual.
        if self._contexto_ativo:
            d_ctx = self._dist_contexto(texto)
            if d_ctx:
                h_atn = self._entropia_ajustada('ATN', texto, self._entropia_dist(d_ctx))
                distribs.append((d_ctx, h_atn))

        # Fonte EPI — Memória episódica
        d_epi = self._dist_episodica(texto)
        if d_epi:
            h_epi = self._entropia_ajustada('EPI', texto, self._entropia_dist(d_epi))
            distribs.append((d_epi, h_epi))

        # Fonte TRN — Fecho transitivo (correlação em múltiplos passos)
        d_trn = self._dist_transitivo(texto, passos=3, p0_conf=p0_conf)
        if d_trn:
            h_trn = self._entropia_ajustada('TRN', texto, self._entropia_dist(d_trn))
            h_trn = 1.0 - (1.0 - h_trn) * p0_conf
            distribs.append((d_trn, h_trn))

        # Fonte CMP — Composição de assinatura
        d_cmp = self._dist_composicao(texto, p0_conf=p0_conf)
        if d_cmp:
            h_cmp = self._entropia_ajustada('CMP', texto, self._entropia_dist(d_cmp))
            h_cmp = 1.0 - (1.0 - h_cmp) * p0_conf
            distribs.append((d_cmp, h_cmp))

        # Fonte BRN — Branch search multi-caminho (só se não reentrante e poucas fontes)
        if not getattr(self, '_em_branch', False) and len(distribs) < 5:
            self._em_branch = True
            try:
                d_brn = self._dist_branch(texto)
                if d_brn:
                    h_brn = self._entropia_ajustada('BRN', texto, self._entropia_dist(d_brn))
                    distribs.append((d_brn, h_brn))
            finally:
                self._em_branch = False

        # Fonte HRC — Hierarquia multi-escala (camadas emergentes)
        if not self._em_hierarquia and self._hierarquia is not None:
            self._em_hierarquia = True
            try:
                acao_hrc, conf_hrc = self._hierarquia.predizer(texto, acao_mk)
                if acao_hrc and conf_hrc > 0:
                    # Confianca escalada por observacoes acumuladas
                    # log2: 0 obs ~0, ~50 obs ~1.0, sem valor magico fixo
                    obs = self._hierarquia._total_observacoes
                    esc_conf = min(1.0, math.log2(obs + 1) / math.log2(51))
                    conf_hrc *= esc_conf
                    d_hrc = {acao_hrc: conf_hrc}
                    # Fonte single-action: entropia = 1-conf (inversa da confianca real),
                    # NAO _entropia_dist (que seria 0 para 1 acao, dando peso maximo)
                    h_hrc = self._entropia_ajustada('HRC', texto, 1.0 - conf_hrc)
                    distribs.append((d_hrc, h_hrc))
            finally:
                self._em_hierarquia = False

        if not distribs:
            return (acao_mk or 'responder'), conf_mk
        combinada = self._superpor(distribs)
        if not combinada:
            return (acao_mk or 'responder'), conf_mk

        # === FASE 20 — Busca ativa (triunvirato) — ANTES de P0 ===
        if self._deliberacao is not None:
            div_media = self._divergencia_media_fontes(distribs)
            pode_responder = True
            if getattr(self, '_meta_ativo', False) and self._meta is not None:
                pode_responder, _, _ = self._meta.pode_responder(
                    texto, combinada[max(combinada, key=combinada.get)],
                    dict(combinada), len(distribs), div_media)
            if self._deliberacao.deve_buscar(div_media, pode_responder):
                busca_dist, eventos = self._deliberacao.buscar(texto, self)
                if busca_dist:
                    h_busca = self._entropia_ajustada(
                        'BUSCA', texto, self._entropia_dist(busca_dist))
                    distribs.append((busca_dist, h_busca))
                    combinada = self._superpor(distribs)

        # #16 — Auto-correção P0: se P0 é verbo específico (H < threshold_entropico)
        # e score > threshold_entropico, sobrescreve decisão.
        # Thresholds derivados da mediana das H de todas as palavras em P0.
        partes = texto.replace('_', ' ').lower().split()
        if partes:
            p0 = partes[0][:10]
            h_norm_p0 = self._h_norm_posicao(0, p0)
            if h_norm_p0 >= 0:
                # Threshold: menor H positivo de todas as palavras P0.
                # Se ate mesmo o menor H e maior que o da palavra atual,
                # a palavra e especifica (mais deterministica que qualquer
                # outra). Zero valores magicos — puramente dos dados.
                todos_h = [h for h in self._todas_h_norm_p0() if h > 0]
                th_esp = min(todos_h) if todos_h else 0.0
                if h_norm_p0 < th_esp:
                    p0_dist = self._posicao_acao.get(f"P0:{p0}", {})
                    total_p0 = sum(p0_dist.values())
                    melhor_p0 = max(p0_dist, key=p0_dist.get)
                    score_p0 = p0_dist[melhor_p0] / total_p0
                    # Score threshold = mediana dos scores das palavras
                    # P0 que tem ENTROPIA > 0 (exclui H=0 pois essas sao
                    # totalmente deterministicas e nao definem threshold)
                    h_p0_nao_zero = [h for h in self._todas_h_norm_p0() if h > 0]
                    th_score = 1.0 - (self._threshold_entropico('p0_score', h_p0_nao_zero)
                                      if h_p0_nao_zero else 1.0)
                    if score_p0 > th_score and combinada.get(melhor_p0, 0) > 0:
                        return melhor_p0, max(combinada[melhor_p0], score_p0)

        melhor = max(combinada, key=combinada.get)
        # === FASE 10 — Meta-cognição (opt-in) ===
        if getattr(self, '_meta_ativo', False) and self._meta is not None:
            n_fontes = len(distribs)
            div_media = self._divergencia_media_fontes(distribs)
            self._meta.observar(texto, melhor, combinada[melhor],
                                dict(combinada), n_fontes, div_media)
            pode, conf_efetiva, _just = self._meta.pode_responder(
                texto, combinada[melhor], dict(combinada),
                n_fontes, div_media)
            if not pode:
                return 'nao_sei', conf_efetiva
            return melhor, conf_efetiva
        return melhor, combinada[melhor]

    @staticmethod
    def _js_divergencia(p: Dict[str, float], q: Dict[str, float]) -> float:
        # Jensen-Shannon divergence simetrica, normalizada [0,1]
        chaves = set(p) | set(q)
        m: Dict[str, float] = {}
        for k in chaves:
            m[k] = (p.get(k, 0.0) + q.get(k, 0.0)) / 2.0
        def kl(a, b):
            s = 0.0
            for k in a:
                if a[k] > 0 and b.get(k, 0) > 0:
                    s += a[k] * math.log2(a[k] / b[k])
            return s
        js = (kl(p, m) + kl(q, m)) / 2.0
        return min(1.0, js)

    def _superpor(self, distribs: List[Tuple[Dict[str, float], float]]) -> Dict[str, float]:
        if not distribs:
            return {}
        # #18 — Peso por divergencia: em vez de (1-entropia) puro, usamos
        # divergencia cruzada entre as fontes. Fontes que discordam do
        # consenso tem peso reduzido; fontes que concordam, mantido.
        # Base: (1 - entropia)
        pesos_div = [(1.0 - h) for _, h in distribs]
        n = len(distribs)
        if n > 1:
            # Divergencia media de cada fonte contra as demais
            divs_medias = []
            for i in range(n):
                di = distribs[i][0]
                total_i = sum(di.values()) or 1.0
                di_norm = {k: v / total_i for k, v in di.items()}
                acc = 0.0
                for j in range(n):
                    if i == j:
                        continue
                    dj = distribs[j][0]
                    total_j = sum(dj.values()) or 1.0
                    dj_norm = {k: v / total_j for k, v in dj.items()}
                    acc += self._js_divergencia(di_norm, dj_norm)
                divs_medias.append(acc / (n - 1))
            # Ajustar pesos: cada fonte tem peso reduzido proporcionalmente a
            # sua divergencia mediana em relacao as demais. Quanto mais diverge,
            # menor o peso — sem thresholds fixos.
            for i in range(n):
                d = divs_medias[i]
                # Thresholds entrópicos: tercis inferior e superior das divergencias
                divs_ord = sorted(divs_medias)
                th_alta = divs_ord[min(len(divs_ord) * 2 // 3, len(divs_ord) - 1)]
                th_media = divs_ord[len(divs_ord) // 3]
                if d > th_alta:
                    # Reducao proporcional: piso = 1/n (entropia maxima com n fontes)
                    pesos_div[i] *= max(1.0 / n, 1.0 - d)
                elif d > th_media:
                    # Reducao proporcional a posicao entre th_media e th_alta
                    fator = (d - th_media) / max(th_alta - th_media, 0.001)
                    pesos_div[i] *= (1.0 - d * fator)
        total_raw = sum(pesos_div) or 1.0
        pesos = [w / total_raw for w in pesos_div]
        combinada: Dict[str, float] = defaultdict(float)
        # #17 — Colisao de rotas: contar top-1 de cada fonte para boost
        top1_contagem: Dict[str, int] = defaultdict(int)
        n_fontes_ativas = 0
        for (d, _), peso in zip(distribs, pesos):
            if not d:
                continue
            n_fontes_ativas += 1
            total_d = sum(d.values()) or 1.0
            top1 = max(d, key=d.get)
            top1_contagem[top1] += 1
            for acao, prob in d.items():
                combinada[acao] += (prob / total_d) * peso
        # Boost de concordancia: se >=2 fontes concordam no top-1, boost
        # proporcional a frequencia de concordancia (nao fixo 2x)
        if n_fontes_ativas > 0:
            for acao, cnt in top1_contagem.items():
                if cnt >= 2 and acao in combinada:
                    # boost = razao de concordancia (cnt / n_fontes_ativas)
                    # multiplicado pelo inverso para amplificar
                    boost = cnt / max(n_fontes_ativas - cnt, 1)
                    combinada[acao] *= (1.0 + boost)
        total = sum(combinada.values()) or 1.0
        return {a: s / total for a, s in combinada.items()}

    def refinar_pesos(self, dados_validacao: List[Tuple[str, str]]):
        # #19 — MCRPesoNota: aprende pesos otimos das fontes por validacao.
        # Testa cada fonte isoladamente e ajusta pesos proporcionalmente
        # a acuracia observada. Fontes mais precisas pesam mais.
        fontes = {
            'W': lambda t: self._dist_palavras(t),
            'P': lambda t: self._dist_posicoes(t),
            'I': lambda t: self._dist_features(t),
        }
        acertos: Dict[str, int] = defaultdict(int)
        total_val = len(dados_validacao)
        for nome, fn in fontes.items():
            for texto, acao_esp in dados_validacao:
                d = fn(texto)
                if d:
                    pred = max(d, key=d.get)
                    if pred == acao_esp:
                        acertos[nome] += 1
        melhores = {k: v / total_val for k, v in acertos.items()}
        if melhores:
            max_acc = max(melhores.values()) or 1
            # Piso = entropia da distribuicao de acuracias (quanto mais
            # uniforme, maior o piso; quanto mais desigual, menor)
            accs = list(melhores.values())
            h_acc = 0.0
            for a in accs:
                p = a / max(sum(accs), 1)
                if p > 0: h_acc -= p * math.log2(p)
            h_max = math.log2(max(len(accs), 2))
            piso = h_acc / h_max if h_max > 0 else 1.0
            self._pesos_fonte = {
                k: max(piso, v / max_acc)
                for k, v in melhores.items()
            }
            # #20 — MCRThreshold: threshold = mediana das confiancas
            aprendido = self._threshold_adpt
            self._confiancas_observadas.clear()
            for texto, acao_esp in dados_validacao:
                acao, conf = self.decidir(texto, (None, 0.0))
                if acao == acao_esp:
                    self._confiancas_observadas.append(conf)
                else:
                    self._confiancas_observadas.append(1.0 - conf)
            if self._confiancas_observadas:
                ord_ = sorted(self._confiancas_observadas)
                self._threshold_adpt = ord_[len(ord_) // 2]
            # #21 — MCRPeso: aprende pesos por categoria
            # Categoriza input por comprimento e tipo de P0
            self._peso_categoria.clear()
            cat_contagens: Dict[str, int] = defaultdict(int)
            cat_acertos: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for texto, acao_esp in dados_validacao:
                partes = texto.lower().split()
                n = len(partes)
                p0 = partes[0][:10] if partes else ''
                # Categoria por entropia P0, nao por lista hardcoded
                p0_dist = self._posicao_acao.get(f'P0:{p0}', {})
                total_p0 = sum(p0_dist.values())
                if total_p0 >= 2:
                    h = 0.0
                    for ct in p0_dist.values():
                        pr = ct / total_p0
                        if pr > 0: h -= pr * math.log2(pr)
                    max_h = math.log2(max(len(p0_dist), 2))
                    h_norm = h / max_h if max_h > 0 else 0
                    todas_h = self._todas_h_norm_p0()
                    if todas_h:
                        ord_h = sorted(todas_h)
                        th_espec = ord_h[len(ord_h) // 3]
                        th_gener = ord_h[len(ord_h) * 2 // 3]
                    else:
                        # Sem dados: tudo intermediario (nao categorizavel)
                        th_espec, th_gener = 0.0, 1.0
                    if h_norm < th_espec:
                        cat = 'verbo_especifico'
                    elif h_norm > th_gener:
                        cat = 'verbo_generico'
                    else:
                        cat = 'intermediario'
                elif n <= self._mediana_comp:
                    cat = 'curta'
                else:
                    cat = 'longa'
                cat_contagens[cat] += 1
                for nome, fn in fontes.items():
                    d = fn(texto)
                    if d:
                        pred = max(d, key=d.get)
                        if pred == acao_esp:
                            cat_acertos[cat][nome] += 1
            for cat, cont in cat_contagens.items():
                if cont > 0:
                    accs = {k: v / cont for k, v in cat_acertos.get(cat, {}).items()}
                    if accs:
                        max_a = max(accs.values()) or 1
                        accs_vals = list(accs.values())
                        h_cat = 0.0
                        for a in accs_vals:
                            p = a / max(sum(accs_vals), 1)
                            if p > 0: h_cat -= p * math.log2(p)
                        h_max_c = math.log2(max(len(accs_vals), 2))
                        piso_c = h_cat / h_max_c if h_max_c > 0 else 1.0
                        self._peso_categoria[cat] = {
                            k: max(piso_c, v / max_a) for k, v in accs.items()
                        }

    def _peso_fonte_ajuste(self, nome_fonte: str, texto: str) -> float:
        # Aplica ajustes #19 e #21 no peso de uma fonte
        partes = texto.lower().split()
        n = len(partes)
        p0 = partes[0][:10] if partes else ''
        # Categoria por entropia P0, nao por lista hardcoded
        p0_dist = self._posicao_acao.get(f'P0:{p0}', {})
        total_p0 = sum(p0_dist.values())
        if total_p0 >= 2:
            h = 0.0
            for ct in p0_dist.values():
                pr = ct / total_p0
                if pr > 0: h -= pr * math.log2(pr)
            max_h = math.log2(max(len(p0_dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            todas_h = self._todas_h_norm_p0()
            if todas_h:
                ord_h = sorted(todas_h)
                th_espec = ord_h[len(ord_h) // 3]
                th_gener = ord_h[len(ord_h) * 2 // 3]
            else:
                # Sem dados: tudo intermediario (nao categorizavel)
                th_espec, th_gener = 0.0, 1.0
            if h_norm < th_espec:
                cat = 'verbo_especifico'
            elif h_norm > th_gener:
                cat = 'verbo_generico'
            else:
                cat = 'intermediario'
        elif n <= self._mediana_comp:
            cat = 'curta'
        else:
            cat = 'longa'
        # #21: peso por categoria (se disponivel)
        peso_cat = self._peso_categoria.get(cat, {}).get(nome_fonte, 1.0)
        # #19: peso global da fonte (se disponivel)
        peso_global = self._pesos_fonte.get(nome_fonte, 1.0)
        return peso_cat * peso_global

    def _dist_palavras(self, texto: str) -> Dict[str, float]:
        # Pilar 4 — Template + gaps: posicao 0 = template (verbo/acao principal),
        # posicoes posteriores = gaps (argumentos/objeto). Peso posicional
        # exponencial: pos 0 = 1.0, pos 1 = 0.5, pos 2 = 0.25, etc.
        # Isso faz o verbo dominar a decisao, evitando que "npc" (count=266)
        # ofusque "edite" (count=18) na frase "edite o looktype do npc vendedor".
        #
        # Pilar 4+2 — Confianca posicional: uma palavra so contribui com
        # peso maximo se foi VISTA naquela posicao no treino. "pocao" vista
        # 6x como objeto (P4) mas 0x como sujeito (P0) tem confianca_pos=0
        # em P0 -> nao domina a decisao com estatisticas de outro contexto.
        palavras_regex = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        partes = texto.replace('_', ' ').lower().split()
        pos_map = {}
        for i, p in enumerate(partes):
            if len(p) >= 3 and p not in pos_map:
                pos_map[p] = i
        scores: Dict[str, float] = defaultdict(float)
        for p in set(palavras_regex):
            pos = pos_map.get(p, 0)
            peso_pos = 2.0 ** (-pos)
            # Confianca posicional: fracao das aparicoes da palavra nesta posicao
            dist = self._palavra_acao.get(p, {})
            if dist:
                pos_data = self._posicao_acao.get(f"P{pos}:{p[:10]}", {})
                pos_count = sum(pos_data.values())
                # #11 — P0 dominance entrópico contínuo (ao inves de binario):
                # se a palavra foi vista 0x em P0, pos_conf=0 (contexto inedito).
                # Se 1x, pos_conf=0.5 (incipiente). Se 2+, usa entropia da
                # distribuicao P0 para modular: H baixa = verbo especifico
                # = confianca alta; H alta = verbo generico = confianca media.
                if pos == 0:
                    if pos_count == 0:
                        pos_conf = 0.0
                    elif pos_count == 1:
                        # pos_conf = mediana dos scores (1-H) das palavras P0
                        th = 1.0 - self._threshold_entropico('p0_incipiente',
                                                              self._todas_h_norm_p0())
                        pos_conf = th
                    else:
                        h_pos = 0.0
                        for c in pos_data.values():
                            prob = c / pos_count
                            if prob > 0:
                                h_pos -= prob * math.log2(prob)
                        max_h = math.log2(max(len(pos_data), 2))
                        h_norm = h_pos / max_h if max_h > 0 else 0
                        # #12 — Boost para P0 quando verbo especifico.
                        # Threshold entrópico: tercil inferior da mediana P0
                        th_esp = self._threshold_entropico('p0_boost',
                                                            self._todas_h_norm_p0()) * (1.0 / 3.0)
                        if h_norm < th_esp:
                            # Boost = 1 / th_esp (quanto mais especifico, maior o boost)
                            pos_conf = (1.0 - h_norm) * (1.0 / max(th_esp, 0.01))
                        else:
                            pos_conf = (1.0 - h_norm)
                    peso_pos = peso_pos * pos_conf
            if not dist:
                # Pilar 7 — Correlacao Universal: heranca morfologica.
                # Isolada em _dist_palavras (decisao) — nao afeta
                # _assinatura_palavra (similaridade), evitando contaminacao.
                # Fallback classico n-gram.
                proxies = self.palavras_similares(p)
                if proxies:
                    sub_scores: Dict[str, float] = defaultdict(float)
                    for prox, conf in proxies:
                        d = self._palavra_acao.get(prox, {})
                        if not d:
                            continue
                        td = sum(d.values()) or 1
                        for a, c in d.items():
                            sub_scores[a] += (c / td) * conf
                    if sub_scores:
                        # Normalizar para [0,1] — heranca e distribuicao relativa,
                        # nao count absoluto (Pilar 2: entropia descobre).
                        max_val = max(sub_scores.values()) or 1
                        for a, v in sub_scores.items():
                            scores[a] += (v / max_val) * peso_pos
                        continue
                # Heranca morfologica (Pilar 7) — fallback do fallback
                heranca = self._heranca_morfologica(p)
                if heranca:
                    sub_h: Dict[str, float] = defaultdict(float)
                    for k, v in heranca.items():
                        if k.startswith('acao:') and v > 0:
                            a = k[len('acao:'):]
                            sub_h[a] += v
                    if sub_h:
                        max_h = max(sub_h.values()) or 1
                        for a, v in sub_h.items():
                            scores[a] += (v / max_h) * peso_pos
                continue
            total = sum(dist.values()) or 1
            # #13 — Especificidade da palavra (markov_cruzado.py adaptado):
            # Especificidade = 1 - H_normalizada. Palavra com distribuicao
            # concentrada (H baixa) é especifica mesmo em multiplas acoes.
            # "monstro" em 7 acoes mas 90% gerar_monstro = especifica.
            probs_pal = [c / total for c in dist.values()]
            h_pal = 0.0
            for pr in probs_pal:
                if pr > 0:
                    h_pal -= pr * math.log2(pr)
            max_h_pal = math.log2(max(len(dist), 2))
            h_norm_pal = h_pal / max_h_pal if max_h_pal > 0 else 0
            especificidade = 1.0 - h_norm_pal
            # #15 — Penalidade por ponte fraca (mcr_emergir.py):
            # se a palavra so tem 1 exemplo, ponte fraca. Penalidade
            # proporcional a (1 - 1/total) — 1 exemplo = 0, infinitos = 1.
            penalidade_ponte = min(1.0, (total - 1) / max(total, 1))
            # #14 — Profundidade da cadeia (markov_cruzado.py):
            # tamanho da cadeia de transicoes a partir da palavra.
            # Normalizada pela mediana de profundidade de todas as palavras.
            prof = len(self._transicao_palavra.get(p, {}))
            todas_prof = [len(self._transicao_palavra.get(w, {}))
                          for w in self._palavra_acao]
            prof_mediana = self._threshold_entropico('profundidade', todas_prof)
            profundidade = min(1.0, prof / max(prof_mediana, 1)) if prof > 0 else 0.0
            fator_palavra = especificidade * penalidade_ponte * profundidade
            for a, c in dist.items():
                scores[a] += (c / total) * peso_pos * fator_palavra
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

    def _dist_features(self, texto: str) -> Dict[str, float]:
        """Fonte I — Features N-dimensionais: P(acao|todas_as_features).

        Extrai as MESMAS 8 features de _extrair_features_nd e consulta
        _feature_acao para cada uma. Agrega com peso por entropia
        (Pilar 2): features com distribuicao concentrada pesam mais.

        Os 8 planos (identicos ao treino):
          t:{token}     — token
          c:{char}      — char
          b:{byte}      — byte
          bg:{bigram}   — bigrama de chars
          ng:{trigram}  — trigrama de chars
          p{i}:{token}  — posicao especifica
          ca:{token}    — contexto ANTES (palavra anterior)
          cd:{token}    — contexto DEPOIS (palavra posterior)

        Os planos ca: e cd: sao os CRITICOS para composicao:
        "pocao" com cd:vida -> responder, mas "pocao" com cd:sprite -> gerar_sprite.
        Sem ca:/cd:, _dist_features perde a composicao que _dist_palavras nao captura.
        """
        texto = str(texto)
        raw = texto.lower()
        feats = set()

        # Token level
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', raw)
        for t in set(tokens):
            feats.add(f"t:{t}")

        # Bigram and trigram levels (chars only)
        chars = re.sub(r'[^a-z0-9]', '', raw)
        for i in range(len(chars) - 1):
            feats.add(f"bg:{chars[i:i+2]}")
        for i in range(len(chars) - 2):
            feats.add(f"ng:{chars[i:i+3]}")

        scores: Dict[str, float] = defaultdict(float)
        for feat in feats:
            dist = self._feature_acao.get(feat, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            # Pilar 2: entropia da feature determina peso
            probs = [c / total for c in dist.values()]
            ent = 0.0
            for pr in probs:
                if pr > 0:
                    ent -= pr * math.log2(pr)
            ent_norm = ent / (math.log2(len(probs)) or 1) if len(probs) > 1 else 0.0
            peso = 1.0 - ent_norm
            for a, c in dist.items():
                scores[a] += (c / total) * peso
        return dict(scores) if scores else {}

    def _dist_trigramas(self, texto: str) -> Dict[str, float]:
        """Fonte T — Trigramas de chars: P(acao|trigrama_char).

        Cada trigrama de 3 chars consecutivos (sem espacos) vota na acao.
        Trigramas com H baixa (deterministicos) pesam mais (Pilar 2).

        Captura padroes sublexicais que palavras inteiras perdem:
        "spr" -> gerar_sprite, "npc" -> gerar_npc, "que" -> responder.
        Resolve ambiguidade onde a palavra inteira e generica mas
        seus substrings sao especificos.
        """
        chars = re.sub(r'[^a-z0-9]', '', texto.lower())
        if len(chars) < 3:
            return {}
        scores: Dict[str, float] = defaultdict(float)
        for i in range(len(chars) - 2):
            tri = chars[i:i+3]
            dist = self._trigrama_acao.get(tri, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            probs = [c / total for c in dist.values()]
            ent = 0.0
            for pr in probs:
                if pr > 0:
                    ent -= pr * math.log2(pr)
            ent_norm = ent / (math.log2(len(probs)) or 1) if len(probs) > 1 else 0.0
            peso = 1.0 - ent_norm
            for a, c in dist.items():
                scores[a] += (c / total) * peso
        return dict(scores) if scores else {}

    def _dist_esfera(self, texto: str) -> Dict[str, float]:
        """Fonte E — Esfera cross-level: P(acao|correlacao_niveis).

        Aprende P(tipo_N_feature | tipo_M_feature) durante treino.
        No teste, extrai features de todos os niveis (t, bg, ng, c)
        e ve quais acoes sao correlacionadas com features de QUALQUER
        nivel. Se "pocao" (t:) correlaciona com vida (ng:ida) que
        correlaciona com responder, a esfera captura isso.

        Cada feature de cada nivel vota. Diferente de _dist_features
        que trata todas features como planas, a esfera preserva que
        features de niveis diferentes reforcam umas as outras.
        """
        texto = str(texto)
        raw = texto.lower()
        # Extrai features por nivel
        tokens = set(re.findall(r'[a-zà-ÿ0-9]{2,}', raw))
        chars = re.sub(r'[^a-z0-9]', '', raw)
        bigrams = set(chars[i:i+2] for i in range(len(chars)-1))
        trigrams = set(chars[i:i+3] for i in range(len(chars)-2))

        scores: Dict[str, float] = defaultdict(float)
        # Cada feature vota em acoes via _feature_acao
        feats = set(f"t:{t}" for t in tokens)
        feats |= set(f"bg:{bg}" for bg in bigrams)
        feats |= set(f"ng:{ng}" for ng in trigrams)

        for feat in feats:
            dist = self._feature_acao.get(feat, {})
            if not dist:
                continue
            total_f = sum(dist.values()) or 1
            for acao, c in dist.items():
                scores[acao] += c / total_f

        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_jaccard(self, texto: str) -> Dict[str, float]:
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return {}
        if len(palavras) < 2:
            return {}
        scores: Dict[str, float] = defaultdict(float)
        for i in range(len(palavras)-1):
            p1, p2 = palavras[i], palavras[i+1]
            # Para cada ação, verifica se esta mesma transição (mesma posição relativa)
            # foi vista levando a esta ação
            chave = f"P{i}:{p1[:10]}"
            d_pos = self._posicao_acao.get(chave, {})
            # Se p1 nesta posição leva a alguma ação, e p2 também foi visto em P{i+1} para mesma ação
            for acao, _ in d_pos.items():
                chave2 = f"P{i+1}:{p2[:10]}"
                d_pos2 = self._posicao_acao.get(chave2, {})
                if d_pos2.get(acao, 0) > 0:
                    scores[acao] += 1.0
        if not scores:
            return {}
        max_s = max(scores.values())
        total = len(palavras) - 1
        return {a: s / total for a, s in scores.items()}

    def _dist_fingerprint(self, texto: str) -> Dict[str, float]:
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return {}
        chars = re.sub(r'[^a-z0-9]', '', texto.lower())
        if not chars:
            return {}
        n = len(chars)
        vogais = sum(1 for c in chars if c in 'aeiou')
        consoantes = sum(1 for c in chars if c in 'bcdfghjklmnpqrstvwxyz')
        digito = sum(1 for c in chars if c.isdigit())
        fp = [vogais/n, consoantes/n, digito/n]
        vc, vv, cv, cc = 0, 0, 0, 0
        for i in range(len(chars)-1):
            a = chars[i] in 'aeiou'
            b = chars[i+1] in 'aeiou'
            if a and b: vv += 1
            elif a and not b: vc += 1
            elif not a and b: cv += 1
            else: cc += 1
        total_pares = max(vv+vc+cv+cc, 1)
        fp += [vv/total_pares, vc/total_pares, cv/total_pares, cc/total_pares]
        scores: Dict[str, float] = defaultdict(float)
        for acao in self._freq_acao:
            acao_chars = acao.replace('_', '')
            if not acao_chars:
                continue
            n_a = len(acao_chars)
            v_a = sum(1 for c in acao_chars if c in 'aeiou')
            c_a = sum(1 for c in acao_chars if c in 'bcdfghjklmnpqrstvwxyz')
            fp_a = [v_a/n_a, c_a/n_a, 0.0]
            vv_a, vc_a, cv_a, cc_a = 0, 0, 0, 0
            for i in range(len(acao_chars)-1):
                a = acao_chars[i] in 'aeiou'
                b = acao_chars[i+1] in 'aeiou'
                if a and b: vv_a += 1
                elif a and not b: vc_a += 1
                elif not a and b: cv_a += 1
                else: cc_a += 1
            tp_a = max(vv_a+vc_a+cv_a+cc_a, 1)
            fp_a += [vv_a/tp_a, vc_a/tp_a, cv_a/tp_a, cc_a/tp_a]
            dot = sum(fp[i]*fp_a[i] for i in range(len(fp)))
            mag = math.sqrt(sum(v*v for v in fp))
            mag_a = math.sqrt(sum(v*v for v in fp_a))
            if mag * mag_a == 0:
                continue
            sim = dot / (mag * mag_a)
            if sim > 0.0:
                scores[acao] += sim
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_ancoras(self, texto: str) -> Dict[str, float]:
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return {}
        scores: Dict[str, float] = defaultdict(float)
        for p in set(palavras):
            dist = self._palavra_acao.get(p, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            n_acoes = len(dist)
            probs = [c / total for c in dist.values()]
            h = 0.0
            for pr in probs:
                if pr > 0: h -= pr * math.log2(pr)
            max_h = math.log2(max(n_acoes, 2))
            h_norm = h / max_h if max_h > 0 else 0
            ancora = 1.0 - h_norm
            for a, c in dist.items():
                scores[a] += (c / total) * ancora
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_observador(self, texto: str) -> Dict[str, float]:
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return {}
        scores: Dict[str, float] = defaultdict(float)
        for p in set(palavras):
            dist = self._palavra_acao.get(p, {})
            if dist:
                continue  # palavras conhecidas usam _dist_palavras, nao observador
            # Palavra nova: busca a palavra mais similar por cosseno
            melhor_sim = 0.0
            melhor_dist = None
            melhor_total = 1
            for outra, dist2 in self._palavra_acao.items():
                total_o = sum(dist2.values()) or 1
                vec_o = {a: c / total_o for a, c in dist2.items()}
                # Usa bigrams para similaridade (agnostico a vocabulario)
                bigs_p = set(p[j:j+2] for j in range(len(p)-1))
                bigs_o = set(outra[j:j+2] for j in range(len(outra)-1))
                inter = bigs_p & bigs_o
                union = bigs_p | bigs_o
                sim = len(inter) / len(union) if union else 0
                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_dist = dist2
                    melhor_total = total_o
            if melhor_dist and melhor_sim > self._threshold_entropico('obs_sim',
                                                                       self._todas_h_norm_palavras()):
                for a, c in melhor_dist.items():
                    scores[a] += (c / melhor_total) * melhor_sim
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _classificar_padrao(self, partes: list) -> str:
        """Classifica cada posicao como V/C/S por entropia posicional.

        Otimizacao: cache por (partes_frozen, geracao). Padrões repetidos
        ("criar monstro dragao", "gerar npc ladrao") sao classificados
        uma unica vez por geracao — eliminando O(P0) por chamada.
        """
        if not hasattr(self, '_cache_padrao'):
            self._cache_padrao = {}
            self._cache_padrao_gen = -1
        gen = self._total // _CACHE_H_JANELA
        if gen != self._cache_padrao_gen:
            self._cache_padrao = {}
            self._cache_padrao_gen = gen
        key = tuple(partes[:6])
        if key in self._cache_padrao:
            return self._cache_padrao[key]
        resultado = self._classificar_padrao_calc(partes)
        self._cache_padrao[key] = resultado
        return resultado

    def _classificar_padrao_calc(self, partes: list) -> str:
        """Classifica cada posicao como V/C/S por entropia posicional.

        Pilar 4 — Template + gaps: descobre a estrutura sintatica SEM hardcode.
          H baixa (< 0.3) = V (verbo — distribuicao concentrada, define acao)
          H alta (> 0.7)  = C (conector — distribuicao espalhada, generico)
          H media         = S (substantivo — intermediario)

        Retorna string como "VCS" para "criar monstro forte".

        Otimizacao: th_inf/th_sup so mudam quando _todas_h_norm_p0 muda
        (geracao). Cacheados por geraçao para evitar recalcular o sort
        a cada uma das 6 posicoes por frase.
        Agnostico a vocabulario: "pocao de vida" -> "SCS" mesmo padrao que
        "machado de guerra" -> "SCS".
        """
        tipos = []
        gen = self._total // _CACHE_H_JANELA
        # th_inf/th_sup cacheados por geracao apenas — uma nova palavra P0
        # nao muda a mediana das H significativamente (mediana e robusta
        # a outliers). Invalidar a cada nova palavra causava 1989
        # recalculos em 2000 frases (quase 1 por frase).
        if (hasattr(self, '_cache_vcs_gen') and self._cache_vcs_gen == gen):
            th_inf, th_sup = self._cache_vcs_cutoffs
        else:
            todas_h = self._todas_h_norm_p0()
            if todas_h:
                th_inf = self._threshold_entropico('vcs_verbo', todas_h) * (1.0 / 3.0)
                th_sup = self._threshold_entropico('vcs_conector', todas_h) * (2.0 / 3.0)
            else:
                th_inf, th_sup = 0.3, 0.7
            self._cache_vcs_cutoffs = (th_inf, th_sup)
            self._cache_vcs_gen = gen
        for i, p in enumerate(partes[:6]):
            p_lower = p[:10].lower()
            pos_dist = self._posicao_acao.get(f"P{i}:{p_lower}", {})
            total_pos = sum(pos_dist.values())
            if total_pos >= 2:
                h_pos = 0.0
                for c in pos_dist.values():
                    prob = c / total_pos
                    if prob > 0:
                        h_pos -= prob * math.log2(prob)
                max_h_pos = math.log2(max(len(pos_dist), 2))
                h_norm = h_pos / max_h_pos if max_h_pos > 0 else 0
                if h_norm < th_inf:
                    tipos.append('V')
                elif h_norm > th_sup:
                    tipos.append('C')
                else:
                    tipos.append('S')
            elif len(p) > 3:
                tipos.append('S')
            else:
                tipos.append('X')
        return ''.join(tipos)

    def _dist_padrao(self, texto: str) -> Dict[str, float]:
        """Fonte PT — Padrao estrutural: P(acao|VCS).

        Classifica a frase em V/C/S por posicao e consulta _padrao_acao.
        Agnostico a vocabulario — resolve ambiguidade lexical:
        "pocao de vida" (SCS) e "machado de guerra" (SCS) compartilham
        o mesmo padrao estrutural -> mesma classe (responder).
        "criar sprite de escudo" (VSCS) -> gerar_sprite.
        """
        partes = texto.replace('_', ' ').lower().split()
        if not partes:
            return {}
        padrao = self._classificar_padrao(partes)
        if not padrao:
            return {}
        dist = self._padrao_acao.get(padrao, {})
        if not dist:
            # Fallback: prefixo do padrao (ex: "VSC" se "VSCS" nao existe)
            for k in range(len(padrao) - 1, 0, -1):
                prefix = padrao[:k]
                dist = self._padrao_acao.get(prefix, {})
                if dist:
                    break
        if not dist:
            return {}
        total = sum(dist.values()) or 1
        return {a: c / total for a, c in dist.items()}

    def _inic_hierarquia(self):
        if self._hierarquia is None:
            from mcr.acoplamento_hierarquico import MCRHierarquico
            self._hierarquia = MCRHierarquico(max_niveis=5, min_delta_h=0.05)
        return self._hierarquia

    def _inic_deliberacao(self):
        if self._deliberacao is None:
            from mcr.triunvirato import Deliberacao
            self._deliberacao = Deliberacao()
            # Registra fontes de busca disponíveis
            try:
                from mcr.base_conhecimento import BaseConhecimento
                bc = BaseConhecimento(self)
                self._deliberacao.registrar_fonte('BaseConhecimento', bc)
            except Exception:
                pass
            try:
                from mcr.knowledge.kg import KnowledgeGraph
                kg = KnowledgeGraph()
                self._deliberacao.registrar_fonte('KnowledgeGraph', kg)
            except Exception:
                pass
        return self._deliberacao

    def _inic_context_buffer(self) -> ContextBuffer:
        if self._context_buffer is None:
            self._context_buffer = ContextBuffer(max_size=128)
        return self._context_buffer

    def _inic_episodic_gateway(self) -> EpisodicGateway:
        if self._episodic_gateway is None:
            try:
                # Verifica se há episódios antes de instanciar (evita I/O do Ollama)
                import os
                base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                mem_path = os.path.join(base, 'sandbox', '.mcr_episodios.json')
                if not os.path.exists(mem_path) or os.path.getsize(mem_path) < 10:
                    self._episodic_gateway = EpisodicGateway(None)
                    return self._episodic_gateway
                from mcr.knowledge.episodic_memory import EpisodicMemory
                mem = EpisodicMemory()
                if not mem.episodios:
                    self._episodic_gateway = EpisodicGateway(None)
                else:
                    self._episodic_gateway = EpisodicGateway(mem)
            except Exception:
                self._episodic_gateway = EpisodicGateway(None)
        return self._episodic_gateway

    def _dist_contexto(self, texto: str) -> Dict[str, float]:
        """Fonte ATN — Contexto temporal (atenção ao buffer).

        Extrai tokens do buffer de contexto (últimas N observações)
        e consulta _palavra_acao para cada um, ponderado por recência.
        O buffer é atualizado automaticamente a cada alimentar().

        Pilar 1: P(acao | ctx:token) — transição markoviana.
        Pilar 2: peso por recência (decai exponencialmente).
        Pilar 7: tokens do buffer são correlacionados via P(acao|token).
        """
        buf = self._inic_context_buffer()
        pares = buf.obter()
        if not pares:
            return {}
        scores: Dict[str, float] = {}
        for token, peso_recencia in pares:
            dist = self._palavra_acao.get(token, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            for acao, c in dist.items():
                scores[acao] = scores.get(acao, 0) + (c / total) * peso_recencia
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_episodica(self, texto: str) -> Dict[str, float]:
        """Fonte EPI — Memória episódica como fonte de decisão.

        Consulta EpisodicMemory por experiências passadas similares.
        Converte lessons em features markovianas e consulta _palavra_acao.

        Pilar 1: P(acao | ep:licao) — transição markoviana.
        Pilar 5: usa experiencias passadas (loop fechado).
        Pilar 7: memórias são correlacionadas via P(acao|licao_keyword).
        """
        gw = self._inic_episodic_gateway()
        dist = gw.consultar(texto, n=3)
        if not dist:
            return {}
        # Mapeia palavras da memoria para _palavra_acao
        scores: Dict[str, float] = {}
        for palavra, peso_mem in dist.items():
            d = self._palavra_acao.get(palavra, {})
            if not d:
                continue
            total = sum(d.values()) or 1
            for acao, c in d.items():
                scores[acao] = scores.get(acao, 0) + (c / total) * peso_mem
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_transitivo(self, texto: str, passos: int = 3,
                         p0_conf: float = 1.0) -> Dict[str, float]:
        """Fonte TRN — Fecho transitivo no grafo de transições.

        Percorre _transicao_palavra em N passos a partir das palavras
        do texto, acumulando palavras alcançáveis com peso decrescente
        por distância. Consulta _palavra_acao para cada palavra alcançada.

        "fogo" -> passo 1: "calor", "dano", "vermelho"
               -> passo 2: "calor" -> "temperatura", "quente"
               -> passo 3: "temperatura" -> "eventos", "clima"
        Resultado: P(acao | correlacao_indireta) mesmo sem transição direta.

        Pilar 1: P(prox | atual) — navegação no grafo.
        Pilar 2: peso por distância (entropia da caminhada).
        Pilar 7: correlação universal em múltiplos passos.
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return {}

        # Peso posicional: P0 pesa 1.0, P1=0.5, P2=0.25, etc.
        # Isso faz o verbo (P0) dominar o fecho transitivo, evitando
        # que substantivos em posições posteriores dominem a decisão.
        partes = texto.replace('_', ' ').lower().split()
        pos_map = {}
        for i, p in enumerate(partes):
            if len(p) >= 3 and p not in pos_map:
                pos_map[p] = i

        # Se p0_conf < 1.0 (P0 é novo ou substantivo), exigir que P0
        # contribua. Se P0 não está em _transicao_palavra, o fecho a
        # partir de P0 é vazio — só restam substantivos, que não devem
        # dominar a decisão.
        p0_palavra = partes[0] if partes else ''
        if p0_conf < 1.0 and p0_palavra not in self._transicao_palavra:
            return {}

        import math
        alcancaveis: Dict[str, float] = {}

        for palavra in set(palavras):
            pos = pos_map.get(palavra, 0)
            peso_pos = 2.0 ** (-pos)
            visitados = {palavra}
            fronteira = [(palavra, peso_pos)]
            for _ in range(passos):
                nova_fronteira = []
                for atual, peso in fronteira:
                    vizinhos = self._transicao_palavra.get(atual, {})
                    if not vizinhos:
                        continue
                    total_viz = sum(vizinhos.values()) or 1
                    for viz, c in vizinhos.items():
                        if viz in visitados:
                            continue
                        visitados.add(viz)
                        peso_viz = peso * (c / total_viz) * 0.5
                        if peso_viz > 0.01:
                            alcancaveis[viz] = max(alcancaveis.get(viz, 0), peso_viz)
                            nova_fronteira.append((viz, peso_viz))
                fronteira = nova_fronteira
                if not fronteira:
                    break

        if not alcancaveis:
            return {}

        scores: Dict[str, float] = {}
        for palavra_alc, peso_trans in alcancaveis.items():
            dist = self._palavra_acao.get(palavra_alc, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            for acao, c in dist.items():
                scores[acao] = scores.get(acao, 0) + (c / total) * peso_trans

        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

    def _dist_branch(self, texto: str) -> Dict[str, float]:
        """Fonte BRN — Branch search multi-caminho.

        Usa BranchSearcher para explorar múltiplos caminhos de predição.
        Retorna a distribuição de ações do melhor caminho encontrado.

        Pilar 2: entropia decide expansão dos caminhos.
        Equação 5D: avalia qualidade de cada caminho.
        """
        try:
            from mcr.branch_search import BranchSearcher
        except ImportError:
            return {}
        bs = BranchSearcher(self, n_caminhos=3, profundidade=2)
        melhor_acao, melhor_nota = bs.buscar(texto)
        if melhor_acao and melhor_nota > 0:
            return {melhor_acao: melhor_nota}
        return {}

    def _dist_composicao(self, texto: str,
                         p0_conf: float = 1.0) -> Dict[str, float]:
        """Fonte CMP — Composição de assinatura como fonte de decisão.

        Extrai a assinatura composicional da frase via _assinatura_frase()
        e consulta _palavra_acao para as palavras da assinatura.
        Captura o significado composto que palavras isoladas perdem.

        "cachorro verde" -> compor(sig("cachorro"), sig("verde"))
                         -> palavras na assinatura composta votam

        Pilar 1: P(acao | assinatura_composta) — transição markoviana.
        Pilar 4: template + gaps (composição recursiva).
        """
        sig = self._assinatura_frase(texto)
        if not sig:
            return {}
        # Se p0_conf < 1.0 (P0 é novo ou substantivo), exigir que P0
        # tenha contribuído para a assinatura composta. Se P0 é palavra
        # nova, sua assinatura é vazia → composição só tem substantivos
        # → não deve dominar.
        if p0_conf < 1.0:
            p0_palavra = texto.replace('_', ' ').lower().split()
            p0_palavra = p0_palavra[0] if p0_palavra else ''
            if p0_palavra not in self._palavra_acao:
                return {}
        # Peso posicional: palavras da assinatura que estão em P0 pesam mais
        partes = texto.replace('_', ' ').lower().split()
        pos_map = {}
        for i, p in enumerate(partes):
            if len(p) >= 3 and p not in pos_map:
                pos_map[p] = i
        palavras_sig = set()
        for k in sig:
            if k.startswith('ctx:'):
                palavras_sig.add(k[len('ctx:'):])
            elif k.startswith('acao:'):
                palavras_sig.add(k[len('acao:'):])
        if not palavras_sig:
            return {}
        scores: Dict[str, float] = {}
        for p in palavras_sig:
            pos = pos_map.get(p, 0)
            peso_pos = 2.0 ** (-pos)
            dist = self._palavra_acao.get(p, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            for acao, c in dist.items():
                scores[acao] = scores.get(acao, 0) + (c / total) * peso_pos
        if not scores:
            return {}
        total = sum(scores.values()) or 1
        return {a: s / total for a, s in scores.items()}

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

        NOTA: A heranca morfologica (Pilar 7) NAO entra aqui — ela e
        isolada em _dist_palavras para nao contaminar a rede de
        similaridade. Assinatura = observado puro.
        """
        if not palavra:
            return {}
        if not hasattr(self, '_cache_assinatura'):
            self._cache_assinatura = {}
        p = palavra.lower()
        if p in self._cache_assinatura:
            return self._cache_assinatura[p]

        # Indice invertido de _posicao_acao: palavra -> lista de chaves
        # Otimizacao: construir UMA vez (lazy) em vez de iterar O(P) por chamada
        if not hasattr(self, '_posicao_acao_inv') or self._posicao_acao_inv is None:
            self._posicao_acao_inv = defaultdict(list)
            for k, d in self._posicao_acao.items():
                palavra_key = k.split(":", 1)[-1] if ":" in k else k
                if d:
                    self._posicao_acao_inv[palavra_key].append((k, d))

        sig = defaultdict(int)
        for k, v in self._palavra_acao.get(p, {}).items():
            sig[f"acao:{k}"] += v
        for k, v in self._transicao_palavra.get(p, {}).items():
            sig[f"ctx:{k}"] += v
        for k, d in self._posicao_acao_inv.get(p, []):
            for ak, av in d.items():
                sig[f"posacao:{ak}"] += av

        self._cache_assinatura[p] = dict(sig) if sig else {}
        return self._cache_assinatura[p]

    def _heranca_morfologica(self, palavra: str) -> Dict[str, float]:
        """Pilar 7 — Correlacao Universal: herda P(acao) de vizinhos morfologicos.

        Para uma palavra nunca observada, herda assinaturas de palavras
        conhecidas ponderadas pela similaridade n-gram.
        A selecao de doadores e' pelo maior gap relativo na distribuicao
        de similaridades — puramente geometrico, nenhum valor magico.
        """
        if not palavra or not self._palavra_acao:
            return {}
        try:
            from mcr.semantic_router import similaridade as ngram_sim
        except ImportError:
            try:
                from semantic_router import similaridade as ngram_sim
            except ImportError:
                return {}

        doadores = []
        for known in self._palavra_acao.keys():
            if known == palavra:
                continue
            s = ngram_sim(palavra, known)
            if s <= 0:
                continue
            sig_known = self._assinatura_palavra(known)
            if not sig_known:
                continue
            doadores.append((s, known, sig_known))
        if not doadores:
            return {}
        doadores.sort(key=lambda x: -x[0])

        # Corte no maior GAP RELATIVO: ponto onde a similaridade despenca
        maior_gap = 0.0
        idx_corte = len(doadores)
        for i in range(len(doadores) - 1):
            if doadores[i][0] == 0:
                continue
            gap = (doadores[i][0] - doadores[i + 1][0]) / doadores[i][0]
            if gap > maior_gap:
                maior_gap = gap
                idx_corte = i + 1
        if idx_corte < 1:
            return {}

        # MCR: herança como distribuição de probabilidade
        # P(acao|palavra_nova) = sum_d s(d) * P(acao|d) / sum_d s(d)
        num = defaultdict(float)
        den = 0.0
        for s, _, sig_known in doadores[:idx_corte]:
            acoes = {k[5:]: v for k, v in sig_known.items() if k.startswith('acao:') and v > 0}
            if not acoes:
                continue
            total = sum(acoes.values())
            s2 = s * s  # similaridade ao quadrado = foco no top match
            for a, v in acoes.items():
                num[a] += (v / sum(acoes.values())) * s2
            den += s2

        if den == 0:
            return {}
        heranca = {k: v / den for k, v in num.items()}

        # Threshold adaptativo: 1/(2*k) onde k=num classes ativas
        k_ativo = len(heranca)
        thresh = 0.5 / max(k_ativo, 2)  # uniforme/2
        return {k: v for k, v in heranca.items() if v >= thresh}

    def _nmi(self, dict_a, dict_b) -> float:
        """Similaridade por reducao de incerteza da mistura — MCR puro.

        Implementa uma variante de Informacao Mutua baseada na entropia
        da MISTURA das duas distribuicoes marginais:

          H_mix = -sum ((pa[k] + pb[k]) / (ta + tb)) * log2(...)
          sim(a,b) = (H(a) + H(b) - H_mix) / min(H(a), H(b))

        Nao é NMI classico (que requer distribuicao conjunta p(a,b)),
        mas captura a mesma ideia: duas distribuicoes similares reduzem
        a incerteza quando combinadas.

        Propriedades:
          - a == b => 1.0 (maxima similaridade)
          - a ∩ b = {} => 0.0 (disjuntas, zero informacao compartilhada)
          - Retorna em [0, 1]

        Denominador: min(H(a), H(b)) — corrige viés de tamanho (Fase A1b).
        Com max(H), subconjuntos (coocorrentes) teriam NMI artificialmente
        baixo. Com min(H), o menor vetor dita a escala — coerente com
        "quanto o menor reduz incerteza do maior".

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
        minh = min(ha, hb)
        if minh <= 0:
            return 0.0
        return max(0.0, min(1.0, mi / minh))

    def _nmi_semantico(self, dict_a, dict_b) -> float:
        """NMI normalizado por plano — para comparacao semantica de assinaturas.

        Pilar 1: IDF documental pondera planos ctx:.
                 IDF = log(N_palavras / df(token)) onde df(token) = quantas
                 palavras tem token como contexto. Palavras-ancora raras
                 (cachorro, dog) tem IDF alto; templates comuns (associado,
                 caracteristica) tem IDF baixo.
        Pilar 2: planos com entropia zero (só um valor) nao discriminam.
        Pilar 7: NMI de assinatura dominada por acao: e props comuns nao
                 discrimina semantica. IDF documental corrige: "late" (6
                 palavras) pesa 4.3, "tem" (271 palavras) pesa 0.49.

        Passos:
          1. Agrupar chaves por plano (prefixo antes de ':')
          2. Remover planos com entropia zero (só um valor) — nao discriminam
          3. Ponderar planos ctx: por IDF documental (Pilar 1)
          4. Normalizar cada plano restante pela soma ponderada
          5. Calcular NMI com denominador sqrt(H(a)*H(b)) — media geometrica
        """
        if not dict_a or not dict_b:
            return 0.0

        # Cache do IDF documental: df(token) = |{w : token in ctx de w}|
        if not hasattr(self, '_cache_idf_doc') or self._cache_idf_doc is None:
            self._cache_idf_doc = {}
            self._cache_idf_total = len(self._palavra_acao) or 1
            for w in self._transicao_palavra:
                for ctx_token in self._transicao_palavra[w]:
                    self._cache_idf_doc[ctx_token] = self._cache_idf_doc.get(ctx_token, 0) + 1

        n_palavras = self._cache_idf_total

        def filtrar_normalizar(d):
            planos = {}
            for k, v in d.items():
                prefixo = k.split(':', 1)[0] if ':' in k else '_sem'
                planos.setdefault(prefixo, {})[k] = v
            resultado = {}
            for prefixo, vals in planos.items():
                if len(vals) <= 1:
                    continue
                pesos = {}
                if prefixo == 'ctx':
                    # IDF documental: ponderar planos ctx: por log(N/df(token))^4
                    # IDF^4 amplifica a diferenca entre palavras raras (cachorro=9.1)
                    # e comuns (tem=1.1): 9.1^4=6857 vs 1.1^4=1.46 — ratio 4690x
                    # A PONTE NATURAL跨-idioma vem dos planos posacao: e acao:
                    # (estrutura posicional + distribuicao de acoes) — nao
                    # precisa de overlap de ctx. IDF^4 suprime stopwords sem
                    # remover tokens estruturais.
                    idf_map = {}
                    for k in vals:
                        token = k.split(':', 1)[1] if ':' in k else k
                        df = self._cache_idf_doc.get(token, 1)
                        idf = math.log(n_palavras / max(df, 1))
                        idf_map[k] = max(idf, 0.01)
                        pesos[k] = idf_map[k] ** 4
                    # FILTRAGEM ENTROPICA (Pilar 2): cortar tokens de baixo IDF
                    # dinamicamente. _corte_dinamico encontra o gap natural na
                    # distribuicao de IDF — sem threshold hardcoded.
                    # Stopwords (the, tem, e) tem IDF ~0.1-1.0 e sao cortadas;
                    # content words (cachorro, perro) tem IDF ~5-10 e ficam.
                    if len(idf_map) > 20:
                        idf_vals = list(idf_map.values())
                        corte = self._corte_dinamico(idf_vals)
                        if 0 < corte < len(idf_map):
                            sorted_kvs = sorted(idf_map.items(),
                                                key=lambda kv: -kv[1])
                            manter = {k for k, _ in sorted_kvs[:corte]}
                            vals = {k: v for k, v in vals.items() if k in manter}
                            pesos = {k: v for k, v in pesos.items() if k in manter}
                else:
                    for k in vals:
                        pesos[k] = 1.0
                soma_pond = sum(vals[k] * pesos[k] for k in vals) or 1
                for k, v in vals.items():
                    resultado[k] = (v * pesos[k]) / soma_pond
            return resultado

        na = filtrar_normalizar(dict_a)
        nb = filtrar_normalizar(dict_b)
        if not na or not nb:
            return 0.0

        # NMI POR PLANO: cada plano (ctx, acao, posacao) contribui
        # igualmente para o NMI final. Isto evita que o plano ctx: (com
        # milhares de tokens, especifico do idioma) afogue os planos
        # posacao: e acao: (poucos tokens, cross-idioma estrutural).
        #
        # A PONTE NATURAL跨-idioma: "cachorro" (PT) e "dog" (EN) nao
        # compartilham ctx tokens, mas tem estrutura posicional similar
        # ( ambos aparecem em P0 como sujeito) e distribuicao de acoes
        # similar ( ambos associados a "descrever"). NMI por plano deixa
        # esse sinal emergir em vez de ser afogado pelo ctx.
        #
        # Pilar 3: cada plano e uma fonte observavel independente na
        # cadeia de Markov. Pilar 1: P(b|a) por fonte, depois agregado.
        planos_a: Dict[str, Dict[str, float]] = {}
        planos_b: Dict[str, Dict[str, float]] = {}
        for k, v in na.items():
            prefixo = k.split(':', 1)[0] if ':' in k else '_sem'
            planos_a.setdefault(prefixo, {})[k] = v
        for k, v in nb.items():
            prefixo = k.split(':', 1)[0] if ':' in k else '_sem'
            planos_b.setdefault(prefixo, {})[k] = v

        planos_comuns = set(planos_a.keys()) & set(planos_b.keys())
        if not planos_comuns:
            return 0.0

        nmi_por_plano: List[float] = []
        for prefixo in planos_comuns:
            pa_raw = planos_a[prefixo]
            pb_raw = planos_b[prefixo]
            if not pa_raw or not pb_raw:
                continue
            # Mutual Information (correto): NMI = 2*I(a;b)/(H(a)+H(b))
            # Retorna 0 para zero overlap — JSD bug retornava 0.7+
            shared_keys = set(pa_raw.keys()) & set(pb_raw.keys())
            if not shared_keys:
                nmi_por_plano.append(0.0)
                continue
            ta = sum(pa_raw.values()) or 1
            tb = sum(pb_raw.values()) or 1
            ha = -sum((v / ta) * math.log2(v / ta) for v in pa_raw.values() if v > 0)
            hb = -sum((v / tb) * math.log2(v / tb) for v in pb_raw.values() if v > 0)
            if ha + hb == 0:
                nmi_por_plano.append(0.0)
                continue
            mi = 0.0
            for k in shared_keys:
                pa = pa_raw[k] / ta
                pb = pb_raw[k] / tb
                mi += pa * math.log2(pa / (pa * pb)) if pa > 0 and pb > 0 else 0
            nmi_plane = max(0.0, min(1.0, 2 * mi / (ha + hb)))
            nmi_por_plano.append(nmi_plane)

        if not nmi_por_plano:
            return 0.0
        return sum(nmi_por_plano) / len(nmi_por_plano)

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

        # Sigma = desvio padrao das H de todas as palavras observadas.
        # Centraliza em 0.5 (sweet spot informacional). Quando mais
        # dispersas as H das palavras, mais tolerante a estabilidade.
        # Cacheado por janela (_CACHE_H_JANELA): media/var/sigma mudam
        # pouco em 200 observacoes. Sem janela, recalcula sobre 62K+
        # palavras a cada _avaliar_composicao (3-6x por _assinatura_frase).
        gen = self._total // _CACHE_H_JANELA
        if hasattr(self, '_cache_comp_stats_gen') and self._cache_comp_stats_gen == gen:
            media_h, sigma = self._cache_comp_stats
        else:
            todas_h = self._todas_h_norm_palavras()
            if todas_h:
                media_h = sum(todas_h) / len(todas_h)
                var_h = sum((h - media_h) ** 2 for h in todas_h) / len(todas_h)
                sigma = max(var_h ** 0.5, 0.01)
            else:
                media_h, sigma = 0.5, 0.2
            self._cache_comp_stats = (media_h, sigma)
            self._cache_comp_stats_gen = gen
        # Sweet spot = 0.5 (ponto de maxima informacao para binario)
        estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * sigma ** 2))

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
            self._cache_stats_h_gen = -1

        # Cache de stats_h por janela: iterar sobre TODO o vocabulario
        # (62K+ palavras) para calcular media/desvio e O(P). Sem janela,
        # recalculava a cada nova palavra (cache_stats_h = None nunca
        # era re-invalidado apos primeira chamada).
        gen = self._total // _CACHE_H_JANELA
        if gen != self._cache_stats_h_gen:
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
            self._cache_stats_h_gen = gen

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
                proxies = self.palavras_similares(p)
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

    def _construir_ctx_index(self) -> Dict[str, set]:
        """Constroi inverted index: ctx_token -> set de palavras que o tem.

        Otimizacao: iterar diretamente sobre _transicao_palavra (O(P))
        em vez de chamar _assinatura_palavra(w) para cada palavra
        (O(P x K) — 53s para 23K palavras). Os ctx tokens de uma
        palavra sao exatamente as chaves de _transicao_palavra[w].
        """
        if getattr(self, '_cache_ctx_index', None) is not None:
            return self._cache_ctx_index

        index: Dict[str, set] = {}
        for w, ctx_dict in self._transicao_palavra.items():
            for ctx_token in ctx_dict:
                index.setdefault(ctx_token, set()).add(w)

        self._cache_ctx_index = index
        return index

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

        # === PRE-FILTRO POR INVERTED INDEX (Otimizacao critical) ===
        # Em vez de iterar sobre TODAS as P palavras (O(P^2) total),
        # iterar apenas sobre palavras que compartilham pelo menos um
        # ctx token com a palavra-alvo. Palavras sem overlap de ctx
        # teriam _nmi_semantico ~ 0 e seriam descartadas pelo corte
        # dinamico de qualquer forma.
        # Tambem inclui vizinhos de transicao (para hiperonimos/hiponimos).

        # Garantir _cache_idf_doc construido (usado no overlap IDF-ponderado)
        if not hasattr(self, '_cache_idf_doc') or self._cache_idf_doc is None:
            self._cache_idf_doc = {}
            self._cache_idf_total = len(self._palavra_acao) or 1
            for w in self._transicao_palavra:
                for ctx_token in self._transicao_palavra[w]:
                    self._cache_idf_doc[ctx_token] = self._cache_idf_doc.get(ctx_token, 0) + 1
        n_pal = self._cache_idf_total

        ctx_index = self._construir_ctx_index()
        sig_ctx_tokens = {k.split(':', 1)[1] if ':' in k else k
                          for k in sig_ctx}
        # Filtrar stopwords dos ctx tokens antes do overlap.
        # Mesmo criterio do _nmi_semantico: media IDF² separa stopwords
        # (the/que/and, IDF²~0.02) de content words (IDF²~27).
        # Sem isso, "the" aparece no ctx_index de content words
        # (por co-ocorrência) e acumula IDF alto — dominando o overlap.
        if len(sig_ctx_tokens) > 3:
            idf2_map = {}
            for tok in sig_ctx_tokens:
                df_tok = self._cache_idf_doc.get(tok, 1)
                idf_tok = max(math.log(n_pal / max(df_tok, 1)), 0.01)
                idf2_map[tok] = idf_tok ** 2
            corte = self._corte_dinamico(list(idf2_map.values()))
            if 0 < corte < len(idf2_map):
                sorted_toks = sorted(idf2_map.items(), key=lambda kv: -kv[1])
                filtrado = {tok for tok, _ in sorted_toks[:corte]}
                if filtrado:
                    sig_ctx_tokens = filtrado
        # Overlap IDF-ponderado: cada token compartilhado contribui com
        # seu IDF. Stopwords ("the", IDF~0.15) somam ~0; content words
        # ("cachorro", IDF~7.5) somam muito. Pilar 1: P(raro|contexto)
        # vale mais que P(comum|contexto) — palavras-funcao nao dominam.
        overlap_idf: Dict[str, float] = {}
        for token in sig_ctx_tokens:
            df_tok = self._cache_idf_doc.get(token, 1)
            idf_tok = max(math.log(n_pal / max(df_tok, 1)), 0.01)
            for w in ctx_index.get(token, set()):
                overlap_idf[w] = overlap_idf.get(w, 0.0) + idf_tok
        # Vizinhos de transicao diretos — boost por IDF do vizinho
        trans_out = self._transicao_palavra.get(palavra, {})
        for w in trans_out:
            df_w = self._cache_idf_doc.get(w, 1)
            idf_w = max(math.log(n_pal / max(df_w, 1)), 0.01)
            overlap_idf[w] = overlap_idf.get(w, 0.0) + idf_w
        # Reverse transitions: construir lazy se necessario
        if not hasattr(self, '_transicao_rev'):
            self._transicao_rev = {}
        if not hasattr(self, '_transicao_rev_full') or self._transicao_rev_full is None:
            self._transicao_rev_full = defaultdict(set)
            for w, vizinhos in self._transicao_palavra.items():
                for v in vizinhos:
                    self._transicao_rev_full[v].add(w)
        for w in self._transicao_rev_full.get(palavra, set()):
            df_w = self._cache_idf_doc.get(w, 1)
            idf_w = max(math.log(n_pal / max(df_w, 1)), 0.01)
            overlap_idf[w] = overlap_idf.get(w, 0.0) + idf_w
        overlap_idf.pop(palavra, None)

        # Limitar candidatos: ordenar por IDF-ponderado (tokens raros
        # compartilhados valem mais que stopwords compartilhadas).
        # Com 94K palavras, sem limite o set pode ter 10K+ candidatos.
        MAX_CANDIDATOS = 500
        if len(overlap_idf) > MAX_CANDIDATOS:
            candidatos_set = set(w for w, _ in
                                 sorted(overlap_idf.items(), key=lambda x: -x[1])
                                 [:MAX_CANDIDATOS])
        else:
            candidatos_set = set(overlap_idf.keys())

        # Sem filtro de candidatos por IDF — _corte_dinamico nos scores
        # NMI faz o corte final emergente (Pilar 2). O IDF-ponderado no
        # overlap ja priorizou content words no top-500.

        candidatos = []
        h_palavra_acao = self._entropia_shannon(self._palavra_acao.get(palavra, {}))

        for p in candidatos_set:
            sig_p = self._assinatura_palavra(p)
            if not sig_p:
                continue

            nmi_full = self._nmi_semantico(sig, sig_p)

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

        # === SINONIMOS: alta NMI full (_nmi_semantico com IDF² documental) ===
        # O _nmi_semantico ja pondera planos ctx: por IDF² documental:
        # palavras-ancora raras (cachorro, dog) pesam mais que templates comuns
        # (associado, caracteristica) e verbos de ligacao (tem, has).
        # NAO adicionar ponderacao extra por freq — e redundante e inverte a ordem.
        for c in candidatos:
            c['score_sin'] = c['nmi_full']
        scores_sin = [c['score_sin'] for c in candidatos]
        corte_sin = self._corte_dinamico(scores_sin)
        if corte_sin > 0:
            sin_ordenado = sorted(candidatos, key=lambda c: -c['score_sin'])
            relacoes['sinonimos'] = [(c['palavra'], round(c['score_sin'], 4))
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

        # === MERONIMOS: NMI medio + candidato menor (parte-de) + IDF alto ===
        # IDF documental: filtra verbos de ligacao curtos ("has", "tem") que
        # aparecem como ctx de muitas palavras (IDF baixo). Partes especificas
        # ("patas", "pelo") aparecem como ctx de poucas palavras (IDF alto).
        # Pilar 2: corte emerge da mediana do IDF dos candidatos.
        # (_cache_idf_doc ja construido no inicio de extrair_relacoes)
        candidatos_mero = [c for c in candidatos
                           if c['len'] < len(palavra) and c['nmi_full'] > 0]
        if candidatos_mero:
            # Pilar 2: IDF mediano dos candidatos define corte emergente
            idfs_mero = [math.log(n_pal / max(self._cache_idf_doc.get(c['palavra'], 1), 1))
                         for c in candidatos_mero]
            idfs_mero.sort()
            corte_idf = idfs_mero[len(idfs_mero) // 2]  # mediana
            candidatos_mero = [c for c, idf in zip(candidatos_mero, idfs_mero)
                               if idf >= corte_idf]
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
        if candidatos_set:
            entropias = [self._entropia_shannon(self._palavra_acao.get(p, {}))
                         for p in candidatos_set
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

        # FASE 8: ponderar acao:* com peso 4x — ações são mais discriminativas
        # que contexto compartilhado. "gato" e "carro" compartilham ctx:corre
        # mas têm acao:* diferente (animais vs veiculos) → NMI deve ser baixo.
        sig_a_pond = {}
        sig_b_pond = {}
        for k, v in sig_a.items():
            sig_a_pond[k] = v * 4 if k.startswith('acao:') else v
        for k, v in sig_b.items():
            sig_b_pond[k] = v * 4 if k.startswith('acao:') else v

        base = self._nmi(sig_a_pond, sig_b_pond)

        if hasattr(self, '_word_clusters') and self._word_clusters:
            ca = self._buscar_cluster_palavra(a, self._word_clusters)
            cb = self._buscar_cluster_palavra(b, self._word_clusters)
            if ca is not None and cb is not None:
                if ca == cb:
                    base = max(base, 0.75)
                else:
                    base = min(base, 0.60)
        return base

    def palavras_similares(self, palavra: str, min_sim: float = 0.0,
                           max_resultados: int = 5) -> List[Tuple[str, float]]:
        """Retorna as palavras mais similares da base, ordenadas por score.
        min_sim=0.0 aceita qualquer similaridade positiva; caller pode
        definir threshold mais alto.
        """
        if not palavra:
            return []
        resultado = []
        for candidata in list(self._palavra_acao):
            score = self.similaridade(palavra, candidata)
            if score > min_sim:
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
            'trigrama_acao': {k: dict(v) for k, v in self._trigrama_acao.items()},
            'padrao_acao': {k: dict(v) for k, v in self._padrao_acao.items()},
            'composicoes': {f'{k[0]}|{k[1]}': v for k, v in self._composicoes_aprendidas.items()},
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)
        # FASE 20 — Salva hierarquia multi-escala
        if self._hierarquia is not None:
            hier_caminho = caminho.replace('.json', '_hierarquia.json')
            self._hierarquia.save(hier_caminho)

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
                    if pref_str:
                        prefix = tuple(pref_str.split('|'))
                        self._ngrama[ordem][prefix] = defaultdict(int, prox_dict)
            tg = dados.get('trigrama_acao', {})
            self._trigrama_acao = defaultdict(lambda: defaultdict(int),
                                              {k: base(v) for k, v in tg.items()})
            pa = dados.get('padrao_acao', {})
            self._padrao_acao = defaultdict(lambda: defaultdict(int),
                                             {k: base(v) for k, v in pa.items()})
            comp_raw = dados.get('composicoes', {})
            self._composicoes_aprendidas = {}
            for k, v in comp_raw.items():
                if '|' in k:
                    pare = k.split('|', 1)
                    self._composicoes_aprendidas[(pare[0], pare[1])] = v
            # Lote 4 — estado extra
            for k in ('pesos_fonte', 'threshold_adpt', 'peso_categoria'):
                if k in dados:
                    setattr(self, f'_{k}', dados[k])
            # FASE 20 — Carrega hierarquia multi-escala
            hier_caminho = caminho.replace('.json', '_hierarquia.json')
            import os as _os
            hier = self._inic_hierarquia()
            hier.load(hier_caminho)
            # FASE 20 — Inicializa deliberação (busca ativa)
            self._inic_deliberacao()
            # Pre-construir cache IDF documental (evita latencia outlier
            # na primeira chamada do _nmi_semantico)
            self._cache_idf_doc = {}
            self._cache_idf_total = len(self._palavra_acao) or 1
            for w in self._transicao_palavra:
                for ctx_token in self._transicao_palavra[w]:
                    self._cache_idf_doc[ctx_token] = self._cache_idf_doc.get(ctx_token, 0) + 1
            return True
        except Exception:
            return False

    # =================================================================
    # Lote 4 — Conceitos arquiteturais (#22-30)
    # =================================================================

    def dimensionalidade_ideal(self) -> List[str]:
        """#22 — Determina automaticamente as fontes mais uteis.
        fingerprint_puro.py:178 — acima de ~80 features, 64D cosseno perfoma.
        Aqui: analisa quais fontes (W, P, I, E, F, J, PT, T) tem cobertura
        suficiente (>20 amostras) e retorna apenas as relevantes.
        Entropia decide: fonte com H media acima do tercil superior nao agrega.
        """
        niveis_disponiveis = {
            'W': lambda t: self._palavra_acao,
            'P': lambda t: self._posicao_acao,
            'I': lambda t: self._feature_acao,
            'PT': lambda t: self._padrao_acao,
            'T': lambda t: self._trigrama_acao,
        }
        # Passo 1: coletar H media de cada fonte
        h_por_fonte: Dict[str, float] = {}
        for nome, get_data in niveis_disponiveis.items():
            dados = get_data(None)
            n_features = len(dados)
            if n_features < 20:
                continue
            entropias = []
            for k, d in list(dados.items())[:100]:
                total = sum(d.values())
                if total < 2:
                    continue
                probs = [c / total for c in d.values()]
                h = 0.0
                for p in probs:
                    if p > 0:
                        h -= p * math.log2(p)
                h_max = math.log2(max(len(d), 2))
                entropias.append(h / h_max if h_max > 0 else 0)
            h_por_fonte[nome] = sum(entropias) / max(len(entropias), 1)
        # Passo 2: threshold = tercil superior das H medias observadas
        if h_por_fonte:
            ord_hm = sorted(h_por_fonte.values())
            th_alta = ord_hm[int(len(ord_hm) * 2 / 3)]
        else:
            th_alta = 1.0  # sem dados: entropia maxima = nao filtra nenhuma fonte
        # Passo 3: filtrar fontes com H media abaixo do threshold
        ideais = [nome for nome, h_m in h_por_fonte.items() if h_m <= th_alta]
        return ideais

    def eixo_nirvana_caos(self, texto: str) -> float:
        """#23 — Eixo Nirvana-Caos. pattern_engine_texto.py.
        Nirvana = H ~0 (repeticao). Caos = H ~1 (aleatorio).
        Sweet spot = H ~0.5 (estrutura rica). Retorna -1..+1:
        -1 = Nirvana, 0 = sweet spot, +1 = Caos.
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if not palavras:
            return 0.0
        counter = defaultdict(int)
        for p in palavras:
            counter[p] += 1
        total = len(palavras)
        h = 0.0
        for c in counter.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)
        h_max = math.log2(max(len(counter), 2))
        h_norm = h / h_max if h_max > 0 else 0
        # sweet spot = 0.5, nirvana = 0, caos = 1
        return 2.0 * (h_norm - 0.5)

    def detectar_loop(self, historico_decisoes: List[str], janela: Optional[int] = None) -> bool:
        """#24 — MCREntropia como loop detector. decisor.py:48-68.
        Detecta se as ultimas N decisoes estao em loop. Janela None =
        todo o historico disponivel (entropia maxima da janela).
        """
        if janela is None:
            janela = len(historico_decisoes)
        if janela < 2:
            return False  # < 2 amostras: matematicamente impossivel computar H
        janela_dec = historico_decisoes[-janela:]
        counter = defaultdict(int)
        for a in janela_dec:
            counter[a] += 1
        total = len(janela_dec)
        h = 0.0
        for c in counter.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)
        h_max = math.log2(max(len(counter), 2))
        h_norm = h / h_max if h_max > 0 else 0
        # Registrar H para aprendizado do threshold de loop
        if not hasattr(self, '_historico_h'):
            self._historico_h = {}
        self._historico_h.setdefault('loop', []).append(h_norm)
        # Manter ultimas 100
        if len(self._historico_h['loop']) > 100:
            self._historico_h['loop'] = self._historico_h['loop'][-100:]
        # Loop = H abaixo do tercil inferior das H de decisoes observadas
        todas_h = self._historico_h.get('loop', [])
        if todas_h:
            ord_h = sorted(todas_h)
            th_loop = ord_h[len(ord_h) // 3]  # tercil inferior
        else:
            th_loop = 1.0  # sem dados: entropia maxima = nunca detecta loop
        return h_norm < th_loop

    @staticmethod
    def quebrar_loop(historico_decisoes: List[str]) -> str:
        """#25 — MCRRuido como loop breaker. decisor.py:71-101.
        Se o historico repete, injeta ruido: escolhe a acao MENOS
        frequente nas ultimas N decisoes.
        """
        if not historico_decisoes:
            return 'responder'
        janela = historico_decisoes[-10:]
        counter = defaultdict(int)
        for a in janela:
            counter[a] += 1
        if not counter:
            return 'responder'
        menos_freq = min(counter, key=counter.get)
        return menos_freq

    def diagnosticar(self) -> Dict:
        """#26 — MCRDiagnostico. decisor.py:189-214.
        Diagnostica o estado cognitivo do MCR por entropia.
        """
        n_palavras = len(self._palavra_acao)
        n_acoes = len(self._freq_acao)
        entropias_pal = []
        for p, d in self._palavra_acao.items():
            total = sum(d.values())
            if total < 2:
                continue
            probs = [c / total for c in d.values()]
            h = 0.0
            for p_ in probs:
                if p_ > 0:
                    h -= p_ * math.log2(p_)
            h_max = math.log2(max(len(d), 2))
            entropias_pal.append(h / h_max if h_max > 0 else 0)
        h_media = sum(entropias_pal) / max(len(entropias_pal), 1)
        cobertura = n_palavras / max(n_acoes, 1)
        # Estado: tercis da distribuicao de H de todas as palavras
        todas_h = self._todas_h_norm_palavras()
        if todas_h:
            ord_h = sorted(todas_h)
            th_baixo = ord_h[len(ord_h) // 3]
            th_alto = ord_h[len(ord_h) * 2 // 3]
            estado = ('sobretreinado' if h_media < th_baixo else
                      'saudavel' if h_media < th_alto else
                      'ruidoso')
        else:
            estado = 'saudavel'
        return {
            'total_amostras': self._total,
            'palavras_conhecidas': n_palavras,
            'acoes_conhecidas': n_acoes,
            'cobertura': round(cobertura, 3),
            'h_media_palavras': round(h_media, 4),
            'estado': estado,
            'dimensionalidade_ideal': self.dimensionalidade_ideal(),
        }

    def refinar_por_sucesso(self, texto: str, acao_pred: str,
                            acao_real: str, sucesso: bool):
        """#28 — Refinamento por sucesso. MarkovRouter.py:135-148.
        Aprende com feedback: se acertou, reforca a transicao.
        Se errou, aprende a acao correta.
        """
        if sucesso and acao_pred == acao_real:
            # Reforca duplicando o peso da acao correta
            for p in re.findall(r'[a-zà-ÿ]{3,}', texto.lower()):
                self._palavra_acao[p][acao_pred] += 1
        elif not sucesso and acao_pred != acao_real:
            # Aprende a acao real para as palavras do texto
            self.alimentar(texto, acao_real)

    def tokenizar_universal(self, texto: str) -> List[str]:
        """#29 — Tokenizacao universal. pattern_engine_texto.py.
        Tokeniza por regex sem vocabulario especifico: alfanumerico 2+ chars.
        Funciona para qualquer idioma, codigo fonte, JSON, XML.
        """
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower())
        return tokens

    def autoavaliar(self, dados_validacao: List[Tuple[str, str]]) -> Dict:
        """#30 — Autoavaliacao multinivel. mcr_emergir.py:422-529.
        Avalia o MCR em tres niveis: texto, palavra, estrutural.
        Retorna nota 5D por nivel + nota global.
        """
        if not dados_validacao:
            return {'nota': 0.0}
        acertos_texto = 0
        acertos_palavra = 0
        acertos_estrutura = 0
        total = len(dados_validacao)
        for texto, acao_esp in dados_validacao:
            # Nivel 1: decisao completa
            acao, conf = self.decidir(texto, (None, 0.0))
            if acao == acao_esp:
                acertos_texto += 1
            # Nivel 2: top-1 palavra
            d_w = self._dist_palavras(texto)
            if d_w and max(d_w, key=d_w.get) == acao_esp:
                acertos_palavra += 1
            # Nivel 3: padrao estrutural
            d_p = self._dist_padrao(texto)
            if d_p and max(d_p, key=d_p.get) == acao_esp:
                acertos_estrutura += 1
        # Nota 5D
        certeza = acertos_texto / total
        completude = min(1.0, total / 100.0)
        informacao = acertos_palavra / total
        estabilidade = 0.5  # sem historico
        eficiencia = acertos_estrutura / total
        soma = (certeza * 3 + completude * 3 + informacao * 2 +
                estabilidade * 2 + eficiencia * 1) / 11.0
        nota = 1.0 / (1.0 + math.exp(-2.0 * (soma - 0.35)))
        return {
            'nota': round(nota, 4),
            'acertos_texto': f'{acertos_texto}/{total}',
            'acertos_palavra': f'{acertos_palavra}/{total}',
            'acertos_estrutura': f'{acertos_estrutura}/{total}',
            'certeza': round(certeza, 3),
            'completude': round(completude, 3),
            'informacao': round(informacao, 3),
            'eficiencia': round(eficiencia, 3),
        }

    # =================================================================
    # FASE 7+ — Integração episódica e contexto
    # =================================================================

    def registrar_episodio(self, request: str, resultado, licao: str = "") -> None:
        """Registra uma experiência na memória episódica.

        Pilar 5: loop fechado — toda decisão bem-sucedida é registrada
        para consulta futura via _dist_episodica().
        """
        gw = self._inic_episodic_gateway()
        gw.registrar(request, resultado, licao)

    def limpar_contexto(self) -> None:
        """Limpa o buffer de contexto (inicia nova conversa)."""
        if self._context_buffer is not None:
            self._context_buffer.limpar()

    def ativar_contexto(self) -> None:
        """Ativa o buffer de contexto (modo conversacional).
        Em modo conversacional, o buffer acumula tokens recentes
        e _dist_contexto fornece atenção temporal."""
        self._contexto_ativo = True
        self._inic_context_buffer()

    def desativar_contexto(self) -> None:
        """Desativa o buffer de contexto (modo classificação)."""
        self._contexto_ativo = False

    def contexto_atual(self) -> List[str]:
        """Retorna os tokens atuais no buffer de contexto."""
        if self._context_buffer is None:
            return []
        return [t for t, _ in self._context_buffer.obter()]

    # === FASE 10 — Meta-cognição ===

    def _divergencia_media_fontes(self, distribs: List[Tuple[Dict[str, float], float]]) -> float:
        """Divergência JS média entre fontes (0 = concordam, 1 = discordam)."""
        n = len(distribs)
        if n < 2:
            return 0.0
        divs = []
        for i in range(n):
            di = distribs[i][0]
            total_i = sum(di.values()) or 1.0
            di_norm = {k: v / total_i for k, v in di.items()}
            acc = 0.0
            for j in range(n):
                if i == j:
                    continue
                dj = distribs[j][0]
                total_j = sum(dj.values()) or 1.0
                dj_norm = {k: v / total_j for k, v in dj.items()}
                acc += self._js_divergencia(di_norm, dj_norm)
            divs.append(acc / (n - 1))
        return sum(divs) / len(divs)

    def ativar_metacognicao(self) -> None:
        """Ativa meta-cognição (MCR observa o próprio MCR).

        Em modo classificação/batch, NÃO ativar — meta-cognição
        pode vetoar decisões e retornar 'nao_sei'.
        Em modo cognitivo/conversacional, ativar para permitir
        auto-diagnóstico e 'não sei' como resposta válida.
        """
        from mcr.meta_cognitivo import MetaCognitivo
        self._meta = MetaCognitivo(self)
        self._meta_ativo = True

    def desativar_metacognicao(self) -> None:
        """Desativa meta-cognição (modo classificação)."""
        self._meta_ativo = False

    def feedback_meta(self, confianca: float, correto: bool,
                      acao: str = '') -> None:
        """Fornece feedback à meta-cognição (estava certo ou errado?).

        Constrói o modelo de calibração P(correto|bin_confiança).
        """
        if self._meta is not None:
            self._meta.feedback(confianca, correto, acao)

    def diagnostico_meta(self) -> dict:
        """Retorna auto-diagnóstico meta-cognitivo."""
        if self._meta is not None:
            return self._meta.auto_diagnosticar()
        return {'status': 'meta_cognicao_desativada'}

    def pode_responder_meta(self, texto: str, confianca: float,
                            distribuicao: Dict[str, float],
                            n_fontes: int = 1,
                            divergencia: float = 0.0
                            ) -> Tuple[bool, float, str]:
        """Consulta meta-cognição: devo responder ou admitir ignorância?

        Returns:
            (deve_responder, confianca_calibrada, justificativa)
        """
        if self._meta is None:
            return True, confianca, 'meta_desativada'
        return self._meta.pode_responder(texto, confianca, distribuicao,
                                          n_fontes, divergencia)

    def estatisticas_meta(self) -> dict:
        """Estatísticas meta-cognitivas resumidas."""
        if self._meta is None:
            return {'status': 'meta_cognicao_desativada'}
        return self._meta.estatisticas()

    # === FASE 11 — Auto-expansão (curiosidade dirigida por entropia) ===

    def ativar_curiosidade(self) -> 'AutoExpansao':
        """Ativa auto-expansão (curiosidade dirigida por entropia).

        Returns a instância de AutoExpansao para configurar fontes.
        O MCR identifica onde sua entropia é maior e busca novos dados
        para reduzi-la. Fechar o loop: gap -> buscar -> aprender -> verificar.
        """
        from mcr.auto_expansao import AutoExpansao
        if not hasattr(self, '_auto_expansao') or self._auto_expansao is None:
            self._auto_expansao = AutoExpansao(self)
        return self._auto_expansao

    def ciclo_curiosidade(self, max_gaps: int = 3) -> dict:
        """Executa um ciclo de curiosidade dirigida por entropia.

        Identifica gaps (alta entropia) -> gera perguntas -> busca fontes
        -> aprende -> verifica redução de entropia.

        Requires: ativar_curiosidade() + adicionar_fonte() antes.
        """
        ae = getattr(self, '_auto_expansao', None)
        if ae is None:
            ae = self.ativar_curiosidade()
        return ae.ciclo_curiosidade(max_gaps)

    def entropia_vocabulario(self) -> float:
        """Entropia média do vocabulário (0 = sabe tudo, 1 = nada sabe)."""
        ae = getattr(self, '_auto_expansao', None)
        if ae is None:
            ae = self.ativar_curiosidade()
        return ae.entropia_vocabulario()

    # === FASE 12 — Meta-Equação (auto-evolução dos pesos 5D) ===

    def ativar_meta_equacao(self) -> 'MetaEquacao':
        """Ativa a Meta-Equação para auto-evoluir os pesos 5D.

        Returns a instância de MetaEquacao. Use avaliar_dataset() para
        registrar o dataset de validação e evoluir() para executar.
        """
        from mcr.meta_equacao import MetaEquacao
        if not hasattr(self, '_meta_equacao') or self._meta_equacao is None:
            self._meta_equacao = MetaEquacao(self)
        return self._meta_equacao

    def evoluir_equacao(self, dataset: list = None,
                        n_geracoes: int = 10) -> dict:
        """Evolui os pesos 5D via hill climbing markoviano.

        Args:
            dataset: lista de (texto, acao_esperada). Se None, usa o
                    histórico de decisões da meta-cognição (se ativa).
            n_geracoes: número de gerações de hill climbing.

        Returns:
            dict com 'melhores_pesos', 'melhor_score', 'historico'.
        """
        me = self.ativar_meta_equacao()
        if dataset:
            me.avaliar_dataset(dataset)
        elif not me._dataset:
            # Tentar construir dataset do histórico da meta-cognição
            if self._meta and self._meta._historico:
                dataset_auto = [(r['texto'], r['acao'])
                                for r in list(self._meta._historico)
                                if r.get('confianca', 0) > 0.5]
                if dataset_auto:
                    me.avaliar_dataset(dataset_auto)
                else:
                    return {'erro': 'sem_dataset'}
            else:
                return {'erro': 'sem_dataset'}
        return me.evoluir(n_geracoes)

    def aplicar_equacao(self) -> dict:
        """Aplica os melhores pesos 5D encontrados à equação global."""
        me = getattr(self, '_meta_equacao', None)
        if me is None:
            return {'erro': 'meta_equacao_desativada'}
        return me.aplicar()

    def reverter_equacao(self) -> dict:
        """Reverte os pesos 5D para o padrão (todos = 2.0)."""
        me = getattr(self, '_meta_equacao', None)
        if me is None:
            me = self.ativar_meta_equacao()
        return me.reverter()

    def estatisticas_equacao(self) -> dict:
        """Estatísticas da meta-equação."""
        me = getattr(self, '_meta_equacao', None)
        if me is None:
            return {'status': 'meta_equacao_desativada'}
        return me.estatisticas()

    # === FASE 13 — Causalidade (P(B|do(A)) vs P(B|A)) ===

    def ativar_causalidade(self) -> 'Causalidade':
        """Ativa inferência causal (do-calculus de Pearl).

        Returns a instância de Causalidade para distinguir
        correlação (P(B|A)) de causalidade (P(B|do(A))).
        """
        from mcr.causalidade import Causalidade
        if not hasattr(self, '_causalidade') or self._causalidade is None:
            self._causalidade = Causalidade(self)
        return self._causalidade

    def efeito_causal(self, a: str, b: str) -> dict:
        """Compara P(B|A) (correlação) com P(B|do(A)) (causalidade).

        Returns:
            dict com p_b_dado_a, p_b_dado_do_a, diferenca, tipo
            ('causal', 'confundido', 'espurio')
        """
        causal = self.ativar_causalidade()
        return causal.efeito_causal(a, b)

    def confounders(self, a: str, b: str) -> list:
        """Identifica confounders de A e B (variáveis que causam ambos)."""
        causal = self.ativar_causalidade()
        return causal.identificar_confounders(a, b)

    def intervir(self, a: str, b: str) -> float:
        """Calcula P(B|do(A)) via backdoor adjustment."""
        causal = self.ativar_causalidade()
        return causal.intervir(a, b)

    def cadeia_causal(self, a: str, b: str, c: str) -> dict:
        """Verifica se A -> B -> C forma cadeia causal."""
        causal = self.ativar_causalidade()
        return causal.cadeia_causal(a, b, c)

    def d_separacao(self, a: str, b: str, c: str) -> dict:
        """Verifica se A e B são d-separados dado C."""
        causal = self.ativar_causalidade()
        return causal.d_separacao(a, b, c)

    # === FASE 14 — Raciocínio contrafactual ===

    def ativar_contrafactual(self) -> 'Contrafactual':
        """Ativa raciocínio contrafactual (3º degrau de Pearl).

        Returns a instância de Contrafactual para responder
        "o que aconteceria se...?"
        """
        from mcr.contrafactual import Contrafactual
        if not hasattr(self, '_contrafactual') or self._contrafactual is None:
            self._contrafactual = Contrafactual(self)
        return self._contrafactual

    def o_que_se(self, a_obs: str, b_obs: str,
                 a_counter: str) -> dict:
        """Contrafactual: "se A fosse a', qual seria B?"

        Args:
            a_obs: o que A foi (observado)
            b_obs: o que B foi (observado)
            a_counter: o que A teria sido (contrafactual)

        Returns:
            dict com p_b_original, p_b_contrafactual, delta, interpretacao
        """
        contra = self.ativar_contrafactual()
        return contra.o_que_se(a_obs, b_obs, a_counter)

    def necessidade_causal(self, a: str, b: str) -> dict:
        """Verifica se A foi necessário para B (sem A, B não aconteceria?)."""
        contra = self.ativar_contrafactual()
        return contra.necessidade_causal(a, b)

    def suficiencia_causal(self, a: str, b: str) -> dict:
        """Verifica se A foi suficiente para B (com A, B sempre acontece?)."""
        contra = self.ativar_contrafactual()
        return contra.suficiencia_causal(a, b)

    def cenarios_contrafactuais(self, a_obs: str, b_obs: str,
                                alternativas: list) -> list:
        """Gera múltiplos cenários contrafactuais."""
        contra = self.ativar_contrafactual()
        return contra.cenarios(a_obs, b_obs, alternativas)

    # === FASE 15 — Planejamento (MCR planeja antes de agir) ===

    def ativar_planejador(self) -> 'Planejador':
        """Ativa o planejador (simulação de futuros + busca em árvore).

        Returns a instância de Planejador para simular futuros
        e escolher a melhor sequência de ações.
        """
        from mcr.planejador import Planejador
        if not hasattr(self, '_planejador') or self._planejador is None:
            self._planejador = Planejador(self)
        return self._planejador

    def planejar(self, estado: str, profundidade: int = 3,
                 top_k: int = 3) -> dict:
        """Planeja a melhor sequência de ações via busca em árvore.

        Simula múltiplos futuros e escolhe o plano com maior
        score 5D (certeza × completude × informação × estabilidade × eficiência).

        Returns:
            dict com 'plano' (lista de ações), 'score', 'alternativas'
        """
        plan = self.ativar_planejador()
        return plan.planejar(estado, profundidade, top_k)

    def simular_acao(self, estado: str, acao: str,
                     n_passos: int = 3) -> list:
        """Simula o que acontece se a ação for tomada no estado.

        Returns: lista de {passo, acao, confianca, entropia} para cada passo.
        """
        plan = self.ativar_planejador()
        return plan.simular(estado, acao, n_passos)

    def replanificar(self, estado_anterior: str, estado_novo: str,
                     plano_anterior: list, profundidade: int = 3) -> dict:
        """Replaneja quando o estado muda inesperadamente."""
        plan = self.ativar_planejador()
        return plan.replanificar(estado_anterior, estado_novo,
                                  plano_anterior, profundidade)

    def heuristicas_estado(self, estado: str) -> dict:
        """Heurísticas do estado para guiar planejamento.

        Returns: dict com diversidade, familiaridade, coerencia.
        """
        plan = self.ativar_planejador()
        return plan.heuristicas(estado)

    # === FASE 16 — Teoria da mente (modelar outros agentes) ===

    def ativar_teoria_da_mente(self) -> 'TeoriaDaMente':
        """Ativa teoria da mente (modelar outros agentes).

        Returns a instância de TeoriaDaMente para criar agentes
        simulados, predizer suas ações, e detectar crenças falsas.
        """
        from mcr.teoria_da_mente import TeoriaDaMente
        if not hasattr(self, '_tom') or self._tom is None:
            self._tom = TeoriaDaMente(self)
        return self._tom

    def criar_agente(self, nome: str,
                     corpus: list = None,
                     conhecimento_compartilhado: bool = False):
        """Cria um agente simulado com conhecimento próprio."""
        tom = self.ativar_teoria_da_mente()
        return tom.criar_agente(nome, corpus, conhecimento_compartilhado)

    def predizer_acao_agente(self, agente, estado: str) -> dict:
        """Prediz que ação um agente faria dado o estado."""
        tom = self.ativar_teoria_da_mente()
        return tom.predizer_acao(agente, estado)

    def teste_crenca_falsa(self, agente, estado: str,
                           realidade: str = "") -> dict:
        """Teste de crença falsa (Sally-Anne)."""
        tom = self.ativar_teoria_da_mente()
        return tom.teste_crenca_falsa(agente, estado, realidade)

    def comparar_perspectivas(self, estado: str,
                              nomes_agentes: list = None) -> dict:
        """Compara como diferentes agentes vêem o mesmo estado."""
        tom = self.ativar_teoria_da_mente()
        return tom.comparar_perspectivas(estado, nomes_agentes)

    # === FASE 17 — Auto-composição (MCR que constrói MCRs) ===

    def ativar_auto_composicao(self) -> 'AutoComposicao':
        """Ativa auto-composição (constrói MCRs especializados).

        Returns a instância de AutoComposicao para observar domínios,
        criar especialistas, e orquestrar consultas.
        """
        from mcr.auto_composicao import AutoComposicao
        if not hasattr(self, '_auto_comp') or self._auto_comp is None:
            self._auto_comp = AutoComposicao(self)
        return self._auto_comp

    def compor_especialistas(self, n_clusters: int = 0) -> dict:
        """Compõe uma equipe de MCRs especializados automaticamente.

        Observa o domínio, identifica clusters de ações via NMI,
        e cria um especialista por cluster.

        Returns:
            dict com 'especialistas', 'n_clusters', 'clusters'
        """
        ac = self.ativar_auto_composicao()
        return ac.compor(n_clusters)

    def orquestrar_especialistas(self, estado: str) -> dict:
        """Roteia o input para o especialista mais adequado.

        Returns:
            dict com 'acao', 'especialista_usado', 'confianca'
        """
        ac = self.ativar_auto_composicao()
        return ac.orquestrar(estado)

    def avaliar_composicao(self, dataset: list) -> dict:
        """Avalia composição vs MCR solo (accuracy comparada)."""
        ac = self.ativar_auto_composicao()
        return ac.avaliar_composicao(dataset)

    # === FASE 18 — Auto-referência recursiva (estrutura formal, não consciência fenomênica) ===

    def ativar_auto_referencia(self) -> 'AutoReferencia':
        """Ativa auto-referência recursiva (MCR modela a si mesmo).

        O MCR constrói um modelo interno do seu próprio estado cognitivo
        e pode observá-lo recursivamente. Isto é auto-referência estrutural,
        NÃO consciência fenomênica (Pilar 9: modelo ≠ coisa modelada).

        Returns a instância de AutoReferencia.
        """
        from mcr.auto_referencia import AutoReferencia
        if not hasattr(self, '_auto_ref_inst') or self._auto_ref_inst is None:
            self._auto_ref_inst = AutoReferencia(self)
        return self._auto_ref_inst

    def auto_modelo(self) -> dict:
        """Constrói um modelo do próprio estado cognitivo.

        Returns: dict descrevendo vocabulário, ações, capacidades, entropia.
        """
        auto = self.ativar_auto_referencia()
        return auto.auto_modelo()

    def refletir(self, niveis: int = 3) -> dict:
        """Reflexão recursiva: MCR observa a si mesmo n níveis.

        Nível 1: "Eu sei X". Nível 2: "Eu sei que sei X". etc.
        Converge quando o modelo do modelo não muda mais.

        Returns: dict com 'niveis', 'convergiu', 'nivel_convergencia'.
        """
        auto = self.ativar_auto_referencia()
        return auto.refletir(niveis)

    def identidade(self) -> dict:
        """Retorna a identidade integrada do MCR (self).

        Returns: dict com 'eu_sou', 'capacidades', 'auto_modelo_self'.
        """
        auto = self.ativar_auto_referencia()
        return auto.identidade()

    def auto_modificar(self, alvo: str, valor: Any = None) -> dict:
        """O MCR modifica seu próprio comportamento.

        Args:
            alvo: capacidade a ativar/desativar/modificar
                  ('ativar_meta', 'ativar_curiosidade', etc.)

        Returns: dict com 'sucesso', 'estado_anterior', 'estado_posterior'.
        """
        auto = self.ativar_auto_referencia()
        return auto.auto_modificar(alvo, valor)

    def estranho_loop(self) -> dict:
        """Strange loop (Hofstadter): ciclo auto-referencial completo.

        Combina auto_modelo + refletir + identidade em um loop.

        Returns: dict com o ciclo completo de auto-referência.
        """
        auto = self.ativar_auto_referencia()
        return auto.estranho_loop()

    # === FASE 19 — Abstração hierárquica emergente ===

    def ativar_abstracao(self) -> 'AbstracaoHierarquica':
        """Ativa abstração hierárquica (conceitos emergentes).

        Conceitos emergem de clusters de palavras com distribuições
        P(acao|palavra) similares (NMI alta). Permite generalizar
        para palavras nunca vistas e operar em nível de conceito.

        Returns a instância de AbstracaoHierarquica.
        """
        from mcr.abstracao import AbstracaoHierarquica
        if not hasattr(self, '_abstracao') or self._abstracao is None:
            self._abstracao = AbstracaoHierarquica(self)
        return self._abstracao

    def detectar_conceitos(self) -> list:
        """Detecta conceitos emergentes (clusters de palavras via NMI).

        Returns: lista de Conceito (nível 1).
        """
        abstr = self.ativar_abstracao()
        return abstr.detectar_conceitos()

    def construir_hierarquia_conceitual(self, n_niveis: int = 3) -> dict:
        """Constrói hierarquia de abstração (palavras -> conceitos -> temas).

        Returns: dict {nivel: [Conceito, ...]}
        """
        abstr = self.ativar_abstracao()
        return abstr.construir_hierarquia(n_niveis)

    def abstrair(self, texto: str) -> dict:
        """Converte texto em representação conceitual.

        Returns: dict com 'conceitos', 'distribuicao', 'cobertura'.
        """
        abstr = self.ativar_abstracao()
        return abstr.abstrair(texto)

    def decidir_em_conceito(self, texto: str) -> tuple:
        """Decide a ação via conceitos (generaliza para palavras novas).

        Returns: (acao, confianca)
        """
        abstr = self.ativar_abstracao()
        return abstr.decidir_em_conceito(texto)

    def generalizar_palavra(self, palavra: str) -> dict:
        """Atribui palavra nova ao conceito mais próximo (zero-shot).

        Returns: dict com 'conceito', 'distribuicao', ou None.
        """
        abstr = self.ativar_abstracao()
        conceito = abstr.generalizar(palavra)
        if conceito:
            return {
                'conceito': conceito.nome,
                'nivel': conceito.nivel,
                'n_palavras': len(conceito.palavras),
                'palavras_similares': sorted(list(conceito.palavras))[:5],
                'distribuicao': conceito.distribuicao,
            }
        return {'conceito': None}
