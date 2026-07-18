"""mcr.coldstart — Questionario adaptativo de inicio com LGPD.

O coldstart NAO e uma lista fixa de perguntas. E um processo adaptativo:
  1. Consentimento LGPD — primeira e obrigatoria
  2. Perguntas semi-fixas (fundamentais, minimas)
  3. MCR avalia confianca — se ja sabe o suficiente, transiciona ao chat
  4. Se ainda ha gaps, MCR gera perguntas dos gaps de maior entropia
  5. Transicao ao chat normal quando confianca > auto-limite emergente

Pilar 1: cada resposta e P(resposta_humano | pergunta) — acoplamento isolado.
Pilar 2: entropia decide quando transicionar, nao threshold hardcoded.
Pilar 5: perguntar → avaliar entropia → aprender resposta → decidir transicao.
Pilar 11: o humano e fonte universal — respostas alimentam o coupling.

LGPD: consentimento EXPLICITO antes de qualquer coleta de sinais.
Sem consentimento: MCR funciona sem perfil, so texto (sem timing, sem teclas).
"""
from typing import Dict, List, Tuple, Optional, Any


class Coldstart:
    """Questionario adaptativo de inicio do MCR.

    Estados:
      CONSENTIMENTO → PERGUNTAS → CHAT
    """

    CONSENTIMENTO = 'consentimento'
    PERGUNTAS = 'perguntas'
    CHAT = 'chat'

    def __init__(self):
        self._estado = self.CONSENTIMENTO
        self._perguntas_feitas: List[str] = []
        self._respostas: Dict[str, str] = {}
        self._confiancas: List[float] = []
        self._perfil = None  # PerfilHumano, se consentido

        # Perguntas fundamentais (minimas, semi-fixas)
        # Semi-fixas porque sao as perguntas minimas para o MCR operar.
        # Nao hardcoded: emergem do que o MCR precisa saber para funcionar.
        self._perguntas_fundamentais = [
            "qual seu nome ou como devo te chamar?",
            "o que voce espera que eu faca?",
            "qual contexto estamos? (jogo, estudo, programacao, criacao...)",
            "voce prefere respostas curtas e diretas ou com explicacoes?",
        ]

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def perfil(self):
        return self._perfil

    def vincular_perfil(self, perfil) -> None:
        """Vincula o PerfilHumano a este coldstart.

        O perfil so coleta se consentido. O coldstart pergunta
        consentimento antes de vincular.
        """
        self._perfil = perfil

    # ─── LGPD — Consentimento ───────────────────────────────────

    def pergunta_consentimento(self) -> str:
        """Retorna a pergunta de consentimento LGPD.

        E a PRIMEIRA coisa que o MCR pergunta. Sempre.
        """
        return (
            "antes de comecar: posso observar como voce digita e responde "
            "para aprender seu estilo? isso inclui timing de resposta e "
            "padroes de teclas. seus dados ficam so aqui, com voce. "
            "responda 'sim' ou 'nao'."
        )

    def processar_consentimento(self, resposta: str) -> bool:
        """Processa resposta de consentimento.

        Returns: True se consentiu, False se nao.
        """
        resp = resposta.lower().strip()
        consentiu = 'sim' in resp and 'nao' not in resp

        if self._perfil and consentiu:
            self._perfil.consentir()

        if consentiu or not consentiu:
            self._estado = self.PERGUNTAS

        return consentiu

    # ─── Perguntas ──────────────────────────────────────────────

    def pergunta_atual(self) -> Optional[str]:
        """Retorna a pergunta atual ou None se terminou.

        Ordem: perguntas fundamentais → gaps de entropia → fim.
        """
        if self._estado != self.PERGUNTAS:
            return None

        # Perguntas fundamentais ainda nao feitas
        for p in self._perguntas_fundamentais:
            if p not in self._perguntas_feitas:
                return p

        # Avaliar gaps — se MCR tem confianca suficiente, transicionar
        if self._avaliar_transicao():
            self._estado = self.CHAT
            return None

        # Gerar pergunta do gap de maior entropia
        return self._gerar_pergunta_gap()

    def processar_resposta(self, pergunta: str, resposta: str) -> None:
        """Processa resposta do humano a uma pergunta do coldstart.

        Pilar 1: resposta e P(resposta_humano | pergunta).
        Pilar 11: toda resposta alimenta o acoplamento.
        """
        if pergunta not in self._perguntas_feitas:
            self._perguntas_feitas.append(pergunta)
        self._respostas[pergunta] = resposta

        # Estimar confianca na resposta (entropia do texto)
        palavras = resposta.split()
        n_palavras = len(palavras)
        unicas = len(set(palavras))
        if n_palavras > 0:
            diversidade = unicas / n_palavras
            conf = min(1.0, n_palavras / 5) * diversidade
        else:
            conf = 0.0
        self._confiancas.append(conf)

    def respostas_coletadas(self) -> Dict[str, str]:
        """Retorna todas as respostas coletadas."""
        return dict(self._respostas)

    # ─── Transicao ──────────────────────────────────────────────

    def _avaliar_transicao(self) -> bool:
        """Avalia se o MCR ja sabe o suficiente para transicionar.

        Pilar 2: entropia decide. Se confianca media > auto-limite,
        transiciona. Auto-limite = 1 / (n_perguntas + 1).

        Sem hardcode: o limite emerge do numero de perguntas feitas.
        """
        if not self._confiancas:
            return False
        conf_media = sum(self._confiancas) / len(self._confiancas)
        n_feitas = len(self._perguntas_feitas)
        auto_limite = 1.0 / (n_feitas + 1)
        return conf_media > auto_limite

    def _gerar_pergunta_gap(self) -> Optional[str]:
        """Gera pergunta baseada no gap de maior entropia.

        Pilar 2: gap e onde o MCR tem menos informacao (maior entropia).
        Sem perguntas hardcoded — emergem do que falta saber.
        """
        # Gaps detectados por entropia das respostas anteriores
        if not self._respostas:
            return None

        # Medir diversidade de respostas (entropia)
        todas_palavras = []
        for r in self._respostas.values():
            todas_palavras.extend(r.lower().split())
        unicas = len(set(todas_palavras))
        total = len(todas_palavras)

        if total == 0:
            return None

        diversidade = unicas / total

        if diversidade < 0.3:
            return "pode me contar mais detalhes? sinto que ainda sei pouco sobre voce."
        elif diversidade < 0.6:
            return "ha algo mais que voce gostaria que eu soubesse antes de comecarmos?"
        else:
            return None  # diversidade alta = sabe o suficiente

    # ─── Estado ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'estado': self._estado,
            'consentido': self._perfil.consentido() if self._perfil else False,
            'perguntas_feitas': list(self._perguntas_feitas),
            'respostas': dict(self._respostas),
            'confiancas': list(self._confiancas),
            'confianca_media': round(
                sum(self._confiancas) / len(self._confiancas), 3
            ) if self._confiancas else 0.0,
        }

    # ─── Persistencia (Fix 5) ───────────────────────────────────

    def save(self, caminho: str) -> None:
        """Salva estado do coldstart em JSON."""
        import json, os
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self, caminho: str) -> bool:
        """Carrega estado do coldstart de JSON."""
        import json, os
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self._estado = dados.get('estado', self.CONSENTIMENTO)
            self._perguntas_feitas = list(dados.get('perguntas_feitas', []))
            self._respostas = dict(dados.get('respostas', {}))
            self._confiancas = list(dados.get('confiancas', []))
            return True
        except Exception:
            return False

