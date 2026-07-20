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
from collections import defaultdict, Counter


class SonhoMarkoviano:
    """O MCR sonha a partir do proprio estado interno.

    Serializa o estado do coupling como sequencia de tokens, usa
    _transicao_palavra e _ngrama para gerar markovianamente, e retorna
    uma sequencia inedita deterministica.
    """

    def __init__(self, coupling):
        self._c = coupling
        self._RE_TOKENS = re.compile(r'[a-zà-ÿ]{2,}|[0-9]+')
        self._confiancas_historico: List[float] = []  # threshold emergente

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

    def emergir(self, n_hipoteses: int = 20) -> List[dict]:
        """O sonho como EMERGIR: o MCR pergunta 'E se X + Y = Z?'

        Como Kheltz faz 'decida, explore, valide' com o LLM, o MCR
        faz consigo mesmo:

        1. DECIDA: sonho escolhe dois conceitos do vocabulario (Pilar 1)
        2. EXPLORE: recombina markovianamente — 'E se X + Y?'
        3. VALIDE: motor verifica se a recombinação tem estrutura
           - decidir() na recombinação → (acao, conf)
           - Se conf alta: hipotese confirmada (expande)
           - Se conf baixa: hipotese refutada (descarta, Pilar 9)
        4. Se confirmada: nova relação descoberta
           - X e Y estao relacionados via acao Z
           - Pode alimentar formigueiro (novo cluster)

        O sonho NAO alimenta o motor diretamente. Ele DESCOBRE
        relacoes que o motor ja conhece mas nao conectou. Como
        'E se 1+2=3?' — o motor ja sabe, mas talvez nao conectou
        que 'um' + 'dois' aparece em PA, FIB, E Collatz.

        Returns:
            lista de hipoteses com (X, Y, Z, conf, confirmada)
        """
        # 1. Amostra conceitos do vocabulario (Pilar 1: P(b|a) puro)
        vocab = list(self._c._palavra_acao.keys())
        if len(vocab) < 2:
            return []

        # 2. Para cada hipotese: 'E se X + Y?'
        hipoteses = []
        for _ in range(n_hipoteses):
            # DECIDA: escolhe dois conceitos (greedy do n-grama)
            # Comeca do ultimo conceito e segue a cadeia
            x = vocab[len(vocab) // 2]  # ponto medio do vocab
            if not self._c._transicao_palavra.get(x):
                # Sem transicoes — pula
                continue

            # EXPLORE: gera Y a partir de X (markoviano)
            prox = self._c._transicao_palavra.get(x, {})
            if not prox:
                continue
            y = max(prox.items(), key=lambda p: p[1])[0]

            # 'E se X + Y?'
            recomb = x + " " + y

            # VALIDE: motor verifica se a recombinação tem estrutura
            acao, conf = self._c.decidir(recomb, (None, 0.0))

            # Tambem verifica cada conceito isolado
            acao_x, conf_x = self._c.decidir(x, (None, 0.0))
            acao_y, conf_y = self._c.decidir(y, (None, 0.0))

            # Hipotese confirmada se:
            # - recomb tem conf alta (motor reconhece estrutura)
            # - recomb mapeia para acao diferente de X ou Y isolados
            #   (sínergia: X+Y revela algo que nem X nem Y isolados revelam)
            confirmada = conf > 0.3 and (
                acao != acao_x or acao != acao_y
            )

            # Sinergia: a recombinação é mais que a soma das partes?
            sinergia = conf - max(conf_x, conf_y)

            hipoteses.append({
                "x": x,
                "y": y,
                "recomb": recomb,
                "acao": acao,
                "conf": round(conf, 4),
                "acao_x": acao_x,
                "conf_x": round(conf_x, 4),
                "acao_y": acao_y,
                "conf_y": round(conf_y, 4),
                "confirmada": confirmada,
                "sinergia": round(sinergia, 4),
            })

        # 3. Ordenar por sinergia (maiores descobertas primeiro)
        hipoteses.sort(key=lambda h: -h["sinergia"])

        return hipoteses

    def emergir_livre(self, n_hipoteses: int = 20) -> List[dict]:
        """Emergir livre: sonho recombina SEM objetivo, motor valida.

        Diferente de emergir(), aqui o sonho recombina conceitos que
        NUNCA coocorrem no corpus. 'E if um + cachorro?' — o motor
        nunca viu isso, mas talvez descubra uma relacao nova.

        1. Sonho pega dois conceitos ALEATORIOS do vocab (mas
           deterministico — Pilar 1: usa hash do estado como seed)
        2. Motor valida: 'faz sentido?'
        3. Se sim: relacao nova descoberta
        4. Se nao: descarta (Pilar 9)

        Returns:
            lista de hipoteses livres
        """
        vocab = sorted(self._c._palavra_acao.keys())
        if len(vocab) < 2:
            return []

        # Seed deterministica: hash do estado (Pilar 1, sem random)
        estado_hash = hash(self._serializar_estado(max_tokens=50))

        hipoteses = []
        for i in range(n_hipoteses):
            # Deterministic: pares baseados em hash
            idx_x = (estado_hash + i * 7) % len(vocab)
            idx_y = (estado_hash + i * 13 + 3) % len(vocab)
            if idx_x == idx_y:
                idx_y = (idx_y + 1) % len(vocab)

            x = vocab[idx_x]
            y = vocab[idx_y]

            # 'E se X + Y?'
            recomb = x + " " + y

            # VALIDE
            acao, conf = self._c.decidir(recomb, (None, 0.0))
            acao_x, conf_x = self._c.decidir(x, (None, 0.0))
            acao_y, conf_y = self._c.decidir(y, (None, 0.0))

            # Sinergia: recombinação mais forte que partes isoladas
            sinergia = conf - max(conf_x, conf_y)
            confirmada = sinergia > 0.05  # recombinação é significativamente melhor

            # Nova: X e Y nunca coocorrem no corpus?
            coocorre = y in self._c._transicao_palavra.get(x, {}) or \
                       x in self._c._transicao_palavra.get(y, {})

            hipoteses.append({
                "x": x,
                "y": y,
                "recomb": recomb,
                "acao": acao,
                "conf": round(conf, 4),
                "sinergia": round(sinergia, 4),
                "confirmada": confirmada,
                "coocorre_no_corpus": coocorre,
                "e_nova": not coocorre and confirmada,
            })

        # Ordenar por sinergia
        hipoteses.sort(key=lambda h: -h["sinergia"])

        return hipoteses

    def emergir_tudo(self, n_tiros: int = 100) -> List[dict]:
        """Tiro cego em TODOS os niveis — mutacao multi-escala.

        X + Y = Z nao e so sobre palavras. E sobre TUDO:
        - byte + byte
        - char + char
        - token + token
        - feature + feature
        - cluster + cluster
        - cross-level: byte + token, feature + cluster, etc

        Como mutacao biologica: pode acontecer em qualquer nivel
        (DNA, gene, cromossomo, organismo). O motor e a selecao
        natural que valida.

        Cada tiro e deterministico (Pilar 1): hash do estado como
        seed. O motor valida (Pilar 2): conf > threshold = sobrevive.

        Returns:
            lista de tiros com (nivel_x, x, nivel_y, y, z, conf, sobrevive)
        """
        # Coletar elementos de cada nivel
        niveis = {}

        # Nivel byte: valores 0-255 que aparecem nas features
        bytes_presentes = set()
        for feat_dict in self._c._acao_features.values():
            for f in feat_dict:
                if f.startswith("b:"):
                    try:
                        bytes_presentes.add(int(f.split(":")[1]))
                    except ValueError:
                        pass
        niveis["byte"] = sorted(bytes_presentes)[:50]

        # Nivel char: chars que aparecem em features c:
        chars_presentes = set()
        for feat_dict in self._c._acao_features.values():
            for f in feat_dict:
                if f.startswith("c:"):
                    chars_presentes.add(f.split(":", 1)[1])
        niveis["char"] = sorted(chars_presentes)[:50]

        # Nivel token: palavras do vocabulario
        niveis["token"] = sorted(self._c._palavra_acao.keys())[:100]

        # Nivel feature: features discriminativas (top por freq)
        feats = Counter()
        for feat_dict in self._c._acao_features.values():
            for f, c in feat_dict.items():
                feats[f] += c
        niveis["feature"] = [f for f, _ in feats.most_common(50)]

        # Nivel cluster: acoes como clusters
        niveis["cluster"] = sorted(self._c._freq_acao.keys())

        # Filtrar niveis vazios
        niveis = {k: v for k, v in niveis.items() if len(v) >= 2}
        nomes_niveis = list(niveis.keys())

        if len(nomes_niveis) < 2:
            return []

        # Seed deterministica
        estado_hash = hash(self._serializar_estado(max_tokens=50))

        tiros = []
        for i in range(n_tiros):
            # Escolher dois niveis (deterministico, pode ser cross-level)
            idx_n1 = (estado_hash + i * 7) % len(nomes_niveis)
            idx_n2 = (estado_hash + i * 13 + 3) % len(nomes_niveis)
            n1 = nomes_niveis[idx_n1]
            n2 = nomes_niveis[idx_n2]

            # Escolher X e Y dos niveis
            elems1 = niveis[n1]
            elems2 = niveis[n2]
            x = elems1[(estado_hash + i * 17) % len(elems1)]
            y = elems2[(estado_hash + i * 23 + 5) % len(elems2)]

            # Evitar X == Y no mesmo nivel
            if n1 == n2 and x == y:
                y = elems2[(elems2.index(y) + 1) % len(elems2)]

            # Recombinar: converter para string de input
            # X + Y = Z
            x_str = str(x)
            y_str = str(y)
            recomb = x_str + " " + y_str

            # Motor valida: Z = decidir(recomb)
            acao, conf = self._c.decidir(recomb, (None, 0.0))

            # Tambem validar X e Y isolados
            acao_x, conf_x = self._c.decidir(x_str, (None, 0.0))
            acao_y, conf_y = self._c.decidir(y_str, (None, 0.0))

            # Sinergia: recomb mais forte que partes
            sinergia = conf - max(conf_x, conf_y)

            # Sobrevive? (Pilar 2: motor decide)
            sobrevive = sinergia > 0.05

            # Nova? (X e Y nunca coocorrem)
            coocorre = (isinstance(x, str) and isinstance(y, str) and
                       (y in self._c._transicao_palavra.get(x, {}) or
                        x in self._c._transicao_palavra.get(y, {})))

            tiros.append({
                "nivel_x": n1,
                "x": x_str[:20],
                "nivel_y": n2,
                "y": y_str[:20],
                "z": acao,
                "conf": round(conf, 4),
                "sinergia": round(sinergia, 4),
                "sobrevive": sobrevive,
                "coocorre": coocorre,
                "e_nova": sobrevive and not coocorre,
                "cross_level": n1 != n2,
            })

        # Ordenar por sinergia
        tiros.sort(key=lambda t: -t["sinergia"])
        return tiros

    def estatisticas(self) -> dict:
        """Retorna estatisticas do estado do coupling apos sonhos."""
        return {
            "total_obs": self._c._total,
            "vocab": len(self._c._palavra_acao),
            "n_acoes": len(self._c._freq_acao),
            "freq_sonhar": self._c._freq_acao.get("sonhar", 0),
            "acoes": dict(self._c._freq_acao),
        }

    def inspirar(self, texto: str, conf_motor: float,
                 threshold: float = None) -> Optional[dict]:
        """Sistema 2 consulta Sistema 1: o motor pede inspiracao ao sonho.

        Como Kahneman invertido:
        - Motor (Sistema 1): rapido, preciso, decidir() em 50ms
        - Sonho (Sistema 2): livre, criativo, sem objetivo

        O motor consulta o sonho SO quando tem baixa confianca.
        O threshold NAO e hardcoded — emerge da mediana das confiancas
        observadas pelo motor (Pilar 2: entropia descobre). Se a
        confianca atual esta abaixo da mediana historica, o motor
        esta "menos confiante que o normal" e pede inspiracao.

        O sonho NAO escreve no motor. O motor CONSULTA o sonho.
        Como o humano que sonha uma solucao mas verifica com logica
        ao acordar.

        Args:
            texto: input do usuario
            conf_motor: confianca do motor (decidir())
            threshold: se None, usa mediana das confiancas observadas

        Returns:
            dict com acao, confianca, fonte ('motor' ou 'sonho_inspirado')
            ou None se o motor ja estava confiante
        """
        # Threshold emergente: mediana das confiancas observadas (Pilar 2)
        # O sonhador mantem seu proprio historico de confiancas do motor
        if threshold is None:
            if len(self._confiancas_historico) >= 5:
                confs_ord = sorted(self._confiancas_historico)
                threshold = confs_ord[len(confs_ord) // 2]
            else:
                # Sem historico suficiente — nao inspira (Pilar 9: honesto)
                # Registra a confianca para futuro
                self._confiancas_historico.append(conf_motor)
                return None

        # Registra confianca para futuro (DEPOIS de calcular threshold)
        self._confiancas_historico.append(conf_motor)

        # Se o motor ja esta confiante, nao precisa de inspiracao
        if conf_motor >= threshold:
            return None

        # 1. Gerar alternativas do sonho
        # Semente = texto do usuario + estado interno
        estado = self._serializar_estado(max_tokens=30)
        semente = texto + " " + estado

        # Gerar 3 sonhos (trindade de perspectivas)
        alternativas = []
        for i in range(3):
            # Variar semente levemente: rotacionar estado
            estado_rot = " ".join(estado.split()[i*10:] + estado.split()[:i*10])
            semente_i = texto + " " + estado_rot
            sonho = self.sonhar(n_passos=20, semente=semente_i, modo="greedy")
            alternativas.append(sonho)

        # 2. Motor avalia cada alternativa
        melhor_acao = None
        melhor_conf = conf_motor  # baseline = confianca original

        for alt in alternativas:
            # Motor avalia a alternativa com sua propria logica
            acao, conf = self._c.decidir(alt, (None, 0.0))
            if conf > melhor_conf:
                melhor_conf = conf
                melhor_acao = acao

        # 3. Se nenhuma alternativa superou o motor, manter original
        if melhor_acao is None:
            return {
                "acao": None,  # manter decisao original
                "confianca": conf_motor,
                "fonte": "motor_sem_inspiracao",
                "n_alternativas": 3,
                "threshold": round(threshold, 4),
            }

        return {
            "acao": melhor_acao,
            "confianca": melhor_conf,
            "fonte": "sonho_inspirado",
            "n_alternativas": 3,
            "conf_original": conf_motor,
            "threshold": round(threshold, 4),
        }
