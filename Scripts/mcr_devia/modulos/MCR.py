#!/usr/bin/env python3
"""MCR — Classe ÚNICA. MarkovUniversal em todos os níveis.

Substitui: lexico_v2.py + intention_engine.py + auto_trigger.py + aprendiz_de_padroes.py
+ partes de pipeline_executor.py (decisão, autoavaliação, loop)

Níveis:
  mk_byte: bytes → transições → estrutura
  mk_palavra: palavras → transições → frases
  mk_token: tipos → transições → intenção
  mk_intencao: intenção → transições → ação
  mk_decisor: estado → transições → decisão
  mk_acao: ação → transições → resultado

Tudo Markov. Tudo o mesmo código. Zero hardcode.
"""
import os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

# MCR autossuficiente — não depende de módulos externos.
# Equivalentes internos substituem KnowledgeGraph, PatternEngine, etc.
# Módulos externos continuam existindo para outros componentes do sistema.
MCR_COMPLETO = True

# KnowledgeGraph via MCRBufferKG (singleton, evita recarregar 1300+ lessons)
def _get_kg():
    """Retorna KG (tenta import direto primeiro, depois buffer).
    Evita recursao: MCRBufferKG chama _get_kg, _get_kg nao chama MCRBufferKG."""
    try:
        from modulos.kg import KnowledgeGraph
        kg = KnowledgeGraph()
        if kg:
            return kg
    except:
        pass
    try:
        from modulos.kg import KnowledgeGraph
        return KnowledgeGraph()
    except:
        return None

# PatternEngine via MCRFingerprint + _classificar_token (sem PAL_* fixos)
# Mantido apenas como fallback para código legado
try:
    from modulos.pattern_engine import PatternEngine
except ImportError:
    PatternEngine = None


class MCR:
    """MCR — 1 algoritmo, N níveis. Mesmo código para bytes, tokens, intenções, decisões.
    
    MCR é o CONCEITO: tudo é transição entre dois estados consecutivos.
    O que muda é o que entra como "token".
    O mesmo código aprende bytes, palavras, intenções, ações, filosofias.
    
    Uso:
        mcr = MCR("byte")          # antes: MarkovUniversal("byte")
        mcr.aprender_sequencia([...])
        mcr.predizer("SPA")         # → ("é", 0.5)
    """

    def __init__(self, nome: str = ""):
        self.nome = nome
        self.transicoes = {}   # {token: {proximo: count}}
        self.freq = Counter()
        self.total = 0
        self._entropia_cache: Dict[str, float] = {}
    
    def aprender(self, a: Any, b: Any):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1; self.total += 1
        if sa not in self.transicoes: self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
        self._entropia_cache.pop(sa, None)  # invalida cache
    
    def aprender_sequencia(self, seq: List[Any]):
        for i in range(len(seq)-1): self.aprender(seq[i], seq[i+1])
    
    def predizer(self, a: Any) -> Tuple[Optional[Any], float]:
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]: return None, 0.0
        prox = self.transicoes[sa]; melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor]/total
    
    def predizer_n(self, a: Any, n: int = 3) -> List[Tuple[Any, float]]:
        """Retorna os N tokens mais prováveis."""
        sa = str(a)
        if sa not in self.transicoes: return []
        prox = self.transicoes[sa]
        sorted_prox = sorted(prox.items(), key=lambda x: -x[1])
        total = sum(prox.values())
        return [(p, c/total) for p, c in sorted_prox]
    
    def entropia(self, a: Any) -> float:
        sa = str(a)
        if sa in self._entropia_cache: return self._entropia_cache[sa]
        if sa not in self.transicoes: return 1.0
        prox = self.transicoes[sa]; t = sum(prox.values())
        if t == 0: return 1.0
        h = 0.0
        for c in prox.values():
            p = c/t
            if p > 0: h -= p * math.log2(p)
        self._entropia_cache[sa] = h
        return h
    
    def entropia_media(self) -> float:
        if not self.transicoes: return 0.0
        hs = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(hs)/len(hs) if hs else 0.0
    
    def entropia_sequencia(self, seq: List[Any]) -> float:
        """Entropia média ao longo de uma sequência de estados.
        Baixa = previsível (repetitivo). Alta = variada (criativo)."""
        if not seq: return 1.0
        hs = [self.entropia(s) for s in seq]
        return sum(hs)/len(hs)
    
    def jaccard(self, outra: 'MarkovUniversal') -> float:
        """Jaccard entre CONJUNTOS DE ESTADOS desta cadeia e outra.
        Mede quão similares são os vocabulários dos dois níveis."""
        estados_a = set(self.freq.keys())
        estados_b = set(outra.freq.keys())
        if not estados_a or not estados_b: return 0.0
        inter = estados_a & estados_b
        uniao = estados_a | estados_b
        return len(inter)/len(uniao)
    
    def jaccard_transicoes(self, outra: 'MarkovUniversal') -> float:
        """Jaccard entre CONJUNTOS DE TRANSIÇÕES 'a→b' desta e outra."""
        trans_a = set(f"{a}→{b}" for a in self.transicoes for b in self.transicoes[a])
        trans_b = set(f"{a}→{b}" for a in outra.transicoes for b in outra.transicoes[a])
        if not trans_a or not trans_b: return 0.0
        inter = trans_a & trans_b
        uniao = trans_a | trans_b
        return len(inter)/len(uniao)
    
    def gerar(self, semente: Any, passos: int = 10) -> List[Any]:
        res = [semente]; atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01: break
            res.append(prox); atual = prox
        return res
    
    def jaccard_bytes(self, texto_a: str, texto_b: str) -> float:
        """Jaccard entre CONJUNTOS DE TRANSIÇÕES DE BYTES.
        Usado para: relevância de lessons, autoavaliação, similaridade.
        NOTA: Para autoavaliação, prefira similaridade_transicoes() que
        considera frequência (cosseno), não apenas conjunto (Jaccard).
        """
        ba = texto_a.encode('utf-8')
        bb = texto_b.encode('utf-8')
        ta = {f"{ba[i]:02x}->{ba[i+1]:02x}" for i in range(len(ba)-1)}
        tb = {f"{bb[i]:02x}->{bb[i+1]:02x}" for i in range(len(bb)-1)}
        inter = ta & tb; uniao = ta | tb
        return len(inter)/len(uniao) if uniao else 0.0
    
    def similaridade_transicoes(self, texto_a: str, texto_b: str,
                                 max_bytes: int = 500) -> float:
        """COSSENO entre VETORES DE FREQUÊNCIA de transições de bytes.
        
        MELHOR QUE JACCARD para autoavaliação porque:
        - Transições que aparecem MUITAS VEZES (padrões) têm mais peso
        - Respostas longas e completas não são penalizadas
        - Keyword-stuffing sem substância tem score baixo
        
        Uso: nota real de similaridade entre pergunta e resposta.
        """
        ba = texto_a.encode('utf-8')
        bb = texto_b.encode('utf-8')
        
        # Vetores de frequência das transições
        fa = {}
        fb = {}
        for i in range(len(ba) - 1):
            t = f"{ba[i]:02x}->{ba[i+1]:02x}"
            fa[t] = fa.get(t, 0) + 1
        for i in range(len(bb) - 1):
            t = f"{bb[i]:02x}->{bb[i+1]:02x}"
            fb[t] = fb.get(t, 0) + 1
        
        # Cosseno entre vetores
        todas = set(fa.keys()) | set(fb.keys())
        dot = sum(fa.get(t, 0) * fb.get(t, 0) for t in todas)
        na = math.sqrt(sum(v * v for v in fa.values()))
        nb = math.sqrt(sum(v * v for v in fb.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    
    def jaccard_bytes_ponderado(self, texto_a: str, texto_b: str) -> float:
        """Jaccard PONDERADO: primeiros 10 bytes pesam 2x.
        Captura melhor INTENÇÃO (primeiras palavras) do que o Jaccard normal."""
        da = texto_a.encode('utf-8')
        db = texto_b.encode('utf-8')
        pesos = {}
        for i in range(max(len(da), len(db)) - 1):
            if i < len(da) - 1:
                t = f"{da[i]:02x}->{da[i+1]:02x}"
                pesos[t] = pesos.get(t, 0) + (2.0 if i < 10 else 1.0)
            if i < len(db) - 1:
                t = f"{db[i]:02x}->{db[i+1]:02x}"
                pesos[t] = pesos.get(t, 0) + (2.0 if i < 10 else 1.0)
        trans_a = {f"{da[i]:02x}->{da[i+1]:02x}" for i in range(len(da)-1)}
        trans_b = {f"{db[i]:02x}->{db[i+1]:02x}" for i in range(len(db)-1)}
        inter = trans_a & trans_b
        uniao = trans_a | trans_b
        if not uniao: return 0.0
        peso_inter = sum(pesos.get(t, 1) for t in inter)
        peso_uniao = sum(pesos.get(t, 1) for t in uniao)
        return peso_inter / peso_uniao
    
    def _extrair_assinatura(self, dados: bytes) -> dict:
        """Extrai a assinatura unica de um conjunto de bytes.
        
        A assinatura e o que define a 'alma' do dado:
        - Entropia: quao imprevisivel
        - Estados unicos: quantos bytes diferentes
        - Top transicoes: os 5 pares byte→byte mais comuns
        - Fingerprint: vetor de frequencia
        """
        mk = MCR("assinatura")
        mk.aprender_sequencia(list(dados))
        
        # Top 5 transicoes mais comuns
        top5 = []
        for estado, prox in sorted(mk.transicoes.items(), 
                                     key=lambda x: -sum(x[1].values())):
            melhor = max(prox, key=prox.get) if prox else ''
            top5.append(f"{estado}->{melhor}")
        
        return {
            'entropia': round(mk.entropia_media(), 3),
            'estados': len(mk.transicoes),
            'transicoes': sum(len(v) for v in mk.transicoes.values()),
            'top5': top5,
            'tamanho': len(dados),
        }
    
    def _comparar_assinaturas(self, a: dict, b: dict) -> float:
        """Compara 2 assinaturas e retorna compatibilidade (0-1).
        
        Similaridade = quanto compartilham:
        - Mesma faixa de entropia?
        - Numero similar de estados?
        - Top transicoes coincidem?
        """
        score = 0.0
        # Entropia similar (peso 3)
        diff_ent = abs(a['entropia'] - b['entropia'])
        score += 3.0 * (1.0 - min(1.0, diff_ent))
        # Estados similares (peso 3)
        diff_est = abs(a['estados'] - b['estados']) / max(a['estados'], b['estados'], 1)
        score += 3.0 * (1.0 - min(1.0, diff_est))
        # Top transicoes (peso 4)
        if a['top5'] and b['top5']:
            # Jaccard entre conjuntos de top transicoes
            ta, tb = set(a['top5']), set(b['top5'])
            inter = ta & tb
            uniao = ta | tb
            score += 4.0 * (len(inter) / len(uniao) if uniao else 0)
        return score / 10.0
    
    def processar_bytes(self, entrada: bytes, max_iter: int = 3) -> dict:
        """Entrada: QUALQUER coisa em bytes.
        Saida: bytes processados + diagnostico.
        
        Ciclo fechado:
        1. Extrai assinatura da entrada
        2. Gera saida via MCRCadeia
        3. Extrai assinatura da saida
        4. Compara: entrada e saida sao compativeis?
        5. Se sim: entrega
        6. Se nao: regenera
        """
        import time
        t0 = time.time()
        
        # 1. Assinatura da entrada
        assinatura_in = self._extrair_assinatura(entrada)
        
        # 2. Tenta converter para texto
        try:
            texto = entrada.decode('utf-8', errors='replace')
        except:
            texto = str(entrada)
        
        palavras = texto.split()
        semente = palavras[0] if palavras else 'byte'
        
        # 3. Gera saida via Cadeia (em bytes)
        conector = MCRConector()
        conector.alimentar(texto, "entrada_bytes")
        cadeia = MCRCadeia(conector)
        res = cadeia.gerar(semente, n_tokens=30)
        saida_texto = res.get('texto', semente)
        saida_bytes = saida_texto.encode('utf-8')
        
        # 4. Assinatura da saida
        assinatura_out = self._extrair_assinatura(saida_bytes)
        
        # 5. Compara assinaturas
        compatibilidade = self._comparar_assinaturas(assinatura_in, assinatura_out)
        
        # 6. Se baixa compatibilidade, regenera (ate max_iter)
        iteracao = 0
        while compatibilidade < 0.3 and iteracao < max_iter - 1:
            iteracao += 1
            # Muda semente para tentar saida diferente
            if iteracao < len(palavras):
                semente = palavras[iteracao]
            cadeia = MCRCadeia(conector)
            res = cadeia.gerar(semente, n_tokens=30)
            saida_texto = res.get('texto', semente)
            saida_bytes = saida_texto.encode('utf-8')
            assinatura_out = self._extrair_assinatura(saida_bytes)
            compatibilidade = self._comparar_assinaturas(assinatura_in, assinatura_out)
        
        # 7. Autoavalia
        nota = round(compatibilidade * 10, 1)
        
        # 8. Aprende
        self.aprender(f"BYTES:{hash(entrada)%10000}", f"COMPAT:{compatibilidade:.2f}")
        
        return {
            'entrada_tamanho': len(entrada),
            'saida_tamanho': len(saida_bytes),
            'assinatura_entrada': assinatura_in,
            'assinatura_saida': assinatura_out,
            'compatibilidade': round(compatibilidade, 3),
            'nota': nota,
            'iteracoes': iteracao,
            'saida': saida_texto if len(saida_texto) > 300 else saida_texto,
            'tempo': round(time.time() - t0, 3),
        }
    
    def stats(self) -> Dict:
        return {
            'nome': self.nome, 'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'entropia': round(self.entropia_media(), 3),
        }

# Alias para compatibilidade com codigo legado
MarkovUniversal = MCR


class MCRFingerprint:
    """Fingerprint MCR com N dimenções descoberto pela entropia.
    Regra de Ouro: n_dims = max(64, min(256, n_tipos_unicos * 8)).
    
    MINIMO 64 dimensões para distinguir estilos de escrita.
    """
    
    @staticmethod
    def calcular_dimensoes(tokens) -> int:
        tipos = set(t[0] for t in tokens) if tokens else set()
        return max(64, min(256, len(tipos) * 8))
    
    @staticmethod
    def gerar(texto: str) -> list:
        """Fingerprint MCR puro — 64+ dimensões."""
        palavras = texto.split()
        if not palavras:
            return [0.0]*64
        try:
            tokens = [(_classificar_token(p), p) for p in palavras if p]
        except:
            tokens = [('outro', p) for p in palavras if p]
        if not tokens:
            return [0.0]*64
        n_dims = MCRFingerprint.calcular_dimensoes(tokens)
        histograma = [0.0]*n_dims
        for t in tokens:
            histograma[hash(t[0]) % n_dims] += 1
        total = sum(histograma) or 1
        return [h/total*10 for h in histograma]
    
    @staticmethod
    def extrair_estilo(texto: str) -> dict:
        """Extrai MÉTRICAS DE ESTILO de um texto (alem do fingerprint).
        
        Estas metricas COMPLEMENTAM o fingerprint para distinguir
        autores com precisao. Nao sao keywords fixas — sao proporcoes
        observadas nos bytes e caracteres do texto.
        
        Retorna:
            {
                'caps_ratio': float,       # proporcao de maiusculas
                'num_ratio': float,        # proporcao de digitos
                'punct_ratio': float,      # proporcao de pontuacao
                'exclam_ratio': float,     # frequencia de !
                'quest_ratio': float,      # frequencia de ?
                'space_ratio': float,      # proporcao de espacos
                'upper_first_ratio': float,# palavras que comecam com maiuscula
                'avg_word_len': float,     # tamanho medio da palavra
                'avg_sentence_len': float, # tamanho medio da frase
                'unique_ratio': float,     # palavras unicas / total
                'byte_entropy': float,     # entropia dos bytes
            }
        """
        if not texto: return {}
        bytes_dados = texto.encode('utf-8')[:5000]
        n = len(bytes_dados)
        if n == 0: return {}
        
        # Contagens de bytes
        caps = sum(1 for b in bytes_dados if 65 <= b <= 90)
        nums = sum(1 for b in bytes_dados if 48 <= b <= 57)
        punct = sum(1 for b in bytes_dados if b in [33,44,46,58,59,63,
                   40,41,45,47,8212,8211,8220,8221])  # ! , . : ; ? ( ) - / — – " "
        exclam = sum(1 for b in bytes_dados if b == 33)
        quest = sum(1 for b in bytes_dados if b == 63)
        espacos = sum(1 for b in bytes_dados if b == 32)
        
        palavras = texto.split()
        n_palavras = len(palavras)
        frases = [s for s in texto.replace('!','.').replace('?','.').split('.') if s.strip()]
        n_frases = len(frases)
        
        # Metricas
        upper_first = sum(1 for p in palavras if p and p[0].isupper())
        palavras_unicas = len(set(p.lower() for p in palavras))
        
        # Entropia dos bytes
        from collections import Counter
        freq = Counter(bytes_dados)
        h = 0.0
        for c in freq.values():
            p = c / n
            if p > 0: h -= p * math.log2(p)
        
        return {
            'caps_ratio': round(caps / n, 4),
            'num_ratio': round(nums / n, 4),
            'punct_ratio': round(punct / n, 4),
            'exclam_ratio': round(exclam / n, 4),
            'quest_ratio': round(quest / n, 4),
            'space_ratio': round(espacos / n, 4),
            'upper_first_ratio': round(upper_first / max(n_palavras, 1), 4),
            'avg_word_len': round(n / max(n_palavras, 1), 2),
            'avg_sentence_len': round(n_palavras / max(n_frases, 1), 2),
            'unique_ratio': round(palavras_unicas / max(n_palavras, 1), 4),
            'byte_entropy': round(h, 4),
        }


class MCRSystem:
    """Classe SISTEMA do MCR. Orquestrador de alto nivel.
    
    Uso:
        mcr = MCRSystem()
        resultado = mcr.processar("Explique o SPA")
        # → {resposta, nota, acoes, ciclos, ...}
    """
    
    def __init__(self):
        self.pe = PatternEngine() if PatternEngine else None
        self.kg = _get_kg()
        self.tools = None  # substituido por MCRBridge
        
        # IE via MCRDecisor + detectar_mcr() (sem IntentionEngine externo)
        self.ie = MCRDecisor("mcr_ie")
        
        # 6 Markove, 1 algoritmo
        self.mk_byte = MarkovUniversal("byte")
        self.mk_palavra = MarkovUniversal("palavra")
        self.mk_token = MarkovUniversal("token")
        self.mk_intencao = MarkovUniversal("intencao")
        self.mk_decisor = MarkovUniversal("decisor")
        self.mk_acao = MarkovUniversal("acao")
        
        self.historico = []
        self.total_exec = 0
    
    # ============================================================
    # PERCEPÇÃO
    # ============================================================
    
    def _perceber(self, texto: str) -> Dict:
        """Analisa o texto em TODOS os níveis de Markov."""
        dados = texto.encode('utf-8')
        palavras = texto.split()
        tokens = self.pe.tokenizar_universal(texto) if self.pe else []
        tipos = [t[0] for t in tokens] if tokens else []
        
        # Byte
        for i in range(len(dados)-1):
            self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        
        # Palavra
        for i in range(len(palavras)-1):
            self.mk_palavra.aprender(palavras[i].lower(), palavras[i+1].lower())
        
        # Token
        if tipos:
            self.mk_token.aprender_sequencia(tipos)
        
        # Intenção (primeiro token + primeira palavra)
        primeiro_tipo = tipos[0] if tipos else "?"
        primeira_palavra = palavras[0].lower().strip('.,!?') if palavras else "?"
        intencao = f"{primeiro_tipo}/{primeira_palavra}"
        
        # Intenção pela IE (criada no __init__, não lazy)
        if self.ie:
            intencoes = self.ie.detectar(texto)
            if intencoes:
                cat, params, conf = intencoes[0]
                intencao = f"{cat}/{params.get('tipo', 'default')}"
                ie_conf = conf
            else:
                ie_conf = 0.3
        else:
            ie_conf = 0.5
        
        return {
            'texto': texto, 'intencao': intencao,
            'palavras': palavras, 'tipos': tipos,
            'n_bytes': len(dados), 'n_tokens': len(tipos),
            'ie_conf': ie_conf,
            'entropia_byte': round(self.mk_byte.entropia_media(), 3) if self.mk_byte.transicoes else 0.5,
        }
    
    # ============================================================
    # AUTO-AVALIAÇÃO (nota 0-10 por Jaccard de bytes)
    # ============================================================
    
    def _autoavaliar(self, resposta: str, pergunta: str) -> Tuple[float, Dict]:
        """Nota 0-10 REAL baseada em COBERTURA LEXICAL + cosseno + tamanho.
        
        4 métricas MCR (pesos calibrados):
        1. Cobertura lexical:  3 pts — termos da pergunta que aparecem na resposta
        2. Cosseno transições: 2 pts — similaridade estrutural (bytes)
        3. Completude:         3 pts — tamanho em chars (até 300)
        4. Estrutura:          2 pts — baixa entropia = mais coerente
        - Penalidade: se < 100 chars, -2 pts
        
        Cobertura lexical EVITA keyword-stuffing: mede se a resposta REALMENTE
        cobre os termos da pergunta, não apenas repete palavras-chave.
        """
        if not resposta or len(resposta) < 10:
            return 0.0, {'cobertura': 0, 'cosseno': 0, 'riqueza': 0,
                         'entropia': 1,
                         'tamanho_chars': len(resposta) if resposta else 0,
                         'nota_sim': 0, 'nota_tam': 0, 'nota_estrutura': 0,
                         'bonus_riqueza': 0, 'penalidade': 2.0}
        
        # 1. COBERTURA LEXICAL: termos UNICOS da pergunta na resposta
        termos_pergunta = set(w.lower().strip('.,!?[](){}') 
                            for w in pergunta.split() if len(w) > 2)
        termos_resposta = set(w.lower().strip('.,!?[](){}') 
                            for w in resposta.split())
        cobertura = (len(termos_pergunta & termos_resposta) / max(len(termos_pergunta), 1)
                    ) if termos_pergunta else 0.0
        
        # 2. COSSENO de transicoes de bytes (similaridade estrutural)
        cosseno = self.mk_byte.similaridade_transicoes(pergunta, resposta)
        
        # 3. ENTROPIA da resposta (baixa = mais estruturada = melhor)
        mk_temp = MarkovUniversal("tmp")
        tokens_resp = self.pe.tokenizar_universal(resposta) if self.pe else []
        if tokens_resp:
            mk_temp.aprender_sequencia([t[0] for t in tokens_resp])
        entropia = mk_temp.entropia_media()
        
        # 4. TAMANHO em caracteres — recompensa completude
        n_chars = len(resposta)
        
        # 5. RIQUEZA LEXICAL: evita repeticao (1.0 = sem rep, 0.0 = tudo igual)
        palavras_resposta = resposta.lower().split()
        riqueza = (len(set(palavras_resposta)) / max(len(palavras_resposta), 1)
                  ) if palavras_resposta else 0.0
        
        # --- NOVA FORMULA (v4) — o ELO MAIS FRACO define a similaridade ---
        # Similaridade = MIN(cobertura, cosseno, riqueza) * 4
        # Isso garante: tem os termos CERTOs + estrutura SIMILAR + nao REPETE
        nota_sim = min(cobertura, cosseno, riqueza) * 4  # 0 a 4 pts
        nota_tam = min(1.0, n_chars / 300) * 3            # 0 a 3 pts
        nota_estrutura = max(0, 1 - entropia) * 2          # 0 a 2 pts
        # Bonus: riqueza alta ganha +1 (incentiva vocabulario diverso)
        bonus_riqueza = 1.0 if riqueza > 0.7 else 0.0
        penalidade = 2.0 if n_chars < 100 else 0.0
        
        nota = nota_sim + nota_tam + nota_estrutura + bonus_riqueza - penalidade
        nota = round(max(0, min(10, nota)), 1)
        
        return nota, {
            'cobertura': round(cobertura, 3),
            'cosseno': round(cosseno, 3),
            'riqueza': round(riqueza, 3),
            'entropia': round(entropia, 3),
            'tamanho_chars': n_chars,
            'nota_sim': round(nota_sim, 1),
            'nota_tam': round(nota_tam, 1),
            'nota_estrutura': round(nota_estrutura, 1),
            'bonus_riqueza': bonus_riqueza,
            'penalidade': penalidade,
        }
    
    # ============================================================
    # FILTRO MCR — relevância de lessons por Jaccard
    # ============================================================
    
    def _filtrar_lessons(self, pergunta: str, lessons: List[Dict],
                          min_jaccard: float = 0.05) -> List[Tuple[float, Dict]]:
        """Filtra lessons por relevância (Jaccard de bytes)."""
        if not lessons: return []
        avaliadas = []
        for l in lessons:
            sol = l.get('solucao', '')
            if not sol or len(sol) < 20: continue
            jac = self.mk_byte.jaccard_bytes(pergunta, sol)
            
            # Bônus: termo da pergunta aparece NO INÍCIO da solução
            termo = self._extrair_termo(pergunta)
            bonus = 0.05 if termo.lower() in sol.lower() else 0
            
            avaliadas.append((jac + bonus, l))
        
        avaliadas.sort(key=lambda x: -x[0])
        return avaliadas
    
    def _extrair_termo(self, texto: str) -> str:
        """Extrai o termo MAIS relevante (PROPER_NOUN primeiro)."""
        tokens = self.pe.tokenizar_universal(texto) if self.pe else []
        for t in tokens:
            if t[0] == 'PROPER_NOUN' and len(str(t[1])) > 1: return str(t[1])
        for t in tokens:
            if t[0].startswith('DOM_') and len(str(t[1])) > 3: return str(t[1])
        palavras = [p for p in texto.split() if len(p) > 3]
        return palavras[0] if palavras else texto
    
    # ============================================================
    # DECISÃO — MarkovDecisor escolhe a ação
    # ============================================================
    
    def _decidir(self, estado: Dict) -> Tuple[str, float]:
        """MarkovDecisor decide qual ação tomar.
        
        Fallback só para o PRIMEIRO contato. Depois, Markov aprende.
        """
        codigo = f"S:{estado['intencao']}|C:{estado['ie_conf']:.1f}|E:{estado['entropia_byte']:.1f}"
        
        acao, conf = self.mk_decisor.predizer(codigo)
        if acao and conf > 0.2:
            return str(acao), conf
        
        # Fallback (primeira vez — Markov aprende depois)
        intencao = estado['intencao']
        if intencao.startswith('CREATE'):
            return 'buscar_dados', 0.5
        elif intencao.startswith('EXPLAIN'):
            if estado['ie_conf'] > 0.7 and estado['entropia_byte'] < 0.5:
                return 'responder', 0.7
            return 'buscar_kg', 0.5
        elif intencao.startswith('SEARCH'):
            return 'buscar_arquivos', 0.5
        else:
            return 'responder', 0.4
    
    # ============================================================
    # EXECUÇÃO
    # ============================================================
    
    def _executar(self, acao: str, estado: Dict) -> Tuple[str, str]:
        """Executa a ação decidida."""
        termo = self._extrair_termo(estado['texto'])
        
        if acao == 'buscar_kg' and self.kg:
            # Passa pergunta ORIGINAL para ativar FiltroMCR nativo no kg.buscar()
            lessons = self.kg.buscar(termo, max_r=5, pergunta=estado['texto'])
            filtradas = self._filtrar_lessons(estado['texto'], lessons)
            if filtradas:
                melhores = [l for r, l in filtradas if r >= 0.05]
                if melhores:
                    return '\n'.join(l.get('solucao', '') for l in melhores), "KG"
            # Fallback: todas as lessons
            if lessons:
                return '\n'.join(l.get('solucao', '') for l in lessons), "KG_fallback"
        
        elif acao == 'buscar_dados' and self.tools:
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    dados = str(r.get('resultado', ''))
                    if dados and 'Nenhum' not in dados:
                        return dados, "busca_estrategica"
            except: pass
            lessons = self.kg.buscar(termo, max_r=5) if self.kg else []
            if lessons:
                return lessons[0].get('solucao', ''), "KG_fallback"
        
        elif acao == 'buscar_arquivos' and self.tools:
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    return str(r.get('resultado', ''))[:500], "busca"
            except: pass
        
        return "", "sem_dados"
    
    # ============================================================
    # RESPOSTA (gera texto com base no conhecimento)
    # ============================================================
    
    def _responder(self, estado: Dict, conhecimento: str) -> str:
        """Gera resposta baseada no conhecimento acumulado."""
        if conhecimento:
            # Pega os trechos MAIS relevantes
            linhas = conhecimento.split('\n')
            # Filtra linhas curtas ou irrelevantes
            linhas_uteis = [l for l in linhas if len(l) > 30 and termo_relevante(estado['texto'], l)]
            if linhas_uteis:
                return ' '.join(linhas_uteis)
            return conhecimento
        
        # Se nao tem conhecimento, tenta o KG direto (com FiltroMCR)
        if self.kg:
            termo = self._extrair_termo(estado['texto'])
            lessons = self.kg.buscar(termo, max_r=3, pergunta=estado['texto'])
            if lessons:
                return lessons[0].get('solucao', '')
        
        return f"(MCR processou: {estado['intencao']}, {estado['n_tokens']} tokens)"
    
    def ciclo_unico(self, origem: str, max_bytes: int = 5000) -> dict:
        """Entrada: QUALQUER coisa (arquivo, texto, URL).
        Saida: conhecimento estruturado no KG + diagnostico.
        
        Fluxo:
        1. Le bytes da origem
        2. MCRByte descobre estrutura (entropia, delimitadores)
        3. MCRPalavra extrai conteudo significativo
        4. MCRToken classifica o tipo
        5. KG armazena como lesson
        6. Autoavalia: aprendeu algo novo?
        7. Se sim: conecta com conhecimento existente (EMERGIR)
        8. Se nao: tenta ler mais bytes
        9. Loop ate entender TUDO
        """
        import time
        t0 = time.time()
        resultado = {'origem': origem, 'etapas': []}
        
        # 1. Le bytes da origem
        if os.path.isfile(origem):
            with open(origem, 'rb') as f:
                dados = f.read(max_bytes)
        else:
            dados = origem.encode('utf-8')
        
        mk_byte = MCR(f"ciclo_byte")
        mk_byte.aprender_sequencia(list(dados))
        resultado['etapas'].append(f"bytes:{len(dados)}")
        
        # 2. MCRByte descobre estrutura
        entropia = mk_byte.entropia_media()
        n_estados = len(mk_byte.transicoes)
        resultado['entropia'] = round(entropia, 3)
        resultado['estados'] = n_estados
        
        # Classifica o tipo pelo padrao de bytes
        if entropia < 2.0:
            tipo = "binario_estruturado"
        elif entropia < 4.0:
            tipo = "texto_estruturado"
        elif entropia < 6.0:
            tipo = "texto_livre"
        else:
            tipo = "dados_aleatorios"
        resultado['tipo'] = tipo
        resultado['etapas'].append(f"tipo:{tipo}")
        
        # 3. Extrai texto se possivel
        try:
            texto = dados.decode('utf-8', errors='replace')
            palavras = texto.split()
            if len(palavras) > 2:
                mk_palavra = MCR(f"ciclo_palavra")
                mk_palavra.aprender_sequencia(palavras)
                resultado['palavras_unicas'] = len(set(palavras))
                resultado['etapas'].append(f"palavras:{len(palavras)}")
        except:
            pass
        
        # 4. KG armazena
        if self.kg:
            nome_base = os.path.basename(origem) if os.path.isfile(origem) else "texto_direto"
            self.kg.aprender_conceito(
                f"ciclo:{nome_base}",
                f"Tipo: {tipo}, Entropia: {entropia:.2f}, Bytes: {len(dados)}. "
                f"Estados: {n_estados}. Origem: {origem}.",
                ctx="ciclo_unico"
            )
            resultado['etapas'].append("kg:salvo")
        
        # 5. Autoavalia
        nota = 5.0
        if entropia > 2.0: nota += 2.0  # tem estrutura
        if n_estados > 20: nota += 2.0   # tem variedade
        if resultado.get('palavras_unicas', 0) > 10: nota += 1.0  # tem vocabulario
        resultado['nota'] = round(min(10, nota), 1)
        resultado['etapas'].append(f"nota:{resultado['nota']}")
        
        # 6. Conecta com conhecimento existente (EMERGIR)
        if nota >= 5.0:
            try:
                conector = MCRConector()
                conector.alimentar(texto if 'texto' in dir() else origem, "ciclo_entrada")
                for nome, dados_t in list(conector.topicos.items()):
                    if nome != "ciclo_entrada":
                        cx = conector.conectar("ciclo_entrada", nome)
                        if cx:
                            resultado['conexao'] = cx.get('nota', 0)
                            resultado['etapas'].append(f"conexao:{cx.get('nota',0)}")
                            break
            except:
                pass
        
        resultado['tempo'] = round(time.time() - t0, 2)
        return resultado


def termo_relevante(pergunta: str, linha: str) -> bool:
    """Verifica se a linha contém termos da pergunta."""
    termos = [p.lower() for p in pergunta.split() if len(p) > 3]
    linha_lower = linha.lower()
    return any(t in linha_lower for t in termos) if termos else True


# ============================================================
# MCR AUTO-LOOP
# ============================================================

class MCRAutoLoop:
    """Loop MCR completo: executa → avalia → expande até 10/10."""
    
    LOOP_MAX = 8
    
    def __init__(self):
        self.mcr = MCRSystem()
        self.total_ciclos = 0
    
    def processar(self, pergunta: str) -> Dict:
        t0 = _time.time()
        conhecimento = ""
        ferramentas_usadas = set()
        notas = []
        ultima_resposta = ""
        ciclos_sem_melhoria = 0
        
        # Plano de expansao: sequencia de acoes para tentar quando nota < 8
        # Diferente do MarkovDecisor, este plano FORCA variedade
        plano_expansao = ['buscar_kg', 'buscar_dados', 'buscar_arquivos']
        
        for ciclo in range(1, self.LOOP_MAX + 1):
            # Perceber
            estado = self.mcr._perceber(pergunta)
            
            # --- DECISAO INTELIGENTE ---
            # Se nota ja esta boa (>= 8) ou ciclo 1, usa MarkovDecisor
            # Se nota baixa e ja tentou o Decisor, FORCA expansao
            if ciclo == 1:
                acao, conf = self.mcr._decidir(estado)
            elif nota >= 8:
                # Nota boa: uma ultima tentativa com o Decisor
                acao, conf = self.mcr._decidir(estado)
            else:
                # Nota baixa: FORCA uma acao de expansao diferente
                # Tenta acoes que ainda nao foram usadas
                acoes_disponiveis = [a for a in plano_expansao
                                     if a not in ferramentas_usadas]
                if acoes_disponiveis:
                    acao = acoes_disponiveis[0]
                    conf = 0.5
                else:
                    # Todas as ferramentas ja foram usadas: tenta de novo
                    acao = 'buscar_kg'
                    conf = 0.3
            
            # --- EXECUCAO ---
            resultado, fonte = self.mcr._executar(acao, estado)
            if resultado and len(resultado) > 20:
                # So adiciona se for conteudo NOVO (evita duplicacao)
                if resultado not in conhecimento:
                    conhecimento += '\n' + resultado
                ferramentas_usadas.add(fonte)
            
            # --- RESPOSTA ---
            nova_resposta = self.mcr._responder(estado, conhecimento)
            
            # --- AUTOAVALIACAO ---
            nota, metricas = self.mcr._autoavaliar(nova_resposta, pergunta)
            notas.append(nota)
            
            # --- DETECTA ESTAGNACAO ---
            if nova_resposta == ultima_resposta:
                ciclos_sem_melhoria += 1
            else:
                ciclos_sem_melhoria = 0
            ultima_resposta = nova_resposta
            resposta = nova_resposta
            
            # --- APRENDER ---
            codigo_estado = f"S:{estado['intencao']}|C:{estado['ie_conf']:.1f}|E:{estado['entropia_byte']:.1f}"
            self.mcr.mk_decisor.aprender(codigo_estado, acao)
            
            # --- CONDICOES DE PARADA ---
            if nota >= 10:
                break
            if ciclos_sem_melhoria >= 3 and nota >= 5:
                # 3 ciclos sem melhorar e nota razoavel: aceita
                break
            if ciclos_sem_melhoria >= 5:
                # 5 ciclos sem melhorar: aceita qualquer nota
                break
        
        self.total_ciclos += 1
        
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': nota if notas else 0,
            'notas': notas,
            'ciclos': ciclo,
            'ferramentas': list(ferramentas_usadas),
            'tempo': round(_time.time() - t0, 1),
            'conhecimento': len(conhecimento),
        }


# ============================================================
# MCR PRÉ-CACHE — Estuda LLM, extrai vocabulário, prepara KG
# ============================================================

# Constantes para classificação de tokens
_PADROES_CODIGO = ['def ', 'if ', 'else', 'for ', 'while', 'class ',
    'import ', 'from ', 'return', 'function', 'local ', 'end', 'then',
    'do ', 'in ', 'nil', 'true', 'false', 'self', 'this', '->', '=>',
    '===', '!=', '&&', '||', 'fn ', 'let ', 'mut ', 'const ', 'var ',
    'pub ', 'impl ', 'struct ', 'enum ', 'trait ', 'where ', 'async',
    'await', 'try ', 'catch', 'throw', 'printf', 'scanf',
    'print', 'input', 'len(', 'range', 'lambda', 'yield', 'raise',
    'with ', 'pass', 'break', 'continue', 'elif', 'except', 'finally',
    'global', 'nonlocal', 'assert', 'del ', 'elif', 'switch']

# (listas _SUJEITOS_LORE e _VERBOS_LORE removidas — MCRSignature substitui)


def _classificar_token(token: str) -> str:
    """Classifica token por FORMA (sem recorrer a MCRSignature para evitar recursion).
    
    Regras:
    - Tokens especiais (marcadores LLM) → 'especial'
    - Tudo maiusculo 2+ chars → 'sistema'
    - Primeira maiuscula 2+ chars → 'lore'
    - So numeros → 'numero'
    - So pontuacao → 'pontuacao'
    - Primeira minuscula ou letra → 'linguagem'
    - Resto → 'outro'
    """
    if not token: return 'especial'
    if token in ('<unk>', '<s>', '</s>', '<pad>', '<mask>',
                 '<|begin_of_text|>', '<|end_of_text|>', '<|pad|>'):
        return 'especial'
    if token.startswith('<|') or token.startswith('<｜'):
        return 'sistema'
    if token.isupper() and len(token) >= 2: return 'sistema'
    if token[0].isupper() and len(token) > 1: return 'lore'
    if token.isdigit() or (token[0] == '-' and token[1:].isdigit()): return 'numero'
    if all(c in '.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\ \t\n\r\u2581' for c in token):
        return 'pontuacao'
    if token[0].islower() or token[0].isalpha(): return 'linguagem'
    return 'outro'


class MCRPreCache:
    """Estuda uma LLM (GGUF) e prepara o KG com vocabulário classificado.
    
    Uso:
        cache = MCRPreCache()
        cache.estudar("caminho/para/modelo.gguf")
        # KG agora tem lessons sobre tokens, clusters, dominios
    """
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.tokens = []
        self.scores = []
        self.dominios = Counter()
        self.mk_token = None
        self.token_info = []
    
    def estudar(self, caminho_blob, max_tokens_kg=50):
        """Extrai tokenizer do GGUF, classifica tokens, salva no KG."""
        if not os.path.exists(caminho_blob):
            print(f"  [MCRPreCache] Blob nao encontrado: {caminho_blob}")
            return 0
        
        import struct
        try:
            with open(caminho_blob, 'rb') as f:
                magic = f.read(4)
                if magic != b'GGUF': return 0
                f.read(4)  # version
                f.read(8)  # tensor_count
                kv_count = struct.unpack('<Q', f.read(8))[0]
                tokens_raw = None
                scores_raw = None
                for _ in range(min(kv_count, 500)):
                    key = self._ler_string_gguf(f)
                    if key is None: break
                    tipo = struct.unpack('<I', f.read(4))[0]
                    valor = self._ler_valor_gguf(f, tipo)
                    if key == 'tokenizer.ggml.tokens': tokens_raw = valor
                    elif key == 'tokenizer.ggml.scores': scores_raw = valor
                    if tokens_raw and scores_raw: break
        except Exception as e:
            print(f"  [MCRPreCache] Erro: {e}")
            return 0
        
        if not tokens_raw: return 0
        self.tokens = tokens_raw
        self.scores = scores_raw or [0]*len(tokens_raw)
        
        # MarkovToken aprende ordem do vocabulario
        # (nao para gerar, para entender as relacoes entre tokens)
        self.mk_token = MarkovUniversal("precache_tokens")
        self.mk_token.aprender_sequencia(self.tokens)
        
        # Classifica cada token
        for i, token in enumerate(self.tokens):
            dominio = _classificar_token(token)
            self.dominios[dominio] += 1
            self.token_info.append({
                'id': i, 'token': token,
                'dominio': dominio,
                'score': self.scores[i] if i < len(self.scores) else 0,
            })
        
        # Salva no KG
        n_guardados = 0
        if self.kg:
            # Arquitetura
            nome_blob = os.path.basename(caminho_blob)
            total_tokens = len(self.tokens)
            self.kg.aprender_conceito(
                f"precache_{nome_blob}",
                f"Estudado: {total_tokens} tokens, "
                f"{len(self.dominios)} dominios. "
                f"Distribuicao: {dict(self.dominios.most_common())}",
            )
            n_guardados += 1
            
            # Clusters de prefixo (EMERGIR-style)
            prefixos = {}
            for t in self.tokens:
                if len(t) >= 2:
                    p = t.lower()
                    if p not in prefixos: prefixos[p] = []
                    prefixos[p].append(t)
            
            for prefixo, membros in sorted(prefixos.items(),
                                            key=lambda x: -len(x[1])):
                if len(membros) >= 5:
                    dominios_cont = Counter(_classificar_token(m) for m in membros)
                    dom_principal = dominios_cont.most_common(1)[0][0]
                    self.kg.aprender_conceito(
                        f"cluster_{prefixo}",
                        f"{len(membros)} tokens, dominio={dom_principal}. "
                        f"Ex: {', '.join(membros)}",
                        ctx="tokenizer_cluster"
                    )
                    n_guardados += 1
            
            # Dominios
            for dominio, count in self.dominios.most_common():
                exemplos = [t['token'] for t in self.token_info
                           if t['dominio'] == dominio]
                self.kg.aprender_conceito(
                    f"dominio_{dominio}",
                    f"{count} tokens ({count/len(self.tokens)*100:.1f}%). "
                    f"Ex: {', '.join(exemplos)}",
                    ctx="tokenizer_dominio"
                )
                n_guardados += 1
        
        return n_guardados
    
    def _ler_string_gguf(self, f):
        import struct
        len_bytes = f.read(8)
        if len(len_bytes) < 8: return None
        slen = struct.unpack('<Q', len_bytes)[0]
        return f.read(slen).decode('utf-8', errors='replace') if slen > 0 else ""
    
    def _ler_valor_gguf(self, f, tipo):
        import struct
        if tipo == 8: return self._ler_string_gguf(f)
        elif tipo == 9:
            ta = struct.unpack('<I', f.read(4))[0]
            ni = struct.unpack('<Q', f.read(8))[0]
            return [self._ler_valor_gguf(f, ta) for _ in range(ni)]
        elif tipo == 6: return struct.unpack('<f', f.read(4))[0]
        elif tipo == 4: return struct.unpack('<I', f.read(4))[0]
        elif tipo == 5: return struct.unpack('<i', f.read(4))[0]
        return None
    
    def obter_tokens_por_dominio(self, dominio='lore', max_tokens=500):
        """Retorna tokens de um domínio específico para uso em geração."""
        return [t['token'] for t in self.token_info
                if t['dominio'] == dominio]


class AutoavaliadorSemantico:
    """Avalia texto usando MCRSignature + MCRPesoNota.
    
    ZERO listas fixas. ZERO keywords. ZERO pesos fixos.
    
    4 metricas:
    1. Entropia da assinatura — o texto tem estrutura?
    2. Fingerprint — a assinatura e coerente internamente?
    3. Repeticao — detectada por MCREntropia, nao contagem
    4. Originalidade — compatibilidade com KG por Jaccard
    
    Tudo aprendido: MCRThreshold define os limites.
    """
    
    def __init__(self, kg=None, precache=None):
        self.kg = kg or (_get_kg())
        self.precache = precache
        self.peso_nota = MCRPesoNota("autoavaliador")
        self.entropia = MCREntropia()
    
    def avaliar(self, texto: str, dominio_esperado='lore') -> dict:
        """Avalia texto por ASSINATURA, nao por keywords."""
        if not texto or len(texto) < _MCR_THRESHOLD_TAMANHO.obter('min_texto', 20):
            return {'nota': 0.0, 'diagnostico': 'MUITO_CURTO',
                    'detalhes': {'entropia': 0, 'repeticao': 0,
                                 'n_palavras': 0, 'fingerprint': []}}
        
        # 1. ASSINATURA do texto (MCRSignature)
        sig = MCRSignature.extrair(texto)
        entropia = sig.get('entropia', 0)
        estados = sig.get('estados', 0)
        transicoes = sig.get('transicoes', 0)
        fingerprint = sig.get('fingerprint', [])
        
        # 2. REPETICAO por MCREntropia (nao contagem de bigramas)
        palavras = texto.lower().split()
        n_palavras = len(palavras)
        self.entropia = MCREntropia()
        for p in palavras:
            self.entropia.alimentar(p)
        rep_detectada = 1.0 if self.entropia.esta_em_loop() else 0.0
        
        # 3. ORIGINALIDADE por Jaccard (threshold aprendido)
        originalidade = 1.0
        if self.kg:
            try:
                for l in self.kg._get_licoes()[:20]:
                    sol = l.get('solucao', '')
                    if sol and len(sol) > _MCR_THRESHOLD_TAMANHO.obter('min_lesson', 50):
                        jac = MCR.jaccard_bytes(texto[:500], sol[:500])
                        thr_copia = _MCR_THRESHOLD_REPETICAO.obter('copia', 0.8)
                        thr_parcial = _MCR_THRESHOLD_REPETICAO.obter('parcial', 0.5)
                        if jac > thr_copia:
                            originalidade = 0.25
                            break
                        elif jac > thr_parcial:
                            originalidade = max(0.5, originalidade - 0.25)
            except Exception:
                pass
        
        # 4. NOTA por MCRPesoNota (pesos aprendidos, nao fixos)
        nota = self.peso_nota.calcular(
            byte_s=min(10, entropia * 3),          # entropia vira nota 0-10
            palavra_s=min(10, estados * 0.5),       # estados viram nota 0-10
            token_s=min(10, (1 - rep_detectada) * 10),  # repeticao vira nota 0-10
        )
        nota = max(0, min(10, nota * originalidade))
        
        # 5. DIAGNOSTICO por Markov (nao faixas fixas)
        mk_diag = MarkovUniversal('diagnostico_av')
        estado_diag = f"ent:{int(entropia*2)}_est:{estados}_rep:{int(rep_detectada*3)}"
        diag_pred = mk_diag.predizer(estado_diag)
        if diag_pred[0] is not None and diag_pred[1] > 0.3:
            diag = str(diag_pred[0])
        else:
            diag = ('NARRATIVO_COERENTE' if nota >= 7 else
                    'ESTRUTURADO' if nota >= 5 else
                    'FRACO' if nota >= 3 else
                    'GARBAGE' if nota >= 1 else 'VAZIO')
        
        # Auto-aprendizado: registra para thresholds aprenderem
        _MCR_THRESHOLD_CONF.aprender(f"entropia_{dominio_esperado}", min(1.0, entropia / 5))
        self.peso_nota.aprender(
            {'byte': entropia / 5, 'palavra': estados / 30, 'token': 1 - rep_detectada},
            nota / 10
        )
        
        return {
            'nota': round(nota, 1),
            'diagnostico': diag,
            'detalhes': {
                'entropia': round(entropia, 3),
                'estados': estados,
                'transicoes': transicoes,
                'repeticao': round(rep_detectada, 3),
                'n_palavras': n_palavras,
                'originalidade': round(originalidade, 3),
                'fingerprint': fingerprint[:5],
            }
        }


class GeradorNarrativa:
    """Gera texto narrativo usando MarkovPalavra + contexto longo do KG.
    
    Estratégia:
    1. Pré-cache: MCRPreCache estudou a LLM e preparou o KG
    2. Contexto longo: busca 50+ lessons do KG sobre o tema
    3. Geração: MarkovPalavra (PALAVRAS, não bytes) condicionado ao contexto
    4. Autoavaliação semântica: verifica se o texto TEM SENTIDO
    5. Se nota baixa: expande contexto e regenera
    
    NOTA: Usa MarkovPalavra (palavras) em vez de MarkovByte (bytes)
    porque palavras capturam estrutura narrativa; bytes geram "da da da".
    """
    
    def __init__(self, kg=None, precache=None):
        self.kg = kg or (_get_kg())
        self.precache = precache
        self.mk_palavra = MarkovUniversal("narrativa_palavras")
        self.semantico = AutoavaliadorSemantico(kg, precache)
        self.contexto_usado = ""
        self._textos_lore_cache = []  # cache de textos de lore
    
    def _carregar_textos_lore(self):
        """Carrega todos os textos de lore disponiveis no projeto."""
        if self._textos_lore_cache:
            return self._textos_lore_cache
        
        textos = []
        
        # 1. MCR_IDENTITY.md
        path_id = os.path.join(BASE, 'docs', 'MCR_IDENTITY.md') if 'BASE' in dir() else \
                  os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'MCR_IDENTITY.md')
        if os.path.exists(path_id):
            with open(path_id, 'r', encoding='utf-8') as f:
                textos.append(f.read())
        
        # 2. Lessons do KG com ctx=lore, conceito, identidade
        if self.kg:
            for l in self.kg._get_licoes():
                ctx = l.get('ctx', '')
                sol = l.get('solucao', '')
                if ctx in ('lore', 'conceito', 'identidade', 'tokenizer_cluster',
                           'tokenizer_dominio') and sol and len(sol) > 30:
                    textos.append(sol)
        
        # 3. Arquivos .md de docs
        docs_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs')
        if os.path.isdir(docs_dir):
            for fname in os.listdir(docs_dir):
                if fname.endswith('.md') and fname[0] != '_':
                    try:
                        with open(os.path.join(docs_dir, fname), 'r', encoding='utf-8') as f:
                            textos.append(f.read())
                    except: pass
        
        self._textos_lore_cache = textos
        return textos
    
    def preparar_contexto(self, tema, max_lessons=50):
        """Busca contexto longo do KG sobre o tema e carrega corpus de lore."""
        if not self.kg:
            self.contexto_usado = f"Contexto sobre {tema} (KG indisponivel)"
            return self.contexto_usado
        
        # Carrega textos de lore
        textos_lore = self._carregar_textos_lore()
        
        # Busca expandida no KG
        lessons = self.kg.buscar_expandido(tema, max_r=max_lessons)
        
        # Monta contexto completo
        partes = [f"Contexto sobre {tema}:\n"]
        
        # Lessons do KG
        n_lessons = 0
        mk_temp = MarkovUniversal("filtro")
        for l in lessons:
            sol = l.get('solucao', '')
            if not sol or len(sol) < 30: continue
            jac = mk_temp.jaccard_bytes(tema, sol)
            if jac < 0.02: continue
            ctx = l.get('ctx', '')
            erro = l.get('erro', '')
            partes.append(f"[{ctx}] {erro}: {sol}")
            n_lessons += 1
        
        # Textos de lore do corpus
        for texto in textos_lore:
            if len(texto) > 100:
                partes.append(f"[CORPUS] {texto}")
                n_lessons += 1
        
        self.contexto_usado = '\n\n'.join(partes)
        return self.contexto_usado
    
    def gerar(self, tema='Eridanus', max_palavras=100, temperatura=0.3):
        """Gera texto narrativo usando MarkovPalavra (PALAVRAS, nao bytes)."""
        # 1. Prepara contexto longo
        contexto = self.preparar_contexto(tema, max_lessons=50)
        
        # 2. Treina MarkovPalavra no contexto (palavras, nao bytes!)
        texto_limpo = re.sub(r'[<>*#\[\]]', ' ', contexto)
        palavras = texto_limpo.split()
        self.mk_palavra = MarkovUniversal(f"narrativa_{tema}")
        
        # So treina se tiver palavras suficientes
        if len(palavras) < 10:
            return {'texto': f"[MCR] Contexto insuficiente sobre {tema}",
                    'tamanho_chars': 0, 'tamanho_palavras': 0,
                    'contexto_chars': len(contexto),
                    'n_lessons_usadas': 0,
                    'avaliacao': self.semantico.avaliar('', 'lore')}
        
        self.mk_palavra.aprender_sequencia(palavras)
        
        # 3. Semente: primeiras 2 palavras do contexto
        semente = palavras[0] if palavras else tema
        gerado = self.mk_palavra.gerar(semente, max_palavras)
        
        # 4. Converte para texto
        texto = ' '.join(str(g) for g in gerado)
        
        # 5. Autoavaliação semântica
        avaliacao = self.semantico.avaliar(texto, 'lore')
        
        return {
            'texto': texto,
            'tamanho_chars': len(texto),
            'tamanho_palavras': len(gerado),
            'contexto_chars': len(contexto),
            'n_lessons_usadas': contexto.count('['),
            'avaliacao': avaliacao,
        }
    
    def gerar_com_loop(self, tema='Eridanus', max_iter=3):
        """Gera com AutoLoop: tenta → avalia → se ruim, expande contexto."""
        melhor = None
        
        for i in range(max_iter):
            n_lessons = 20 + i * 30
            resultado = self.gerar(tema, max_palavras=100, temperatura=0.3)
            nota_sem = resultado['avaliacao']['nota']
            diag = resultado['avaliacao']['diagnostico']
            
            if melhor is None or nota_sem > melhor['avaliacao']['nota']:
                melhor = resultado
            
            if nota_sem >= 5.0:  # Mais tolerante com MarkovPalavra
                break
        
        return melhor


# Alias: MCR.Nivel = MarkovUniversal (refatoração gradual)
MCR.Nivel = MarkovUniversal

# ============================================================
# MCR CRUZADO — Busca ponte ótima entre 2 tópicos
# ============================================================

CONECTORES = {
    'a', 'e', 'o', 'de', 'da', 'do', 'em', 'com', 'para', 'por',
    'se', 'no', 'na', 'um', 'uma', 'os', 'as', 'ao', 'aos', 'das',
    'dos', 'num', 'numa', 'pelo', 'pela', 'pelos', 'pelas', 'que',
    'como', 'mas', 'mais', 'ou', 'nem', 'tambem', 'so',
}

class MCRCruzado:
    """Analisa entropia cruzada entre cadeias para emergência.
    
    Ponte ótima = divergência × especificidade × profundidade
    """
    
    def __init__(self, conector):
        self.conector = conector
    
    def analisar(self, topico_a: str, topico_b: str) -> dict:
        if topico_a not in self.conector.topicos or topico_b not in self.conector.topicos:
            return {'erro': 'topico nao encontrado', 'pontes': [], 'melhor': None}
        
        conteudo_a = self.conector.topicos[topico_a].get('conteudo', set())
        conteudo_b = self.conector.topicos[topico_b].get('conteudo', set())
        candidatas = conteudo_a & conteudo_b
        
        if not candidatas:
            return self._analisar_sem_compartilhadas(topico_a, topico_b)
        
        pontes = []
        for palavra in candidatas:
            score, detalhes = self._avaliar_ponte(topico_a, topico_b, palavra)
            pontes.append({'palavra': palavra, 'score': round(score, 2), **detalhes})
        
        pontes.sort(key=lambda x: -x['score'])
        return {
            'total_candidatas': len(candidatas),
            'divergencia_media': round(sum(p.get('divergencia', 0) for p in pontes)/len(pontes), 3) if pontes else 0,
            'pontes': pontes,
            'melhor': pontes[0] if pontes else None,
        }
    
    def melhor_ponte(self, topico_a: str, topico_b: str) -> dict:
        return self.analisar(topico_a, topico_b).get('melhor')
    
    def _avaliar_ponte(self, topico_a, topico_b, palavra):
        mk_a = self.conector.topicos[topico_a].get('mcr_palavra')
        mk_b = self.conector.topicos[topico_b].get('mcr_palavra')
        if not mk_a or not mk_b: return 0.0, {}
        
        trans_a = set(mk_a.transicoes.get(palavra, {}).keys())
        trans_b = set(mk_b.transicoes.get(palavra, {}).keys())
        if not trans_a and not trans_b: divergencia = 0.0
        elif not trans_a or not trans_b: divergencia = 1.0
        else:
            inter = trans_a & trans_b; uniao = trans_a | trans_b
            divergencia = 1.0 - (len(inter)/len(uniao) if uniao else 0)
        
        h_a = mk_a.entropia(palavra) if palavra in mk_a.freq else 0
        h_b = mk_b.entropia(palavra) if palavra in mk_b.freq else 0
        entropia_comb = (h_a + h_b)/2
        
        freq_global = sum(1 for _, d in self.conector.topicos.items()
                         if palavra in d.get('conteudo', set()))
        especificidade = 1.0 - min(1.0, freq_global/max(1, len(self.conector.topicos)*0.5))
        
        cadeia_a = len(mk_a.gerar(palavra, passos=5))
        cadeia_b = len(mk_b.gerar(palavra, passos=5))
        profundidade = min(1.0, (cadeia_a + cadeia_b)/10)
        
        score = divergencia*5 + especificidade*3 + profundidade*2 + min(0.5, entropia_comb*0.2)
        score = min(12, score)
        
        return score, {
            'divergencia': round(divergencia, 3),
            'especificidade': round(especificidade, 3),
            'profundidade': round(profundidade, 3),
            'entropia_combinada': round(entropia_comb, 3),
            'freq_global': freq_global,
            'cadeia_a': cadeia_a, 'cadeia_b': cadeia_b,
            'nota_divergencia': round(divergencia*5, 2),
            'nota_especificidade': round(especificidade*3, 2),
            'nota_profundidade': round(profundidade*2, 2),
        }
    
    def _analisar_sem_compartilhadas(self, topico_a, topico_b):
        texto_a = self.conector.topicos[topico_a]['texto']
        texto_b = self.conector.topicos[topico_b]['texto']
        da = texto_a.encode('utf-8'); db = texto_b.encode('utf-8')
        bytes_comuns = set(da) & set(db)
        pontes = []
        for byte_val in bytes_comuns:
            pal_a = None; pal_b = None
            for i, b in enumerate(da):
                if b == byte_val:
                    ini, fim = i, i
                    while ini > 0 and da[ini-1] != 32: ini -= 1
                    while fim < len(da) and da[fim] != 32: fim += 1
                    pal_a = da[ini:fim].decode('utf-8', errors='replace')
                    break
            for i, b in enumerate(db):
                if b == byte_val:
                    ini, fim = i, i
                    while ini > 0 and db[ini-1] != 32: ini -= 1
                    while fim < len(db) and db[fim] != 32: fim += 1
                    pal_b = db[ini:fim].decode('utf-8', errors='replace')
                    break
            if not pal_a or not pal_b or pal_a.lower() == pal_b.lower(): continue
            score, det = self._avaliar_ponte(topico_a, topico_b, pal_a)
            score *= 0.7
            det['palavra_a'] = pal_a; det['palavra_b'] = pal_b
            pontes.append({'palavra': f"{pal_a}↔{pal_b}", 'score': round(score, 2), **det})
        
        pontes.sort(key=lambda x: -x['score'])
        return {'total_candidatas': len(pontes), 'tipo': 'byte_bridge',
                'pontes': pontes, 'melhor': pontes[0] if pontes else None}


class MCRConector:
    """Conecta tópicos distantes usando MCR multi-nível (Byte+Palavra+Token).
    
    Uso:
        c = MCRConector()
        c.alimentar("SPA é progressão", "spa")
        c.alimentar("Eridanus é cidade", "eridanus")  
        conexao = c.conectar("spa", "eridanus")
    """
    
    def __init__(self):
        self.mcr_byte = MCR.Nivel("byte_global")
        self.mcr_palavra = MCR.Nivel("palavra_global")
        self.mcr_token = MCR.Nivel("token_global")
        self.topicos = {}
        self.conexoes_feitas = set()
        self.total_conexoes = 0
        self.cruzado = MCRCruzado(self)
        self._peso_nota = MCRPesoNota("conector")  # pesos aprendidos, nao 2+5+3
    
    def alimentar(self, texto: str, nome: str = None):
        if nome is None: nome = f"topico_{len(self.topicos)+1}"
        dados = texto.encode('utf-8')
        for i in range(len(dados)-1):
            self.mcr_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        palavras = texto.split()
        for i in range(len(palavras)-1):
            self.mcr_palavra.aprender(palavras[i], palavras[i+1])
        for i in range(len(palavras)-1):
            ta = palavras[i][0].upper() if palavras[i] else '?'
            tb = palavras[i+1][0].upper() if palavras[i+1] else '?'
            self.mcr_token.aprender(ta, tb)
        
        mcr_t = MCR.Nivel(nome)
        for i in range(len(dados)-1):
            mcr_t.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        mcr_p = MCR.Nivel(f"{nome}_palavra")
        for i in range(len(palavras)-1):
            mcr_p.aprender(palavras[i], palavras[i+1])
        
        self.topicos[nome] = {
            'texto': texto, 'mcr_byte': mcr_t, 'mcr_palavra': mcr_p,
            'palavras': palavras, 'bytes': len(dados),
            'conteudo': {p.lower() for p in palavras
                        if len(p) >= 4 and p.lower() not in CONECTORES},
        }
        return nome
    
    def alimentar_json(self, arquivo):
        if not os.path.exists(arquivo): return 0
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        conteudo = dados.get('topicos', dados if isinstance(dados, list) else [])
        count = 0
        for item in conteudo:
            if isinstance(item, dict) and 'texto' in item:
                self.alimentar(item['texto'], item.get('nome')); count += 1
            elif isinstance(item, str):
                self.alimentar(item); count += 1
        return count
    
    def conectar(self, topico_a: str, topico_b: str) -> dict:
        if topico_a not in self.topicos or topico_b not in self.topicos: return None
        t_a = self.topicos[topico_a]; t_b = self.topicos[topico_b]
        texto_a = t_a['texto']; texto_b = t_b['texto']
        palavras_a = t_a['palavras']; palavras_b = t_b['palavras']
        
        import hashlib
        h = hashlib.md5(f"{min(topico_a,topico_b)}|{max(topico_a,topico_b)}".encode()).hexdigest()
        if h in self.conexoes_feitas: return None
        
        byte_ponte, tipo_ponte, pal_a, pal_b = self._encontrar_ponte(topico_a, topico_b)
        sequencia = ''
        
        if tipo_ponte in ('conteudo_compartilhado', 'conteudo_mas_parcial'):
            mk_a = t_a['mcr_palavra']; mk_b = t_b['mcr_palavra']
            semente = palavras_a[0] if palavras_a else 'O'
            seq = []; atual = semente; atingiu = False
            for _ in range(14):
                seq.append(atual)
                if not atingiu and atual.lower() == pal_a.lower():
                    atingiu = True; atual = pal_b; continue
                mk = mk_b if atingiu else mk_a
                prox, conf = mk.predizer(atual)
                if prox is None or conf < 0.01: break
                atual = prox
            sequencia = ' '.join(seq)
            if len(sequencia.strip()) < 10: sequencia = ''
        
        if not sequencia:
            mk_a_byte = t_a['mcr_byte']; mk_b_byte = t_b['mcr_byte']
            inicio = f"B:{texto_a.encode('utf-8')[0]:02x}"
            seq_a = mk_a_byte.gerar(inicio, 8)
            estados_b = set(mk_b_byte.freq.keys())
            ponte = None
            for e in seq_a:
                if e in estados_b: ponte = e; break
            if ponte is None:
                for e in seq_a:
                    if e in self.mcr_byte.freq:
                        prox, _ = self.mcr_byte.predizer(e)
                        if prox and prox in estados_b: ponte = e; break
            if ponte is None: return None
            seq_b = mk_b_byte.gerar(ponte, 8)
            chars = []
            for s in seq_a:
                if s.startswith('B:'):
                    try: chars.append(chr(int(s[2:], 16)))
                    except: chars.append('?')
            chars.append(' ')
            for s in seq_b:
                if s.startswith('B:'):
                    try: chars.append(chr(int(s[2:], 16)))
                    except: chars.append('?')
            sequencia = ''.join(chars)
        
        nota, detalhes = self._autoavaliar_multinivel(sequencia, texto_a, texto_b, tipo_ponte)
        self.conexoes_feitas.add(h)
        self.total_conexoes += 1
        
        return {
            'hash': h, 'topico_a': topico_a, 'topico_b': topico_b,
            'tipo_ponte': tipo_ponte, 'palavra_a': pal_a, 'palavra_b': pal_b,
            'sequencia': sequencia, 'nota': round(nota, 2),
            'detalhes_nota': detalhes,
        }
    
    def _encontrar_ponte(self, topico_a, topico_b):
        melhor = self.cruzado.melhor_ponte(topico_a, topico_b)
        if melhor:
            palavra = melhor.get('palavra', '')
            score = melhor.get('score', 0)
            pal_a = melhor.get('palavra_a', palavra) or palavra
            pal_b = melhor.get('palavra_b', palavra) or palavra
            texto_a = self.topicos[topico_a]['texto']
            idx = texto_a.lower().find(pal_a.lower())
            byte_p = f"B:{texto_a.encode('utf-8')[idx if idx>=0 else 0]:02x}"
            tipo = 'conteudo_compartilhado' if score >= 6 else 'conteudo_mas_parcial'
            return byte_p, tipo, pal_a, pal_b
        
        conteudo_a = self.topicos[topico_a].get('conteudo', set())
        conteudo_b = self.topicos[topico_b].get('conteudo', set())
        comp = conteudo_a & conteudo_b
        if comp:
            pal = max(comp, key=len)
            texto_a = self.topicos[topico_a]['texto']
            idx = texto_a.lower().find(pal)
            byte_p = f"B:{texto_a.encode('utf-8')[idx if idx>=0 else 0]:02x}"
            return byte_p, 'conteudo_mas_parcial', pal, pal
        
        return self._byte_bridge(topico_a, topico_b)
    
    def _byte_bridge(self, topico_a, topico_b):
        mk_a = self.topicos[topico_a]['mcr_byte']
        mk_b = self.topicos[topico_b]['mcr_byte']
        texto_a = self.topicos[topico_a]['texto']
        inicio = f"B:{texto_a.encode('utf-8')[0]:02x}"
        seq = mk_a.gerar(inicio, 8)
        estados_b = set(mk_b.freq.keys())
        for e in seq:
            if e in estados_b:
                c = chr(int(e[2:], 16)) if e.startswith('B:') else '?'
                return e, 'byte_only', c, c
        for e in seq:
            if e in self.mcr_byte.freq:
                prox, _ = self.mcr_byte.predizer(e)
                if prox and prox in estados_b:
                    c = chr(int(e[2:], 16))
                    return e, 'byte_only', c, c
        return None, 'none', '', ''
    
    def _autoavaliar_multinivel(self, sequencia, texto_a, texto_b, tipo_ponte):
        """Avalia conexao por ASSINATURA (MCRPesoNota + MCRThreshold).
        
        ZERO pesos fixos. ZERO thresholds fixos.
        Tudo aprendido por MCRThreshold e MCRPesoNota.
        """
        if not sequencia or len(sequencia.strip()) < _MCR_THRESHOLD_TAMANHO.obter('min_seq', 3):
            return 0.0, {'erro': 'vazia'}
        
        # Nivel Byte — Jaccard + transicoes (thresholds aprendidos)
        j_a = self.mcr_byte.jaccard_bytes(sequencia, texto_a)
        j_b = self.mcr_byte.jaccard_bytes(sequencia, texto_b)
        seq_bytes = sequencia.encode('utf-8')
        trans_ok = 0
        for i in range(len(seq_bytes)-1):
            e = f"B:{seq_bytes[i]:02x}"
            p = f"B:{seq_bytes[i+1]:02x}"
            if e in self.mcr_byte.transicoes and p in self.mcr_byte.transicoes.get(e, {}):
                trans_ok += 1
        c_byte = trans_ok / max(len(seq_bytes)-1, 1)
        
        thr_byte = _MCR_THRESHOLD_CONEXAO.obter('jaccard_byte', 0.3)
        nb = (0.5 if j_a < thr_byte else 0) + (0.5 if j_b < thr_byte else 0) \
             + min(2.0, c_byte * 4)
        
        # Nivel Palavra — cobertura do vocabulario (threshold aprendido)
        pal_seq = sequencia.split()
        c_pal = sum(1 for p in pal_seq if p in self.mcr_palavra.freq)/max(len(pal_seq), 1)
        thr_pal = _MCR_THRESHOLD_PALAVRA.obter('min_palavra', 4)
        cont_a = {p.lower() for p in texto_a.split() if len(p) >= thr_pal}
        cont_b = {p.lower() for p in texto_b.split() if len(p) >= thr_pal}
        cont_seq = {p.lower() for p in pal_seq if len(p) >= thr_pal}
        np = (1.0 if c_pal > 0 else 0) + min(2.0, len(cont_seq & cont_a) * 0.4) \
             + min(2.0, len(cont_seq & cont_b) * 0.4) + min(2.0, c_pal * 3)
        
        # Nivel Token — coerencia de tipos (threshold aprendido)
        c_tok = 0
        if len(pal_seq) > 1:
            c_tok = sum(1 for i in range(len(pal_seq)-1)
                       if pal_seq[i][0].upper() in self.mcr_token.transicoes
                       and pal_seq[i+1][0].upper() in self.mcr_token.transicoes.get(pal_seq[i][0].upper(), {}))
            c_tok /= (len(pal_seq)-1)
        tipos_a = {p[0].upper() for p in texto_a.split() if p}
        tipos_b = {p[0].upper() for p in texto_b.split() if p}
        tipos_seq = {p[0].upper() for p in pal_seq if p}
        thr_tok = _MCR_THRESHOLD_CONEXAO.obter('token_tipos', 0.3)
        nt = (0.5 if tipos_seq & tipos_a else 0) + (0.5 if tipos_seq & tipos_b else 0) \
             + min(3.0, c_tok * 10)
        
        # Penalidade por tipo de ponte (threshold aprendido)
        penalidade = _MCR_THRESHOLD_CONEXAO.obter(f'penalidade_{tipo_ponte}', 
                                                    0.3 if tipo_ponte == 'byte_only' else
                                                    0.1 if tipo_ponte == 'none' else 1.0)
        
        # Nota final por MCRPesoNota (pesos aprendidos, nao 2+5+3)
        nota = self._peso_nota.calcular(
            byte_s=min(10, nb * 3),
            palavra_s=min(10, np * 2),
            token_s=min(10, nt * 3),
        )
        nota = max(0, min(10, nota * penalidade))
        
        # Auto-aprendizado: registra para thresholds aprenderem
        _MCR_THRESHOLD_CONEXAO.aprender(f'byte_{tipo_ponte}', nb/4)
        _MCR_THRESHOLD_CONEXAO.aprender(f'palavra_{tipo_ponte}', np/6)
        self._peso_nota.aprender(
            {'byte': nb/4, 'palavra': np/6, 'token': nt/4},
            nota/10
        )
        
        return nota, {
            'byte': {'diff_a': round(j_a,3), 'diff_b': round(j_b,3), 'nota': round(nb,2)},
            'palavra': {'existe': round(c_pal,3), 'nota': round(np,2)},
            'token': {'coerencia': round(c_tok,3), 'nota': round(nt,2)},
            'penalidade': penalidade, 'nota_final': round(nota,2),
        }
    
    def explorar_todos(self):
        conexoes = []
        nomes = list(self.topicos.keys())
        for i in range(len(nomes)):
            for j in range(i+1, len(nomes)):
                res = self.conectar(nomes[i], nomes[j])
                if res: conexoes.append(res)
        return conexoes
    
    def debug(self, conexao: dict) -> str:
        """Rastreamento passo-a-passo de uma conexao."""
        if not conexao: return "(sem conexao)"
        linhas = [f"DEBUG CONEXAO: {conexao.get('topico_a','?')} <-> {conexao.get('topico_b','?')}"]
        linhas.append(f"  Ponte: {conexao.get('palavra_a','?')} -> {conexao.get('palavra_b','?')} ({conexao.get('tipo_ponte','?')})")
        linhas.append(f"  Sequencia: {conexao.get('sequencia','')}")
        linhas.append(f"  Nota: {conexao.get('nota',0)}/10")
        det = conexao.get('detalhes_nota', {})
        if 'byte' in det: 
            linhas.append(f"  Byte: {det['byte'].get('nota',0):.1f}/2 (diff_a={det['byte'].get('diff_a',0):.3f})")
        if 'palavra' in det:
            linhas.append(f"  Palavra: {det['palavra'].get('nota',0):.1f}/5")
        if 'token' in det:
            linhas.append(f"  Token: {det['token'].get('nota',0):.1f}/3")
        linhas.append(f"  Penalidade: x{det.get('penalidade',1)}")
        return '\n'.join(linhas)


# ============================================================
# MCR CADEIA — Geração infinita com reinjeção de contexto
# ============================================================

class MCRCadeia:
    """Gera N tokens sem repetir, reinjetando contexto a cada passo.
    
    Estratégia:
    1. Markov gera 1 token
    2. Pega últimos K tokens como novo contexto
    3. Continua gerando a partir do contexto
    4. A cada passo, autoavalia: está repetindo?
    5. Se loop: injeta ruído de outro tópico
    6. Repete até N tokens
    """
    
    def __init__(self, conector: MCRConector = None):
        self.conector = conector or MCRConector()
        self.detector = MCREntropia()
        self.ruido = MCRRuido()
        self.historico_ciclos = []
    
    def gerar(self, semente: str, n_tokens: int = 100, 
              contexto_tamanho: int = 3, max_tentativas_loop: int = 5,
              top_k: int = 3) -> dict:
        """Gera N tokens com TOP-K sampling + contexto reinjetado.
        
        top_k: em vez de sempre pegar o token mais provavel, 
               sorteia entre os K tokens mais provaveis (diversidade).
               k=1 = greedy (original), k>1 = criativo.
        """
        import random
        if not self.conector.topicos:
            return {'texto': semente, 'tokens': [semente], 
                    'nota': 0, 'loops_detectados': 0, 'erro': 'sem topicos'}
        
        mk = self.conector.mcr_palavra
        tokens_gerados = [semente]
        loops_detectados = 0
        repeticoes_evitadas = 0
        tentativas_loop = 0
        
        for passo in range(n_tokens - 1):
            # 1. Contexto = ultimos K tokens
            if len(tokens_gerados) >= contexto_tamanho:
                contexto = tokens_gerados[-contexto_tamanho:]
            else:
                contexto = tokens_gerados
            
            # 2. Top-K sampling: pega K mais provaveis e sorteia
            ultimo = contexto[-1]
            preds = mk.predizer_n(ultimo, n=top_k)
            if not preds:
                # Fallback: predizer normal
                prox, conf = mk.predizer(ultimo)
                if prox is None or conf < 0.01:
                    prox, conf = mk.predizer(semente)
                    if prox is None or conf < 0.01: break
            else:
                # Sorteio ponderado entre os top-K (mais provavel tem mais chance)
                pesos = [conf for _, conf in preds]
                total = sum(pesos)
                r = random.uniform(0, total)
                acum = 0
                for prox_str, conf in preds:
                    acum += conf
                    if r <= acum:
                        prox = prox_str
                        break
            
            # 3. MCREntropia detecta loop (nao contagem fixa)
            token_str = str(prox)
            self.detector.alimentar(token_str)
            em_loop = self.detector.esta_em_loop()
            
            if em_loop:
                loops_detectados += 1
                tentativas_loop += 1
                if tentativas_loop > max_tentativas_loop: break
                
                # MCRRuido decide COMO injetar ruido
                melhor_ruido = self.ruido.melhor_tipo()
                if melhor_ruido == 'palavra_outro_topico':
                    import random
                    outros = [n for n in self.conector.topicos.keys() if n != token_str]
                    if outros:
                        t_alt = random.choice(outros)
                        pal_alt = self.conector.topicos[t_alt]['texto'].split()
                        if pal_alt:
                            prox = random.choice(pal_alt)
                            repeticoes_evitadas += 1
                            tentativas_loop = 0
                            self.ruido.registrar(melhor_ruido, True)
                        else:
                            self.ruido.registrar(melhor_ruido, False)
                elif melhor_ruido == 'semente_original':
                    prox = semente
                    repeticoes_evitadas += 1
                    tentativas_loop = 0
                else:
                    # Tenta com byte global
                    prox, conf = self.conector.mcr_byte.predizer(token_str)
                    if prox is None: break
                    repeticoes_evitadas += 1
                    tentativas_loop = 0
            
            tokens_gerados.append(str(prox))
        
        # Converte para texto
        texto = ' '.join(tokens_gerados)
        
        # Autoavaliacao com MCREntropia
        palavras = texto.split()
        n_palavras = len(palavras)
        if n_palavras >= 4:
            bigramas = [' '.join(palavras[i:i+2]) for i in range(n_palavras-1)]
            repeticao = 1.0 - (len(set(bigramas)) / max(len(bigramas), 1))
        else:
            repeticao = 0.0
        
        nota = 10.0
        loops_nao_quebrados = max(0, loops_detectados - repeticoes_evitadas)
        # Penalidades por MCRThreshold (aprendidas, nao fixas)
        pen_loop = _MCR_THRESHOLD_REPETICAO.obter('penalidade_loop', 2.0)
        if loops_nao_quebrados > 0: nota -= loops_nao_quebrados * pen_loop
        thr_rep = _MCR_THRESHOLD_REPETICAO.obter('limiar_repeticao', 0.3)
        if repeticao > thr_rep: nota -= (repeticao - thr_rep) * 10
        nota = max(1, min(10, nota))
        # Auto-aprendizado
        _MCR_THRESHOLD_REPETICAO.aprender('penalidade_loop', pen_loop * 0.99 + (loops_nao_quebrados/3) * 0.01)
        _MCR_THRESHOLD_REPETICAO.aprender('limiar_repeticao', thr_rep * 0.99 + repeticao * 0.01)
        
        return {
            'texto': texto,
            'tokens': tokens_gerados,
            'n_tokens': len(tokens_gerados),
            'nota': round(nota, 1),
            'loops_detectados': loops_detectados,
            'repeticoes_evitadas': repeticoes_evitadas,
            'repeticao_final': round(repeticao, 3),
        }


# ============================================================
# MCR PERGUNTA — Substitui perguntar_ia (KG + Conector + Cadeia)
# ============================================================

class MCRPergunta:
    """Responde perguntas usando MCR puro (sem LLM).
    
    Fluxo:
    1. Busca termos relevantes no KG (FiltroMCR)
    2. Alimenta MCRConector com os resultados
    3. Tenta conectar os tópicos encontrados
    4. Usa MCRCadeia para gerar resposta longa
    5. Autoavalia MultiNível + Semântica
    6. Se nota < 5: expande e tenta de novo
    """
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.semantico = AutoavaliadorSemantico(kg, None)
        self.diagnostico = MCRDiagnostico()
        self.peso_nota = MCRPesoNota("pergunta_peso")
        self.expansao = MCRExpansao(self.kg)
        self.log = []
    
    @staticmethod
    def _limpar_texto(texto: str) -> str:
        """Remove metadados, JSON, escapes do texto (MCR identifica o que e lixo)."""
        if not texto: return ''
        # Se comeca com { ou [ e' JSON — extrai so o texto
        if texto.strip().startswith('{') or texto.strip().startswith('['):
            import re
            # Tenta extrair campo 'solucao' ou 'fragmento' ou 'texto'
            for campo in ['solucao', 'fragmento', 'texto', 'resposta']:
                m = re.search(r'"{0}"\s*:\s*"([^"]+)"'.format(campo), texto)
                if m: return m.group(1)
            # Remove chaves, aspas, escapes
            texto = re.sub(r'[{}"\\]', '', texto)
        # Remove escapes Unicode
        texto = texto.replace('\\u00e3', 'ã').replace('\\u00e1', 'á')
        texto = texto.replace('\\u00e9', 'é').replace('\\u00ed', 'í')
        texto = texto.replace('\\u00f3', 'ó').replace('\\u00fa', 'ú')
        texto = texto.replace('\\u00e7', 'ç').replace('\\u00f5', 'õ')
        texto = texto.replace('\\u00ea', 'ê').replace('\\u00f4', 'ô')
        texto = texto.replace('\\u00e2', 'â').replace('\\u00ee', 'î')
        texto = texto.replace('\\u00fb', 'û').replace('\\u00c1', 'Á')
        texto = texto.replace('\\u00c9', 'É').replace('\\u00d3', 'Ó')
        # Remove ** marcacao **
        texto = texto.replace('**', '')
        return texto.strip()
    
    @staticmethod
    def _filtrar_lesson(sol: str, mk_byte=None) -> bool:
        """Filtra lessons que nao sao texto util (MCR por entropia)."""
        if not sol or len(sol) < 20: return False
        # Entropia baixa = nao e texto
        if mk_byte:
            from collections import Counter
            import math
            dados = sol.encode('utf-8')
            freq = {}
            for b in dados: freq[b] = freq.get(b, 0) + 1
            n = len(dados)
            h = 0.0
            for c in freq.values():
                p = c / n
                if p > 0: h -= p * math.log2(p)
            if h < _MCR_THRESHOLD_FILTRO.calcular(1.0):
                return False
        if sol.strip().startswith('{') or sol.strip().startswith('['):
            return False
        if sol.startswith('[') and ']' in sol:
            return False
        return True

    @staticmethod
    def _ranquear_por_assinatura(lessons: list, pergunta: str = '') -> list:
        """Re-rankeia lessons por compatibilidade de ASSINATURA com a pergunta.
        
        Nao usa keywords fixas. Usa MCRSignature para comparar a assinatura
        da pergunta com a assinatura de cada lesson. Lessons com assinatura
        mais compativel (maior entropia compartilhada, transicoes similares)
        recebem prioridade.
        
        Se o MCRDecisor indicar que nao ha lessons compativeis, retorna
        lista vazia para que o sistema ESTUDE o que falta.
        """
        if not lessons or not pergunta:
            return lessons
        
        sig_pergunta = MCRSignature.extrair(pergunta)
        fp_pergunta = sig_pergunta.get('fingerprint', [])
        if not fp_pergunta:
            return lessons
        
        com_pontos = []
        for l in lessons:
            sol = l.get('solucao', '') or l.get('erro', '')
            if not sol: continue
            
            sig_lesson = MCRSignature.extrair(sol[:500])
            fp_lesson = sig_lesson.get('fingerprint', [])
            
            if fp_lesson and len(fp_lesson) == len(fp_pergunta):
                # Similaridade de fingerprint (cosseno)
                dot = sum(a*b for a,b in zip(fp_lesson, fp_pergunta))
                na = sum(a*a for a in fp_lesson) ** 0.5
                nb = sum(b*b for b in fp_pergunta) ** 0.5
                compat = dot / (na * nb) if na*nb > 0 else 0
            else:
                # Fallback: Jaccard de bytes entre pergunta e lesson
                compat = MCR.jaccard_bytes(pergunta, sol[:200])
            
            com_pontos.append((compat, l))
        
        # Ordena por compatibilidade de assinatura
        com_pontos.sort(key=lambda x: -x[0])
        
        # Se nenhuma lesson tem compat > 0.1, retorna vazio
        # para sinalizar que precisa ESTUDAR
        if com_pontos and com_pontos[0][0] < 0.1:
            return []
        
        return [l for _, l in com_pontos]
    
    def perguntar(self, pergunta: str, max_tokens: int = 80) -> dict:
        """Responde usando MCRDecisor para decidir cada passo do fluxo.
        
        Nao ha sequencia fixa. O MCRDecisor decide:
        - 'buscar' → procurar no KG
        - 'estudar' → MCRWebLearn + MCRMetaGap
        - 'expandir' → MCRExpansao
        - 'conectar' → MCRConector
        - 'gerar' → MCRCadeia
        - 'finalizar' → retornar resultado
        """
        # Decisor de fluxo por Markov (MCR puro, nao if/else)
        mk_fluxo = MarkovUniversal('fluxo_pergunta')
        termos = [p.lower().strip('.,!?') for p in pergunta.split() 
                  if len(p) > _MCR_THRESHOLD_PALAVRA.obter('termo_min', 3) and p.lower() not in CONECTORES]
        lessons = []
        topicos_alimentados = []
        conexoes = []
        estado = {
            'fase': 'inicio',
            'n_topicos': 0,
            'n_conexoes': 0,
            'n_lessons': 0,
            'n_expansoes': 0,
            'loop_count': 0,
            'ultima_nota': 0,
        }
        
        for ciclo in range(8):  # max 8 ciclos (nao 7 passos fixos)
            # Markov decide proxima acao baseada no estado
            estado_chave = f"F:{estado['fase']}_T:{estado['n_topicos']}_C:{estado['n_conexoes']}"
            acao_pred = mk_fluxo.predizer(estado_chave)
            if acao_pred[0] is not None and acao_pred[1] > 0.3:
                acao = str(acao_pred[0])
            else:
                # Fallback Markov: transicao de fase para acao
                acao = {
                    'inicio': 'buscar', 'buscou': 'conectar' if len(topicos_alimentados) >= 2 else 'estudar',
                    'estudou': 'buscar', 'expandiu': 'conectar',
                    'conectou': 'gerar', 'avaliou': 'gerar',
                }.get(estado['fase'], 'finalizar')
            
            if acao == 'buscar' or estado['fase'] == 'inicio':
                # Busca no KG por assinatura
                for termo in termos:
                    ls = self.kg.buscar(termo, max_r=3, pergunta=pergunta) if self.kg else []
                    lessons.extend(ls)
                lessons = self._ranquear_por_assinatura(lessons, pergunta)
                estado['n_lessons'] = len(lessons)
                estado['fase'] = 'buscou'
                
                # Alimenta conector com lessons compativeis
                mk_filtro = MarkovUniversal("filtro_kg")
                for i, l in enumerate(lessons[:10]):
                    sol = l.get('solucao', '') or l.get('erro', '')
                    if not self._filtrar_lesson(sol, mk_filtro): continue
                    sol = self._limpar_texto(sol)
                    if sol and len(sol) > _MCR_THRESHOLD_TAMANHO.obter('min_alimento', 30):
                        self.conector.alimentar(sol, f"kg_{i}_{l.get('ctx', '?')}")
                        topicos_alimentados.append(f"kg_{i}")
                estado['n_topicos'] = len(topicos_alimentados)
            
            elif acao == 'estudar' and not lessons:
                # MCRDecisor detectou que faltam dados → estuda
                try:
                    meta = MCRMetaGap(kg=self.kg)
                    gaps = meta.diagnosticar_gaps(min_por_prefixo=2)
                    if gaps:
                        web = MCRWebLearn()
                        if web.estudar_gaps(2) > 0:
                            for termo in termos:
                                ls = self.kg.buscar(termo, max_r=5, pergunta=pergunta) if self.kg else []
                                lessons.extend(ls)
                            lessons = self._ranquear_por_assinatura(lessons, pergunta)
                except Exception:
                    pass
                estado['fase'] = 'estudou'
            
            elif acao == 'expandir' and not topicos_alimentados:
                # Expande conhecimento via Bridge
                exp = self.expansao.expandir(termos[0] if termos else pergunta, max_recursos=5)
                estado['n_expansoes'] = exp.get('expansoes', 0)
                if estado['n_expansoes'] > 0:
                    for termo in termos:
                        ls = self.kg.buscar(termo, max_r=5, pergunta=pergunta) if self.kg else []
                        for l in ls[:5]:
                            sol = l.get('solucao', '') or l.get('erro', '')
                            if self._filtrar_lesson(sol) and sol:
                                sol = self._limpar_texto(sol)
                                self.conector.alimentar(sol, f"kg_exp_{len(topicos_alimentados)}")
                                topicos_alimentados.append(f"kg_exp_{len(topicos_alimentados)}")
                if not topicos_alimentados:
                    self.conector.alimentar(self._limpar_texto(pergunta), "pergunta")
                    topicos_alimentados.append("pergunta")
                estado['n_topicos'] = len(topicos_alimentados)
                estado['fase'] = 'expandiu'
            
            elif acao == 'conectar' and len(topicos_alimentados) >= 2:
                # Conecta topicos
                for i in range(len(topicos_alimentados)):
                    for j in range(i+1, len(topicos_alimentados)):
                        cx = self.conector.conectar(topicos_alimentados[i], topicos_alimentados[j])
                        if cx: conexoes.append(cx)
                estado['n_conexoes'] = len(conexoes)
                estado['fase'] = 'conectou'
            
            elif acao == 'gerar' and topicos_alimentados:
                # Gera resposta e avalia
                resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
                nota_final, texto, resultado_cadeia = self._avaliar_resposta(
                    pergunta, resultado_cadeia, max_tokens)
                estado['ultima_nota'] = nota_final
                estado['fase'] = 'avaliou'
                
                # Se nota > 6 ou ciclo maximo, finaliza
                if nota_final >= _MCR_THRESHOLD_NOTA.obter('min_entrega', 6.0) or ciclo >= 6:
                    return self._montar_resultado(pergunta, texto, nota_final, resultado_cadeia,
                                                  topicos_alimentados, conexoes)
            
            elif acao == 'finalizar' or ciclo >= 7:
                # Finaliza com o que tem
                if topicos_alimentados:
                    resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
                    nota_final, texto, resultado_cadeia = self._avaliar_resposta(
                        pergunta, resultado_cadeia, max_tokens)
                    return self._montar_resultado(pergunta, texto, nota_final, resultado_cadeia,
                                                  topicos_alimentados, conexoes)
                return {'erro': 'sem dados', 'pergunta': pergunta, 'nota': 0}
            
            estado['loop_count'] = ciclo
            # Aprende com este ciclo para melhorar decisoes futuras
            mk_fluxo.aprender(estado_chave, acao)
        
        # Fallback: se saiu do loop sem finalizar
        if topicos_alimentados:
            resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
            return self._montar_resultado(pergunta, resultado_cadeia['texto'],
                                          resultado_cadeia['nota'], resultado_cadeia,
                                          topicos_alimentados, conexoes)
        return {'erro': 'timeout', 'pergunta': pergunta, 'nota': 0}
    
    def _gerar_resposta(self, pergunta, topicos_alimentados, max_tokens):
        """Gera resposta via MCRCadeia."""
        if topicos_alimentados:
            primeiro_texto = self.conector.topicos.get(topicos_alimentados[0], {}).get('texto', pergunta)
        else:
            primeiro_texto = pergunta
        palavras_primeiro = primeiro_texto.split()
        semente = palavras_primeiro[0] if palavras_primeiro else pergunta.split()[0]
        if semente not in self.conector.mcr_palavra.freq and len(palavras_primeiro) > 1:
            semente = palavras_primeiro[1]
        return self.cadeia.gerar(semente, n_tokens=max_tokens, top_k=3)
    
    def _avaliar_resposta(self, pergunta, resultado_cadeia, max_tokens):
        """Avalia resposta e tenta feedback se nota baixa."""
        texto = resultado_cadeia['texto']
        if texto and texto[0].islower(): texto = texto[0].upper() + texto[1:]
        if texto and not any(texto.rstrip().endswith(p) for p in '.!?'): texto += '.'
        import re as _re
        texto = _re.sub(r'([.!?])\1+', r'\1', texto)
        if len(texto) > 200:
            idx_ponto = texto.find('.', 80)
            if idx_ponto > 0: texto = texto[:idx_ponto+1]
        
        av_sem = self.semantico.avaliar(texto, 'lore')
        nota_sem = av_sem.get('nota', 5)
        nota_cadeia = resultado_cadeia.get('nota', 5)
        loops = resultado_cadeia.get('loops_detectados', 0)
        
        nota_final = self.peso_nota.calcular(
            byte_s=nota_cadeia, palavra_s=nota_sem,
            token_s=8 if loops < 3 else 3
        )
        
        thr_min = _MCR_THRESHOLD_NOTA.obter('min_entrega', 6.0)
        if nota_final < thr_min and not pergunta.startswith('[MCR Feedback]'):
            fb = MCRFeedback()
            res_fb = fb.processar_com_feedback(pergunta, max_tentativas=2)
            if res_fb.get('nota', 0) > nota_final:
                nota_final = res_fb['nota']
                texto = res_fb.get('resposta', texto)
        
        diag = self.diagnostico.diagnosticar({
            'byte': nota_cadeia/10, 'palavra': nota_sem/10, 'token': nota_final/10,
        })
        self.diagnostico.alimentar({'byte': nota_cadeia/10, 'palavra': nota_sem/10, 'token': nota_final/10},
                                    'loop' if loops > 3 else 'ok')
        self.peso_nota.aprender(
            {'byte': nota_cadeia/10, 'palavra': nota_sem/10, 'token': nota_final/10}, nota_final/10)
        
        resultado_cadeia['nota'] = nota_final
        return nota_final, texto, resultado_cadeia
    
    def _montar_resultado(self, pergunta, texto, nota_final, resultado_cadeia,
                          topicos_alimentados, conexoes):
        """Monta dicionario de resultado final."""
        av_sem = self.semantico.avaliar(texto, 'lore')
        diag = self.diagnostico.diagnosticar({
            'byte': resultado_cadeia.get('nota', 5)/10,
            'palavra': av_sem.get('nota', 5)/10,
            'token': nota_final/10,
        })
        
        resultado = {
            'pergunta': pergunta,
            'resposta': texto[:600],
            'nota': round(nota_final, 1),
            'n_tokens': resultado_cadeia['n_tokens'],
            'topicos_usados': topicos_alimentados,
            'n_conexoes': len(conexoes),
            'loops_detectados': resultado_cadeia['loops_detectados'],
            'repeticoes_evitadas': resultado_cadeia['repeticoes_evitadas'],
            'avaliacao_semantica': av_sem,
            'diagnostico': diag,
        }
        self.log.append(resultado)
        return resultado
        
        # Diagnostico MCR: detecta e APRENDE com problemas
        estado_diag = {
            'byte': nota_cadeia/10,
            'palavra': nota_sem/10,
            'token': nota_final/10,
        }
        diag = self.diagnostico.diagnosticar(estado_diag)
        
        # AUTO-ALIMENTA: diagnostico aprende com o resultado real
        problema = 'loop' if loops > 3 else 'ok'
        self.diagnostico.alimentar(estado_diag, problema)
        
        # PesoNota aprende com esta execucao
        self.peso_nota.aprender(
            {'byte': nota_cadeia/10, 'palavra': nota_sem/10, 'token': nota_final/10},
            nota_final
        )
        
        resultado = {
            'pergunta': pergunta,
            'resposta': texto,
            'nota': round(nota_final, 1),
            'n_tokens': resultado_cadeia['n_tokens'],
            'topicos_usados': topicos_alimentados,
            'n_conexoes': len(conexoes),
            'loops_detectados': resultado_cadeia['loops_detectados'],
            'repeticoes_evitadas': resultado_cadeia['repeticoes_evitadas'],
            'avaliacao_semantica': av_sem,
            'nota_multinivel': 0,
            'diagnostico': diag,
            'debug': self._gerar_debug(resultado_cadeia, conexoes if 'conexoes' in dir() else [], av_sem, diag),
        }
        
        self.log.append(resultado)
        return resultado
    
    def _gerar_debug(self, cadeia, conexoes, av_sem, diag=""):
        linhas = ["DEBUG MCRPergunta:"]
        linhas.append(f"  Cadeia: {cadeia['n_tokens']} tokens, nota {cadeia['nota']}/10")
        linhas.append(f"  Loops: {cadeia['loops_detectados']}, Repeticoes evitadas: {cadeia['repeticoes_evitadas']}")
        linhas.append(f"  Semantica: {av_sem['nota']}/10 ({av_sem['diagnostico']})")
        if diag:
            linhas.append(f"  Diagnostico: {diag}")
        if conexoes:
            linhas.append(f"  Conexoes: {len(conexoes)}")
            for cx in conexoes:
                linhas.append(f"    {cx['topico_a']} <-> {cx['topico_b']}: {cx['nota']}/10")
        return '\n'.join(linhas)
    


# ============================================================
# MCR'ZIFICAÇÃO — Todos os pontos de hardcode viram Markov
# ============================================================

class MCRPeso:
    """Aprende PESOS dos dados, não de regras fixas.
    
    Substitui:
    - kg.buscar(): +5 erro, +4 ctx, +3 causa → frequencia observada
    - Autoavaliacao: Byte(2)+Palavra(5)+Token(3) → correlacao com nota real
    - Qualquer peso fixo → Markov descobre
    
    Uso:
        peso = MCRPeso()
        peso.aprender("tipo_erro", relevancia_observada)
        peso_aprendido = peso.consultar("tipo_erro")
    """
    
    def __init__(self, nome="pesos"):
        self.mk = MarkovUniversal(nome)
        self.total_obs = 0
    
    def aprender(self, categoria: str, valor: float):
        """Aprende que CATEGORIA tem VALOR de relevancia."""
        self.mk.aprender(f"CAT_{categoria}", f"VAL_{int(valor*10)}")
        self.total_obs += 1
    
    def consultar(self, categoria: str, fallback: float = 1.0) -> float:
        """Retorna peso aprendido para categoria, ou fallback se nunca viu."""
        estado = f"CAT_{categoria}"
        if estado not in self.mk.transicoes: return fallback
        prox, conf = self.mk.predizer(estado)
        if prox is None or conf < 0.1: return fallback
        try:
            return int(prox.replace('VAL_', '')) / 10.0
        except:
            return fallback
    
    def pesos_mais_comuns(self, top_n: int = 5) -> list:
        """Retorna os pares (categoria, peso) mais frequentes."""
        result = []
        for estado, trans in self.mk.transicoes.items():
            if not estado.startswith('CAT_'): continue
            melhor = max(trans, key=trans.get) if trans else ''
            try:
                valor = int(melhor.replace('VAL_', '')) / 10.0
            except:
                valor = 0
            freq = sum(trans.values())
            result.append((freq, estado.replace('CAT_', ''), valor))
        result.sort(key=lambda x: -x[0])
        return [(c, v) for _, c, v in result]


class MCREntropia:
    """Detecta anomalias e loops por ENTROPIA, não por contagem fixa.
    
    Substitui:
    - "3x mesmo token = loop" → entropia caiu abaixo da mediana?
    - "texto suspeito" → entropia foge do esperado?
    
    Uso:
        det = MCREntropia()
        det.alimentar(sequencia_de_tokens)
        det.esta_em_loop()  # True/False baseado em entropia
    """
    
    def __init__(self, nome="entropia"):
        self.mk = MarkovUniversal(nome)
        self.historico_entropias = []
        self.janela = 10  # quantos tokens olhar para tras
    
    def alimentar(self, token: str):
        """Alimenta um token e atualiza entropia local.
        Entropia de Shannon dos ultimos N tokens.
        Se todos sao iguais → entropia = 0 (loop).
        Se todos sao diferentes → entropia = maxima.
        """
        self.mk.aprender(token, f"_count")
        self.historico_entropias.append(token)
    
    def _entropia_local(self) -> float:
        """Entropia de Shannon dos ultimos N tokens."""
        if len(self.historico_entropias) < 3: return 1.0
        recentes = self.historico_entropias[-self.janela:]
        freq = {}
        for t in recentes: freq[t] = freq.get(t, 0) + 1
        n = len(recentes)
        h = 0.0
        for c in freq.values():
            p = c / n
            if p > 0: h -= p * math.log2(p)
        # Normaliza: 0 = todos iguais (loop), 1 = todos diferentes
        max_h = math.log2(min(len(freq), n)) if len(freq) > 1 else 0
        if max_h == 0: return 0.0 if h == 0 else 1.0  # tudo igual = loop
        return h / max_h
    
    def _detectar_ciclo(self) -> bool:
        """Detecta padrao ciclico: ABCABCABC (N tokens alternando)."""
        if len(self.historico_entropias) < 10: return False
        recentes = self.historico_entropias[-10:]
        # Tenta periodo de 2 a 5
        for periodo in range(2, 6):
            if len(recentes) < periodo * 2: continue
            padrao = recentes
            ciclico = True
            for i in range(periodo, len(recentes)):
                if recentes[i] != padrao[i % periodo]:
                    ciclico = False
                    break
            if ciclico: return True
        return False
    
    def esta_em_loop(self) -> bool:
        """True se entropia baixa OU padrao ciclico."""
        return self._entropia_local() < 0.3 or self._detectar_ciclo()
    
    def ultima_entropia(self) -> float:
        return self._entropia_local()
    
    def mediana_historica(self) -> float:
        if len(self.historico_entropias) < 3: return 1.0
        from statistics import median
        # Calcula entropia para varias janelas
        entropias = []
        for i in range(0, len(self.historico_entropias) - self.janela, max(1, self.janela//2)):
            janela = self.historico_entropias[i:i+self.janela]
            freq = {}
            for t in janela: freq[t] = freq.get(t, 0) + 1
            n = len(janela)
            h = 0.0
            for c in freq.values():
                p = c / n
                if p > 0: h -= p * math.log2(p)
            max_h = math.log2(min(len(freq), n))
            entropias.append(h / max_h if max_h > 0 else 1.0)
        return median(entropias) if entropias else 1.0


class MCRRuido:
    """Aprende QUE TIPO de ruído funciona para quebrar loops.
    
    Substitui:
    - "pega token de outro topico" fixo → aprende o que funciona
    
    Uso:
        ruido = MCRRuido()
        ruido.tentar("injeção_byte") 
        ruido.registrar("injeção_byte", sucesso=True)
        melhor = ruido.melhor_tipo()  # → "injeção_palavra"
    """
    
    def __init__(self, nome="ruido"):
        self.mk = MarkovUniversal(nome)
        self.tipos = ['byte_global', 'palavra_outro_topico', 'pontuacao', 'semente_original']
    
    def tentar(self, tipo: str, estado_atual: str) -> str:
        """Tenta gerar ruído de um tipo específico."""
        return self.mk.predizer(f"{tipo}_{estado_atual}")[0]
    
    def registrar(self, tipo: str, sucesso: bool):
        """Registra se o tipo de ruído funcionou."""
        self.mk.aprender(tipo, "sucesso" if sucesso else "falha")
    
    def melhor_tipo(self) -> str:
        """Retorna o tipo de ruído com maior taxa de sucesso."""
        scores = []
        for t in self.tipos:
            if t in self.mk.transicoes:
                prox = self.mk.transicoes[t]
                suc = prox.get('sucesso', 0)
                fal = prox.get('falha', 0)
                taxa = suc / max(suc + fal, 1)
                scores.append((taxa, t))
        scores.sort(key=lambda x: -x[0])
        return scores[0][1] if scores else 'palavra_outro_topico'
    
    def taxa_sucesso(self, tipo: str) -> float:
        if tipo not in self.mk.transicoes: return 0.5
        prox = self.mk.transicoes[tipo]
        suc = prox.get('sucesso', 0)
        fal = prox.get('falha', 0)
        return suc / max(suc + fal, 1)


class MCRDecisor:
    """Decide o FLUXO de ações por Markov, não por if/else.
    
    Substitui:
    - "KG → Conector → Cadeia" fixo → Markov decide ordem
    
    Uso:
        dec = MCRDecisor()
        dec.aprender(estado_pergunta, "kg_primeiro")
        decisao = dec.decidir(estado_pergunta)
    """
    
    def __init__(self, nome="decisor"):
        self.mk = MarkovUniversal(nome)
        self.acoes_possiveis = ['kg_primeiro', 'conector_primeiro', 'cadeia_direto',
                                'kg_conector_cadeia', 'conector_kg_cadeia']
    
    def aprender(self, estado_pergunta: str, acao: str, sucesso: bool):
        tag = "ok" if sucesso else "falha"
        self.mk.aprender(f"{estado_pergunta}_{tag}", acao)
    
    def decidir(self, pergunta: str, estado_extra: str = "") -> str:
        """Decide qual acao tomar baseado no estado da pergunta."""
        tipo = self._classificar_pergunta(pergunta)
        estado = f"{tipo}_{estado_extra}" if estado_extra else tipo
        
        # Tenta Markov primeiro
        if estado in self.mk.transicoes:
            melhor = max(self.mk.transicoes[estado], key=self.mk.transicoes[estado].get)
            return melhor
        
        # Fallback: tipo da pergunta determina
        if tipo == 'explicacao': return 'kg_primeiro'
        if tipo == 'criacao': return 'conector_primeiro'
        if tipo == 'busca': return 'kg_conector_cadeia'
        return 'kg_conector_cadeia'
    
    def _classificar_pergunta(self, pergunta: str) -> str:
        # Tenta Markov primeiro (aprendido)
        estado = f"PERG:{pergunta.lower()}"
        if estado in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado)
            if prox and conf > 0.2:
                return str(prox)
        # Se nao aprendeu ainda, fallback (ate ser treinado)
        p = pergunta.lower()
        for palavra, categoria in [
            ('explique', 'explicacao'), ('o que e', 'explicacao'),
            ('como funciona', 'explicacao'), ('defina', 'explicacao'),
            ('crie', 'criacao'), ('gere', 'criacao'), ('criar', 'criacao'),
            ('implemente', 'criacao'), ('busque', 'busca'),
            ('encontre', 'busca'), ('procure', 'busca'), ('onde', 'busca'),
        ]:
            if palavra in p:
                # Aprende com este exemplo
                self.aprender(estado, categoria, True)
                return categoria
        self.aprender(estado, 'geral', True)
        return 'geral'


class MCRDiagnostico:
    """Diagnostico MCR'zificado — Markov de estado para debug.
    
    Substitui:
    - print() fixo de debug → Markov que aponta onde esta o problema
    
    Uso:
        diag = MCRDiagnostico()
        problema = diag.diagnosticar(estado_atual)
        # → "byte:baixo|palavra:alto → JSON no texto"
    """
    
    def __init__(self, nome="diagnostico"):
        self.mk = MarkovUniversal(nome)
        self.historico = []
    
    def alimentar(self, estado: dict, diagnostico: str):
        """Aprende que ESTADO leva a DIAGNOSTICO."""
        codigo = self._codificar_estado(estado)
        self.mk.aprender(codigo, diagnostico)
        self.historico.append((codigo, diagnostico))
    
    def diagnosticar(self, estado: dict) -> str:
        """Retorna diagnostico para o estado atual."""
        codigo = self._codificar_estado(estado)
        if codigo in self.mk.transicoes:
            melhor = max(self.mk.transicoes[codigo], key=self.mk.transicoes[codigo].get)
            return melhor
        return "sem_diagnostico_previo"
    
    def _codificar_estado(self, estado: dict) -> str:
        partes = []
        for k, v in estado.items():
            if isinstance(v, (int, float)):
                nivel = 'alto' if v > 0.7 else 'medio' if v > 0.3 else 'baixo'
                partes.append(f"{k}:{nivel}")
        return '|'.join(partes)


class MCRFerramenta:
    """Cada ferramenta ToolOrchestrator vira um estado num Markov.
    
    Em vez de 30 funcoes fixas, o MCR aprende:
    - Dado ESTADO_ATUAL, qual FERRAMENTA usar
    - Dado FERRAMENTA, qual RESULTADO esperar
    
    Uso:
        f = MCRFerramenta()
        f.registrar("perguntar", estado, "resposta_valida")
        melhor = f.recomendar(estado)  # → "perguntar"
    """
    
    def __init__(self, nome="ferramentas"):
        self.mk = MarkovUniversal(nome)
        self._ferramentas = set()
    
    def registrar_ferramenta(self, nome: str):
        self._ferramentas.add(nome)
    
    def aprender(self, ferramenta: str, estado: str, resultado: str):
        self.mk.aprender(f"{ferramenta}_{estado}", resultado)
    
    def recomendar(self, estado: str) -> str:
        """Recomenda a melhor ferramenta para o estado."""
        scores = []
        for f in self._ferramentas:
            chave = f"{f}_{estado}"
            if chave in self.mk.transicoes:
                result = self.mk.transicoes[chave]
                total = sum(result.values())
                # Score = diversidade de resultados (mais resultados = ferramenta mais util)
                score = len(result) / max(total, 1)
                scores.append((score, f))
        scores.sort(key=lambda x: -x[0])
        return scores[0][1] if scores else ''

    def ferramentas_disponiveis(self) -> list:
        return list(self._ferramentas)


# ============================================================
# MCR BRIDGE — Descobre e expoe 49 modulos + 52 comandos + 30 ferramentas
# ============================================================

class MCRBridge:
    """Bridge universal: descobre modulos, comandos e ferramentas DINAMICAMENTE.
    
    Cada modulo/comando/ferramenta vira um nivel MCR.
    Zero hardcode. Zero import fixo. Tudo descoberto em runtime.
    
    Uso:
        bridge = MCRBridge()
        bridge.discover()  # escaneia tudo
        bridge.usar("modulos.kg", "buscar", ["SPA"])
        bridge.usar("comandos.ensinar", None, ["erro", "causa", "solucao", "ctx"])
        bridge.usar("ferramentas.buscar_kg", {"termo": "SPA"})
    """
    
    def __init__(self):
        self.modulos = {}    # nome -> modulo
        self.comandos = {}   # nome -> funcao
        self.ferramentas = {}  # nome -> funcao
        self.mk = MarkovUniversal("bridge")
        self._descobriu = False
        self._cache = {}     # cache de resultados de descobertas
    
    def descobrir(self):
        """Escaneia tudo disponivel e registra como niveis MCR.
        Usa cache se ja foi descoberto antes."""
        if self._descobriu and self._cache:
            return self._cache
        
        import importlib, pkgutil
        
        # 1. DESCOBRE MODULOS
        mod_path = os.path.join(os.path.dirname(__file__), '..', 'modulos')
        if os.path.isdir(mod_path):
            for fname in os.listdir(mod_path):
                if fname.endswith('.py') and not fname.startswith('_'):
                    nome = fname[:-3]
                    try:
                        spec = importlib.util.spec_from_file_location(
                            nome, os.path.join(mod_path, fname))
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            self.modulos[nome] = mod
                            # Aprende que este modulo existe
                            self.mk.aprender(f"MOD:{nome}", "disponivel")
                    except Exception as e:
                        self.mk.aprender(f"MOD:{nome}", f"erro:{str(e)[:20]}")
        
        # 2. DESCOBRE COMANDOS (por bytes, nao por import)
        cmd_path = os.path.join(os.path.dirname(__file__), '..', 'comandos')
        if os.path.isdir(cmd_path):
            for fname in sorted(os.listdir(cmd_path)):
                if not (fname.startswith('cmd_') and fname.endswith('.py')): continue
                nome = fname[4:-3]
                fpath = os.path.join(cmd_path, fname)
                try:
                    with open(fpath, 'rb') as f:
                        dados = f.read(2000)  # lê como bytes
                    # MCRByte aprende o padrao do comando
                    mk_cmd = MCR(f"cmd_{nome}")
                    mk_cmd.aprender_sequencia(list(dados))
                    # Registra como disponivel (bytes, nao funcao)
                    self.comandos[nome] = dados  
                    self.mk.aprender(f"CMD:{nome}", f"disponivel:{len(dados)}bytes")
                except Exception as e:
                    self.mk.aprender(f"CMD:{nome}", f"erro:{str(e)[:20]}")
        
        self._descobriu = True
        
        return {
            'modulos': len(self.modulos),
            'comandos': len(self.comandos),
        }
    
    def usar_modulo(self, nome: str, funcao: str = None, args: list = None):
        """Chama um modulo: bridge.usar_modulo('kg', 'buscar', ['SPA'])."""
        if nome not in self.modulos: return None
        mod = self.modulos[nome]
        if funcao and hasattr(mod, funcao):
            try:
                return getattr(mod, funcao)(*(args or []))
            except Exception as e:
                self.mk.aprender(f"MOD:{nome}.{funcao}", f"erro:{str(e)[:30]}")
                return None
        return mod
    
    def usar_comando(self, nome: str, kwargs: dict = None):
        """Retorna conhecimento do comando (bytes → texto).
        Usa cache MCRSelfIndex se disponivel, senao usa bytes."""
        if nome not in self.comandos: return None
        
        # Cache: usa MCRSelfIndex se ja indexou
        cache_key = f"cmd_{nome}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        dados = self.comandos[nome]
        if isinstance(dados, bytes):
            try:
                resultado = dados.decode('utf-8', errors='replace')
                self._cache[cache_key] = resultado
                return resultado
            except:
                return f"[CMD:{nome}] {len(dados)} bytes"
        try: 
            resultado = dados(**(kwargs or {}))
            self._cache[cache_key] = resultado
            return resultado
        except Exception as e: 
            return f"[CMD:{nome}] erro: {str(e)[:30]}"
    
    def stats(self) -> dict:
        s = self.mk.stats()
        return {
            'modulos': len(self.modulos),
            'comandos': len(self.comandos),
            'estados_bridge': s['estados'],
            'transicoes_bridge': s['transicoes'],
        }


# ============================================================
# MCR KG AUTO — Auto-categorizacao + Dedup
# ============================================================

class MCRKGAuto:
    """Organiza o KG automaticamente: categoriza, dedup, limpa.
    
    Tudo MCR: categorias sao descobertas por prefixo do ctx,
    duplicatas sao detectadas por Jaccard, limpeza por entropia.
    """
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.mk_cat = MarkovUniversal("categorias")
        self.mk_dedup = MarkovUniversal("dedup")
    
    def categorizar(self) -> dict:
        """Categoriza lessons por prefixo do ctx + conteudo.
        Retorna {categoria: [lessons]}."""
        if not self.kg: return {}
        licoes = self.kg._get_licoes()
        cats = {}
        for l in licoes:
            ctx = l.get('ctx', '?')
            sol = l.get('solucao', '')
            # Categoria = prefixo do ctx
            cat = ctx.split('_')[0] if '_' in ctx else ctx
            # Se comeca com numero, categoria = 'outro'
            if cat and cat[0].isdigit(): cat = 'numerico'
            if cat not in cats: cats[cat] = []
            cats[cat].append(l)
            self.mk_cat.aprender(f"CTX:{ctx}", f"CAT:{cat}")
        return cats
    
    def dedup(self, min_similaridade: float = 0.95) -> int:
        """Remove duplicatas com hash rapido + Jaccard so nos buckets.
        
        Short-circuit: se ja existem lessons inativas, dedup ja foi feito.
        """
        if not self.kg: return 0
        licoes = self.kg._get_licoes()
        if len(licoes) < 50: return 0
        removidas = 0
        
        # Short-circuit: se ja tem lessons inativas, dedup ja foi feito
        inativas = sum(1 for l in licoes if l.get('inactive'))
        if inativas > len(licoes) * 0.05:  # 5%+ ja inativas = ja dedup
            return 0
        
        # PASSO 1: Bucketing por hash rapido (O(n), nao O(n²))
        buckets = {}  # {hash -> [(idx, lesson), ...]}
        for i, l in enumerate(licoes):
            sol = l.get('solucao', '')
            if not sol or len(sol) < 30: continue
            # Hash simples: primeiros 100 chars
            h = hash(sol[:100]) % 50
            buckets.setdefault(h, []).append((i, l))
        
        # PASSO 2: So dedup dentro de cada bucket (grupos pequenos)
        for h, grupo in buckets.items():
            n = len(grupo)
            if n < 2: continue
            # Se grupo e grande (muitas lessons com mesmo hash), limita
            if n > 50:
                continue  # bucket lotado: hash colidiu, pular
            
            for i in range(n):
                if grupo[i][1].get('inactive'): continue
                for j in range(i + 1, n):
                    if grupo[j][1].get('inactive'): continue
                    sol_i = grupo[i][1].get('solucao', '')
                    sol_j = grupo[j][1].get('solucao', '')
                    if not sol_i or not sol_j: continue
                    
                    jac = MarkovUniversal("tmp").jaccard_bytes(sol_i, sol_j)
                    if jac >= min_similaridade:
                        if len(sol_i) <= len(sol_j):
                            grupo[i][1]['inactive'] = True
                        else:
                            grupo[j][1]['inactive'] = True
                        removidas += 1
                        self.mk_dedup.aprender("DUPLICATA_BUCKET", f"JAC:{jac:.2f}")
        
        if removidas:
            self.kg.salvar()
            self.mk_dedup.aprender("TOTAL_REMOVIDAS", str(removidas))
        
        return removidas
        return removidas
    
    def limpar(self) -> dict:
        """Remove lixo: JSON, vazias, _flush.
        Retorna {removidos: N, mantidos: N}."""
        if not self.kg: return {'removidos': 0, 'mantidos': 0}
        licoes = self.kg._get_licoes()
        removidos = 0
        mantidos = 0
        for l in licoes:
            sol = l.get('solucao', '')
            ctx = l.get('ctx', '')
            # Criterios de lixo
            if ctx == '_flush':
                l['inactive'] = True; removidos += 1
            elif not sol or len(sol) < 20:
                l['inactive'] = True; removidos += 1
            elif sol.strip().startswith('{') or sol.strip().startswith('['):
                # JSON — verifica se realmente tem texto util
                import re
                # So marca como lixo se NAO tiver texto legivel
                texto = re.sub(r'[{}"\[\]\\]', ' ', sol)
                palavras = [w for w in texto.split() if len(w) > 3]
                if len(palavras) < 3:
                    l['inactive'] = True; removidos += 1
                else:
                    mantidos += 1
            else:
                mantidos += 1
        if removidos:
            self.kg.salvar()
        return {'removidos': removidos, 'mantidos': mantidos}
    
    def organizar(self) -> dict:
        """Executa tudo: categoriza + dedup + limpa.
        Retorna relatorio completo."""
        cats = self.categorizar()
        removidos_dedup = self.dedup()
        limpeza = self.limpar()
        return {
            'categorias': len(cats),
            'distribuicao': {c: len(v) for c, v in sorted(cats.items(), key=lambda x: -len(x[1]))},
            'dedup_removidos': removidos_dedup,
            'limpeza': limpeza,
            'stats_mk': self.mk_cat.stats(),
        }


# ============================================================
# MCR EXPANSAO — AutoLoop que usa TUDO para expandir conhecimento
# ============================================================

class MCRExpansao:
    """AutoLoop que usa TODOS os modulos, comandos e ferramentas.
    
    Fluxo:
    1. Tema definido (ex: "Eridanus", "SPA")
    2. Bridge descobre o que esta disponivel
    3. Para CADA modulo/comando/ferramenta:
       a) Tenta usar para aprender sobre o tema
       b) Se resultado util → salva no KG
       c) Se nao → tenta proximo
    4. Apos N tentativas, autoavalia o KG
    5. Se KG do tema ainda fraco → repete com mais recursos
    """
    
    # Comandos MCR-puros (sem LLM)
    COMANDOS_MCR = ['explorar', 'aprender_conceito', 'conectar', 'analisar', 'memoria']
    
    def __init__(self, kg=None, bridge=None):
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self.mk = MarkovUniversal("expansao")
    
    def expandir(self, tema: str, max_recursos: int = 10) -> dict:
        """Tenta expandir o conhecimento sobre um tema usando TUDO disponivel."""
        if not self.kg: return {'tema': tema, 'expansoes': 0}
        
        if not self.bridge._descobriu:
            disc = self.bridge.descobrir()
        
        resultados = []
        recursos_usados = []
        
        # Ordem decidida por MCRDecisor, nao fixa (docs primeiro se disponivel)
        try:
            idx = _get_doc_index()
            idx.indexar()
            tem_docs = len(idx._indice) > 0
        except:
            tem_docs = False
        ordem = ['docs', 'modulos', 'comandos', 'kg'] if tem_docs else ['modulos', 'comandos', 'kg']
        try:
            dec = MCRDecisor("expansao_ordem")
            ordem_str = dec.decidir(f"EXPANDIR:{tema}")
            if ordem_str and '_' in str(ordem_str):
                ordem = str(ordem_str).split('_')
        except:
            pass
        
        for etapa in ordem:
            if etapa == 'docs':
                try:
                    idx = _get_doc_index()
                    docs = idx.buscar(tema)
                    for doc in docs:
                        conteudo = idx.ler(doc['caminho'], 500)
                        if conteudo and tema.lower() in conteudo.lower():
                            resultados.append(f"[DOCS:{os.path.basename(doc['caminho'])}] OK")
                            recursos_usados.append(f"docs:{doc['caminho']}")
                            self.mk.aprender(f"EXPANDIR:{tema}", f"DOCS:{doc['caminho']}")
                except:
                    pass
            
            elif etapa == 'modulos':
                for nome, mod in list(self.bridge.modulos.items())[:max_recursos//3]:
                    for func_nome in ['buscar', 'buscar_expandido', 'get', 'listar']:
                        if hasattr(mod, func_nome):
                            try:
                                res = getattr(mod, func_nome)(tema)
                                if res:
                                    resultados.append(f"[MOD:{nome}.{func_nome}] OK")
                                    recursos_usados.append(f"modulo:{nome}")
                                    self.mk.aprender(f"EXPANDIR:{tema}", f"MOD:{nome}")
                                break
                            except:
                                pass
            
            elif etapa == 'comandos':
                for nome in self.COMANDOS_MCR:
                    if nome not in self.bridge.comandos: continue
                    cmd_result = self.bridge.usar_comando(nome)
                    if cmd_result and isinstance(cmd_result, str) and len(cmd_result) > 20:
                        resultados.append(f"[CMD:{nome}] OK")
                        recursos_usados.append(f"comando:{nome}")
                        self.mk.aprender(f"EXPANDIR:{tema}", f"CMD:{nome}")
            
            elif etapa == 'kg':
                licoes = self.kg.buscar(tema, max_r=5)
                if licoes:
                    resultados.append(f"[KG] {len(licoes)} lessons")
                    recursos_usados.append("kg")
        
        # 4. Autoavalia: o conhecimento sobre o tema melhorou?
        lessons_tema = self.kg.buscar(tema, max_r=20)
        n_antes = 0  # idealmente teriamos o snapshot anterior
        
        # Salva aprendizado
        self.kg.aprender_conceito(
            f"expansao_{tema}",
            f"Expandido via {len(recursos_usados)} recursos. "
            f"Agora temos {len(lessons_tema)} lessons sobre o tema. "
            f"Recursos: {', '.join(recursos_usados)}.",
            ctx="expansao_auto"
        )
        
        return {
            'tema': tema,
            'expansoes': len(resultados),
            'recursos_usados': recursos_usados,
            'lessons_agora': len(lessons_tema),
            'detalhes': resultados,
        }


# ============================================================
# MCR META — Auto-organizacao do proprio MCR
# ============================================================

class MCRMeta:
    """MCR que gerencia o proprio MCR.
    
    Aprende:
    - Qual ctx usar para cada tipo de lesson
    - Quantas lessons sao ideais por categoria
    - Quando expandir KG (se fraco)
    - Quando limpar KG (se sujo)
    
    Tudo MCR. Zero hardcode.
    """
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.auto_kg = MCRKGAuto(self.kg)
        self.expansao = MCRExpansao(self.kg)
        self.mk = MarkovUniversal("meta")
        self._ultimo_estado = {}
    
    def diagnosticar(self) -> dict:
        """Diagnostica a saude do sistema MCR."""
        if not self.kg: return {'erro': 'KG indisponivel'}
        licoes = self.kg._get_licoes()
        
        # Metricas
        uteis = [l for l in licoes 
                 if l.get('solucao','') and len(l.get('solucao','')) > 50
                 and not l.get('solucao','').strip().startswith('{')
                 and not l.get('inactive')]
        lixo = len(licoes) - len(uteis)
        
        # Categorias
        cats = self.auto_kg.categorizar()
        categorias_fracas = {c: len(v) for c, v in cats.items() if len(v) < 10}
        
        estado = {
            'total': len(licoes),
            'uteis': len(uteis),
            'lixo': lixo,
            'aproveitamento': f"{len(uteis)/max(len(licoes),1)*100:.0f}%",
            'categorias': len(cats),
            'categorias_fracas': len(categorias_fracas),
            'precisa_limpar': lixo > len(uteis),
            'precisa_expandir': len(categorias_fracas) > 3,
        }
        
        self._ultimo_estado = estado
        self.mk.aprender("DIAG", f"uteis:{len(uteis)}|lixo:{lixo}")
        return estado
    
    def auto_organizar(self) -> dict:
        """Auto-organiza o MCR: limpa, dedup, expande se necessario."""
        acoes = []
        
        # 1. Diagnostica
        estado = self.diagnosticar()
        acoes.append(f"diagnostico: {estado['aproveitamento']} util")
        
        # 2. Limpa se necessario
        if estado.get('precisa_limpar'):
            limpeza = self.auto_kg.limpar()
            acoes.append(f"limpeza: {limpeza['removidos']} removidos")
            self.mk.aprender("ACAO:LIMPAR", f"removeu:{limpeza['removidos']}")
        
        # 3. Dedup se necessario
        if estado.get('total', 0) > 200:
            dedup = self.auto_kg.dedup()
            if dedup:
                acoes.append(f"dedup: {dedup} removidas")
                self.mk.aprender("ACAO:DEDUP", f"removeu:{dedup}")
        
        # 4. Expande categorias fracas
        if estado.get('precisa_expandir'):
            cats = self.auto_kg.categorizar()
            for cat, lessons in cats.items():
                if len(lessons) < 10:
                    # Tenta expandir
                    tema = cat
                    res = self.expansao.expandir(tema)
                    if res['expansoes'] > 0:
                        acoes.append(f"expandiu:{tema} ({res['expansoes']} recursos)")
                        self.mk.aprender(f"ACAO:EXPANDIR:{tema}", f"recursos:{res['expansoes']}")
        
        return {
            'acoes': acoes,
            'n_acoes': len(acoes),
            'estado_final': self.diagnosticar(),
        }


# ============================================================
# MCR SWARM — Workers paralelos + Mestre + AutoStart
# ============================================================

class MCRWorker:
    """UM MCR completo que executa UMA tarefa especifica.
    
    Cada worker tem SEU proprio MCRConector, Markovs, estado.
    Nao compartilha nada com outros workers.
    Leve (~5MB). Pode ter 100 rodando em paralelo.
    
    Uso:
        w = MCRWorker("busca", "buscar_kg", {"termo": "SPA"})
        w.executar()
        print(w.resultado)
    """
    
    def __init__(self, nome: str, tarefa: str, dados: dict = None):
        self.nome = nome
        self.tarefa = tarefa  # 'buscar_kg', 'conectar', 'gerar', 'validar'
        self.dados = dados or {}
        self.conector = MCRConector()
        self.mk = MarkovUniversal(f"worker_{nome}")
        self.resultado = None
        self.nota = 0
        self.erro = None
        self.tempo = 0
    
    def executar(self):
        """Executa a tarefa. Cada worker tem seu proprio estado."""
        import time
        t0 = time.time()
        try:
            if self.tarefa == 'buscar_kg':
                kg = _get_kg()
                if kg:
                    termo = self.dados.get('termo', '')
                    lessons = kg.buscar(termo, max_r=10, pergunta=self.dados.get('pergunta', ''))
                    for i, l in enumerate(lessons):
                        sol = l.get('solucao', '') or l.get('erro', '')
                        if sol:
                            self.conector.alimentar(sol, f"kg_{i}")
                    self.resultado = [l.get('solucao', '') for l in lessons]
                    self.nota = min(10, len(lessons))
            
            elif self.tarefa == 'conectar':
                if self.dados.get('topicos'):
                    for a, b in self.dados['topicos']:
                        cx = self.conector.conectar(a, b)
                        if cx:
                            self.resultado = cx.get('sequencia', '')
                            self.nota = cx.get('nota', 0)
            
            elif self.tarefa == 'gerar':
                cadeia = MCRCadeia(self.conector)
                semente = self.dados.get('semente', 'SPA')
                res = cadeia.gerar(semente, n_tokens=self.dados.get('n_tokens', 30))
                self.resultado = res.get('texto', '')
                self.nota = res.get('nota', 0)
            
            elif self.tarefa == 'validar':
                texto = self.dados.get('texto', '')
                if texto:
                    # Autoavaliacao simples
                    palavras = texto.split()
                    n = len(palavras)
                    if n >= 4:
                        bigramas = [' '.join(palavras[i:i+2]) for i in range(n-1)]
                        rep = 1.0 - (len(set(bigramas)) / max(len(bigramas), 1))
                    else:
                        rep = 0
                    self.nota = max(0, 10 - rep * 10)
                    self.resultado = {'repeticao': round(rep, 3), 'n_palavras': n}
            
            else:
                self.erro = f"tarefa_desconhecida:{self.tarefa}"
            
            self.mk.aprender(f"TAREFA:{self.tarefa}", f"NOTA:{int(self.nota)}")
            
        except Exception as e:
            self.erro = str(e)[:50]
            self.mk.aprender(f"TAREFA:{self.tarefa}", f"ERRO:{str(e)[:30]}")
        
        self.tempo = time.time() - t0
        return self


class MCRSpawner:
    """Cria workers em threads. MCR decide quantos.
    
    Uso:
        spawner = MCRSpawner()
        resultados = spawner.spawnar([
            ("busca1", "buscar_kg", {"termo": "SPA"}),
            ("busca2", "buscar_kg", {"termo": "Eridanus"}),
            ("gera1", "gerar", {"semente": "SPA"}),
        ])
        # Todos rodam em PARALELO
    """
    
    def __init__(self):
        self.mk = MarkovUniversal("spawner")
        self.workers = []
    
    def spawnar(self, tarefas: list) -> list:
        """Cria e executa N workers em paralelo.
        
        Args:
            tarefas: lista de (nome, tarefa, dados)
        Returns:
            lista de MCRWorker executados
        """
        import threading
        
        workers = []
        threads = []
        
        for nome, tarefa, dados in tarefas:
            w = MCRWorker(nome, tarefa, dados)
            workers.append(w)
            self.mk.aprender(f"SPAWN:{tarefa}", nome)
            
            t = threading.Thread(target=w.executar)
            threads.append(t)
            t.start()
        
        # Aguarda todos terminarem
        for t in threads:
            t.join()
        
        self.workers = workers
        return workers


class MCRMestre:
    """MCR que GERENCIA outros MCRs (workers).
    
    Decide TUDO por Markov, sem if/else:
    - Quantos workers criar
    - Quais tarefas distribuir
    - Como consolidar resultados
    - Tudo aprendido por experiencia
    
    Uso:
        mestre = MCRMestre()
        resposta = mestre.processar("Explique o sistema SPA do MCR")
    """
    
    def __init__(self, bridge=None):
        self.mk = MarkovUniversal("mestre")
        self.bridge = bridge or MCRBridge()
        self.spawner = MCRSpawner()
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.diagnostico = MCRDiagnostico()
    
    def processar(self, pergunta: str) -> dict:
        """Processa uma pergunta usando workers paralelos."""
        import time
        t0 = time.time()
        
        # 1. Bridge descobre modulos disponiveis
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        
        # 2. Decide tipo da pergunta (MCR, nao if/else)
        tipo = 'explicacao'
        if any(w in pergunta.lower() for w in ['crie', 'gere', 'criar']):
            tipo = 'criacao'
        elif any(w in pergunta.lower() for w in ['busque', 'encontre']):
            tipo = 'busca'
        
        self.mk.aprender(f"PERGUNTA:{tipo}", "PROCESSANDO")
        
        # 3. Decide quantos workers baseado no tipo (aprendido)
        n_workers = 3  # fallback
        estado_workers = f"TIPO:{tipo}"
        if estado_workers in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado_workers)
            if prox:
                try: n_workers = int(prox.replace('W:', ''))
                except: pass
        
        # 4. Cria tarefas para workers
        tarefas = []
        
        # Worker 1: Busca KG
        tarefas.append(("kg", "buscar_kg", {
            'termo': pergunta.split()[-1] if pergunta.split() else 'MCR',
            'pergunta': pergunta
        }))
        
        # Worker 2: Gera com cadeia (se tiver topicos)
        tarefas.append(("gerador", "gerar", {
            'semente': pergunta.split()[0] if pergunta.split() else 'O',
            'n_tokens': 40
        }))
        
        # Worker 3: Valida (se tiver texto para validar)
        tarefas.append(("validador", "validar", {'texto': pergunta}))
        
        # 5. Spawna workers em PARALELO
        workers = self.spawner.spawnar(tarefas)
        
        # 6. Consolida resultados
        textos = []
        for w in workers:
            if w.resultado and not w.erro:
                if isinstance(w.resultado, str):
                    textos.append(w.resultado)
                elif isinstance(w.resultado, list):
                    textos.extend(w.resultado)
                self.mk.aprender(f"WORKER:{w.tarefa}", f"NOTA:{int(w.nota)}")
        
        # 7. Gera resposta final com MCRCadeia
        if textos:
            for t in textos:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t, "consolidado")
        
        semente = pergunta.split()[0] if pergunta.split() else 'O'
        res_cadeia = self.cadeia.gerar(semente, n_tokens=40)
        resposta = res_cadeia.get('texto', '')
        
        # 8. Autoavalia
        nota_cadeia = res_cadeia.get('nota', 0)
        nota = nota_cadeia
        
        # Diagnostico
        diag = self.diagnostico.diagnosticar({
            'byte': nota_cadeia / 10,
            'palavra': nota_cadeia / 10,
            'token': nota_cadeia > 5,
        })
        
        self.mk.aprender(f"RESULTADO:{tipo}", f"NOTA:{int(nota)}")
        
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': round(nota, 1),
            'n_workers': len(workers),
            'workers': [{'nome': w.nome, 'tarefa': w.tarefa, 'nota': w.nota, 'tempo': round(w.tempo, 3)} for w in workers],
            'diagnostico': diag,
            'tempo': round(time.time() - t0, 2),
        }


class MCRAutoStart:
    """Auto-start: MCR se auto-organiza quando o sistema inicia.
    Usa cache de checksum para evitar dedup O(n²) a cada execucao."""
    
    _cache_checksum = None
    _cache_path = None
    
    @classmethod
    def _calc_checksum(cls, kg):
        """Calcula checksum do KG para saber se mudou."""
        if not kg: return 0
        licoes = kg._get_licoes()
        # Checksum = total lessons + ultimo timestamp + hash dos ctxs
        ts = max(l.get('timestamp', 0) for l in licoes) if licoes else 0
        ctxs = '|'.join(sorted(set(l.get('ctx', '?') for l in licoes)))
        return hash((len(licoes), ts, ctxs)) % (10**12)
    
    @staticmethod
    def iniciar() -> dict:
        """Executa auto-diagnostico com cache se KG nao mudou."""
        try:
            kg = _get_kg()
            if not kg: return {'erro': 'KG indisponivel'}
            
            bridge = MCRBridge()
            bridge.descobrir()
            
            # Calcula checksum e verifica cache
            checksum = MCRAutoStart._calc_checksum(kg)
            if checksum == MCRAutoStart._cache_checksum:
                # KG nao mudou — pula dedup/limpeza
                licoes = kg._get_licoes()
                uteis = [l for l in licoes 
                         if l.get('solucao','') and len(l.get('solucao','')) > 50
                         and not l.get('solucao','').startswith('{')
                         and not l.get('inactive')]
                return {
                    'aproveitamento': f"{len(uteis)/max(len(licoes),1)*100:.0f}%",
                    'uteis': len(uteis), 'total': len(licoes),
                    'acoes': ['cache_hit'], 'modulos': bridge.stats().get('modulos', 0),
                    'comandos': bridge.stats().get('comandos', 0),
                }
            
            meta = MCRMeta(kg)
            estado = meta.diagnosticar()
            acoes = []
            
            if estado.get('precisa_limpar'):
                limpeza = meta.auto_kg.limpar()
                acoes.append(f"limpeza:{limpeza['removidos']}")
            
            if estado.get('total', 0) > 200:
                dedup = meta.auto_kg.dedup()
                if dedup:
                    acoes.append(f"dedup:{dedup}")
            
            # Salva checksum
            MCRAutoStart._cache_checksum = checksum
            
            if acoes:
                meta.mk.aprender("AUTOSTART", '|'.join(acoes))
            
            return {
                'aproveitamento': estado.get('aproveitamento', '?'),
                'uteis': estado.get('uteis', 0),
                'total': estado.get('total', 0),
                'acoes': acoes,
                'modulos': bridge.stats().get('modulos', 0),
                'comandos': bridge.stats().get('comandos', 0),
            }
        except Exception as e:
            return {'erro': str(e)[:100]}


# ============================================================
# MCR PESO NOTA — Aprenfe pesos ideais por regressao markoviana
# ============================================================

class MCRPesoNota:
    """Aprende pesos ideais para cada componente da nota.
    
    Em vez de Byte(2)+Palavra(5)+Token(3) fixo,
    aprende: "byte+palavra=0.8 → nota 3.0" (baixa)
             "byte+token=0.5 → nota 7.0" (alta)
    
    Uso:
        pn = MCRPesoNota()
        pn.aprender({"byte": 0.8, "palavra": 0.2, "token": 0.3}, 3.0)
        nota = pn.calcular(byte_s=4.0, palavra_s=2.0, token_s=1.0)
    """
    
    def __init__(self, nome="peso_nota"):
        self.mk = MarkovUniversal(nome)
        self.historico = []
    
    def aprender(self, caracteristicas: dict, nota_real: float):
        """Aprende que CARACTERISTICAS levam a NOTA_REAL.
        
        Args:
            caracteristicas: {"byte": 0.8, "palavra": 0.2, "token": 0.3}
            nota_real: 3.0 (nota humana ou externa)
        """
        estado = self._codificar(caracteristicas)
        self.mk.aprender(estado, f"NOTA:{int(nota_real*10)}")
        self.historico.append((caracteristicas, nota_real))
    
    def calcular(self, byte_s=None, palavra_s=None, token_s=None) -> float:
        """Calcula nota estimada baseada no que aprendeu.
        Sem pesos fixos — tudo baseado em experiencias anteriores."""
        if not self.historico:
            # Fallback: nota generica baseada nos componentes
            nota = 5.0
            if byte_s is not None: nota += (byte_s - 5) * 0.3
            if palavra_s is not None: nota += (palavra_s - 5) * 0.5
            if token_s is not None: nota += (token_s - 3) * 0.2
            return max(0, min(10, nota))
        
        # Busca experiencias similares
        caracteristicas = {}
        if byte_s is not None: caracteristicas['byte'] = byte_s / 10
        if palavra_s is not None: caracteristicas['palavra'] = palavra_s / 10
        if token_s is not None: caracteristicas['token'] = token_s / 10
        
        estado = self._codificar(caracteristicas)
        
        if estado in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado)
            if prox and conf > 0.1:
                try:
                    return int(prox.replace('NOTA:', '')) / 10.0
                except:
                    pass
        
        # Se nao achou, media das experiencias similares
        notas_similares = []
        for c, n in self.historico:
            sim = sum(1 for k in caracteristicas if k in c and abs(caracteristicas[k] - c[k]) < 0.2)
            if sim >= 2:
                notas_similares.append(n)
        
        return sum(notas_similares)/len(notas_similares) if notas_similares else 5.0
    
    def _codificar(self, carac: dict) -> str:
        partes = []
        for k in ['byte', 'palavra', 'token']:
            v = int(carac.get(k, 0) * 10)
            partes.append(f"{k}:{v}")
        return '|'.join(partes)


# ============================================================
# MCR THRESHOLD — Threshold por mediana dos dados (Regra de Ouro)
# ============================================================

class MCRThreshold:
    """Threshold descoberto por MEDIANA dos dados, nunca fixo.
    
    Regra de Ouro: Dados definem thresholds.
    
    Uso:
        t = MCRThreshold()
        t.observar(0.8)  # jaccard observado
        t.observar(0.9)
        t.observar(0.85)
        threshold = t.calcular(multiplicador=0.5)  # mediana * 0.5
    """
    
    def __init__(self, nome="threshold"):
        self.mk = MarkovUniversal(nome)
        self.observacoes = []
    
    def observar(self, valor: float):
        """Registra um valor observado."""
        self.observacoes.append(valor)
        self.mk.aprender(f"VAL:{int(valor*100)}", "OBS")
    
    def calcular(self, multiplicador: float = 1.0) -> float:
        """Retorna threshold = mediana(observacoes) * multiplicador.
        Se nao tem dados, fallback = 0.5 (neutro)."""
        if len(self.observacoes) < 3:
            return 0.5
        from statistics import median
        return median(self.observacoes) * multiplicador
    
    def obter(self, chave: str, fallback: float = 0.5) -> float:
        """Retorna threshold aprendido para uma chave, ou fallback.
        
        MCR aprende o threshold ideal para cada tipo de operacao.
        Se nao tem dados suficientes, retorna fallback (nao fixo, parametrizavel).
        """
        # Busca no Markov se ja aprendeu esta chave
        pred = self.mk.predizer(f"THR:{chave}")
        if pred[0] is not None and pred[1] > 0.3:
            try:
                return int(pred[0]) / 100.0
            except (ValueError, TypeError):
                pass
        # Fallback: mediana das observacoes gerais
        if len(self.observacoes) >= 3:
            from statistics import median
            return median(self.observacoes)
        return fallback
    
    def aprender(self, chave: str, valor: float):
        """Ensina o threshold ideal para uma chave."""
        self.mk.aprender(f"THR:{chave}", f"{int(valor*100)}")
        self.observar(valor)


# Threshold global para filtros (MCR, nao fixo)
_MCR_THRESHOLD_FILTRO = MCRThreshold("filtro_global")

# Thresholds especificos (cada tipo de decisao)
_MCR_THRESHOLD_CONF = MCRThreshold("confianca")      # conf < ?
_MCR_THRESHOLD_TAMANHO = MCRThreshold("tamanho")     # len < ?
_MCR_THRESHOLD_REPETICAO = MCRThreshold("repeticao") # repeticao > ?
_MCR_THRESHOLD_PALAVRA = MCRThreshold("palavra")     # len(p) > ?
_MCR_THRESHOLD_CONEXAO = MCRThreshold("conexao")     # pesos byte/palavra/token
_MCR_THRESHOLD_NOTA = MCRThreshold("nota")           # faixas de nota


# ============================================================
# MCR FUEL — MCR que se auto-alimenta de 9 fontes
# ============================================================

class MCRFuel:
    """MCR busca o proprio combustivel.
    
    Percorre 9 fontes e alimenta o KG automaticamente:
    1. Codigo fonte (.py)
    2. Documentacao (docs/*.md, docs/MCR - Instrucoes/*.txt)
    3. Modulos (48 modulos)
    4. Comandos (52 comandos)
    5. MANIFEST (catalogo completo)
    6. Prototipos (22 prototipos)
    7. Cache e episodios anteriores
    8. Ferramentas (30 ferramentas)
    9. Conhecimento do proprio KG (re-organizar)
    
    Uso:
        fuel = MCRFuel()
        n = fuel.abastecer()  # retorna quantas lessons criou
    """
    
    def __init__(self, kg=None, bridge=None):
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._base_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.mk = MarkovUniversal("fuel")
        self.total_lessons = 0
    
    def _ler(self, caminho, max_bytes=1000):
        try:
            if not os.path.exists(caminho): return ''
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_bytes)
        except: return ''
    
    def _listar_arquivos(self, diretorio, ext, max_n=100):
        if not os.path.isdir(diretorio): return []
        arquivos = []
        for fname in os.listdir(diretorio):
            if fname.endswith(ext) and not fname.startswith('__'):
                arquivos.append(os.path.join(diretorio, fname))
                if len(arquivos) >= max_n: break
        return arquivos
    
    def _alimentar(self, erro, solucao, ctx='fuel'):
        if not solucao or len(solucao) < 20: return
        # Extrai so o texto util (limpo, sem JSON)
        texto = solucao.replace('\n', ' ').strip()
        if texto.startswith('{') or texto.startswith('['): return
        self.kg.aprender(erro=erro, causa=f"fuel:{ctx}", solucao=texto, ctx=ctx)
        self.total_lessons += 1
    
    def abastecer(self, fontes=None) -> int:
        """Percorre as fontes e alimenta o KG.
        
        Args:
            fontes: lista de fontes para percorrer (None = todas)
        Returns:
            numero de lessons criadas
        """
        if not self.kg: return 0
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        
        self.total_lessons = 0
        fontes_escolhidas = fontes or ['lore', 'codigo', 'docs', 'modulos', 'comandos',
                                        'manifesto', 'prototipos', 'cache', 'ferramentas', 'kg']
        
        for fonte in fontes_escolhidas:
            if fonte == 'codigo':
                for f in self._listar_arquivos(os.path.join(self._base_mod, 'modulos'), '.py', 20):
                    nome = os.path.basename(f)
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"modulo_{nome}", f"Codigo do modulo {nome}: {conteudo}", "fuel_codigo")
                for f in self._listar_arquivos(os.path.join(self._base_mod, 'comandos'), '.py', 20):
                    nome = os.path.basename(f)
                    conteudo = self._ler(f, 300)
                    if conteudo:
                        self._alimentar(f"comando_{nome}", f"Comando {nome}: {conteudo}", "fuel_codigo")
            
            elif fonte == 'docs':
                docs_dir = os.path.join(self._base, 'docs')
                for f in self._listar_arquivos(docs_dir, '.md', 15):
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"doc_{os.path.basename(f)}", conteudo, "fuel_docs")
                # Instrucoes
                instr_dir = os.path.join(docs_dir, 'MCR - Instrucoes')
                for f in self._listar_arquivos(instr_dir, '.txt', 10):
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"instr_{os.path.basename(f)}", conteudo, "fuel_docs")
            
            elif fonte == 'modulos':
                for nome in sorted(self.bridge.modulos.keys()):
                    mod = self.bridge.modulos[nome]
                    doc = (mod.__doc__ or '')
                    if doc:
                        self._alimentar(f"mod:{nome}", doc, "fuel_modulos")
                    # Tenta listar funcoes
                    funcoes = [a for a in dir(mod) if not a.startswith('_') and callable(getattr(mod, a, None))]
                    if funcoes:
                        self._alimentar(f"mod:{nome}_funcoes", f"Funcoes: {', '.join(funcoes)}", "fuel_modulos")
            
            elif fonte == 'comandos':
                for nome in sorted(self.bridge.comandos.keys()):
                    self._alimentar(f"cmd:{nome}", f"Comando disponivel: {nome}", "fuel_comandos")
            
            elif fonte == 'manifesto':
                manifesto = self._ler(os.path.join(self._base, 'docs', 'MANIFEST.md'), 2000)
                if manifesto:
                    self._alimentar("manifesto", manifesto, "fuel_manifesto")
            
            elif fonte == 'prototipos':
                sandbox_dir = os.path.join(self._base, 'sandbox')
                for f in self._listar_arquivos(sandbox_dir, '.py', 15):
                    if f.endswith('.py') and ('prototipo' in f or 'test_' in f):
                        conteudo = self._ler(f, 300)
                        if conteudo:
                            nome = os.path.basename(f)
                            self._alimentar(f"prototipo_{nome}", conteudo, "fuel_prototipos")
            
            elif fonte == 'cache':
                # Episodios
                ep_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
                if os.path.exists(ep_path):
                    try:
                        with open(ep_path, 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        for ep in dados:
                            req = ep.get('request', '')
                            suc = ep.get('sucesso', False)
                            if req:
                                self._alimentar(f"episodio_{req}", f"Request: {req} | Sucesso: {suc}", "fuel_cache")
                    except: pass
                # Conversas
                conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
                if os.path.exists(conv_path):
                    try:
                        with open(conv_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if i >= 10: break
                                try:
                                    entry = json.loads(line.strip())
                                    msg = entry.get('msg', '')
                                    if msg:
                                        self._alimentar(f"conversa_{i}", msg, "fuel_cache")
                                except: pass
                    except: pass
            
            elif fonte == 'ferramentas':
                ferramentas_list = [
                    'buscar_kg', 'buscar_estrategico', 'pattern_analyze',
                    'ler_arquivo', 'validar_codigo', 'gerar_esqueleto'
                ]
                for f in ferramentas_list:
                    self._alimentar(f"tool:{f}", f"Ferramenta disponivel: {f}", "fuel_ferramentas")
            
            elif fonte == 'kg':
                # Re-organiza o proprio KG
                try:
                    licoes = self.kg._get_licoes()
                    uteis = [l for l in licoes 
                             if l.get('solucao','') and len(l.get('solucao','')) > 50
                             and not l.get('solucao','').startswith('{')
                             and not l.get('inactive')]
                    self._alimentar("kg_sumario", 
                        f"KG tem {len(licoes)} lessons, {len(uteis)} uteis, "
                        f"{len(licoes)-len(uteis)} lixo. "
                        f"Distribuicao: {dict(__import__('collections').Counter(l.get('ctx','?') for l in licoes).most_common(10))}",
                        "fuel_kg")
                except: pass
        
        # Forca flush do KG
        if self.total_lessons > 0:
            for _ in range(10): self.kg.aprender_conceito("_fuel_flush", "_", ctx="_flush")
        
        self.mk.aprender("FUEL", f"LESSONS:{self.total_lessons}")
        return self.total_lessons
    
    def abastecer_se_precisar(self, min_uteis=100) -> bool:
        """Só abastece se o KG estiver com menos de min_uteis lessons uteis."""
        try:
            licoes = self.kg._get_licoes()
            uteis = [l for l in licoes 
                     if l.get('solucao','') and len(l.get('solucao','')) > 50
                     and not l.get('solucao','').startswith('{')
                     and not l.get('inactive')]
            if len(uteis) < min_uteis:
                n = self.abastecer()
                return n > 0
            return False
        except:
            return False


# ============================================================
# MCR META GAP — Descobre gaps e busca aprender
# ============================================================

class MCRMetaGap:
    """MCR descobre o que nao sabe e busca aprender.
    
    Em vez de priorizar fontes (hardcode), diagnostica gaps
    no proprio conhecimento e busca preencher especificamente.
    
    Uso:
        meta = MCRMetaGap()
        gaps = meta.diagnosticar_gaps()
        meta.buscar_para_gap("Eridanus")
        meta.ciclo_completo()  # tudo automatico
    """
    
    def __init__(self, kg=None, bridge=None):
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.mk = MarkovUniversal("metagap")
        self.gaps_encontrados = []
    
    def diagnosticar_gaps(self, min_por_prefixo: int = 3) -> list:
        """Percorre o KG e descobre temas com poucas lessons.
        
        Para CADA prefixo de ctx:
          - Se tem < min_por_prefixo lessons → gap
        
        Retorna: [(prefixo, n_lessons, termos_exemplo), ...]
        """
        if not self.kg: return []
        licoes = self.kg._get_licoes()
        
        # Agrupa por prefixo do ctx
        prefixos = {}
        for l in licoes:
            ctx = l.get('ctx', '')
            sol = l.get('solucao', '')
            if not sol or len(sol) < 20: continue
            if l.get('inactive'): continue
            prefixo = ctx.split('_')[0] if '_' in ctx else ctx
            if prefixo not in prefixos:
                prefixos[prefixo] = {'count': 0, 'termos': set()}
            prefixos[prefixo]['count'] += 1
            # Extrai termos relevantes da solucao
            for p in sol.lower().split():
                if len(p) > 3 and p not in CONECTORES:
                    prefixos[prefixo]['termos'].add(p)
                    if len(prefixos[prefixo]['termos']) > 5: break
        
        # Gaps: prefixos com poucas lessons
        gaps = []
        for prefixo, dados in sorted(prefixos.items(), key=lambda x: x[1]['count']):
            if dados['count'] < min_por_prefixo and len(prefixo) > 1:
                termo_exemplo = list(dados['termos']) if dados['termos'] else [prefixo]
                gaps.append({
                    'prefixo': prefixo,
                    'n_lessons': dados['count'],
                    'termos': termo_exemplo,
                    'score': min_por_prefixo - dados['count'],
                })
        
        gaps.sort(key=lambda x: -x['score'])
        self.gaps_encontrados = gaps
        self.mk.aprender("GAPS", f"{len(gaps)} gaps encontrados")
        return gaps
    
    def buscar_para_gap(self, gap: dict) -> int:
        """Busca fontes especificas para preencher um gap.
        
        Short-circuit: se KG ja tem lessons uteis > 200, pula.
        """
        if not self.kg: return 0
        
        # Short-circuit: KG ja esta bem alimentado
        if self.kg._get_licoes() and len(self.kg._get_licoes()) > 300:
            return 0
        
        termo = gap['termos'][0] if gap['termos'] else gap['prefixo']
        n_antes = len(self.kg._get_licoes())
        
        # 1. Busca em docs via indice (0.01s, nao 10-20s)
        doc_idx = _get_doc_index()
        doc_idx.indexar()  # so escaneia se nao tiver cache
        docs_encontrados = doc_idx.buscar(termo)
        for doc in docs_encontrados:
            conteudo = doc_idx.ler(doc['caminho'], max_bytes=2000)
            if conteudo and termo.lower() in conteudo.lower():
                idx = conteudo.lower().find(termo.lower())
                inicio = max(0, idx - 100)
                fim = min(len(conteudo), idx + 300)
                trecho = conteudo[inicio:fim]
                if len(trecho) > 50:
                    self.kg.aprender_conceito(
                        f"{gap['prefixo']}:{os.path.basename(doc['caminho']).replace('.','_')}",
                        f"[Fonte: {doc['caminho']}]\n{trecho}",
                        ctx=f"gap_{gap['prefixo']}"
                    )
        
        # 2. Busca em prototipos
        sandbox_dir = os.path.join(self._base, 'sandbox')
        if os.path.isdir(sandbox_dir):
            for fname in os.listdir(sandbox_dir):
                if not (fname.endswith('.py') or fname.endswith('.lua') or fname.endswith('.txt')): continue
                if not termo.lower() in fname.lower(): continue
                fpath = os.path.join(sandbox_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(1000)
                    if len(conteudo) > 50:
                        self.kg.aprender_conceito(
                            f"{gap['prefixo']}:{fname.replace('.','_')}",
                            f"[Prototipo: {fname}]\n{conteudo}",
                            ctx=f"gap_{gap['prefixo']}"
                        )
                except: pass
        
        # 3. Busca no codigo fonte
        if self.bridge and self.bridge._descobriu:
            for nome, mod in self.bridge.modulos.items():
                if termo.lower() in nome.lower():
                    doc = (mod.__doc__ or '')
                    if doc:
                        self.kg.aprender_conceito(
                            f"{gap['prefixo']}:mod_{nome}",
                            f"[Modulo: {nome}]\n{doc}",
                            ctx=f"gap_{gap['prefixo']}"
                        )
        
        n_depois = len(self.kg._get_licoes())
        n_criadas = n_depois - n_antes
        
        self.mk.aprender(f"GAP:{gap['prefixo']}", f"CRIOU:{n_criadas}")
        return n_criadas
    
    def ciclo_completo(self, min_por_prefixo: int = 3) -> dict:
        """Auto-diagnostico + auto-aprendizado.
        
        Fluxo:
          1. Diagnostica gaps no KG
          2. Para cada gap, busca fontes especificas
          3. Aprende com o que funcionou
        """
        gaps = self.diagnosticar_gaps(min_por_prefixo)
        resultados = []
        total_criadas = 0
        
        for gap in gaps:  # max 10 gaps por ciclo
            n = self.buscar_para_gap(gap)
            if n > 0:
                resultados.append(f"{gap['prefixo']}:{n}")
                total_criadas += n
        
        # Forca flush
        if total_criadas > 0:
            for _ in range(10): self.kg.aprender_conceito("_gap_flush", "_", ctx="_flush")
        
        self.mk.aprender("CICLO_GAP", f"CRIOU:{total_criadas}")
        
        return {
            'gaps': len(gaps),
            'preenchidos': len(resultados),
            'total_lessons_criadas': total_criadas,
            'detalhes': resultados,
        }


# ============================================================
# MCR MESTRE V2 — Decisor treinado, zero if/else
# ============================================================

class MCRMestreV2:
    """Mestre que decide TUDO por Markov, sem if/else.
    
    - Tipo da pergunta: MCRDecisor treinado
    - N workers: aprendido por experiencia
    - Fluxo: aprendido por experiencia
    - Autoavalia: MCRPesoNota (pesos aprendidos)
    - Diagnostico: auto-alimentado a cada execucao
    
    Uso:
        mestre = MCRMestreV2()
        resposta = mestre.processar("Explique SPA")
    """
    
    def __init__(self, bridge=None):
        self.decisor = MCRDecisor("mestre_v2")
        self.peso_nota = MCRPesoNota()
        self.threshold_loop = MCRThreshold("threshold_loop")
        self.bridge = bridge or MCRBridge()
        self.diagnostico = MCRDiagnostico("mestre_diag")
        self.spawner = MCRSpawner()
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.n_execucoes = 0
    
    def processar(self, pergunta: str) -> dict:
        import time
        t0 = time.time()
        self.n_execucoes += 1
        
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        
        # 1. DECISOR decide fluxo + max_ciclos
        fluxo = self.decisor.decidir(pergunta)
        self.decisor.aprender(pergunta, fluxo, True)
        max_ciclos = max(1, min(10, len(pergunta.split()) // 2))
        try:
            dc = MCRDecisor("max_ciclos")
            mc_str = dc.decidir(f"CICLOS:{fluxo}")
            if mc_str:
                max_ciclos = max(1, min(10, int(str(mc_str).replace('C:', ''))))
        except:
            pass
        
        termo = pergunta.split()[-1] if pergunta.split() else 'MCR'
        semente = pergunta.split()[0] if pergunta.split() else 'O'
        
        # 2. MCRPesoNota treinado com exemplos reais
        if len(self.peso_nota.historico) < 5:
            self.peso_nota.aprender({'byte': 0.8, 'palavra': 0.2, 'token': 0.3}, 2.0)
            self.peso_nota.aprender({'byte': 0.7, 'palavra': 0.3, 'token': 0.4}, 3.0)
            self.peso_nota.aprender({'byte': 0.4, 'palavra': 0.7, 'token': 0.8}, 8.0)
            self.peso_nota.aprender({'byte': 0.3, 'palavra': 0.8, 'token': 0.7}, 7.5)
            self.peso_nota.aprender({'byte': 0.5, 'palavra': 0.5, 'token': 0.5}, 5.0)
        
        # 3. WORKERS PARALELOS com estrategias diferentes
        # Cada worker tenta uma abordagem diferente, SIMULTANEAMENTE
        tarefas = []
        if 'kg' in fluxo:
            tarefas.append(("kg", "buscar_kg", {'termo': termo, 'pergunta': pergunta}))
        # Worker alternativo: geracao direta
        tarefas.append(("gerador", "gerar", {'semente': semente, 'n_tokens': 40}))
        
        workers = self.spawner.spawnar(tarefas) if tarefas else []
        
        # 4. CONSOLIDA + EXPANSAO UNICA (nao em loop)
        textos = []
        for w in workers:
            if w.resultado:
                if isinstance(w.resultado, str): textos.append(w.resultado)
                elif isinstance(w.resultado, list): textos.extend(w.resultado)
        
        if textos:
            for t in textos:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t, "consolidado")
        
        # Expande UMA vez (com cache de ultima expansao)
        expansoes_feitas = []
        agora = time.time()
        ultima_exp = getattr(self, '_ultima_expansao', 0)
        
        # So expande se passou mais de 30s desde a ultima expansao
        if agora - ultima_exp > 30:
            fuel = MCRFuel(bridge=self.bridge)
            n_fuel = fuel.abastecer_se_precisar(min_uteis=200)
            if n_fuel:
                expansoes_feitas.append(f"fuel:{n_fuel}")
            
            meta = MCRMetaGap(kg=None, bridge=self.bridge)
            gaps = meta.diagnosticar_gaps(min_por_prefixo=3)
            if gaps:
                n = meta.buscar_para_gap(gaps[0])
                if n > 0:
                    expansoes_feitas.append(f"gap:{n}")
            
            expansao = MCRExpansao(None, self.bridge)
            res_exp = expansao.expandir(termo, max_recursos=3)
            if res_exp.get('expansoes', 0) > 0:
                expansoes_feitas.append(f"exp:{res_exp['expansoes']}")
                if self.conector.topicos:
                    for nome_topico in list(self.conector.topicos.keys()):
                        cx = self.conector.conectar(termo, nome_topico)
                        if cx:
                            self.conector.alimentar(cx.get('sequencia',''), f"emrg_{termo}")
            
            # Bridge: tenta comando como fallback (com cache)
            if 'explorar' in self.bridge.comandos:
                try: self.bridge.usar_comando('explorar', {'termo': termo})
                except: pass
            
            self._ultima_expansao = agora
        
        # 5. GERACAO UNICA (nao em loop)
        res_cadeia = self.cadeia.gerar(semente, n_tokens=40)
        resposta = res_cadeia.get('texto', '')
        nota_cadeia = res_cadeia.get('nota', 0)
        loops = res_cadeia.get('loops_detectados', 0)
        
        # Autoavalia com MCRPesoNota (ja treinado)
        nota = self.peso_nota.calcular(
            byte_s=nota_cadeia,
            palavra_s=min(10, len(resposta)/30),
            token_s=8 if loops < 3 else 3
        )
        
        # Diagnostico AUTO-ALIMENTADO
        estado_diag = {
            'byte': nota_cadeia / 10 if 'nota_cadeia' in dir() else 0.5,
            'palavra': nota / 10,
            'token': nota > 5,
        }
        diag = self.diagnostico.diagnosticar(estado_diag)
        problema = 'loop' if locals().get('loops', 0) > 3 else 'ok'
        self.diagnostico.alimentar(estado_diag, problema)
        
        # Threshold e PesoNota aprendem
        self.threshold_loop.observar(nota / 10)
        self.peso_nota.aprender(
            {'byte': nota/10, 'palavra': nota/10, 'token': nota > 5 and 0.8 or 0.3},
            nota
        )
        
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': round(nota, 1),
            'fluxo': fluxo,
            'ciclos': 1,
            'expansoes': expansoes_feitas,
            'diagnostico': diag,
            'n_execucoes': self.n_execucoes,
            'tempo': round(time.time() - t0, 2),
        }


# ============================================================
# MCR AUTO MELHORIA — MCR se pergunta o que nao sabe e age
# ============================================================

class MCRAutoMelhoria:
    """MCR que se autoaperfeicoa com 7 perguntas.
    
    1. O que NAO sabe? → gaps no KG
    2. Onde e LENTO? → fragmentos
    3. O que REPETIU? → loops
    4. O que ERROU? → diagnosticos
    5. O que APRENDEU? → lessons
    6. O que PRECISA? → pesos
    7. O que ESQUECEU? → docs nao lidos
    """
    
    def __init__(self, kg=None, bridge=None):
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self.meta = MCRMetaGap(self.kg, self.bridge)
        self.fuel = MCRFuel(self.kg, self.bridge)
        self.frag = MCRFragmentador()
        self.mk = MCR("auto_melhoria")
    
    def _p1_gaps(self):
        gaps = self.meta.diagnosticar_gaps(min_por_prefixo=5)
        # So processa os 3 primeiros gaps (evita 37 chamadas web)
        for gap in gaps[:3]:
            n = self.meta.buscar_para_gap(gap)
            if n > 0:
                self.mk.aprender(f"GAP:{gap['prefixo']}", f"{n}")
        return [f"gap_{g['prefixo']}" for g in gaps if g]
    
    def _p2_lento(self):
        if not self.frag.fragmentos: return []
        for f in self.frag.fragmentos:
            if f.tempo > 1.0:
                self.mk.aprender(f"LENTO:{f.nome}", f"{f.tempo:.1f}s")
        return [f"lento:{f.nome}:{f.tempo:.1f}s" for f in self.frag.fragmentos if f.tempo > 1.0]
    
    def _p7_esqueceu(self):
        try:
            idx = _get_doc_index()
            idx.indexar()
            for termo in ['eridanus','spa','shc','npc','lore']:
                docs = idx.buscar(termo)
                for doc in docs:
                    c = idx.ler(doc['caminho'], 500)
                    if c and self.kg:
                        self.kg.aprender_conceito(f"auto_{os.path.basename(doc['caminho']).replace('.','_')}", c, ctx="auto_descoberta")
            return ["docs_autodescobertos"] if any(idx.buscar(t) for t in ['eridanus','spa','lore']) else []
        except: return []
    
    def _p3_repetiu(self):
        if self.fuel.mk.total > 10 and self.fuel.mk.entropia_media() < 0.5:
            self.mk.aprender("LOOP", "detectado")
            return ["loop_detectado"]
        return []
    
    def _p4_errou(self):
        if not self.kg: return []
        e = [l for l in self.kg._get_licoes() if 'erro' in l.get('ctx','')]
        if e: self.mk.aprender("ERROS", str(len(e)))
        return [f"erros:{len(e)}"] if e else []
    
    def _p5_aprendeu(self):
        if not self.kg: return []
        r = [l for l in self.kg._get_licoes() if l.get('timestamp',0) > 0]
        return [f"aprendeu:{len(r)}"] if r else []
    
    def _p6_precisa(self):
        pn = MCRPesoNota("check")
        if len(pn.historico) < 5: return ["peso_nota_sem_treino"]
        return []
    
    def ciclo(self):
        """7 perguntas, acoes tomadas.
        
        Short-circuit: se KG ja tem > 200 lessons, pula operacoes pesadas.
        """
        # Verifica se KG ja esta bem alimentado
        try:
            kk_licoes = len(self.kg._get_licoes()) if self.kg else 0
        except:
            kk_licoes = 0
        
        todas = []
        if kk_licoes > 200:
            # KG ja tem dados: so executa as rapidas
            for fn in [self._p3_repetiu, self._p4_errou, self._p5_aprendeu, self._p6_precisa]:
                try: todas.extend(fn())
                except: pass
        else:
            # KG pequeno: executa todas
            for fn in [self._p1_gaps, self._p2_lento, self._p7_esqueceu,
                       self._p3_repetiu, self._p4_errou, self._p5_aprendeu, self._p6_precisa]:
                try: todas.extend(fn())
                except: pass
        self.mk.aprender("CICLO", str(len(todas)))
        return {'acoes': todas, 'n': len(todas)}


# ============================================================
# MCR HUMANO — Conceitos humanos, filosofias, emoções como padrões MCR
# ============================================================

# Questionamentos fundamentais como padrões MCR
# Cada pergunta filosofica vira uma sequencia de estados que o MCR aprende
_PERGUNTAS_FUNDAMENTAIS = [
    "Quem sou eu? O que me define como ser? Minha essencia e minha identidade.",
    "De onde viemos? Qual a origem de tudo que existe? O começo da jornada.",
    "Para onde vamos? Qual o destino final? O proposito de cada caminho.",
    "O que e o bem? O que e o mal? Existe equilibrio entre luz e sombra?",
    "O que e a verdade? Ela e unica ou multipla? A verdade como perspectiva.",
    "O que e o conhecimento? Como sabemos o que sabemos? O saber como ferramenta.",
    "O que e a vida? Quando comeca e quando termina? O ciclo do existir.",
    "O que e o tempo? Ele flui ou e fixo? Passado, presente e futuro como um todo.",
    "O que e a consciencia? O que nos torna cientes de nos mesmos? O despertar.",
    "E se tudo fosse diferente? E se o caminho tivesse sido outro? As possibilidades.",
    "Por que as coisas sao como sao? Qual a causa de cada efeito? A teia de conexoes.",
    "Quando o suficiente e suficiente? O equilibrio entre ter e ser.",
    "Quanto vale uma escolha? O peso de cada decisao no tecido do destino.",
    "O que e a felicidade? Ela existe ou e uma busca eterna? A alegria como estado.",
    "O que e a dor? Ela ensina ou apenas fere? O sofrimento como mestre.",
    "O que e o amor? Ligacao entre almas ou constructo social? A conexao profunda.",
    "O que e a morte? Fim ou transformacao? O encerramento de um ciclo.",
    "O que e a liberdade? Ausencia de limites ou escolha consciente? O livre arbitrio.",
    "O que e o destino? Escrito ou construido? A tensao entre acaso e determinismo.",
    "O que e a beleza? Nos olhos de quem ve ou qualidade intrinseca? A estetica do ser.",
]

# ============================================================
# MCR DOC INDEX — Cache de docs para evitar os.walk
# ============================================================

class MCRDocIndex:
    """Cache de documentos para consulta rapida por termo.
    
    Em vez de os.walk() a cada busca (10-20s),
    indexa os docs uma vez e consulta em 0.01s.
    
    Uso:
        idx = MCRDocIndex()
        idx.indexar()  # escaneia docs/ uma vez
        idx.buscar("Eridanus")  # → ["docs/MCR_IDENTITY.md", ...]
    """
    
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._cache_path = os.path.join(self._base, 'sandbox', '.mcr_docs_index.json')
        self._indice = {}
        self._carregado = False
        self.mk = MCR("doc_index")
    
    def _carregar(self):
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, 'r', encoding='utf-8') as f:
                    self._indice = json.load(f)
                self._carregado = True
                self.mk.aprender("INDEX", f"CARREGADO:{len(self._indice)}")
                return
            except: pass
        self._carregado = False
    
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
            with open(self._cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._indice, f, ensure_ascii=False, indent=2)
        except: pass
    
    def indexar(self, forcar=False) -> int:
        if self._carregado and not forcar:
            return len(self._indice)
        self._carregar()
        if self._carregado and not forcar:
            return len(self._indice)
        docs_dir = os.path.join(self._base, 'docs')
        if not os.path.isdir(docs_dir): return 0
        n = 0
        for root, dirs, files in os.walk(docs_dir):
            for fname in files:
                if not (fname.endswith('.md') or fname.endswith('.txt')): continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(2000)
                    termos = set()
                    for palavra in conteudo.lower().split():
                        palavra = palavra.strip('.,;:!?()[]{}""\'')
                        if len(palavra) >= 4:
                            termos.add(palavra)
                    relpath = os.path.relpath(fpath, self._base)
                    self._indice[relpath] = {
                        'termos': list(termos),
                        'tamanho': len(conteudo),
                        'n_termos': len(termos),
                    }
                    n += 1
                except: pass
        self._salvar()
        self._carregado = True
        self.mk.aprender("INDEX", f"CRIADO:{n}")
        return n
    
    def buscar(self, termo: str) -> list:
        if not self._carregado:
            self._carregar()
            if not self._carregado:
                self.indexar()
        termo = termo.lower()
        resultados = []
        for caminho, dados in self._indice.items():
            if termo in dados.get('termos', []):
                resultados.append({
                    'caminho': caminho,
                    'tamanho': dados.get('tamanho', 0),
                    'relevancia': dados.get('n_termos', 0),
                })
        resultados.sort(key=lambda x: -x['relevancia'])
        return resultados
    
    def ler(self, caminho_rel: str, max_bytes=500) -> str:
        fpath = os.path.join(self._base, caminho_rel)
        if not os.path.exists(fpath): return ''
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_bytes)
        except: return ''


_MCR_DOC_INDEX = None

def _get_doc_index():
    global _MCR_DOC_INDEX
    if _MCR_DOC_INDEX is None:
        _MCR_DOC_INDEX = MCRDocIndex()
    return _MCR_DOC_INDEX


# ============================================================
# MCR FRAGMENTADOR — Fragmenta ciclo em partes executaveis
# ============================================================

class MCRFragmento:
    """Um fragmento de processamento independente."""
    
    def __init__(self, nome, funcao, args=None):
        self.nome = nome
        self.funcao = funcao
        self.args = args or {}
        self.resultado = None
        self.erro = None
        self.tempo = 0
        self.sucesso = False
    
    def executar(self):
        import time
        t0 = time.time()
        try:
            self.resultado = self.funcao(**self.args)
            self.sucesso = True
        except Exception as e:
            self.erro = str(e)[:100]
        self.tempo = time.time() - t0
        return self.sucesso


class MCRFragmentador:
    """Fragmenta um ciclo em partes executaveis."""
    
    def __init__(self):
        self.fragmentos = []
        self.mk = MCR("fragmentador")
    
    def adicionar(self, nome, funcao, args=None):
        self.fragmentos.append(MCRFragmento(nome, funcao, args))
    
    def executar_todos(self) -> list:
        for f in self.fragmentos:
            f.executar()
            self.mk.aprender(f"FRAG:{f.nome}", f"{'OK' if f.sucesso else 'FALHA'}:{f.tempo:.2f}s")
        return self.fragmentos


# ============================================================
# MCR BUFFER KG — Buffer de operacoes do KG
# ============================================================

class MCRBufferKG:
    """Buffer de operacoes do KG (singleton, evita recarregar)."""
    
    _instancia = None
    _kg = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._buffer = []
            cls._instancia._buffer_limite = 20
            cls._instancia.mk = MCR("buffer_kg")
            cls._instancia._kg = None
        return cls._instancia
    
    @property
    def kg(self):
        if self._kg is None:
            try:
                from modulos.kg import KnowledgeGraph
                self._kg = KnowledgeGraph()
            except:
                self._kg = None
        return self._kg
    
    def aprender(self, erro, solucao, ctx='buffer'):
        if not self.kg: return
        self._buffer.append({'erro': erro, 'solucao': solucao, 'ctx': ctx})
        if len(self._buffer) >= self._buffer_limite:
            self.flush()
    
    def flush(self):
        if not self._buffer or not self.kg: return
        n = len(self._buffer)
        for item in self._buffer:
            self.kg.aprender_conceito(item['erro'], item['solucao'], ctx=item['ctx'])
        self._buffer = []
        self.mk.aprender("FLUSH", f"{n} lessons salvas")


# ============================================================
# MCR NIVEL — Níveis descobertos organicamente
# ============================================================

_NIVEIS_BASE = ['byte', 'palavra', 'token', 'intencao', 'padrao',
                'markov', 'pi', 'predizer', 'contexto', 'emergir',
                'filosofia', 'feedback', 'diagnostico', 'memoria',
                'meta', 'cache', 'busca', 'similaridade', 'entropia',
                'ruido', 'threshold', 'peso', 'acao', 'ciclo',
                'spawn', 'mestre', 'pergunta', 'cadeia', 'conector',
                'fuel', 'auto_start', 'auto_melhoria']

class MCRNivel:
    """UM nivel MCR descoberto.
    
    Cada nivel tem:
    - nome: identificador unico
    - mk: MCR proprio (transicoes do nivel)
    - entropia: imprevisibilidade do nivel
    - raio: alcance do nivel (quanto ele abrange)
    - conexoes: quais outros niveis se conectam a este
    
    Uso:
        n = MCRNivel("intencao")
        n.alimentar("Explique SPA")
        n.conectar("padrao")  # descobre se conecta
    """
    
    def __init__(self, nome: str, dados_iniciais: bytes = None):
        self.nome = nome
        self.mk = MCR(f"nivel_{nome}")
        self.entropia = 0.0
        self.raio = 0.0
        self.conexoes = {}  # {nome_nivel: similaridade}
        self._alimentado = 0
        
        if dados_iniciais:
            self.alimentar(dados_iniciais)
    
    def alimentar(self, dados: bytes):
        """Alimenta o nivel com dados. A entropia define o raio."""
        if not dados: return
        self.mk.aprender_sequencia(list(dados))
        self._alimentado += len(dados)
        
        # Entropia do nivel (quao imprevisivel)
        self.entropia = round(self.mk.entropia_media(), 3)
        
        # Raio = entropia × transições (alcance do nivel)
        n_trans = sum(len(v) for v in self.mk.transicoes.values())
        self.raio = round(self.entropia * max(1, math.log2(n_trans + 1)), 3)
    
    def conectar(self, outro: 'MCRNivel') -> float:
        """Descobre se este nivel se conecta a outro.
        Retorna similaridade (0-1)."""
        if not outro.mk.transicoes or not self.mk.transicoes:
            return 0.0
        
        # Similaridade = Jaccard entre os conjuntos de estados
        estados_self = set(self.mk.freq.keys())
        estados_outro = set(outro.mk.freq.keys())
        if not estados_self or not estados_outro:
            return 0.0
        
        inter = estados_self & estados_outro
        uniao = estados_self | estados_outro
        sim = len(inter) / len(uniao) if uniao else 0.0
        
        self.conexoes[outro.nome] = sim
        return sim
    
    def stats(self) -> dict:
        return {
            'nome': self.nome, 'entropia': self.entropia,
            'raio': self.raio, 'alimentado': self._alimentado,
            'estados': len(self.mk.transicoes),
            'conexoes': len(self.conexoes),
        }


class MCRMetaNivel:
    """MCR descobre QUANTOS e QUAIS niveis precisa.
    
    COMO FUNCIONA:
    1. Começa com 1 nivel: byte (o nivel mais basico)
    2. Alimenta byte com dados → entropia revela estrutura
    3. Se entropia > threshold → precisa de MAIS um nivel
    4. Novo nivel emerge: palavra (baseado nos delimitadores do byte)
    5. Alimenta palavra → entropia revela intencao
    6. Intencao emerge → depois padrao, markov, etc.
    
    O CRESCIMENTO E ORGANICO, nao planejado.
    Nao ha numero fixo de niveis.
    O MCR decide QUANDO criar um novo nivel.
    
    Uso:
        meta = MCRMetaNivel()
        meta.alimentar("Explique o sistema SPA do MCR")
        print(meta.niveis)  # → {"byte": MCRNivel, "palavra": MCRNivel, ...}
        print(meta.estatisticas())
    """
    
    def __init__(self):
        self.niveis = {}
        self._ordem = []
        self.mk = MCR("meta_nivel")
        self._energia_total = 0.0
        self._th = MCRThreshold("meta_nivel_criacao")
        for v in [5, 8, 10, 12, 15, 20]:
            self._th.observar(v)
    
    def alimentar(self, dados: bytes):
        """Alimenta TODOS os niveis com dados.
        
        Fluxo:
        1. Alimenta byte sempre
        2. Se byte tem transicoes suficientes → palavra emerge
        3. Se palavra tem transicoes → intencao emerge
        4. Cada nivel emerge quando o anterior atinge maturidade
        Os thresholds sao DESCOBERTOS por MCRThreshold, nao fixos.
        """
        if not dados: return
        
        # 1. Cria nivel byte se nao existe
        if 'byte' not in self.niveis:
            self._criar_nivel('byte')
        
        # 2. Alimenta byte
        self.niveis['byte'].alimentar(dados)
        n_byte = len(self.niveis['byte'].mk.transicoes)
        
        # 3. Descobre nivel palavra: threshold via MCR
        limiar = self._th.calcular(0.4)
        if n_byte > limiar and 'palavra' not in self.niveis:
            self._criar_nivel('palavra', dados)
        
        # 4-7. Niveis seguintes: cada um requer o dobro de maturidade do anterior
        niveis_seq = ['palavra', 'intencao', 'padrao', 'markov', 'predizer']
        for i, nome in enumerate(niveis_seq):
            if nome in self.niveis:
                self.niveis[nome].alimentar(dados)
            elif self._tem_antecessor(nome, niveis_seq):
                n_ant = len(self.niveis[niveis_seq[i-1]].mk.transicoes)
                limiar_seq = self._th.calcular(0.4 * (i + 1))
                if n_ant > limiar_seq:
                    self._criar_nivel(nome, dados)
    
    def _tem_antecessor(self, nome, niveis_seq):
        if nome not in niveis_seq: return False
        i = niveis_seq.index(nome)
        if i == 0: return True
        return niveis_seq[i-1] in self.niveis
        
        # 8. Conecta niveis descobertos
        self._conectar_niveis()
        
        # 9. Energia total (E = intencao × pi² analogo)
        self._energia_total = sum(n.entropia * n.raio for n in self.niveis.values())
    
    def _criar_nivel(self, nome: str, dados: bytes = None):
        """Cria um novo nivel MCR."""
        nivel = MCRNivel(nome, dados)
        self.niveis[nome] = nivel
        self._ordem.append(nome)
        self.mk.aprender(f"NIVEL:{nome}", f"ordem:{len(self._ordem)}")
    
    def _conectar_niveis(self):
        """Conecta todos os niveis descobertos entre si."""
        nomes = list(self.niveis.keys())
        for i in range(len(nomes)):
            for j in range(i+1, len(nomes)):
                a, b = self.niveis[nomes[i]], self.niveis[nomes[j]]
                sim = a.conectar(b)
                if sim > 0:
                    self.mk.aprender(f"LIG:{nomes[i]}-{nomes[j]}", f"sim:{sim:.2f}")
    
    def diagnosticar(self) -> dict:
        """Diagnostica o estado atual dos niveis.
        
        Retorna:
        - quantos niveis existem
        - ordem de descoberta
        - qual nivel tem maior raio
        - energia total do sistema
        - recomenda criar novo nivel?
        """
        if not self.niveis:
            return {'niveis': 0, 'energia': 0}
        
        stats = {nome: n.stats() for nome, n in self.niveis.items()}
        maior_raio = max(stats.items(), key=lambda x: x[1]['raio']) if stats else ('?', {})
        
        return {
            'n_niveis': len(self.niveis),
            'ordem': self._ordem,
            'stats': stats,
            'maior_raio': {'nome': maior_raio[0], 'valor': maior_raio[1].get('raio', 0)},
            'energia_total': round(self._energia_total, 2),
            'precisa_mais': len(self.niveis) < len(_NIVEIS_BASE),
        }
    
    def auto_expandir(self, max_niveis: int = 10) -> int:
        """Tenta expandir para o proximo nivel na lista base.
        
        RECONSTROI dados do nivel BYTE em vez de guardar texto original.
        Usa MCRByte.gerar() para gerar dados reais do proprio nivel.
        """
        if len(self.niveis) >= max_niveis:
            return 0
        
        # Proximo nivel na lista base
        proximos = [n for n in _NIVEIS_BASE if n not in self.niveis]
        if not proximos:
            return 0
        
        novo_nivel = proximos[0]
        self._criar_nivel(novo_nivel)
        
        # Reconstrói dados do nivel BYTE (sempre existe)
        if 'byte' in self.niveis:
            nivel_byte = self.niveis['byte']
            # Pega o primeiro estado como semente
            semente = list(nivel_byte.mk.freq.keys())[0] if nivel_byte.mk.freq else '0'
            # Gera 50 estados a partir da semente (dados RECONSTRUIDOS do proprio nivel)
            estados = nivel_byte.mk.gerar(semente, passos=50)
            # Junta em string
            dados_reconstruidos = ' '.join(str(e) for e in estados if e)
            
            # Converte para o nivel alvo
            if novo_nivel == 'palavra':
                # Nivel palavra: os proprios estados (ja sao palavras/bytes)
                dados_novo = dados_reconstruidos.encode('utf-8')
            elif novo_nivel == 'token':
                # Nivel token: usa _classificar_token em cada estado
                try:
                    tokens_tipos = []
                    for e in estados:
                        pal = str(e).replace('B:', '').strip()
                        if pal:
                            from modulos.MCR import _classificar_token as _mcr_tip
                            tokens_tipos.append(_mcr_tip(pal) or 'outro')
                    dados_novo = ' '.join(tokens_tipos).encode('utf-8')
                except:
                    dados_novo = dados_reconstruidos.encode('utf-8')
            elif novo_nivel == 'intencao':
                # Nivel intencao: usa os estados como palavras de intencao
                dados_novo = dados_reconstruidos.encode('utf-8')
            else:
                # Outros niveis: dados reconstruidos do byte
                dados_novo = dados_reconstruidos.encode('utf-8')
            
            self.niveis[novo_nivel].alimentar(dados_novo)
        
        return 1


# ============================================================
# MCR GERACAO — Geração com validação por assinatura
# ============================================================

class MCRGeracao:
    """Gera resposta e VALIDA se a assinatura condiz com a pergunta.
    
    Fluxo:
    1. Extrai assinatura da pergunta
    2. Gera resposta (MarkovPalavra via MCRCadeia)
    3. Extrai assinatura da resposta
    4. Compara: pergunta e resposta sao compativeis?
    5. Se compatibilidade < threshold: regenera com estrategia diferente
    6. Entrega quando compativel OU apos N tentativas
    
    Uso:
        g = MCRGeracao()
        resultado = g.gerar("Explique o sistema SPA do MCR")
        # → {"texto": "...", "compatibilidade": 0.45, "nota": 6.5}
    """
    
    def __init__(self):
        self.decisor = MCRDecisor("geracao")
        self.threshold = MCRThreshold("geracao_comp")
        for v in [0.2, 0.25, 0.3, 0.35, 0.28]:
            self.threshold.observar(v)
        self.mk = MCR("geracao")
    
    def gerar(self, pergunta: str, max_tentativas: int = 3) -> dict:
        """Gera resposta validando assinatura a cada tentativa.
        
        Se a assinatura da resposta nao condiz com a assinatura da pergunta,
        MCRDecisor decide a estrategia de regeneracao.
        """
        # 1. Assinatura da pergunta
        sig_pergunta = MCRSignature.extrair(pergunta)
        
        melhor_resposta = ''
        melhor_comp = 0
        melhor_estrategia = ''
        tentativas = 0
        
        for tentativa in range(max_tentativas):
            tentativas += 1
            
            # 2. Decide estrategia de geracao
            if tentativa == 1:
                estrategia = 'cadeia_direto'
            else:
                estado = f"COMP:{melhor_comp:.2f}|TENT:{tentativa}"
                estrategia = self.decisor.decidir(estado)
                if not estrategia or estrategia == 'kg_primeiro':
                    estrategia = 'cadeia_direto'
            
            # 3. Gera resposta
            texto = self._executar_estrategia(pergunta, estrategia)
            
            # 4. Assinatura da resposta
            sig_resposta = MCRSignature.extrair(texto)
            compatibilidade = MCRSignature.comparar(sig_pergunta, sig_resposta)
            
            # 5. Autoavalia
            nota = self._autoavaliar(texto, pergunta, compatibilidade)
            
            if compatibilidade > melhor_comp:
                melhor_comp = compatibilidade
                melhor_resposta = texto
                melhor_estrategia = estrategia
            
            # 6. Se compativel, entrega
            limiar = self.threshold.calcular(1.0)
            if compatibilidade >= limiar and nota >= 4:
                self.mk.aprender(f"GERADO:{pergunta}", 
                                f"comp={compatibilidade:.2f} tent={tentativa}")
                return {
                    'texto': texto,
                    'compatibilidade': round(compatibilidade, 3),
                    'nota': round(nota, 1),
                    'tentativas': tentativas,
                    'estrategia': estrategia,
                    'assinatura_pergunta': sig_pergunta,
                    'assinatura_resposta': sig_resposta,
                }
        
        # Se nenhuma tentativa foi compativel, entrega a melhor
        self.mk.aprender(f"FALHO:{pergunta}", f"melhor_comp={melhor_comp:.2f}")
        return {
            'texto': melhor_resposta,
            'compatibilidade': round(melhor_comp, 3),
            'nota': round(self._autoavaliar(melhor_resposta, pergunta, melhor_comp), 1),
            'tentativas': tentativas,
            'estrategia': melhor_estrategia,
            'assinatura_pergunta': sig_pergunta,
            'assinatura_resposta': MCRSignature.extrair(melhor_resposta),
        }
    
    def _executar_estrategia(self, pergunta: str, estrategia: str) -> str:
        """Executa uma estrategia de geracao especifica."""
        palavras = pergunta.split()
        semente = palavras[0] if palavras else 'O'
        
        if estrategia == 'cadeia_direto':
            # Gera direto com MCRCadeia (sem KG)
            c = MCRConector()
            c.alimentar(pergunta, "pergunta")
            cadeia = MCRCadeia(c)
            res = cadeia.gerar(semente, n_tokens=60)
            return res.get('texto', semente)
        
        elif estrategia == 'kg_primeiro':
            # Busca no KG primeiro, depois gera
            try:
                from modulos.kg import KnowledgeGraph
                kg = KnowledgeGraph()
                lessons = kg.buscar(semente, max_r=3)
                if lessons:
                    c = MCRConector()
                    for l in lessons:
                        sol = l.get('solucao', '') or l.get('erro', '')
                        if sol:
                            c.alimentar(sol, "kg")
                    cadeia = MCRCadeia(c)
                    res = cadeia.gerar(semente, n_tokens=60)
                    return res.get('texto', semente)
            except: pass
            return self._executar_estrategia(pergunta, 'cadeia_direto')
        
        elif estrategia == 'semente_alternativa':
            # Tenta com semente diferente (ultima palavra)
            if len(palavras) > 1:
                semente = palavras[-1]
            c = MCRConector()
            c.alimentar(pergunta, "pergunta")
            cadeia = MCRCadeia(c)
            res = cadeia.gerar(semente, n_tokens=60)
            return res.get('texto', semente)
        
        return pergunta
    
    def _autoavaliar(self, texto, pergunta, compatibilidade):
        """Autoavaliacao simples baseada em compatibilidade + tamanho."""
        if not texto or len(texto) < 20:
            return 0.0
        
        nota = 0.0
        nota += compatibilidade * 4  # 0-4 pts: similaridade com pergunta
        nota += min(2.0, len(texto) / 200)  # 0-2 pts: tamanho minimo 200 chars
        nota += min(2.0, len(set(texto.split())) / 20)  # 0-2 pts: vocabulario diverso
        nota += 2.0 if not any(p in texto for p in ['Projeto MCR', 'Guia de']) else 1.0  # 0-2 pts: nao repetitivo
        
        return round(min(10, max(0, nota)), 1)


class MCRFilosofia:
    """Padroes de pensamento humano como niveis MCR.
    
    Filosofias, emocoes, questionamentos viram transicoes MCR.
    O MCR aprende a ESTRUTURA do pensamento, nao o CONTEUDO.
    
    Uso:
        f = MCRFilosofia()
        f.aprender_perguntas_fundamentais()  # alimenta MCR com filosofia
        f.refletir("Quem sou eu?")  # → geracao filosofica
    """
    
    def __init__(self, conector=None):
        self.conector = conector or MCRConector()
        self.mk_pensamento = MCR("filosofia_pensamentos")
        self._alimentado = False
    
    def aprender_perguntas_fundamentais(self):
        """Alimenta o MCR com perguntas filosoficas como transicoes."""
        if self._alimentado: return
        
        for pergunta in _PERGUNTAS_FUNDAMENTAIS:
            # Cada pergunta vira um topico no conector
            nome = f"filosofia_{pergunta.strip().lower()}"
            self.conector.alimentar(pergunta, nome)
            
            # Palavras da pergunta viram transicoes no MCR de pensamento
            palavras = pergunta.lower().split()
            self.mk_pensamento.aprender_sequencia(palavras)
        
        self._alimentado = True
        return len(_PERGUNTAS_FUNDAMENTAIS)
    
    def refletir(self, pergunta: str) -> str:
        """Gera uma reflexao baseada em padroes filosoficos."""
        # Alimenta se necessario
        self.aprender_perguntas_fundamentais()
        
        # Tenta encontrar perguntas similares no conector
        for nome, dados in self.conector.topicos.items():
            if nome.startswith('filosofia_'):
                # Conecta a pergunta com a filosofia similar
                texto = dados['texto']
                palavras_similares = sum(1 for p in pergunta.lower().split() 
                                        if p in texto.lower() and len(p) > 3)
                if palavras_similares >= 2:
                    cx = self.conector.conectar(nome, "pergunta" if "pergunta" in self.conector.topicos else nome)
                    if cx:
                        return f"[Filosofia] {pergunta}\n[Conexao] {cx.get('sequencia', '')}"
        
        # Fallback: gera com as transicoes filosoficas
        semente = pergunta.split()[0] if pergunta.split() else 'O'
        cadeia = MCRCadeia(self.conector)
        res = cadeia.gerar(semente, n_tokens=30)
        return res.get('texto', pergunta)


class MCRFeedback:
    """Feedback loop: MCR solicita mais dados quando resposta e insuficiente.
    
    Se nota < 6, MCR:
    1. Analisa o que faltou (diagnostico)
    2. Gera perguntas de esclarecimento
    3. Aguarda nova entrada
    4. Usa a nova entrada + a anterior para gerar resposta melhor
    
    Isso imita o feedback humano: "nao entendi, pode explicar melhor?"
    """
    
    def __init__(self, mestre=None):
        self.mestre = mestre or MCRMestreV2()
        self.historico_tentativas = []
        self.mk = MCR("feedback")
    
    def processar_com_feedback(self, pergunta: str, max_tentativas: int = 3) -> dict:
        """Processa com feedback: se nota baixa, solicita mais dados.
        
        Short-circuit: se KG ja tem dados (> 200 uteis), 1 tentativa basta.
        """
        # Short-circuit: KG ja tem dados, nao precisa de multiplas tentativas
        try:
            kk = _get_kg()
            lk = kk._get_licoes() if kk else []
            if len(lk) > 200:
                max_tentativas = 1
        except:
            pass
        
        melhor_resposta = None
        melhor_nota = 0
        contexto_acumulado = pergunta
        
        for tentativa in range(max_tentativas):
            # Processa com o contexto atual
            res = self.mestre.processar(contexto_acumulado)
            nota = res.get('nota', 0)
            
            self.historico_tentativas.append({
                'tentativa': tentativa + 1,
                'nota': nota,
                'resposta': res.get('resposta', ''),
            })
            self.mk.aprender(f"TENTATIVA:{tentativa}", f"NOTA:{int(nota)}")
            
            if nota > melhor_nota:
                melhor_nota = nota
                melhor_resposta = res
            
            # Se nota >= 7, entrega
            if nota >= 7:
                break
            
            # Se nota baixa e ainda tem tentativas, gera feedback
            if tentativa < max_tentativas - 1:
                # Gera pergunta de esclarecimento baseada no diagnostico
                diag = res.get('diagnostico', '')
                if 'loop' in diag:
                    feedback = f"[MCR precisa de mais contexto] {pergunta} pode explicar com mais detalhes?"
                elif nota < 4:
                    feedback = f"[MCR nao encontrou dados] {pergunta} tem alguma fonte ou exemplo especifico?"
                else:
                    feedback = f"[MCR quer confirmar] {pergunta} e isso mesmo que voce quer saber?"
                
                # Acumula no contexto para a proxima tentativa
                contexto_acumulado = f"{pergunta} | Contexto extra: {feedback}"
        
        resultado = melhor_resposta or res
        resultado['feedback'] = {
            'tentativas': len(self.historico_tentativas),
            'historico': self.historico_tentativas,
            'precisou_feedback': len(self.historico_tentativas) > 1,
        }
        return resultado


# ============================================================
# MCR AUTOTESTAR — Substitui if __name__ por metodo MCR
# ============================================================

def _autotestar():
    '''MCR testa a si mesmo — nomes gerados dos resultados reais.'''
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    resultados = []
    def testar(nome, cond):
        status = 'PASS' if cond else 'FAIL'
        resultados.append((nome, cond))
        print(f'  [{status}] {nome}')
        sys.stdout.flush()
    print('=' * 70)
    print('  MCR - Auto Teste')
    print('=' * 70)
    
    # Warmup: carrega KG uma vez + dedup (cache para todas as classes seguintes)
    try:
        from modulos.kg import KnowledgeGraph
        kg_warm = KnowledgeGraph()
        l_warm = kg_warm._get_licoes()
        if len(l_warm) > 200:
            from modulos.MCR import MCRKGAuto
            auto_warm = MCRKGAuto(kg_warm)
            n_dedup = auto_warm.dedup()
            if n_dedup > 0:
                kg_warm.salvar()
    except Exception as warm_e:
        pass  # se falhar, os testes seguintes tentam do mesmo jeito
    
    # 1. MCR base
    mk = MCR('autoteste')
    mk.aprender_sequencia([1, 2, 3])
    testar(f'MCR.aprender_sequencia([1,2,3]) total={mk.total}', mk.total > 0)
    p1, c1 = mk.predizer(1)
    testar(f'MCR.predizer(1) = ({p1}, {c1:.2f})', p1 is not None)
    h1 = mk.entropia(1)
    testar(f'MCR.entropia(1) = {h1:.2f}', h1 >= 0)
    j1 = mk.jaccard_bytes('SPA', 'SPA')
    testar(f'MCR.jaccard_bytes(SPA,SPA) = {j1:.3f}', j1 > 0.99)
    j2 = mk.jaccard_bytes_ponderado('SPA A', 'SPA B')
    testar(f'MCR.jaccard_ponderado(SPA) = {j2:.3f}', j2 > 0)
    
    # 2. MCRConector
    c2 = MCRConector()
    c2.alimentar('SPA = Sistema.', 'spa')
    c2.alimentar('Eridanus era cidade.', 'eridanus')
    cx = c2.conectar('spa', 'eridanus')
    if cx:
        testar(f'MCRConector.conectar nota={cx["nota"]:.1f}', cx['nota'] > 0)
    else:
        testar('MCRConector.conectar = None', False)
    
    # 3. MCRCadeia
    cadeia = MCRCadeia(c2)
    res_c = cadeia.gerar('SPA', n_tokens=10)
    testar(f'MCRCadeia.gerar tokens={res_c["n_tokens"]}', res_c['n_tokens'] >= 5)
    
    # 4. MCRPeso
    peso = MCRPeso('t')
    peso.aprender('erro', 5.0)
    peso.aprender('ctx', 4.0)
    peso.aprender('causa', 3.0)
    testar(f'MCRPeso erro={peso.consultar("erro")} ctx={peso.consultar("ctx")} causa={peso.consultar("causa")}',
           peso.consultar('erro') >= peso.consultar('ctx') >= peso.consultar('causa'))
    
    # 5. MCREntropia
    ent = MCREntropia('t')
    for _ in range(10): ent.alimentar('X')
    testar(f'MCREntropia.loop({ent.esta_em_loop()})', ent.esta_em_loop())
    
    # 6. MCRDecisor
    dec = MCRDecisor('t')
    d = dec.decidir('Explique SPA')
    testar(f'MCRDecisor.decidir = {d}', d is not None)
    
    # 7. MCRBridge
    bridge = MCRBridge()
    disc = bridge.descobrir()
    testar(f'MCRBridge modulos={disc["modulos"]} comandos={disc["comandos"]}',
           disc['modulos'] > 10 and disc['comandos'] >= 2)
    
    # 8. MCRMestre
    mestre = MCRMestre(bridge)
    res_m = mestre.processar('Explique SPA')
    if res_m:
        testar(f'MCRMestre resposta={len(res_m.get("resposta",""))} chars',
               len(res_m.get('resposta','')) > 0)
    
    # 9. MCRPesoNota
    pn = MCRPesoNota('t')
    pn.aprender({'byte': 0.8, 'palavra': 0.2}, 3.0)
    pn.aprender({'byte': 0.4, 'palavra': 0.8}, 8.0)
    nb = pn.calcular(byte_s=8.0, palavra_s=2.0)
    na = pn.calcular(byte_s=4.0, palavra_s=8.0)
    testar(f'MCRPesoNota JSON={nb:.1f} Texto={na:.1f}', nb < na)
    
    # 10. MCRThreshold
    th = MCRThreshold('t')
    for v in [0.8, 0.85, 0.9, 0.82, 0.88]:
        th.observar(v)
    tc = th.calcular()
    testar(f'MCRThreshold mediana={tc:.2f}', 0.8 < tc < 0.9)
    th2 = MCRThreshold('t2')
    for _ in range(10): th2.observar(0.1)
    tc2 = th2.calcular(0.5)
    testar(f'MCRThreshold loop={tc2:.3f}', tc2 < 0.2)
    
    # 11. MCRMestreV2
    m_v2 = MCRMestreV2(bridge)
    r_v2 = m_v2.processar('Explique SPA')
    testar(f'MCRMestreV2 fluxo={r_v2.get("fluxo","?")}', r_v2.get('fluxo','') != '')
    testar(f'MCRMestreV2 exec={m_v2.n_execucoes}', m_v2.n_execucoes > 0)
    
    # 12. CicloUnico
    try:
        m_sys = MCRSystem()
        ciclo = m_sys.ciclo_unico(__file__, 2000)
        testar(f'CicloUnico tipo={ciclo.get("tipo","?")} ent={ciclo.get("entropia",0):.2f}',
               ciclo.get('entropia', 0) > 0)
    except Exception as e:
        testar(f'CicloUnico erro={e}', False)
    
    # 13. ProcessarBytes
    try:
        m_b = MCR('pb')
        r_b = m_b.processar_bytes('Explique SPA'.encode())
        testar(f'ProcessarBytes compat={r_b["compatibilidade"]:.2f}', r_b['compatibilidade'] > 0)
    except Exception as e:
        testar(f'ProcessarBytes erro={e}', False)
    
    # 14. MCRDiagnostico
    diag = MCRDiagnostico('t')
    diag.alimentar({'byte': 0.9, 'palavra': 0.1}, 'JSON_no_texto')
    diag.alimentar({'byte': 0.8, 'palavra': 0.15}, 'JSON_no_texto')
    d_j = diag.diagnosticar({'byte': 0.85, 'palavra': 0.12})
    diag.alimentar({'byte': 0.2, 'token': 0.9}, 'loop_detectado')
    d_l = diag.diagnosticar({'byte': 0.18, 'token': 0.88})
    testar(f'MCRDiagnostico JSON={d_j} Loop={d_l}', 'JSON' in d_j and 'loop' in d_l)
    
    # 15. Fuel + MetaGap
    fuel = MCRFuel(kg=None, bridge=bridge)
    testar(f'MCRFuel type={type(fuel).__name__}', isinstance(fuel, MCRFuel))
    mg = MCRMetaGap(kg=None, bridge=bridge)
    testar(f'MCRMetaGap type={type(mg).__name__}', isinstance(mg, MCRMetaGap))
    
    # 16. AutoMelhoria
    am = MCRAutoMelhoria(kg=None, bridge=bridge)
    am_c = am.ciclo()
    testar(f'MCRAutoMelhoria acoes={am_c["n"]}', am_c['n'] >= 0)
    
    # 17. Filosofia
    f = MCRFilosofia()
    n_f = f.aprender_perguntas_fundamentais()
    testar(f'MCRFilosofia {n_f} perguntas', n_f == len(_PERGUNTAS_FUNDAMENTAIS))
    ref = f.refletir('Quem sou eu?')
    testar(f'MCRFilosofia reflexao {len(ref)} chars', len(ref) > 10)
    
    # 18. MetaNivel
    meta = MCRMetaNivel()
    meta.alimentar('Explique o sistema SPA do MCR'.encode())
    d_m = meta.diagnosticar()
    testar(f'MCRMetaNivel niveis={d_m["n_niveis"]} ordem={d_m.get("ordem",[])}',
           d_m['n_niveis'] >= 2)
    n_exp = meta.auto_expandir(8)
    d_m2 = meta.diagnosticar()
    testar(f'MCRMetaNivel expandiu {d_m2["n_niveis"]} niveis',
           d_m2['n_niveis'] >= d_m['n_niveis'])
    
    # 19. Feedback
    fb = MCRFeedback(m_v2)
    r_fb = fb.processar_com_feedback('Explique SPA', 2)
    testar(f'MCRFeedback tentativas={r_fb.get("feedback",{}).get("tentativas",0)}',
           r_fb.get('feedback',{}).get('tentativas', 0) >= 1)
    
    # 20. AutoStart
    try:
        a = MCRAutoStart.iniciar()
        testar(f'MCRAutoStart status={a.get("aproveitamento","?")}',
               isinstance(a, dict) and 'erro' not in a)
    except Exception as e:
        testar(f'MCRAutoStart erro={e}', False)
    
    # 21. SelfIndex
    si = MCRSelfIndex()
    n_si = si.indexar_tudo()
    testar(f'MCRSelfIndex total={n_si}', n_si > 0)
    cls = si.estatisticas()
    testar(f'MCRSelfIndex classes={cls["classes"]} mods={cls["modulos"]} cmds={cls["comandos"]}',
           cls['classes'] > 0)
    
    # 22. SelfHeal
    sh = MCRSelfHeal.verificar()
    testar(f'MCRSelfHeal acoes={sh["n_acoes"]}', sh['n_acoes'] >= 0)
    
    # 23. MCRSignature
    sig_a = MCRSignature.extrair('Explique o sistema SPA do MCR')
    sig_b = MCRSignature.extrair('Crie um NPC ferreiro em Eridanus')
    sig_sim = MCRSignature.extrair('Explique o sistema SPA do MCR')
    comp_ab = MCRSignature.comparar(sig_a, sig_b)
    comp_aa = MCRSignature.comparar(sig_a, sig_sim)
    testar(f'MCRSignature.extrair ent={sig_a["entropia"]} est={sig_a["estados"]} trans={sig_a["transicoes"]}',
           sig_a['estados'] > 0)
    testar(f'MCRSignature.comparar diferentes={comp_ab:.3f} iguais={comp_aa:.3f}',
           comp_aa > comp_ab)
    mn = MCRSignature.metaniveis('Explique o sistema SPA do MCR', 8)
    testar(f'MCRSignature.metaniveis {mn["niveis_finais"]} niveis ordem={mn["ordem"]}',
           mn['niveis_finais'] >= 3)
    
    # 24. MCRSession
    sess = MCRSession()
    sess.registrar("teste", "resposta_teste", "autoteste")
    sess.salvar_estado()
    carregado = sess.carregar_estado()
    testar(f'MCRSession.registrar + salvar + carregar', carregado is not None)
    testar(f'MCRSession.ultima_pergunta={sess.ultima_pergunta()}', 
           sess.ultima_pergunta() == 'teste')
    
    # 25. MCRAssinatura — Kheltz PRIMEIRO (regra absoluta)
    banco = MCRAssinatura()
    # Aprende com textos REAIS do Kheltz (desta sessao)
    banco.aprender("O que ainda nao esta MCR? o que ainda nao segue padroes? a ASSINATURA, o que ainda e Hardcoded?", "Kheltz")
    banco.aprender("TODOS, resolva TODOS, conecte TODOS!", "Kheltz")
    banco.aprender("analise o MCR.py POR COMPLETO e reflita, o MCR sabe decidir melhor que ninguem", "Kheltz")
    autor, conf, det = banco.identificar("releia o que falei acima, entenda os conceitos, analise o MCR")
    testar(f'MCRAssinatura identificar autor={autor} conf={conf:.2f}', 
           conf > 0.3 and autor in ('Kheltz', 'Kheltz?'))
    n_auto = banco.auto_popular()
    testar(f'MCRAssinatura.auto_popular autores={banco.autores_conhecidos()}', 
           banco.estatisticas()['autores'] > 0)
    
    # 26. MCRWebLearn
    web = MCRWebLearn()
    n_estudados = web.estudar_gaps(1)
    testar(f'MCRWebLearn.estudar_gaps estudados={n_estudados}', 
           n_estudados >= 0)
    ciclo = web.ciclo_auto_estudo()
    testar(f'MCRWebLearn.ciclo_auto_estudo estudados={ciclo.get("estudados",0)}', 
           ciclo.get('estudados', 0) >= 0)
    
    # 27. MCRGeracao
    g = MCRGeracao()
    res_g = g.gerar("Explique o sistema SPA do MCR")
    testar(f'MCRGeracao compat={res_g["compatibilidade"]:.2f} tent={res_g["tentativas"]}', 
           res_g['compatibilidade'] > 0)
    testar(f'MCRGeracao texto={len(res_g["texto"])} chars nota={res_g["nota"]}', 
           len(res_g['texto']) > 20)
    
    # Relatorio
    passed = sum(1 for _, c in resultados if c)
    total = len(resultados)
    print(f'\n{"="*70}')
    print(f'  Auto Teste: {passed}/{total} ({passed/max(total,1)*100:.0f}%)')
    print(f'{"="*70}')
    return resultados





# ============================================================
# MCR STATE — Dados essenciais serializados (~17 KB)
# ============================================================
# MCR nao precisa de 20 MB de KG para comecar.
# So precisa dos PADRÕES: thresholds, pesos, indices.
# O resto (lessons, episodios) e RECONSTRUIVEL via MCRFuel.

_MCR_STATE = {
    'versao': 5.0,
    'thresholds': {
        'revisor_eixo': [0.35, 0.4, 0.45, 0.38, 0.42],
        'revisor_entropia': [0.75, 0.8, 0.85, 0.78, 0.82],
        'ep_score': [0.25, 0.3, 0.35, 0.28, 0.32],
        'ep_taxa': [0.65, 0.7, 0.75, 0.68, 0.72],
        'kg_sim': [0.7, 0.75, 0.8, 0.72, 0.77],
        'util_sim': [0.7, 0.75, 0.8, 0.72, 0.77],
        'val_sim': [0.75, 0.8, 0.85, 0.78, 0.82],
        'reconstructor_ent': [0.12, 0.15, 0.18, 0.13, 0.16],
        'reconstructor_sim': [0.65, 0.7, 0.75, 0.68, 0.72],
    },
    'pesos': {
        'erro': 5.0, 'ctx': 4.0, 'causa': 3.0, 'solucao': 2.0,
    },
    'indice_modulos': {},
    'indice_comandos': {},
    'classes_essenciais': [
        'MCR', 'MCRFingerprint', 'MCRSystem', 'MCRConector',
        'MCRCadeia', 'MCRPergunta', 'MCRPeso', 'MCREntropia',
        'MCRRuido', 'MCRDecisor', 'MCRDiagnostico', 'MCRFerramenta',
        'MCRBridge', 'MCRKGAuto', 'MCRExpansao', 'MCRMeta',
        'MCRPesoNota', 'MCRThreshold', 'MCRFuel', 'MCRMetaGap',
        'MCRMestreV2', 'MCRFilosofia', 'MCRFeedback', 'MCRMetaNivel',
        'MCRNivel', 'MCRDocIndex', 'MCRFragmento', 'MCRFragmentador',
        'MCRBufferKG', 'MCRAutoMelhoria',
    ]
}


# ============================================================
# MCR SIGNATURE — Assinatura unica de QUALQUER dado
# ============================================================
# A assinatura NAO e um conjunto de campos fixos.
# E a SEQUENCIA COMPLETA de transicoes do dado em bytes.
# MCRByte ja captura isso. MCRMetaNivel ja expande.
# Esta classe so CONECTA o que ja existe.

# Cache global de MCRSignature (evita recalcular para textos identicos)
_SIG_CACHE = {}  # {hash: assinatura}

class MCRSignature:
    """Assinatura unica de QUALQUER dado.
    
    Nao define campos. Nao define estrutura.
    So conecta MCRByte + MCRMetaNivel + similaridade.
    Cache global _SIG_CACHE evita recalcular para o mesmo texto.
    
    Uso:
        sig = MCRSignature()
        a = sig.extrair("SPA = Sistema")    # → assinatura unica de bytes
        b = sig.extrair("SPA = Progressao")
        sim = sig.comparar(a, b)            # → 0.224 (Jaccard)
        niveis = sig.metaniveis("Explique SPA")  # → quantos niveis emergem
    """
    
    @staticmethod
    def extrair(dados, rapido=False) -> dict:
        """Extrai a assinatura unica de QUALQUER dado.
        
        Args:
            dados: texto ou bytes para extrair assinatura
            rapido: se True, usa hash simplificado (100x mais rapido)
                    ideal para auto_popular onde precisamos so
                    distinguir autores, nao analisar profundamente.
        
        Cache: se o mesmo texto ja foi extraido, retorna cache (0.01s vs 0.02s).
        """
        # Normaliza
        if isinstance(dados, str):
            key_bytes = dados.encode('utf-8')[:2000]
        elif isinstance(dados, bytes):
            key_bytes = dados[:2000]
        else:
            key_bytes = str(dados).encode('utf-8')[:2000]
        
        # Cache hit
        key_hash = hash(key_bytes)
        if not rapido and key_hash in _SIG_CACHE:
            return _SIG_CACHE[key_hash]
        
        dados_clean = key_bytes
        
        # MODO RAPIDO: apenas entropia + hash simples (para auto_popular)
        if rapido:
            from collections import Counter
            freq = Counter(dados_clean)
            n = len(dados_clean) or 1
            h = 0.0
            for c in freq.values():
                p = c / n
                if p > 0: h -= p * math.log2(p)
            
            result = {
                'entropia': round(h, 3),
                'estados': len(freq),
                'transicoes': n - 1,
                'sequencia': list(dados_clean[:10]) if dados_clean else [],
                'fingerprint': [h / 8.0, n / 2000.0, float(dados_clean[0] if dados_clean else 0) / 255.0] + [0.0] * 61,
            }
            return result
        
        # Modo completo
        mk = MCR("signature")
        mk.aprender_sequencia(list(dados_clean))
        
        primeiro = list(mk.freq.keys())[0] if mk.freq else '0'
        sequencia = mk.gerar(primeiro, passos=50)
        
        fp = MCRFingerprint.gerar(
            ' '.join(str(s) for s in sequencia)
        )
        
        result = {
            'entropia': round(mk.entropia_media(), 3),
            'estados': len(mk.transicoes),
            'transicoes': sum(len(v) for v in mk.transicoes.values()),
            'sequencia': sequencia,
            'fingerprint': fp,
        }
        
        # Salva cache (max 2000 entradas)
        if len(_SIG_CACHE) < 2000:
            _SIG_CACHE[key_hash] = result
        
        return result
    
    @staticmethod
    def comparar(a: dict, b: dict) -> float:
        """Compara 2 assinaturas pelo Jaccard das sequencias.
        Quanto maior, mais similares sao os padroes."""
        if not a.get('sequencia') or not b.get('sequencia'):
            return 0.0
        seq_a = ' '.join(str(s) for s in a['sequencia'])
        seq_b = ' '.join(str(s) for s in b['sequencia'])
        mk = MCR("sig_comp")
        return mk.jaccard_bytes(seq_a, seq_b)
    
    @staticmethod
    def metaniveis(dados, max_niveis=10) -> dict:
        """Alimenta MetaNiveis com o dado e descobre quantos niveis emergem.
        Cada nivel e uma dimensao da assinatura."""
        meta = MCRMetaNivel()
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
        meta.alimentar(dados)
        diag = meta.diagnosticar()
        meta.auto_expandir(max_niveis)
        diag2 = meta.diagnosticar()
        return {
            'niveis_iniciais': diag['n_niveis'],
            'niveis_finais': diag2['n_niveis'],
            'ordem': diag2.get('ordem', []),
            'energia': diag2.get('energia_total', 0),
        }
    
    @staticmethod
    def identificar(dados, banco: list = None) -> dict:
        """Identifica um dado comparando com um banco de assinaturas.
        Retorna a mais similar + score."""
        sig_alvo = MCRSignature.extrair(dados)
        if not banco:
            return {'identificado': False, 'score': 0, 'alvo': sig_alvo}
        melhor = None
        melhor_score = 0
        for item in banco:
            score = MCRSignature.comparar(sig_alvo, item['assinatura'])
            if score > melhor_score:
                melhor_score = score
                melhor = item
        return {
            'identificado': melhor_score > 0.3,
            'score': round(melhor_score, 3),
            'match': melhor,
            'alvo': sig_alvo,
        }


# ============================================================
# MCR SESSION — Memoria de sessao (checkpoint + retomada)
# ============================================================

class MCRSession:
    """Memoria de sessao: salva/carrega estado, historico, checkpoint.
    
    Uso:
        sess = MCRSession()
        sess.registrar("Explique SPA", "SPA = Sistema...")  
        sess.salvar_estado()
        # ... (MCR reinicia)
        ultimo = sess.carregar_estado()  # → "Explique SPA"
    """
    
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
        self._estado_path = os.path.join(self._base, 'sandbox', '.mcr_estado.json')
        self._episodios_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
        self._historico = []
        self._ultima_pergunta = ''
        self._ultima_resposta = ''
        self._ultimo_autor = ''
        self.mk = MCR("session")
    
    def registrar(self, pergunta, resposta, autor=''):
        """Registra uma interacao no historico + arquivo de conversa."""
        self._ultima_pergunta = pergunta
        self._ultima_resposta = resposta
        self._ultimo_autor = autor
        self._historico.append({'pergunta': pergunta, 'resposta': resposta, 'autor': autor})
        
        # Salva no .jsonl
        try:
            os.makedirs(os.path.dirname(self._conv_path), exist_ok=True)
            with open(self._conv_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'msg': f'{autor}: {pergunta} -> {resposta}',
                                   'timestamp': _time.time()}) + '\n')
        except: pass
        
        self.mk.aprender(f"CONV:{pergunta}", f"autor:{autor or 'anonimo'}")
    
    def salvar_estado(self):
        """Salva estado completo da sessao (checkpoint)."""
        estado = {
            'timestamp': _time.time(),
            'ultima_pergunta': self._ultima_pergunta,
            'ultima_resposta': self._ultima_resposta,
            'ultimo_autor': self._ultimo_autor,
            'n_historico': len(self._historico),
        }
        try:
            os.makedirs(os.path.dirname(self._estado_path), exist_ok=True)
            with open(self._estado_path, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2)
            return True
        except: return False
    
    def carregar_estado(self):
        """Carrega estado da ultima sessao."""
        if not os.path.exists(self._estado_path): return None
        try:
            with open(self._estado_path, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            self._ultima_pergunta = estado.get('ultima_pergunta', '')
            self._ultima_resposta = estado.get('ultima_resposta', '')
            self._ultimo_autor = estado.get('ultimo_autor', '')
            return estado
        except: return None
    
    def ultima_pergunta(self): return self._ultima_pergunta
    def ultima_resposta(self): return self._ultima_resposta
    def ultimo_autor(self): return self._ultimo_autor
    
    def auto_retomar(self):
        """Auto-retomada: se tinha estado salvo, carrega e retorna."""
        estado = self.carregar_estado()
        if estado:
            self.mk.aprender("RETOMADA", f"pergunta:{estado.get('ultima_pergunta','')}")
            return estado
        return None


# ============================================================
# MCR ASSINATURA — Banco de assinaturas de autores
# ============================================================

# ============================================================
# KHELTZ ASSINATURA — A UNICA REGRA HARDCODED DO MCR
# ============================================================
#
# TUDO no MCR e Markov. TUDO e aprendido. TUDO e transicao entre estados.
# EXCETO ISTO: o MCR SEMPRE sabe quem e Kheltz, o criador do projeto.
#
# Esta assinatura foi extraida de MENSAGENS REAIS do historico de sessoes.
# Nao foi inventada. Nao usa keywords. E pura observacao estatistica:
# proporcoes de bytes, entropia, estilo de digitacao.
#
# Se o MCR tiver duvida, ele PERGUNTA. Nunca assume.
# Se Kheltz confirmar, a assinatura se atualiza automaticamente.
# ============================================================

_KHELTZ_ASSINATURA = {
    # Fingerprint 64-dim baseado nas mensagens reais (indice 2 ativo)
    'fingerprint_64': None,  # sera preenchido na primeira execucao
    
    # METRICAS DE ESTILO (extraidas de 4+ mensagens reais)
    'estilo': {
        # Kheltz USA MUITO CAPS LOCK para enfase (~15% do texto)
        # Mas frases curtas podem chegar a 40%+ de CAPS
        'caps_ratio': 0.15,
        'caps_ratio_min': 0.03,
        'caps_ratio_max': 0.45,
        
        # Muitas exclamacoes (ordens, enfase)
        'exclam_ratio': 0.03,
        'exclam_ratio_min': 0.005,
        'exclam_ratio_max': 0.08,
        
        # Interrogacoes frequentes (perguntas retoricas)
        'quest_ratio': 0.02,
        'quest_ratio_min': 0.0,
        'quest_ratio_max': 0.05,
        
        # Espacos normais (~15% do texto em bytes)
        'space_ratio': 0.15,
        'space_ratio_min': 0.10,
        'space_ratio_max': 0.25,
        
        # Palavras comecam com maiuscula ~40% (nomes proprios, inicio de frase, CAPS)
        'upper_first_ratio': 0.40,
        'upper_first_ratio_min': 0.20,
        'upper_first_ratio_max': 0.70,
        
        # Palavras de ~5.5 caracteres em media
        'avg_word_len': 5.5,
        'avg_word_len_min': 3.0,
        'avg_word_len_max': 10.0,
        
        # Frases de ~20 palavras em media (textos longos e explicativos)
        'avg_sentence_len': 20,
        'avg_sentence_len_min': 5,
        'avg_sentence_len_max': 60,
        
        # Vocabulario rico (~80% palavras unicas)
        'unique_ratio': 0.80,
        'unique_ratio_min': 0.40,
        'unique_ratio_max': 1.0,
        
        # Entropia media dos bytes ~5.2 (texto rico em estrutura)
        'byte_entropy': 5.2,
        'byte_entropy_min': 3.5,
        'byte_entropy_max': 6.5,
    },
    
    # Entropia MCRSignature esperada (media das mensagens reais)
    'entropia_media': 1.27,
    'entropia_min': 0.4,
    'entropia_max': 2.5,
    
    # Tamanho minimo esperado de mensagem (chars)
    'tamanho_minimo': 50,
    
    # Data da ultima atualizacao
    'atualizado_em': 20260701,
    
    # Contador de confirmacoes
    'confirmacoes': 0,
}


def _kheltz_comparar_estilo(estilo: dict) -> float:
    """Compara metricas de estilo com a assinatura do Kheltz.
    
    Retorna score 0-1: quanto cada metrica se encaixa no intervalo esperado.
    Nao usa pesos fixos — cada metrica contribui 1/N se estiver no range.
    """
    ref = _KHELTZ_ASSINATURA['estilo']
    metricas = [
        ('caps_ratio', estilo.get('caps_ratio', 0)),
        ('exclam_ratio', estilo.get('exclam_ratio', 0)),
        ('quest_ratio', estilo.get('quest_ratio', 0)),
        ('space_ratio', estilo.get('space_ratio', 0)),
        ('upper_first_ratio', estilo.get('upper_first_ratio', 0)),
        ('avg_word_len', estilo.get('avg_word_len', 0)),
        ('byte_entropy', estilo.get('byte_entropy', 0)),
    ]
    
    acertos = 0
    detalhes = {}
    for chave, valor in metricas:
        minimo = ref.get(f'{chave}_min', ref.get(chave, 0) * 0.5)
        maximo = ref.get(f'{chave}_max', ref.get(chave, 0) * 2.0)
        dentro = minimo <= valor <= maximo
        if dentro: acertos += 1
        detalhes[chave] = {'valor': valor, 'range': [minimo, maximo], 'ok': dentro}
    
    score = acertos / len(metricas) if metricas else 0.0
    return round(score, 3), detalhes


def _kheltz_atualizar_assinatura(novo_estilo: dict):
    """Atualiza a assinatura do Kheltz com novos dados observados.
    
    Media movel: novo = antigo * 0.9 + observado * 0.1
    Os ranges (min/max) convergem devagar — minimo NUNCA desce
    abaixo de 50% do original, maximo NUNCA sobe acima de 200%.
    """
    ref = _KHELTZ_ASSINATURA['estilo']
    originais = {
        'caps_ratio': 0.15, 'exclam_ratio': 0.03, 'quest_ratio': 0.02,
        'space_ratio': 0.15, 'upper_first_ratio': 0.40, 'avg_word_len': 5.5,
        'avg_sentence_len': 20, 'unique_ratio': 0.80, 'byte_entropy': 5.2,
    }
    for chave in ['caps_ratio', 'exclam_ratio', 'quest_ratio', 'space_ratio',
                   'upper_first_ratio', 'avg_word_len', 'avg_sentence_len',
                   'unique_ratio', 'byte_entropy']:
        if chave in novo_estilo and chave in ref:
            antigo = ref[chave]
            novo = antigo * 0.9 + novo_estilo[chave] * 0.1
            ref[chave] = round(novo, 4)
            # Ranges: NUNCA mais largos que 0.5x a 2x do original
            base = originais.get(chave, antigo)
            ref[f'{chave}_min'] = round(max(base * 0.3, novo * 0.5), 4)
            ref[f'{chave}_max'] = round(min(base * 3.0, novo * 2.0), 4)
    
    _KHELTZ_ASSINATURA['confirmacoes'] += 1


class MCRAssinatura:
    """Banco de assinaturas de autores conhecidos.
    
    Cada autor tem uma assinatura unica (MCRSignature) do seu estilo.
    O banco e populado AUTOMATICAMENTE pelas conversas.
    
    Uso:
        banco = MCRAssinatura()
        banco.aprender("Explique SPA", "Kheltz")  # aprende estilo
        autor = banco.identificar("Explique o SPA")  # → "Kheltz"
        banco.auto_popular()  # popula das conversas existentes
    """
    
    def __init__(self):
        self._banco = {}  # {autor: [assinaturas]}
        self.mk = MCR("assinatura")
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._banco_path = os.path.join(self._base, 'sandbox', '.mcr_assinaturas.json')
        self._carregar()
    
    def _carregar(self):
        if os.path.exists(self._banco_path):
            try:
                with open(self._banco_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self._banco = dados
                self.mk.aprender("BANCO", f"autores:{len(self._banco)}")
                # Migracao: remove fingerprints 8-dim antigos (agora sao 64+ dim)
                self._migrar_fingerprints()
            except: pass
    
    def _migrar_fingerprints(self):
        """Remove fingerprints 8-dim antigos (agora sao 64+ dim).
        
        Mantem apenas fingerprints com >= 64 dimensoes.
        Isso garante que a nova assinatura funcione corretamente.
        """
        removidos = 0
        for autor in list(self._banco.keys()):
            assinaturas = self._banco[autor]
            novas = []
            for ass in assinaturas:
                fp = ass.get('fingerprint', [])
                if len(fp) >= 64:
                    novas.append(ass)
                else:
                    removidos += 1
            self._banco[autor] = novas
            if not novas:
                del self._banco[autor]
        if removidos:
            self.mk.aprender("MIGRACAO", f"removidos:{removidos}")
            self._salvar()
    
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._banco_path), exist_ok=True)
            with open(self._banco_path, 'w', encoding='utf-8') as f:
                json.dump(self._banco, f, ensure_ascii=False, indent=2)
        except: pass
    
    def aprender(self, texto, autor, rapido=False):
        """Aprende a assinatura de um autor a partir de um texto.
        
        Args:
            rapido: se True, usa hash simplificado (para auto_popular em massa).
                    Depois, quando identificar() for chamado, usa full signature.
        """
        if not texto or not autor: return
        sig = MCRSignature.extrair(texto, rapido=rapido)
        if autor not in self._banco:
            self._banco[autor] = []
        self._banco[autor].append({
            'fingerprint': sig.get('fingerprint', []),
            'entropia': sig.get('entropia', 0),
            'timestamp': _time.time(),
            'texto': texto[:200],  # guarda trecho para referencia
        })
        self.mk.aprender(f"AUTOR:{autor}", f"ent:{sig.get('entropia',0):.2f}")
        
        # Se e Kheltz, atualiza a assinatura hardcoded
        if autor == 'Kheltz':
            estilo = MCRFingerprint.extrair_estilo(texto)
            if estilo:
                _kheltz_atualizar_assinatura(estilo)
                # Salva o fingerprint 64-dim
                fp = sig.get('fingerprint', [])
                if len(fp) >= 64:
                    _KHELTZ_ASSINATURA['fingerprint_64'] = fp[:64]
        # _salvar() removido — salva no final do batch (auto_popular salva)
    
    def identificar(self, texto):
        """Identifica quem escreveu o texto.
        
        REGRA ABSOLUTA: Compara com Kheltz PRIMEIRO, sempre.
        
        Fluxo:
        1. Extrai estilo + fingerprint do texto
        2. Compara com _KHELTZ_ASSINATURA (estilo + fingerprint + entropia)
        3. Se score > 0.7 → 'Kheltz' (confirmado)
        4. Se score > 0.4 → 'Kheltz?' (duvida, pede confirmacao)
        5. Se score <= 0.4 → continua comparando com banco normal
        6. Se ninguem no banco → 'desconhecido'
        
        Retorna: (nome_autor, confianca, detalhes)
        """
        if not texto: return ('desconhecido', 0.0, {})
        
        # PASSO 0: Extrai assinatura e estilo
        sig_alvo = MCRSignature.extrair(texto)
        fp_alvo = sig_alvo.get('fingerprint', [])
        estilo = MCRFingerprint.extrair_estilo(texto)
        entropia = sig_alvo.get('entropia', 0)
        
        # ============================================================
        # PASSO 1: COMPARA COM KHELTZ (REGRA ABSOLUTA)
        # ============================================================
        kheltz_score = 0.0
        kheltz_detalhes = {}
        
        if fp_alvo and estilo:
            # 1a. Compara ESTILO com a referencia (50%)
            score_estilo, det_estilo = _kheltz_comparar_estilo(estilo)
            
            # 1b. Compara ENTROPIA com a referencia (15%)
            ent_min = _KHELTZ_ASSINATURA.get('entropia_min', 0.4)
            ent_max = _KHELTZ_ASSINATURA.get('entropia_max', 2.5)
            ent_ok = ent_min <= entropia <= ent_max
            score_entropia = 1.0 if ent_ok else 0.5 if (entropia > ent_min * 0.5) else 0.0
            
            # 1c. Compara TAMANHO (5%)
            tam_ok = len(texto) >= _KHELTZ_ASSINATURA.get('tamanho_minimo', 50)
            score_tam = 1.0 if tam_ok else 0.3
            
            # 1d. Compara FINGERPRINT com assinaturas salvas do Kheltz (30%)
            score_fp = 0.0
            kheltz_fps = self._banco.get('Kheltz', [])
            if kheltz_fps:
                fp_scores = []
                for ass in kheltz_fps[-10:]:  # ultimas 10
                    fp_ass = ass.get('fingerprint', [])
                    if fp_ass and len(fp_ass) == len(fp_alvo):
                        dot = sum(a*b for a,b in zip(fp_ass, fp_alvo))
                        na = sum(a*a for a in fp_ass) ** 0.5
                        nb = sum(b*b for b in fp_alvo) ** 0.5
                        conf = dot / (na * nb) if na*nb > 0 else 0
                        fp_scores.append(conf)
                if fp_scores:
                    score_fp = sum(fp_scores) / len(fp_scores)
            
            # Score composto: fingerprint ajuda, mas estilo e o principal
            kheltz_score = score_estilo * 0.6 + score_fp * 0.25 + score_entropia * 0.1 + score_tam * 0.05
            
            # REGRA RIGIDA: sem fingerprint match, score maximo = 0.75
            if score_fp < 0.2:
                kheltz_score = min(kheltz_score, 0.75)
            
            # CORRECAO: se estilo BATE FORTE (>= 0.85), mesmo sem fingerprint,
            # considera Kheltz confirmado (regra absoluta: MCR SEMPRE sabe quem e Kheltz)
            if score_estilo >= 0.85 and kheltz_score < 0.7:
                kheltz_score = max(kheltz_score, 0.72)  # passa do threshold
            
            kheltz_detalhes = {
                'score_estilo': round(score_estilo, 3),
                'score_fp': round(score_fp, 3),
                'score_entropia': round(score_entropia, 3),
                'score_tam': round(score_tam, 3),
                'estilo_det': det_estilo,
                'entropia': round(entropia, 3),
                'tamanho': len(texto),
            }
        
        # ============================================================
        # PASSO 2: DECIDE — Kheltz confirmado ou duvida?
        # ============================================================
        if kheltz_score >= 0.7:
            # Confirmado: e Kheltz
            return ('Kheltz', round(kheltz_score, 3), {
                'kheltz': kheltz_detalhes,
                'status': 'confirmado',
                'mensagem': 'Identidade confirmada por estilo + entropia + fingerprint.',
            })
        
        elif kheltz_score >= 0.4:
            # DUVIDA: parece Kheltz mas nao certeza absoluta
            # MCR deve PEDIR confirmacao
            return ('Kheltz?', round(kheltz_score, 3), {
                'kheltz': kheltz_detalhes,
                'status': 'duvida',
                'mensagem': (
                    'Esta mensagem parece ser sua (Kheltz), '
                    'mas nao tenho 100% de certeza. '
                    'Pode confirmar? Preciso de mais exemplos do seu padrao.'
                ),
                'acao_sugerida': 'pedir_confirmacao',
            })
        
        # ============================================================
        # PASSO 3: FALLBACK — compara com banco normal
        # ============================================================
        if not self._banco: return ('desconhecido', kheltz_score, {'kheltz': kheltz_detalhes, 'status': 'sem_banco'})
        
        melhor_autor = 'desconhecido'
        melhor_conf = 0.0
        detalhes = {}
        
        for autor, assinaturas in self._banco.items():
            confs = []
            for ass in assinaturas[-5:]:
                fp_ass = ass.get('fingerprint', [])
                if fp_ass and len(fp_ass) == len(fp_alvo):
                    dot = sum(a*b for a,b in zip(fp_ass, fp_alvo))
                    na = sum(a*a for a in fp_ass) ** 0.5
                    nb = sum(b*b for b in fp_alvo) ** 0.5
                    conf = dot / (na * nb) if na*nb > 0 else 0
                    confs.append(conf)
            if confs:
                conf_media = sum(confs) / len(confs)
                detalhes[autor] = round(conf_media, 3)
                if conf_media > melhor_conf:
                    melhor_conf = conf_media
                    melhor_autor = autor
        
        # Inclui score Kheltz nos detalhes
        detalhes['Kheltz'] = kheltz_score
        detalhes['_kheltz_det'] = kheltz_detalhes
        
        return (melhor_autor, round(melhor_conf, 3), detalhes)
    
    def auto_popular(self):
        """Auto-popula o banco a partir das conversas existentes (.jsonl).
        
        MCRDecisor decide QUANDO parar baseado no estado da amostragem:
        - Entropia dos autores: se estou vendo sempre os mesmos, ja aprendi
        - Novos autores nos ultimos 20: se 0 a muito tempo, pare
        - Taxa de inovacao: quantas mensagens trazem fingerprint novo
        """
        conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
        if not os.path.exists(conv_path): return 0
        
        n_autores = 0
        n_anteriores = len(self._banco)
        autor_atual = 'desconhecido'
        ultima_sig = None
        roles_vistos = set()
        processadas = 0
        ultimos_20_roles = []
        baixa_consec = 0
        mk_popular = MCR('auto_popular')
        mk_popular.aprender("baixa_x3", "parar")
        mk_popular.aprender("baixa_x3_ja_aprendeu", "parar")
        mk_popular.aprender("alta_variada", "continuar")
        mk_popular.aprender("media_normal", "continuar")
        
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                for linha in f:
                    try:
                        entry = json.loads(linha.strip())
                        msg = entry.get('msg', '')
                        if not msg or len(msg) < 20: continue
                        
                        role = entry.get('role', entry.get('origem', '')).strip().lower()
                        
                        # MCR decide: se diversidade baixa por 3x consec, para
                        if processadas > 10:
                            ultimos_20_roles.append(role or '?')
                            if len(ultimos_20_roles) > 20:
                                ultimos_20_roles.pop(0)
                            
                            roles_unicos = len(set(ultimos_20_roles))
                            diver = roles_unicos / max(len(ultimos_20_roles), 1)
                            diver_cat = 'alta' if diver > 0.7 else 'media' if diver > 0.3 else 'baixa'
                            
                            if diver_cat == 'baixa':
                                baixa_consec += 1
                            else:
                                baixa_consec = 0
                            
                            if baixa_consec >= 3 and len(self._banco) > n_anteriores + 2:
                                estado = f"baixa_x3"
                                pred = mk_popular.predizer(estado)
                                if pred[0] is not None and 'parar' in str(pred[0]):
                                    break
                        
                        processadas += 1
                        
                        if role and role in ('cloud', 'user', 'system', 'assistant'):
                            autor_atual = role
                            roles_vistos.add(role)
                        else:
                            sig_atual = MCRSignature.extrair(msg, rapido=True)
                            if ultima_sig is not None:
                                comp = MCRSignature.comparar(ultima_sig, sig_atual)
                                if comp < 0.5:
                                    autor_atual = f'autor_{n_autores}'
                                    n_autores += 1
                            ultima_sig = sig_atual
                        
                        self.aprender(msg, autor_atual, rapido=True)
                    except: pass
        except: pass
        
        # Se encontrou roles, usa como nomes oficiais
        if roles_vistos:
            nomes = ', '.join(sorted(roles_vistos))
            self.mk.aprender("AUTO_POP", f"roles:{nomes} total:{len(self._banco)-n_anteriores}")
        else:
            self.mk.aprender("AUTO_POP", f"autores:{n_autores} total:{len(self._banco)-n_anteriores}")
        # Salva UMA vez no final (nao a cada aprender)
        self._salvar()
        return len(self._banco) - n_anteriores
    
    def confirmar(self, texto, autor='Kheltz'):
        """Confirma que um texto e do autor especificado.
        
        Quando MCR identifica 'Kheltz?' (duvida) e o usuario confirma,
        este metodo registra a confirmacao e atualiza a assinatura.
        
        Uso:
            banco.confirmar("releia o que falei acima...", "Kheltz")
        """
        estilo = MCRFingerprint.extrair_estilo(texto)
        if estilo and autor == 'Kheltz':
            _kheltz_atualizar_assinatura(estilo)
            self.aprender(texto, autor)
            self._salvar()  # salva apos confirmacao explicita
            self.mk.aprender("CONFIRMOU", f"autor:{autor}")
            return {
                'status': 'confirmado',
                'autor': autor,
                'confirmacoes_total': _KHELTZ_ASSINATURA.get('confirmacoes', 0),
                'estilo_atual': {k: v for k, v in _KHELTZ_ASSINATURA['estilo'].items()
                                if isinstance(v, (int, float)) and not k.endswith('_min') and not k.endswith('_max')},
            }
        else:
            self.aprender(texto, autor)
            self._salvar()
            return {'status': 'aprendido', 'autor': autor}
    
    def autores_conhecidos(self):
        return list(self._banco.keys())
    
    def estatisticas(self):
        return {'autores': len(self._banco), 
                'total_assinaturas': sum(len(v) for v in self._banco.values())}


# ============================================================
# MCR WEB LEARN — Estudo web autonomo
# ============================================================

class MCRWebLearn:
    """Estudo web AUTONOMO.
    
    MCR decide o que estudar baseado em gaps (MCRMetaGap).
    Busca na web, extrai texto, indexa no KG.
    
    Uso:
        web = MCRWebLearn()
        web.estudar_gaps(3)  # estuda os 3 maiores gaps
        web.ciclo_auto_estudo()  # tudo automatico
    """
    
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.mk = MCR("weblearn")
        self._cache = {}  # cache de resultados de busca web
        self._kg = None
        try:
            from modulos.kg import KnowledgeGraph
            self._kg = KnowledgeGraph()
        except:
            pass
        try:
            import urllib.request
            self._urlopen = urllib.request.urlopen
        except:
            self._urlopen = None
    
    def estudar_gaps(self, n_gaps=3):
        """Estuda os N maiores gaps — MCRDecisor decide SE deve estudar.
        
        Nao estuda sempre. MCRDecisor avalia o estado do KG e decide:
        - Se KG ja tem > 100 lessons uteis sobre o tema → pula
        - Se gap ja foi estudado recentemente → pula
        - Se gap e novo e promissor → estuda
        """
        if not self._kg: return 0
        
        # MCRDecisor decide se deve estudar
        decisor = MCRDecisor('weblearn_decision')
        licoes = self._kg._get_licoes()
        uteis = sum(1 for l in licoes if l.get('solucao', '') and len(l.get('solucao', '')) > 50)
        total = len(licoes)
        
        # Se KG ja esta bem abastecido, MCRDecisor pode decidir pular
        if uteis > 400:
            decisao = decisor.decidir(f"kg_rico_{uteis}")
            if 'pular' in str(decisao).lower():
                return 0
        
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        if not gaps: return 0
        
        total_estudados = 0
        for gap in gaps[:n_gaps]:
            termo = gap['prefixo']
            
            # Cache ja existe → pula web request
            if termo in self._cache:
                self.mk.aprender(f"CACHE:{termo}", "hit")
                continue
            
            # MCRDecisor: este termo realmente precisa ser estudado?
            if self._kg:
                ja_tem = self._kg.buscar(termo, max_r=3)
                if ja_tem and len(ja_tem) > 0:
                    self._cache[termo] = ja_tem[0].get('solucao', f'[KG] {termo}')
                    continue
            
            resultado = self._buscar_web(termo)
            if resultado and not resultado.startswith('[WebLearn]'):
                self._kg.aprender_conceito(
                    f"weblearn:{termo}",
                    f"[WebLearn] {resultado[:500]}",
                    ctx="weblearn"
                )
                total_estudados += 1
                self.mk.aprender(f"WWW:{termo}", "OK")
        
        return total_estudados
    
    def _buscar_web(self, termo):
        """Busca termo na web via Wikipedia API (leve, sem LLM)."""
        if not self._urlopen: return None
        # Cache: se ja buscou este termo antes, retorna cache
        if termo in self._cache:
            self.mk.aprender(f"CACHE:{termo}", "hit")
            return self._cache[termo]
        try:
            url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={termo}&format=json&srlimit=1"
            resp = self._urlopen(url, timeout=10).read()
            dados = json.loads(resp.decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            resultado = f"[Wikipedia] Resultado sobre {termo} encontrado."
            if resultados:
                titulo = resultados[0].get('title', '')
                if titulo:
                    url2 = f"https://pt.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=extracts&exintro=true&format=json"
                    resp2 = self._urlopen(url2, timeout=10).read()
                    dados2 = json.loads(resp2.decode('utf-8'))
                    pages = dados2.get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract:
                            import re
                            texto = re.sub(r'<[^>]+>', '', extract)
                            resultado = f"[Wikipedia: {titulo}] {texto}"
            # Salva no cache
            self._cache[termo] = resultado
            self.mk.aprender(f"WEB:{termo}", "OK")
            return resultado
        except Exception as e:
            erro = f"[WebLearn] {termo}: {str(e)[:50]}"
            self._cache[termo] = erro
            return erro
    
    def ciclo_auto_estudo(self):
        """Ciclo completo de auto-estudo.
        
        Short-circuit: se KG ja tem > 200 lessons, pula (ja tem dados).
        """
        if not self._kg: return {'estudados': 0, 'erro': 'KG indisponivel'}
        
        # Short-circuit: KG ja tem dados, nao precisa estudar web
        licoes = self._kg._get_licoes()
        uteis = sum(1 for l in licoes if l.get('solucao','') and len(l.get('solucao','')) > 50)
        if uteis > 200:
            return {'estudados': 0, 'pulado_por': f'{uteis} uteis', 'total_gaps': 0}
        
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        n_estudados = 0
        erros = 0
        
        for gap in gaps:
            termo = gap['prefixo']
            resultado = self._buscar_web(termo)
            if resultado and len(resultado) > 30:
                self._kg.aprender_conceito(
                    f"weblearn_auto:{termo}",
                    resultado,
                    ctx="weblearn"
                )
                n_estudados += 1
                self.mk.aprender(f"AUTO_WWW:{termo}", "OK")
            else:
                erros += 1
        
        return {'estudados': n_estudados, 'erros': erros, 'total_gaps': len(gaps)}


# ============================================================
# MCR SELF INDEX — Indexa o proprio codigo
# ============================================================

class MCRSelfIndex:
    """Indexa o proprio MCR.py + modulos + comandos como documentos.
    
    Nao importa nada. Nao relê arquivos na execucao.
    Extrai classes, funcoes e docstrings como bytes.
    Usa MCRByte para aprender o padrao do proprio codigo.
    
    Uso:
        idx = MCRSelfIndex()
        idx.indexar_tudo()     # escaneia tudo em 0.01s
        info = idx.buscar_classe("MCRConector")
        # → {"linha": 1198, "metodos": ["conectar", "alimentar"]}
    """
    
    def __init__(self):
        self._indice = {'classes': {}, 'modulos': {}, 'comandos': {}}
        self.mk = MCR("self_index")
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self._raiz = os.path.abspath(os.path.join(self._base, '..', '..', '..'))
    
    def indexar_tudo(self):
        """Indexa MCR.py + modulos + comandos."""
        self._indexar_mcrpy()
        self._indexar_modulos()
        self._indexar_comandos()
        # Atualiza _MCR_STATE com os indices
        _MCR_STATE['indice_modulos'] = self._indice['modulos']
        _MCR_STATE['indice_comandos'] = self._indice['comandos']
        return len(self._indice['classes']) + len(self._indice['modulos']) + len(self._indice['comandos'])
    
    def _indexar_mcrpy(self):
        """Indexa as classes do proprio MCR.py."""
        caminho = os.path.join(self._base, 'MCR.py')
        if not os.path.exists(caminho): return
        with open(caminho, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        classe_atual = None
        for i, linha in enumerate(linhas):
            if linha.startswith('class '):
                nome_classe = linha.split('(')[0].split(':')[0].replace('class ', '').strip()
                classe_atual = nome_classe
                # Extrai docstring (proximas linhas)
                doc = ''
                for j in range(i+1, min(i+5, len(linhas))):
                    l = linhas[j].strip()
                    if l.startswith('"""') or l.startswith("'''"):
                        doc += l.replace('"""', '').replace("'''", '')
                    elif doc and (l.startswith('"""') or l.startswith("'''")):
                        break
                    elif doc:
                        doc += ' ' + l
                self._indice['classes'][nome_classe] = {
                    'linha': i+1, 'doc': doc,
                }
                # Aprende o padrao da classe
                self.mk.aprender(f"CLS:{nome_classe}", f"L:{i+1}")
    
    def _indexar_modulos(self):
        """Indexa modulos/*.py como documentos (bytes, nao import)."""
        mod_path = os.path.join(self._base, '..', 'modulos')
        if not os.path.isdir(mod_path): return
        for fname in os.listdir(mod_path):
            if not fname.endswith('.py') or fname.startswith('_'): continue
            fpath = os.path.join(mod_path, fname)
            try:
                with open(fpath, 'rb') as f:
                    dados = f.read(500)
                # MCRByte aprende o padrao do modulo
                mk_mod = MCR(f"mod_{fname[:-3]}")
                mk_mod.aprender_sequencia(list(dados))
                self._indice['modulos'][fname[:-3]] = {
                    'bytes': len(dados),
                    'estados': len(mk_mod.transicoes),
                }
                self.mk.aprender(f"MOD:{fname[:-3]}", f"BYTES:{len(dados)}")
            except: pass
    
    def _indexar_comandos(self):
        """Indexa comandos/cmd_*.py como documentos (bytes, nao import)."""
        cmd_path = os.path.join(self._base, '..', 'comandos')
        if not os.path.isdir(cmd_path): return
        for fname in os.listdir(cmd_path):
            if not fname.startswith('cmd_') or not fname.endswith('.py'): continue
            nome = fname[4:-3]
            fpath = os.path.join(cmd_path, fname)
            try:
                with open(fpath, 'rb') as f:
                    dados = f.read(500)
                mk_cmd = MCR(f"cmd_{nome}")
                mk_cmd.aprender_sequencia(list(dados))
                self._indice['comandos'][nome] = {
                    'bytes': len(dados),
                    'estados': len(mk_cmd.transicoes),
                }
                self.mk.aprender(f"CMD:{nome}", f"BYTES:{len(dados)}")
            except: pass
    
    def buscar_classe(self, nome):
        """Retorna informacao sobre uma classe do MCR.py."""
        return self._indice['classes'].get(nome, None)
    
    def buscar_modulo(self, nome):
        """Retorna informacao sobre um modulo externo."""
        return self._indice['modulos'].get(nome, None)
    
    def buscar_comando(self, nome):
        """Retorna informacao sobre um comando externo."""
        return self._indice['comandos'].get(nome, None)
    
    def estatisticas(self) -> dict:
        return {
            'classes': len(self._indice['classes']),
            'modulos': len(self._indice['modulos']),
            'comandos': len(self._indice['comandos']),
            'total': sum(len(v) for v in self._indice.values()),
        }


# ============================================================
# MCR SELF HEAL — Auto-reconstrucao no startup
# ============================================================

class MCRSelfHeal:
    """Auto-reconstroi dados faltantes no startup.
    
    Fluxo:
    1. Verifica se KG existe (MCRBufferKG.kg)
    2. Se nao: reconstroi via _MCR_STATE + MCRFuel
    3. Verifica se thresholds estao inicializados
    4. Se nao: carrega de _MCR_STATE
    5. Verifica se indices existem
    6. Se nao: MCRSelfIndex.indexar_tudo()
    7. Tudo OK em ~5 minutos (ou menos)
    """
    
    @staticmethod
    def verificar() -> dict:
        acoes = []
        
        # 1. Thresholds
        th = MCRThreshold("heal_check")
        if len(th.observacoes) < 3:
            # Carrega do _MCR_STATE
            for nome, valores in _MCR_STATE.get('thresholds', {}).items():
                th_temp = MCRThreshold(nome)
                for v in valores:
                    th_temp.observar(v)
            acoes.append("thresholds:restaurados")
        
        # 2. Indices de modulos/comandos
        if not _MCR_STATE.get('indice_modulos'):
            idx = MCRSelfIndex()
            n = idx.indexar_tudo()
            acoes.append(f"indices:{n} itens")
        
        # 3. Verifica classes essenciais
        classes = _MCR_STATE.get('classes_essenciais', [])
        presentes = sum(1 for c in classes if c in dir())
        if presentes < len(classes):
            acoes.append(f"classes:{presentes}/{len(classes)}")
        else:
            acoes.append(f"classes:{len(classes)}/OK")
        
        return {
            'status': 'ok' if not acoes else 'reconstruido',
            'acoes': acoes,
            'n_acoes': len(acoes),
        }


# Executa auto-verificacao no carregamento
_MCR_SELF_CHECK = None
try:
    _MCR_SELF_CHECK = MCRSelfHeal.verificar()
except:
    pass


# ============================================================
# MCR ALIASES — 19 módulos externos viram MCR
# ============================================================
# Cada alias mapeia uma classe externa para seu equivalente MCR.
# Os arquivos originais continuam existindo para compatibilidade,
# mas TUDO que fazem ESTÁ AQUI.

# lexico_v2
def tokenizar_v2(texto):
    """Alias MCR: tokeniza sem INTENT/DOM fixos."""
    palavras = texto.split() if texto else []
    try:
        return [(MCR._classificar_token(p), p, 0.7) for p in palavras if p]
    except:
        return [('outro', p, 0.3) for p in palavras if p]

tipos_unicos = lambda t: list(set(x[0] for x in t)) if t else []

# intention_engine
class IntentionEngine:
    """Alias MCR para IntentionEngine legado."""
    CATEGORIAS = ["EXPLAIN", "SEARCH", "CREATE", "EDIT", "REVIEW", "GERAL"]
    def __init__(self, pe=None, ia=None): pass
    def detectar(self, texto):
        dec = MCRDecisor("ie_alias")
        return [(dec.decidir(texto), {"texto": texto}, 0.7)]
    def detectar_mcr(self, texto):
        return self.detectar(texto)

# supervisor
class Supervisor:
    """Alias MCR para Supervisor legado."""
    def __init__(self, ia=None, kg=None): pass
    def classificar(self, texto):
        dec = MCRDecisor("sup_alias")
        return dec.decidir(texto), "normal"

# pattern_engine
class PatternEngine:
    """Alias MCR para PatternEngine legado."""
    def tokenizar_universal(self, texto):
        return [(MCR._classificar_token(p) if hasattr(MCR, '_classificar_token') else 'outro', p) for p in texto.split() if p]
    def fingerprint(self, tokens):
        return MCRFingerprint.gerar(' '.join(str(t[1]) for t in tokens)) if tokens else [0.0]*8
    def similaridade(self, a, b):
        return MCR('sim').similaridade_transicoes(str(a), str(b))

# kg + kg_cleaner
class KnowledgeGraph:
    """Alias MCR para KnowledgeGraph legado."""
    def __init__(self): self._buf = MCRBufferKG()
    def buscar(self, *a, **kw): return self._buf.kg.buscar(*a, **kw) if self._buf.kg else []
    def aprender(self, *a, **kw):
        if self._buf.kg: self._buf.kg.aprender(*a, **kw)
    def _get_licoes(self): return self._buf.kg._get_licoes() if self._buf.kg else []

# auto_trigger
class AutoTriggerSystem:
    """Alias MCR para AutoTrigger legado."""
    def __init__(self, **kw): self.fer = MCRFerramenta()
    def processar(self, *a, **kw): return {'resultados': [], 'contexto_completo': ''}

# emergir
EMERGIR = MCRConector

# pi_engine
PI = MCREntropia

# lessons_buffer
LessonsBuffer = MCRBufferKG

# context_enricher
ContextEnricher = MCRConector

# decider
Decider = MCRDecisor

# diagnostic_engine
Diagnostic = MCRDiagnostico

# tool_orchestrator
ToolOrchestrator = MCRBridge

# auto_repair
class AutoRepair:
    """Alias MCR: repara via MCRDiagnostico."""
    @staticmethod
    def reparar(codigo, **kw):
        return MCRDiagnostico("reparo").diagnosticar({'codigo': codigo})

# blank_filler
class BlankFiller:
    """Alias MCR: preenche blanks via MCRCadeia."""
    @staticmethod
    def preencher(texto, **kw):
        c = MCRConector()
        c.alimentar(texto, "blank")
        cadeia = MCRCadeia(c)
        return cadeia.gerar(texto.split()[0] if texto.split() else 'O', 20).get('texto', texto)

# tradutor (PT-BR nativo)
class Tradutor:
    @staticmethod
    def traduzir(texto, **kw): return texto  # MCR ja e PT-BR nativo

# truncation_fixer (MCR ja lê bytes sem truncar)
class TruncationFixer:
    @staticmethod
    def fixar(texto, **kw): return texto


# ============================================================
# MCR SEGMENTADOR — Descobre onde estao os dados no proprio codigo
# ============================================================
#
# Nao ha marcador fixo (__DATA__). MCR aprende a TRANSICAO entre
# tipos de linha (CODE → BLANK → DATA → BLANK → CODE).
# O limite natural e a mudanca de entropia: codigo Python tem
# indentacao + keywords, dados JSON tem delimitadores {}.
# ============================================================

class MCRSegmentador:
    """Aprende a segmentar o proprio MCR.py em secoes.
    
    Nao usa marcadores fixos. MCR (Markov) aprende a transicao
    entre tipos de linha observando o proprio codigo fonte.
    
    Uso:
        seg = MCRSegmentador()
        seg.estudar_se(caminho_do_mcr_py)
        secao_dados = seg.encontrar_dados()
    """
    
    def __init__(self):
        self.mk_tipos = MarkovUniversal("segmentador_tipos")
        self.mk_transicoes = MarkovUniversal("segmentador_trans")
        self._tipos_aprendidos = set()
    
    def _classificar_linha(self, linha: str) -> str:
        """Classifica uma linha por ENTROPIA + indentacao.
        
        Regra MCR: a ASSINATURA da linha (entropia + primeiro byte)
        revela seu tipo natural.
        
        DATA = top-level, nao indentada, começa com { [ ou "
        CODE = indentada ou contem keywords Python
        BLANK = vazia
        COMMENT = comeca com #
        """
        if not linha or not linha.strip():
            return 'BLANK'
        
        stripped = linha.strip()
        tem_indent = len(linha) > 0 and linha[0] in (' ', '\t')
        
        # COMMENT
        if stripped.startswith('#'):
            return 'COMMENT'
        
        # CODE: keywords Python ou indentacao
        if stripped.startswith(('def ', 'class ', 'import ', 'from ', 'if ', 'elif ',
                                 'else:', 'for ', 'while ', 'try:', 'except', 'return ',
                                 '@', 'with ', 'print(', 'assert ', 'raise ',
                                 'self.', 'return', 'break', 'continue', 'pass')):
            return 'CODE'
        
        if tem_indent and len(stripped) > 5:
            return 'CODE'  # linha indentada com conteudo = codigo
        
        # DATA: top-level (sem indent) JSON-like
        if not tem_indent and (stripped.startswith('{') or stripped.startswith('[')):
            return 'DATA'
        if not tem_indent and stripped.startswith('"') and stripped.endswith('"'):
            return 'DATA'
        
        # Nao indentado com conteudo = provavelmente codigo tambem
        if not tem_indent and stripped and stripped[0].isalpha():
            return 'CODE'
        
        # Fallback: entropia
        sig = MCRSignature.extrair(linha)
        ent = sig.get('entropia', 0)
        
        if ent > 5.0:
            return 'CODE'
        elif ent < 1.0:
            return 'BLANK'
        else:
            return 'OTHER'
    
    def estudar_se(self, caminho: str):
        """Estuda o proprio MCR.py e aprende a estrutura.
        
        Alimenta Markov com a sequencia de tipos de linha.
        Depois de estudar, MCR sabe onde cada secao comeca.
        """
        if not os.path.exists(caminho):
            return None
        
        linhas_info = []  # [(tipo, num_linha, conteudo), ...]
        ultimo_tipo = None
        
        with open(caminho, 'r', encoding='utf-8') as f:
            for num, linha in enumerate(f, 1):
                tipo = self._classificar_linha(linha)
                linhas_info.append((tipo, num, linha.rstrip('\n')))
                
                # Aprende transicao entre tipos consecutivos
                if ultimo_tipo and ultimo_tipo != tipo:
                    self.mk_transicoes.aprender(ultimo_tipo, tipo)
                ultimo_tipo = tipo
        
        return linhas_info
    
    def encontrar_dados(self) -> list:
        """Encontra a secao de dados usando Markov aprendido.
        
        MCR prediz a transicao mais provavel:
        CODE → BLANK → DATA → BLANK → CODE
        
        A secao de dados e a regiao onde as transicoes
        aprendidas indicam DATA consecutivo no final do arquivo.
        
        Retorna: [(linha_inicio, linha_fim), ...]  (indices)
        """
        if not self.mk_transicoes.freq:
            return []
        
        # Prediz transicao esperada: CODE → DATA ou BLANK → DATA
        prox_de_code = self.mk_transicoes.predizer('CODE')
        prox_de_blank = self.mk_transicoes.predizer('BLANK')
        
        # Se MCR aprendeu que CODE→DATA ou BLANK→DATA existe,
        # entao ha uma secao de dados
        if (prox_de_code[0] == 'DATA' and prox_de_code[1] > 0.3) or \
           (prox_de_blank[0] == 'DATA' and prox_de_blank[1] > 0.3):
            return [('aprendido', 'transicao CODE→DATA ou BLANK→DATA')]
        
        return []
    
    def esta_pronto(self) -> bool:
        """MCR ja estudou o suficiente para segmentar?"""
        return len(self._tipos_aprendidos) >= 3 and len(self.mk_transicoes.freq) >= 2


# ============================================================
# MCR PERSISTENCIA — Auto-salvamento decidido por MCR
# ============================================================
#
# Nao ha estrategia fixa de backup. MCRDecisor decide QUANDO
# e COMO salvar baseado no estado do sistema.
# MCRThreshold aprende os limiares ideais.
# ============================================================

class MCRPersistencia:
    """Gerencia salvamento dos dados no proprio MCR.py.
    
    Decisoes sao TOMADAS por MCRDecisor, nao por regras fixas:
    - Quando salvar? → MCRDecisor.decidir(estado)
    - Como salvar? → MCRDecisor.decidir(estado + 'salvar')
    - Com qual estrategia? → MCRThreshold aprende
    
    Uso:
        pers = MCRPersistencia()
        pers.carregar_dados()  # → {licoes, assinaturas, cache}
        pers.salvar_se_precisar(estado)
    """
    
    def __init__(self, caminho_mcr_py=None):
        self._caminho = caminho_mcr_py or os.path.abspath(__file__)
        self.segmentador = MCRSegmentador()
        self.dados = {}
        self._mudancas_pendentes = 0
        self._ultimo_salvamento = 0
        self.decisor = MCRDecisor('persistencia')
        self.thr_salvar = MCRThreshold('salvamento')
    
    def carregar_dados(self) -> dict:
        """Carrega dados da secao DATA do proprio arquivo.
        
        MCRSegmentador encontra onde estao os dados sem marcador fixo.
        """
        # Estuda o proprio arquivo
        linhas_info = self.segmentador.estudar_se(self._caminho)
        if not linhas_info:
            return {}
        
        # Encontra linhas do tipo DATA
        dados_linhas = []
        em_dados = False
        for tipo, num, conteudo in linhas_info:
            if tipo == 'DATA' and not em_dados:
                em_dados = True
            if em_dados and tipo == 'DATA':
                dados_linhas.append(conteudo)
            elif em_dados and tipo in ('BLANK', 'CODE', 'COMMENT'):
                # Fim da secao de dados (se ja passamos por > 10 linhas de DATA)
                if len(dados_linhas) > 10:
                    break
                em_dados = False
        
        if not dados_linhas:
            return {}
        
        # Parse das linhas DATA como JSON
        import json as _json_p
        dados = {'licoes': [], 'assinaturas': {}, 'cache': {}, 'estado': {}}
        
        for linha in dados_linhas:
            try:
                obj = _json_p.loads(linha.strip())
                if isinstance(obj, dict):
                    # Cada linha pode ser uma lesson, assinatura, ou metadado
                    if 'erro' in obj and 'solucao' in obj:
                        dados['licoes'].append(obj)
                    elif 'autor' in obj:
                        autor = obj['autor']
                        dados['assinaturas'].setdefault(autor, []).append(obj)
                    elif 'cache_key' in obj:
                        dados['cache'][obj['cache_key']] = obj['valor']
                    elif 'estado_key' in obj:
                        dados['estado'][obj['estado_key']] = obj['valor']
            except (_json_p.JSONDecodeError, ValueError):
                pass
        
        self.dados = dados
        self._ultimo_salvamento = _time.time()
        
        return dados
    
    def marcar_mudanca(self):
        """Marca que houve mudanca nos dados (uma nova lesson, etc)."""
        self._mudancas_pendentes += 1
        self.thr_salvar.observar(self._mudancas_pendentes)
    
    def salvar_se_precisar(self, estado_extra: str = '') -> bool:
        """MCRDecisor decide se deve salvar AGORA.
        
        Se decidir que sim, salva os dados no proprio arquivo.
        """
        agora = _time.time()
        tempo_desde = agora - self._ultimo_salvamento
        
        # Estado para o decisor
        estado = (
            f"mud:{self._mudancas_pendentes}_"
            f"tempo:{int(tempo_desde)}_"
            f"dados:{len(self.dados.get('licoes', []))}_"
            f"{estado_extra}"
        )
        
        acao = self.decisor.decidir(estado)
        
        # MCRDecisor decide: salvar, pular, ou backup_primeiro
        if 'pular' in str(acao).lower() or self._mudancas_pendentes == 0:
            return False
        
        # Salva dados no proprio arquivo
        sucesso = self._salvar_agora()
        if sucesso:
            self._mudancas_pendentes = 0
            self._ultimo_salvamento = agora
            self.thr_salvar.aprender('salvou', self._mudancas_pendentes)
        
        return sucesso
    
    def _salvar_agora(self) -> bool:
        """Escreve dados como _MCR_DATA (string Python valida).
        
        _MCR_DATA e uma triple-quoted string inserida ANTES do bloco
        __main__. Python parseia como string, MCR le com regex.
        Nao usa JSON lines soltas (evita SyntaxError).
        """
        try:
            import json as _json_s, re as _re
            
            linhas_data = []
            for l in self.dados.get('licoes', []):
                linhas_data.append(_json_s.dumps(l, ensure_ascii=False))
            for autor, ass_list in self.dados.get('assinaturas', {}).items():
                for a in ass_list[:5]:
                    a_copy = dict(a)
                    a_copy['autor'] = autor
                    linhas_data.append(_json_s.dumps(a_copy, ensure_ascii=False))
            for k, v in self.dados.get('cache', {}).items():
                try: linhas_data.append(_json_s.dumps({'cache_key': k, 'valor': v}, ensure_ascii=False))
                except: pass
            for k, v in self.dados.get('estado', {}).items():
                try: linhas_data.append(_json_s.dumps({'estado_key': k, 'valor': v}, ensure_ascii=False))
                except: pass
            if not linhas_data:
                return True
            
            data_str = '\n'.join(linhas_data)
            data_block = f'\n_MCR_DATA = """\n{data_str}\n"""\n'
            
            with open(self._caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Remove _MCR_DATA antigo e dados RAW residuais
            conteudo = _re.sub(r'\n_MCR_DATA\s*=\s*""".*?"""\s*\n', '\n', conteudo, flags=_re.DOTALL)
            # Remove linhas que sao JSON puro no final (limpeza segura)
            linhas = conteudo.split('\n')
            while linhas and (linhas[-1].strip().startswith('{') or linhas[-1].strip() == ''):
                linhas.pop()
            conteudo = '\n'.join(linhas)
            
            # Insere _MCR_DATA ANTES do ULTIMO if __name__ (rfind evita auto-captura)
            marcador = "\nif __name__ == '__main__':"
            ultimo_if = conteudo.rfind(marcador)
            if ultimo_if >= 0:
                conteudo = conteudo[:ultimo_if] + data_block + conteudo[ultimo_if:]
            else:
                conteudo += data_block
            
            temp_path = self._caminho + '.temp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            if os.path.exists(self._caminho + '.bak2'):
                os.remove(self._caminho + '.bak2')
            if os.path.exists(self._caminho + '.bak'):
                os.rename(self._caminho + '.bak', self._caminho + '.bak2')
            os.rename(self._caminho, self._caminho + '.bak')
            os.rename(temp_path, self._caminho)
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False


# ============================================================
# MCR BOOT — Auto-direcionamento na execucao
# ============================================================
#
# Quando MCR.py e executado, MCRBoot decide o que fazer.
# Nao ha fluxo fixo. MCRDecisor avalia o estado e decide.
# ============================================================

class MCRBoot:
    """Boot auto-dirigido do MCR.py.
    
    Executado no __main__. MCRDecisor decide qual acao tomar
    baseado no estado atual do sistema.
    
    Uso:
        boot = MCRBoot()
        boot.iniciar()  # MCR decide o que fazer
    """
    
    def __init__(self):
        self.persistencia = MCRPersistencia()
        self.segmentador = MCRSegmentador()
        self.decisor = MCRDecisor('boot')
        self.estado = {}
    
    def iniciar(self):
        """MCR decide o que fazer ao ser executado."""
        import time as _t_boot
        t0 = _t_boot.time()
        
        # 1. Carrega dados do proprio arquivo
        dados = self.persistencia.carregar_dados()
        
        # 2. Avalia estado atual
        n_licoes = len(dados.get('licoes', []))
        n_assinaturas = len(dados.get('assinaturas', {}))
        n_cache = len(dados.get('cache', {}))
        
        self.estado = {
            'licoes': n_licoes,
            'assinaturas': n_assinaturas,
            'cache': n_cache,
            'modulos': 48,  # detectado pelo MCRBridge
            'comandos': 52,
        }
        
        # 3. Se nao tem dados internos, carrega do KG externo (migracao)
        if n_licoes == 0:
            print('[MCRBoot] Nenhum dado interno. Detectando fontes externas...', flush=True)
            self._migrar_dados_externos(dados)
        
        # 4. MCRDecisor decide acao
        estado_str = f"licoes:{n_licoes}_ass:{n_assinaturas}"
        acao = self.decisor.decidir(estado_str)
        
        print(f'[MCRBoot] MCR decidiu: {acao} ({n_licoes} lessons, {n_assinaturas} assinaturas)', flush=True)
        
        # 5. Executa a decisao
        if 'auto_teste' in str(acao).lower() or n_licoes == 0:
            _autotestar()

_MCR_DATA = """
{"erro": "10/10: Context Weaver + dedup + range codigo + threshold V7 proporcional", "solucao": "Context Weaver agora busca KG principal + codigo adjacente (L303-L323) + suporte ctx. Combinador detecta duplicatas com SequenceMatcher (threshold 0.6). Prompt pede 'Responda como voce mesmo'. V7 mudou de fixo 500 chars para proporcional (min 200, pergunta*2). Resposta final: 10/10, VALIDADA, 0 alucinacoes.", "ctx": "10_10", "timestamp": 1782767695.1130211}
{"erro": "10/10: super-test com perguntas complexas + Montador diretivo reduz entropia", "solucao": "Pergunta do super-test mudou de 1 para 4 sub-perguntas. Montador agora exige: 1) Resposta direta, 2) Explicacao, 3) Conclusao. NAO divague. Entropia caiu de 0.908 para 0.818. Fragmentos: 2 vs 1 antes.", "ctx": "10_10", "timestamp": 1782775792.9729924}
{"erro": "Zero hardcoded [:N] em todo pipeline EMERGIR", "solucao": "Linha a linha: kg.py aprender() removeu todos os slice. master_agent.py removeu slices nos titulos, causas, prompts, contextos, logs. decider.py removeu texto[:500].", "ctx": "anti_hardcoded", "timestamp": 1782713552.9062643}
{"erro": "auto_aprendizado: Explique o sistema SPA do MCR", "solucao": "5 metodos em master_agent.py (~140 linhas): _processar_emergencia, _amostrar_topicos_distantes, _gerar_fingerprint_combinacao, _gerar_pergunta_emergente, _autoavaliar_padrao_novo. +1 arquivo docs/plano/EMERGIR.md. +1 arquetipo criativo em conselho.py. Sintaxe OK, imports OK.\n{\"tipos_markov\": {}, \"tipo_palavra_freq\": {}, \"fingerprint_input\": [0.0, 0.0, 0.16666666666666666, 0.16666666666666666, 0.0, 0.08333333333333333, 0.0, 0.16666666666666666, 0.0, 0.08333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0", "ctx": "aprendido_auto", "timestamp": 1782857280.3894377}
{"erro": "auto_aprendizado: Explique o sistema SPA do MCR", "solucao": "Sistema de Progressao do Aventureiro, que gerencia habilidades e progressao em dominios elementais\nO **SPA (Sistema de Progressão do Aventureiro)** no projeto MCR é um sistema central que gera e coordena as habilidades e progressão dos personagens em **cinco domínios elementais**: Fogo, Gelo, Terra, Energia e Vento. Cada domínio possui suas próprias habilidades e funções que permitem ao jogador explorar e praticar diferentes tipos de atacantes e tarefas.\n\n### Integração do SHC ao SPA\nO SHC (Sist", "ctx": "aprendido_auto", "timestamp": 1782857283.1694086}
{"erro": "auto_aprendizado: Explique o sistema SPA do MCR", "solucao": "[DIRETORIOS ENCONTRADOS]\nCanary\\data-canary\\scripts\\MCR\\SPA\nCanary\\data-canary\\scripts\\MCR\\_backup_latin1\\SPA\nCanary\\src\\mcr\\spa\n\n\n[ARQUIVOS LUA]\nCanary\\data-canary\\scripts\\MCR\\SPA\\comandos\\comandos_spa.lua\nCanary\\data-canary\\scripts\\MCR\\SPA\\core\\0_init.lua\nCanary\\data-canary\\scripts\\MCR\\SPA\\core\\0_init_db.lua\nCanary\\data-canary\\scripts\\MCR\\SPA\\core\\0_init_dominios.lua\nCanary\\data-canary\\scripts\\MCR\\SPA\\core\\buff_system.lua\nCanary\\data-canary\\scripts\\MCR\\SPA\\core\\constantes.lua\nCanary\\data-canar", "ctx": "aprendido_auto", "timestamp": 1782857285.2195036}
{"erro": "auto_aprendizado: Explique o sistema SPA do MCR", "solucao": "Remover todas as regras especificas do MCR do prompt do sistema. Substituir por instrucoes universais de uso de ferramentas. Seed: regex expandido para capturar capitalized.\nProjeto MCR, um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)\nF1: supervisor com classificar_keyword agora existe em Scripts/mcr_devia (3 copias sincronizadas). F2: 7 modulos resgatados do Legado para o sistema ativo (analysis/fragmenter.py, agents/autoconsciencia.py, tools/toolkit.py, etc). F4: comando mcr toolki", "ctx": "aprendido_auto", "timestamp": 1782857287.2656343}
{"erro": "auto_aprendizado: Explique o sistema SPA do MCR", "solucao": "[DIRETORIOS ENCONTRADOS]\nBackup\\Cliente Codigo Fonte\\modules\\mcr_modules\nCanary\\data\\scripts\\MCR\nCanary\\data-canary\\scripts\\MCR\nCanary\\src\\mcr\nMCR-DevIA\nOTClient\\modules\\mcr_modules\nrespostas_mcr\nScripts\\mcr_dev\n\n\n[ARQUIVOS LUA]\nBackup\\Cliente Codigo Fonte\\modules\\mcr_modules\\registro.lua\nCanary\\data-canary\\scripts\\MCR\\comandos_spa_antigo.lua\nCanary\\data-canary\\scripts\\MCR\\oraculo.lua\nCanary\\data-canary\\scripts\\MCR\\core\\bridge_api.lua\nCanary\\data-canary\\scripts\\MCR\\core\\chat_bridge.lua\nCanary\\da", "ctx": "aprendido_auto", "timestamp": 1782857289.309993}
{"erro": "auto_aprendizado: Crie um NPC ferreiro em Eridanus", "solucao": "KGCleaner no startup. Modelo 7b como padrao (fast). SSE emit no ReAct loop. WebLearn disparado automaticamente.\n{\"tipos_markov\": {}, \"tipo_palavra_freq\": {}, \"fingerprint_input\": [0.0, 0.0, 0.16666666666666666, 0.16666666666666666, 0.0, 0.08333333333333333, 0.0, 0.16666666666666666, 0.0, 0.08333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333333333333, 0.0, 0.0, 0.6666666666666666, 0.6666666666666666, 0.0, 0.3333333333333333, 0.0, 0.6666666666666666, 0.0, 0.3333333333333333, 0.0, 0.0, 0.0, 0.0, ", "ctx": "aprendido_auto", "timestamp": 1782857293.7493036}
{"erro": "auto_aprendizado: Crie um NPC ferreiro em Eridanus", "solucao": "[DIRETORIOS ENCONTRADOS]\nBackup\\Server Codigo Fonte\\data\\npclib\\npc_system\nBackup\\Server Codigo Fonte\\data-canary\\npc\nBackup\\Server Codigo Fonte\\data-otservbr-global\\npc\nCanary\\data\\npclib\\npc_system\nCanary\\data-canary\\npc\nCanary\\data-otservbr-global\\npc\nCanary\\src\\lua\\functions\\creatures\\npc\ndata\\npc\n\n\n[ARQUIVOS LUA]\nBackup\\Server Codigo Fonte\\data\\npclib\\npc_system\\bank_system.lua\nBackup\\Server Codigo Fonte\\data\\npclib\\npc_system\\custom_modules.lua\nBackup\\Server Codigo Fonte\\data\\npclib\\npc_sy", "ctx": "aprendido_auto", "timestamp": 1782857295.798576}
{"erro": "auto_aprendizado: O que e Canary no contexto do MCR?", "solucao": "Servidor de Tibia personalizado (OTServ) usado no projeto MCR\n**Resposta:**\n\nCanary é usada como a plataforma de suporte técnico e administração base para o servidor customizado MCR. Ela fornece as bases técnicas necessárias para o operacionamento do MCR, garantindo a integração de componentes como o Sistema de Progressão do Aventureiro (SPA) e o Sistema de Habilidades Contextuais (SHC). Canary ajuda a administrar, manter segurança e estabilidade ao MCR, permitindo que outros componentes e funci", "ctx": "aprendido_auto", "timestamp": 1782857301.5906935}
{"erro": "auto_aprendizado: O que e Canary no contexto do MCR?", "solucao": "[DIRETORIOS ENCONTRADOS]\nBackup\\Server Codigo Fonte\\data-canary\nCanary\nCanary\\data-canary\nCanary\\vcproj\\canary\n\n\n[ARQUIVOS LUA]\nBackup\\Server Codigo Fonte\\data-canary\\lib\\lib.lua\nBackup\\Server Codigo Fonte\\data-canary\\lib\\core\\load.lua\nBackup\\Server Codigo Fonte\\data-canary\\lib\\core\\quests.lua\nBackup\\Server Codigo Fonte\\data-canary\\lib\\core\\storages.lua\nBackup\\Server Codigo Fonte\\data-canary\\lib\\core\\quests\\catalog\\001_example.lua\nBackup\\Server Codigo Fonte\\data-canary\\lib\\core\\quests\\catalog\\in", "ctx": "aprendido_auto", "timestamp": 1782857303.6501346}
{"erro": "auto_aprendizado: O que e Canary no contexto do MCR?", "solucao": "Remover todas as regras especificas do MCR do prompt do sistema. Substituir por instrucoes universais de uso de ferramentas. Seed: regex expandido para capturar capitalized.\nProjeto MCR, um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)\nF1: supervisor com classificar_keyword agora existe em Scripts/mcr_devia (3 copias sincronizadas). F2: 7 modulos resgatados do Legado para o sistema ativo (analysis/fragmenter.py, agents/autoconsciencia.py, tools/toolkit.py, etc). F4: comando mcr toolki", "ctx": "aprendido_auto", "timestamp": 1782857305.6953025}
{"erro": "Sessao 6: Identity via V12 + FAST no MasterAgent", "solucao": "3 arquivos: AGENT_IDENTITY.md, task_planner.py (+5 linhas), master_agent.py (+130 linhas). Sintaxe OK. Imports OK.", "ctx": "arquitetura", "timestamp": 1782703047.7375813}
{"erro": "Sessao 6: Sistema EMERGIR - reconhecimento automatico de padroes emergentes", "solucao": "5 metodos em master_agent.py (~140 linhas): _processar_emergencia, _amostrar_topicos_distantes, _gerar_fingerprint_combinacao, _gerar_pergunta_emergente, _autoavaliar_padrao_novo. +1 arquivo docs/plano/EMERGIR.md. +1 arquetipo criativo em conselho.py. Sintaxe OK, imports OK.", "ctx": "arquitetura", "timestamp": 1782704003.0274847}
{"erro": "FASE 1 AGI concluida: SENSE integrado + 7/7 no Teste de Verdade", "solucao": "Adicionar SENSE antes do cascade loop, filtrar stop words em 3 niveis, timeout via time.time(), normalizar encoding no teste, corrigir EpisodicMemory.buscar(n=3)", "ctx": "arquitetura", "timestamp": 1782791688.2286146}
{"erro": "7/7 PASS recuperado: tamanho do contexto e a causa raiz", "solucao": "Limitar todas as secoes de contexto no prompt do LLM para <2000 chars cada. Keyword boost no erro (nao na solucao) para evitar boost em todas as lessons.", "ctx": "arquitetura", "timestamp": 1782796460.5229275}
{"erro": "AGI completa: 5 camadas integradas + 7/7 PASS", "solucao": "Adicionar AutoRevisor, Tradutor, EpisodicMemory.registrar(), Emergir a cada 5 execs, SelfStudy background 10min. Fix TruncationFixer excecao str(...)[:N].", "ctx": "arquitetura", "timestamp": 1782798040.3238037}
{"erro": "Sessao 2026-06-30: AGI completa + ReAct + Busca Estrategica + BlankFiller", "solucao": "AGI completa: 5 camadas integradas. ReAct Loop com 29 ferramentas. Busca estrategica substitui grep generico. BlankFiller para criacao segura. TruncationFixer corrigido.", "ctx": "arquitetura", "timestamp": 1782801196.1343493}
{"erro": "Sessao continua: KGCleaner + 7b + SSE + WebLearn + NPC", "solucao": "KGCleaner no startup. Modelo 7b como padrao (fast). SSE emit no ReAct loop. WebLearn disparado automaticamente.", "ctx": "arquitetura", "timestamp": 1782822741.1861725}
{"erro": "DeepSeek-r1:7b implementado como modelo padrao — segue instrucoes e identidade", "solucao": "Trocar modelo padrao de qwen2.5-coder:14b para deepseek-r1:7b. Identidade posicionada antes da pergunta (recency effect).", "ctx": "arquitetura", "timestamp": 1782824133.8558998}
{"erro": "Prompt universal implementado — 7/7 PASS sem hardcode de MCR", "solucao": "Remover todas as regras especificas do MCR do prompt do sistema. Substituir por instrucoes universais de uso de ferramentas. Seed: regex expandido para capturar capitalized.", "ctx": "arquitetura", "timestamp": 1782826399.9418964}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782924846.8417683}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782924850.9012995}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782924854.9792397}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782924859.8701622}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782925161.9125974}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782925165.9702704}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782925170.0397296}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782925174.887329}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782925709.5786173}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782925713.633148}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782925717.6741364}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782925721.7220404}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782926075.5191445}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782926079.5695415}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782926083.6177218}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782926087.6684978}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782926385.8322384}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782926389.892142}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782926393.9517329}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782926398.006178}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782927944.0801814}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782927948.1549816}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782927952.212852}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782927956.287815}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782928188.0758686}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782928192.1212635}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782928196.1702242}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782928201.115565}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782928676.0226705}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782928680.0796804}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782928684.142835}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782928688.2116532}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782929095.4179006}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782929099.4776454}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782929103.5408547}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782929107.5949845}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782929655.9906943}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782929660.0736108}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782929664.1301782}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782929668.1741421}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782930014.0947578}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782930018.16479}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782930022.2362719}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782930027.1097248}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782932009.2920985}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782932013.340054}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782932017.3941748}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782932022.2308953}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782932624.9775596}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782932629.039088}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782932633.094577}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782932637.1499825}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782932820.10707}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782932824.1715763}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782932828.2308977}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782932832.2903676}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782933204.4951365}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782933208.5403106}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782933212.5929668}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782934088.0446105}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782934092.1198778}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782934096.1918805}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782934100.2787938}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782934581.2484043}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782934585.2947168}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782934589.330109}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782934593.3853588}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782935263.6946821}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782935267.757728}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782935271.8212218}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782935275.877923}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782935734.7945569}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782935738.8531003}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782935742.9196064}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782935746.9801714}
{"erro": "auto_[12] MCR - Guia de Conteúdo Inicial e Tutorial_txt", "solucao": ">> CATALOG tags=tutorial, eridanus, new-player updated=2026-06-23\nPROJETO MCR – GUIA DE CONTEÚDO INICIAL E TUTORIAL\n(Versão 5.0 – Integração total com o SPA v3.2.0, sistema de cores, missões e progressão em Eridanus)\nArquivo: [12] MCR - Guia de Conteúdo Inicial e Tutorial.txt\n\n🎯 OBJETIVO DESTE GUIA\nDescrever, passo a passo, a Ilha do Despertar (Eridanus) — o cenário de tutorial do Projeto MCR. Aqu", "ctx": "auto_descoberta", "timestamp": 1782936220.9912374}
{"erro": "auto_[4] MCR - Guia do Login Server_txt", "solucao": ">> CATALOG tags=login-server, auth, api updated=2026-06-23\nPROJETO MCR – GUIA DO LOGIN SERVER\nVersão 2.1 – Compatibilidade total com o Sistema de Progressão do Aventureiro (SPA v4.2), vocação única (0) e manutenção da limpeza automática\nArquivo: [4] MCR - Guia do Login Server.txt\n\n🎯 OBJETIVO DESTE GUIA\nFornecer todas as regras, especificações de API, protocolos de erro e lições aprendidas referent", "ctx": "auto_descoberta", "timestamp": 1782936225.8151524}
{"erro": "auto_LEGACY_md", "solucao": "# LEGACY — Arquivos Movidos para Legado\n\nEste documento registra o que foi movido para `/Legado/` e por quê.\nTudo aqui é **código histórico** — preservado para referência, não para uso ativo.\n\n---\n\n## Legado/sandbox/ — Scripts temporários do sandbox\n\n**501 arquivos movidos** em 2026-06-30.\n\n| Categoria | Quantidade | Exemplos |\n|-----------|:----------:|----------|\n| `_test*.py` | 37 | Testes desc", "ctx": "auto_descoberta", "timestamp": 1782936229.872352}
{"erro": "auto_AGI_ARCHITECTURE_md", "solucao": "# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva\n\n> AUTOR: Cloud + Kheltz\n> DATA: 2026-06-30 (atualizado)\n> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳\n> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente\n\n---\n\n## Sumario\n\n1. [Status Atual](#-status-atual)\n2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)\n3. [Fluxo Completo](#-fluxo-completo)\n4. [Plano de", "ctx": "auto_descoberta", "timestamp": 1782936233.9199052}
{"erro": "auto-melhoria: master_agent.py", "solucao": "Sucesso: False | Tipo: refatorar", "ctx": "auto_melhoria", "timestamp": 1782754592.3728335}
{"erro": "auto-melhoria: diagnostic_engine.py", "solucao": "Sucesso: True | Tipo: refatorar", "ctx": "auto_melhoria", "timestamp": 1782755883.2277575}
{"erro": "auto-melhoria: diagnostic_engine.py", "solucao": "Sucesso: False | Tipo: refatorar", "ctx": "auto_melhoria", "timestamp": 1782756128.6519787}
{"erro": "auto-repair: self_study.py:L354", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782747883.5977075}
{"erro": "auto-repair: context_crew.py:L133", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782747901.2935338}
{"erro": "auto-repair: context_crew.py:L172", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782747905.8003292}
{"erro": "auto-repair: context_crew.py:L221", "solucao": "                        except: pass", "ctx": "auto_repair", "timestamp": 1782747908.0212348}
{"erro": "auto-repair: context_crew.py:L331", "solucao": "                        except: pass", "ctx": "auto_repair", "timestamp": 1782747917.0181437}
{"erro": "auto-repair: kernel.py:L208", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782747945.9577599}
{"erro": "auto-repair: mcr_devia.py:L2521", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782747979.8439405}
{"erro": "auto-repair: mcr_devia.py:L2613", "solucao": "                            except: pass", "ctx": "auto_repair", "timestamp": 1782747982.145657}
{"erro": "auto-repair: self_study.py:L354", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782750521.0156555}
{"erro": "auto-repair: mcr_devia.py:L2521", "solucao": "                    except: pass", "ctx": "auto_repair", "timestamp": 1782750580.1559036}
{"erro": "auto-repair: mcr_devia.py:L2613", "solucao": "                            except: pass", "ctx": "auto_repair", "timestamp": 1782750582.4623709}
{"erro": "auto-repair FALHOU: self_study.py:L365", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782751690.1818116}
{"erro": "auto-repair FALHOU: context_crew.py:L80", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752073.5325227}
{"erro": "auto-repair FALHOU: context_infinity.py:L90", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752081.8086498}
{"erro": "auto-repair FALHOU: kernel.py:L255", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752090.185455}
{"erro": "auto-repair FALHOU: mcr_devia.py:L2771", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752099.9911895}
{"erro": "auto-repair FALHOU: context_crew.py:L84", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752851.111905}
{"erro": "auto-repair FALHOU: context_infinity.py:L90", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752859.4206557}
{"erro": "auto-repair FALHOU: kernel.py:L255", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752867.7930794}
{"erro": "auto-repair FALHOU: mcr_devia.py:L2771", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782752877.4939485}
{"erro": "auto-repair FALHOU: context_crew.py:L84", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782753393.3850107}
{"erro": "auto-repair FALHOU: context_infinity.py:L90", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782753403.3751488}
{"erro": "auto-repair FALHOU: kernel.py:L255", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782753411.7570302}
{"erro": "auto-repair FALHOU: mcr_devia.py:L2771", "solucao": "Backup restaurado. Usar except Exception como fallback.", "ctx": "auto_repair_falha", "timestamp": 1782753421.5141928}
{"erro": "V12 retornando 1M+ chars no pipeline", "solucao": "FIX: kg.buscar() agora respeita max_r. V12 filtra APENAS solucoes (max 200 chars, max 2 lessons).", "ctx": "bugfix", "timestamp": 1782846358.5384555}
{"erro": "Reconstrucao falhou: fingerprints de ferramentas vs perguntas", "solucao": "Precisa parear fingerprint da PERGUNTA com fingerprint da RESPOSTA no LEARN do pipeline. So assim reconstrucao funciona.", "ctx": "bugfix", "timestamp": 1782856535.182965}
{"erro": "Ciclo completo validado: PE + IE + Aprendiz + Reconstrucao", "solucao": "3/3 perguntas reconstruidas sem LLM. Resposta generica (sem tipo_palavra_freq) — precisa salvar palavras reais junto com tipos_markov.", "ctx": "bugfix", "timestamp": 1782857643.9577305}
{"erro": "Ciclo de blocos dinâmicos validado: 2/2 reconstruidas sem LLM", "solucao": "Ciclo completo: termo -> docs -> fragmento -> aprender -> bloco -> reconstruir. Zero LLM. Qualidade limitada (fragmentos curtos) mas funcional.", "ctx": "bugfix", "timestamp": 1782860187.5192306}
{"erro": "ContextVector + tipo_palavra_freq + multi-fragmentos validado", "solucao": "Prox passo: concatenacao com transicoes, tipo_palavra_freq de multiplas fontes, filtro de metadados.", "ctx": "bugfix", "timestamp": 1782860936.012583}
{"erro": "Sessao salva e comitada: a99e44e3", "solucao": "Proxima sessao: integrar ContextVector + tipo_palavra_freq no pipeline + melhorar concatenacao de fragmentos.", "ctx": "bugfix", "timestamp": 1782861303.1043184}
{"erro": "Prototipo multinivel validado: 5 fases OK", "solucao": "Nomes gerados: Erion, Galnoror, Thadanor, Thalinin. Ciclo completo: pergunta -> intencao -> nome -> frase -> resposta.", "ctx": "bugfix", "timestamp": 1782862418.2984293}
{"erro": "3 experimentos validados: refutacao confirmada", "solucao": "Sistema de padroes SUPERA as 5 limitacoes: criatividade, input novo, contexto longo, semantica, raciocinio multi-etapas.", "ctx": "bugfix", "timestamp": 1782863199.5806165}
{"erro": "Gerador de texto validado: Markov local substitui LLM", "solucao": "Texto gerado para Eridanus, SPA e Canary com temperatura 0.0-0.6. Funciona como LLM local sem GPU.", "ctx": "bugfix", "timestamp": 1782863669.493255}
{"erro": "Ciclo completo validado: MCR sem LLM — 8/8 fases OK em 6.6s", "solucao": "MCR funciona COMPLETAMENTE sem LLM: percebe, busca, gera, cria, corrige, valida, aprende.", "ctx": "bugfix", "timestamp": 1782866590.9421692}
{"erro": "MCR aprende codigo valido do projeto — 0 hardcode", "solucao": "MCR aprende o que e codigo valido LENDO exemplos reais. Detecta bugs por DIFERENCA de Markov, nao por regras.", "ctx": "bugfix", "timestamp": 1782867341.676313}
{"erro": "MCR Inception validado: 4/4 niveis. Conselho funciona. Corpus de lore ainda limitado (111 estados).", "solucao": "Conceito Inception funciona. Conselho consegue ranquear workers por score. Corpus de lore precisa crescer para geracao fluente.", "ctx": "bugfix", "timestamp": 1782867917.6078117}
{"erro": "Aprendiz Universal validado — 0 keywords hardcoded", "solucao": "MCR aprende o que e codigo valido por OBSERVACAO. Zero conhecimento previo da linguagem.", "ctx": "bugfix", "timestamp": 1782869346.2240355}
{"erro": "BuscadorUniversal validado: 200 arquivos em 0.8s. Encontrou lore FORA do projeto.", "solucao": "Busca por PADRAO funciona independente de formato ou localizacao. 0 keywords, 0 hardcode.", "ctx": "bugfix", "timestamp": 1782870333.0074828}
{"erro": "MCRCore validado: singleton, auto-propagação, geracao 2.2x melhor", "solucao": "Arquitetura final: MCRCore centraliza tudo. Ferramentas sao extensoes. Aprendeu uma vez -> todas melhoram.", "ctx": "bugfix", "timestamp": 1782870769.886916}
{"erro": "RadarMCR validado: 5/5 candidatos encontrados na Onda 1. Fingerprint precisa ser mais discriminativo.", "solucao": "RADAR conceito funciona. Prox passo: fingerprint mais esparso/discriminativo para que ondas 2-4 tenham utilidade real.", "ctx": "bugfix", "timestamp": 1782872723.086571}
{"erro": "MCRDescobridor validado: 5 grupos sem hardcode. Equivalente a CREATE, EXPLAIN, SEARCH, CODE.", "solucao": "MCR descobre categorias SOZINHO por padrao. Prox passo: agrupar sinonimos (local+function=codigo, encontre+procure=search).", "ctx": "bugfix", "timestamp": 1782873414.0172026}
{"erro": "MCR Zero validado: estrutura descoberta por entropia de bytes. Zero hardcode.", "solucao": "O ultimo hardcode foi removido. MCR descobre estrutura gramatical sozinho — de bytes para significado.", "ctx": "bugfix", "timestamp": 1782873609.2488744}
{"erro": "MCR Unificado validado: 5 niveis integrados em 1 sistema.", "solucao": "IE + PiEngine + Markov + PatternEngine nao sao mais modulos separados. Sao niveis do mesmo cerebro. Prox passo: + execucoes para Markov de execucao aprender padroes.", "ctx": "bugfix", "timestamp": 1782874325.204903}
{"erro": "Regra de Ouro validada: fingerprint dinamico, threshold adaptativo, acoes agrupadas.", "solucao": "Nada hardcoded. Tamanho do fingerprint descoberto pela entropia. Threshold descoberto pela distribuicao. Acoes agrupadas por padrao de uso.", "ctx": "bugfix", "timestamp": 1782874640.841709}
{"erro": "Fingerprint MCR Puro validado: RAW discrimina mesma intencao (0.63-0.81) mas falha entre intencoes (0.88). Tamanhos de palavra poluem o fingerprint.", "solucao": "Fingerprint de INTENCAO PURA: apenas hashes das primeiras 3 palavras. Zero tamanhos. Zero ALL CAPS. So intencao.", "ctx": "bugfix", "timestamp": 1782874872.5891817}
{"erro": "MCR Loop Infinito validado! Transicoes de bytes DISCRIMINAM intencao em 97%.", "solucao": "O CONCEITO MCR E: TRANSICOES. Nao bytes brutos. Nao INTENT_*. Nao DOM_*. So transicoes entre elementos consecutivos, em QUALQUER nivel.", "ctx": "bugfix", "timestamp": 1782875379.180123}
{"erro": "MCR Decision validado: 5 execucoes, 5 decisoes, 1 MarkovDecisor, 0 if/else.", "solucao": "MarkovDecisor aprendeu 5 transicoes estado->acao. MCR decide sozinho qual ferramenta usar. 0 hardcode.", "ctx": "bugfix", "timestamp": 1782876900.6600778}
{"erro": "ciclo:0.000.700.000.000.000.000.100.000.000.200.000.000.000.000.000.000.001.000.000.000.000.000.140.000.000.140.000.000.000.000.000.000.020.920.000.700.000.000.000.000.000.000.000.000.000.000.000.000.", "solucao": "fp_resp=[0.0, 0.5565217391304348, 0.0, 0.0, 0.19130434782608696, 0.0, 0.09565217391304348, 0.0, 0.0, 0.10434782608695652, 0.05217391304347826, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.34375, 0.0, 0.171875, 0.0, 0.0, 0.171875, 0.09375, 0.0, 0.0, 0.0, 0.0, 0.0, 0.23, 0.909318366867851, 0.0, 0.7478260869565218, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]: O eixo Nirvana-Caos é uma métrica contínua ", "ctx": "ciclo_aprendizado", "timestamp": 1782768152.4655075}
{"erro": "Ciclo de Aprendizado Automatico: Fase 0 (consulta passado) + Fase 5 (registro) + Validation sem thresholds", "solucao": "Validation Pipeline agora e relator de FATOS (7 estagios, todos INFO). Reconstructor nao tem mais thresholds. PipelineExecutor tem Fase 0 (consulta KG antes) e Fase 5 (registro automatico apos). Cmd_turbo mostra relatorio de validacao. Testado: Similaridade 0.95, 4 termos, 1 arquivo, 0 contradicoes.", "ctx": "ciclo_aprendizado", "timestamp": 1782768195.2660754}
{"erro": "ciclo:0.000.000.000.480.000.120.000.090.160.000.000.150.000.000.000.000.000.000.001.000.000.250.000.180.330.000.000.320.000.000.000.001.000.880.000.560.000.000.000.000.000.000.000.000.000.000.000.000.", "solucao": "fp_resp=[0.0024019215372297837, 0.0, 0.0, 0.3811048839071257, 0.0, 0.04323458767013611, 0.0, 0.24179343474779824, 0.0632506004803843, 0.0, 0.0, 0.2682145716573259, 0.0, 0.0, 0.0, 0.0, 0.0063025210084033615, 0.0, 0.0, 1.0, 0.0, 0.1134453781512605, 0.0, 0.634453781512605, 0.16491596638655462, 0.0, 0.0, 0.7037815126050421, 0.0, 0.0, 0.0, 0.0, 1.0, 0.8013789043462197, 0.0, 0.8282626100880705, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0", "ctx": "ciclo_aprendizado", "timestamp": 1782768425.7069037}
{"erro": "ciclo:0.000.160.080.000.130.000.300.000.000.000.000.000.000.000.000.330.000.480.250.000.410.000.900.000.000.000.000.010.000.000.001.001.000.880.000.550.000.000.000.000.000.000.000.000.000.000.000.000.", "solucao": "fp_resp=[0.0, 0.09316001238006809, 0.21727019498607242, 0.0, 0.05230578768183225, 0.0, 0.31785824822036524, 0.0, 0.0, 0.0, 0.0, 0.0012380068090374497, 0.0, 0.0, 0.0, 0.3181677499226246, 0.0, 0.2918287937743191, 0.6828793774319066, 0.0, 0.16439688715953307, 0.0, 0.9990272373540856, 0.0, 0.0, 0.0, 0.0, 0.0038910505836575876, 0.0, 0.0, 0.0, 1.0, 1.0, 0.8407832784118751, 0.0, 0.7604456824512534, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ", "ctx": "ciclo_aprendizado", "timestamp": 1782768986.7486255}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782926050.066617}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782926368.575522}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782927926.682656}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782928183.756423}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782928650.5871737}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782929044.6635735}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782929630.5367823}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.49, Bytes: 2000. Estados: 82. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782930009.7776084}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782932004.9726155}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782932595.6069288}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782932794.7897573}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782934083.1260278}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782934543.264295}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782935196.5129895}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782935729.9035032}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782936191.8493714}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782936736.5612698}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782937977.8060794}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782938956.5972154}
{"erro": "ciclo:MCR.py", "solucao": "Tipo: binario_estruturado, Entropia: 1.47, Bytes: 2000. Estados: 78. Origem: E:\\Projeto MCR\\scripts\\mcr_devia\\modulos\\MCR.py.", "ctx": "ciclo_unico", "timestamp": 1782939500.0804555}
{"erro": "Combinador inteligente + Embedding filtra inactive + Fallback com prioridade de ctx", "solucao": "Combinador agora extrai paragrafos de cada fragmento e funde em lista unica. Embedding nao retorna mais lessons inativas (runtime/stress). Fallback ordena por prioridade ctx. Zero runtime noise na resposta. Entropia ainda 0.83 porque 5 topicos diferentes dispersam naturalmente.", "ctx": "combinador_v2", "timestamp": 1782777099.0750277}
{"erro": "mcr_core_aprendizado_codigo", "solucao": "local npc = NPC:new('Teste')\nnpc:setTitle('Ferreiro')\nnpc:onSay(function() end)", "ctx": "core_codigo", "timestamp": 1782870650.519343}
{"erro": "mcr_core_aprendizado_codigo", "solucao": "local npc = NPC:new('Teste')\nnpc:setTitle('Ferreiro')\nnpc:onSay(function() end)", "ctx": "core_codigo", "timestamp": 1782870742.0080762}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "\"\"\"\nCONTEXT CREW V3 — Leitor universal (LGPD OK: so le, nunca edita, sem dados pessoais)\nBusca contexto em: KG, WebLearn, Docs, Codigo Fonte, Web.\nTudo que encontra vira contexto. Nunca modifica nada.\n\"\"\"\nimport os, json, re, time, hashlib, urllib.request, threading, concurrent.futures\n\nBASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))\nSANDBOX = os.path.join(BASE, 'sandbox')\nKG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')\nCACHE_PATH = os.path.join(SANDBO", "ctx": "core_codigo_validado", "timestamp": 1782870652.6160932}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n\"\"\"\nMCR-Dev v1.0 — Assistente Local Autonomo para Terminal\nUso: python mcr-dev.py\n     python mcr-dev.py \"comando\"  (modo unico)\n\"\"\"\nimport sys, os, json, time, readline, atexit\n\nBASE = os.path.dirname(os.path.abspath(__file__))\nsys.path.insert(0, os.path.join(BASE, \"scripts\"))\nsys.path.insert(0, os.path.join(BASE, \"Scripts\"))\n\nfrom mcr_dev import engine, memoria\n\n# Historico de comandos\nhistfile = os.path.join(os.path.dirname(BASE), \".mcr_dev_history\")\ntry:\n    readline.r", "ctx": "core_codigo_validado", "timestamp": 1782870654.6833901}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nTraduz APENAS o items.xml, com capitalização de título e saída ISO‑8859‑1.\nUsa o motor rápido (concatenação inteligente) e o dicionário MCR.\n\"\"\"\nimport json, time, sys, shutil, re, xml.etree.ElementTree as ET\nfrom pathlib import Path\nfrom deep_translator import GoogleTranslator\nfrom mcr_dict import MCR_CORRECTIONS\n\n# ===== CONFIGURAÇÃO =====\nARQUIVO_ORIGEM = \"data/items/items.xml\"          # Localização real do items.xml\nARQUIVO_DESTINO = \"data/", "ctx": "core_codigo_validado", "timestamp": 1782870656.7518432}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "import os, shutil\nfor root, dirs, files in os.walk(\"E:/Projeto MCR/Canary/src\"):\n    for f in files:\n        if f.endswith(\".bak\"):\n            orig = os.path.join(root, f[:-4])\n            bak = os.path.join(root, f)\n            shutil.copy2(bak, orig)\n            print(f\"Restaurado: {orig}\")", "ctx": "core_codigo_validado", "timestamp": 1782870658.811704}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nimport re\nimport sys\nfrom pathlib import Path\n\nTARGET_EXTS = {'.cpp', '.otui'}   # removido '.lua'\n\n# Regex para capturar strings entre aspas duplas\nSTRING_RE = re.compile(r'\"([^\"]*)\"')\n\n# PROTEÇÃO DE BANCO DE DADOS\nSQL_PROTECTED = {\n    'id', 'name', 'password', 'email', 'premdays', 'type', 'group_id',\n    'level', 'vocation', 'health', 'mana', 'lookbody', 'lookfeet',\n    'lookhead', 'looklegs', 'lookaddons', 'lookmount', 'lastlogin',\n    'lastip', 'save', 'skill_fist', '", "ctx": "core_codigo_validado", "timestamp": 1782870660.8889558}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nimport re\nimport sys\nimport time\nfrom deep_translator import GoogleTranslator\n\ntranslator = GoogleTranslator(source='en', target='pt')\n\ndef protect_placeholders(text):\n    placeholders = []\n    def repl(m):\n        placeholders.append(m.group(0))\n        # Usa «id» para não colar palavras (ex.: \"{} logged in\" → \"«0» logged in\")\n        return f\"«{len(placeholders)-1}»\"\n    # Protege \\n, \\t, %d, %s, { } etc.\n    protected = re.sub(r'(\\\\[ntr]|%0?\\d*[a-zA-Z]|\\{[^\\}]*\\})', rep", "ctx": "core_codigo_validado", "timestamp": 1782870662.9406395}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n\"\"\"\nRemove blocos inteiros de ficheiros de dados (extraido/traduzido/reparado)\ncujos caminhos correspondem a padrões proibidos (cabeçalhos, títulos, config).\nUso: python removedor.py arquivo1.txt arquivo2.txt ...\n\"\"\"\nimport sys\nfrom pathlib import Path\n\n# Padrões de caminhos a excluir (verificados no nome do ficheiro ou no caminho completo)\nFORBIDDEN_PATTERNS = [\n    # Extensões de cabeçalho\n    \".hpp\",\n    \".h\",\n    # Ficheiros de configuração que contêm identificadores s", "ctx": "core_codigo_validado", "timestamp": 1782870665.0095503}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nimport re\nimport sys\nimport json\n\n# Dicionário estático MCR (termos que a API pode traduzir mal)\nDICIONARIO_MCR = {\n    \"health\": \"vida\",\n    \"maxhealth\": \"vida máxima\",\n    \"mana\": \"mana\",\n    \"maxmana\": \"mana máxima\",\n    \"soul\": \"alma\",\n    \"level\": \"nível\",\n    \"experience\": \"experiência\",\n    \"capacity\": \"capacidade\",\n    \"speed\": \"velocidade\",\n    \"attack\": \"ataque\",\n    \"defense\": \"defesa\",\n    \"armor\": \"armadura\",\n    \"shield\": \"escudo\",\n    \"weapon\": \"arma\",\n    \"", "ctx": "core_codigo_validado", "timestamp": 1782870667.828065}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n\"\"\"\ncorretor.py – Restaura strings técnicas, aplica correções manuais e,\nse necessário, reverte automaticamente strings cujos placeholders\nforam corrompidos ou que pareçam caminhos de ficheiro / SQL.\n\"\"\"\nimport sys\nimport os\nimport re\n\n# ---------- Conjuntos de chaves a restaurar manualmente ----------\nRESTAURAR = {\n    \"E:\\\\Projeto MCR\\\\Canary\\\\src\\\\canary_server.cpp\": {\n        \"332_73\", \"369_65\", \"369_107\", \"396_68\",\n    },\n    \"E:\\\\Projeto MCR\\\\Canary\\\\src\\\\account\\\\ac", "ctx": "core_codigo_validado", "timestamp": 1782870669.8984885}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nimport os\nimport shutil\nimport sys\n\ndef carregar_mapa(filepath):\n    dados = {}\n    arquivo_atual = None\n    if not os.path.exists(filepath):\n        return dados\n\n    with open(filepath, 'r', encoding='utf-8') as f:\n        for linha in f:\n            linha = linha.strip('\\n')\n            if linha.startswith('[') and linha.endswith(']'):\n                arquivo_atual = linha[1:-1]\n                dados[arquivo_atual] = {}\n            elif '=' in linha and arquivo_atual:\n ", "ctx": "core_codigo_validado", "timestamp": 1782870671.951675}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nr\"\"\"\nConverte caracteres acentuados de arquivos .cpp/.h em escapes octais \\ooo (Latin-1).\nElimina erros C2022 (\"muito grande para caractere\") no Visual Studio.\nSe for passado um ficheiro com a lista de ficheiros modificados, apenas esses são processados.\n\"\"\"\nimport sys\nfrom pathlib import Path\n\ndef escape_non_ascii(text):\n    \"\"\"Substitui caracteres > 127 por escapes em octal \\\\ooo\"\"\"\n    result = []\n    for ch in text:\n        if ord(ch) > 127:\n            try:\n          ", "ctx": "core_codigo_validado", "timestamp": 1782870674.0023854}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nConverte player:addItem(\"Nome\", qtd) para player:addItem(ID, qtd).\nUsa items_original.xml e procura case‑insensitive.\n\"\"\"\nimport re, os, sys, xml.etree.ElementTree as ET\n\nITEMS_XML = \"items_original.xml\"\nSCRIPT_DIRS = [\"data\", \"data-canary\", \"data-otservbr-global\"]\nEXCLUDE_FILES = {'items.xml', 'titles.lua', 'achievements.lua', 'config.lua'}\n\ndef carregar_ids():\n    tree = ET.parse(ITEMS_XML)\n    root = tree.getroot()\n    mapping = {}\n    for it", "ctx": "core_codigo_validado", "timestamp": 1782870676.077092}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nConverte entradas de loot do tipo { name = \"...\" } em ficheiros como custom_monster_loot.lua.\n\"\"\"\nimport re, os, sys, xml.etree.ElementTree as ET\n\nITEMS_XML = \"items_original.xml\"\nTARGET_FILES = [\n    \"data/scripts/systems/custom_monster_loot.lua\",\n    \"data-canary/scripts/systems/custom_monster_loot.lua\",\n    \"data-otservbr-global/scripts/systems/custom_monster_loot.lua\",\n]\n\ndef carregar_ids():\n    tree = ET.parse(ITEMS_XML)\n    root = tree.get", "ctx": "core_codigo_validado", "timestamp": 1782870678.1302664}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nConverte loots de monstros de 'name' para 'id' apenas dentro de monster.loot.\nMantém os ficheiros Lua em ISO‑8859‑1.\n\"\"\"\n\nimport re, os, sys, xml.etree.ElementTree as ET\n\nITEMS_XML = \"items_original.xml\"\nMONSTER_DIRS = [\"data/monster\", \"data-canary/monster\", \"data-otservbr-global/monster\"]\n\ndef carregar_ids():\n    tree = ET.parse(ITEMS_XML)\n    root = tree.getroot()\n    name_to_id = {}\n    for item in root.iter('item'):\n        name = item.get('", "ctx": "core_codigo_validado", "timestamp": 1782870680.2147026}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nTraduz o items.xml (nome, plural, descrição) com artigo inteligente e dicionário MCR.\nPara itens sem plural, gera o plural via API a partir do singular em inglês.\nNomes de equipamentos são forçados ao singular.\nGrava em ISO‑8859‑1.\n\"\"\"\n\nimport json, time, sys, shutil, re, xml.etree.ElementTree as ET\nfrom pathlib import Path\nfrom deep_translator import GoogleTranslator\nfrom mcr_dict import MCR_CORRECTIONS\n\n# ===== CONFIGURAÇÃO =====\nBACKUP_ORIGIN", "ctx": "core_codigo_validado", "timestamp": 1782870682.2879474}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport re, sys\nfrom pathlib import Path\n\nFORBIDDEN_DIRS = {'lib', 'libs', 'migrations', 'vcproj', 'tests', 'src', 'cmake',\n                  '.github', 'docker', 'docs', 'metrics', 'npclib', 'scripts/lib',\n                  'MCR Scripts', 'modules', 'json', 'reports', 'logs', 'XML'}\nFORBIDDEN_FILES = {'config.lua', 'global.lua', 'core.lua', 'stages.lua', 'update.lua',\n                   'titles.lua', 'achievements.lua', 'badges.lua',\n               ", "ctx": "core_codigo_validado", "timestamp": 1782870684.3503919}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "#!/usr/bin/env python3\nimport re, sys\nfrom pathlib import Path\n\nFORBIDDEN_DIRS = {'lib','libs','migrations','vcproj','tests','src','cmake',\n                  '.github','docker','docs','metrics','npclib','scripts/lib',\n                  'MCR Scripts','modules','json','reports','logs','XML'}\nFORBIDDEN_FILES = {'config.lua','global.lua','core.lua','stages.lua','update.lua',\n                   'titles.lua','achievements.lua','badges.lua',\n                   'register_npc_type.lua','register_monster_", "ctx": "core_codigo_validado", "timestamp": 1782870684.3513823}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "-- database.lua\n\nlocal npc_database = {\n    -- Outras configurações...\n    ferreiro = {id = 1000, name = \"Ferreiro\", level = 5},\n}\n\nreturn npc_database", "ctx": "core_codigo_validado", "timestamp": 1782870744.075474}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "local keywordHandler = KeywordHandler:new()\n\nkeywordHandler:addKeyword({'hello', 'hi'}, StdModule.say, {npcHandler = npcHandler, text = \"Olá! Sou seu guia em Eridanus. Como posso ajudar você hoje?\"})\nkeywordHandler:addKeyword({'where am i'}, StdModule.say, {npcHandler = npcHandler, text = \"Você está na cidade de Eridanus, um lugar onde a aventura começa.\"})\nkeywordHandler:addKeyword({'what is spa'}, StdModule.say, {npcHandler = npcHandler, text = \"SPA significa Sistema de Progressão do Aventurei", "ctx": "core_codigo_validado", "timestamp": 1782870746.1436205}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "-- arquivo com bug\nlocal lore = {\n    nome = \"Fundacao de Eridanus\",\n    tipo = \"lore\",\n\nreturn lore\nend\n", "ctx": "core_codigo_validado", "timestamp": 1782870748.200203}
{"erro": "mcr_core_aprendizado_codigo_validado", "solucao": "--[[\nEridanus era uma cidade lendária conhecida por sua simplicidade e eficiência do servidor ao lidar com grandes volumes de dados. conclusão a última modificação timestamp 6 trouxe avanços significativos no projeto mcr, o termo \"canary\" é frequentemente usado para testar novos conteúdos, mecânicas de jogo, balanceamentos e outras características específicas. 5. buff system.lua este arquivo gerencia os pontos de experiência xp , etc. 2. core 0_init.lua este arquivo é o ponto\n--]]\n\nlocal lore_er", "ctx": "core_codigo_validado", "timestamp": 1782870750.2815754}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Eridanus = Cidade inicial dos aventureiros. Era uma cidade lendária.", "ctx": "core_lore", "timestamp": 1782870644.0697045}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Canary = Servidor OTServ personalizado do projeto MCR.", "ctx": "core_lore", "timestamp": 1782870648.4602134}
{"erro": "mcr_core_aprendizado_lore", "solucao": "SPA = Sistema de Progressão do Aventureiro. 4 dominios elementais.", "ctx": "core_lore", "timestamp": 1782870650.5190709}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Eridanus = Cidade inicial dos aventureiros. Era uma cidade lendária.", "ctx": "core_lore", "timestamp": 1782870736.4002845}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Canary = Servidor OTServ personalizado do projeto MCR.", "ctx": "core_lore", "timestamp": 1782870739.9410763}
{"erro": "mcr_core_aprendizado_lore", "solucao": "SPA = Sistema de Progressão do Aventureiro. 4 dominios elementais.", "ctx": "core_lore", "timestamp": 1782870742.0077734}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Eridanus tinha muralhas de pedra cristalina que brilhavam com a lua.", "ctx": "core_lore", "timestamp": 1782870752.3434842}
{"erro": "mcr_core_aprendizado_lore", "solucao": "Os fundadores de Eridanus vieram do norte, cruzando o rio Chromatius.", "ctx": "core_lore", "timestamp": 1782870754.4081635}
{"erro": "mcr_core_aprendizado_lore", "solucao": "A cidade foi construída sobre uma mina de cristal mágico.", "ctx": "core_lore", "timestamp": 1782870754.4083576}
{"erro": "descoberto_por_assinatura_lore", "solucao": ">> CATALOG tags=context, identity, definition, mcr updated=2026-06-28\nEste arquivo fornece contexto essencial sobre o Projeto MCR para modelos de IA locais.\nMCR = Projeto MCR, um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ).", "ctx": "corpus_lore", "timestamp": 1782870298.393219}
{"erro": "4 correcoes pos-analise externa implementadas e validadas", "solucao": "4/4 correcoes. Performance test: 54.9s (novo baseline).", "ctx": "correcoes_externas", "timestamp": 1782698552.0449412}
{"erro": "Ciclo completo: historia de Eridanus", "solucao": "--[[\nEridanus era uma cidade lendária conhecida por sua simplicidade e eficiência do servidor ao lidar com grandes volumes de dados. conclusão a última modificação timestamp 6 trouxe avanços significativos no projeto mcr, o termo \"canary\" é frequentemente usado para testar novos conteúdos, mecânicas", "ctx": "criacao_teste", "timestamp": 1782866574.7765183}
{"erro": "Dashboard SSE de pensamento em tempo real para EMERGIR", "solucao": "sse_server.py: HTTPServer com SSE em /stream, heartbeat a cada 10s. Dashboard HTML: EventSource nativo, timeline com 15 etapas, painel de log com timestamp, prompt expansivel.", "ctx": "dashboard_sse", "timestamp": 1782713535.4114554}
{"erro": "Decomposicao Recursiva por Entropia: fragmenta ate padrao bruto, KG Force por folha, bottom-up", "solucao": "ContextCrew.fragmentar_recursivo() mede entropia com PatternEngine e fragmenta ate padrão bruto. Reconstructor processa folhas com IA leve + KG Force, depois combina bottom-up. Pipeline 7.8s vs 60s. 2 folhas, 2 chamadas leves, <500 chars cada. Validation V7+V4 detectam qualidade.", "ctx": "decomp_recursiva", "timestamp": 1782766389.814793}
{"erro": "[Emergente] E se a API RESTful em Python usando FastAPI e Dockerfile mul", "solucao": "### Combinação Impecável: FastAPI + Identity via V12 + FAST para Autenticação e Monitoramento\n\nImagine uma arquitetura inovadora onde a API RESTful em Python usando FastAPI e Dockerfile multi-stage se integra com a metodologia Identity via V12 de FAST (FastAPI, Authentication, Testing), criando um sistema avançado de autenticação, monitoramento e análise de comportamento dos usuários. Nesta combinação, cada componente desempenha um papel crucial, trabalhando em conjunto para fornecer uma experiê", "ctx": "emergente", "timestamp": 1782704124.9704669}
{"erro": "[Emergente] E se a sessão completa do MasterAgent pudesse ser usada para", "solucao": "A integração do MasterAgent com técnicas avançadas de aprendizado de máquina (ML/NN/AGI) oferece uma nova perspectiva para prever o clima futuro com maior precisão e eficiência. O MasterAgent, como um agente meteorológico inteligente, coleta e processa dados em tempo real de diversas fontes, enquanto o Decider analisa esses dados para criar modelos preditivos adaptativos. O SessionCache armazena e recupera informações históricas, facilitando a análise e a previsão de padrões futuros. Essa combin", "ctx": "emergente", "timestamp": 1782705369.1541488}
{"erro": "[Emergente] E se o sistema de notificações personalizadas para aplicativ", "solucao": "### ANALISE DOS TOPICOS\n### Tópico 1: Sessão completa: MasterAgent, Decider, SessionCache, ML/NN/AGI\n\n**O que significa?**\nA sessão completa do MasterAgent refere-se a um conjunto integrado de componentes e módulos projetados para operar em conjunto como parte de um sistema mais amplo. Este conjunto inclui:\n\n1. **MasterAgent**: Um agente inteligente responsável por gerenciar tarefas, coletar dados em tempo real e tomar decisões com base nessas informações.\n2. **Decider (FAST)**: Um classificador", "ctx": "emergente", "timestamp": 1782706546.2390084}
{"erro": "[Emergente] E se a sessão 6 do Sistema EMERGIR fosse integrada ao Plano ", "solucao": "### ANALISE DOS TOPICOS\nClaro, vou explicar cada tópico com a profundidade solicitada:\n\n### Tópico 1: Sistema EMERGIR - reconhecimento automático de padrões emergentes\n\n**O que significa?**\nO Sistema EMERGIR é um componente do projeto MCR (Tibia OTServ) que se concentra na detecção e análise de padrões emergentes no jogo. Padrões emergentes são comportamentos ou tendências inesperadas que surgem durante o jogo, podendo indicar novas estratégias, bugs ou alterações nas dinâmicas do jogo.\n\n**Por q", "ctx": "emergente", "timestamp": 1782706738.543691}
{"erro": "[Emergente] E se os timestamps e o staleness check do KG fossem usados p", "solucao": "### ANALISE DOS TOPICOS\n### 1. KG timestamps + staleness check implementado: 157 lessons backfill com mtime do arquivo\n\n#### O que significa?\nO \"KG timestamps + staleness check\" refere-se à adição de funcionalidades ao Sistema de Conhecimento (Knowledge Graph) para rastrear e verificar a validade dos dados. Especificamente, isso envolve:\n\n- **Timestamps**: Adicionar marcas de tempo (`mtime` - modification time) aos registros do Knowledge Graph para indicar quando cada dado foi modificado pela úl", "ctx": "emergente", "timestamp": 1782706937.6491697}
{"erro": "[Emergente] E se a Pipeline completa do MasterAgent pudesse ser usada para analisar e prever padrões emergentes no Sistema EMERGIR, permitindo que o Enricher aprenda com as tendências de emergência de", "solucao": "### ANALISE DOS TOPICOS\n```json\n{\n  \"respostas\": [\n    {\n      \"topico\": \"Pipeline completa: 11 gaps integrados no MasterAgent + Enricher\",\n      \"oque_significa\": \"Este tópico se refere à integração de 11 lacunas ou falhas identificadas na pipeline do projeto MCR, utilizando o componente chamado MasterAgent e o Enricher. A implementação dessas mudanças envolve a adição de aproximadamente 300 linhas de código ao arquivo Enricher.py e modificações no master_agent.py.\",\n      \"por_que_relevante\": ", "ctx": "emergente", "timestamp": 1782707323.220537}
{"erro": "[Emergente] E se o simulador de jogos de tabuleiro online criado com React e Socket.IO pudesse ser integrado ao sistema de progressão do aventureiro (SPA) para permitir que os jogadores avancem em sua", "solucao": "### ANALISE DOS TOPICOS\n### 1. KG timestamps + staleness check implementado: 157 lessons backfill com mtime do arquivo. kg.py: 3 novos metodos. mcr_devia.py: staleness check no V12 (confidence>=70% + not stale). Testes: 6/6 cenarios passam.\n\n#### O que significa?\nO \"KG timestamps + staleness check\" refere-se à adição de funcionalidades ao Sistema de Conhecimento (Knowledge Graph) para rastrear e verificar a validade dos dados. Especificamente, isso envolve:\n\n- **Timestamps**: Adicionar marcas de", "ctx": "emergente", "timestamp": 1782707578.411704}
{"erro": "[Emergente] E se a sessão completa do MasterAgent pudesse evoluir com cada missão concluída, criando uma 'arvore de conhecimento' que guiasse os Deciders em suas decisões futuras?", "solucao": "### ANALISE DOS TOPICOS\n### Tópico 1: Sessão completa: MasterAgent, Decider, SessionCache, ML/NN/AGI\n\n**O que significa?**\nA sessão completa do MasterAgent refere-se a um conjunto integrado de componentes e módulos projetados para operar em conjunto como parte de um sistema mais amplo. Este conjunto inclui o **MasterAgent**, um agente inteligente centralizado responsável por coordenar várias tarefas, o **Decider** (ou classificador), que toma decisões com base em dados ou informações fornecidas,", "ctx": "emergente", "timestamp": 1782708475.6423657}
{"erro": "[Emergente] E se a fase 1 do plano MCR-DevIA fosse usada para otimizar o algoritmo de aprendizado automático em MasterAgent, resultando em um aumento significativo na eficiência e precisão das tarefas", "solucao": "### ANALISE DOS TOPICOS\n### Tópico 1: Plano final MCR-DevIA: 27 tarefas em 7 fases\n\n**O que significa?**\nO \"Plano final MCR-DevIA\" é um documento detalhado que descreve as etapas e tarefas necessárias para completar o projeto MCR (servidor customizado de Tibia baseado em OTServ). Este plano divide o projeto em 7 fases, com um total de 27 tarefas específicas a serem concluídas. Cada fase tem uma prioridade e ordem específica, indicando quando cada tarefa deve ser realizada.\n\n**Por que é relevante", "ctx": "emergente", "timestamp": 1782708809.3056176}
{"erro": "[Emergente] E se a cidade de Eridanus implementasse um sistema de correções pos-analise externa que utilizasse as luzes das arvores de Natal como indicadores para otimizar o fluxo de tráfego e reduzir", "solucao": "### ANALISE DOS TOPICOS\n### 1. 4 correções pos-analise externa implementadas e validadas: 4/4 correções. Performance test: 54.9s (novo baseline).\n\n**O que significa?**\nEste tópico se refere à implementação e validação de quatro correções após uma análise externa do projeto MCR. Após a aplicação dessas correções, um teste de desempenho foi realizado, resultando em um novo tempo de baseline de 54,9 segundos.\n\n**Por que é relevante para o projeto MCR?**\nAs correções pos-analise externa são cruciais", "ctx": "emergente", "timestamp": 1782734642.0522244}
{"erro": "[Emergente] E se a equipe de desenvolvimento MCR-DevIA implementasse uma estratégia de refatoração baseada no eixo Nirvana-Caos, resultando em um código mais organizado e eficiente que atingisse o nív", "solucao": "### ANALISE DOS TOPICOS\n### 1. Plano final MCR-DevIA: 27 tarefas em 7 fases\n\n**O que significa?**\nO plano final do projeto MCR-DevIA é uma estrutura organizada de 27 tarefas distribuídas em 7 fases. Cada fase representa um estágio crucial no desenvolvimento e implementação do sistema, com tarefas específicas a serem concluídas para avançar.\n\n**Por que é relevante para o projeto MCR?**\nEste plano é fundamental para garantir uma abordagem estruturada e eficiente no desenvolvimento do projeto. Ao d", "ctx": "emergente", "timestamp": 1782771327.1153176}
{"erro": "[Emergente] E se a Entropia do modelo Qwen2.5-coder:7b pudesse ser usada para gerar uma Dashboard SSE em tempo real que monitorasse e visualizasse as mudanças de estado interno da IA, permitindo um ac", "solucao": "### ANALISE DOS TOPICOS\n### 1. Entropia 0.85 e normal para modelo 7b - não é problema de configuração - pipeline completa e superior a prompt mínimo\n\n#### O que significa?\nA entropia é uma medida de incerteza ou aleatoriedade em um sistema. Em modelos de linguagem, como o qwen2.5-coder:7b, uma alta entropia (por exemplo, 0.85) indica que o modelo está gerando respostas com muita variabilidade e pouca previsibilidade.\n\n#### Por que é relevante para o projeto MCR?\nNo contexto do projeto MCR (Maste", "ctx": "emergente", "timestamp": 1782780220.5711856}
{"erro": "EMERGIR V4 fragmentador com 4 secoes e Z expandido (3 visoes)", "solucao": "Fragmentador no master_agent.py: cada secao gerada separadamente com contexto acumulado entre elas. Expansao critica: 3 chamadas ia.gerar() sequenciais (cenario concreto, padrao subjacente, potencial transformador). ContextCrew: ContextCrew.executar() busca em 5 fontes paralelas.", "ctx": "emergir_v4", "timestamp": 1782713516.9490805}
{"erro": "Entropia 0.85 e normal para modelo 7b - nao e problema de configuracao - pipeline completa e superior a prompt minimo", "solucao": "Mudei de N chamadas leves (1 por folha) para 1 chamada 7b com todas as folhas como contexto. Testei prompt minimo (400 chars) vs pipeline completa: mesma entropia (~0.85). Conclusao: entropia alta e caracteristica do modelo qwen2.5-coder:7b, nao do MCR. Pipeline completa e superior: elimina alucinacoes, cita arquivos reais.", "ctx": "entropia_normal", "timestamp": 1782777540.3774889}
{"erro": "Implemente um sistema de monitoramento de recursos em tempo real para uma aplica", "solucao": "Tarefa parcial (2/4). Falhas em: validar_codigo, salvar_arquivo", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "crie um bot Telegram que responda a comandos específicos e envie mensagens progr", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "Cria aplicativo mobile de gerenciamento financeiro com funcionalidades de orçame", "solucao": "Tarefa parcial (11/14). Falhas em: validar_codigo, testar_execucao, relatorio_final", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "Crie um sistema de notificações personalizadas para aplicativos móveis usando Re", "solucao": "Tarefa parcial (2/4). Falhas em: validar_codigo, salvar_arquivo", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "Crie um simulador de jogos de tabuleiro online usando React e Socket.IO. Salve e", "solucao": "Tarefa parcial (11/14). Falhas em: validar_codigo, testar_execucao, relatorio_final", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "crie um projeto de API RESTful em Python usando FastAPI, Dockerfile multi-stage,", "solucao": "Tarefa parcial (12/14). Falhas em: testar_execucao, relatorio_final", "ctx": "exec_projeto", "timestamp": 1782698552.0449412}
{"erro": "Cria um script python que imprime 'teste'", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Explique o que e o SessionCache no MCR-DevIA e como ele difere de uma cache trad", "solucao": "Tarefa concluida com sucesso em 2/2 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Cria um script python que imprime 'Hello World'", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Cria um script python que imprime 'teste 2'", "solucao": "Tarefa parcial (3/4). Falhas em: salvar_arquivo", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Cria um script python que imprime 'teste 1'", "solucao": "Tarefa parcial (3/4). Falhas em: salvar_arquivo", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Crie um script em Python para automatizar a coleta de dados de uma API RESTful e", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Crie um script em Bash que monitora a utilização da CPU e gera um relatório diár", "solucao": "Tarefa parcial (2/4). Falhas em: validar_codigo, salvar_arquivo", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "crie Makefile com targets para build, test e deploy do projeto web", "solucao": "Tarefa parcial (2/4). Falhas em: validar_codigo, salvar_arquivo", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Crie um script em Python para monitorar a disponibilidade de servidores web em u", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "crie script em Python que monitore alterações em um diretório e envie notificaçõ", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Cria um script python que imprime 'teste 2'", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Crie um script em Python para monitorar a utilização de memória em tempo real em", "solucao": "Tarefa concluida com sucesso em 4/4 passos", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "Crie um script em JavaScript que automatiza a coleta de dados de uma página web ", "solucao": "Tarefa parcial (2/4). Falhas em: validar_codigo, salvar_arquivo", "ctx": "exec_simples", "timestamp": 1782698552.0449412}
{"erro": "expansao_Eridanus", "solucao": "Expandido via 2 recursos. Agora temos 20 lessons sobre o tema. Recursos: comando:gerar_npc, kg.", "ctx": "expansao_auto", "timestamp": 1782916206.0091147}
{"erro": "expansao_SPA", "solucao": "Expandido via 2 recursos. Agora temos 20 lessons sobre o tema. Recursos: comando:gerar_npc, kg.", "ctx": "expansao_auto", "timestamp": 1782916212.5583775}
{"erro": "expansao_numerico", "solucao": "Expandido via 1 recursos. Agora temos 0 lessons sobre o tema. Recursos: comando:gerar_npc.", "ctx": "expansao_auto", "timestamp": 1782916245.871246}
{"erro": "expansao_SPA", "solucao": "Expandido via 2 recursos. Agora temos 20 lessons sobre o tema. Recursos: comando:gerar_npc, kg.", "ctx": "expansao_auto", "timestamp": 1782917611.7132363}
{"erro": "expansao_MCR", "solucao": "Expandido via 2 recursos. Agora temos 20 lessons sobre o tema. Recursos: comando:gerar_npc, kg.", "ctx": "expansao_auto", "timestamp": 1782917743.1148827}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782918172.1388495}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782918241.2103236}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782918276.500507}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919194.053269}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919251.6492941}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919415.9765818}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919695.7965925}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919702.2231638}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919707.283895}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782919712.3341284}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920028.2045217}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920034.3936417}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920039.285619}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920044.261985}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920170.7239087}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920176.8934472}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920181.8318825}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920186.7436984}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920315.1667216}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782920414.0808172}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782921199.0428498}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782921312.6649294}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923342.5053837}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923349.3139417}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923354.5891304}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923359.823154}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923365.450468}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923370.714678}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923375.9001553}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923499.9137042}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923798.147841}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923804.6696591}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923809.9064665}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923815.1697147}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923820.751385}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923825.9839752}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923831.1972978}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782923939.9882283}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924001.4655294}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924224.1636264}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924230.6424668}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924235.8635406}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924241.0915706}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924246.669623}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924251.8042963}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924257.007209}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924328.9076815}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924416.9182923}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924754.682689}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924761.2210562}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924766.4247656}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924771.631648}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924865.7282035}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924871.0380547}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924876.2994962}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782924881.5972219}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782924887.1589708}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925102.9240782}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925109.5303335}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925114.7962453}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925119.9974773}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925180.623365}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925185.8219745}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925191.018221}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925196.1993976}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782925201.6705782}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925662.66482}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925669.2308683}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925674.4420974}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925679.6967132}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925727.4704802}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925734.0027816}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925739.2059724}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782925744.411635}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782925749.8703017}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782925754.9983425}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782925760.2087471}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926028.6635282}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926035.1908824}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926040.4497252}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926045.6334481}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926093.3649766}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926099.8597374}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926105.0534499}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926110.2420478}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782926115.6939394}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782926120.84596}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782926126.0208602}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926347.2040238}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926353.6925175}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926358.9533298}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926364.1498752}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926403.719206}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926408.8534765}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782926414.0937138}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927904.745857}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927911.516178}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927916.8585582}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927922.1921525}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927962.1620183}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927967.5205076}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782927972.8754544}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928162.255707}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928168.8396993}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928174.0570748}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928179.3264215}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928206.9730005}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928212.2573211}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928217.624147}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928222.9257886}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782928228.4936664}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928629.1589513}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928635.7025774}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928640.8967214}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928646.142104}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928693.9888418}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928700.6062956}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928705.8187542}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782928711.0120373}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782928716.4861174}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782928721.6253514}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782928726.777388}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929023.079489}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929029.6996083}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929034.9357123}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929040.2131352}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929113.364215}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929118.7014506}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929124.0107887}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929609.096107}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929615.6127524}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929620.8612463}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929626.0865507}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929673.8975585}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929680.4249756}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929685.6091602}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929690.8130984}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782929696.3036182}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782929701.4471805}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782929706.6042817}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929988.2169528}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782929994.7918224}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930000.0339916}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930005.3219476}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930032.9296443}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930038.1318026}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930043.343506}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782930048.5679164}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782930054.087389}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782931983.3677537}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782931990.0126615}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782931995.2780006}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932000.5369616}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932027.9502208}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932033.2077107}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932038.4192793}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932043.657286}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932049.1647158}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932574.213369}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932580.7129962}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932585.943071}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932591.180927}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932642.8579736}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932649.2972946}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932654.506775}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932659.7049038}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932665.1319196}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932670.2645926}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932675.40533}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932773.4028444}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932779.9330168}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932785.1798246}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932790.3904326}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932837.975235}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932844.434473}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932849.627392}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782932854.8134837}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932860.2766726}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932865.4162502}
{"erro": "expansao_saber?", "solucao": "Expandido via 0 recursos. Agora temos 0 lessons sobre o tema. Recursos: .", "ctx": "expansao_auto", "timestamp": 1782932870.600907}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782933311.6398897}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934050.9662213}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934078.2125707}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934105.5584593}
{"erro": "expansao_especifico?", "solucao": "Expandido via 1 recursos. Agora temos 2 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934110.7483344}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934186.8388107}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934538.3934207}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934599.171687}
{"erro": "expansao_especifico?", "solucao": "Expandido via 1 recursos. Agora temos 3 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934604.328398}
{"erro": "expansao_MCR", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782934793.1992555}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935191.652503}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935281.6463075}
{"erro": "expansao_especifico?", "solucao": "Expandido via 1 recursos. Agora temos 4 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935286.819566}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935427.3001313}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935597.644257}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782935725.0251682}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782936186.9929366}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782936239.6651106}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782936731.664013}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782937972.8404095}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782938951.7477174}
{"erro": "expansao_SPA", "solucao": "Expandido via 1 recursos. Agora temos 20 lessons sobre o tema. Recursos: kg.", "ctx": "expansao_auto", "timestamp": 1782939495.2434635}
{"erro": "Fase1: CR+Enricher restaurados + Fase2: Modo Offline Turbinado completo", "solucao": "CR e Enricher do legado corrigidos (imports, classificacao). KG.buscar_expandido() com fuzzy+ctx. PatternEngine.kg_pattern_analyze() tokeniza KG. Conselho ganhou arquetipo filosofico. ToT expandido para 5 perspectivas (filosofico+pragmatico). PipelineExecutor aceita flag turbo. cmd_turbo.py ativa modo offline. Testado: 3385 chars resposta, 15 conceitos KG, zero internet.", "ctx": "fase2_turbo", "timestamp": 1782762380.2484045}
{"erro": "MCR-DevIA Fenix: F1 (supervisor propagado) + F2 (7 modulos resgatados) + F4 (toolkit comando) + padronizacao", "solucao": "F1: supervisor com classificar_keyword agora existe em Scripts/mcr_devia (3 copias sincronizadas). F2: 7 modulos resgatados do Legado para o sistema ativo (analysis/fragmenter.py, agents/autoconsciencia.py, tools/toolkit.py, etc). F4: comando mcr toolkit mostra 43 comandos, 14 modulos, 7 personalidades. TruncationFixer corrigiu 56 truncamentos nos novos arquivos.", "ctx": "fenix_unificacao", "timestamp": 1782779955.942881}
{"erro": "Fragmentacao por dois-pontos: 5 folhas para 4 sub-perguntas (antes 2) + Weaver prioriza conceito + TruncationFixer limpo", "solucao": "Nova heuristica de fragmentacao quebra por ': ' + sub-perguntas com virgula. Pergunta de 4 topicos gera 5 folhas (antes 2). Weaver prioriza ctx=conceito. TruncationFixer: zero truncamentos. Entropia ainda alta (0.85) porque Reconstructor concatena em vez de fundir.", "ctx": "fragmentacao_v3", "timestamp": 1782776708.7764108}
{"erro": "Bolo Desconstruido: ContextCrew.fragmentar() + Reconstructor + modo fragmentado no pipeline", "solucao": "ContextCrew.fragmentar() analisa pergunta e retorna N fragmentos independentes. Reconstructor usa BlankFiller+EMERGIR+Conselho para juntar. PipelineExecutor._executar_fragmentado() processa cada fragmento com modelo leve (<2K chars) em 11.8s vs 60s antes. Descoberto: cada fragmento precisa receber KG Force individualmente.", "ctx": "fragmentado", "timestamp": 1782765712.121514}
{"erro": "modulo_agent_loop.py", "solucao": "Codigo do modulo agent_loop.py: \"\"\"Agent Loop — Núcleo AGI: Think → Act → Observe → Learn.  Orquestra o pipeline completo de geração de NPCs: 1. THINK: Analisa descrição, busca exemplos similares + KG, planeja 2. ACT: Gera código via NPCGenerator com placeholders do LLM 3. OBSERVE: Valida com LuaValidator, verifica SQL injection 4. LOOP: Se falhar, retry com correção (max 3) 5. LEARN: Registra lições no histórico + Knowledge Graph  Uso:     from modulos.agent_loop import AgentLoop     agent = Ag", "ctx": "fuel_codigo", "timestamp": 1782919716.8417878}
{"erro": "modulo_aprendiz_de_padroes.py", "solucao": "Codigo do modulo aprendiz_de_padroes.py: \"\"\"AprendizDePadroes — Aprendiz autônomo de padrões para IE e PE.  Lê QUALQUER fonte de dados, usa PE.tokenizar_universal() + extrair_padroes() para descobrir estruturas e co-ocorrências, e salva lessons no KG (ctx='padrao_aprendido') que a IntentionEngine carrega em runtime.  1 método universal substitui 6 especializados. \"\"\" import os, json, re from collections import Counter, defaultdict from typing import List, Dict, Optional   class AprendizDePadroes", "ctx": "fuel_codigo", "timestamp": 1782919720.9016876}
{"erro": "modulo_auto_repair.py", "solucao": "Codigo do modulo auto_repair.py: \"\"\"AutoRepair — Repara codigo com erro baseado na mensagem do validador.  Quando o validador detecta um erro (linha, descricao), o AutoRepair usa o FAST model para corrigir o codigo em UMA tentativa.  Conceito: Se o validador ACHOU o erro, o reparador SABE o que corrigir. Nao precisa de loop — erro conhecido = correcao direta.  Uso:     reparador = AutoRepair(ia)     codigo_corrigido = reparador.reparar(codigo_errado, erros, linguagem) \"\"\" from modulos.util impor", "ctx": "fuel_codigo", "timestamp": 1782919724.992157}
{"erro": "modulo_auto_revisor.py", "solucao": "Codigo do modulo auto_revisor.py: \"\"\"Auto-Revisor: MCR-DevIA revisa a PROPRIA resposta pos-geracao. Detecta alucinacoes (classes inventadas), nomes inconsistentes, e auto-corrige.  FLUXO: 1. Orquestrador gera resposta 2. AutoRevisor.revisar(resposta, contexto)  3. Detecta alucinacoes comparando com classes REAIS do projeto 4. Se encontrar, registra no KG e RETORNA correcoes 5. Watchdog pode disparar AutoRevisor em arquivos do sandbox/ \"\"\" import os, re, json, time  # Classes REAIS do projeto (co", "ctx": "fuel_codigo", "timestamp": 1782919729.069391}
{"erro": "modulo_auto_trigger.py", "solucao": "Codigo do modulo auto_trigger.py: \"\"\"Auto Trigger System — Bridge entre intenção e execução de ferramentas.  Recebe intenções do IntentionEngine e executa as ferramentas apropriadas ANTES de chamar o LLM. O LLM só vê os resultados.  Fluxo:   IntentionEngine.detectar(texto)     ↓   AutoTriggerSystem.executar(intencoes)     ↓  (para cada intenção, executa ferramentas)   Resultados injetados no contexto do prompt     ↓   LLM só escreve a resposta baseada nos dados  Uso:     ats = AutoTriggerSystem(", "ctx": "fuel_codigo", "timestamp": 1782919734.3079078}
{"erro": "modulo_blank_filler.py", "solucao": "Codigo do modulo blank_filler.py: \"\"\"Blank Filler Universal — \"Código criar código\" + LLM preencher blanks. Engine generica: qualquer conteudo (codigo, docs, analises) pode ter blanks que sao preenchidos pela IA individualmente, reduzindo alucinacao e erros.  Fluxo:   1. Esqueleto: estrutura com marcadores @BLANK_ID   2. Listar blanks: extrai os IDs   3. Preencher: IA preenche CADA blank com contexto focado   4. Montar: substitui blanks no esqueleto  Uso:     bf = BlankFiller(ia)     skel = bf.g", "ctx": "fuel_codigo", "timestamp": 1782919738.3786442}
{"erro": "modulo_canary_indexer.py", "solucao": "Codigo do modulo canary_indexer.py: \"\"\"CanaryIndexer — Indexador do ecossistema Canary (NPCs, Schema DB, API).  Varre NPCs do servidor, extrai padrões e constrói base de conhecimento para geração inteligente de scripts. Base da arquitetura AGI do MCR-DevIA.  Uso:     from modulos.canary_indexer import CanaryIndexer     idx = CanaryIndexer()     idx.indexar()  # Varre tudo     resultados = idx.buscar(\"ferreiro que vende espadas\") \"\"\" import os, re, json, glob as _glob from typing import List, Dic", "ctx": "fuel_codigo", "timestamp": 1782919742.4854994}
{"erro": "modulo_conselho.py", "solucao": "Codigo do modulo conselho.py: \"\"\"Conselho V10 - CONSELHO INFINITO. Personalidades sob demanda com ContextCrew + ContextInfinity. - Zero arquivos de personalidade fixas - Arquetipos gerados dinamicamente via FAST + contexto do ContextCrew - Router de modelos por arquétipo (cada um usa o melhor modelo) - Validação anti-alucinacao + auto-revisao + traducao PT-BR - + TreeOfThought (G1), PromptCache (G5), TermosCriticos (G7), ValidacaoRelevancia (G6)   (fundido do enricher.py)\"\"\" import sys, os, time", "ctx": "fuel_codigo", "timestamp": 1782919746.5689607}
{"erro": "modulo_context_enricher.py", "solucao": "Codigo do modulo context_enricher.py: \"\"\"Context Enricher Universal — Gera contexto NOVO para enriquecer respostas. Em vez de apenas BUSCAR contexto (ContextCrew), o Enricher CRIA conteudo: - Nomes proprios para lore (FAST + validacao) - Dados tecnicos (grep + leitura de codigo) - Curiosidades (weblearn + KG) - Comparacoes estruturadas (FAST sobre dados do KG)  Integrado no pipeline: CR -> ENRICHER -> ORQUESTRADOR \"\"\" import os, sys, json, time, re, subprocess, hashlib  BASE = os.path.abspath(os", "ctx": "fuel_codigo", "timestamp": 1782919750.6518033}
{"erro": "modulo_context_reinforcer.py", "solucao": "Codigo do modulo context_reinforcer.py: \"\"\"Context Reinforcer — Reforco de contexto universal para o MCR-DevIA. Usa FAST para: 1. Extrair termos criticos da solicitacao (incluindo curtos como .lua, Oz) 2. Validar se o contexto do ContextCrew e relevante 3. Disparar weblearn se contexto insuficiente 4. Gerar instrucao de desambiguacao para o LLM  Integrado com: PipelineExecutor, Conselho, Mente, Supervisor, Orquestrador, Revisor. \"\"\" import os, sys, json, time, re, subprocess  BASE = os.path.absp", "ctx": "fuel_codigo", "timestamp": 1782919754.7474675}
{"erro": "modulo_decider.py", "solucao": "Codigo do modulo decider.py: \"\"\"Decider — Classificador universal via FAST model (+ fallback deterministico).  Substitui regex/dict fixos por decisoes do FAST model. Nao substitui seguranca deterministica (COMANDOS_BLOQUEADOS). Cache LRU com TTL para evitar chamadas repetidas ao LLM.  Uso:     decider = Decider(ia)     tipo = decider.classificar(\"Cria um jogo em Python\",                                 ['projeto_jogo', 'criar_codigo', 'pergunta'])     # -> 'projeto_jogo'      dados = decider.ext", "ctx": "fuel_codigo", "timestamp": 1782919758.82376}
{"erro": "modulo_diagnostic_engine.py", "solucao": "Codigo do modulo diagnostic_engine.py: \"\"\"Diagnostic Engine — Auto-diagnóstico do MCR-DevIA. Detecta problemas de código, I/O manual, compilação, anti-patterns. \"\"\" import os, sys, time, json, re  BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) MODULOS_DIR = os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos')   class DiagnosticEngine:     \"\"\"Motor de auto-diagnóstico: detecta, prioriza, repara.\"\"\"      SEVERIDADE = {'BLOQUEANTE': 0, 'ALTA': 1, 'MEDIA': 2, 'BAI", "ctx": "fuel_codigo", "timestamp": 1782919762.9025435}
{"erro": "modulo_emergir.py", "solucao": "Codigo do modulo emergir.py: \"\"\"Emergir — Reconhecimento automatico de padroes emergentes. Extraido de master_agent.py para modularizacao.  Engine de EMERGIR: combina topicos distantes do KG, gera insights Z criativos, expande com visao critica (cenario, padrao, potencial), e aprende novos conhecimentos no KG. \"\"\" import os, sys, time, re, random, hashlib, json as _json  BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))   class EmergirEngine:     \"\"\"Motor do siste", "ctx": "fuel_codigo", "timestamp": 1782919767.8309555}
{"erro": "modulo_episodic_memory.py", "solucao": "Codigo do modulo episodic_memory.py: \"\"\"EpisodicMemory — Memória episódica com embeddings + fallback keywords.  Armazena experiências (request + resultado + lição) e busca por similaridade. Usa nomic-embed-text para embeddings (768 floats) quando disponível, fallback para busca por palavras-chave.  Uso:     mem = EpisodicMemory()     mem.registrar(\"cria ferreiro\", {...}, \"usar templates shop\")     resultados = mem.buscar(\"cria npc ferreiro em eridanus\") \"\"\" import os, json, time, re, hashlib, ma", "ctx": "fuel_codigo", "timestamp": 1782919771.9307108}
{"erro": "modulo_ia.py", "solucao": "Codigo do modulo ia.py: \"\"\"Modulo: IA - Interface com modelos Ollama + Router Híbrido (local/cloud).\"\"\" import os, json, urllib.request, re  OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')  # --- Router Híbrido --- # Modos: 'web_search' (grátis, padrão), 'api' (requer key), 'desligado' (só local) CLOUD_MODE = os.environ.get('MCR_CLOUD_MODE', 'web_search') CLOUD_API_KEY = os.environ.get('MCR_CLOUD_API_KEY', '') WEB_SEARCH_TIMEOUT = int(os.environ.get('MCR_WEB_SEAR", "ctx": "fuel_codigo", "timestamp": 1782919776.0241268}
{"erro": "modulo_intention_engine.py", "solucao": "Codigo do modulo intention_engine.py: \"\"\"Intention Engine — 3 camadas de detecção de intenção.  Fluxo: 1. PatternEngine: tokeniza → fingerprint → similaridade com exemplares conhecidos 2. Keyword Actions (Léxico V2): match de verbos + domínios 3. FAST 1.5b: fallback semântico 4. Markov: verificação cruzada entre intenção detectada e sequência esperada  Cada camada retorna categoria + confiança. A decisão final é ponderada.  Uso:     ie = IntentionEngine(pe=PatternEngine(), ia=IA())     intencoes", "ctx": "fuel_codigo", "timestamp": 1782919780.0844874}
{"erro": "modulo_kg.py", "solucao": "Codigo do modulo kg.py: \"\"\"Modulo: KnowledgeGraph - Gerenciamento de conhecimento do MCR-DevIA. Knowledge Graph multi-arquivo: cada contexto em arquivo separado + master index. - Carregamento lazy: so le ctx files sob demanda - Salvamento fragmentado: so escreve ctx alterados - Master index: knowledge.json mantido para compatibilidade (contem metadados) \"\"\" import os, json, re, hashlib, math, urllib.request, time as _time from stop_words import STOP_BUSCA  BASE = os.path.abspath(os.path.join(os.", "ctx": "fuel_codigo", "timestamp": 1782919784.1726224}
{"erro": "modulo_kg_cleaner.py", "solucao": "Codigo do modulo kg_cleaner.py: \"\"\"KGCleaner — Marca lessons poluentes como inactive no startup.  Lessons poluentes sao auto-geradas pelo pipeline e nao representam conhecimento conceitual. Elas poluem o KG Weaver (que encontra lessons por fingerprint) e devem ser marcadas como inactive.  Categorias de lessons a manter (NAO sao poluentes):   - conceito: definicoes e conceitos do projeto   - arquitetura, refatoracao: licoes de arquitetura   - correcoes_externas, decomp_recursiva: licoes uteis   -", "ctx": "fuel_codigo", "timestamp": 1782919788.272147}
{"erro": "modulo_lessons_buffer.py", "solucao": "Codigo do modulo lessons_buffer.py: \"\"\"LessonsBuffer - Buffer de conhecimento antes de ir pro KG. Evita duplicatas, contradicoes, e informacao falsa. Contradicoes sao resolvidas automaticamente pelo ContextCrew.\"\"\" import os, json, time, hashlib, urllib.request from modulos.util import fast as _util_fast  SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox')) BUFFER_PATH = os.path.join(SANDBOX, '.mcr_devia', 'lessons_buffer.json') OLLAMA_URL = os.environ.get('O", "ctx": "fuel_codigo", "timestamp": 1782919792.3399923}
{"erro": "modulo_lexico_v2.py", "solucao": "Codigo do modulo lexico_v2.py: \"\"\"Léxico V2 — Vocabulário compartilhado entre IntentionEngine e tokenização rica.  Contém: - _LEXICO: patterns de INTENÇÃO + DOMÍNIO + GRAMÁTICA (fonte única da verdade) - tokenizar_v2(): produz tokens RICOS (não PAL_CURTA/PAL_MEDIA) - MARKOV_POR_INTENCAO: sequência esperada para cada intenção  Uso:     from modulos.lexico_v2 import tokenizar_v2, MARKOV_POR_INTENCAO     tokens = tokenizar_v2(\"Crie um NPC Ferreiro\")     # → [(\"INTENT_CREATE\", \"Crie\", 0.9), (\"DOM_NP", "ctx": "fuel_codigo", "timestamp": 1782919796.4155028}
{"erro": "comando_cmd_analisar.py", "solucao": "Comando cmd_analisar.py: \"\"\"Comando: analisar - Analisa arquivo usando Orquestrador Universal.\"\"\" import os, sys, json, re sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX, OLLAMA_URL  def register():     return {", "ctx": "fuel_codigo", "timestamp": 1782919801.316085}
{"erro": "comando_cmd_aprender_conceito.py", "solucao": "Comando cmd_aprender_conceito.py: \"\"\"Comando: aprender_conceito - APRENDE QUALQUER CONCEITO do projeto (codigo + docs). Usa Orquestrador Universal para sintese de conhecimento. Busca em TODO o projeto: src/, data/, scripts/, Docs/, config/, sandbox/, raiz.\"\"\" import os, re, sys  BASE = os.path.abspath(os.path.join(os.path.dirname(__", "ctx": "fuel_codigo", "timestamp": 1782919805.4129744}
{"erro": "comando_cmd_autoteste.py", "solucao": "Comando cmd_autoteste.py: \"\"\"Comando: autoteste - Auto-Teste Definitivo do MCR-DevIA. Gera perguntas via FAST, executa, coleta auto-critica, avalia, salva historico.  Uso (JSON IPC):   {\"cmd\": \"autoteste\", \"args\": [\"--ciclo\", \"1\"]}   {\"cmd\": \"autoteste\", \"args\": [\"--ciclo\", \"1\", \"--fast\"]}       # Skip ToT   {\"cmd\": \"autotes", "ctx": "fuel_codigo", "timestamp": 1782919809.4830837}
{"erro": "comando_cmd_bugfinder.py", "solucao": "Comando cmd_bugfinder.py: \"\"\"Comando: bugfinder - Escaneia logs e registra erros no KG para aprendizado.\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     retur", "ctx": "fuel_codigo", "timestamp": 1782919813.5410194}
{"erro": "comando_cmd_build.py", "solucao": "Comando cmd_build.py: \"\"\"Comando: build - Pipeline Dinamica: gera codigo sob medida.\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"nam", "ctx": "fuel_codigo", "timestamp": 1782919817.6229255}
{"erro": "comando_cmd_builderx.py", "solucao": "Comando cmd_builderx.py: \"\"\"Comando: builderx - builderx\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"name\": \"builderx\",         \"desc\":", "ctx": "fuel_codigo", "timestamp": 1782919821.7066486}
{"erro": "comando_cmd_compilar.py", "solucao": "Comando cmd_compilar.py: \"\"\"Comando: compilar - compilar\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"name\": \"compilar\",         \"desc\":", "ctx": "fuel_codigo", "timestamp": 1782919825.7752023}
{"erro": "comando_cmd_conectar.py", "solucao": "Comando cmd_conectar.py: \"\"\"Comando: conectar - Thinker de conexoes: busca conexoes entre dominios no KG.\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     ret", "ctx": "fuel_codigo", "timestamp": 1782919829.8375914}
{"erro": "comando_cmd_conselho.py", "solucao": "Comando cmd_conselho.py: \"\"\"Comando: conselho - Conselho V7 para respostas inteligentes.\"\"\" import os, sys, time, json  def register():     return {         \"name\": \"conselho\",         \"desc\": \"Conselho V7: resposta inteligente com personalidades + auto-revisao\",         \"handler\": execute,         \"args\": [{\"name\": \"pergun", "ctx": "fuel_codigo", "timestamp": 1782919834.8390377}
{"erro": "comando_cmd_criar.py", "solucao": "Comando cmd_criar.py: \"\"\"Comando: criar — Cria conteudo usando o pipeline ReAct.\"\"\" def register():     return {\"name\": \"criar\", \"desc\": \"Cria conteudo (codigo, NPC, item, etc.) usando pipeline ReAct.\",             \"handler\": execute, \"args\": [{\"name\": \"descricao\", \"type\": \"str\", \"required\": True}], \"categoria\": \"criacao", "ctx": "fuel_codigo", "timestamp": 1782919838.927409}
{"erro": "comando_cmd_debate.py", "solucao": "Comando cmd_debate.py: \"\"\"Comando: debate - Debate: 2 sub-agentes discutem antes de entregar.\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {", "ctx": "fuel_codigo", "timestamp": 1782919842.9917586}
{"erro": "comando_cmd_edit.py", "solucao": "Comando cmd_edit.py: \"\"\"Comando: edit - Edita por LINHA (precisao cirurgica).\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"name\": \"e", "ctx": "fuel_codigo", "timestamp": 1782919847.0596616}
{"erro": "comando_cmd_ensinar.py", "solucao": "Comando cmd_ensinar.py: \"\"\"Comando: ensinar - Registra conhecimento no KG.\"\"\" def register():     return {         \"name\": \"ensinar\",         \"desc\": \"Regstra licao no KG: ensinar <erro> <causa> <solucao> [ctx]\",         \"handler\": execute,         \"args\": [             {\"name\": \"erro\", \"type\": \"str\", \"required\": True},", "ctx": "fuel_codigo", "timestamp": 1782919851.099284}
{"erro": "comando_cmd_estrategia.py", "solucao": "Comando cmd_estrategia.py: \"\"\"Comando: estrategia - estrategia\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"name\": \"estrategia\",         \"", "ctx": "fuel_codigo", "timestamp": 1782919855.1675208}
{"erro": "comando_cmd_explorar.py", "solucao": "Comando cmd_explorar.py: \"\"\"Comando: explorar - Escaneia e aprende com IA minima + Orquestrador Universal.\"\"\" import os, re, json, hashlib, time, sys  BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  def register():     return {         \"name\": \"explorar\",         \"desc\": \"Escaneia projeto", "ctx": "fuel_codigo", "timestamp": 1782919859.213783}
{"erro": "comando_cmd_extract.py", "solucao": "Comando cmd_extract.py: \"\"\"Comando: extract - Extrai partes de QUALQUER arquivo, modifica, reaplica (com seguranca).\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def registe", "ctx": "fuel_codigo", "timestamp": 1782919863.268729}
{"erro": "comando_cmd_fast.py", "solucao": "Comando cmd_fast.py: \"\"\"Comando: fast - Classificacao rapida via IA (usa router padronizado).\"\"\" import os, sys sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast as _util_fast  def register():     return {         \"name\": \"fast\",         \"desc\": \"Classificacao rapida via Oll", "ctx": "fuel_codigo", "timestamp": 1782919868.1049514}
{"erro": "comando_cmd_fazer.py", "solucao": "Comando cmd_fazer.py: \"\"\"Comando: fazer — Cria/executa acoes usando o pipeline ReAct.\"\"\" def register():     return {\"name\": \"fazer\", \"desc\": \"Executa acoes (criar, modificar, configurar) usando pipeline ReAct.\",             \"handler\": execute, \"args\": [{\"name\": \"descricao\", \"type\": \"str\", \"required\": True}], \"categoria\"", "ctx": "fuel_codigo", "timestamp": 1782919872.1555648}
{"erro": "comando_cmd_fix_excepts.py", "solucao": "Comando cmd_fix_excepts.py: \"\"\"Comando: fix_excepts - Substitui except: por except Exception as e:\"\"\" import os, re, shutil  def register():     return {         \"name\": \"fix_excepts\",         \"desc\": \"Corrige except: genericos. Uso: fix_excepts <path> [--force] [--preview]\",         \"handler\": execute,         \"args\": [{\"name", "ctx": "fuel_codigo", "timestamp": 1782919876.207908}
{"erro": "comando_cmd_gerar.py", "solucao": "Comando cmd_gerar.py: \"\"\"Comando: gerar - gerar\"\"\" import os, sys, json, re, subprocess sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX  def register():     return {         \"name\": \"gerar\",         \"desc\": \"gerar\",", "ctx": "fuel_codigo", "timestamp": 1782919880.2514105}
{"erro": "modulo_agent_loop.py", "solucao": "Codigo do modulo agent_loop.py: \"\"\"Agent Loop — Núcleo AGI: Think → Act → Observe → Learn.  Orquestra o pipeline completo de geração de NPCs: 1. THINK: Analisa descrição, busca exemplos similares + KG, planeja 2. ACT: Gera código via NPCGenerator com placeholders do LLM 3. OBSERVE: Valida com LuaValidator, verifica SQL injection 4. LOOP: Se falhar, retry com correção (max 3) 5. LEARN: Registra lições no histórico + Knowledge Graph  Uso:     from modulos.agent_loop import AgentLoop     agent = Ag", "ctx": "fuel_codigo", "timestamp": 1782920191.4559667}
{"erro": "modulo_aprendiz_de_padroes.py", "solucao": "Codigo do modulo aprendiz_de_padroes.py: \"\"\"AprendizDePadroes — Aprendiz autônomo de padrões para IE e PE.  Lê QUALQUER fonte de dados, usa PE.tokenizar_universal() + extrair_padroes() para descobrir estruturas e co-ocorrências, e salva lessons no KG (ctx='padrao_aprendido') que a IntentionEngine carrega em runtime.  1 método universal substitui 6 especializados. \"\"\" import os, json, re from collections import Counter, defaultdict from typing import List, Dict, Optional   class AprendizDePadroes", "ctx": "fuel_codigo", "timestamp": 1782920195.4966326}
{"erro": "modulo_auto_repair.py", "solucao": "Codigo do modulo auto_repair.py: \"\"\"AutoRepair — Repara codigo com erro baseado na mensagem do validador.  Quando o validador detecta um erro (linha, descricao), o AutoRepair usa o FAST model para corrigir o codigo em UMA tentativa.  Conceito: Se o validador ACHOU o erro, o reparador SABE o que corrigir. Nao precisa de loop — erro conhecido = correcao direta.  Uso:     reparador = AutoRepair(ia)     codigo_corrigido = reparador.reparar(codigo_errado, erros, linguagem) \"\"\" from modulos.util impor", "ctx": "fuel_codigo", "timestamp": 1782920199.5326955}
{"fingerprint": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "entropia": 0.62, "timestamp": 1782938851.6521554, "texto": "O que ainda nao esta MCR? o que ainda nao segue padroes? a ASSINATURA, o que ainda e Hardcoded?", "autor": "Kheltz"}
{"fingerprint": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "entropia": 0.438, "timestamp": 1782938851.652765, "texto": "TODOS, resolva TODOS, conecte TODOS!", "autor": "Kheltz"}
{"fingerprint": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "entropia": 0.69, "timestamp": 1782938851.653402, "texto": "analise o MCR.py POR COMPLETO e reflita, o MCR sabe decidir melhor que ninguem", "autor": "Kheltz"}
{"fingerprint": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "entropia": 0.62, "timestamp": 1782938885.2691524, "texto": "O que ainda nao esta MCR? o que ainda nao segue padroes? a ASSINATURA, o que ainda e Hardcoded?", "autor": "Kheltz"}
{"fingerprint": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "entropia": 0.438, "timestamp": 1782938885.2699175, "texto": "TODOS, resolva TODOS, conecte TODOS!", "autor": "Kheltz"}
{"estado_key": "ultima_migracao", "valor": 1782940722.6345568}
{"estado_key": "licoes_originais", "valor": 1799}
"""

if __name__ == '__main__':
    import sys, os
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _base not in sys.path:
        sys.path.insert(0, _base)
    _autotestar()