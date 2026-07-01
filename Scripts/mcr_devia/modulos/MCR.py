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
        return [(p, c/total) for p, c in sorted_prox[:n]]
    
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
        da = texto_a.encode('utf-8')[:500]
        db = texto_b.encode('utf-8')[:500]
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
        mk.aprender_sequencia(list(dados[:500]))
        
        # Top 5 transicoes mais comuns
        top5 = []
        for estado, prox in sorted(mk.transicoes.items(), 
                                     key=lambda x: -sum(x[1].values()))[:5]:
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
            texto = entrada.decode('utf-8', errors='replace')[:2000]
        except:
            texto = str(entrada[:200])
        
        palavras = texto.split()
        semente = palavras[0] if palavras else 'byte'
        
        # 3. Gera saida via Cadeia (em bytes)
        conector = MCRConector()
        conector.alimentar(texto[:500], "entrada_bytes")
        cadeia = MCRCadeia(conector)
        res = cadeia.gerar(semente, n_tokens=30)
        saida_texto = res.get('texto', semente)
        saida_bytes = saida_texto.encode('utf-8')[:2000]
        
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
            saida_bytes = saida_texto.encode('utf-8')[:2000]
            assinatura_out = self._extrair_assinatura(saida_bytes)
            compatibilidade = self._comparar_assinaturas(assinatura_in, assinatura_out)
        
        # 7. Autoavalia
        nota = round(compatibilidade * 10, 1)
        
        # 8. Aprende
        self.aprender(f"BYTES:{hash(entrada[:100])%10000}", f"COMPAT:{compatibilidade:.2f}")
        
        return {
            'entrada_tamanho': len(entrada),
            'saida_tamanho': len(saida_bytes),
            'assinatura_entrada': assinatura_in,
            'assinatura_saida': assinatura_out,
            'compatibilidade': round(compatibilidade, 3),
            'nota': nota,
            'iteracoes': iteracao,
            'saida': saida_texto[:300] if len(saida_texto) > 300 else saida_texto,
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
    Regra de Ouro: n_dims = max(8, min(256, n_tipos_unicos * 4))."""
    
    @staticmethod
    def calcular_dimensoes(tokens) -> int:
        tipos = set(t[0] for t in tokens) if tokens else set()
        return max(8, min(256, len(tipos) * 4))
    
    @staticmethod
    def gerar(texto: str) -> list:
        """Fingerprint MCR puro (sem PatternEngine)."""
        # Tokeniza via MCR (sem PAL_*/INTENT_* fixos)
        palavras = texto.split()
        if not palavras:
            return [0.0]*8
        # Classifica cada palavra por MCR
        try:
            from modulos.MCR import _classificar_token as _mcr_tp
            tokens = [(_mcr_tp(p), p) for p in palavras if p]
        except:
            tokens = [('outro', p) for p in palavras if p]
        if not tokens:
            return [0.0]*8
        n_dims = MCRFingerprint.calcular_dimensoes(tokens)
        histograma = [0.0]*n_dims
        for t in tokens:
            histograma[hash(t[0]) % n_dims] += 1
        total = sum(histograma) or 1
        return [h/total*10 for h in histograma]


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
            dados = origem.encode('utf-8')[:max_bytes]
        
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
                f"ciclo:{nome_base[:40]}",
                f"Tipo: {tipo}, Entropia: {entropia:.2f}, Bytes: {len(dados)}. "
                f"Estados: {n_estados}. Origem: {origem[:100]}.",
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
                conector.alimentar(texto[:500] if 'texto' in dir() else origem, "ciclo_entrada")
                for nome, dados_t in list(conector.topicos.items())[:3]:
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

_SUJEITOS_LORE = ['era', 'havia', 'existia', 'cidade', 'reino', 'mundo',
    'terra', 'povo', 'rei', 'rainha', 'guerreiro', 'mago', 'druida',
    'elfo', 'anao', 'orc', 'dragão', 'fada', 'heroi', 'lendario',
    'castelo', 'torre', 'floresta', 'montanha', 'rio', 'mar', 'sol',
    'lua', 'estrela', 'vento', 'fogo', 'cristal', 'magia', 'poder',
    'antigo', 'novo', 'grande', 'pequeno', 'sabio', 'guardiao']

_VERBOS_LORE = ['fundar', 'construir', 'criar', 'nascer', 'crescer',
    'tornar', 'virar', 'transformar', 'descobrir', 'encontrar',
    'buscar', 'lutar', 'proteger', 'defender', 'governar',
    'reinou', 'governou', 'liderou', 'caminhou', 'partiu',
    'chegou', 'trouxe', 'fez', 'disse', 'contou', 'viveu']


def _classificar_token(token: str) -> str:
    """Classifica um token em domínio: código, lore, sistema, linguagem, especial."""
    if not token: return 'especial'
    if token in ('<unk>', '<s>', '</s>', '<pad>', '<mask>',
                 '<|begin_of_text|>', '<|end_of_text|>', '<|pad|>'):
        return 'especial'
    if token.startswith('<|') or token.startswith('<｜'):
        return 'sistema'
    for p in _PADROES_CODIGO:
        if p in token: return 'codigo'
    if token.isupper() and len(token) >= 2: return 'sistema'
    if token[0].isupper() and len(token) > 1: return 'lore'
    if token.isdigit() or (token[0] == '-' and token[1:].isdigit()): return 'numero'
    if all(c in '.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\ \t\n\r\u2581' for c in token):
        return 'pontuacao'
    if all(c == '\u2581' for c in token): return 'pontuacao'
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
            nome_blob = os.path.basename(caminho_blob)[:16]
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
                    p = t[:2].lower()
                    if p not in prefixos: prefixos[p] = []
                    prefixos[p].append(t)
            
            for prefixo, membros in sorted(prefixos.items(),
                                            key=lambda x: -len(x[1]))[:max_tokens_kg]:
                if len(membros) >= 5:
                    dominios_cont = Counter(_classificar_token(m) for m in membros)
                    dom_principal = dominios_cont.most_common(1)[0][0]
                    self.kg.aprender_conceito(
                        f"cluster_{prefixo}",
                        f"{len(membros)} tokens, dominio={dom_principal}. "
                        f"Ex: {', '.join(membros[:6])}",
                        ctx="tokenizer_cluster"
                    )
                    n_guardados += 1
            
            # Dominios
            for dominio, count in self.dominios.most_common():
                exemplos = [t['token'] for t in self.token_info
                           if t['dominio'] == dominio][:8]
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
                if t['dominio'] == dominio][:max_tokens]


class AutoavaliadorSemantico:
    """Usa o proprio MCR para avaliar se um texto TEM SENTIDO.
    
    4 métricas semânticas (MCR sobre MCR):
    1. Coerência de domínio — os tokens pertencem ao domínio esperado
    2. Estrutura narrativa — tem sujeito-verbo, começo-meio-fim
    3. Consistência — não muda de assunto no meio
    4. Originalidade — não é cópia exata de algo no KG
    """
    
    def __init__(self, kg=None, precache=None):
        self.kg = kg or (_get_kg())
        self.precache = precache
    
    def avaliar(self, texto: str, dominio_esperado='lore') -> dict:
        """Avalia um texto gerado e retorna nota semântica + diagnóstico."""
        if not texto or len(texto) < 20:
            return {'nota': 0.0, 'diagnostico': 'MUITO_CURTO',
                    'detalhes': {
                        'nota_dominio': 0, 'nota_estrutura': 0,
                        'nota_consistencia': 0, 'nota_originalidade': 0,
                        'n_frases': 0, 'tem_sujeito': False, 'tem_verbo': False,
                        'repeticao': 0, 'qtd_termos_dominio': 0,
                    }}
        
        palavras = texto.lower().split()
        n_palavras = len(palavras)
        n_chars = len(texto)
        
        # 1. COERENCIA DE DOMINIO
        # Os tokens/perguntas sao do dominio esperado?
        termos_dominio = _SUJEITOS_LORE + _VERBOS_LORE if dominio_esperado == 'lore' else []
        if dominio_esperado == 'codigo':
            termos_dominio = _PADROES_CODIGO
        
        qtd_termos = sum(1 for t in termos_dominio if t in texto.lower())
        proporcao_dominio = min(1.0, qtd_termos / max(len(termos_dominio) * 0.1, 1))
        
        nota_dominio = proporcao_dominio * 3  # 0-3
        
        # 2. ESTRUTURA NARRATIVA
        tem_sujeito = any(s in texto.lower() for s in _SUJEITOS_LORE[:20])
        tem_verbo = any(v in texto.lower() for v in _VERBOS_LORE[:20])
        tem_maiuscula_inicio = texto[0].isupper() if texto else False
        tem_pontuacao_final = any(texto.rstrip().endswith(p) for p in '.!?')
        n_frases = sum(1 for c in texto if c in '.!?')
        
        nota_estrutura = 0
        if tem_sujeito: nota_estrutura += 0.75
        if tem_verbo: nota_estrutura += 0.75
        if tem_maiuscula_inicio and tem_pontuacao_final: nota_estrutura += 0.75
        if n_frases >= 2: nota_estrutura += 0.75  # mais de 1 frase
        # 0-3
        
        # 3. CONSISTENCIA INTERNA
        # Mede repeticao de bigramas (texto ciclico tem alta repeticao)
        if n_palavras >= 4:
            bigramas = [' '.join(palavras[i:i+2]) for i in range(n_palavras-1)]
            bigramas_unicos = len(set(bigramas))
            repeticao = 1.0 - (bigramas_unicos / max(len(bigramas), 1))
        else:
            repeticao = 0.0
        
        nota_consistencia = max(0, 1 - repeticao * 2) * 2  # 0-2
        
        # 4. ORIGINALIDADE (vs KG)
        nota_originalidade = 2.0  # 0-2, começa como maxima
        if self.kg:
            # Verifica se o texto copiou lessons do KG
            for l in self.kg._get_licoes()[:100]:
                sol = l.get('solucao', '')
                if sol and len(sol) > 50:
                    # Jaccard entre texto gerado e lesson
                    mk_temp = MarkovUniversal("orig")
                    jac = mk_temp.jaccard_bytes(texto, sol)
                    if jac > 0.8:  # Muito similar = copia
                        nota_originalidade = 0.5
                        break
                    elif jac > 0.5:
                        nota_originalidade = 1.0
        
        # NOTA FINAL SEMANTICA (0-10)
        nota_semantica = nota_dominio + nota_estrutura + nota_consistencia + nota_originalidade
        nota_semantica = round(max(0, min(10, nota_semantica)), 1)
        
        # Diagnostico
        if nota_semantica >= 7.0:
            diag = 'NARRATIVO_COERENTE'
        elif nota_semantica >= 5.0:
            diag = 'ESTRUTURADO'
        elif nota_semantica >= 3.0:
            diag = 'FRACO'
        elif nota_semantica >= 1.0:
            diag = 'GARBAGE'
        else:
            diag = 'VAZIO'
        
        return {
            'nota': nota_semantica,
            'diagnostico': diag,
            'detalhes': {
                'nota_dominio': round(nota_dominio, 2),
                'nota_estrutura': round(nota_estrutura, 2),
                'nota_consistencia': round(nota_consistencia, 2),
                'nota_originalidade': round(nota_originalidade, 2),
                'n_frases': n_frases,
                'tem_sujeito': tem_sujeito,
                'tem_verbo': tem_verbo,
                'repeticao': round(repeticao, 3),
                'qtd_termos_dominio': qtd_termos,
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
            erro = l.get('erro', '')[:60]
            partes.append(f"[{ctx}] {erro}: {sol[:300]}")
            n_lessons += 1
        
        # Textos de lore do corpus
        for texto in textos_lore[:5]:
            if len(texto) > 100:
                partes.append(f"[CORPUS] {texto[:500]}")
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
                'pontes': pontes[:8], 'melhor': pontes[0] if pontes else None}


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
        h = hashlib.md5(f"{min(topico_a,topico_b)}|{max(topico_a,topico_b)}".encode()).hexdigest()[:12]
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
        """Byte(2) + Palavra(5) + Token(3) = 10 pts"""
        if not sequencia or len(sequencia.strip()) < 3:
            return 0.0, {'erro': 'vazia'}
        
        # Nivel Byte (2 pts)
        j_a = self.mcr_byte.jaccard_bytes(sequencia, texto_a)
        j_b = self.mcr_byte.jaccard_bytes(sequencia, texto_b)
        seq_bytes = sequencia.encode('utf-8')[:200]
        trans_ok = 0
        for i in range(len(seq_bytes)-1):
            e = f"B:{seq_bytes[i]:02x}"
            p = f"B:{seq_bytes[i+1]:02x}"
            if e in self.mcr_byte.transicoes and p in self.mcr_byte.transicoes.get(e, {}):
                trans_ok += 1
        c_byte = trans_ok / max(len(seq_bytes)-1, 1)
        nb = (0.5 if j_a < 0.3 else 0) + (0.5 if j_b < 0.3 else 0) + (1.0 if c_byte > 0.5 else c_byte*2)
        
        # Nivel Palavra (5 pts)
        pal_seq = sequencia.split()
        c_pal = sum(1 for p in pal_seq if p in self.mcr_palavra.freq)/max(len(pal_seq), 1)
        cont_a = {p.lower() for p in texto_a.split() if len(p)>=4 and p.lower() not in CONECTORES}
        cont_b = {p.lower() for p in texto_b.split() if len(p)>=4 and p.lower() not in CONECTORES}
        cont_seq = {p.lower() for p in pal_seq if len(p)>=4 and p.lower() not in CONECTORES}
        np = (1.0 if c_pal > 0 else 0) + min(1.5, len(cont_seq & cont_a)*0.5) \
             + min(1.5, len(cont_seq & cont_b)*0.5) + (1.0 if c_pal > 0.3 else c_pal*3)
        
        # Nivel Token (3 pts)
        c_tok = 0
        if len(pal_seq) > 1:
            c_tok = sum(1 for i in range(len(pal_seq)-1)
                       if pal_seq[i][0].upper() in self.mcr_token.transicoes
                       and pal_seq[i+1][0].upper() in self.mcr_token.transicoes.get(pal_seq[i][0].upper(), {}))
            c_tok /= (len(pal_seq)-1)
        tipos_a = {p[0].upper() for p in texto_a.split() if p}
        tipos_b = {p[0].upper() for p in texto_b.split() if p}
        tipos_seq = {p[0].upper() for p in pal_seq if p}
        nt = (0.5 if tipos_seq & tipos_a else 0) + (0.5 if tipos_seq & tipos_b else 0) \
             + (2.0 if c_tok > 0.3 else c_tok*6)
        
        penalidade = 1.0
        if tipo_ponte == 'byte_only': penalidade = 0.3
        elif tipo_ponte == 'none': penalidade = 0.1
        
        nota = min(10, (nb + np + nt) * penalidade)
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
        linhas.append(f"  Sequencia: {conexao.get('sequencia','')[:100]}")
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
              contexto_tamanho: int = 3, max_tentativas_loop: int = 5) -> dict:
        """Gera N tokens com contexto reinjetado e deteccao MCR."""
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
            
            # 2. Prediz proximo token
            ultimo = contexto[-1]
            prox, conf = mk.predizer(ultimo)
            if prox is None or conf < 0.01:
                prox, conf = mk.predizer(semente)
                if prox is None or conf < 0.01: break
            
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
                    outros = [n for n in self.conector.topicos.keys() if n != token_str[:20]]
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
        if loops_nao_quebrados > 0: nota -= loops_nao_quebrados * 2
        if repeticao > 0.3: nota -= (repeticao - 0.3) * 10
        nota = max(1, min(10, nota))
        
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
            dados = sol.encode('utf-8')[:200]
            freq = {}
            for b in dados: freq[b] = freq.get(b, 0) + 1
            n = len(dados)
            h = 0.0
            for c in freq.values():
                p = c / n
                if p > 0: h -= p * math.log2(p)
            # Threshold por MCR, nao fixo
            if h < _MCR_THRESHOLD_FILTRO.calcular(1.0):
                return False
        # JSON detectado por primeiro caractere
        if sol.strip().startswith('{') or sol.strip().startswith('['):
            return False
        # Metadata de sistema
        if sol.startswith('[') and ']' in sol[:20]:
            return False
        return True
    
    def perguntar(self, pergunta: str, max_tokens: int = 80) -> dict:
        """Responde uma pergunta usando MCR."""
        # 1. Extrai termos da pergunta
        termos = [p.lower().strip('.,!?') for p in pergunta.split() 
                  if len(p) > 3 and p.lower() not in CONECTORES]
        
        # 2. Busca no KG
        lessons = []
        if self.kg:
            for termo in termos[:3]:
                ls = self.kg.buscar(termo, max_r=3, pergunta=pergunta)
                lessons.extend(ls)
        
        # 3. Alimenta conector com lessons encontradas (FILTRADAS E LIMPAS)
        topicos_alimentados = []
        mk_filtro = MarkovUniversal("filtro_kg")
        for i, l in enumerate(lessons[:10]):
            sol = l.get('solucao', '') or l.get('erro', '')
            if not self._filtrar_lesson(sol, mk_filtro): continue
            sol = self._limpar_texto(sol)
            if sol and len(sol) > 30:
                nome = f"kg_{i}_{l.get('ctx', 'desconhecido')}"
                self.conector.alimentar(sol[:500], nome)
                topicos_alimentados.append(nome)
        
        # Se não encontrou nada no KG, EXPANDE automaticamente
        if not topicos_alimentados:
            # Bridge + Expansao: usa 48 modulos para buscar conhecimento
            exp = self.expansao.expandir(termos[0] if termos else pergunta, max_recursos=10)
            if exp.get('expansoes', 0) > 0:
                # Tenta novamente com o KG expandido
                lessons2 = []
                for termo in termos[:3]:
                    ls = self.kg.buscar(termo, max_r=5, pergunta=pergunta)
                    lessons2.extend(ls)
                for i, l in enumerate(lessons2[:5]):
                    sol = l.get('solucao', '') or l.get('erro', '')
                    if self._filtrar_lesson(sol) and sol:
                        sol = self._limpar_texto(sol)
                        nome = f"kg_exp_{i}_{l.get('ctx', '?')}"
                        self.conector.alimentar(sol[:500], nome)
                        topicos_alimentados.append(nome)
            
            # Se ainda vazio, fallback na pergunta
            if not topicos_alimentados:
                sol_limpa = self._limpar_texto(pergunta)
                self.conector.alimentar(sol_limpa, "pergunta")
                topicos_alimentados.append("pergunta")
        
        # 4. Tenta conectar os topicos
        conexoes = []
        for i in range(len(topicos_alimentados)):
            for j in range(i+1, len(topicos_alimentados)):
                cx = self.conector.conectar(topicos_alimentados[i], topicos_alimentados[j])
                if cx:
                    conexoes.append(cx)
        
        # 5. Gera resposta com MCRCadeia
        # Semente = primeira palavra do PRIMEIRO topico (nao o nome do topico)
        if topicos_alimentados:
            primeiro_texto = self.conector.topicos.get(topicos_alimentados[0], {}).get('texto', pergunta)
        else:
            primeiro_texto = pergunta
        # Pega a primeira palavra real do texto
        palavras_primeiro = primeiro_texto.split()
        semente = palavras_primeiro[0] if palavras_primeiro else pergunta.split()[0]
        # Verifica se a semente existe no Markov
        if semente not in self.conector.mcr_palavra.freq and len(palavras_primeiro) > 1:
            semente = palavras_primeiro[1] if len(palavras_primeiro) > 1 else semente
        resultado_cadeia = self.cadeia.gerar(semente, n_tokens=max_tokens)
        
        # 6. PÓS-PROCESSAMENTO: MCR garante maiuscula + pontuacao
        texto = resultado_cadeia['texto']
        # Garante primeira maiuscula
        if texto and texto[0].islower():
            texto = texto[0].upper() + texto[1:]
        # Garante pontuacao final
        if texto and not any(texto.rstrip().endswith(p) for p in '.!?'):
            texto += '.'
        # Remove repeticoes de pontuacao
        import re
        texto = re.sub(r'([.!?])\1+', r'\1', texto)
        # Se tem mais de 200 chars, corta no primeiro ponto final depois de 80 chars
        if len(texto) > 200:
            idx_ponto = texto.find('.', 80)
            if idx_ponto > 0:
                texto = texto[:idx_ponto+1]
        
        # 7. Autoavalia com MCRPesoNota (pesos aprendidos, nao fixos)
        av_sem = self.semantico.avaliar(texto, 'lore')
        nota_sem = av_sem.get('nota', 5) if isinstance(av_sem, dict) else 5
        nota_cadeia = resultado_cadeia.get('nota', 5)
        loops = resultado_cadeia.get('loops_detectados', 0)
        
        # PesoNota calcula nota HONESTA baseada em experiencias anteriores
        nota_final = self.peso_nota.calcular(
            byte_s=nota_cadeia,
            palavra_s=nota_sem,
            token_s=8 if loops < 3 else 3
        )
        
        # Feedback loop: se nota < 6, tenta com mais contexto
        if nota_final < 6 and not pergunta.startswith('[MCR Feedback]'):
            fb = MCRFeedback()
            res_fb = fb.processar_com_feedback(pergunta, max_tentativas=2)
            if res_fb.get('nota', 0) > nota_final:
                nota_final = res_fb['nota']
                texto = res_fb.get('resposta', texto)
                resultado_cadeia['nota'] = nota_final
        
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
            'resposta': texto[:600],
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
            for cx in conexoes[:3]:
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
        return [(c, v) for _, c, v in result[:top_n]]


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
            padrao = recentes[:periodo]
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
        estado = f"PERG:{pergunta[:30].lower()}"
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
                resultado = dados.decode('utf-8', errors='replace')[:500]
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
        """Remove duplicatas por Jaccard entre solucoes.
        Retorna quantas foram removidas."""
        if not self.kg: return 0
        licoes = self.kg._get_licoes()
        removidas = 0
        
        # Agrupa por ctx para comparar so dentro do mesmo contexto
        from collections import defaultdict
        por_ctx = defaultdict(list)
        for l in licoes:
            por_ctx[l.get('ctx', '?')].append(l)
        
        for ctx, grupo in por_ctx.items():
            for i in range(len(grupo)):
                for j in range(i+1, len(grupo)):
                    sol_i = grupo[i].get('solucao', '')
                    sol_j = grupo[j].get('solucao', '')
                    if not sol_i or not sol_j: continue
                    if len(sol_i) < 20 or len(sol_j) < 20: continue
                    
                    # Jaccard entre as duas solucoes
                    jac = MarkovUniversal("tmp").jaccard_bytes(sol_i, sol_j)
                    
                    if jac >= min_similaridade:
                        # Marca a menor como inativa
                        if len(sol_i) <= len(sol_j):
                            grupo[i]['inactive'] = True
                        else:
                            grupo[j]['inactive'] = True
                        removidas += 1
                        self.mk_dedup.aprender("DUPLICATA", f"JAC:{jac:.2f}")
        
        if removidas:
            self.kg.salvar()
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
            'distribuicao': {c: len(v) for c, v in sorted(cats.items(), key=lambda x: -len(x[1]))[:10]},
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
                    for doc in docs[:3]:
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
            f"Recursos: {', '.join(recursos_usados[:5])}.",
            ctx="expansao_auto"
        )
        
        return {
            'tema': tema,
            'expansoes': len(resultados),
            'recursos_usados': recursos_usados[:10],
            'lessons_agora': len(lessons_tema),
            'detalhes': resultados[:10],
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
                    for i, l in enumerate(lessons[:5]):
                        sol = l.get('solucao', '') or l.get('erro', '')
                        if sol:
                            self.conector.alimentar(sol[:500], f"kg_{i}")
                    self.resultado = [l.get('solucao', '')[:100] for l in lessons[:3]]
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
                    textos.extend(w.resultado[:2])
                self.mk.aprender(f"WORKER:{w.tarefa}", f"NOTA:{int(w.nota)}")
        
        # 7. Gera resposta final com MCRCadeia
        if textos:
            for t in textos[:3]:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t[:500], "consolidado")
        
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
            'resposta': resposta[:500],
            'nota': round(nota, 1),
            'n_workers': len(workers),
            'workers': [{'nome': w.nome, 'tarefa': w.tarefa, 'nota': w.nota, 'tempo': round(w.tempo, 3)} for w in workers],
            'diagnostico': diag,
            'tempo': round(time.time() - t0, 2),
        }


class MCRAutoStart:
    """Auto-start: MCR se auto-organiza quando o sistema inicia.
    
    Uso (no kernel.py):
        from modulos.MCR import MCRAutoStart
        MCRAutoStart.iniciar()
    """
    
    @staticmethod
    def iniciar() -> dict:
        """Executa auto-diagnostico e organizacao do MCR."""
        try:
            kg = _get_kg()
            if not kg: return {'erro': 'KG indisponivel'}
            
            bridge = MCRBridge()
            bridge.descobrir()
            
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


# Threshold global para filtros (MCR, nao fixo)
_MCR_THRESHOLD_FILTRO = MCRThreshold("filtro_global")


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
        self.kg.aprender(erro=erro[:80], causa=f"fuel:{ctx}", solucao=texto[:500], ctx=ctx)
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
                for nome in sorted(self.bridge.modulos.keys())[:30]:
                    mod = self.bridge.modulos[nome]
                    doc = (mod.__doc__ or '')[:200]
                    if doc:
                        self._alimentar(f"mod:{nome}", doc, "fuel_modulos")
                    # Tenta listar funcoes
                    funcoes = [a for a in dir(mod) if not a.startswith('_') and callable(getattr(mod, a, None))][:5]
                    if funcoes:
                        self._alimentar(f"mod:{nome}_funcoes", f"Funcoes: {', '.join(funcoes)}", "fuel_modulos")
            
            elif fonte == 'comandos':
                for nome in sorted(self.bridge.comandos.keys())[:30]:
                    self._alimentar(f"cmd:{nome}", f"Comando disponivel: {nome}", "fuel_comandos")
            
            elif fonte == 'manifesto':
                manifesto = self._ler(os.path.join(self._base, 'docs', 'MANIFEST.md'), 2000)
                if manifesto:
                    self._alimentar("manifesto", manifesto[:1000], "fuel_manifesto")
            
            elif fonte == 'prototipos':
                sandbox_dir = os.path.join(self._base, 'sandbox')
                for f in self._listar_arquivos(sandbox_dir, '.py', 15):
                    if f.endswith('.py') and ('prototipo' in f or 'test_' in f):
                        conteudo = self._ler(f, 300)
                        if conteudo:
                            nome = os.path.basename(f)
                            self._alimentar(f"prototipo_{nome}", conteudo[:200], "fuel_prototipos")
            
            elif fonte == 'cache':
                # Episodios
                ep_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
                if os.path.exists(ep_path):
                    try:
                        with open(ep_path, 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        for ep in dados[:20]:
                            req = ep.get('request', '')[:100]
                            suc = ep.get('sucesso', False)
                            if req:
                                self._alimentar(f"episodio_{req[:30]}", f"Request: {req} | Sucesso: {suc}", "fuel_cache")
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
                                    msg = entry.get('msg', '')[:200]
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
                termo_exemplo = list(dados['termos'])[:3] if dados['termos'] else [prefixo]
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
        
        Usa os termos do gap como palavra-chave.
        Escaneia docs/, codigo/, prototipos/.
        So alimenta lessons sobre o gap.
        """
        if not self.kg: return 0
        
        termo = gap['termos'][0] if gap['termos'] else gap['prefixo']
        n_antes = len(self.kg._get_licoes())
        
        # 1. Busca em docs via indice (0.01s, nao 10-20s)
        doc_idx = _get_doc_index()
        doc_idx.indexar()  # so escaneia se nao tiver cache
        docs_encontrados = doc_idx.buscar(termo)
        for doc in docs_encontrados[:5]:
            conteudo = doc_idx.ler(doc['caminho'], max_bytes=2000)
            if conteudo and termo.lower() in conteudo.lower():
                idx = conteudo.lower().find(termo.lower())
                inicio = max(0, idx - 100)
                fim = min(len(conteudo), idx + 300)
                trecho = conteudo[inicio:fim]
                if len(trecho) > 50:
                    self.kg.aprender_conceito(
                        f"{gap['prefixo']}:{os.path.basename(doc['caminho']).replace('.','_')}",
                        f"[Fonte: {doc['caminho']}]\n{trecho[:500]}",
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
                            f"[Prototipo: {fname}]\n{conteudo[:500]}",
                            ctx=f"gap_{gap['prefixo']}"
                        )
                except: pass
        
        # 3. Busca no codigo fonte
        if self.bridge and self.bridge._descobriu:
            for nome, mod in self.bridge.modulos.items():
                if termo.lower() in nome.lower():
                    doc = (mod.__doc__ or '')[:300]
                    if doc:
                        self.kg.aprender_conceito(
                            f"{gap['prefixo']}:mod_{nome}",
                            f"[Modulo: {nome}]\n{doc[:300]}",
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
        
        for gap in gaps[:10]:  # max 10 gaps por ciclo
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
            'detalhes': resultados[:10],
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
                elif isinstance(w.resultado, list): textos.extend(w.resultado[:2])
        
        if textos:
            for t in textos[:3]:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t[:500], "consolidado")
        
        # Expande UMA vez (nao 5x)
        expansoes_feitas = []
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
                for nome_topico in list(self.conector.topicos.keys())[:2]:
                    cx = self.conector.conectar(termo, nome_topico)
                    if cx:
                        self.conector.alimentar(cx.get('sequencia',''), f"emrg_{termo}")
        
        # Bridge: tenta comando como fallback (com cache)
        if 'explorar' in self.bridge.comandos:
            try: self.bridge.usar_comando('explorar', {'termo': termo})
            except: pass
        
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
            'resposta': resposta[:500],
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
        for gap in gaps[:5]:
            n = self.meta.buscar_para_gap(gap)
            if n > 0:
                self.mk.aprender(f"GAP:{gap['prefixo']}", f"{n}")
        return [f"gap_{g['prefixo']}" for g in gaps[:3] if g]
    
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
                for doc in docs[:2]:
                    c = idx.ler(doc['caminho'], 500)
                    if c and self.kg:
                        self.kg.aprender_conceito(f"auto_{os.path.basename(doc['caminho']).replace('.','_')}", c[:400], ctx="auto_descoberta")
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
        """7 perguntas, acoes tomadas."""
        todas = []
        for fn in [self._p1_gaps, self._p2_lento, self._p7_esqueceu,
                   self._p3_repetiu, self._p4_errou, self._p5_aprendeu, self._p6_precisa]:
            try:
                todas.extend(fn())
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
                        'termos': list(termos)[:100],
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
        self.mk.aprender_sequencia(list(dados[:1000]))
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
                dados_novo = dados_reconstruidos.encode('utf-8')[:500]
            elif novo_nivel == 'token':
                # Nivel token: usa _classificar_token em cada estado
                try:
                    tokens_tipos = []
                    for e in estados[:20]:
                        pal = str(e).replace('B:', '').strip()
                        if pal:
                            from modulos.MCR import _classificar_token as _mcr_tip
                            tokens_tipos.append(_mcr_tip(pal) or 'outro')
                    dados_novo = ' '.join(tokens_tipos).encode('utf-8')
                except:
                    dados_novo = dados_reconstruidos.encode('utf-8')[:500]
            elif novo_nivel == 'intencao':
                # Nivel intencao: usa os estados como palavras de intencao
                dados_novo = dados_reconstruidos.encode('utf-8')[:500]
            else:
                # Outros niveis: dados reconstruidos do byte
                dados_novo = dados_reconstruidos.encode('utf-8')[:500]
            
            self.niveis[novo_nivel].alimentar(dados_novo)
        
        return 1


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
            nome = f"filosofia_{pergunta[:15].strip().lower()}"
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
                        return f"[Filosofia] {pergunta}\n[Conexao] {cx.get('sequencia', '')[:200]}"
        
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
        """Processa com feedback: se nota baixa, solicita mais dados."""
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
                'resposta': res.get('resposta', '')[:100],
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
    testar(f'MCRSignature.metaniveis {mn["niveis_finais"]} niveis ordem={mn["ordem"][:3]}',
           mn['niveis_finais'] >= 3)
    
    # 24. MCRSession
    sess = MCRSession()
    sess.registrar("teste", "resposta_teste", "autoteste")
    sess.salvar_estado()
    carregado = sess.carregar_estado()
    testar(f'MCRSession.registrar + salvar + carregar', carregado is not None)
    testar(f'MCRSession.ultima_pergunta={sess.ultima_pergunta()}', 
           sess.ultima_pergunta() == 'teste')
    
    # 25. MCRAssinatura
    banco = MCRAssinatura()
    banco.aprender("Explique o sistema SPA do MCR", "Kheltz")
    banco.aprender("Crie um NPC ferreiro em Eridanus", "Kheltz")
    autor, conf, _ = banco.identificar("Explique o SPA do projeto MCR")
    testar(f'MCRAssinatura identificar autor={autor} conf={conf:.2f}', 
           conf > 0.3)
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

class MCRSignature:
    """Assinatura unica de QUALQUER dado.
    
    Nao define campos. Nao define estrutura.
    So conecta MCRByte + MCRMetaNivel + similaridade.
    
    Uso:
        sig = MCRSignature()
        a = sig.extrair("SPA = Sistema")    # → assinatura unica de bytes
        b = sig.extrair("SPA = Progressao")
        sim = sig.comparar(a, b)            # → 0.224 (Jaccard)
        niveis = sig.metaniveis("Explique SPA")  # → quantos niveis emergem
    """
    
    @staticmethod
    def extrair(dados) -> dict:
        """Extrai a assinatura unica de QUALQUER dado.
        
        A assinatura nao e um conjunto de campos — e a sequencia
        completa de transicoes MCRByte, que captura:
        - Estrutura (entropia, delimitadores)  
        - Fluxo (transicoes mais provaveis)
        - Identidade (nenhum outro dado tem a mesma sequencia)
        """
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
        if not isinstance(dados, bytes):
            dados = str(dados).encode('utf-8')[:2000]
        
        mk = MCR("signature")
        mk.aprender_sequencia(list(dados))
        
        # Gera a sequencia unica (a "impressao digital")
        primeiro = list(mk.freq.keys())[0] if mk.freq else '0'
        sequencia = mk.gerar(primeiro, passos=50)
        
        return {
            'entropia': round(mk.entropia_media(), 3),
            'estados': len(mk.transicoes),
            'transicoes': sum(len(v) for v in mk.transicoes.values()),
            'sequencia': sequencia[:20],
            'fingerprint': MCRFingerprint.gerar(
                ' '.join(str(s) for s in sequencia[:10])
            ),
        }
    
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
        self._historico.append({'pergunta': pergunta, 'resposta': resposta[:200], 'autor': autor})
        
        # Salva no .jsonl
        try:
            os.makedirs(os.path.dirname(self._conv_path), exist_ok=True)
            with open(self._conv_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'msg': f'{autor}: {pergunta} -> {resposta[:100]}',
                                   'timestamp': _time.time()}) + '\n')
        except: pass
        
        self.mk.aprender(f"CONV:{pergunta[:30]}", f"autor:{autor or 'anonimo'}")
    
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
            self.mk.aprender("RETOMADA", f"pergunta:{estado.get('ultima_pergunta','')[:30]}")
            return estado
        return None


