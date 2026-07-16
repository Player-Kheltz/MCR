"""mcr.chat — Loop de conversa 100% MCR.

Conecta as pecas:
  Coupling.decidir() -> entende intencao
  Markov walk        -> gera resposta
  Coupling.alimentar() -> aprende entrada E resposta

Sem LLM. Sem API. Sem GPU.
"""
import random
from typing import List, Optional

from mcr.coupling import MCRCoupling


class MCRChat:

    def __init__(self, coupling: MCRCoupling = None, temperatura: float = 0.7):
        self._coupling = coupling or MCRCoupling()
        self._temperatura = temperatura
        self._historico: List[dict] = []

    @property
    def coupling(self) -> MCRCoupling:
        return self._coupling

    def alimentar_corpus(self, pares: list):
        self._coupling.alimentar_swarm(pares)

    def _amostrar(self, distribuicao: dict, temperatura: float = None) -> Optional[str]:
        if not distribuicao:
            return None
        temp = temperatura if temperatura is not None else self._temperatura
        total = sum(distribuicao.values())
        if total == 0:
            return None
        probs = {k: (v / total) ** (1.0 / temp) for k, v in distribuicao.items()}
        total_p = sum(probs.values())
        if total_p == 0:
            return None
        r = random.random() * total_p
        acum = 0.0
        for k, p in sorted(probs.items(), key=lambda x: -x[1]):
            acum += p
            if r <= acum:
                return k
        return None

    def _candidatos(self, contexto: list, max_candidatos: int = 30) -> list:
        c = self._coupling
        candidatos = {}
        for ordem in (4, 3):
            if len(contexto) >= ordem - 1:
                prefix = tuple(contexto[-(ordem - 1):])
                for prox, count in c._ngrama[ordem].get(prefix, {}).items():
                    candidatos[prox] = candidatos.get(prox, 0) + count
        if contexto:
            for prox, count in c._transicao_palavra.get(contexto[-1], {}).items():
                candidatos[prox] = candidatos.get(prox, 0) + count
        ordenados = sorted(candidatos.items(), key=lambda x: -x[1])
        return [p for p, _ in ordenados[:max_candidatos]]

    def _proximo_token_markov(self, contexto: list,
                               _visitados: set = None) -> Optional[str]:
        c = self._coupling
        for ordem in (4, 3):
            if len(contexto) >= ordem - 1:
                prefix = tuple(contexto[-(ordem - 1):])
                dist = c._ngrama[ordem].get(prefix, {})
                if dist:
                    if _visitados:
                        dist = {k: v for k, v in dist.items() if k not in _visitados}
                        if not dist:
                            dist = c._ngrama[ordem].get(prefix, {})
                    if dist:
                        return self._amostrar(dist)
        if contexto:
            dist = c._transicao_palavra.get(contexto[-1], {})
            if dist:
                if _visitados:
                    dist = {k: v for k, v in dist.items() if k not in _visitados}
                    if not dist:
                        dist = c._transicao_palavra.get(contexto[-1], {})
                if dist:
                    return self._amostrar(dist)
        return None

    def _proximo_token_semantico(self, contexto: list,
                                  _visitados: set = None) -> Optional[str]:
        candidatos = self._candidatos(contexto, max_candidatos=30)
        if not candidatos:
            return None
        if _visitados:
            nao_visitados = [t for t in candidatos if t not in _visitados]
            if nao_visitados:
                candidatos = nao_visitados
        if len(candidatos) == 1:
            return candidatos[0]

        ultimo = contexto[-1] if contexto else ''
        scores = []
        for token in candidatos:
            sim_ultimo = self._coupling.similaridade(ultimo, token)
            if len(contexto) >= 2:
                sim_penult = self._coupling.similaridade(contexto[-2], token)
                score = sim_ultimo * 0.65 + sim_penult * 0.35
            else:
                score = sim_ultimo
            scores.append((token, score))

        scores.sort(key=lambda x: -x[1])
        return self._amostrar({t: max(1, int(s * 100)) for t, s in scores})

    def _escolher_semente(self, semente: str) -> str:
        c = self._coupling
        trans = c._transicao_palavra
        if semente and semente in trans:
            return semente
        palavras = semente.replace('_', ' ').split() if semente else []
        for p in palavras:
            p_lower = p.lower()[:12]
            if p_lower in trans:
                return p_lower
        if palavras:
            melhor_p, melhor_n = palavras[0].lower()[:12], 0
            for p in set(palavras):
                p_lower = p.lower()[:12]
                n = sum(c._palavra_acao.get(p_lower, {}).values())
                if n > melhor_n:
                    melhor_n, melhor_p = n, p_lower
            if melhor_p in trans:
                return melhor_p
        comuns = [p for p in trans if len(p) >= 3]
        if comuns:
            return random.choice(comuns)
        return semente or '...'

    def _gerar_resposta(self, semente: str, max_tokens: int = 20,
                         modo: str = 'semantico') -> str:
        atual = self._escolher_semente(semente)
        if atual == '...':
            return "..."

        palavras = [atual]
        janela_visitados = {atual}

        for _ in range(max_tokens - 1):
            if modo == 'semantico':
                prox = self._proximo_token_semantico(palavras, janela_visitados)
                if not prox:
                    prox = self._proximo_token_markov(palavras, janela_visitados)
            else:
                prox = self._proximo_token_markov(palavras, janela_visitados)

            if not prox:
                break
            if prox == palavras[-1]:
                break
            if len(palavras) >= 2 and prox == palavras[-2]:
                janela_visitados.add(prox)
                continue

            palavras.append(prox)
            janela_visitados.add(prox)
            if len(janela_visitados) > 8:
                janela_visitados = set(palavras[-5:])

        return ' '.join(palavras)

    def perguntar(self, entrada: str, max_tokens: int = 25) -> str:
        acao, conf = self._coupling.decidir(entrada, (None, 0.0))
        if not acao or conf < 0.1:
            acao = 'responder'

        resposta = self._gerar_resposta(acao, max_tokens)

        self._coupling.alimentar(entrada, acao)
        if resposta and len(resposta.split()) >= 2:
            self._coupling.alimentar(resposta, acao)

        self._historico.append({'entrada': entrada, 'acao': acao,
                                'resposta': resposta, 'conf': conf})

        return resposta

    def historico(self, n: int = 5) -> List[dict]:
        return self._historico[-n:]

    def estado(self) -> dict:
        est = self._coupling.estatisticas()
        return {
            'observacoes': est['total'],
            'palavras': est['palavras'],
            'features_nd': est['features_nd'],
            'interacoes': len(self._historico),
        }
