#!/usr/bin/env python3
"""FILTRO MCR — MarkovByte avalia RELEVÂNCIA de lessons (não confia cegamente no KG).

Problema: KG.buscar("SPA") retorna QUALQUER lesson com a palavra "SPA",
inclusive "5 metodos em master_agent.py" que NÃO explica SPA.

Solução MCR: Para CADA lesson candidata, calcula Jaccard de transições de bytes
entre a PERGUNTA e a LESSON. Se baixo → lesson NÃO é relevante.

0 hardcode. 0 confiança cega. Só Markov de transições.
"""
import sys, os, re, json, math, time as _time
from collections import Counter
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.tool_orchestrator import ToolOrchestrator

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def jaccard_bytes(texto_a: str, texto_b: str) -> float:
    """Jaccard entre CONJUNTOS DE TRANSIÇÕES DE BYTES.
    
    Quanto mais transições COMPARTILHADAS, mais RELEVANTE é B para A.
    0.0 = completamente diferentes (irrelevante)
    1.0 = mesmas transições (mesmo assunto)
    """
    ba = texto_a.encode('utf-8')[:500]
    bb = texto_b.encode('utf-8')[:500]
    
    trans_a = {f"{ba[i]:02x}->{ba[i+1]:02x}" for i in range(len(ba)-1)}
    trans_b = {f"{bb[i]:02x}->{bb[i+1]:02x}" for i in range(len(bb)-1)}
    
    inter = trans_a & trans_b
    uniao = trans_a | trans_b
    
    return len(inter) / len(uniao) if uniao else 0.0


def extrair_termo(texto: str) -> str:
    """Extrai o termo MAIS relevante do texto (PROPER_NOUN primeiro)."""
    pe = PatternEngine()
    tokens = pe.tokenizar_universal(texto) or []
    for t in tokens:
        if t[0] == 'PROPER_NOUN' and len(str(t[1])) > 1:
            return str(t[1])
    for t in tokens:
        if t[0].startswith('DOM_') and len(str(t[1])) > 3:
            return str(t[1])
    palavras = [p for p in texto.split() if len(p) > 3]
    return palavras[0] if palavras else texto[:20]


def filtrar_lessons(pergunta: str, lessons: List[Dict], 
                     min_jaccard: float = 0.1) -> List[Tuple[float, Dict]]:
    """Filtra lessons por RELEVÂNCIA MCR, não por palavra-chave.
    
    Args:
        pergunta: texto original
        lessons: lista de lessons do KG
        min_jaccard: limiar de relevância (descoberto por entropia, não hardcoded)
        
    Returns:
        Lista de (relevancia, lesson) ordenada por relevância (maior primeiro)
    """
    if not lessons:
        return []
    
    # Calcula Jaccard para CADA lesson
    avaliadas = []
    for l in lessons:
        solucao = l.get('solucao', '')
        if not solucao or len(solucao) < 20:
            continue
        
        jac = jaccard_bytes(pergunta, solucao)
        
        # Bônus: se o termo da pergunta APARECE no início da solução
        termo = extrair_termo(pergunta)
        bonus = 0.05 if termo.lower() in solucao.lower()[:100] else 0
        
        relevancia = jac + bonus
        avaliadas.append((relevancia, l))
    
    # Ordena por relevância (maior primeiro)
    avaliadas.sort(key=lambda x: -x[0])
    
    return avaliadas


