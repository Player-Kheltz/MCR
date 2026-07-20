"""SonhoMarkoviano — O MCR sonha markovianamente a partir do proprio estado.

O MCR ja gera sequencias ineditas a partir de sementes externas (GeradorCoerente).
O sonho aponta a geracao para DENTRO: le o estado interno do coupling como
sequencia, gera markovianamente a partir dela, e alimenta o resultado de volta.

Isso e a fonte de variacao que faltava para o nivel 7 (self):
- Variação: geracao markoviana do proprio estado (deterministico, sem random)
- Ciclo: sonho alimentado de volta via FASE 21 (alimentar)
- Persistencia diferencial: consequencias realimentadas como P(b|a) (H22)

O MCR "sonha" como na Fase 4 gerava nomes ineditos ("Eridan"):
recombina a estrutura que internalizou em sequencias que nunca existiram.

Pilar 1: P(b|a) puro — sem random, sem LLM
Pilar 2: entropia decide quais sonhos persistem
Pilar 4: esquecimento poda sonhos que nao geram estrutura
Pilar 9: se o sonho nao faz sentido, a entropia revela

Uso:
    from mcr.sonho_markoviano import SonhoMarkoviano
    from mcr.coupling import MCRCoupling
    c = MCRCoupling()
    # ... alimentar c com corpus ...
    sonho = SonhoMarkoviano(c)
    sequencia = sonho.sonhar(n_passos=50)
    # sequencia e uma string gerada markovianamente a partir do estado de c
    # pode ser alimentada de volta: c.alimentar(sequencia, "sonhar")
"""
import re, math, random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


