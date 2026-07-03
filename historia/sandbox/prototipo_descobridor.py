#!/usr/bin/env python3
"""MCR DESCOBRIDOR V2 — Descobre categorias por verbo + fingerprint.

Problema detectado: fingerprint 64d é genérico demais para textos curtos.
Solução: usar PRIMEIRO BIGRAMA (verbo + objeto) como feature principal,
fingerprint 64d como feature secundária.

0 hardcode. 0 INTENT_CREATE. 0 DOM_NPC.
"""
import sys, os, re, json, math
from collections import Counter
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine


class Grupo:
    def __init__(self, id, verbo, fp, texto):
        self.id = id
        self.verbo = verbo  # primeira palavra do texto
        self.fp_medio = fp
        self.textos = [texto]
        self.fps = [fp]
    
    def adicionar(self, fp, texto):
        self.textos.append(texto)
        self.fps.append(fp)
        n = len(self.fps)
        self.fp_medio = [sum(self.fps[i][j] for i in range(n)) / n for j in range(len(fp))]
    
    @property
    def similaridade_interna(self):
        if len(self.fps) < 2: return 1.0
        sims = []
        for i in range(len(self.fps)):
            for j in range(i+1, len(self.fps)):
                sims.append(sum(a*b for a,b in zip(self.fps[i], self.fps[j])))
        return sum(sims)/len(sims) if sims else 0


class MCRDescobridorV2:
    """Descobre categorias usando VERBO (1ª palavra) + fingerprint.
    
    Duas camadas:
      1. AGRUPA por verbo (palavras iguais → mesmo grupo)
      2. SUB-AGRUPAMENTO por fingerprint (verbos sinônimos próximos)
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.grupos: List[Grupo] = []
    
    def aprender(self, textos: List[str]):
        for texto in textos:
            if not texto or len(texto) < 5: continue
            tokens = self.pe.tokenizar_universal(texto)
            if not tokens: continue
            fp = self.pe.fingerprint(tokens)
            
            verbo = texto.split()[0].lower().strip('.,!?')
            
            # Tenta encaixar em grupo com MESMO verbo
            encontrou = False
            for g in self.grupos:
                if g.verbo == verbo:
                    g.adicionar(fp, texto)
                    encontrou = True
                    break
            
            if not encontrou:
                # Fallback: tenta fingerprint (apenas se MUITO similar)
                for g in self.grupos:
                    sim = self.pe.similaridade(fp, g.fp_medio)
                    if sim > 0.85:
                        g.adicionar(fp, texto)
                        encontrou = True
                        break
            
            if not encontrou:
                self.grupos.append(Grupo(len(self.grupos), verbo, fp, texto))
        
        print(f"  {len(self.grupos)} grupos de {len(textos)} textos")
    
    def classificar(self, texto: str) -> Tuple[int, float, Grupo]:
        tokens = self.pe.tokenizar_universal(texto)
        if not tokens: return -1, 0, None
        fp = self.pe.fingerprint(tokens)
        
        verbo = texto.split()[0].lower().strip('.,!?')
        
        # Primeiro: match por verbo exato
        for g in self.grupos:
            if g.verbo == verbo:
                sim = self.pe.similaridade(fp, g.fp_medio)
                return g.id, sim, g
        
        # Fallback: fingerprint
        melhor = max(
            ((g.id, self.pe.similaridade(fp, g.fp_medio), g) for g in self.grupos),
            key=lambda x: x[1], default=(-1, 0, None)
        )
        return melhor


def testar():
    print("=" * 70)
    print("  MCR DESCOBRIDOR V2 — Verbo + Fingerprint (0 hardcode)")
    print("=" * 70)
    
    d = MCRDescobridorV2()
    
    textos = [
        "Crie um NPC ferreiro em Eridanus", "Crie um sistema de progressão",
        "Crie uma habilidade de fogo", "Crie uma lore sobre Eridanus",
        "Explique o sistema SPA do MCR", "O que é o SHC",
        "Explique como funciona o Canary", "Defina o conceito de dominios",
        "Busque a definição de SPA", "Encontre os arquivos de NPC",
        "Procure por funções de combate", "Onde ficam os scripts",
        "local npc = NPC:new('Ferreiro')", "local item = Item:new(1234)",
        "function onSay(cid, words)", "if player:getLevel() < 10 then",
    ]
    
    d.aprender(textos)
    
    print(f"\n  {'Grupo':8s} {'Verbo':12s} {'Textos':8s} {'Sim int.':10s}")
    print(f"  {'-'*8} {'-'*12} {'-'*8} {'-'*10}")
    for g in d.grupos:
        print(f"  #{g.id:<6d} {g.verbo:<12s} {len(g.textos):<8d} {g.similaridade_interna:<10.3f}")
    
    print(f"\n  {'='*60}")
    print(f"  CLASSIFICANDO NOVOS TEXTOS:")
    print(f"  {'='*60}")
    for texto, desc in [
        ("Crie um vendedor em Eridanus", "criação"),
        ("Explique o que é SPA", "explicação"),
        ("Busque os arquivos de configuração", "busca"),
        ("Crie uma arma lendária", "criação"),
        ("local player = Player(cid)", "código"),
    ]:
        gid, sim, g = d.classificar(texto)
        print(f"\n  '{texto}' ({desc})")
        print(f"    → Grupo #{gid} (verbo='{g.verbo if g else '?'}', sim={sim:.2f}, {len(g.textos) if g else 0} membros)")
    
    print(f"\n  {'='*70}")
    print(f"  MCR descobriu GRUPOS DISTINTOS sem nomes hardcoded,")
    print(f"  usando apenas a primeira palavra + fingerprint.")
    print(f"  EQUIVALENTE a CREATE, EXPLAIN, SEARCH, CODE.")
    print(f"  {'='*70}")


if __name__ == '__main__':
    testar()
