"""mcr.triunvirato — Loop de Busca Ativa + Eventos de Pensamento.

O triunvirato nao e uma decisao — e um PROCESSO:
  1. Acoplamento delibera (superposicao normal)
  2. Se divergencia alta OU meta-cog diz "nao posso responder":
     → busca ativa em todas as fontes disponíveis
     → cada fonte publica contribuição (evento de pensamento)
     → resultados sao alimentados de volta ao coupling
     → re-decisao com evidencia adicional
  3. Se consenso apos busca: retorna decisao + eventos
  4. Se persiste divergencia: retorna com confianca baixa + eventos

Gatilho (sem hardcoded):
  Divergencia JS media > tercil superior das divergencias historicas.
  Tercil e aprendido dos dados, nao fixo.

Pilar 1: busca e P(fonte|incerteza) — quanto mais incerto, mais busca
Pilar 2: threshold de busca emerge dos dados (tercil)
Pilar 5: delibera → busca → re-delibera (loop)
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any


class EventoPensamento:
    """Um evento de pensamento: contribuicao de uma fonte na deliberacao."""

    __slots__ = ('fonte', 'contribuicao', 'score', 'timestamp', 'duracao_ms')

    def __init__(self, fonte: str, contribuicao: str,
                 score: float = 0.0, duracao_ms: float = 0.0):
        self.fonte = fonte
        self.contribuicao = contribuicao
        self.score = score
        self.timestamp = time.time()
        self.duracao_ms = duracao_ms

    def to_dict(self) -> dict:
        return {
            'fonte': self.fonte,
            'contribuicao': self.contribuicao,
            'score': round(self.score, 4),
            'timestamp': self.timestamp,
            'duracao_ms': round(self.duracao_ms, 2),
        }


class Deliberacao:
    """Motor de busca ativa deliberativa.

    Coleta divergencias historicas, detecta gatilho, consulta fontes,
    e retorna resultados + eventos de pensamento.
    """

    def __init__(self):
        self._divergencias_historicas: List[float] = []
        self._eventos: List[EventoPensamento] = []
        self._buscas_realizadas: int = 0
        self._fontes: Dict[str, Any] = {}

    def registrar_fonte(self, nome: str, fonte: Any) -> None:
        """Registra uma fonte de busca ativa.

        A fonte deve implementar um metodo que retorne resultados
        relevantes para uma query (texto).
        """
        self._fontes[nome] = fonte

    def _tercil_superior(self) -> float:
        """Tercil superior das divergencias historicas.

        Pilar 2: threshold emerge dos dados, nao e hardcoded.
        Com <3 amostras, retorna 1.0 (desativa busca — dados insuficientes).
        """
        if len(self._divergencias_historicas) < 3:
            return 1.0
        ord_ = sorted(self._divergencias_historicas)
        idx = len(ord_) * 2 // 3
        return ord_[min(idx, len(ord_) - 1)]

    def deve_buscar(self, div_media: float, pode_responder: bool = True) -> bool:
        """Decide se busca ativa e necessaria.

        Gatilho 1: divergencia JS media > tercil superior historico
        Gatilho 2: meta-cog diz "nao posso responder"

        Returns True se busca deve ser disparada.
        """
        self._divergencias_historicas.append(div_media)
        if len(self._divergencias_historicas) > 500:
            self._divergencias_historicas = self._divergencias_historicas[-500:]

        th = self._tercil_superior()
        if div_media > th:
            return True
        if not pode_responder:
            return True
        return False

    def buscar(self, texto: str, coupling=None) -> Tuple[Dict[str, float], List[EventoPensamento]]:
        """Busca ativa em todas as fontes registradas.

        Cada fonte retorna resultados relevantes. Resultados sao
        convertidos em distribuicoes P(acao|fato) e alimentados
        de volta ao coupling.

        Returns: (distribuicao_combinada, eventos)
        """
        t0 = time.time()
        eventos = []
        distribuicoes: List[Tuple[Dict[str, float], float]] = []

        for nome, fonte in self._fontes.items():
            t_fonte = time.time()
            try:
                resultado = self._consultar_fonte(nome, fonte, texto, coupling)
                dur = (time.time() - t_fonte) * 1000

                if resultado:
                    dist, score, resumo = resultado
                    eventos.append(EventoPensamento(
                        fonte=nome,
                        contribuicao=resumo,
                        score=score,
                        duracao_ms=dur,
                    ))
                    distribuicoes.append((dist, 1.0 - score))
            except Exception as e:
                dur = (time.time() - t_fonte) * 1000
                eventos.append(EventoPensamento(
                    fonte=nome,
                    contribuicao=f'erro: {str(e)[:80]}',
                    score=0.0,
                    duracao_ms=dur,
                ))

        self._buscas_realizadas += 1
        self._eventos.extend(eventos)

        if not distribuicoes:
            return {}, eventos

        combinada: Dict[str, float] = defaultdict(float)
        total_peso = sum(p for _, p in distribuicoes) or 1.0
        for dist, peso in distribuicoes:
            total_d = sum(dist.values()) or 1.0
            for acao, prob in dist.items():
                combinada[acao] += (prob / total_d) * (peso / total_peso)

        return dict(combinada), eventos

    def _consultar_fonte(self, nome: str, fonte: Any,
                         texto: str,
                         coupling=None) -> Optional[Tuple[Dict[str, float], float, str]]:
        """Consulta uma fonte e retorna (distribuicao, score, resumo).

        Detecta automaticamente a API da fonte:
          - recuperar(pergunta, top_n) → BaseConhecimento
          - buscar(texto, max_r) → KnowledgeGraph
        """
        if hasattr(fonte, 'recuperar'):
            fatos = fonte.recuperar(texto, top_n=3)
            if not fatos:
                return None
            dist = defaultdict(float)
            for fato, fonte_nome, score in fatos:
                acoes_relevantes = self._inferir_acoes(fato, coupling)
                for acao in acoes_relevantes:
                    dist[acao] += score
            resumo = fatos[0][0][:80] if fatos else ''
            score_medio = sum(f[2] for f in fatos) / len(fatos)
            return dict(dist), score_medio, resumo

        if hasattr(fonte, 'buscar'):
            resultados = fonte.buscar(texto, max_r=3)
            if not resultados:
                return None
            dist = defaultdict(float)
            for r in resultados:
                if isinstance(r, dict):
                    texto_r = r.get('texto', str(r))
                    score = r.get('score', 0.5)
                else:
                    texto_r = str(r)
                    score = 0.5
                acoes = self._inferir_acoes(texto_r, coupling)
                for acao in acoes:
                    dist[acao] += score
            resumo = str(resultados[0])[:80] if resultados else ''
            return dict(dist), 0.5, resumo

        return None

    def _inferir_acoes(self, texto: str, coupling=None) -> List[str]:
        """Inferiu acoes relevantes de um texto de busca.

        Consulta o coupling para descobrir quais acoes estao associadas
        as palavras do texto. Sem hardcode de dominio.
        Se coupling nao disponivel, retorna acao padrao.
        """
        if coupling is None:
            return ['responder']
        palavras = set(texto.lower().split())
        scores_por_acao: Dict[str, float] = defaultdict(float)
        for p in palavras:
            if len(p) < 3:
                continue
            dist = coupling._palavra_acao.get(p, {})
            if not dist:
                continue
            total = sum(dist.values()) or 1
            for acao, c in dist.items():
                scores_por_acao[acao] += c / total
        if not scores_por_acao:
            return ['responder']
        ordenadas = sorted(scores_por_acao.items(), key=lambda x: -x[1])
        total = sum(v for _, v in ordenadas)
        k = len(ordenadas)
        threshold = 1.0 / max(k, 2)
        return [acao for acao, score in ordenadas if score / total >= threshold]

    def eventos_recentes(self, n: int = 10) -> List[EventoPensamento]:
        """Retorna os N eventos de pensamento mais recentes."""
        return self._eventos[-n:]

    def limpar_eventos(self) -> None:
        """Limpa historico de eventos."""
        self._eventos.clear()

    def estatisticas(self) -> Dict:
        """Estatisticas da deliberacao."""
        return {
            'buscas_realizadas': self._buscas_realizadas,
            'total_eventos': len(self._eventos),
            'fontes_registradas': list(self._fontes.keys()),
            'divergencias_historicas': len(self._divergencias_historicas),
            'tercil_superior': round(self._tercil_superior(), 4),
        }
