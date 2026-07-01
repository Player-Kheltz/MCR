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
    
    def aprender(self, a: Any, b: Any):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1; self.total += 1
        if sa not in self.transicoes: self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    
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
        if sa not in self.transicoes: return 0.0
        prox = self.transicoes[sa]; t = sum(prox.values())
        if t == 0: return 0.0
        h = 0.0
        for c in prox.values():
            p = c/t
            if p > 0: h -= p * math.log2(p)
        return h
    
    def entropia_media(self) -> float:
        if not self.transicoes: return 0.0
        hs = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(hs)/len(hs) if hs else 0.0
    
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
    
    def stats(self) -> Dict:
        return {
            'nome': self.nome, 'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'entropia': round(self.entropia_media(), 3),
        }


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
