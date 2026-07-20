"""GeradorCoerente — Geração longa com working memory.

MCR gera token-a-token via P(next|current). Após ~20 tokens, diverge
porque perde a estrutura global. Este módulo mantém 3 componentes de
memória de trabalho:

1. Buffer recente (exato, lossless) — últimos N tokens
2. Assinatura temática (comprimida, lossy) — hierarquia do texto todo
3. Buffer de entidades (exato) — sujeitos/objetos mencionados

A cada passo:
  estado = token_atual + buffer_recente + assinatura_tema + entidades
  P(next | estado) → top-K candidatos
  5D avalia cada candidato (coerência com tema, novidade, entropia)
  escolhe o melhor

Pilar 1: P(next | estado_enriquecido) — ainda Markov 1ª ordem
Pilar 2: 5D decide qual token gerar (sem threshold hardcoded)
Pilar 5: cada token gerado atualiza a memória (loop fechado)
Pilar 7: entidades e tema são correlacionados via NMI

Uso:
    gen = GeradorCoerente(coupling)
    texto = gen.gerar("criar monstro dragao", max_tokens=100)
"""
import re, math
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict


class GeradorCoerente:

    def __init__(self, coupling, max_recentes: int = 30,
                 max_entidades: int = 20):
        self._coupling = coupling
        self._max_recentes = max_recentes
        self._max_entidades = max_entidades
        self._tema_cache_texto = ""  # ultimo texto cacheado em _tema_cache_sig
        self._tema_cache_sig: Dict[str, int] = {}

    def gerar(self, semente: str, max_tokens: int = 100,
              top_k: int = 5) -> str:
        """Gera texto longo coerente a partir de uma semente.

        Working memory mantém coerência global:
        - buffer_recentes: últimos N tokens gerados (contexto imediato)
        - assinatura_tema: assinatura composicional do texto todo (tema)
        - entidades: palavras de alta especificidade mencionadas

        A cada passo, avalia top-K candidatos com 5D e escolhe o mais
        coerente com o tema (sem repetir — loop detection).
        """
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', semente.lower())
        if not tokens:
            return semente

        # Resetar cache incremental de tema (nova semente = novo tema)
        self._tema_cache_texto = ""
        self._tema_cache_sig = {}

        entidades: Set[str] = set()
        recentes: List[str] = list(tokens)
        texto_acumulado = semente

        for _ in range(max_tokens):
            estado = self._construir_estado(recentes, entidades)
            tema_sig = self._assinatura_tema(texto_acumulado)
            candidatos = self._gerar_candidatos(estado, top_k, tema_sig, recentes)
            if not candidatos:
                break

            melhor = self._escolher_candidato(
                candidatos, recentes, tema_sig, entidades)
            if not melhor:
                break

            tokens.append(melhor)
            recentes.append(melhor)
            if len(recentes) > self._max_recentes:
                recentes = recentes[-self._max_recentes:]

            if self._e_entidade(melhor):
                entidades.add(melhor)
                if len(entidades) > self._max_entidades:
                    entidades = set(list(entidades)[-self._max_entidades:])

            texto_acumulado += ' ' + melhor

            if self._detectar_loop(recentes):
                # Tentar restart temático antes de parar
                tema_sig = self._assinatura_tema(texto_acumulado)
                restart = self._restart_tematico(top_k, tema_sig, recentes)
                if restart:
                    # Forçar o melhor candidato do restart
                    melhor_restart = restart[0][0]
                    tokens.append(melhor_restart)
                    recentes.append(melhor_restart)
                    if len(recentes) > self._max_recentes:
                        recentes = recentes[-self._max_recentes:]
                    texto_acumulado += ' ' + melhor_restart
                    continue
                break

        return ' '.join(tokens)

    def _construir_estado(self, recentes: List[str],
                          entidades: Set[str]) -> str:
        """Constrói estado enriquecido: recentes + entidades."""
        partes = list(recentes[-self._max_recentes:])
        if entidades:
            partes.append(' '.join(list(entidades)[-5:]))
        return ' '.join(partes)

    def _gerar_candidatos(self, estado: str,
                          top_k: int,
                          tema_sig: Optional[Dict[str, int]] = None,
                          recentes: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """Gera top-K candidatos via transição markoviana de palavras.

        Usa _transicao_palavra (P(proxima_palavra | palavra_atual))
        em vez de decidir() (que retorna ações). Isso gera PALAVRAS,
        não classificações — necessário para geração de texto.
        """
        palavras = re.findall(r'[a-zà-ÿ0-9]{2,}', estado.lower())
        if not palavras:
            return []

        # Ordem superior: _ngrama[3] (P(prox | 2 tokens anter.)) e _ngrama[4].
        # Estes indices sao alimentados em coupling.alimentar() mas eram mortos.
        # Conectar aqui revive ordem > 1: captura regressao n->n+1, evita loops.
        # IMPORTANTE: usa RECENTES (sem injecao de entidades) para o prefixo.
        # O `estado` injeta entidades no final e corromperia o prefixo.
        ngramas = self._coupling._ngrama
        candidatos_ord = []
        if recentes and len(recentes) >= 2:
            for ordem in (4, 3):
                if len(recentes) >= ordem - 1:
                    prefix = tuple(recentes[-(ordem - 1):])
                    dist = ngramas.get(ordem, {}).get(prefix, {})
                    if dist:
                        total = sum(dist.values()) or 1
                        for w, cnt in dist.items():
                            candidatos_ord.append((w, cnt / total))
                        break
        if candidatos_ord:
            candidatos_ord.sort(key=lambda x: -x[1])
            return candidatos_ord[:top_k]

        ultima = palavras[-1]
        vizinhos = self._coupling._transicao_palavra.get(ultima, {})
        if not vizinhos:
            for p in reversed(palavras[:-1]):
                vizinhos = self._coupling._transicao_palavra.get(p, {})
                if vizinhos:
                    break

        if not vizinhos:
            # Fallback: fecho transitivo para encontrar palavras indiretas
            d_trn = self._coupling._dist_transitivo(ultima, passos=2)
            if d_trn:
                alcancaveis = {}
                visitados = {ultima}
                fronteira = [(ultima, 1.0)]
                for _ in range(2):
                    nova_front = []
                    for atual, peso in fronteira:
                        viz = self._coupling._transicao_palavra.get(atual, {})
                        for v, c in viz.items():
                            if v not in visitados:
                                visitados.add(v)
                                total_v = sum(viz.values()) or 1
                                p = peso * (c / total_v)
                                alcancaveis[v] = p
                                nova_front.append((v, p))
                    fronteira = nova_front
                if alcancaveis:
                    candidatos = sorted(alcancaveis.items(), key=lambda x: -x[1])
                    return candidatos[:top_k]
            # Último fallback: restart temático
            return self._restart_tematico(top_k, tema_sig, recentes)

        total = sum(vizinhos.values()) or 1
        candidatos = [(palavra, count / total)
                      for palavra, count in vizinhos.items()]
        candidatos.sort(key=lambda x: -x[1])

        # Se sobra espaço, completar com fecho transitivo (palavras indiretas)
        if len(candidatos) < top_k:
            alcancaveis = {}
            visitados = {ultima} | {c[0] for c in candidatos}
            fronteira = [(ultima, 1.0)]
            for _ in range(2):
                nova_front = []
                for atual, peso in fronteira:
                    viz = self._coupling._transicao_palavra.get(atual, {})
                    for v, c in viz.items():
                        if v not in visitados:
                            visitados.add(v)
                            total_v = sum(viz.values()) or 1
                            p = peso * (c / total_v) * 0.5
                            alcancaveis[v] = p
                            nova_front.append((v, p))
                fronteira = nova_front
            for palavra, peso in sorted(alcancaveis.items(), key=lambda x: -x[1]):
                candidatos.append((palavra, peso))
                if len(candidatos) >= top_k:
                    break

        # Se ainda não há candidatos suficientes, expandir globalmente
        if len(candidatos) < top_k:
            palavras_estado = set(palavras)
            globais = {}
            for p in palavras_estado:
                for palavra_vocab, viz in self._coupling._transicao_palavra.items():
                    if p in viz and palavra_vocab not in palavras_estado:
                        if palavra_vocab not in dict(candidatos):
                            globais[palavra_vocab] = globais.get(palavra_vocab, 0) + viz[p]
            for palavra, peso in sorted(globais.items(), key=lambda x: -x[1]):
                candidatos.append((palavra, min(0.3, peso / 10)))
                if len(candidatos) >= top_k:
                    break

        # Se candidatos são poucos E já muito repetidos, adicionar restart temático
        recentes_set = set(recentes[-10:]) if recentes else set()
        candidatos_novos = [c for c in candidatos if c[0] not in recentes_set]
        if len(candidatos_novos) < 2 and tema_sig:
            restart = self._restart_tematico(top_k - len(candidatos), tema_sig, recentes)
            candidatos.extend(restart)

        return candidatos[:top_k]

    def _restart_tematico(self, top_k: int,
                          tema_sig: Optional[Dict[str, int]],
                          recentes: Optional[List[str]]) -> List[Tuple[str, float]]:
        """Restart temático: encontra palavras do vocabulário com maior NMI
        com o tema atual, excluindo palavras já usadas recentemente.

        Determinístico (sem aleatoriedade) — ordena por NMI.
        """
        if not tema_sig or top_k <= 0:
            return []

        recentes_set = set(recentes[-10:]) if recentes else set()
        candidatos = []

        for palavra in self._coupling._palavra_acao:
            if palavra in recentes_set:
                continue
            sig = self._coupling._assinatura_palavra(palavra)
            if not sig:
                continue
            nmi = self._coupling._nmi(sig, tema_sig)
            if nmi > 0.01:
                candidatos.append((palavra, nmi * 0.3))  # peso reduzido

        candidatos.sort(key=lambda x: -x[1])
        return candidatos[:top_k]

    def _assinatura_tema(self, texto: str) -> Dict[str, int]:
        """Extrai assinatura composicional do texto acumulado (tema).

        Cache incremental: se texto e extensao do cache anterior,
        compor cached sig com o token novo em vez de recompor do zero.
        Elimina O(n²) de _tentar_inversao_funtor a cada token gerado.
        """
        # Se texto cresceu apenas um token, usar cache incremental
        if self._tema_cache_sig and texto.startswith(self._tema_cache_texto):
            sufixo = texto[len(self._tema_cache_texto):].strip()
            if sufixo and ' ' not in sufixo.strip():
                sig_novo = self._coupling._assinatura_palavra(sufixo)
                if sig_novo:
                    sig = self._coupling.compor(self._tema_cache_sig, sig_novo)
                    self._tema_cache_texto = texto
                    self._tema_cache_sig = sig
                    return sig

        # Cache miss ou texto muito diferente: recompor do zero
        sig = self._coupling._assinatura_frase(texto)
        self._tema_cache_texto = texto
        self._tema_cache_sig = sig
        return sig

    def _escolher_candidato(self, candidatos: List[Tuple[str, float]],
                            recentes: List[str],
                            tema_sig: Dict[str, int],
                            entidades: Set[str]) -> Optional[str]:
        """Escolhe o melhor candidato via Equação 5D.

        CERTEZA: confiança do coupling
        COMPLETUDE: coerência com tema (NMI candidato vs tema)
        INFORMACAO: entropia do candidato
        ESTABILIDADE: pune repetição (loop) e caos
        EFICIENCIA: 1/log2(n_candidatos+1)
        """
        try:
            from mcr.equacao_mcr import avaliar_5d
        except ImportError:
            from equacao_mcr import avaliar_5d

        melhor_token = None
        melhor_nota = -1.0

        contagem_recente = defaultdict(int)
        for t in recentes:
            contagem_recente[t] += 1

        for token, conf in candidatos:
            # Penalidade suave por repetição (não filtro duro)
            repeticao = contagem_recente.get(token, 0)
            penalidade_rep = 1.0 / (1.0 + repeticao * 2)  # 0x=1.0, 1x=0.33, 2x=0.2
            conf_ajustada = conf * penalidade_rep

            if conf_ajustada < 0.01:
                continue

            certeza = conf_ajustada

            sig_token = self._coupling._assinatura_palavra(token)
            completude = self._coupling._nmi(sig_token, tema_sig) if sig_token and tema_sig else 0.0

            d_acao = self._coupling._palavra_acao.get(token, {})
            informacao = self._coupling._entropia_dist(d_acao) if d_acao else 0.5

            estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * 0.15 ** 2))

            eficiencia = 1.0 / math.log2(max(len(candidatos) + 1, 2))

            nota = avaliar_5d(certeza, completude, informacao,
                              estabilidade, eficiencia)

            if nota > melhor_nota:
                melhor_nota = nota
                melhor_token = token

        return melhor_token

    def _e_entidade(self, token: str) -> bool:
        """Verifica se um token é uma entidade (alta especificidade)."""
        dist = self._coupling._palavra_acao.get(token, {})
        if not dist:
            return False
        total = sum(dist.values()) or 1
        probs = [c / total for c in dist.values()]
        h = 0.0
        for p in probs:
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(dist), 2))
        h_norm = h / max_h if max_h > 0 else 0
        return (1.0 - h_norm) > 0.7

    def _detectar_loop(self, recentes: List[str]) -> bool:
        """Detecta repetição nos últimos tokens (H < tercil inferior)."""
        if len(recentes) < 6:
            return False
        janela = recentes[-6:]
        counter = defaultdict(int)
        for t in janela:
            counter[t] += 1
        total = len(janela)
        h = 0.0
        for c in counter.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(counter), 2))
        h_norm = h / max_h if max_h > 0 else 0
        return h_norm < 0.3