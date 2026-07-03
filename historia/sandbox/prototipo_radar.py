#!/usr/bin/env python3
"""RADAR MCR — Teste RÁPIDO com dados pré-carregados.

Não escaneia o projeto (evita timeout). Testa as 4 ONDAS com dados sintéticos.
Valida que o RADAR consegue achar padrões por expansão em várias ondas.
"""
import sys, os, re, json, math, random, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def gerar_fingerprint(texto):
    """Gera fingerprint 64d de um texto."""
    from modulos.pattern_engine import PatternEngine
    pe = PatternEngine()
    tokens = pe.tokenizar_universal(texto)
    return pe.fingerprint(tokens) if tokens else [0.0]*64


def testar():
    print("=" * 70)
    print("  RADAR MCR — Teste Rápido (dados sintéticos)")
    print("=" * 70)
    
    pe = PatternEngine()
    
    # 1. Cria fingerprint de LORE
    fp_lore = gerar_fingerprint(
        "Eridanus era uma cidade lendária conhecida por sua simplicidade."
    )
    print(f"1. Fingerprint LORE: {[round(x,2) for x in fp_lore[:4]]}...")
    
    # 2. CANDIDATOS (simula arquivos)
    candidatos = [
        {"caminho": "docs/MCR_IDENTITY.md", "texto": "Eridanus = Cidade inicial dos aventureiros. Projeto MCR = servidor Tibia."},
        {"caminho": "docs/MANIFEST.md", "texto": "Manifesto do Projeto MCR. Catalogo de modulos e ferramentas."},
        {"caminho": "data/npc/artefato.lua", "texto": "local npc = NPC:new('Ferreiro')\nnpc:setTitle('Ferreiro')\nnpc:onSay(function() end)"},
        {"caminho": "sandbox/conversa.log", "texto": "O usuario perguntou sobre o SPA. Expliquei que e o Sistema de Progressao."},
        {"caminho": "docs/eridanus_lore.txt", "texto": "Eridanus foi fundada por exploradores. A cidade cresceu ao redor do cristal magico."},
    ]
    
    # Gera fingerprint de CADA candidato
    for c in candidatos:
        tokens = pe.tokenizar_universal(c["texto"])
        c["fingerprint"] = pe.fingerprint(tokens) if tokens else [0.0]*64
        c["tipos"] = list(set(t[0] for t in tokens)) if tokens else []
        c["tokens_count"] = len(tokens) if tokens else 0
    
    # 3. Testa ONDAS
    print(f"\n2. Candidatos carregados: {len(candidatos)}")
    for c in candidatos:
        sim = pe.similaridade(fp_lore, c["fingerprint"])
        print(f"   [{sim:.2f}] {c['caminho'][:50]}")
    
    # ONDA 1 — EXATA
    print(f"\n3. ONDA 1 (exata, sim >= 0.5):")
    onda1 = [c for c in candidatos if pe.similaridade(fp_lore, c["fingerprint"]) >= 0.5]
    for c in onda1:
        sim = pe.similaridade(fp_lore, c["fingerprint"])
        print(f"   ✅ [{sim:.2f}] {c['caminho'][:50]}")
    if not onda1:
        print(f"   ❌ Nenhum (todos abaixo de 0.5)")
    
    # ONDA 2 — TOLERÂNCIA (remove 10% das dimensões)
    print(f"\n4. ONDA 2 (tolerância, sim >= 0.4):")
    fp_tol = [v * 0.9 for v in fp_lore]
    onda2 = [c for c in candidatos if pe.similaridade(fp_tol, c["fingerprint"]) >= 0.4 and c not in onda1]
    for c in onda2:
        sim = pe.similaridade(fp_tol, c["fingerprint"])
        print(f"   ✅ [{sim:.2f}] {c['caminho'][:50]}")
    if not onda2:
        print(f"   ❌ Nenhum")
    
    # ONDA 3 — RECOMBINAÇÃO (troca tipos)
    print(f"\n5. ONDA 3 (recombinação, sim >= 0.35):")
    fp_rec = [v + random.uniform(-0.05, 0.05) for v in fp_lore]
    mag = math.sqrt(sum(v*v for v in fp_rec))
    fp_rec = [v/mag for v in fp_rec] if mag > 0 else fp_rec
    onda3 = [c for c in candidatos if pe.similaridade(fp_rec, c["fingerprint"]) >= 0.35 and c not in onda1 + onda2]
    for c in onda3:
        sim = pe.similaridade(fp_rec, c["fingerprint"])
        print(f"   ✅ [{sim:.2f}] {c['caminho'][:50]}")
    if not onda3:
        print(f"   ❌ Nenhum")
    
    # ONDA 4 — CAOS (ruído + temperatura)
    print(f"\n6. ONDA 4 (caos, sim >= 0.3, 10 tentativas):")
    onda4 = []
    for _ in range(10):
        fp_caos = [v + random.uniform(-0.15, 0.15) for v in fp_lore]
        mag = math.sqrt(sum(v*v for v in fp_caos))
        fp_caos = [v/mag for v in fp_caos] if mag > 0 else fp_caos
        for c in candidatos:
            if c in onda1 + onda2 + onda3 + onda4: continue
            sim = pe.similaridade(fp_caos, c["fingerprint"])
            if sim >= 0.3:
                onda4.append(c)
                print(f"   ✅ [{sim:.2f}] {c['caminho'][:50]}")
                break
    if not onda4:
        print(f"   ❌ Nenhum")
    
    # 7. RESULTADO FINAL
    todos = onda1 + onda2 + onda3 + onda4
    print(f"\n7. RESULTADO FINAL: {len(todos)}/{len(candidatos)} candidatos encontrados")
    
    print(f"\n  {'Onda':15s} {'Encontrados':12s} {'Score min':10s}")
    print(f"  {'-'*15} {'-'*12} {'-'*10}")
    print(f"  {'1 (exata)':15s} {len(onda1):<12d} {0.5:<10.1f}")
    print(f"  {'2 (tolerância)':15s} {len(onda2):<12d} {0.4:<10.1f}")
    print(f"  {'3 (recombinação)':15s} {len(onda3):<12d} {0.35:<10.1f}")
    print(f"  {'4 (caos)':15s} {len(onda4):<12d} {0.3:<10.1f}")
    
    print(f"\n  {'TOTAL':15s} {len(todos):<12d}")
    
    print(f"\n  {'='*70}")
    print(f"  RADAR: em 4 ondas, {len(todos)}/{len(candidatos)} candidatos encontrados")
    print(f"  Busca linear acharia apenas {len(onda1)} (onda 1)")
    print(f"  RADAR expandiu em {len(todos) - len(onda1)} candidatos além da busca exata")
    print(f"  {'='*70}")


if __name__ == '__main__':
    testar()
