"""BaseConhecimento — Ingestão enciclopédica + recuperação por NMI.

LLMs são treinados em 10T tokens da internet. MCR começa vazio.
Este módulo resolve o problema: ingere texto em massa e recupera
conhecimento relevante por NMI na hora da pergunta.

Arquitetura:
  ingerir(texto, fonte) → coupling.alimentar() + EpisodicMemory.registrar()
  recuperar(pergunta) → NMI entre pergunta e conhecimento indexado
  responder(pergunta) → recuperar + raciocinar

Pilar 1: cada fato é P(fato | conceito) no coupling
Pilar 2: NMI decide o que é relevante (sem threshold)
Pilar 5: ingerir → recuperar → aprender (loop)
Pilar 7: correlação universal — qualquer fato se conecta via P(b|a)

Uso:
    bc = BaseConhecimento(coupling)
    bc.ingerir("O fogo é quente. Fogo queima madeira.", "enciclopedia")
    resposta = bc.responder("o que o fogo faz?")
"""
import re, math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class BaseConhecimento:

    def __init__(self, coupling):
        self._coupling = coupling
        self._fatos: List[Tuple[str, str, str]] = []
        self._indice_conceitos: Dict[str, List[int]] = defaultdict(list)

    def ingerir(self, texto: str, fonte: str = "desconhecida") -> int:
        """Ingere texto: extrai fatos e alimenta o coupling.

        Cada frase do texto vira uma observação no coupling.
        Conceitos-chave são indexados para recuperação rápida.

        Returns: número de fatos extraídos
        """
        frases = self._extrair_frases(texto)
        n_fatos = 0

        for frase in frases:
            frase = frase.strip().lower()
            if len(frase) < 5:
                continue

            conceito = self._extrair_conceito_principal(frase)
            if not conceito:
                continue

            acao = self._classificar_fato(frase, conceito)
            if acao:
                self._coupling.alimentar(frase, acao)
                idx = len(self._fatos)
                self._fatos.append((frase, fonte, conceito))
                self._indice_conceitos[conceito].append(idx)
                n_fatos += 1

        return n_fatos

    def ingerir_lote(self, textos: List[Tuple[str, str]]) -> int:
        """Ingere múltiplos textos. Cada item é (texto, fonte)."""
        total = 0
        for texto, fonte in textos:
            total += self.ingerir(texto, fonte)
        return total

    def recuperar(self, pergunta: str, top_n: int = 5
                  ) -> List[Tuple[str, str, float]]:
        """Recupera fatos relevantes para a pergunta via NMI.

        Pilar 2: NMI decide relevância (sem threshold hardcoded).
        Pilar 7: pergunta se correlaciona com fatos via P(b|a).

        Returns: lista de (fato, fonte, score_nmi) ordenada por score
        """
        pergunta = pergunta.lower().strip()
        sig_pergunta = self._coupling._assinatura_frase(pergunta)
        if not sig_pergunta:
            return []

        resultados = []
        palavras_pergunta = set(re.findall(r'[a-zà-ÿ]{3,}', pergunta))

        for fato, fonte, conceito in self._fatos:
            palavras_fato = set(re.findall(r'[a-zà-ÿ]{3,}', fato))

            overlap = len(palavras_pergunta & palavras_fato)
            if overlap == 0:
                sig_fato = self._coupling._assinatura_palavra(conceito)
                if sig_fato:
                    nmi = self._coupling._nmi(sig_pergunta, sig_fato)
                else:
                    continue
            else:
                sig_fato = self._coupling._assinatura_frase(fato)
                if not sig_fato:
                    continue
                nmi = self._coupling._nmi(sig_pergunta, sig_fato)

            if nmi > 0:
                resultados.append((fato, fonte, nmi))

        resultados.sort(key=lambda x: -x[2])
        return resultados[:top_n]

    def responder(self, pergunta: str) -> Tuple[Optional[str], float, List]:
        """Responde uma pergunta: recuperar + raciocinar.

        1. Recupera fatos relevantes via NMI
        2. Constrói contexto com os fatos recuperados
        3. Raciocina sobre a pergunta com o contexto

        Returns: (resposta, confianca, fatos_usados)
        """
        fatos = self.recuperar(pergunta, top_n=3)
        if not fatos:
            pred, conf = self._coupling.decidir(pergunta, (None, 0.0))
            return pred, conf, []

        contexto = ' '.join(f for f, _, _ in fatos)
        estado = f"{pergunta} {contexto}"

        pred, conf = self._coupling.decidir(estado, (None, 0.0))

        fatos_usados = [(f, s) for f, _, s in fatos]
        return pred, conf, fatos_usados

    def _extrair_frases(self, texto: str) -> List[str]:
        """Extrai frases do texto (split por pontuação)."""
        frases = re.split(r'[.\n;!]+', texto)
        return [f.strip() for f in frases if f.strip()]

    def _extrair_conceito_principal(self, frase: str) -> Optional[str]:
        """Extrai o conceito principal de uma frase.

        Heurística markoviana: a palavra mais específica
        (menor entropia em _palavra_acao) é o conceito principal.
        """
        palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
        if not palavras:
            return None

        melhor_palavra = None
        melhor_spec = -1.0

        for p in set(palavras):
            dist = self._coupling._palavra_acao.get(p, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            probs = [c / total for c in dist.values()]
            h = 0.0
            for pr in probs:
                if pr > 0:
                    h -= pr * math.log2(pr)
            max_h = math.log2(max(len(dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            spec = 1.0 - h_norm
            if spec > melhor_spec:
                melhor_spec = spec
                melhor_palavra = p

        if not melhor_palavra:
            return palavras[0] if palavras else None
        return melhor_palavra

    def _classificar_fato(self, frase: str, conceito: str) -> str:
        """Classifica um fato em uma ação para o coupling.

        Usa a própria frase como ação (cada fato é único).
        Alternativamente, se o conceito já tem ações, reusa.
        """
        dist = self._coupling._palavra_acao.get(conceito, {})
        if dist:
            return max(dist, key=dist.get)

        palavras = re.findall(r'[a-zà-ÿ]{3,}', frase)
        if len(palavras) >= 2:
            return f"info_{palavras[0]}"
        return "info_geral"

    def n_fatos(self) -> int:
        return len(self._fatos)

    def conceitos(self) -> List[str]:
        return list(self._indice_conceitos.keys())