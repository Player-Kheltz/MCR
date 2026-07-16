"""mcr.multimodal — FASE 6: Assinatura unificada texto/audio/imagem via NMI.

Cada modalidade (texto, audio, imagem, codigo) e convertida para features
markovianas. Quando duas modalidades compartilham contexto de acao, suas
assinaturas convergem via NMI — MCR descobre a equivalencia cross-modal
sem dicionario, sem embedding, sem GPU, sem rede neural.

O insight fundamental:
  Se "fogo" (texto) e um som de fogo (audio) aparecem ambos com a acao
  "criar_monstro", suas assinaturas markovianas compartilham features
  acao:criar_monstro. NMI detecta essa convergencia — cross-modal puro.

  "fire" (EN) e "fogo" (PT) tambem convergem se compartilham acoes.
  Traducao sem dicionario.

Pilar 1: P(feature | conceito) — tudo e transicao markoviana
Pilar 2: NMI descobre cross-modal (sem threshold hardcoded)
Pilar 3: mesmo motor (MCRCoupling), qualquer modalidade
Pilar 5: alimentar -> recuperar -> aprender (loop fechado)

Uso:
    from mcr.multimodal import MCRMultimodal
    mm = MCRMultimodal()
    mm.alimentar("texto", "fogo", "criar_monstro")
    mm.alimentar("audio", som_fogo_bytes, "criar_monstro", chave="som_fogo")
    mm.alimentar("imagem", img_fogo_bytes, "criar_monstro", chave="img_fogo")

    # Cross-modal: dado audio, encontra texto
    resultados = mm.recuperar_crossmodal("audio", som_fogo_bytes, "texto")
    # -> [("fogo", "texto", 0.85), ...]

    # Traducao cross-modal
    texto = mm.traduzir("audio", som_fogo_bytes, "texto")
    # -> "fogo"
"""
import re
import math
import struct
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from mcr.coupling import MCRCoupling


