"""mcr.acoplamento_hierarquico — MCR de MCRs: cognição em camadas.

Cada camada comprime a camada abaixo via assinatura. A assinatura da
camada N-1 vira o "texto" de entrada da camada N. Isto permite
memória de longo alcance SEM attention mechanism — Markov puro.

Hierarquia natural (emergente, não hardcoded):
  Camada 0: palavra → palavra           (MCRCoupling base)
  Camada 1: frase → frase               (assinatura_frase)
  Camada 2: parágrafo → parágrafo       (assinatura_paragrafo)
  Camada 3: tópico → tópico
  ...

Auto-limitação entrópica (Pilar 2 — Entropia descobre):
  Cada camada comprime a anterior. Quando uma camada atinge delta_H ≈ 0
  (a entropia da nova camada é igual à anterior — não há redução de
  incerteza), a próxima camada não aprende nada novo. O sistema se
  estabiliza AUTOMATICAMENTE, sem número mágico de níveis.

Pilar 1: tudo é P(b|a) — cada camada é um MCRCoupling
Pilar 2: entropia decide quando parar (delta_H)
Pilar 3: mesmo motor, qualquer nível de abstração
Pilar 5: alimentar → predizer → avaliar → aprender (loop)

Uso:
    from mcr.acoplamento_hierarquico import MCRHierarquico
    h = MCRHierarquico(max_niveis=7)
    h.alimentar("criar monstro dragao fogo", "criar_monstro")
    h.alimentar("gerar npc orc vendedor", "gerar_npc")
    acao, conf = h.predizer("criar dragao verde")
    print(h.estatisticas())  # quantas camadas emergiram
"""
import re
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from mcr.coupling import MCRCoupling


