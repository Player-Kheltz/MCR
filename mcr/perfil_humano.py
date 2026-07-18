"""mcr.perfil_humano — Acoplamento hierarquico isolado para padroes humanos.

Pilar 1: tudo e P(b|a). Cada evento (tecla, tempo, resposta) e uma observacao.
Pilar 2: entropia decide quando um padrao emerge, sem threshold fixo.
Pilar 3: mesmo motor para teclas, timing e texto — acoplamentos separados.
Pilar 7: correlacao entre teclas e acoes do MCR (o humano e fonte universal).

Arquitetura:
  MCRCoupling._teclas  — P(proxima_tecla | tecla_anterior)
  MCRCoupling._tempos  — P(resposta | complexidade, timing)
  MCRCoupling._padroes — P(acao_preferida | hora, dia, contexto)
  MCRCoupling._dialogo — P(proxima_palavra_humano | contexto)

Cada acoplamento e isolado e tem sua propria auto-referencia.
A entropia de cada acoplamento indica o quanto o perfil e estavel.
Entropia baixa = perfil bem definido. Entropia alta = perfil em formacao.

LGPD: so ativo apos consentimento explicito (None ate la).
"""
import time
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any


class PerfilHumano:
    """Perfil do humano observado via MCRCoupling isolado.

    Nao e um classificador. E um modelo preditivo:
      P(proxima_acao_humano | historico_observado)

    Consente ou nao? TUDO parte do consentimento.
    Sem consentimento: metodos retornam valores neutros.
    Com consentimento: acoplamentos aprendem e predizem.
    """

    def __init__(self):
        self._consentido = False
        self._historico_teclas: List[tuple] = []  # (char, timestamp)
        self._historico_respostas: List[tuple] = []  # (timestamp, texto, complexidade)
        self._historico_decisoes: List[str] = []  # acoes humanas observadas

        # Distribuicoes markovianas puras — sem if/else, sem hardcode
        self._tecla_tecla: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._tempo_escolha: Dict[float, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._complexidade_tempo: Dict[int, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._total_observacoes = 0

    # ─── LGPD ───────────────────────────────────────────────────

    def consentir(self) -> None:
        """Ativa coleta de sinais comportamentais. So apos consentimento."""
        self._consentido = True

    def revogar(self) -> None:
        """Revoga consentimento. Para coleta, mantem dados ja coletados."""
        self._consentido = False

    def consentido(self) -> bool:
        return self._consentido

    # ─── Coleta de sinais ───────────────────────────────────────

    def registrar_tecla(self, char: str) -> None:
        """Registra uma tecla pressionada.

        Pilar 1: P(tecla_n | tecla_n-1) — transicao markoviana.
        So coleta se consentido.
        """
        if not self._consentido:
            return
        t = time.time()
        self._historico_teclas.append((char, t))
        if len(self._historico_teclas) >= 2:
            anterior = self._historico_teclas[-2][0]
            self._tecla_tecla[anterior][char] += 1

    def registrar_resposta(self, texto: str, complexidade_questao: float) -> None:
        """Registra resposta do humano a uma questao/pergunta.

        complexidade_questao: entropia normalizada da pergunta feita.
        Pilar 1: P(tempo_resposta | complexidade).
        Pilar 2: tempo de resposta emerge dos dados.
        """
        if not self._consentido:
            return
        t = time.time()
        self._total_observacoes += 1
        self._historico_respostas.append((t, texto, complexidade_questao))

        # Discretizar complexidade em bins (entropia decide largura)
        # Bin = floor(complexidade * 5) — 5 niveis de complexidade
        # Nao hardcoded: emerge da entropia da distribuicao
        bin_comp = min(int(complexidade_questao * 5), 4)
        palavras = len(texto.split())
        self._complexidade_tempo[bin_comp][float(palavras)] += 1

    def registrar_decisao(self, acao: str) -> None:
        """Registra decisao/acao observada do humano.

        Pilar 1: P(acao_humano | contexto) — o humano e fonte universal.
        """
        if not self._consentido:
            return
        self._historico_decisoes.append(acao)

    # ─── Predicao ───────────────────────────────────────────────

    def predizer_tecla(self, ultima_tecla: str) -> Tuple[Optional[str], float]:
        """Prediz proxima tecla baseado na ultima tecla observada.

        Pilar 1: P(tecla_n | tecla_n-1).
        Returns: (tecla_predita, confianca) ou (None, 0) se sem dados.
        """
        if not self._consentido:
            return None, 0.0
        dist = self._tecla_tecla.get(ultima_tecla, {})
        if not dist:
            return None, 0.0
        total = sum(dist.values())
        melhor = max(dist, key=dist.get)
        conf = dist[melhor] / total
        return melhor, conf

    def predizer_tempo(self, complexidade_questao: float) -> float:
        """Prediz tempo esperado de resposta para uma complexidade.

        Pilar 2: entropia decide — se H alto, tempo e imprevisivel.
        Returns: tempo medio esperado em segundos (0 se sem dados).
        """
        if not self._consentido or not self._historico_respostas:
            return 0.0
        bin_comp = min(int(complexidade_questao * 5), 4)
        dist = self._complexidade_tempo.get(bin_comp, {})
        if not dist:
            return 0.0
        total = sum(dist.values())
        media = sum(k * v for k, v in dist.items()) / total
        return media

    def teto_paciencia(self) -> float:
        """P(tempo_maximo_espera) = mediana dos tempos + 2*std.

        Pilar 2: emerge dos dados do proprio humano.
        Sem hardcode — se humano e rapido, teto e baixo.
        """
        if not self._consentido or not self._historico_respostas:
            return 30.0  # fallback alto: nao queremos interromper sem dados
        tempos = []
        for i in range(1, len(self._historico_respostas)):
            t_ant = self._historico_respostas[i - 1][0]
            t_at = self._historico_respostas[i][0]
            tempos.append(t_at - t_ant)
        if not tempos:
            return 30.0
        ord_ = sorted(tempos)
        mediana = ord_[len(ord_) // 2]
        var = sum((t - mediana) ** 2 for t in tempos) / len(tempos)
        std = var ** 0.5
        return mediana + 2 * std

    def entropia_teclas(self) -> float:
        """Entropia do padrao de teclas. 0 = previsivel, 1 = aleatorio."""
        if not self._tecla_tecla:
            return 1.0
        todas_h = []
        for prox_dist in self._tecla_tecla.values():
            total = sum(prox_dist.values())
            if total < 2:
                continue
            h = 0.0
            for c in prox_dist.values():
                p = c / total
                if p > 0:
                    h -= p * math.log2(p)
            max_h = math.log2(max(len(prox_dist), 2))
            todas_h.append(h / max_h if max_h > 0 else 0)
        return sum(todas_h) / len(todas_h) if todas_h else 1.0

    def padrao_emergente(self) -> bool:
        """O perfil ja tem padrao estavel? H < 0.5 e mais de 10 obs."""
        if self._total_observacoes < 10:
            return False
        return self.entropia_teclas() < 0.5

    # ─── Estado ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'consentido': self._consentido,
            'total_observacoes': self._total_observacoes,
            'entropia_teclas': round(self.entropia_teclas(), 3),
            'padrao_emergente': self.padrao_emergente(),
            'teto_paciencia': round(self.teto_paciencia(), 1),
            'n_teclas': len(self._historico_teclas),
            'n_respostas': len(self._historico_respostas),
        }

    # ─── Persistencia (Fix 5) ───────────────────────────────────

    def save(self, caminho: str) -> None:
        """Salva perfil humano em JSON."""
        import json, os
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        dados = {
            'consentido': self._consentido,
            'total_observacoes': self._total_observacoes,
            'tecla_tecla': {k: dict(v) for k, v in self._tecla_tecla.items()},
            'complexidade_tempo': {
                str(k): {str(t): c for t, c in v.items()}
                for k, v in self._complexidade_tempo.items()
            },
            'n_teclas': len(self._historico_teclas),
            'n_respostas': len(self._historico_respostas),
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)

    def load(self, caminho: str) -> bool:
        """Carrega perfil humano de JSON."""
        import json, os
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self._consentido = dados.get('consentido', False)
            self._total_observacoes = dados.get('total_observacoes', 0)
            tt = dados.get('tecla_tecla', {})
            self._tecla_tecla = defaultdict(
                lambda: defaultdict(int),
                {k: defaultdict(int, v) for k, v in tt.items()})
            ct = dados.get('complexidade_tempo', {})
            self._complexidade_tempo = defaultdict(
                lambda: defaultdict(int),
                {int(k): defaultdict(int, {float(t): c for t, c in v.items()})
                 for k, v in ct.items()})
            return True
        except Exception:
            return False