class MCRMultimodal:
    """MCR multimodal — assinatura unificada via NMI cross-modal.

    Cada modalidade e convertida para features markovianas sinteticas
    e alimentada num MCRCoupling subjacente. A chave do conceito
    (e.g. "fogo", "som_fogo") e uma palavra reconhecivel que o coupling
    associa com a acao. Quando duas modalidades compartilham a acao,
    NMI entre suas assinaturas revela a equivalencia.

    Zero dependencias externas: audio/imagem sao processados como bytes
    brutos, sem numpy/PIL/scipy. Apenas matematica pura.
    """

    def __init__(self):
        self.coupling = MCRCoupling()
        self._conceitos: Dict[str, Tuple[str, object]] = {}
        self._modalidades: set = set()
        self._chave_para_acoes: Dict[str, set] = defaultdict(set)

    # ─── Extracao de features por modalidade ───────────────────

    def _extrair_features_modal(self, modalidade: str, dados) -> str:
        """Extrai features markovianas unificadas de qualquer modalidade.

        Texto: passado diretamente (MCRCoupling ja extrai tokens, bytes,
               bigrams, trigrams, posicoes, contexto).
        Audio: histograma de bytes (16 bins) + taxa de cruzamento por zero
               + envelope de energia (4 segmentos) -> tokens sinteticos.
        Imagem: histograma de cor (R/G/B 8 bins cada) + distribuicao
                espacial (4 quadrantes) -> tokens sinteticos.
        Codigo: tratado como texto (ja e texto).

        Pilar 1: cada token e uma transicao P(token | conceito).
        Pilar 3: metodo generico, qualquer modalidade vira tokens.
        """
        if modalidade == "texto" or modalidade == "codigo":
            return str(dados) if not isinstance(dados, bytes) else dados.decode('utf-8', errors='replace')

        if isinstance(dados, str):
            dados = dados.encode('utf-8')

        if not dados:
            return ""

        if modalidade == "audio":
            return self._extrair_features_audio(dados)
        elif modalidade == "imagem":
            return self._extrair_features_imagem(dados)
        else:
            return self._extrair_features_generico(dados)

    def _extrair_features_audio(self, dados: bytes) -> str:
        """Extrai features de audio a partir de bytes brutos.

        Sem numpy/scipy: usa apenas matematica pura.

        3 grupos de features:
        1. Histograma de bytes (16 bins de 16 valores cada) — timbre
        2. Taxa de cruzamento por zero (4 segmentos) — ritmo/frequencia
        3. Energia media (4 segmentos) — volume/intensidade

        Cada feature vira um token puramente alfabetico (letras a-z)
        para ser reconhecido pelo regex do coupling: [a-z]{3,}.
        Formato: prefixo + bin_letter + level_letter
        Ex: auhaa, auhab, ..., auhpj (16 bins x 10 niveis)
        """
        n = len(dados)
        if n == 0:
            return ""

        tokens = []
        bin_letters = "abcdefghijklmnop"
        lvl_letters = "abcdefghij"

        # 1. Histograma de bytes — 16 bins
        bins = [0] * 16
        for b in dados:
            bins[b >> 4] += 1
        total = sum(bins) or 1
        for i, c in enumerate(bins):
            pct = c / total
            nivel = min(int(pct * 20), 9)
            if nivel > 0:
                tokens.append(f"auh{bin_letters[i]}{lvl_letters[nivel]}")

        # 2. Taxa de cruzamento por zero — 4 segmentos
        amostras = []
        for i in range(0, min(n, 4096), 2):
            if i + 1 < n:
                val = struct.unpack_from('<h', dados, i)[0]
                amostras.append(val)

        if len(amostras) > 1:
            seg_size = len(amostras) // 4 or 1
            for seg in range(4):
                inicio = seg * seg_size
                fim = min(inicio + seg_size, len(amostras))
                zcr = 0
                for j in range(inicio + 1, fim):
                    if (amostras[j] >= 0) != (amostras[j - 1] >= 0):
                        zcr += 1
                taxa = zcr / max(fim - inicio - 1, 1)
                nivel = min(int(taxa * 20), 9)
                tokens.append(f"auz{lvl_letters[seg]}{lvl_letters[nivel]}")

            # 3. Energia media — 4 segmentos
            energias = []
            for seg in range(4):
                inicio = seg * seg_size
                fim = min(inicio + seg_size, len(amostras))
                energia = sum(a * a for a in amostras[inicio:fim]) / max(fim - inicio, 1)
                energias.append(energia)

            max_eng = max(energias) or 1
            for seg, eng in enumerate(energias):
                norm = eng / max_eng
                nivel = min(int(norm * 10), 9)
                tokens.append(f"aue{lvl_letters[seg]}{lvl_letters[nivel]}")

        return ' '.join(tokens)

    def _extrair_features_imagem(self, dados: bytes) -> str:
        """Extrai features de imagem a partir de bytes brutos.

        Sem PIL/numpy: usa apenas bytes brutos.

        3 grupos de features:
        1. Histograma de cor — R, G, B (8 bins cada canal)
        2. Luminancia media (4 quadrantes) — brilho espacial
        3. Variancia de cor (4 quadrantes) — contraste espacial

        Tokens puramente alfabeticos para o regex do coupling.
        Ex: imraa, imrbj, imlaa, imvcj
        """
        n = len(dados)
        if n == 0:
            return ""

        tokens = []
        bin8_letters = "abcdefgh"
        lvl_letters = "abcdefghij"

        # 1. Histograma de cor — assumir RGB ou bytes brutos
        r_bins = [0] * 8
        g_bins = [0] * 8
        b_bins = [0] * 8

        for i in range(0, min(n, 3072), 3):
            if i < n:
                r_bins[dados[i] >> 5] += 1
            if i + 1 < n:
                g_bins[dados[i + 1] >> 5] += 1
            if i + 2 < n:
                b_bins[dados[i + 2] >> 5] += 1

        total = sum(r_bins) or 1
        for i, c in enumerate(r_bins):
            pct = c / total
            if pct > 0.01:
                nivel = min(int(pct * 20), 9)
                tokens.append(f"imr{bin8_letters[i]}{lvl_letters[nivel]}")
        for i, c in enumerate(g_bins):
            pct = c / total
            if pct > 0.01:
                nivel = min(int(pct * 20), 9)
                tokens.append(f"img{bin8_letters[i]}{lvl_letters[nivel]}")
        for i, c in enumerate(b_bins):
            pct = c / total
            if pct > 0.01:
                nivel = min(int(pct * 20), 9)
                tokens.append(f"imb{bin8_letters[i]}{lvl_letters[nivel]}")

        # 2. Luminancia e variancia por quadrante (4 quadrantes)
        pixels = []
        for i in range(0, min(n, 3072), 3):
            if i + 2 < n:
                r, g, b = dados[i], dados[i + 1], dados[i + 2]
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                pixels.append(lum)

        if pixels:
            seg_size = len(pixels) // 4 or 1
            for q in range(4):
                inicio = q * seg_size
                fim = min(inicio + seg_size, len(pixels))
                seg_pixels = pixels[inicio:fim]
                if not seg_pixels:
                    continue
                media = sum(seg_pixels) / len(seg_pixels)
                variancia = sum((p - media) ** 2 for p in seg_pixels) / len(seg_pixels)

                nivel_l = min(int(media / 25.6), 9)
                nivel_v = min(int(math.sqrt(variancia) / 25.6), 9)
                tokens.append(f"iml{lvl_letters[q]}{lvl_letters[nivel_l]}")
                tokens.append(f"imv{lvl_letters[q]}{lvl_letters[nivel_v]}")

        return ' '.join(tokens)

    def _extrair_features_generico(self, dados: bytes) -> str:
        """Extrai features de bytes brutos para modalidades desconhecidas.

        Usa histograma de bytes (16 bins) + entropia de Shannon.
        Tokens puramente alfabeticos para o regex do coupling.
        """
        n = len(dados)
        if n == 0:
            return ""

        bin_letters = "abcdefghijklmnop"
        lvl_letters = "abcdefghij"

        bins = [0] * 16
        for b in dados:
            bins[b >> 4] += 1

        total = sum(bins) or 1
        tokens = []
        for i, c in enumerate(bins):
            pct = c / total
            if pct > 0.01:
                nivel = min(int(pct * 20), 9)
                tokens.append(f"gn{bin_letters[i]}{lvl_letters[nivel]}")

        h = 0.0
        for c in bins:
            if c > 0:
                p = c / total
                h -= p * math.log2(p)
        nivel_h = min(int(h / 0.4), 9)
        tokens.append(f"gnh{lvl_letters[nivel_h]}")

        return ' '.join(tokens)

    # ─── Geracao de chaves ─────────────────────────────────────

    def _gerar_chave(self, modalidade: str, dados) -> str:
        """Gera chave de conceito a partir da modalidade e dados.

        Para texto: usa o proprio texto (primeiras palavras).
        Para audio/imagem: gera hash estavel dos bytes.
        """
        if modalidade == "texto" or modalidade == "codigo":
            if isinstance(dados, str):
                palavras = re.findall(r'[a-zà-ÿ0-9]{3,}', dados.lower())
                if palavras:
                    return '_'.join(palavras[:3])
        return f"{modalidade}_{abs(hash(dados)) & 0xFFFFFF}"

    def _limpar_chave(self, chave: str) -> str:
        """Limpa chave para ser reconhecida pelo regex do coupling (3+ chars)."""
        limpa = re.sub(r'[^a-z0-9]', '', chave.lower())
        if len(limpa) < 3:
            limpa = f"modal{limpa}"
        return limpa

    # ─── API publica ───────────────────────────────────────────

    def alimentar(self, modalidade: str, dados, acao: str,
                  chave: Optional[str] = None) -> str:
        """Alimenta par (modalidade, dados, acao) no MCR multimodal.

        Extrai features da modalidade, cria uma chave de conceito, e
        alimenta o MCRCoupling subjacente. A chave e uma palavra
        reconhecivel que o coupling associa com a acao.

        Pilar 1: P(feature | conceito) — transicao markoviana.
        Pilar 5: alimentar -> recuperar -> aprender (loop).

        Args:
            modalidade: "texto", "audio", "imagem", "codigo"
            dados: str, bytes, ou objeto serializavel
            acao: acao associada ao conceito
            chave: identificador opcional do conceito (auto se None)
        Returns:
            chave do conceito alimentado
        """
        if chave is None:
            chave = self._gerar_chave(modalidade, dados)

        texto_features = self._extrair_features_modal(modalidade, dados)
        chave_limpa = self._limpar_chave(chave)

        texto_completo = f"{chave_limpa} {texto_features}"
        self.coupling.alimentar(texto_completo, acao)

        self._conceitos[chave] = (modalidade, dados)
        self._modalidades.add(modalidade)
        self._chave_para_acoes[chave].add(acao)

        return chave

    def _dist_acao_conceito(self, texto: str) -> Dict[str, float]:
        """Extrai a distribuicao de acoes de um texto de features.

        Usa coupling._dist_palavras que agrega P(acao|palavra) de todas
        as palavras no texto. As feature tokens (auh03, imr79, etc.)
        sao palavras que o coupling ja conhece — suas distribuicoes de
        acao revelam quais conceitos elas pertencem.

        O sinal cross-modal esta aqui: feature tokens unicos a "fogo"
        terao acao:criar_monstro, enquanto tokens unicos a "agua" terao
        acao:curar. Tokens compartilhados terao distribuicoes mistas,
        mas o NMI entre distribuicoes ainda distingue os conceitos.
        """
        dist = self.coupling._dist_palavras(texto)
        return dist or {}

    def _sig_acao(self, chave: str) -> Dict[str, int]:
        """Extrai apenas features acao:* da assinatura de um conceito.

        Isola o sinal cross-modal (acoes compartilhadas) do ruido
        (feature tokens compartilhados entre modalidades).
        """
        sig = self.coupling._assinatura_palavra(chave)
        if not sig:
            return {}
        return {k: v for k, v in sig.items() if k.startswith("acao:")}

    def recuperar_crossmodal(self, modalidade_query: str, dados_query,
                             modalidade_alvo: Optional[str] = None,
                             top_n: int = 5) -> List[Tuple[str, str, float]]:
        """Dado um query numa modalidade, encontra conceitos similares.

        Extrai a distribuicao de acao do query (via feature tokens) e
        compara via NMI com a distribuicao de acao de cada conceito.
        O sinal cross-modal esta nas ACOES compartilhadas — feature
        tokens unicos a cada conceito carregam sua assinatura de acao.

        Pilar 2: NMI descobre equivalencia, sem threshold hardcoded.
        Pilar 3: funciona com qualquer combinacao de modalidades.

        Args:
            modalidade_query: modalidade do query ("audio", "texto", etc)
            dados_query: dados do query
            modalidade_alvo: filtrar resultados por modalidade (None = todas)
            top_n: maximo de resultados
        Returns:
            lista de (chave, modalidade, score_nmi) ordenada por score desc
        """
        texto_query = self._extrair_features_modal(modalidade_query, dados_query)
        chave_query = self._limpar_chave(self._gerar_chave(modalidade_query, dados_query))
        texto_completo = f"{chave_query} {texto_query}"

        # Distribuicao de acao do query (feature tokens -> P(acao|token))
        dist_query = self._dist_acao_conceito(texto_completo)
        if not dist_query:
            # Fallback: assinatura direta (conceito ja alimentado)
            sig_q = self.coupling._assinatura_palavra(chave_query)
            if not sig_q:
                return []
            dist_query = {k.replace("acao:", ""): v
                          for k, v in sig_q.items() if k.startswith("acao:")}
        if not dist_query:
            return []

        resultados = []
        for chave, (modal, _) in self._conceitos.items():
            if modalidade_alvo and modal != modalidade_alvo:
                continue

            chave_limpa = self._limpar_chave(chave)
            if chave_limpa == chave_query:
                continue

            # Apenas features acao:* do candidato (sinal cross-modal puro)
            sig_acao_cand = self._sig_acao(chave_limpa)
            if not sig_acao_cand:
                continue

            # Converter para mesmo formato: {acao: valor}
            dist_cand = {k.replace("acao:", ""): v for k, v in sig_acao_cand.items()}

            # NMI entre distribuicoes de acao
            nmi = self.coupling._nmi(dist_query, dist_cand)
            if nmi > 0:
                resultados.append((chave, modal, round(nmi, 4)))

        resultados.sort(key=lambda x: -x[2])
        return resultados[:top_n]

    def traduzir(self, modalidade_origem: str, dados,
                 modalidade_destino: str = "texto") -> Optional[str]:
        """Traduz dados de uma modalidade para outra via NMI cross-modal.

        Dado um audio ou imagem, encontra o conceito de texto mais
        similar. Isso e "traducao cross-modal" — MCR descobre que
        um som de fogo corresponde a "fogo" (texto) sem dicionario.

        Pilar 5: usar -> recuperar -> aprender (loop).

        Args:
            modalidade_origem: modalidade dos dados de entrada
            dados: dados de entrada (bytes ou str)
            modalidade_destino: modalidade alvo (default: "texto")
        Returns:
            chave do melhor conceito na modalidade destino, ou None
        """
        resultados = self.recuperar_crossmodal(
            modalidade_origem, dados, modalidade_destino, top_n=1
        )
        if resultados:
            return resultados[0][0]
        return None

    def avaliar_crossmodal(self, modalidade_query: str, dados_query,
                           modalidade_cand: str, dados_cand) -> float:
        """Equacao 5D avalia a qualidade de um match cross-modal.

        5 dimensoes organicas para cross-modal:
        - CERTEZA: NMI entre distribuicoes de acao — fidelidade cross-modal
        - COMPLETUDE: fracao de acoes do query presentes no candidato
        - INFORMACAO: entropia Shannon normalizada do candidato
        - ESTABILIDADE: gaussiana da entropia (pune extremos)
        - EFICIENCIA: 1/log2(n_modalidades_envolvidas + 1)

        Sem threshold hardcoded — Equacao 5D e a fonte da verdade.

        Returns:
            nota 0-1 via sigmoide 5D
        """
        try:
            from mcr.equacao_mcr import avaliar_5d
        except ImportError:
            from equacao_mcr import avaliar_5d

        texto_q = self._extrair_features_modal(modalidade_query, dados_query)
        chave_q = self._limpar_chave(self._gerar_chave(modalidade_query, dados_query))
        dist_q = self._dist_acao_conceito(f"{chave_q} {texto_q}")
        if not dist_q:
            sig_q = self.coupling._assinatura_palavra(chave_q)
            dist_q = {k.replace("acao:", ""): v
                      for k, v in (sig_q or {}).items() if k.startswith("acao:")}

        texto_c = self._extrair_features_modal(modalidade_cand, dados_cand)
        chave_c = self._limpar_chave(self._gerar_chave(modalidade_cand, dados_cand))
        sig_acao_c = self._sig_acao(chave_c)
        if not sig_acao_c:
            dist_c = self._dist_acao_conceito(f"{chave_c} {texto_c}")
            sig_acao_c = {f"acao:{k}": v for k, v in dist_c.items()}

        if not dist_q or not sig_acao_c:
            return 0.0

        dist_c = {k.replace("acao:", ""): v for k, v in sig_acao_c.items()}

        certeza = self.coupling._nmi(dist_q, dist_c)

        acoes_q = set(dist_q.keys())
        acoes_c = set(dist_c.keys())
        completude = len(acoes_q & acoes_c) / len(acoes_q) if acoes_q else 0.0

        informacao = self.coupling._entropia_dist(sig_acao_c)
        estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * 0.2 ** 2))

        n_mods = len({modalidade_query, modalidade_cand})
        eficiencia = 1.0 / math.log2(n_mods + 1)

        return avaliar_5d(certeza, completude, informacao,
                          estabilidade, eficiencia)

    def similaridade_crossmodal(self, chave_a: str, chave_b: str) -> float:
        """NMI direto entre dois conceitos conhecidos (cross-modal ou nao).

        Args:
            chave_a, chave_b: chaves de conceitos alimentados
        Returns:
            NMI entre assinaturas, 0-1
        """
        sig_a = self.coupling._assinatura_palavra(self._limpar_chave(chave_a))
        sig_b = self.coupling._assinatura_palavra(self._limpar_chave(chave_b))
        if not sig_a or not sig_b:
            return 0.0
        return self.coupling._nmi(sig_a, sig_b)

    def listar_conceitos(self, modalidade: Optional[str] = None) -> List[Tuple[str, str]]:
        """Lista conceitos conhecidos, opcionalmente filtrados por modalidade."""
        if modalidade:
            return [(k, m) for k, (m, _) in self._conceitos.items() if m == modalidade]
        return [(k, m) for k, (m, _) in self._conceitos.items()]

    def predizer_acao(self, modalidade: str, dados,
                      acao_markov: str = None) -> Tuple[Optional[str], float]:
        """Prediz a acao associada a dados de qualquer modalidade.

        Usa o MCRCoupling subjacente para classificar os dados.
        Cross-modal: um audio pode ativar a mesma acao que um texto.

        Args:
            modalidade: modalidade dos dados
            dados: dados de entrada
            acao_markov: predicao anterior do Markov (opcional)
        Returns:
            (acao, confianca)
        """
        texto = self._extrair_features_modal(modalidade, dados)
        chave = self._limpar_chave(self._gerar_chave(modalidade, dados))
        texto_completo = f"{chave} {texto}"
        return self.coupling.decidir(
            texto_completo,
            (acao_markov, 0.5 if acao_markov else 0.0)
        )

    def estatisticas(self) -> Dict:
        return {
            'conceitos': len(self._conceitos),
            'modalidades': sorted(self._modalidades),
            'conceitos_por_modalidade': {
                m: sum(1 for _, (mod, _) in self._conceitos.items() if mod == m)
                for m in self._modalidades
            },
            'coupling': self.coupling.estatisticas(),
        }

    def save(self, caminho: str) -> None:
        self.coupling.save(caminho)

    def load(self, caminho: str) -> bool:
        return self.coupling.load(caminho)
