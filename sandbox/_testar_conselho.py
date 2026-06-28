#!/usr/bin/env python3
"""Prototipo do Conselho Interno - testa debate entre personalidades."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from personalidades.personalidade_analista import Analista
from personalidades.personalidade_critico import Critico
from modulos.util import fast as _fast

def testar_conselho(pergunta, contexto=""):
    """Simula o conselho: cada personalidade pensa, depois debatem."""
    print(f'\n{"="*60}')
    print(f'CONSELHO INTERNO MCR')
    print(f'Pergunta: {pergunta}')
    print(f'{"="*60}')
    
    t0 = time.time()
    
    # 1. Cada personalidade pensa individualmente
    personalidades = [
        ("Analista", Analista()),
        ("Critico", Critico()),
    ]
    
    opinioes = []
    for nome, pers in personalidades:
        print(f'\n  [{nome}] Pensando...')
        t1 = time.time()
        opiniao = pers.pensar(pergunta, contexto)
        dt = time.time() - t1
        opinioes.append((nome, opiniao))
        print(f'  [{nome}] ({dt:.1f}s) {opiniao[:120]}...')
    
    # 2. Debate: um resume, o outro critica
    print(f'\n  [Debate] Confrontando opinioes...')
    if len(opinioes) >= 2:
        debate_prompt = f"""Duas personalidades do MCR-DevIA analisaram uma questao:

Opiniao 1 (Analista): {opinioes[0][1][:300]}

Opiniao 2 (Critico): {opinioes[1][1][:300]}

Pergunta original: {pergunta}

Apos confrontar as duas visoes, qual e a conclusao FINAL do conselho?
Responda em 2-3 frases com uma sintese equilibrada.
"""
        t1 = time.time()
        veredito = _fast(debate_prompt, 0.3, "leve")
        dt = time.time() - t1
        print(f'\n  [Veredito] ({dt:.1f}s)')
        print(f'  {veredito}')
    else:
        veredito = opinioes[0][1] if opinioes else "Sem opinioes"
    
    tempo_total = time.time() - t0
    
    print(f'\n{"="*60}')
    print(f'Tempo total: {tempo_total:.1f}s')
    print(f'Personalidades: {len(personalidades)}')
    print(f'{"="*60}')
    
    return veredito


if __name__ == '__main__':
    testar_conselho("Qual o melhor arquivo para comecar a migracao?")