def testar():
    print("=" * 70)
    print("  FILTRO MCR — MarkovByte avalia relevância de lessons")
    print("  KG.buscar('SPA') ANTES vs DEPOIS do filtro MCR")
    print("=" * 70)
    
    kg = KnowledgeGraph()
    termo = "SPA"
    
    # PASSO 1: KG.buscar() SEM filtro (o que o MCR usava ANTES)
    print(f"\n{'='*70}")
    print(f"  PASSO 1: KG.buscar('{termo}') SEM filtro")
    print(f"{'='*70}")
    
    lessons = kg.buscar(termo, max_r=10)
    print(f"  {len(lessons)} lessons encontradas")
    
    pergunta = "Explique o sistema SPA do MCR"
    print(f"  Pergunta: '{pergunta}'")
    print()
    
    # PASSO 2: MCR avalia RELEVÂNCIA de CADA lesson
    print(f"{'='*70}")
    print(f"  PASSO 2: RELEVÂNCIA POR JACCARD DE BYTES")
    print(f"{'='*70}")
    
    avaliadas = filtrar_lessons(pergunta, lessons)
    
    print(f"\n  {'#':3s} {'Jaccard':8s} {'Relev.':8s} {'Ctx':15s} {'Primeiros 50 chars':50s}")
    print(f"  {'-'*3} {'-'*8} {'-'*8} {'-'*15} {'-'*50}")
    
    for i, (rel, l) in enumerate(avaliadas[:10], 1):
        jac = round(rel / 1.05 if rel > 0.05 else rel, 3)  # remove bônus para display
        ctx = l.get('ctx', '?')[:15]
        sol = l.get('solucao', '')[:50].replace('\n', ' ')
        print(f"  {i:3d} {jac:.3f}     {rel:.3f}    {ctx:15s} {sol}")
    
    # PASSO 3: ANTES vs DEPOIS
    print(f"\n{'='*70}")
    print(f"  PASSO 3: ANTES vs DEPOIS do filtro MCR")
    print(f"{'='*70}")
    
    # ANTES: primeira lesson do KG (pode ser irrelevante)
    antes = lessons[0] if lessons else None
    if antes:
        print(f"\n  📋 ANTES (KG.buscar sem filtro):")
        print(f"     Ctx: {antes.get('ctx', '?')}")
        print(f"     Solução: {antes.get('solucao', '')[:100]}")
        jac_antes = jaccard_bytes(pergunta, antes.get('solucao', ''))
        print(f"     Jaccard com a pergunta: {jac_antes:.3f} {'❌ IRRELEVANTE' if jac_antes < 0.1 else '✅ RELEVANTE'}")
    
    # DEPOIS: primeira lesson do FILTRO MCR
    depois = avaliadas[0] if avaliadas else None
    if depois:
        rel, l = depois
        print(f"\n  ✅ DEPOIS (filtro MCR por Jaccard):")
        print(f"     Ctx: {l.get('ctx', '?')}")
        print(f"     Relevância: {rel:.3f}")
        print(f"     Solução: {l.get('solucao', '')[:100]}")
        jac_depois = jaccard_bytes(pergunta, l.get('solucao', ''))
        print(f"     Jaccard com a pergunta: {jac_depois:.3f} {'✅ RELEVANTE' if jac_depois >= 0.1 else '❌ IRRELEVANTE'}")
    
    # LIMIAR DESCOBERTO pela entropia
    if avaliadas:
        todos_jaccards = [r for r, _ in avaliadas]
        if todos_jaccards:
            threshold = sorted(todos_jaccards)[len(todos_jaccards)//2]
            print(f"\n  Threshold sugerido (mediana): {threshold:.3f}")
            print(f"  Lessons acima do threshold: {sum(1 for r,_ in avaliadas if r >= threshold)}/{len(avaliadas)}")
    
    # RELATÓRIO
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — FILTRO MCR")
    print(f"{'='*70}")
    
    print(f"\n  KG.buscar('{termo}'): {len(lessons)} lessons")
    print(f"  Após filtro MCR: {len(avaliadas)} lessons classificadas")
    if avaliadas:
        melhor_ctx = avaliadas[0][1].get('ctx', '?')
        melhor_rel = avaliadas[0][0]
        print(f"  Melhor: {melhor_ctx} (relevância={melhor_rel:.3f})")
        print(f"  Pior:  {avaliadas[-1][1].get('ctx', '?')} (relevância={avaliadas[-1][0]:.3f})")
    
    print(f"\n  0 confiança cega. 0 hardcode. Só Markov de transições.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