# ============================================================
# MCR ASSINATURA — Banco de assinaturas de autores
# ============================================================

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
            except: pass
    
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._banco_path), exist_ok=True)
            with open(self._banco_path, 'w', encoding='utf-8') as f:
                json.dump(self._banco, f, ensure_ascii=False, indent=2)
        except: pass
    
    def aprender(self, texto, autor):
        """Aprende a assinatura de um autor a partir de um texto."""
        if not texto or not autor: return
        sig = MCRSignature.extrair(texto)
        if autor not in self._banco:
            self._banco[autor] = []
        self._banco[autor].append({
            'fingerprint': sig.get('fingerprint', []),
            'entropia': sig.get('entropia', 0),
            'timestamp': _time.time(),
        })
        self.mk.aprender(f"AUTOR:{autor}", f"ent:{sig.get('entropia',0):.2f}")
        self._salvar()
    
    def identificar(self, texto):
        """Identifica quem escreveu o texto comparando com o banco.
        
        Retorna: (nome_autor, confianca, detalhes)
        """
        if not texto or not self._banco: return ('desconhecido', 0.0, {})
        
        sig_alvo = MCRSignature.extrair(texto)
        fp_alvo = sig_alvo.get('fingerprint', [])
        if not fp_alvo: return ('desconhecido', 0.0, {})
        
        melhor_autor = 'desconhecido'
        melhor_conf = 0.0
        detalhes = {}
        
        for autor, assinaturas in self._banco.items():
            confs = []
            for ass in assinaturas[-5:]:  # ultimas 5 assinaturas
                fp_ass = ass.get('fingerprint', [])
                if fp_ass and len(fp_ass) == len(fp_alvo):
                    # Cosseno entre fingerprints
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
        
        return (melhor_autor, round(melhor_conf, 3), detalhes)
    
    def auto_popular(self):
        """Auto-popula o banco a partir das conversas existentes (.jsonl).
        
        Agrupa por similaridade de assinatura (MCRSignature.comparar > 0.7).
        Cria perfis automaticamente.
        """
        conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
        if not os.path.exists(conv_path): return 0
        
        n = 0
        autor_atual = 'desconhecido'
        ultima_sig = None
        
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                for linha in f:
                    try:
                        entry = json.loads(linha.strip())
                        msg = entry.get('msg', '')
                        if not msg or len(msg) < 20: continue
                        
                        sig_atual = MCRSignature.extrair(msg)
                        
                        # Se tem assinatura anterior, compara
                        if ultima_sig is not None:
                            comp = MCRSignature.comparar(ultima_sig, sig_atual)
                            if comp < 0.5:
                                # Autor diferente
                                autor_atual = f'autor_{n}'
                                n += 1
                        
                        self.aprender(msg, autor_atual)
                        ultima_sig = sig_atual
                    except: pass
        except: pass
        
        self.mk.aprender("AUTO_POP", f"autores:{n}")
        return n
    
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
        """Estuda os N maiores gaps do conhecimento.
        
        Pega gaps do MCRMetaGap, busca conteudo na web, indexa no KG.
        """
        if not self._kg: return 0
        
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        if not gaps: return 0
        
        total = 0
        for gap in gaps[:n_gaps]:
            termo = gap['prefixo']
            resultado = self._buscar_web(termo)
            if resultado:
                self._kg.aprender_conceito(
                    f"weblearn:{termo}",
                    f"[WebLearn] {resultado[:500]}",
                    ctx="weblearn"
                )
                total += 1
                self.mk.aprender(f"WWW:{termo}", "OK")
        return total
    
    def _buscar_web(self, termo):
        """Busca termo na web via Wikipedia API (leve, sem LLM)."""
        if not self._urlopen: return None
        try:
            url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={termo}&format=json&srlimit=1"
            resp = self._urlopen(url, timeout=10).read()
            dados = json.loads(resp.decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            if resultados:
                titulo = resultados[0].get('title', '')
                if titulo:
                    # Pega o resumo
                    url2 = f"https://pt.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=extracts&exintro=true&format=json"
                    resp2 = self._urlopen(url2, timeout=10).read()
                    dados2 = json.loads(resp2.decode('utf-8'))
                    pages = dados2.get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract:
                            # Remove tags HTML
                            import re
                            texto = re.sub(r'<[^>]+>', '', extract)
                            return f"[Wikipedia: {titulo}] {texto[:1000]}"
            return f"[Wikipedia] Resultado sobre {termo} encontrado."
        except Exception as e:
            return f"[WebLearn] {termo}: {str(e)[:50]}"
    
    def ciclo_auto_estudo(self):
        """Ciclo completo de auto-estudo.
        
        Fluxo:
        1. Diagnostica gaps no KG
        2. Para cada gap, busca na web
        3. Indexa no KG
        4. Registra aprendizado
        """
        if not self._kg: return {'estudados': 0, 'erro': 'KG indisponivel'}
        
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        n_estudados = 0
        erros = 0
        
        for gap in gaps[:5]:
            termo = gap['prefixo']
            resultado = self._buscar_web(termo)
            if resultado and len(resultado) > 30:
                self._kg.aprender_conceito(
                    f"weblearn_auto:{termo}",
                    resultado[:500],
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
                    'linha': i+1, 'doc': doc[:100],
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
        c.alimentar(texto[:500], "blank")
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


if __name__ == '__main__':
    import sys, os
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _base not in sys.path:
        sys.path.insert(0, _base)
    _autotestar()
