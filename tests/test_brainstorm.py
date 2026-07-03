#!/usr/bin/env python3
"""BRAINSTORM — MCR-DevIA analisa o proprio ecossistema e propoe melhorias."""
import sys, os, json, time as _time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

# Carrega o MANIFEST.md para contexto
manifest_path = os.path.join(BASE, 'docs', 'MANIFEST.md')
manifest_content = ""
try:
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest_content = f.read()
except Exception as e:
    manifest_content = f"(Erro ao ler MANIFEST: {e})"

implementacao_path = os.path.join(BASE, 'docs', 'IMPLEMENTACAO_MANIFEST.md')
implementacao_content = ""
try:
    with open(implementacao_path, 'r', encoding='utf-8') as f:
        implementacao_content = f.read()
except Exception as e:
    implementacao_content = f"(Erro ao ler IMPLEMENTACAO: {e})"

PROMPT = f"""[SISTEMA]
Voce e o MCR-DevIA — o proprio sistema que esta sendo desenvolvido.
Use TODAS as suas capacidades de analise para examinar SEU PROPRIO ESTADO ATUAL.

[MANIFEST ATUAL]
Aqui esta o catalogo completo do que voce tem (docs/MANIFEST.md):
{manifest_content[:8000]}

[PLANO DE IMPLEMENTACAO]
Aqui esta o guia de implementacao (docs/IMPLEMENTACAO_MANIFEST.md):
{implementacao_content[:4000]}

[SITUACAO ATUAL]
Voce atualmente funciona com:
1. SENSE: Security -> ContextCrew -> EpisodicMemory -> ContextInfinity
2. THINK: Decider + Mente.think (1.5b, ~3s)
3. SEED: KG definitions (busca automatica por siglas)
4. REACT LOOP: DeepSeek-r1:7b + 30 ferramentas
5. VALIDATE: AutoRevisor + Tradutor + V1-V9
6. LEARN: KG.aprender + EpisodicMemory + ContextInfinity
7. BACKGROUND: KGCleaner + SelfStudy + Emergir

[IMPASSE]
Conceitos validados (Conselho V10, Orquestrador, Reconstructor, BlankFiller,
ContextReinforcer, AutoRepair, TreeOfThought, Fragmenter, PiEngine) estao FORA
do ciclo. O plano de implementacao tem 33 etapas para integra-los.

[DESTINO]
Uma AGI hibrida que usa:
- Reconstructor como WEAVER (fingerprint + KG)
- Conselho V10 como processador multi-perspectiva (arquetipos com router de modelo)
- Orquestrador como gerador principal (templates + fragmentacao)
- ReAct como fallback (exploracao)
- Todas as 30 ferramentas integradas
- Auto-reparo e auto-consciencia ativos

[FERRAMENTAS DISPONIVEIS]
Use [FER: ...] para explorar durante a resposta se precisar de mais dados.
- buscar_estrategico(termo): descobre diretorios, arquivos e funcoes
- buscar_kg(texto): busca conhecimento no Knowledge Graph
- pattern_analyze(texto): analisa padroes em texto/codigo
- ler_arquivo(caminho): le conteudo de arquivo
- meta_planejar(tarefa): planeja uma tarefa em etapas

[PERGUNTAS]
1. Analise o MANIFEST.md criticamente. O que esta faltando? O que esta errado?
2. O impasse atual (conceitos fora do ciclo) faz sentido ou ha outra abordagem?
3. Use CRIATIVIDADE: combine 2 conceitos DISTANTES do MANIFEST para criar algo NOVO (Z = X+Y).
   Ex: Conselho + PiEngine = ?  |  Orquestrador + Fragmenter = ?  |  AutoRepair + Emergir = ?
4. Qual seria a PRIORIDADE REAL de implementacao, na SUA perspectiva de sistema?
5. Existe algo que VOCE (MCR-DevIA) pode fazer SOZINHO sem intervencao humana agora?
6. Crie um "Plano de Otimizacao" de 5 etapas que voce executaria agora mesmo.

[FORMATO DE RESPOSTA]
Seccoes:
1. ANALISE CRITICA — o que esta errado no MANIFEST
2. IDEIA EMERGENTE — combinacao de 2 conceitos distantes (Z = X+Y)
3. PRIORIDADE REAL — na sua perspectiva
4. AUTO-MELHORIA — o que voce pode fazer sozinho
5. PLANO DE OTIMIZACAO — 5 etapas executaveis

[RESPOSTA]:"""


def executar():
    print("=" * 70)
    print("  BRAINSTORM — MCR-DevIA analisa o proprio ecossistema")
    print("=" * 70)
    print(f"\n[Init] Carregando PipelineExecutor + ferramentas...\n")
    
    from modulos.kg import KnowledgeGraph
    from modulos.ia import IA
    from modulos.pipeline_executor import PipelineExecutor
    from modulos.tool_orchestrator import ToolOrchestrator
    
    kg = KnowledgeGraph()
    ia = IA()
    tools = ToolOrchestrator()
    
    print(f"[Init] KG: {len(kg._get_licoes())} lessons | IA + Tools OK\n")
    
    t0 = _time.time()
    
    try:
        resposta, meta = PipelineExecutor(
            kg=kg, ia=ia, tool_orchestrator=tools
        ).executar(PROMPT, modo_ia="auto", skip_tot=True)
    except Exception as e:
        resposta = f"[ERRO] {e}"
        meta = {"status": "ERRO"}
        import traceback
        traceback.print_exc()
    
    tempo = round(_time.time() - t0, 1)
    
    print("\n" + "=" * 70)
    print("  RESPOSTA DO MCR-DevIA")
    print("=" * 70)
    print(f"\n{resposta}")
    print(f"\n  [{len(resposta)} chars | {tempo}s | nivel={meta.get('nivel','?')} | nota={meta.get('nota','?')}]")
    
    # Salva
    out_path = os.path.join(BASE, 'sandbox', '.mcr_brainstorm.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            "pergunta": "Brainstorm: analise critica do ecossistema",
            "resposta": resposta,
            "tempo": tempo,
            "meta": meta,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Salvo: sandbox/.mcr_brainstorm.json")
    print("=" * 70)


if __name__ == "__main__":
    executar()
