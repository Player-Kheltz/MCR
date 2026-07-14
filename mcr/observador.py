"""mcr.observador — Observador Universal de Padrões X→Y.

Filosofia MCR: ZERO hardcode. ZERO conhecimento do sistema observado.

Observa pares (entrada, saída) de QUALQUER sistema (LLM, API, código, jogo...).
Aprende: fingerprint(entrada) → cluster_X → cluster_Y → predição.

O cluster é o "atalho" — acesso aleatório ao padrão aprendido.
Entropia delta mede quão bem o padrão foi capturado.

Arquitetura:
  1. FINGERPRINT: MCRSignature 64D de cada X e cada Y
  2. CLUSTER: agrupa fingerprints similares (DescobridorUniversal)
  3. ASSOCIA: Markov aprende P(cluster_Y | cluster_X)
  4. ENTROPIA: H(cluster_X → cluster_Y) mede determinismo
  5. EQUAÇÃO: Sigmoide 5D avalia qualidade da associação
  6. PREDIÇÃO: novo X → fp → cluster → cluster_Y previsto
"""
import re, math, time, statistics
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Set

from devia.kernel.mcr_kernel.engine import MCR as MarkovEngine
from devia.kernel.mcr_kernel.signature import MCRSignature


class ObservadorUniversal:
    """Aprende padrões X→Y de qualquer sistema observável."""

    def __init__(self, nome: str = "observador"):
        self.nome = nome
        self._pares: List[Tuple[str, str]] = []       # (X, Y) raw
        self._fp_x: List[List[float]] = []             # fingerprints de X
        self._fp_y: List[List[float]] = []             # fingerprints de Y
        self._clusters_x: Dict[str, int] = {}           # fp_key → cluster_id
        self._clusters_y: Dict[str, int] = {}           # fp_key → cluster_id
        self._mk = MarkovEngine(f"{nome}_assoc")
        self._entropia_historico: List[float] = []
        self._treinado = False

    # ═══════════════════════════════════════════════════════
    # FASE 1: OBSERVAR
    # ═══════════════════════════════════════════════════════

    def observar(self, entrada: str, saida: str):
        """Registra um par (entrada, saída) do sistema observado."""
        self._pares.append((entrada, saida))

    # ═══════════════════════════════════════════════════════
    # FASE 2: FINGERPRINT
    # ═══════════════════════════════════════════════════════

    def _fingerprint(self, texto: str) -> List[float]:
        """Gera fingerprint 64D de qualquer texto (agnóstico a domínio)."""
        if not texto:
            return [0.0] * 8
        sig = MCRSignature.extrair(texto.encode('utf-8'), rapido=False)
        if sig and sig.get('fingerprint'):
            return sig['fingerprint']
        return [0.0] * 8

    def _fp_key(self, fp: List[float]) -> str:
        """Fingerprint → chave compacta para clusterização."""
        return ",".join(str(round(x, 1)) for x in fp[:8])

    # ═══════════════════════════════════════════════════════
    # FASE 3: CLUSTERIZAR
    # ═══════════════════════════════════════════════════════

    def _clusterizar(self, fingerprints: List[List[float]],
                     limiar_sim: float = 0.85) -> Dict[str, int]:
        """Agrupa fingerprints similares via similaridade de cosseno."""
        clusters = {}
        proximo_id = 0

        for i, fp in enumerate(fingerprints):
            key = self._fp_key(fp)
            if key in clusters:
                continue
            # Encontra o cluster mais próximo
            melhor_id = None
            melhor_sim = 0.0
            for exist_key, cid in clusters.items():
                exist_fp = [float(x) for x in exist_key.split(",")]
                sim = self._cosine_sim(fp, exist_fp)
                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_id = cid
            if melhor_id is not None and melhor_sim > limiar_sim:
                clusters[key] = melhor_id
            else:
                clusters[key] = proximo_id
                proximo_id += 1

        return clusters

    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            n = min(len(a), len(b))
            a, b = a[:n], b[:n]
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    # ═══════════════════════════════════════════════════════
    # FASE 4: TREINAR
    # ═══════════════════════════════════════════════════════

    def treinar(self):
        """Aprende associações X→Y a partir dos pares observados."""
        if len(self._pares) < 5:
            return self

        # 1. Gera fingerprints
        self._fp_x = [self._fingerprint(x) for x, _ in self._pares]
        self._fp_y = [self._fingerprint(y) for _, y in self._pares]

        # 2. Clusteriza X e Y independentemente
        self._clusters_x = self._clusterizar(self._fp_x)
        self._clusters_y = self._clusterizar(self._fp_y)

        # 2b. Mapeamento reverso cluster_Y → ação mais comum
        from collections import Counter
        cluster_acoes = {}
        for i, (_, y) in enumerate(self._pares):
            fp_key = self._fp_key(self._fp_y[i])
            cid = self._clusters_y.get(fp_key, 0)
            acao_base = y.split(':')[0] if ':' in y else y
            cluster_acoes.setdefault(cid, Counter())[acao_base] += 1
        self._cluster_para_acao = {
            cid: counter.most_common(1)[0][0]
            for cid, counter in cluster_acoes.items()
        }

        # 3. Mede entropia ANTES de aprender
        H_antes = self._mk.entropia_media()

        # 4. Aprende associações cluster_X → cluster_Y
        for i, (x, y) in enumerate(self._pares):
            fp_x = self._fp_x[i]
            fp_y = self._fp_y[i]
            cid_x = self._clusters_x.get(self._fp_key(fp_x), 0)
            cid_y = self._clusters_y.get(self._fp_key(fp_y), 0)
            estado = f"CX{cid_x}"
            acao = f"CY{cid_y}"
            self._mk.aprender(estado, acao)
            self._mk.aprender(estado, acao)  # reforço

        # 5. Mede entropia DEPOIS
        H_depois = self._mk.entropia_media()
        delta_H = H_depois - H_antes
        self._entropia_historico.append(delta_H)

        self._treinado = True
        return self

    # ═══════════════════════════════════════════════════════
    # FASE 5: PREDIZER
    # ═══════════════════════════════════════════════════════

    def predizer(self, entrada: str) -> Optional[int]:
        """Prediz cluster de saída para uma nova entrada (atalho = cluster)."""
        if not self._treinado:
            return None
        fp = self._fingerprint(entrada)
        key = self._fp_key(fp)
        # Encontra o cluster mais próximo
        cid_x = None
        melhor_sim = 0.0
        for exist_key, cid in self._clusters_x.items():
            exist_fp = [float(x) for x in exist_key.split(",")]
            sim = self._cosine_sim(fp, exist_fp)
            if sim > melhor_sim:
                melhor_sim = sim
                cid_x = cid
        if cid_x is None:
            return None
        estado = f"CX{cid_x}"
        pred, conf = self._mk.predizer(estado)
        if pred and str(pred).startswith("CY"):
            return int(str(pred).replace("CY", ""))
        return None

    def predizer_com_confianca(self, entrada: str) -> Tuple[Optional[int], float, float]:
        """Prediz com confiança e entropia do estado."""
        if not self._treinado:
            return None, 0.0, 1.0
        fp = self._fingerprint(entrada)
        key = self._fp_key(fp)
        cid_x = None
        melhor_sim = 0.0
        for exist_key, cid in self._clusters_x.items():
            exist_fp = [float(x) for x in exist_key.split(",")]
            sim = self._cosine_sim(fp, exist_fp)
            if sim > melhor_sim:
                melhor_sim = sim
                cid_x = cid
        if cid_x is None:
            return None, 0.0, 1.0
        estado = f"CX{cid_x}"
        pred, conf = self._mk.predizer(estado)
        H = self._mk.entropia(estado) if estado in self._mk.transicoes else 1.0
        if pred and str(pred).startswith("CY"):
            return int(str(pred).replace("CY", "")), conf, H
        return None, conf, H

    def _mapear_cluster_para_acao(self, cluster_id: int) -> Optional[str]:
        """Mapeia cluster_Y de volta para ação original (ex: 'gerar_npc')."""
        if not hasattr(self, '_cluster_para_acao'):
            return None
        return self._cluster_para_acao.get(cluster_id)

    # ═══════════════════════════════════════════════════════
    # MÉTRICAS
    # ═══════════════════════════════════════════════════════

    def entropia_delta(self) -> float:
        """ΔH do último treinamento. Negativo = aprendeu."""
        return self._entropia_historico[-1] if self._entropia_historico else 0.0

    def cobertura(self) -> float:
        """Fração de estados de X que têm associação aprendida."""
        if not self._treinado:
            return 0.0
        total_x = len(set(self._clusters_x.values()))
        aprendidos = sum(1 for cid in set(self._clusters_x.values())
                        if f"CX{cid}" in self._mk.transicoes)
        return aprendidos / max(total_x, 1)

    def estatisticas(self) -> Dict:
        mk_stats = self._mk.stats()
        return {
            'pares_observados': len(self._pares),
            'clusters_X': len(set(self._clusters_x.values())),
            'clusters_Y': len(set(self._clusters_y.values())),
            'delta_H': round(self.entropia_delta(), 4),
            'cobertura': round(self.cobertura(), 3),
            'markov_estados': mk_stats.get('estados', 0),
            'markov_transicoes': mk_stats.get('transicoes', 0),
        }

    # ═══════════════════════════════════════════════════════
    # F3: AUTO-EXPANSÃO — gera variações para melhorar cobertura
    # ═══════════════════════════════════════════════════════

    def clusters_fracos(self) -> List[int]:
        """Retorna clusters X com alta entropia (poucos exemplos)."""
        if not self._treinado:
            return []
        fracos = []
        for cid in set(self._clusters_x.values()):
            estado = f"CX{cid}"
            if estado in self._mk.transicoes:
                H = self._mk.entropia(estado)
                if H > 0.5:  # alta entropia = incerto
                    fracos.append(cid)
        return fracos

    def precisa_expandir(self) -> bool:
        """Entropia decide: precisa de mais dados?"""
        return self.entropia_delta() > 0.01 or len(self.clusters_fracos()) > 0

    # ═══════════════════════════════════════════════════════
    # F4: EQUAÇÃO avalia qualidade do observador
    # ═══════════════════════════════════════════════════════

    def avaliar_qualidade(self) -> Dict:
        """Equação MCR avalia o próprio observador."""
        if not self._treinado:
            return {'nota': 0.0, 'pronto': False}
        import math
        certeza = self.cobertura()
        completude = min(1.0, len(self._pares) / 100.0)
        informacao = max(0.0, -self.entropia_delta())
        estabilidade = 0.5  # neutro até ter histórico
        eficiencia = 1.0 / math.log2(max(len(set(self._clusters_x.values())), 1) + 1)
        soma = (certeza*3 + completude*3 + informacao*2 + estabilidade*2 + eficiencia*1) / 11.0
        nota = 1.0 / (1.0 + math.exp(-3.0 * (soma - 0.4)))
        return {
            'nota': round(nota, 3),
            'pronto': nota > 0.5,
            'certeza': round(certeza, 3),
            'completude': round(completude, 3),
            'delta_H': round(self.entropia_delta(), 4),
        }
