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

# Imports opcionais (só se disponíveis)
try:
    from modulos.pattern_engine import PatternEngine
    from modulos.kg import KnowledgeGraph
    from modulos.tool_orchestrator import ToolOrchestrator
    MCR_COMPLETO = True
except ImportError:
    MCR_COMPLETO = False


class MarkovUniversal:
    """1 algoritmo, N níveis. Mesmo código para bytes, tokens, intenções, decisões."""
    
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
    
    def stats(self) -> Dict:
        return {
            'nome': self.nome, 'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'entropia': round(self.entropia_media(), 3),
        }


class MCRFingerprint:
    """Fingerprint MCR com N dimenções descoberto pela entropia.
    Regra de Ouro: n_dims = max(8, min(256, n_tipos_unicos * 4))."""
    
    @staticmethod
    def calcular_dimensoes(tokens) -> int:
        tipos = set(t[0] for t in tokens) if tokens else set()
        return max(8, min(256, len(tipos) * 4))
    
    @staticmethod
    def gerar(texto: str) -> list:
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        tokens = pe.tokenizar_universal(texto) if pe else []
        if not tokens: return [0.0]*8
        n_dims = MCRFingerprint.calcular_dimensoes(tokens)
        histograma = [0.0]*n_dims
        for t in tokens:
            histograma[hash(t[0]) % n_dims] += 1
        total = sum(histograma) or 1
        return [h/total*10 for h in histograma]


