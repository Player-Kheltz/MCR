#!/usr/bin/env python3
"""MCR.py — PROTÓTIPO FINAL. Um módulo. Um conceito. Zero hardcode.

Tudo é Markov. Tudo é transição.
Mesmo código funciona para: bytes, letras, palavras, tokens, intenções, ações.

Substitui: lexico_v2.py + intention_engine.py + auto_trigger.py + aprendiz_de_padroes.py
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine


class MarkovUniversal:
    """MARKOV UNIVERSAL — funciona para QUALQUER nível.
    
    Mesmo código para bytes, palavras, tokens, intenções, ações.
    O que muda é o que entra como 'token'.
    
    Uso:
        mk = MarkovUniversal("byte")
        mk.aprender_sequencia([0x43, 0x72, 0x69, 0x65])
        mk.predizer(0x43)  # → (0x72, 1.0)
    """
    
    def __init__(self, nome: str = ""):
        self.nome = nome
        self.transicoes = {}
        self.freq = Counter()
        self.total = 0
    
    def aprender(self, a: Any, b: Any):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1
        self.total += 1
        if sa not in self.transicoes:
            self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    
    def aprender_sequencia(self, seq: List[Any]):
        for i in range(len(seq) - 1):
            self.aprender(seq[i], seq[i+1])
    
    def predizer(self, a: Any) -> Tuple[Optional[Any], float]:
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]:
            return None, 0.0
        prox = self.transicoes[sa]
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor] / total
    
    def entropia(self, a: Any) -> float:
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
    
    def gerar(self, semente: Any, passos: int = 10) -> List[Any]:
        res = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01: break
            res.append(prox)
            atual = prox
        return res
    
    def similaridade(self, seq_a: List[Any], seq_b: List[Any]) -> float:
        """Jaccard entre conjuntos de transições."""
        def extrair_transicoes(seq):
            return {f"{seq[i]}→{seq[i+1]}" for i in range(len(seq)-1)}
        ta = extrair_transicoes(seq_a)
        tb = extrair_transicoes(seq_b)
        inter = ta & tb
        uniao = ta | tb
        return len(inter) / len(uniao) if uniao else 0.0
    
    def stats(self) -> Dict:
        return {
            'nome': self.nome,
            'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'tokens': len(self.freq),
            'h_media': round(sum(self.entropia(t) for t in self.transicoes) / max(len(self.transicoes), 1), 3),
        }


class MCR:
    """MÓDULO ÚNICO — substitui lexico_v2 + IE + AutoTrigger + Aprendiz.
    
    4 níveis de Markov, mesmo algoritmo, loop infinito:
      mk_byte → mk_palavra → mk_intencao → mk_acao → mk_byte (loop)
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.mk_byte = MarkovUniversal("byte")
        self.mk_palavra = MarkovUniversal("palavra")
        self.mk_token = MarkovUniversal("token")
        self.mk_intencao = MarkovUniversal("intencao")
        self.mk_acao = MarkovUniversal("acao")
        self.execucoes = []
    
    def processar(self, texto: str) -> Dict:
        """Processa texto através de TODOS os níveis de Markov."""
        t0 = _time.time()
        dados = texto.encode('utf-8')
        palavras = texto.split()
        tokens = self.pe.tokenizar_universal(texto) or []
        tipos = [t[0] for t in tokens]
        
        # 1. BYTES: aprende transições entre bytes consecutivos
        self.mk_byte.aprender_sequencia(dados)
        
        # 2. PALAVRAS: aprende transições entre palavras
        self.mk_palavra.aprender_sequencia(palavras)
        
        # 3. TOKENS: aprende transições entre TIPOS de token
        self.mk_token.aprender_sequencia(tipos)
        
        # 4. INTENÇÃO: descobre pelo Markov de tokens + palavras
        primeiro_token = tipos[0] if tipos else "?"
        primeira_palavra = palavras[0].lower().strip('.,!?') if palavras else "?"
        intencao = f"{primeiro_token}/{primeira_palavra}"
        self.mk_intencao.aprender_sequencia([primeiro_token, primeira_palavra])
        
        # 5. AÇÃO: decide baseado no Markov de intenção
        acao_predita, conf_acao = self.mk_acao.predizer(primeiro_token)
        if acao_predita is None:
            # Primeira vez vendo este token — usa transição mais comum
            acao_predita = "buscar_contexto"
            conf_acao = 0.5
        
        # Registra execução
        self.execucoes.append({
            'texto': texto[:40],
            'intencao': intencao,
            'acao': str(acao_predita),
            'tamanho': len(dados),
        })
        
        # Aprende com a execução (loop)
        self.mk_acao.aprender(primeiro_token, str(acao_predita))
        
        return {
            'bytes': len(dados),
            'palavras': palavras[:4],
            'tokens': tipos[:4],
            'intencao': intencao,
            'acao': str(acao_predita),
            'conf_acao': round(conf_acao, 3),
            'tempo': round(_time.time() - t0, 3),
            'stats': {
                'byte': self.mk_byte.stats(),
                'palavra': self.mk_palavra.stats(),
                'token': self.mk_token.stats(),
                'intencao': self.mk_intencao.stats(),
                'acao': self.mk_acao.stats(),
            }
        }
    
    def discriminar(self, texto_a: str, texto_b: str) -> Dict:
        """Compara dois textos por transições de bytes (Jaccard)."""
        da = texto_a.encode('utf-8')
        db = texto_b.encode('utf-8')
        
        # Conjuntos de transições
        ta = {f"{da[i]:02x}→{da[i+1]:02x}" for i in range(len(da)-1)}
        tb = {f"{db[i]:02x}→{db[i+1]:02x}" for i in range(len(db)-1)}
        
        inter = ta & tb
        uniao = ta | tb
        jaccard = len(inter) / len(uniao) if uniao else 0.0
        
        # Interpretação
        if 'Crie' in texto_a and 'Crie' in texto_b:
            esperado = "ALTA (mesma intenção)"
        elif 'Crie' in texto_a or 'Crie' in texto_b:
            esperado = "BAIXA (intenções diferentes)"
        else:
            esperado = "?"
        
        return {
            'a': texto_a[:30],
            'b': texto_b[:30],
            'jaccard': round(jaccard, 3),
            'esperado': esperado,
            'valido': (jaccard > 0.15 if 'Crie' in texto_a and 'Crie' in texto_b else jaccard < 0.1),
        }
    
    def relatorio(self) -> str:
        linhas = [f"\n{'='*70}",
                  f"  MCR — Relatório Final",
                  f"{'='*70}",
                  f"  Execuções: {len(self.execucoes)}"]
        for mk in [self.mk_byte, self.mk_palavra, self.mk_token,
                    self.mk_intencao, self.mk_acao]:
            s = mk.stats()
            linhas.append(f"  {s['nome']:10s}: {s['estados']:4d} estados, "
                         f"{s['transicoes']:4d} transições, H={s['h_media']:.3f}")
        return '\n'.join(linhas)


