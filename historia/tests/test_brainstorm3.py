#!/usr/bin/env python3
"""BRAINSTORM 3v3 — 1 pergunta por ronda, seed MINIMO, texto livre.
Abordagem final: o modelo responde do jeito dele.
"""
import sys, os, json, time as _time
import concurrent.futures as cf

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))


def _seed():
    """Seed ultra-minimo: so os status dos modulos."""
    modulos_path = os.path.join(BASE, 'docs', 'MANIFEST.md')
    lines = []
    if os.path.exists(modulos_path):
        with open(modulos_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '| `' in line and '|' in line:
                    cols = line.split('|')
                    if len(cols) >= 5:
                        nome = cols[1].strip().strip('`').strip()
                        status = cols[2].strip()
                        if nome and len(nome) > 3 and nome not in ['Módulo', '---']:
                            lines.append(f"{status} {nome}")
    seed = 'Estado atual dos modulos:\n' + '\n'.join(lines[:40])
    
    # Tenta 1 KG
    try:
        from modulos.tool_orchestrator import ToolOrchestrator as TO
        t = TO()
        r = t.executar("buscar_kg", {"texto": "arquitetura"})
        if r.get("sucesso"):
            txt = str(r.get("resultado", ""))
            if len(txt) > 10 and "Nenhuma" not in txt:
                seed += f"\n\nKG: {txt[:400]}"
    except: pass
    
    return seed


def _ia(prompt):
    from modulos.ia import IA
    return IA().gerar(prompt, 0.3, 'instrucao') or "[ERRO]"


def executar():
    print("=" * 70)
    print("  BRAINSTORM 3v3 — 1 pergunta por ronda, texto livre")
    print("=" * 70)
    
    seed = _seed()
    print(f"\n[Seed] {len(seed)} chars\n")
    
    t0 = _time.time()
    resultados = []
    
    # RONDA 1
    p1 = f"""{seed}

Pergunta 1: O MANIFEST lista 52 modulos. Varios estao como "Fora do ciclo".
Na sua visao de sistema, o que deveria entrar PRIMEIRO e por que?
(Responda em 1-2 paragrafos, seja direto)"""
    
    r1 = _ia(p1)
    resultados.append(("O que entra primeiro?", r1))
    print(f"\n[RONDA 1] {len(r1)} chars — {r1[:300]}...")
    
    # RONDA 2 (com contexto da anterior)
    p2 = f"""{seed}

Resposta anterior: {r1[:500]}

Pergunta 2: Olhando a resposta acima, pense em 1 ideia NOVA combinando
2 conceitos do MANIFEST que ninguem pensou ainda (nao repita Gate de Entropia).
Explique: X = conceito 1, Y = conceito 2, Z = X+Y = o que surge.
Seja especifico e original."""
    
    r2 = _ia(p2)
    resultados.append(("Ideia nova (X+Y=Z)", r2))
    print(f"\n[RONDA 2] {len(r2)} chars — {r2[:300]}...")
    
    # RONDA 3
    p3 = f"""{seed}

Respostas anteriores:
1: {r1[:300]}
2: {r2[:300]}

Pergunta 3: Com base em tudo, qual acao CONCRETA o MCR-DevIA pode executar
AGORA MESMO sem codigo novo? (ex: rodar scan, emergir, weblearn, kg query...)
Seja especifico: de o comando exato."""
    
    r3 = _ia(p3)
    resultados.append(("Acao imediata (sem codigo)", r3))
    print(f"\n[RONDA 3] {len(r3)} chars — {r3[:300]}...")
    
    tempo_total = round(_time.time() - t0, 1)
    
    print(f"\n{'='*70}")
    print("  RELATORIO FINAL")
    print(f"{'='*70}")
    for titulo, resposta in resultados:
        print(f"\n--- {titulo} ({len(resposta)} chars) ---")
        print(resposta[:500])
    
    print(f"\n  Tempo total: {tempo_total}s")
    
    out = {
        "brainstorm": "3v3",
        "seed_tamanho": len(seed),
        "resultados": [{"pergunta": t, "resposta": r} for t, r in resultados],
        "tempo": tempo_total,
    }
    with open(os.path.join(BASE, 'sandbox', '.mcr_brainstorm3.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n  Salvo: sandbox/.mcr_brainstorm3.json")


if __name__ == "__main__":
    executar()
