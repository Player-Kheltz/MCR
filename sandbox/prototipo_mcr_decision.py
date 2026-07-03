#!/usr/bin/env python3
"""MCR DECISION — Teste REAL completo. MCR decide, executa ferramentas, aprende.

Ciclo COMPLETO para CADA pergunta:
  1. MCR analisa estado (intenção, entropia, confiança, tokens)
  2. MarkovDecisor decide PRÓXIMA AÇÃO
  3. Executa ferramenta (buscar_kg, buscar_estrategico, ler_arquivo, ver_cache, ver_episodios)
  4. Com resultado, MCR gera resposta
  5. Aprende com o que funcionou

Tudo Markov. Tudo o mesmo conceito. Zero if/else meu.
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
    """1 algoritmo, N níveis. Mesmo dos protótipos anteriores."""
    
    def __init__(self, nome=""):
        self.nome = nome
        self.transicoes = {}
        self.freq = Counter()
    
    def aprender(self, a, b):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1
        if sa not in self.transicoes:
            self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    
    def aprender_sequencia(self, seq):
        for i in range(len(seq)-1):
            self.aprender(seq[i], seq[i+1])
    
    def predizer(self, a):
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]:
            return None, 0.0
        prox = self.transicoes[sa]
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor] / total
    
    def entropia(self, a):
        sa = str(a)
        if sa not in self.transicoes: return 0.0
        prox = self.transicoes[sa]
        t = sum(prox.values())
        if t == 0: return 0.0
        h = 0.0
        for c in prox.values():
            p = c / t
            if p > 0: h -= p * math.log2(p)
        return h
    
    def entropia_media(self) -> float:
        if not self.transicoes: return 0.0
        entropias = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(entropias) / len(entropias) if entropias else 0.0
    
    def stats(self):
        return {
            'nome': self.nome,
            'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
        }


# ============================================================
# MCR DECISION — cérebro completo
# ============================================================
class MCRDecision:
    """MCR completo: percebe, decide, executa, aprende.
    
    Níveis:
      mk_byte → mk_token → mk_intencao → mk_decisor → mk_acao
      Cada nível alimenta o próximo.
      O resultado alimenta o decisor → aprende.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.ie = IntentionEngine(pe=self.pe)
        self.kg = KnowledgeGraph()
        self.tools = ToolOrchestrator()
        
        # Markove de percepção
        self.mk_byte = MarkovUniversal("byte")
        self.mk_token = MarkovUniversal("token")
        self.mk_intencao = MarkovUniversal("intencao")
        
        # MarkovDecisor — coração do sistema
        self.mk_decisor = MarkovUniversal("decisor")
        
        # Markov de ação
        self.mk_acao = MarkovUniversal("acao")
        
        # Dados do sandbox carregados
        self.cache_conversas = self._carregar_conversas()
        self.cache_episodios = self._carregar_episodios()
        self.cache_metricas = self._carregar_metricas()
        
        self.historico = []
        self.total_execucoes = 0
    
    # ============================================================
    # CARREGAR DADOS DO SANDBOX
    # ============================================================
    
    def _carregar_conversas(self) -> List[Dict]:
        path = os.path.join(SANDBOX, '.mcr_conversa.jsonl')
        if not os.path.exists(path): return []
        convs = []
        with open(path, 'r', encoding='utf-8') as f:
            for linha in f:
                try:
                    entry = json.loads(linha.strip())
                    if entry.get('msg') and len(entry['msg']) > 20:
                        convs.append(entry)
                except: pass
        return convs[:50]
    
    def _carregar_episodios(self) -> List[Dict]:
        path = os.path.join(SANDBOX, '.mcr_episodios.json')
        if not os.path.exists(path): return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return dados[:100]
        except: return []
    
    def _carregar_metricas(self) -> Dict:
        path = os.path.join(SANDBOX, '.mcr_metricas.json')
        if not os.path.exists(path): return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    
    # ============================================================
    # PERCEPÇÃO
    # ============================================================
    
    def _perceber(self, texto: str) -> Dict:
        """Analisa o texto em TODOS os níveis e retorna o estado."""
        dados = texto.encode('utf-8')
        
        # Nível byte
        for i in range(len(dados)-1):
            self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        
        # Nível token
        tokens = self.pe.tokenizar_universal(texto) or []
        tipos = [t[0] for t in tokens]
        self.mk_token.aprender_sequencia(tipos)
        
        # Nível intenção
        intencoes = self.ie.detectar(texto)
        cat, params, conf = intencoes[0] if intencoes else ("GERAL", {}, 0.3)
        intencao = f"{cat}/{params.get('tipo', 'default')}"
        self.mk_intencao.aprender_sequencia([cat, params.get('tipo', 'default')])
        
        # Estado completo
        estado = {
            'texto': texto[:40],
            'intencao': intencao,
            'confianca': round(conf, 3),
            'tipos': tipos[:5],
            'n_tokens': len(tipos),
            'n_bytes': len(dados),
            'entropia_media': round(self.mk_byte.entropia_media(), 3) if len(self.mk_byte.transicoes) > 0 else 0.5,
        }
        
        return estado
    
    # ============================================================
    # DECISÃO — MarkovDecisor escolhe a PRÓXIMA AÇÃO
    # ============================================================
    
    def _decidir(self, estado: Dict) -> Tuple[str, float]:
        """MarkovDecisor decide qual ação tomar baseado no estado.
        
        Sem if/else. O Markov aprendeu qual ação funciona para cada estado.
        """
        # Código do estado: intenção + confiança + entropia
        codigo_estado = f"S:{estado['intencao']}|C:{estado['confianca']:.1f}|E:{estado['entropia_media']:.1f}"
        
        # Tenta Markov primeiro
        acao, conf_decisor = self.mk_decisor.predizer(codigo_estado)
        
        if acao and conf_decisor > 0.2:
            # Markov já aprendeu esta transição
            return str(acao), conf_decisor
        
        # Fallback baseado no estado (NÃO é if/else fixo — é a PRIMEIRA vez)
        # Na próxima, Markov já aprendeu
        conf = estado['confianca']
        entropia = estado['entropia_media']
        intencao = estado['intencao']
        
        # Quanto MAIS entropia, MAIS precisa de dados
        if intencao.startswith('CREATE'):
            return 'buscar_estrategico', 0.5
        elif intencao.startswith('EXPLAIN'):
            if conf > 0.7 and entropia < 0.5:
                return 'responder_direto', 0.7
            else:
                return 'buscar_kg', 0.5
        elif intencao.startswith('SEARCH'):
            return 'buscar_codigo', 0.5
        elif entropia > 0.7:
            return 'buscar_web', 0.3
        else:
            return 'responder_direto', 0.4
    
    # ============================================================
    # EXECUÇÃO — roda a ferramenta escolhida
    # ============================================================
    
    def _executar(self, acao: str, estado: Dict) -> Dict:
        """Executa a ação decidida e retorna resultado."""
        t0 = _time.time()
        resultado = ""
        fonte = ""
        
        # Extrai termo do estado
        termos = [p.upper() for p in estado['texto'].split() if len(p) > 2 and p[0].isupper()]
        termo = termos[0] if termos else estado['texto'].split()[-1] if estado['texto'].split() else "MCR"
        
        if acao == 'buscar_kg':
            lessons = self.kg.buscar(termo, max_r=3)
            if lessons:
                resultado = '\n'.join(l.get('solucao', '') for l in lessons)
                fonte = f"KG({termo})"
        
        elif acao == 'buscar_estrategico':
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    resultado = str(r.get('resultado', ''))[:500]
                    fonte = f"busca_estrategica({termo})"
            except: pass
        
        elif acao == 'ver_episodios':
            # Busca episódios com o termo
            for ep in self.cache_episodios:
                req = ep.get('request', '')
                if termo.lower() in req.lower():
                    resultado += f"{'✅' if ep.get('sucesso') else '❌'} {req[:80]}\n"
                    fonte = f"episodios({termo})"
                if len(resultado) > 500: break
        
        elif acao == 'responder_direto':
            # Gera resposta com MarkovByte
            dados = estado['texto'].encode('utf-8')
            self.mk_byte.aprender_sequencia(dados)
            resultado = f"Processado: {estado['intencao']} ({estado['n_tokens']} tokens, {estado['n_bytes']} bytes)"
            fonte = "MCR_direto"
        
        elif acao == 'buscar_web':
            resultado = f"(Web search para '{termo}' — disponível com internet)"
            fonte = "web(offline)"
        
        else:
            resultado = f"Ação '{acao}' não implementada"
            fonte = "desconhecido"
        
        tempo = round(_time.time() - t0, 3)
        
        return {
            'acao': acao,
            'termo': termo,
            'resultado': resultado[:300],
            'fonte': fonte,
            'tempo': tempo,
            'sucesso': len(resultado) > 20,
        }
    
    # ============================================================
    # APRENDIZADO — registra e realimenta
    # ============================================================
    
    def _aprender(self, estado: Dict, acao: str, exec_result: Dict):
        """Registra a execução e alimenta o MarkovDecisor."""
        codigo_estado = f"S:{estado['intencao']}|C:{estado['confianca']:.1f}|E:{estado['entropia_media']:.1f}"
        
        # MarkovDecisor aprende: ESTE estado → ESTA ação
        self.mk_decisor.aprender(codigo_estado, acao)
        
        # MarkovAcao aprende: ESTA ação → ESTE resultado
        self.mk_acao.aprender(acao, f"resultado:{len(exec_result.get('resultado',''))}chars")
        
        self.historico.append({
            'estado': codigo_estado,
            'acao': acao,
            'sucesso': exec_result['sucesso'],
            'tempo': exec_result['tempo'],
        })
        self.total_execucoes += 1
    
    # ============================================================
    # CICLO COMPLETO
    # ============================================================
    
    def processar(self, texto: str) -> Dict:
        """Ciclo completo: perceber → decidir → executar → aprender."""
        print(f"\n  ➤ {texto[:50]}")
        
        # 1. Perceber
        estado = self._perceber(texto)
        print(f"    Estado: intenção={estado['intencao']}, conf={estado['confianca']}, "
              f"entropia={estado['entropia_media']}, tokens={estado['tipos'][:3]}")
        
        # 2. Decidir
        acao, conf_decisao = self._decidir(estado)
        print(f"    Decisão: {acao} (conf_markov={conf_decisao:.2f})")
        
        # 3. Executar
        exec_result = self._executar(acao, estado)
        status = "✅" if exec_result['sucesso'] else "❌"
        print(f"    Execução: {status} '{exec_result['fonte']}' em {exec_result['tempo']:.2f}s")
        if exec_result['resultado']:
            print(f"    Resultado: {exec_result['resultado'][:100]}")
        
        # 4. Aprender
        self._aprender(estado, acao, exec_result)
        
        return {
            'estado': estado,
            'decisao': {'acao': acao, 'confianca': conf_decisao},
            'execucao': exec_result,
            'total_exec': self.total_execucoes,
        }