class MCR:
    """Classe ÚNICA do MCR. Substitui IE + AutoTrigger + Aprendiz + Pipeline.
    
    Uso:
        mcr = MCR()
        resultado = mcr.processar("Explique o SPA")
        # → {resposta, nota, acoes, ciclos, ...}
    """
    
    def __init__(self):
        self.pe = PatternEngine() if MCR_COMPLETO else None
        self.kg = KnowledgeGraph() if MCR_COMPLETO else None
        self.tools = ToolOrchestrator() if MCR_COMPLETO else None
        
        # IE (criado uma vez, não lazy)
        self.ie = None
        if self.pe and MCR_COMPLETO:
            try:
                from modulos.intention_engine import IntentionEngine
                self.ie = IntentionEngine(pe=self.pe)
            except ImportError:
                pass
        
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
        self.mcr = MCR()
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
        self.kg = kg or (KnowledgeGraph() if MCR_COMPLETO else None)
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
        self.kg = kg or (KnowledgeGraph() if MCR_COMPLETO else None)
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
        self.kg = kg or (KnowledgeGraph() if MCR_COMPLETO else None)
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
        self.historico_ciclos = []
    
    def gerar(self, semente: str, n_tokens: int = 100, 
              contexto_tamanho: int = 3, max_tentativas_loop: int = 5) -> dict:
        """Gera N tokens com contexto reinjetado.
        
        Args:
            semente: palavra inicial
            n_tokens: quantos tokens gerar
            contexto_tamanho: quantos tokens usar como contexto (K)
            max_tentativas_loop: quantas vezes tenta quebrar loop antes de desistir
        """
        if not self.conector.topicos:
            return {'texto': semente, 'tokens': [semente], 
                    'nota': 0, 'loops_detectados': 0, 'erro': 'sem topicos'}
        
        # Usa o mcr_palavra global do conector
        mk = self.conector.mcr_palavra
        
        tokens_gerados = [semente]
        loops_detectados = 0
        repeticoes_evitadas = 0
        tentativas_loop = 0
        ultimos_tokens = []
        
        for passo in range(n_tokens - 1):
            # 1. Define contexto = últimos K tokens
            if len(tokens_gerados) >= contexto_tamanho:
                contexto = tokens_gerados[-contexto_tamanho:]
            else:
                contexto = tokens_gerados
            
            # 2. Pega o ÚLTIMO token do contexto como semente
            ultimo = contexto[-1]
            prox, conf = mk.predizer(ultimo)
            
            if prox is None or conf < 0.01:
                # Tenta com semente original
                prox, conf = mk.predizer(semente)
                if prox is None or conf < 0.01:
                    break
            
            # 3. DETECTOR DE LOOP
            token_str = str(prox)
            em_loop = False
            
            # 3a. Mesmo token 3x seguidas
            if len(tokens_gerados) >= 3:
                if tokens_gerados[-1] == tokens_gerados[-2] == token_str:
                    em_loop = True
                # 3b. Bigrama repetido
                if len(tokens_gerados) >= 4:
                    ultimo_bigrama = f"{tokens_gerados[-2]} {tokens_gerados[-1]}"
                    novo_bigrama = f"{tokens_gerados[-1]} {token_str}"
                    # Verifica se o novo bigrama já apareceu antes
                    texto_ate_agora = ' '.join(tokens_gerados[:-1])
                    if novo_bigrama in texto_ate_agora:
                        em_loop = True
            
            if em_loop:
                loops_detectados += 1
                tentativas_loop += 1
                
                if tentativas_loop > max_tentativas_loop:
                    break  # Desiste
                
                # INJETA RUÍDO: pega token de outro tópico
                outros_topicos = [n for n in self.conector.topicos.keys()
                                 if n != token_str[:20]]
                if outros_topicos:
                    import random
                    topico_alternativo = random.choice(outros_topicos)
                    texto_alt = self.conector.topicos[topico_alternativo]['texto']
                    palavras_alt = texto_alt.split()
                    if palavras_alt:
                        prox = random.choice(palavras_alt)
                        conf = 0.5
                        repeticoes_evitadas += 1
                        tentativas_loop = 0  # reset após injetar ruído
            
            # 4. Adiciona token
            tokens_gerados.append(str(prox))
            ultimos_tokens.append(str(prox))
        
        # Converte para texto
        texto = ' '.join(tokens_gerados)
        
        # Autoavaliação simples
        palavras = texto.split()
        n_palavras = len(palavras)
        if n_palavras >= 4:
            bigramas = [' '.join(palavras[i:i+2]) for i in range(n_palavras-1)]
            repeticao = 1.0 - (len(set(bigramas)) / max(len(bigramas), 1))
        else:
            repeticao = 0.0
        
        nota = 10.0
        # Penaliza loops NÃO quebrados (repeticoes_evitadas = sucesso)
        loops_nao_quebrados = max(0, loops_detectados - repeticoes_evitadas)
        if loops_nao_quebrados > 0: nota -= loops_nao_quebrados * 2
        if repeticao > 0.3: nota -= (repeticao - 0.3) * 10
        nota = max(1, min(10, nota))  # nota minima 1
        
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
        self.kg = kg or (KnowledgeGraph() if MCR_COMPLETO else None)
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.semantico = AutoavaliadorSemantico(kg, None)
        self.log = []
    
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
        
        # 3. Alimenta conector com lessons encontradas
        topicos_alimentados = []
        for i, l in enumerate(lessons[:5]):
            sol = l.get('solucao', '') or l.get('erro', '')
            if sol and len(sol) > 20:
                nome = f"kg_{i}_{l.get('ctx', 'desconhecido')}"
                self.conector.alimentar(sol[:500], nome)
                topicos_alimentados.append(nome)
        
        # Se não encontrou nada no KG, usa a própria pergunta
        if not topicos_alimentados:
            self.conector.alimentar(pergunta, "pergunta")
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
        
        # 6. Autoavalia
        texto = resultado_cadeia['texto']
        av_sem = self.semantico.avaliar(texto, 'lore')
        
        # Tenta avaliacao multi-nivel se tiver pelo menos 2 topicos
        nota_multinivel = 0
        if len(topicos_alimentados) >= 2:
            ta = self.conector.topicos.get(topicos_alimentados[0], {}).get('texto', '')
            tb = self.conector.topicos.get(topicos_alimentados[1], {}).get('texto', '')
            nota_multinivel, _ = self.conector._autoavaliar_multinivel(
                texto, ta, tb, "conteudo_compartilhado"
            )
        
        # Nota final: media entre cadeia e semantica
        nota_cadeia = resultado_cadeia['nota']
        nota_final = (nota_cadeia + av_sem['nota'] + nota_multinivel) / 3
        
        resultado = {
            'pergunta': pergunta,
            'resposta': texto[:500],
            'nota': round(nota_final, 1),
            'n_tokens': resultado_cadeia['n_tokens'],
            'topicos_usados': topicos_alimentados,
            'n_conexoes': len(conexoes),
            'loops_detectados': resultado_cadeia['loops_detectados'],
            'repeticoes_evitadas': resultado_cadeia['repeticoes_evitadas'],
            'avaliacao_semantica': av_sem,
            'nota_multinivel': round(nota_multinivel, 1) if nota_multinivel else 0,
            'debug': self._gerar_debug(resultado_cadeia, conexoes, av_sem),
        }
        
        self.log.append(resultado)
        return resultado
    
    def _gerar_debug(self, cadeia, conexoes, av_sem):
        linhas = ["DEBUG MCRPergunta:"]
        linhas.append(f"  Cadeia: {cadeia['n_tokens']} tokens, nota {cadeia['nota']}/10")
        linhas.append(f"  Loops: {cadeia['loops_detectados']}, Repeticoes evitadas: {cadeia['repeticoes_evitadas']}")
        linhas.append(f"  Semantica: {av_sem['nota']}/10 ({av_sem['diagnostico']})")
        if conexoes:
            linhas.append(f"  Conexoes: {len(conexoes)}")
            for cx in conexoes[:3]:
                linhas.append(f"    {cx['topico_a']} <-> {cx['topico_b']}: {cx['nota']}/10")
        return '\n'.join(linhas)