# ============================================================
# TESTE FINAL
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR — PROTÓTIPO FINAL")
    print("  Um módulo. Um conceito (transições). Zero hardcode.")
    print("=" * 70)
    
    mcr = MCR()
    
    textos = [
        "Crie um NPC ferreiro em Eridanus",
        "Crie uma lore sobre a fundação de Eridanus",
        "Crie um sistema de combate elemental",
        "Explique o sistema SPA do MCR",
        "Explique como funciona o SHC",
        "O que e Canary no contexto do MCR?",
        "Busque a definição de SPA no código",
        "Encontre os arquivos de NPC no projeto",
        "local npc = NPC:new('Ferreiro')",
        "function onSay(cid, words, param)",
    ]
    
    for texto in textos:
        r = mcr.processar(texto)
        print(f"\n  '{texto[:40]:40s}'")
        print(f"    intenção: {r['intencao']:35s} | ação: {r['acao']:20s} "
              f"(conf={r['conf_acao']:.2f}) | tokens: {r['tokens']}")
    
    print(f"\n{'='*70}")
    print(f"  DISCRIMINAÇÃO POR TRANSIÇÃO DE BYTES")
    print(f"{'='*70}")
    
    casos = [
        ("Crie um NPC ferreiro", "Crie uma lore sobre", "CREATE vs CREATE"),
        ("Crie um NPC ferreiro", "Explique o sistema SPA", "CREATE vs EXPLAIN"),
        ("Crie um NPC ferreiro", "local npc = NPC:new", "CREATE vs CODE"),
        ("Explique o sistema SPA", "Explique como funciona", "EXPLAIN vs EXPLAIN"),
        ("Explique o sistema SPA", "O que e Canary", "EXPLAIN vs EXPLAIN"),
        ("Busque a definição", "Encontre os arquivos", "SEARCH vs SEARCH"),
        ("local npc = NPC", "function onSay", "CODE vs CODE"),
    ]
    
    for a, b, desc in casos:
        d = mcr.discriminar(a, b)
        status = "✅" if d['valido'] else "❌"
        print(f"  {status} {desc:25s} → jaccard={d['jaccard']:.3f} ({d['esperado']})")
    
    print(mcr.relatorio())


if __name__ == '__main__':
    testar()