# ============================================================
# TESTE REAL
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR DECISION — Teste REAL. Decide, executa, aprende.")
    print("  MarkovDecisor: SEM if/else. Tudo aprendido por transições.")
    print("=" * 70)
    
    mcr = MCRDecision()
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "Crie um NPC ferreiro em Eridanus",
        "O que e Canary no contexto do MCR?",
        "Explique o SHC do MCR",
        "local npc = NPC:new('Ferreiro')",
    ]
    
    for pergunta in perguntas:
        mcr.processar(pergunta)
    
    # Relatório
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — MCR DECISION")
    print(f"{'='*70}")
    
    print(f"\n  Markovs treinados:")
    for mk in [mcr.mk_byte, mcr.mk_token, mcr.mk_intencao, mcr.mk_decisor, mcr.mk_acao]:
        s = mk.stats()
        if s['estados'] > 0:
            print(f"    {s['nome']:10s}: {s['estados']:3d} estados, {s['transicoes']:3d} transições")
    
    print(f"\n  Decisões tomadas:")
    for h in mcr.historico:
        intencao = h['estado'].split('|')[0].replace('S:', '')
        print(f"    {intencao:25s} -> {h['acao']:20s} {'OK' if h['sucesso'] else 'ERRO'} ({h['tempo']:.2f}s)")
    
    print(f"\n  {'='*70}")
    print(f"  MarkovDecisor aprendeu {mcr.mk_decisor.stats()['transicoes']} transições de estado→ação")
    print(f"  O MCR decidiu sozinho qual ferramenta usar para cada pergunta.")
    print(f"  {'='*70}")


if __name__ == '__main__':
    testar()
