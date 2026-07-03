#!/usr/bin/env python3
"""BRAINSTORM FINAL — MCR-DevIA analisa-se usando SEUS proprios conceitos.
Ativa arquétipo ANALISTA do Conselho V10 + Emergir + PiEngine.
NAO usa pipeline padrao — usa os modulos do proprio sistema.
"""
import sys, os, json, time as _time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))


def _coletar_seed():
    """Coleta dados minimos do proprio ecossistema (~1K chars)."""
    partes = []
    
    # 1. Status dos modulos (do MANIFEST)
    path = os.path.join(BASE, 'docs', 'MANIFEST.md')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for linha in f:
                if '| `' in linha and '|' in linha:
                    cols = linha.split('|')
                    if len(cols) >= 5:
                        nome = cols[1].strip().strip('`').strip()
                        status = cols[2].strip()
                        desc = cols[3].strip() if len(cols) >= 4 else ''
                        if nome and len(nome) > 3 and nome not in ['Módulo', '---']:
                            partes.append(f"{status} {nome}: {desc[:60]}")
    
    seed = "ESTADO ATUAL DO ECOSSISTEMA MCR-DevIA:\n\n"
    seed += '\n'.join(partes[:50])
    seed += "\n\nConceitos FORA do ciclo: Conselho V10, Orquestrador, Reconstructor, BlankFiller, AutoRepair, TreeOfThought, ContextReinforcer, PiEngine"
    
    return seed[:2000]


def executar():
    print("=" * 70)
    print("  BRAINSTORM FINAL — MCR-DevIA usa SEUS proprios conceitos")
    print("  Ativando: Conselho V10 (analista) + Emergir + PiEngine")
    print("=" * 70)
    
    seed = _coletar_seed()
    print(f"\n[Seed] {len(seed)} chars\n")
    
    from modulos.ia import IA
    from modulos.kg import KnowledgeGraph
    
    kg = KnowledgeGraph()
    ia = IA()
    
    # Prompt que ATIVA o arquétipo ANALISTA
    # (mesma abordagem que o Conselho V10 usa internamente)
    prompt_ativacao = f"""{seed}

[SISTEMA]
Ativando arquétipo ANALISTA do Conselho V10.
Use Emergir para conectar conceitos distantes.
Use PiEngine para auto-avaliar a entropia da sua resposta.

[INSTRUCAO]
1. ANALISE os dados acima. Identifique 1 problema REAL no ecossistema.
2. EMERGIR: conecte 2 modulos DISTANTES para resolver o problema.
3. PIENGINE: auto-avalie sua resposta (entropia baixa = ideia solida).
4. ORQUESTRADOR: responda no formato:
   PROBLEMA: [o que esta errado]
   CAUSA: [por que acontece]
   SOLUCAO: [o que fazer] (cite 2 modulos DISTANTES)
   IMPACTO: [o que muda]
   AUTO-AVALIACAO: [entropia alta/baixa e por que]

[RESPOSTA DO ANALISTA]:"""
    
    t0 = _time.time()
    
    # Usa IA diretamente com prompt de arquétipo ANALISTA
    # (mesmo padrao do Conselho V10: identidade + prompt + resposta)
    print("[Conselho V10] Ativando arquétipo ANALISTA (via prompt)...")
    try:
        resposta = ia.gerar(prompt_ativacao, 0.3, 'instrucao') or "[ERRO]"
        origem = "IA (arquetipo ANALISTA)"
    except Exception as e:
        resposta = f"[ERRO] {e}"
        origem = "ERRO"
    
    tempo = round(_time.time() - t0, 1)
    
    print(f"\n[Origem] {origem}")
    print(f"[Tempo] {tempo}s")
    print(f"[Tamanho] {len(resposta)} chars")
    print(f"\n{'='*70}")
    print("  RESPOSTA DO CONSELHO (arquetipo ANALISTA)")
    print(f"{'='*70}\n")
    print(resposta)
    print(f"\n{'='*70}")
    
    # Salva
    out = {
        "brainstorm": "final",
        "seed_tamanho": len(seed),
        "origem": origem,
        "resposta": resposta,
        "tempo": tempo,
    }
    out_path = os.path.join(BASE, 'sandbox', '.mcr_brainstorm_final.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n  Salvo: sandbox/.mcr_brainstorm_final.json")


if __name__ == "__main__":
    executar()
