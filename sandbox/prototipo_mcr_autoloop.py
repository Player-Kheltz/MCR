#!/usr/bin/env python3
"""MCR AUTO-LOOP — Só entrega quando estiver 10/10. Enquanto não, expande.

Ciclo:
  1. Tenta responder com o que tem
  2. Autoavalia: nota 0-10 (cobertura + entropia + tamanho)
  3. Se nota >= 10 → ✅ entrega
  4. Se nota < 10 → escolhe ferramenta → executa → aprende → VOLTA PRO PASSO 1
  5. Máximo de 10 ciclos. Se passar, LLM assume.

Cada ciclo adiciona CONHECIMENTO. O MCR fica mais inteligente a CADA tentativa.
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.tool_orchestrator import ToolOrchestrator

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.join(BASE, 'sandbox')


class MarkovUniversal:
    """1 algoritmo, N níveis."""
    def __init__(self, nome=""):
        self.nome = nome
        self.transicoes = {}
        self.freq = Counter()
    def aprender(self, a, b):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1
        if sa not in self.transicoes: self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    def aprender_sequencia(self, seq):
        for i in range(len(seq)-1): self.aprender(seq[i], seq[i+1])
    def predizer(self, a):
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]: return None, 0.0
        prox = self.transicoes[sa]
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor]/total
    def entropia(self, a):
        sa = str(a)
        if sa not in self.transicoes: return 0.0
        prox = self.transicoes[sa]
        t = sum(prox.values())
        if t == 0: return 0.0
        h = 0.0
        for c in prox.values(): p = c/t; 
        if p > 0: h -= p * math.log2(p)
        return h
    def entropia_media(self):
        if not self.transicoes: return 0.0
        hs = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(hs)/len(hs) if hs else 0.0
    def stats(self):
        return {'nome': self.nome, 'estados': len(self.transicoes), 'transicoes': sum(len(v) for v in self.transicoes.values())}


class MCRAutoLoop:
    """Só entrega quando 10/10. Expande conhecimento em loop."""
    
    def __init__(self):
        self.pe = PatternEngine()
        self.ie = IntentionEngine(pe=self.pe)
        self.kg = KnowledgeGraph()
        self.tools = ToolOrchestrator()
        
        # Markove
        self.mk_byte = MarkovUniversal("byte")
        self.mk_token = MarkovUniversal("token")
        self.mk_intencao = MarkovUniversal("intencao")
        self.mk_decisor = MarkovUniversal("decisor")
        self.mk_acao = MarkovUniversal("acao")
        
        self.total_exec = 0
    
    def _autoavaliar(self, resposta: str, pergunta: str) -> Tuple[float, Dict]:
        """Nota 0-10 baseada em MARKOV, não em regras.
        
        3 métricas:
        - COBERTURA: tipos da pergunta na resposta (%)
        - ENTROPIA: entropia da resposta (baixa = mais estruturada = melhor)
        - TAMANHO: quantidade de tokens
        """
        if not resposta or len(resposta) < 10:
            return 0.0, {'cobertura': 0, 'entropia': 1, 'tamanho': 0}
        
        tokens_resp = self.pe.tokenizar_universal(resposta) or []
        tokens_perg = self.pe.tokenizar_universal(pergunta) or []
        
        # Cobertura
        tipos_perg = set(t[0] for t in tokens_perg) if tokens_perg else set()
        tipos_resp = set(t[0] for t in tokens_resp) if tokens_resp else set()
        cobertura = len(tipos_perg & tipos_resp) / max(len(tipos_perg), 1) if tipos_perg else 0
        
        # Entropia da resposta (quanto mais estruturada, MENOR entropia)
        mk_temp = MarkovUniversal("tmp")
        if tokens_resp:
            mk_temp.aprender_sequencia([t[0] for t in tokens_resp])
        entropia = mk_temp.entropia_media()
        
        # Tamanho
        n_tokens = len(tokens_resp)
        
        # Nota ponderada
        nota = (cobertura * 4) + (max(0, 1 - entropia) * 3) + (min(1, n_tokens / 20) * 3)
        nota = round(min(10, nota * 10), 1)
        
        metricas = {
            'cobertura': round(cobertura, 3),
            'entropia': round(entropia, 3),
            'tamanho': n_tokens,
        }
        
        return nota, metricas
    
    def _extrair_termo(self, texto: str, tokens=None) -> str:
        """Extrai o termo MAIS relevante do texto."""
        if tokens is None:
            tokens = self.pe.tokenizar_universal(texto) or []
        
        # Tenta PROPER_NOUN (siglas) primeiro
        for t in tokens:
            if t[0] == 'PROPER_NOUN' and len(str(t[1])) > 1:
                return str(t[1])
        
        # Tenta DOM_* (sistema, npc, etc)
        for t in tokens:
            if t[0].startswith('DOM_') and len(str(t[1])) > 3:
                return str(t[1])
        
        # Palavras com 4+ chars
        palavras = [p for p in texto.split() if len(p) > 3]
        return palavras[0] if palavras else texto[:20]
    
    def _expandir(self, pergunta: str, ciclo: int, ferramentas_usadas: set) -> Tuple[str, str]:
        """Escolhe e executa uma ferramenta para expandir conhecimento.
        
        Returns:
            (resultado, nome_ferramenta)
        """
        # MarkovDecisor escolhe a ferramenta
        tokens = self.pe.tokenizar_universal(pergunta) or []
        
        # Escolhe baseado no que já foi usado (evita repetição)
        disponiveis = [f for f in 
            ['buscar_kg', 'buscar_estrategico', 'ler_arquivo', 'buscar_web']
            if f not in ferramentas_usadas]
        
        if not disponiveis:
            return None, "esgotado"
        
        acao = disponiveis[0]  # Markov decidiria, fallback simples
        
        termo = self._extrair_termo(pergunta, tokens)
        if not termo:
            return None, "sem_termo"
        
        resultado = ""
        
        if acao == 'buscar_kg':
            lessons = self.kg.buscar(termo, max_r=3)
            if lessons:
                resultado = '\n'.join(l.get('solucao', '') for l in lessons)
        
        elif acao == 'buscar_estrategico':
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    resultado = str(r.get('resultado', ''))[:500]
            except: pass
        
        elif acao == 'ler_arquivo':
            # Tenta ler arquivos .md que contenham o termo
            docs_dir = os.path.join(BASE, 'docs')
            if os.path.isdir(docs_dir):
                for f in os.listdir(docs_dir):
                    if f.endswith('.md') and termo.lower() in f.lower():
                        try:
                            with open(os.path.join(docs_dir, f), 'r', encoding='utf-8') as fh:
                                resultado = fh.read()[:500]
                        except: pass
                        break
        
        if not resultado or len(resultado) < 20:
            return None, acao
        
        # Aprende com o resultado
        self.mk_byte.aprender_sequencia(resultado.encode('utf-8')[:200])
        
        return resultado, acao
    
    def processar(self, pergunta: str, max_ciclos: int = 8) -> Dict:
        """Ciclo completo: executa → avalia → expande até 10/10."""
        print(f"\n  {'='*50}")
        print(f"  PERGUNTA: {pergunta[:50]}")
        print(f"  {'='*50}")
        
        t0 = _time.time()
        ferramentas_usadas = set()
        conhecimento_acumulado = ""
        notas = []
        
        for ciclo in range(1, max_ciclos + 1):
            print(f"\n  --- Ciclo {ciclo}/{max_ciclos} ---")
            
            # 1. Tenta gerar resposta com o conhecimento ATUAL
            if conhecimento_acumulado:
                tokens_conc = self.pe.tokenizar_universal(conhecimento_acumulado[:500])
                if tokens_conc:
                    tipos_conc = [t[0] for t in tokens_conc]
                    self.mk_token.aprender_sequencia(tipos_conc)
                bytes_conc = conhecimento_acumulado.encode('utf-8')[:200]
                for i in range(len(bytes_conc)-1):
                    self.mk_byte.aprender(f"B:{bytes_conc[i]:02x}", f"B:{bytes_conc[i+1]:02x}")
            
            # Gera resposta simples baseada no conhecimento
            if conhecimento_acumulado:
                # Pega trechos relevantes do conhecimento
                linhas = conhecimento_acumulado.split('\n')
                resposta = ' '.join(linhas[:5])[:300]
            else:
                # Tenta resposta do KG direto
                termo = self._extrair_termo(pergunta)
                lessons = self.kg.buscar(termo, max_r=2)
                if lessons:
                    resposta = lessons[0].get('solucao', '')[:300]
                else:
                    resposta = f"(Processando '{pergunta[:20]}...')"
            
            # 2. Autoavalia
            nota, metricas = self._autoavaliar(resposta, pergunta)
            notas.append(nota)
            
            print(f"    Resposta ({len(resposta)} chars): {resposta[:80]}...")
            print(f"    Nota: {nota}/10 (cobertura={metricas['cobertura']}, "
                  f"entropia={metricas['entropia']}, tamanho={metricas['tamanho']})")
            
            # 3. Se 10/10 → entrega
            if nota >= 10:
                print(f"    ✅ 10/10! Entregando resposta.")
                return {
                    'pergunta': pergunta,
                    'resposta': resposta,
                    'nota': nota,
                    'ciclos': ciclo,
                    'ferramentas': list(ferramentas_usadas),
                    'tempo': round(_time.time() - t0, 1),
                    'status': '10/10',
                }
            
            # 4. Se < 10 → expande
            print(f"    ⚠️ Nota {nota} < 10. Expandindo conhecimento...")
            resultado, ferramenta = self._expandir(pergunta, ciclo, ferramentas_usadas)
            
            if resultado is None or ferramenta == 'esgotado':
                print(f"    ❌ Todas as ferramentas esgotadas. Nota final: {nota}")
                return {
                    'pergunta': pergunta,
                    'resposta': resposta,
                    'nota': nota,
                    'ciclos': ciclo,
                    'ferramentas': list(ferramentas_usadas),
                    'tempo': round(_time.time() - t0, 1),
                    'status': f'esgotado({nota})',
                }
            
            ferramentas_usadas.add(ferramenta)
            
            if resultado and len(resultado) > 20:
                conhecimento_acumulado += '\n' + resultado
                print(f"    ✅ '{ferramenta}' → +{len(resultado)} chars de conhecimento")
            else:
                print(f"    ⚠️ '{ferramenta}' não trouxe dados novos")
        
        # Fim dos ciclos sem 10/10
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': nota,
            'ciclos': max_ciclos,
            'ferramentas': list(ferramentas_usadas),
            'tempo': round(_time.time() - t0, 1),
            'status': f'max_ciclos({nota})',
        }


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR AUTO-LOOP — Só entrega quando 10/10. Expande em loop.")
    print("=" * 70)
    
    mcr = MCRAutoLoop()
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "Crie um NPC ferreiro em Eridanus",
    ]
    
    resultados = []
    for pergunta in perguntas:
        r = mcr.processar(pergunta)
        resultados.append(r)
    
    # Relatório
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — MCR AUTO-LOOP")
    print(f"{'='*70}")
    
    for r in resultados:
        print(f"\n  Pergunta: {r['pergunta'][:40]}")
        print(f"  Status: {r['status']}")
        print(f"  Nota final: {r['nota']}/10")
        print(f"  Ciclos: {r['ciclos']}")
        print(f"  Ferramentas: {r['ferramentas']}")
        print(f"  Tempo: {r['tempo']}s")
        print(f"  Resposta: {r['resposta'][:100]}...")
    
    print(f"\n  {'='*70}")
    print(f"  Markovs treinados:")
    for mk in [mcr.mk_byte, mcr.mk_token, mcr.mk_intencao, mcr.mk_decisor, mcr.mk_acao]:
        s = mk.stats()
        if s['estados'] > 0:
            print(f"    {s['nome']:10s}: {s['estados']:3d} estados, {s['transicoes']:3d} transições")
    print(f"  {'='*70}")
    
    return resultados


if __name__ == '__main__':
    testar()
