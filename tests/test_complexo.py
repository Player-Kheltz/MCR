#!/usr/bin/env python3
"""TESTE COMPLEXO AGI — Mede o ecossistema completo com 1 pergunta complexa.

Envolve: SENSE, THINK, ACT (Tool + KG + Enricher + LLM), VALIDATE, LEARN
Pergunta: SPA + dominios + SHC + codigo Lua real + lore criativa
"""
import sys, os, json, time as _time
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

PERGUNTA = (
    "Explique o sistema SPA do MCR: quais sao seus dominios elementais, "
    "como o SHC se integra a ele, de exemplos de funcoes Lua que mostram "
    "essa integracao, e crie uma lore curta para um novo dominio chamado "
    "'Vento' com 3 nomes de habilidades."
)

CRITERIOS = {
    "spa_definido": {"peso": 2, "termos": ["sistema de progressao", "aventureiro"]},
    "dominios": {"peso": 2, "termos": ["fogo", "gelo", "terra", "energia"]},
    "shc_integrado": {"peso": 2, "termos": ["shc", "habilidades contextuais", "spa"]},
    "codigo_lua": {"peso": 2, "termos": [".lua", "function", "spa"]},
    "lore_vento": {"peso": 1, "termos": ["vento", "habilidade"]},
    "nao_alucinar": {"peso": 1, "termos_proibidos": ["agua", "trevas", "luz", "minecraft"]},
}

def _normalizar(texto):
    """Remove acentos para comparacao."""
    import unicodedata as _uni
    return _uni.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower().strip()

def avaliar(resposta):
    """Avalia resposta contra criterios. Retorna (nota, detalhes)."""
    r = _normalizar(resposta)
    total = 0
    obtido = 0
    detalhes = []
    
    for nome, crit in CRITERIOS.items():
        peso = crit["peso"]
        total += peso
        
        if "termos" in crit:
            ok = all(_normalizar(t) in r for t in crit["termos"])
            if ok:
                obtido += peso
                detalhes.append(f"  [OK] {nome}")
            else:
                faltando = [t for t in crit["termos"] if _normalizar(t) not in r]
                detalhes.append(f"  [FALTA] {nome}: {faltando}")
        
        if "termos_proibidos" in crit:
            proibidos = [t for t in crit["termos_proibidos"] if _normalizar(t) in r]
            if proibidos:
                detalhes.append(f"  [PROIBIDO] {nome}: {proibidos}")
            else:
                obtido += peso
                detalhes.append(f"  [OK] {nome}")
    
    nota = round(obtido / total * 10, 1)
    return nota, detalhes


def executar():
    print("=" * 70)
    print("  TESTE COMPLEXO AGI — Ecossistema Completo")
    print("=" * 70)
    print(f"\nPergunta: {PERGUNTA[:80]}...")
    print(f"\n[INICIALIZANDO] Carregando PipelineExecutor + KG + ToolOrchestrator...")
    
    from modulos.kg import KnowledgeGraph
    from modulos.ia import IA
    from modulos.pipeline_executor import PipelineExecutor
    from modulos.tool_orchestrator import ToolOrchestrator
    
    kg = KnowledgeGraph()
    ia = IA()
    tools = ToolOrchestrator()
    
    licoes = kg._get_licoes()
    ativas = [l for l in licoes if not l.get('inactive', False)]
    print(f"  KG: {len(licoes)} lessons carregadas, {len(ativas)} ativas")
    print(f"  Iniciando pipeline...\n")
    
    t0 = _time.time()
    
    try:
        resposta, meta = PipelineExecutor(
            kg=kg, ia=ia, tool_orchestrator=tools
        ).executar(PERGUNTA, modo_ia="auto", skip_tot=True)
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return
    
    tempo = round(_time.time() - t0, 1)
    
    print("\n" + "=" * 70)
    print("  RESPOSTA COMPLETA")
    print("=" * 70)
    print(f"\n{resposta}")
    print(f"\n  [{len(resposta)} chars | {tempo}s | nivel={meta.get('nivel','?')} | nota_interna={meta.get('nota','?')}]")
    
    print("\n" + "=" * 70)
    print("  AVALIACAO POR CRITERIOS")
    print("=" * 70)
    nota, detalhes = avaliar(resposta)
    for d in detalhes:
        print(d)
    
    print(f"\n  NOTA FINAL: {nota}/10")
    print(f"  TEMPO: {tempo}s")
    
    # Salva resultado
    resultado = {
        "pergunta": PERGUNTA,
        "resposta": resposta,
        "tempo": tempo,
        "nivel": meta.get('nivel', '?'),
        "nota_interna": meta.get('nota', '?'),
        "nota_avaliacao": nota,
        "tamanho": len(resposta),
    }
    out_path = os.path.join(BASE, 'sandbox', '.mcr_teste_complexo.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultado salvo em: sandbox/.mcr_teste_complexo.json")
    print("=" * 70)


if __name__ == "__main__":
    executar()
