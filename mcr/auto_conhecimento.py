"""mcr.auto_conhecimento — MCR se auto-alimenta com conhecimento.

Pilar 1: cada fato e P(b|a) — o MCR aprende observando.
Pilar 5: ingerir → recuperar → aprender (loop).
Pilar 9: comeca vazio, admite ignorancia, cresce com dados.

O MCR nao nasce sabendo — ele APRENDE. Este modulo e o "boot"
do conhecimento: fatos basicos que o MCR ingere ao iniciar para
poder responder perguntas fundamentais.

Conhecimento ingerido:
  1. Data e hora atual (temporal)
  2. Conceitos sobre si mesmo (identidade)
  3. Vocabulario base (palavras comuns e seus significados)

Nada e hardcoded no motor — e ingerido como FATOS no
BaseConhecimento e como OBSERVACOES no coupling. O motor
continua sendo P(b|a) puro.

Uso:
    from mcr.auto_conhecimento import AutoConhecimento
    ac = AutoConhecimento(coupling)
    ac.ingerir_base()
"""
import time
import datetime
from typing import Optional


class AutoConhecimento:
    """MCR se auto-alimenta com conhecimento basico.

    Nao e uma lista hardcoded de respostas — e INGESTAO de fatos.
    O BaseConhecimento recupera por NMI, o coupling aprende padroes.
    O motor continua sendo P(b|a) puro.
    """

    def __init__(self, coupling, base_conhecimento=None):
        self._coupling = coupling
        self._bc = base_conhecimento

    def _get_bc(self):
        """Acessa BaseConhecimento do triunvirato."""
        if self._bc:
            return self._bc
        delib = self._coupling._deliberacao
        if delib is None:
            delib = self._coupling._inic_deliberacao()
        if delib:
            self._bc = delib._fontes.get('BaseConhecimento')
        return self._bc

    def ingerir_base(self) -> int:
        """Ingere conhecimento base no BC e no coupling.

        Pilar 9: sem identidade ou vocabulario hardcoded.
        So ingere data/hora atual (dinamico, nao hardcoded).
        Identidade emerge do corpus (codigo, docs, conversas).
        Returns: numero de fatos ingeridos.
        """
        n = 0
        n += self._ingerir_temporal()
        return n

    def _ingerir_temporal(self) -> int:
        """Ingere data e hora atual como fatos.

        Pilar 5: o MCR precisa saber que dia e para responder.
        Atualizado a cada inicializacao — sempre correto.
        """
        bc = self._get_bc()
        if not bc:
            return 0

        agora = datetime.datetime.now()
        dias = ['segunda-feira', 'terca-feira', 'quarta-feira',
                'quinta-feira', 'sexta-feira', 'sabado', 'domingo']
        meses = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

        fatos = [
            f"hoje e dia {agora.day} de {meses[agora.month - 1]} de {agora.year}",
            f"hoje e {dias[agora.weekday()]}",
            f"a data de hoje e {agora.strftime('%d/%m/%Y')}",
            f"agora sao {agora.strftime('%H')} horas e {agora.strftime('%M')} minutos",
            f"o ano atual e {agora.year}",
            f"o mes atual e {meses[agora.month - 1]}",
        ]

        for fato in fatos:
            bc.ingerir(fato, "temporal")
            self._coupling.alimentar(fato, "responder")

        return len(fatos)

    # identidade e vocabulario removidos — Pilar 9: sem hardcode
    # O MCR descobre quem e pelo que ingere do mundo real.

    def ingerir_fato(self, fato: str, fonte: str = "humano") -> None:
        """Ingere um fato novo — usado pelo loop de auto-treinamento.

        Quando o humano explica algo, o MCR ingere como fato.
        Proxima vez que alguem perguntar, o MCR sabe.
        """
        bc = self._get_bc()
        if bc:
            bc.ingerir(fato, fonte)
        self._coupling.alimentar(fato, "responder")

    def estatisticas(self) -> dict:
        """Estatisticas do conhecimento ingerido."""
        bc = self._get_bc()
        if not bc:
            return {'fatos': 0}
        return {
            'fatos': len(bc._fatos),
            'fontes': list(set(f[1] for f in bc._fatos)),
        }
