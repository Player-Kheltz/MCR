#!/usr/bin/env python3
"""BRAINSTORM 2 — MCR-DevIA analisa o proprio ecossistema.
Ferramentas executadas AUTOMATICAMENTE antes do LLM.
Dados reais sao injetados no prompt — LLM nao precisa pedir.
"""
import sys, os, json, time as _time
import concurrent.futures as _cf

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))


PROMPT = """[SISTEMA]
Voce e o MCR-DevIA — o proprio sistema sendo desenvolvido.
Abaixo estao dados REAIS obtidos automaticamente das ferramentas do sistema.
NAO confie no seu conhecimento interno — use SOMENTE os dados abaixo.

[DADOS COLETADOS DAS FERRAMENTAS]
{seed}

[PERGUNTAS]
1. Analise criticamente o MANIFEST.md com base nos dados ACIMA.
   O que esta faltando? O que esta errado? O que pode ser melhorado?
2. O impasse atual (conceitos validados como Conselho, Orquestrador, Reconstructor
   estao FORA do ciclo) faz sentido ou ha outra abordagem?
3. Crie 1 IDEA EMERGENTE combinando 2 conceitos DISTANTES do MANIFEST (Z = X+Y).
   Exemplo: Conselho + PiEngine = gate de entropia.
4. Qual a PRIORIDADE REAL de implementacao na sua perspectiva de sistema?
   NAO siga o plano atual — crie SEU proprio plano.

[RESPOSTA]:"""


def executar():
    print("=" * 70)
    print("  BRAINSTORM 2 — MCR-DevIA analisa o ecossistema com dados REAIS")
    print("  Ferramentas executadas AUTOMATICAMENTE — LLM so analisa")
    print("=" * 70)
    
    from modulos.ia import IA
    from modulos.tool_orchestrator import ToolOrchestrator
    
    ia = IA()
    tools = ToolOrchestrator()
    
    print(f"\n[Executando ferramentas automaticamente...]\n")
    
    # Executa TODAS as ferramentas em paralelo
    seed_parts = []
    ferramentas_usadas = []
    t0 = _time.time()
    
    tarefas = [
        ("buscar_estrategico", {"termo": "MCR"}, "Estrutura do MCR"),
        ("buscar_estrategico", {"termo": "SPA"}, "Estrutura do SPA"),
        ("buscar_kg", {"texto": "MCR"}, "Definicoes do KG (MCR)"),
        ("buscar_kg", {"texto": "SPA"}, "Definicoes do KG (SPA)"),
        ("buscar_kg", {"texto": "SHC"}, "Definicoes do KG (SHC)"),
        ("buscar_kg", {"texto": "arquitetura"}, "Lessons de arquitetura"),
    ]
    
    with _cf.ThreadPoolExecutor(max_workers=4) as _executor:
        _futuros = {}
        for nome, params, desc in tarefas:
            _f = _executor.submit(tools.executar, nome, params)
            _futuros[_f] = (nome, params, desc)
        
        for _f in _cf.as_completed(_futuros):
            nome, params, desc = _futuros[_f]
            try:
                r = _f.result()
                txt = str(r.get("resultado", "")) if r.get("sucesso") else "(Erro)"
                if len(txt) > 30 and "Nenhum" not in txt:
                    seed_parts.append(f"--- {desc} ---\n{txt[:2000]}")
                    print(f"  [OK] {desc} ({len(txt)} chars)")
                else:
                    print(f"  [--] {desc}: sem resultados")
            except Exception as e:
                print(f"  [ERRO] {desc}: {e}")
            ferramentas_usadas.append(nome)
    
    # Carrega MANIFEST.md e IMPLEMENTACAO.md diretamente
    for arquivo, desc in [
        ("docs/MANIFEST.md", "MANIFEST.md (catalogo completo)"),
        ("docs/IMPLEMENTACAO_MANIFEST.md", "IMPLEMENTACAO_MANIFEST.md (plano de implementacao)"),
    ]:
        path = os.path.join(BASE, arquivo)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read()[:4000]
            seed_parts.append(f"--- {desc} ---\n{txt}")
            print(f"  [OK] {desc} ({len(txt)} chars)")
            ferramentas_usadas.append(f"ler_arquivo({arquivo})")
    
    seed_completo = "\n\n".join(seed_parts)
    print(f"\n  Seed total: {len(seed_completo)} chars de dados reais\n")
    
    # Monta prompt com seed
    prompt_final = PROMPT.format(seed=seed_completo)
    
    print(f"[LLM] Gerando analise...")
    t_llm = _time.time()
    try:
        resposta = ia.gerar(prompt_final, 0.3, 'instrucao') or ""
    except Exception as e:
        resposta = f"[ERRO] {e}"
    tempo_llm = round(_time.time() - t_llm, 1)
    
    tempo_total = round(_time.time() - t0, 1)
    
    print(f"\n" + "=" * 70)
    print("  RESPOSTA DO MCR-DevIA")
    print("=" * 70)
    print(f"\n{resposta}")
    print(f"\n  [{len(resposta)} chars | {tempo_total}s total | {tempo_llm}s LLM | {len(set(ferramentas_usadas))} ferramentas]")
    
    # Salva
    out_path = os.path.join(BASE, 'sandbox', '.mcr_brainstorm2.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            "descricao": "Brainstorm 2 — seed automatico com dados reais",
            "resposta": resposta,
            "tempo": tempo_total,
            "tempo_llm": tempo_llm,
            "ferramentas": list(set(ferramentas_usadas)),
            "tamanho_seed": len(seed_completo),
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Salvo: sandbox/.mcr_brainstorm2.json")
    print("=" * 70)


if __name__ == "__main__":
    executar()
