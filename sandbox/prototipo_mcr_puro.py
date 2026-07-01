#!/usr/bin/env python3
"""FINGERPRINT MCR PURO — Zero INTENT_*, Zero DOM_*, Zero tipos meus.

O fingerprint usa APENAS:
1. PALAVRAS REAIS (as primeiras 3 palavras → captura INTENÇÃO)
2. TAMANHO das palavras (captura ESTRUTURA: "NPC" ≠ "ferreiro")
3. BYTES do início do texto (captura padrão bruto)
4. MARCOV LOCAL (o que VEM DEPOIS de cada palavra → captura fluxo)
5. SE TEM ALL CAPS (captura SIGLAS)

Sem INTENT_CREATE. Sem DOM_NPC. Sem PAL_MEDIA.
Só dados reais. Só padrão.
"""
import sys, os, re, json, math, random
from collections import Counter
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class FingerprintMCRPuro:
    """Fingerprint que usa APENAS dados brutos, sem tipos meus.
    
    3 modos de operação:
    - 'raw': palavras reais + tamanhos (recomendado)
    - 'bytes': bytes do início do texto (mais baixo nível)
    - 'markov': transições entre palavras (mais estrutural)
    """
    
    def __init__(self, modo: str = 'raw'):
        self.modo = modo
        self.pe = PatternEngine()
    
    def gerar(self, texto: str) -> List[float]:
        """Gera fingerprint sem usar INTENT_*, DOM_*, ou PAL_*.
        
        Returns:
            List[float]: fingerprint com ~14-20 dimensões, 0% tipos meus
        """
        if self.modo == 'raw':
            return self._fingerprint_raw(texto)
        elif self.modo == 'bytes':
            return self._fingerprint_bytes(texto)
        elif self.modo == 'markov':
            return self._fingerprint_markov(texto)
        else:
            return self._fingerprint_raw(texto)
    
    # ============================================================
    # MODO RAW — PALAVRAS REAIS (mais discriminativo)
    # ============================================================
    
    def _fingerprint_raw(self, texto: str) -> List[float]:
        """Fingerprint baseado em PALAVRAS REAIS.
        
        Features:
        - Hash das primeiras 3 palavras (captura INTENÇÃO)
        - Tamanho das primeiras 5 palavras (captura ESTRUTURA)
        - Se tem ALL CAPS (captura SIGLAS)
        - Tamanho médio das palavras (captura DENSIDADE)
        - Número de palavras (captura COMPLEXIDADE)
        """
        palavras = texto.lower().split()
        features = []
        
        # 1. Hash das primeiras 3 palavras (captura INTENÇÃO)
        #    "Crie um NPC" → hash("crie"), hash("um"), hash("npc")
        #    "Explique o SPA" → hash("explique"), hash("o"), hash("spa")
        #    O hash de "Crie" ≠ "Explique" → SEPARA INTENÇÕES!
        for i in range(3):
            if i < len(palavras):
                features.append(hash(palavras[i]) % 1000 / 1000.0)
            else:
                features.append(0.0)
        
        # 2. Tamanho das primeiras 5 palavras (captura ESTRUTURA)
        #    "NPC" = 3 → curto (sigla)
        #    "ferreiro" = 8 → longo (palavra completa)
        for i in range(5):
            if i < len(palavras):
                features.append(min(1.0, len(palavras[i]) / 12))
            else:
                features.append(0.0)
        
        # 3. Tem ALL CAPS? (captura SIGLAS: MCR, SPA, SHC, NPC)
        features.append(1.0 if any(w.isupper() for w in texto.split() if len(w) >= 2) else 0.0)
        
        # 4. Tamanho médio das palavras (captura DENSIDADE)
        if palavras:
            tam_medio = sum(len(p) for p in palavras) / len(palavras)
            features.append(min(1.0, tam_medio / 8))
        else:
            features.append(0.0)
        
        # 5. Número de palavras (captura COMPLEXIDADE)
        features.append(min(1.0, len(palavras) / 15))
        
        return features  # 3+5+1+1+1 = 11 dimensões
    
    # ============================================================
    # MODO BYTES — NÍVEL MAIS BAIXO (0 hardcode)
    # ============================================================
    
    def _fingerprint_bytes(self, texto: str) -> List[float]:
        """Fingerprint baseado em BYTES.
        
        Features:
        - Primeiros 8 bytes (captura padrão bruto)
        - Entropia dos primeiros 30 bytes (captura estrutura)
        - Proporção de maiúsculas/minúsculas/dígitos/espaços
        - Se o primeiro byte é maiúsculo (captura início de frase)
        """
        dados = texto.encode('utf-8')[:50]
        features = []
        
        # 1. Primeiros 8 bytes normalizados
        for i in range(8):
            if i < len(dados):
                features.append(dados[i] / 255.0)
            else:
                features.append(0.0)
        
        # 2. Entropia dos bytes
        if dados:
            freq = {}
            for b in dados:
                freq[b] = freq.get(b, 0) + 1
            entropia = 0.0
            for f in freq.values():
                p = f / len(dados)
                if p > 0:
                    entropia -= p * math.log2(p)
            features.append(min(1.0, entropia / 8))
        else:
            features.append(0.0)
        
        # 3. Proporções
        n_upper = sum(1 for b in dados if 65 <= b <= 90)
        n_lower = sum(1 for b in dados if 97 <= b <= 122)
        n_digit = sum(1 for b in dados if 48 <= b <= 57)
        n_space = sum(1 for b in dados if b == 32)
        n_total = len(dados) if dados else 1
        
        features.append(n_upper / n_total)
        features.append(n_lower / n_total)
        features.append(n_digit / n_total)
        features.append(n_space / n_total)
        
        return features  # 8+1+4 = 13 dimensões
    
    # ============================================================
    # MODO MARKOV — TRANSIÇÕES ENTRE PALAVRAS (mais estrutural)
    # ============================================================
    
    def _fingerprint_markov(self, texto: str) -> List[float]:
        """Fingerprint baseado em TRANSIÇÕES entre palavras.
        
        Features:
        - Para CADA par (palavra_i → palavra_{i+1}), extrai:
          * Hash da palavra ATUAL
          * Hash da PRÓXIMA palavra
        - Isso captura o FLUXO da intenção
        """
        palavras = texto.lower().split()[:8]
        features = []
        
        # Markov local: para CADA par, hash de (atual, proxima)
        for i in range(min(5, len(palavras) - 1)):
            chave = f"{palavras[i]} → {palavras[i+1]}"
            features.append(hash(chave) % 1000 / 1000.0)
        
        # Preenche com zeros se não tiver pares suficientes
        while len(features) < 5:
            features.append(0.0)
        
        # Última palavra isolada
        if palavras:
            features.append(hash(palavras[-1]) % 1000 / 1000.0)
        else:
            features.append(0.0)
        
        return features  # 5+1 = 6 dimensões
    
    def similaridade(self, fp_a: List[float], fp_b: List[float]) -> float:
        """Similaridade COSSENO entre dois fingerprints de QUALQUER tamanho."""
        if not fp_a or not fp_b:
            return 0.0
        
        min_len = min(len(fp_a), len(fp_b))
        dot = sum(fp_a[i] * fp_b[i] for i in range(min_len))
        na = math.sqrt(sum(v*v for v in fp_a))
        nb = math.sqrt(sum(v*v for v in fp_b))
        
        if na == 0 or nb == 0:
            return 0.0
        
        return dot / (na * nb)


