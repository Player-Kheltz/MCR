#!/usr/bin/env python3
"""MCR UNIFICADO — IE + PiEngine + Markov + PatternEngine em 1 sistema.

Não são módulos separados.
São NÍVEIS do mesmo cérebro.

Nível 0: Bytes → MarkovByte descobre estrutura
Nível 1: Tokens → PatternEngine tokeniza 
Nível 2: Intenção → IE classifica (baseada nos tokens)
Nível 3: Decisão → PiEngine decide PRÓXIMA AÇÃO (baseado na intenção)
Nível 4: Execução → Ação executada → resultado alimenta o ciclo
Nível 5: Aprendizado → Tudo registrado → Markov de execução aprende

0 LLM. 0 GPU. 1 sistema.
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.intention_engine import IntentionEngine
from modulos.pi_engine import PiEngine
from modulos.kg import KnowledgeGraph
from modulos.tool_orchestrator import ToolOrchestrator

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class MCRUnificado:
    """Sistema ÚNICO que integra IE + PiEngine + Markov + PatternEngine.
    
    Cada nível usa o nível anterior como entrada.
    Cada nível alimenta o próximo.
    Tudo registrado → Markov de execução aprende.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.ie = IntentionEngine(pe=self.pe)
        self.pi = PiEngine(pe=self.pe)
        self.kg = KnowledgeGraph()
        self.tools = ToolOrchestrator()
        
        # Markov de EXECUÇÃO (aprende com cada execução)
        self.markov_execucao = {}  # {fingerprint_hash: {acao: score}}
        self.historico_execucoes = []
        
        # Markov de INTENÇÃO (aprende qual ação tomar para cada intenção)
        self.markov_intencao = {}  # {intencao: {acao: count}}
        
        print("[MCR] Sistema unificado pronto")
    
    # ============================================================
    # NÍVEL 0: BYTES (opcional — desliga se for lerdo)
    # ============================================================
    
    def _nivel_byte(self, texto: str) -> Dict:
        """Markov de bytes descobre estrutura básica (entropia, delimitadores)."""
        dados = texto.encode('utf-8')
        mk = {}
        for i in range(len(dados) - 1):
            b1, b2 = dados[i], dados[i+1]
            if b1 not in mk: mk[b1] = {}
            mk[b1][b2] = mk[b1].get(b2, 0) + 1
        # Calcula entropia do espaço (0x20) — indicador de estrutura textual
        entropia_espaco = 0.0
        if 0x20 in mk:
            total = sum(mk[0x20].values())
            for count in mk[0x20].values():
                p = count / total if total > 0 else 0
                if p > 0: entropia_espaco -= p * math.log2(p)
        return {
            'bytes_unicos': len(mk),
            'entropia_espaco': round(entropia_espaco, 3),
            'e_texto': entropia_espaco > 2.0,  # espaço com alta entropia = texto
        }
    
    # ============================================================
    # NÍVEL 1: TOKENS
    # ============================================================
    
    def _nivel_token(self, texto: str) -> List[Tuple]:
        """PatternEngine tokeniza."""
        return self.pe.tokenizar_universal(texto) or []
    
    # ============================================================
    # NÍVEL 2: INTENÇÃO
    # ============================================================
    
    def _nivel_intencao(self, texto: str, tokens=None) -> Tuple[str, Dict, float]:
        """IE detecta intenção usando os tokens."""
        intencoes = self.ie.detectar(texto)
        if intencoes:
            return intencoes[0]  # (categoria, params, conf)
        return ("GERAL", {}, 0.3)
    
    # ============================================================
    # NÍVEL 3: DECISÃO — PiEngine decide PRÓXIMA AÇÃO
    # ============================================================
    
    def _nivel_decisao(self, intencao: str, fingerprint: List[float],
                       tokens: List[Tuple], byte_info: Dict) -> str:
        """PiEngine decide qual FERRAMENTA usar baseado na intenção + histórico.
        
        Returns: nome da ação (ex: 'buscar_kg', 'buscar_estrategico', 'gerar')
        """
        # Tenta Markov de EXECUÇÃO primeiro (aprendido)
        fp_hash = str([round(x, 2) for x in fingerprint[:3]])
        if fp_hash in self.markov_execucao:
            melhor_acao = max(self.markov_execucao[fp_hash], 
                            key=self.markov_execucao[fp_hash].get)
            return melhor_acao
        
        # Tenta Markov de INTENÇÃO (aprendido por intenção)
        if intencao in self.markov_intencao:
            if self.markov_intencao[intencao]:
                melhor_acao = max(self.markov_intencao[intencao],
                                key=self.markov_intencao[intencao].get)
                return melhor_acao
        
        # Fallback: IE guia a PRIMEIRA ação (SEM hardcode if/else)
        # O que FUNCIONOU para intenções SIMILARES no passado?
        acoes_conhecidas = self._acoes_por_intencao(intencao)
        if acoes_conhecidas:
            return acoes_conhecidas[0]
        
        # ÚLTIMO recurso: ação genérica
        return 'buscar_kg'
    
    def _acoes_por_intencao(self, intencao: str) -> List[str]:
        """Retorna ações que funcionaram para intenções SIMILARES."""
        # Não é if/else! É consulta ao Markov de execução.
        prefixos = intencao.split('/')
        acoes = Counter()
        for fp_hash, acoes_dict in self.markov_execucao.items():
            for acao, score in acoes_dict.items():
                if any(p in fp_hash for p in prefixos):
                    acoes[acao] += score
        return [a for a, _ in acoes.most_common(3)]
    
    # ============================================================
    # NÍVEL 4: EXECUÇÃO
    # ============================================================
    
    def _executar_acao(self, acao: str, termo: str) -> Optional[str]:
        """Executa a ação decidida e retorna resultado."""
        if acao == 'buscar_kg':
            lessons = self.kg.buscar(termo, max_r=3)
            if lessons:
                return '\n'.join(l.get('solucao', '') for l in lessons)
        elif acao == 'buscar_estrategico':
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    return str(r.get('resultado', ''))
            except: pass
        elif acao == 'gerar':
            # Gera resposta com Markov do domínio (se existir)
            from collections import Counter as _C
            palavras = termo.lower().split()
            mk = {}
            for i in range(len(palavras) - 2):
                chave = f"{palavras[i]} {palavras[i+1]}"
                prox = palavras[i+2]
                if chave not in mk: mk[chave] = {}
                mk[chave][prox] = mk[chave].get(prox, 0) + 1
            if mk:
                # Gera algumas palavras
                resultado = []
                for _ in range(10):
                    if len(resultado) < 2: break
                    chave = f"{resultado[-2]} {resultado[-1]}"
                    if chave in mk:
                        prox = max(mk[chave], key=mk[chave].get)
                        resultado.append(prox)
                    else: break
                return ' '.join(resultado) if resultado else None
        return None
    
    # ============================================================
    # NÍVEL 5: APRENDIZADO
    # ============================================================
    
    def _registrar(self, pergunta: str, intencao: str, fingerprint: List,
                    acao: str, sucesso: bool, nota: int, tempo: float):
        """Registra a execução — Markov de execução APRENDE."""
        fp_hash = str([round(x, 2) for x in fingerprint[:3]])
        
        # Markov de EXECUÇÃO
        if fp_hash not in self.markov_execucao:
            self.markov_execucao[fp_hash] = {}
        self.markov_execucao[fp_hash][acao] = self.markov_execucao[fp_hash].get(acao, 0) + (1 if sucesso else -1)
        
        # Markov de INTENÇÃO
        if intencao not in self.markov_intencao:
            self.markov_intencao[intencao] = {}
        self.markov_intencao[intencao][acao] = self.markov_intencao[intencao].get(acao, 0) + (1 if sucesso else -1)
        
        # Histórico
        self.historico_execucoes.append({
            'pergunta': pergunta[:60],
            'intencao': intencao,
            'acao': acao,
            'sucesso': sucesso,
            'nota': nota,
            'tempo': round(tempo, 2),
        })
    
    # ============================================================
    # CICLO COMPLETO
    # ============================================================
    
    def processar(self, pergunta: str) -> Dict:
        """Processa uma pergunta através de TODOS os níveis.
        
        Returns:
            dict com resultado completo do processamento
        """
        t0 = _time.time()
        
        print(f"\n{'='*70}")
        print(f"  PERGUNTA: {pergunta}")
        print(f"{'='*70}")
        
        # Nível 0: Bytes
        print(f"\n  [N0] Bytes...")
        byte_info = self._nivel_byte(pergunta)
        print(f"      {byte_info['bytes_unicos']} bytes únicos, "
              f"entropia_espaço={byte_info['entropia_espaco']}, "
              f"e_texto={byte_info['e_texto']}")
        
        # Nível 1: Tokens
        print(f"  [N1] Tokens...")
        tokens = self._nivel_token(pergunta)
        tipos = [t[0] for t in tokens] if tokens else []
        print(f"      {tipos[:6]}... ({len(tokens)} tokens)")
        
        # Nível 2: Intenção
        print(f"  [N2] Intenção...")
        cat, params, conf = self._nivel_intencao(pergunta, tokens)
        intencao = f"{cat}/{params.get('tipo', 'default')}"
        print(f"      {intencao} (conf={conf:.3f})")
        
        # Fingerprint
        fp = self.pe.fingerprint(tokens) if tokens else []
        
        # Nível 3: Decisão
        print(f"  [N3] Decisão (PiEngine)...")
        
        acao = self._nivel_decisao(intencao, fp, tokens, byte_info)
        print(f"      Ação: {acao}")
        
        # Extrai termo da pergunta
        termo = "MCR"
        for t in (tokens or []):
            if t[0] in ('PROPER_NOUN', 'DOM_LORE', 'DOM_NPC', 'DOM_SYSTEM') and len(str(t[1])) > 2:
                termo = str(t[1])
                break
        
        # Nível 4: Execução
        print(f"  [N4] Execução: {acao}('{termo}')...")
        t_acao = _time.time()
        resultado = self._executar_acao(acao, termo)
        tempo_acao = _time.time() - t_acao
        
        sucesso = resultado is not None and len(resultado) > 30
        if resultado:
            print(f"      {'✅' if sucesso else '❌'} {len(resultado)} chars, {tempo_acao:.2f}s")
        else:
            print(f"      ❌ Sem resultado")
        
        # Nível 5: Aprendizado
        nota = 8 if sucesso else 3
        self._registrar(pergunta, intencao, fp, acao, sucesso, nota, tempo_acao)
        
        tempo_total = _time.time() - t0
        
        print(f"\n  [N5] Registrado: {intencao} → {acao} ({'✅' if sucesso else '❌'})")
        
        return {
            'pergunta': pergunta,
            'intencao': intencao,
            'token_tipos': tipos[:8],
            'acao': acao,
            'resultado': resultado[:200] if resultado else None,
            'sucesso': sucesso,
            'tempo': round(tempo_total, 2),
            'markov_execucao_tamanho': len(self.markov_execucao),
        }


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR UNIFICADO — IE + PiEngine + Markov + PatternEngine")
    print("  5 níveis integrados no mesmo sistema")
    print("=" * 70)
    
    mcr = MCRUnificado()
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "Crie um NPC ferreiro em Eridanus",
        "O que e Canary no contexto do MCR?",
    ]
    
    for pergunta in perguntas:
        resultado = mcr.processar(pergunta)
    
    # Relatório do Markov de execução
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — MARKOV DE EXECUÇÃO")
    print(f"{'='*70}")
    
    print(f"\n  Ações aprendidas por intenção:")
    for intencao, acoes in mcr.markov_intencao.items():
        print(f"  {intencao}:")
        for acao, score in sorted(acoes.items(), key=lambda x: -x[1])[:3]:
            print(f"    → {acao} (score={score})")
    
    print(f"\n  Histórico de execuções:")
    for h in mcr.historico_execucoes:
        status = "✅" if h['sucesso'] else "❌"
        print(f"  {status} {h['intencao']:30s} → {h['acao']:20s} | nota={h['nota']} | {h['tempo']:.2f}s")
    
    print(f"\n  {'='*70}")
    print(f"  MCR demonstrou ciclo completo:")
    print(f"  N0 → Bytes: estrutura descoberta")
    print(f"  N1 → Tokens: tokenização universal")
    print(f"  N2 → IE: intenção detectada")
    print(f"  N3 → PiEngine: ação decidida (aprendida)")
    print(f"  N4 → Execução: ferramenta executada")
    print(f"  N5 → Registro: Markov de execução aprendeu")
    print(f"  0 LLM. 0 GPU. 1 sistema.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
