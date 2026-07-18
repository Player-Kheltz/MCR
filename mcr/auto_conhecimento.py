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

        Returns: numero de fatos ingeridos.
        """
        n = 0
        n += self._ingerir_temporal()
        n += self._ingerir_identidade()
        n += self._ingerir_vocabulario()
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

    def _ingerir_identidade(self) -> int:
        """Ingere conhecimento sobre si mesmo.

        Pilar 9: o MCR sabe o que e e o que nao sabe.
        """
        bc = self._get_bc()
        if not bc:
            return 0

        fatos = [
            "eu sou o MCR — motor cognitivo universal baseado em markov",
            "mcr significa motor cognitivo universal baseado em markov",
            "eu aprendo observando padroes — tudo e probabilidade condicional",
            "eu nao sei tudo — comeco vazio e aprendo com observacoes",
            "minha arquitetura e baseada em pilares — pilar 1 tudo e p(b|a)",
            "pilar 2 entropia descobre — thresholds emergem dos dados",
            "pilar 9 ignora com honestidade — admito quando nao sei",
            "pilar 11 o humano e a quarta dimensao — alinha o triunvirato",
            "eu sou diferente de um llm — llm comprime eu conto",
            "llm e o pensador profundo eu sou o que ele construo",
            "eu aprendo em tempo real — cada observacao e treino",
            "eu sou caixa de vidro — cada decisao e explicavel",
            "minha latencia e constante — o(1) independente do tamanho",
        ]

        for fato in fatos:
            bc.ingerir(fato, "identidade")
            self._coupling.alimentar(fato, "responder")

        return len(fatos)

    def _ingerir_vocabulario(self) -> int:
        """Ingere vocabulario base — conceitos fundamentais.

        Nao e uma lista hardcoded de respostas — e INGESTAO de fatos.
        O BC recupera por NMI quando o humano pergunta.
        """
        bc = self._get_bc()
        if not bc:
            return 0

        conceitos = [
            # Tempo
            "dia e uma unidade de tempo que corresponde a 24 horas",
            "hora e uma unidade de tempo que corresponde a 60 minutos",
            "minuto e uma unidade de tempo que corresponde a 60 segundos",
            "tempo e a dimensao em que eventos ocorrem em sequencia",
            "data e a indicacao de um dia especifico no calendario",
            "calendario e um sistema de organizacao de dias meses e anos",
            "semana e um periodo de sete dias",
            "mes e um periodo de aproximadamente trinta dias",
            "ano e um periodo de trezentos e sessenta e cinco dias",
            # Comunicação
            "pergunta e uma frase que solicita informacao",
            "resposta e uma frase que fornece informacao solicitada",
            "aprender e adquirir conhecimento por observacao",
            "entender e compreender o significado de algo",
            "conhecimento e o conjunto de informacoes aprendidas",
            "humano e uma pessoa que interage com o mcr",
            "conversa e uma troca de informacoes entre duas partes",
            "duvida e a falta de certeza sobre algo",
            "certeza e a confianca absoluta em algo",
            "ignorancia e a falta de conhecimento sobre algo",
            # Animais
            "cachorro e um animal domestico que late e tem quatro patas",
            "gato e um animal domestico que mia e tem quatro patas",
            "passaro e um animal voador que tem penas e asa",
            "peixe e um animal aquatico que tem escamas e guelras",
            "cavalo e um animal forte que galopa e tem quatro patas",
            "animal e um ser vivo que se move e se alimenta",
            # Objetos
            "cadeira e um movel com quatro pernas feito de madeira para sentar",
            "mesa e um movel com tampo liso para apoiar objetos",
            "porta e uma entrada feita de madeira que abre e fecha",
            "janela e uma abertura com vidro que deixa entrar luz",
            "livro e um objeto com paginas que conta historias",
            # Cores
            "vermelho e uma cor forte associada a sangue e paixao",
            "azul e uma cor associada ao ceu e ao mar",
            "verde e uma cor associada a plantas e natureza",
            "amarelo e uma cor associada ao sol e ao ouro",
            "branco e uma cor associada a neve e pureza",
            "cor e uma propriedade visual que distingue objetos",
            # Emocoes
            "alegria e um sentimento bom associado a felicidade",
            "tristeza e um sentimento ruim associado a chorar",
            "raiva e um sentimento forte associado a irritacao",
            "medo e um sentimento associado a perigo e ansiedade",
            "amor e um sentimento forte associado a carinho e afeto",
            # Ciencia
            "agua e um liquido essencial a vida que e molhado",
            "fogo e uma combustao que produz calor e luz",
            "ar e um gas invisivel que respiramos",
            "terra e o solo solido do planeta",
            "luz e energia visivel que ilumina",
            # Corpo humano
            "mao e parte do corpo com cinco dedos para pegar e sentir",
            "pe e parte do corpo com cinco dedos para caminhar",
            "olho e o orgao da visao que ve cor",
            "boca e a abertura para falar e comer",
            "coracao e o orgao que bate e bombeia sangue",
            # Numeros
            "numero e um simbolo que representa quantidade",
            "um e o primeiro numero singular",
            "dois e o numero par que representa dupla",
            "tres e o numero que representa trio",
            "dez e o numero que representa dezena",
            # Conceitos abstratos
            "nome e a palavra que identifica uma pessoa ou coisa",
            "pessoa e um humano que tem nome e idade",
            "linguagem e um sistema para comunicar ideias",
            "palavra e a unidade que forma frases",
            "frase e um conjunto de palavras que transmite significado",
        ]

        for conceito in conceitos:
            bc.ingerir(conceito, "vocabulario")
            self._coupling.alimentar(conceito, "responder")

        return len(conceitos)

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