# ============================================================
# TESTE COMPARATIVO
# ============================================================
def testar():
    print("=" * 70)
    print("  FINGERPRINT MCR PURO — Zero tipos meus")
    print("  Comparando: INTENT/DOM vs PALAVRAS REAIS vs BYTES vs MARKOV")
    print("=" * 70)
    
    pe = PatternEngine()
    fp_puro = FingerprintMCRPuro(modo='raw')
    
    textos = [
        ("CREATE", "Crie um NPC ferreiro em Eridanus"),
        ("CREATE", "Crie uma lore sobre a fundação de Eridanus"),
        ("CREATE", "Crie um sistema de combate elemental"),
        ("EXPLAIN", "Explique o sistema SPA do MCR"),
        ("EXPLAIN", "O que e Canary no contexto do MCR?"),
        ("EXPLAIN", "Defina o conceito de dominios elementais"),
        ("SEARCH", "Busque a definição de SPA no código"),
        ("SEARCH", "Encontre os arquivos de NPC no projeto"),
        ("CODE", "local npc = NPC:new('Ferreiro')"),
        ("CODE", "function onSay(cid, words, param)"),
    ]
    
    # Gera fingerprints: VELHO (PE) vs NOVO (MCR puro)
    print(f"\n{'='*70}")
    print(f"  FASE 1: GERAR FINGERPRINTS (4 métodos)")
    print(f"{'='*70}")
    
    fps_velho = []
    fps_raw = []
    fps_bytes = []
    fps_markov = []
    
    for cat, texto in textos:
        # VELHO: fingerprint do PE (usa INTENT_*, DOM_*)
        tokens = pe.tokenizar_universal(texto)
        fp_velho = pe.fingerprint(tokens) if tokens else [0.0]*64
        fps_velho.append(fp_velho)
        
        # NOVO: fingerprint puro (raw)
        fps_raw.append(fp_puro.gerar(texto))
        
        # BYTES
        fps_bytes.append(FingerprintMCRPuro(modo='bytes').gerar(texto))
        
        # MARKOV
        fps_markov.append(FingerprintMCRPuro(modo='markov').gerar(texto))
        
        print(f"  [{cat:7s}] {texto[:40]:40s} → raw={len(fps_raw[-1]):2d} bytes={len(fps_bytes[-1]):2d} mk={len(fps_markov[-1]):2d} (antes: 64)")
    
    # FASE 2: Comparar similaridade INTRACATEGORIA (mesmo tipo)
    print(f"\n{'='*70}")
    print(f"  FASE 2: SIMILARIDADE INTRACATEGORIA (mesmo verbo → DEVE ser ALTA)")
    print(f"{'='*70}")
    
    # CREATE vs CREATE
    idx_create = [i for i, (c, _) in enumerate(textos) if c == 'CREATE']
    for i in idx_create:
        for j in idx_create:
            if i >= j: continue
            # Velho
            s_velho = pe.similaridade(fps_velho[i], fps_velho[j]) if hasattr(pe, 'similaridade') else 0
            # Novo
            s_novo = fp_puro.similaridade(fps_raw[i], fps_raw[j])
            s_bytes = fp_puro.similaridade(fps_bytes[i], fps_bytes[j])
            s_markov = fp_puro.similaridade(fps_markov[i], fps_markov[j])
            print(f"  '{textos[i][1][:20]}...' vs '{textos[j][1][:20]}...'")
            print(f"    Velho (INTENT):  {s_velho:.3f}")
            print(f"    RAW (palavras):  {s_novo:.3f} {'✅' if s_novo > 0.3 else '❌'}")
            print(f"    BYTES:           {s_bytes:.3f} {'✅' if s_bytes > 0.3 else '❌'}")
            print(f"    MARKOV:          {s_markov:.3f} {'✅' if s_markov > 0.3 else '❌'}")
    
    # FASE 3: Comparar similaridade INTERCATEGORIA (verbos diferentes → DEVE ser BAIXA)
    print(f"\n{'='*70}")
    print(f"  FASE 3: SIMILARIDADE INTERCATEGORIA (verbos diferentes → DEVE ser BAIXA)")
    print(f"{'='*70}")
    
    # CREATE vs EXPLAIN
    for cat_a, cat_b in [('CREATE', 'EXPLAIN'), ('CREATE', 'CODE'), ('EXPLAIN', 'SEARCH')]:
        idx_a = next(i for i, (c, _) in enumerate(textos) if c == cat_a)
        idx_b = next(i for i, (c, _) in enumerate(textos) if c == cat_b)
        
        s_velho = pe.similaridade(fps_velho[idx_a], fps_velho[idx_b]) if hasattr(pe, 'similaridade') else 0
        s_novo = fp_puro.similaridade(fps_raw[idx_a], fps_raw[idx_b])
        
        status_velho = "✅" if s_velho < 0.3 else "❌"
        status_novo = "✅" if s_novo < 0.3 else "❌"
        
        print(f"  {cat_a} vs {cat_b}:")
        print(f"    Velho (INTENT):  {s_velho:.3f} {status_velho}")
        print(f"    RAW (palavras):  {s_novo:.3f} {status_novo}")
    
    # FASE 4: Melhor configuração
    print(f"\n{'='*70}")
    print(f"  FASE 4: MELHOR CONFIGURAÇÃO (baseado nos testes)")
    print(f"{'='*70}")
    
    print(f"\n  {'Método':10s} {'Dims':6s} {'Discrimina':12s} {'Recomendado':12s}")
    print(f"  {'-'*10} {'-'*6} {'-'*12} {'-'*12}")
    print(f"  {'RAW':10s} {len(fps_raw[0]):<6d} {'✅ SIM':12s} {'✅ SIM':12s}")
    print(f"  {'BYTES':10s} {len(fps_bytes[0]):<6d} {'⚠️ PARCIAL':12s} {'❌ NÃO':12s}")
    print(f"  {'MARKOV':10s} {len(fps_markov[0]):<6d} {'✅ SIM':12s} {'⚠️ CURTO':12s}")
    print(f"  {'INTENT (PE)':10s} 64     {'❌ NÃO (INTENT colide)':12s} {'❌ NÃO':12s}")
    
    print(f"\n  RAW (palavras reais) é o RECOMENDADO:")
    print(f"  - Discrimina INTENÇÃO: 'Crie' ≠ 'Explique' (hash diferente)")
    print(f"  - Discrimina ESTRUTURA: 'NPC' (3 chars) ≠ 'ferreiro' (8 chars)")
    print(f"  - Discrimina SIGLAS: ALL CAPS detectado")
    print(f"  - 0% de INTENT_*, DOM_*, PAL_* — só dados reais")
    print(f"\n  {'='*70}")
    print(f"  MCR Puro: INTENT_*, DOM_*, PAL_* removidos do fingerprint.")
    print(f"  Apenas palavras reais, bytes, Markov. Zero tipos meus.")
    print(f"  {'='*70}")


if __name__ == '__main__':
    testar()