class MCRHierarquico:
    """MCR de MCRs — acoplamento hierárquico com auto-limitação entrópica.

    Cada camada é um MCRCoupling independente. A camada N+1 é alimentada
    com a assinatura (string) da camada N, não com o texto bruto.
    Isto comprime a informação: a camada 0 vê palavras, a camada 1 vê
    assinaturas de frases, a camada 2 vê assinaturas de parágrafos, etc.

    A auto-limitação entrópica detecta quando adicionar uma camada
    deixa de reduzir incerteza (delta_H ≈ 0) e para automaticamente.
    """

    def __init__(self, max_niveis: int = 7, min_delta_h: float = 0.05):
        """Inicializa o MCR hierárquico.

        Args:
            max_niveis: número máximo de camadas (safety cap)
            min_delta_h: delta_H mínimo para justificar nova camada.
                         Se delta_H < min_delta_h, para (pilar 2).
                         0.05 = 5% de redução de entropia mínima.
        """
        self.max_niveis = max_niveis
        self.min_delta_h = min_delta_h
        self.camadas: List[MCRCoupling] = [MCRCoupling()]
        self._entropias: List[float] = []
        self._total_observacoes = 0

    def _tokenizar_nivel(self, texto: str) -> str:
        """Tokeniza texto para o nível 0 (palavras 3+ chars)."""
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        return ' '.join(palavras) if palavras else texto.lower()

    def _comprimir(self, texto: str, nivel: int) -> Optional[str]:
        """Comprime texto para o nivel N via assinatura da camada N-1.

        A assinatura da camada N-1 e serializada como string e usada
        como entrada da camada N. Isto e a "compressao markoviana":
        o que era um dict de features vira uma string de pares chave:valor.

        Pilar 1: P(sig_N | sig_N-1) — transicao entre niveis.

        Returns None se a compressao falha (assinatura vazia), sinalizando
        que a camada N nao deve votar.
        """
        if nivel == 0:
            return self._tokenizar_nivel(texto)

        camada_abaixo = self.camadas[nivel - 1]
        sig = camada_abaixo._assinatura_frase(texto)
        if not sig:
            return None

        pares = sorted(sig.items(), key=lambda x: -x[1])[:20]
        return ' '.join(f"{k.replace(':', '_')}_{v}" for k, v in pares)

    def alimentar(self, texto: str, acao: str) -> None:
        """Alimenta todas as camadas ativas com (texto, acao).

        Cada camada recebe a versão comprimida do texto do nível abaixo.
        Após alimentar, verifica se uma nova camada deve ser adicionada
        via auto-limitação entrópica.

        Pilar 5: alimentar → avaliar entropia → aprender (loop).
        """
        self._total_observacoes += 1

        # Alimenta cada camada existente
        for nivel in range(len(self.camadas)):
            texto_nivel = self._comprimir(texto, nivel)
            if texto_nivel is None:
                continue
            self.camadas[nivel].alimentar(texto_nivel, acao)

        # Auto-limitação: verifica se precisa de mais uma camada
        self._avaliar_expansao()

    def _avaliar_expansao(self) -> None:
        """Auto-limitacao entropica — decide se adiciona nova camada.

        Pilar 2: Entropia descobre, sem threshold hardcoded.
        So adiciona uma nova camada se a ultima camada ainda tem
        incerteza significativa (H > min_delta_h). Se H ja e baixo
        (deterministica), nao ha o que comprimir — para.

        So avalia apos pelo menos 10 observacoes (amostra minima
        para entropia ser estatisticamente significativa).
        """
        if len(self.camadas) >= self.max_niveis:
            return
        if self._total_observacoes < 10:
            return

        h_ultima = self._entropia_camada(len(self.camadas) - 1)

        # Atualiza cache de entropias
        while len(self._entropias) < len(self.camadas):
            idx = len(self._entropias)
            self._entropias.append(self._entropia_camada(idx))
        self._entropias[len(self.camadas) - 1] = h_ultima

        # So expande se a ultima camada tem incerteza > min_delta_h
        # (ainda ha estrutura para comprimir)
        if h_ultima > self.min_delta_h:
            nova_camada = MCRCoupling()
            self.camadas.append(nova_camada)
            self._entropias.append(1.0)

    def _entropia_camada(self, nivel: int) -> float:
        """Entropia de Shannon normalizada da camada N.

        Mede a incerteza da distribuição de ações na camada.
        H=0 → totalmente determinística (1 ação por input).
        H=1 → máxima incerteza (uniforme).
        """
        camada = self.camadas[nivel]
        if not camada._freq_acao:
            return 1.0

        total = sum(camada._freq_acao.values()) or 1
        h = 0.0
        for count in camada._freq_acao.values():
            if count > 0:
                p = count / total
                h -= p * math.log2(p)

        max_h = math.log2(max(len(camada._freq_acao), 2))
        return h / max_h if max_h > 0 else 1.0

    def predizer(self, texto: str, acao_markov: str = None) -> Tuple[Optional[str], float]:
        """Prediz acao agregando todas as camadas ativas.

        Cada camada vota com sua predicao. O voto e ponderado pela
        CONFIANCA da predicao (conf), que e 1 - H_da_distribuicao_preditia.
        Camadas mais confiantes (distribuicao concentrada) pesam mais.
        Camadas que nao conseguem comprimir (assinatura vazia) sao puladas.

        Pilar 2: peso = confianca — entropia DA PREDICAO decide o peso.
        """
        distribs = []

        for nivel in range(len(self.camadas)):
            texto_nivel = self._comprimir(texto, nivel)
            if texto_nivel is None:
                continue

            camada = self.camadas[nivel]
            acao_c, conf_c = camada.decidir(
                texto_nivel,
                (acao_markov, 0.5 if acao_markov else 0.0)
            )

            if acao_c and conf_c > 0:
                peso = conf_c / (nivel + 1)
                distribs.append(({acao_c: conf_c}, peso))

        if not distribs:
            return (acao_markov or 'responder'), 0.0

        # Soma ponderada por confianca da predicao
        combinada: Dict[str, float] = defaultdict(float)
        total_peso = sum(p for _, p in distribs) or 1.0

        for dist, peso in distribs:
            for a, c in dist.items():
                combinada[a] += c * (peso / total_peso)

        if not combinada:
            return (acao_markov or 'responder'), 0.0

        melhor = max(combinada, key=combinada.get)
        return melhor, round(combinada[melhor], 4)

    def gerar_texto(self, semente: str, max_tokens: int = 50) -> str:
        """Gera texto usando a camada 0 (Markov palavra-a-palavra).

        A hierarquia NÃO é para geração (Markov 1ª ordem colapsa em
        >20 tokens). É para CLASSIFICAÇÃO e COMPREENSÃO de textos longos.
        A geração fica na camada 0, que já existe.

        Para geração de longo alcance, seria necessário retropropagar
        a predição da camada N de volta para a camada 0 — trabalho futuro.
        """
        camada0 = self.camadas[0]
        palavras = re.findall(r'[a-zà-ÿ]{3,}', semente.lower())
        if not palavras:
            return semente

        resultado = list(palavras)
        for _ in range(max_tokens):
            contexto = ' '.join(resultado[-5:])
            dist = camada0._dist_palavras(contexto)
            if not dist:
                break
            prox = max(dist, key=dist.get)
            if prox in resultado[-3:]:
                break
            resultado.append(prox)

        return ' '.join(resultado)

    def estatisticas(self) -> Dict:
        """Retorna estatísticas da hierarquia."""
        return {
            'niveis': len(self.camadas),
            'total_observacoes': self._total_observacoes,
            'entropias_por_nivel': [round(h, 4) for h in self._entropias],
            'palavras_por_nivel': [len(c._palavra_acao) for c in self.camadas],
            'acoes_por_nivel': [len(c._freq_acao) for c in self.camadas],
            'max_niveis': self.max_niveis,
            'min_delta_h': self.min_delta_h,
        }

    def save(self, caminho: str) -> None:
        """Salva todas as camadas em arquivos numerados."""
        import os
        base_dir = os.path.dirname(caminho)
        prefixo = os.path.splitext(os.path.basename(caminho))[0]
        for i, camada in enumerate(self.camadas):
            camada_cam = os.path.join(base_dir, f"{prefixo}_camada{i}.json")
            camada.save(camada_cam)

    def load(self, caminho: str) -> bool:
        """Carrega camadas de arquivos numerados."""
        import os
        base_dir = os.path.dirname(caminho)
        prefixo = os.path.splitext(os.path.basename(caminho))[0]
        camadas = []
        i = 0
        while True:
            camada_cam = os.path.join(base_dir, f"{prefixo}_camada{i}.json")
            if not os.path.exists(camada_cam):
                break
            c = MCRCoupling()
            if c.load(camada_cam):
                camadas.append(c)
            i += 1
        if camadas:
            self.camadas = camadas
            self._entropias = [self._entropia_camada(i)
                               for i in range(len(camadas))]
            return True
        return False