# ============================================================
# TESTE RÁPIDO
# ============================================================

if __name__ == '__main__':
    import sys
    # Forca UTF-8 na saida (evita erro de encoding com acentos)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    print("=" * 70)
    print("  MCR - Teste Rapido de Validacao")
    print("=" * 70)
    
    if not MCR_COMPLETO:
        print("  [AVISO] Modulos opcionais nao disponiveis (kg, tools, pe)")
        print("  Testando apenas MarkovUniversal...")
        mk = MarkovUniversal("teste")
        mk.aprender_sequencia([1, 2, 3, 4, 5])
        print(f"  MarkovUniversal: {mk.stats()}")
        print(f"  Jaccard('SPA', 'SPA'): {mk.jaccard_bytes('SPA', 'SPA'):.3f}")
        print(f"  Jaccard('SPA', 'NPC'): {mk.jaccard_bytes('SPA', 'NPC'):.3f}")
        sys.exit(0)
    
    mcr = MCR()
    loop = MCRAutoLoop()
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "Crie um NPC ferreiro em Eridanus",
    ]
    
    for pergunta in perguntas:
        resultado = loop.processar(pergunta)
        status = "10/10" if resultado['nota'] >= 10 else f"{resultado['nota']}/10"
        print(f"\n  '{pergunta}...'")
        print(f"    Status: {status} em {resultado['ciclos']} ciclos")
        print(f"    Ferramentas: {resultado['ferramentas']}")
        print(f"    Resposta: {resultado['resposta']}...")
        print(f"    Notas: {resultado['notas']}")
    
    print(f"\n{'='*70}")
    print(f"  Teste concluido. Markovs treinados:")
    for mk in [mcr.mk_byte, mcr.mk_palavra, mcr.mk_token,
               mcr.mk_intencao, mcr.mk_decisor, mcr.mk_acao]:
        s = mk.stats()
        if s['estados'] > 0:
            print(f"    {s['nome']:10s}: {s['estados']:4d} estados, {s['transicoes']:4d} transicoes")
    print(f"{'='*70}")