class SonhoMarkoviano:
    """O MCR sonha a partir do proprio estado interno.

    Serializa o estado do coupling como sequencia de tokens, usa
    _transicao_palavra e _ngrama para gerar markovianamente, e retorna
    uma sequencia inedita deterministica.
    """

    def __init__(self, coupling):
        self._c = coupling
        self._RE_TOKENS = re.compile(r'[a-zà-ÿ]{2,}|[0-9]+')

    def _serializar_estado(self, max_tokens: int = 200) -> str:
        """Serializa o estado interno do coupling como texto.

        Le os planos N-dim do coupling e os concatena como sequencia:
        - _palavra_acao: palavras conhecidas e suas acoes
        - _transicao_palavra: transicoes aprendidas
        - _freq_acao: distribuicao de acoes
        - _feature_acao: features por acao

        Returns:
            string com tokens do estado, pronta para gerar a partir dela.
        """
        tokens = []

        # 1. Palavras conhecidas (amostra para nao explodir)
        palavras = list(self._c._palavra_acao.keys())[:max_tokens // 4]
        for p in palavras:
            tokens.append(p)

        # 2. Acoes mais frequentes
        acoes_freq = sorted(self._c._freq_acao.items(), key=lambda x: -x[1])[:20]
        for acao, freq in acoes_freq:
            tokens.append(acao)

        # 3. Transicoes mais frequentes (amostra)
        transicoes = []
        for a, proximos in list(self._c._transicao_palavra.items())[:max_tokens // 4]:
            if proximos:
                b = max(proximos.items(), key=lambda x: x[1])[0]
                transicoes.append(a)
                transicoes.append(b)
        tokens.extend(transicoes[:max_tokens // 2])

        # 4. Features mais discriminativas (top por frequencia)
        for acao, feats in list(self._c._acao_features.items())[:20]:
            if feats:
                top_feat = max(feats.items(), key=lambda x: x[1])[0]
                # Extrai token da feature (remove prefixo do plano)
                feat_token = top_feat.split(":")[-1] if ":" in top_feat else top_feat
                if self._RE_TOKENS.fullmatch(feat_token):
                    tokens.append(feat_token)

        # Limita e junta
        tokens = tokens[:max_tokens]
        return " ".join(tokens)

    def sonhar(self, n_passos: int = 50, semente: Optional[str] = None,
               modo: str = "entropia") -> str:
        """Gera uma sequencia markoviana a partir do estado interno.

        Args:
            n_passos: numero de tokens a gerar
            semente: semente opcional (default: estado serializado)
            modo: "greedy" (max P(b|a)) ou "entropia" (max H da sequencia)

        Returns:
            string com a sequencia gerada (sonho)
        """
        if semente is None:
            semente = self._serializar_estado()

        tokens = self._RE_TOKENS.findall(semente.lower())
        if not tokens:
            return ""

        # Gera markovianamente usando _transicao_palavra + _ngrama
        for _ in range(n_passos):
            proximo = self._gerar_proximo(tokens, modo=modo)
            if proximo is None:
                break
            tokens.append(proximo)

        return " ".join(tokens)

    def _gerar_proximo(self, tokens: List[str],
                       modo: str = "entropia") -> Optional[str]:
        """Gera o proximo token markovianamente.

        Estrategia (sem random, Pilar 1):
        1. Tenta n-grama de ordem 3 (contexto mais rico)
        2. Cai para n-grama de ordem 2
        3. Cai para _transicao_palavra (ordem 1)
        4. Se nada, para

        Escolha:
        - greedy: maior P(b|a) — deterministico, mas converge
        - entropia: token que MAXIMIZA H da sequencia apos adiciona-lo
          Deterministico (Pilar 1) e gera diversidade sem random.
          Quem empata em H desempata por P(b|a) (preferir o mais provavel).
        """
        # Obter candidatos do n-grama mais rico disponivel
        candidatos = self._obter_candidatos(tokens)
        if not candidatos:
            return None

        if modo == "greedy":
            return max(candidatos.items(), key=lambda x: x[1])[0]

        # Modo entropia: escolher token que maximiza H da JANELA recente
        # (não da sequência inteira — impacto real do próximo token)
        from collections import Counter
        from math import log2

        # Janela de working memory: últimos 20 tokens
        janela = tokens[-20:] if len(tokens) > 20 else tokens[:]
        contagem = Counter(janela)
        n = len(janela)

        melhor_token = None
        melhor_h = -1.0
        melhor_p = 0.0

        for token, p_ba in candidatos.items():
            # Simular adicionar token e calcular H da janela
            cont_sim = contagem.copy()
            cont_sim[token] = cont_sim.get(token, 0) + 1
            n_sim = n + 1
            h_sim = 0.0
            for c in cont_sim.values():
                p = c / n_sim
                if p > 0:
                    h_sim -= p * log2(p)

            # Maximizar H; desempatar por P(b|a)
            if h_sim > melhor_h or (abs(h_sim - melhor_h) < 1e-9 and p_ba > melhor_p):
                melhor_h = h_sim
                melhor_token = token
                melhor_p = p_ba

        return melhor_token

    def _obter_candidatos(self, tokens: List[str]) -> Dict[str, float]:
        """Obtem candidatos a proximo token do n-grama mais rico disponivel.

        Returns:
            dict {token: P(b|a)} dos candidatos
        """
        # Ordem 3: _ngrama[3]
        if len(tokens) >= 2:
            pref = (tokens[-2], tokens[-1])
            ngrama3 = self._c._ngrama.get(3, {})
            prox = ngrama3.get(pref, {})
            if prox:
                return dict(prox)

        # Ordem 2: _ngrama[2]
        if len(tokens) >= 1:
            pref = (tokens[-1],)
            ngrama2 = self._c._ngrama.get(2, {})
            prox = ngrama2.get(pref, {})
            if prox:
                return dict(prox)

        # Ordem 1: _transicao_palavra
        ultima = tokens[-1] if tokens else ""
        prox = self._c._transicao_palavra.get(ultima, {})
        if prox:
            return dict(prox)

        return {}

    def ciclo_sonho(self, n_ciclos: int = 10, n_passos: int = 50,
                    modo: str = "entropia") -> List[dict]:
        """Executa n ciclos de sonho com realimentacao.

        Cada ciclo:
        1. Serializa estado atual OU usa final do sonho anterior como semente
        2. Gera sonho markovianamente
        3. Alimenta sonho de volta como observacao (acao="sonhar")
        4. Registra metricas (entropia, novidade, persistencia)

        Variacao sem random (Pilar 1): cada ciclo usa o final do sonho
        anterior como semente do proximo. Markov puro — o estado mudou
        porque o sonho anterior foi alimentado de volta.

        Args:
            n_ciclos: numero de ciclos de sonho
            n_passos: tokens gerados por ciclo
            modo: "greedy" (max P(b|a)) ou "entropia" (max H da sequencia)

        Returns:
            lista de dicts com metricas de cada ciclo
        """
        resultados = []
        sonhos_unicos = set()
        semente_atual = None  # None = usar estado serializado no primeiro ciclo

        for i in range(n_ciclos):
            # 1. Semente: primeiro ciclo usa estado, demais usam final do anterior
            if semente_atual is None:
                semente = self._serializar_estado()
            else:
                semente = semente_atual

            # 2. Gera sonho
            sonho = self.sonhar(n_passos=n_passos, semente=semente, modo=modo)

            # 3. Metricas
            tokens_sonho = self._RE_TOKENS.findall(sonho.lower())
            n_tokens = len(tokens_sonho)
            n_uniq = len(set(tokens_sonho))
            # Entropia do sonho
            from collections import Counter
            from math import log2
            cont = Counter(tokens_sonho)
            entropia = 0.0
            for c in cont.values():
                p = c / n_tokens if n_tokens > 0 else 0
                if p > 0:
                    entropia -= p * log2(p)

            # Novidade: quantos tokens do sonho sao novos vs conhecidos
            vocab = set(self._c._palavra_acao.keys())
            n_novos = sum(1 for t in tokens_sonho if t not in vocab)
            n_conhecidos = n_tokens - n_novos

            # Sonho e unico? (nao repetido)
            sonho_hash = sonho[:100]  # primeiros 100 chars
            is_novo = sonho_hash not in sonhos_unicos
            sonhos_unicos.add(sonho_hash)

            # 4. Alimenta de volta (FASE 21)
            self._c.alimentar(sonho, "sonhar")

            # 5. Proxima semente = estado serializado + final do sonho (markoviano)
            if tokens_sonho:
                # Combina estado atual com final do sonho — o estado mudou
                # porque o sonho foi alimentado de volta
                estado_atual = self._serializar_estado(max_tokens=50)
                final_sonho = " ".join(tokens_sonho[-15:])
                semente_atual = final_sonho + " " + estado_atual

            # 6. Registra
            r = {
                "ciclo": i + 1,
                "n_tokens": n_tokens,
                "n_uniq": n_uniq,
                "entropia": round(entropia, 3),
                "n_novos": n_novos,
                "n_conhecidos": n_conhecidos,
                "is_novo": is_novo,
                "semente": semente[:60],
                "sonho_preview": sonho[:120],
            }
            resultados.append(r)
            print(f"  Ciclo {i+1}/{n_ciclos}: {n_tokens} tokens, H={entropia:.3f}, "
                  f"novos={n_novos}, unico={'sim' if is_novo else 'nao'}")
            print(f"    Semente: '{semente[:50]}...'")
            print(f"    Sonho:   '{sonho[:60]}...'")

        return resultados

    def estatisticas(self) -> dict:
        """Retorna estatisticas do estado do coupling apos sonhos."""
        return {
            "total_obs": self._c._total,
            "vocab": len(self._c._palavra_acao),
            "n_acoes": len(self._c._freq_acao),
            "freq_sonhar": self._c._freq_acao.get("sonhar", 0),
            "acoes": dict(self._c._freq_acao),
        }
