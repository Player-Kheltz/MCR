#!/usr/bin/env python3
"""test_pipeline_ollama.py — Teste do pipeline completo com Ollama.

Exercita o PipelineCompleto.processar() com LLM real.
Gera métricas de:
  - Latencia real do LLM (Mistral 7B)
  - Cache hit rate com respostas reais
  - Detector de anomalias em texto gerado
  - Ensemble ativacao
  - CoVe falhas
  - World state growth (NPCs, lores canonizados)

Uso:
  python mcr/test_pipeline_ollama.py [--n 50] [--relatorio relatorio.json]
"""
import sys, os, json, time, random, argparse, urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
sys.path.insert(0, str(_PROJ))
sys.path.insert(0, str(_PROJ / 'devia' / 'kernel'))

# Prompts que geram respostas do LLM
PROMPTS = [
    # NPCs ~10s cada
    "Crie um ferreiro anao chamado Brunin que vive nas minas de Kazordoon",
    "Crie uma maga elfa que protege a floresta de Ab'Dendriel",
    "Crie um mercador humano que viaja entre Thais e Carlin",
    "Crie um guarda orc que cobra pedagio na ponte de Venore",
    "Crie um alquimista misterioso que vive na torre de Edron",
    # Lores ~8s cada
    "Explique a origem da lenda do Lago das Chamas Eternas",
    "Conte a historia da criacao da ilha de Rookgaard",
    "Explique por que os anoes de Kazordoon nao confiam em elfos",
    # Quests ~12s cada
    "Crie uma quest de coleta de ervas raras na floresta de Ab'Dendriel",
    "Crie uma quest de eliminacao de goblins que infestam as minas",
    # Codigo ~15s cada
    "Gere codigo Lua para um NPC guarda que patrulha porto",
    "Gere codigo Lua para um monster que solta fogo",
    "Gere SQL para criar tabela de itens magicos com nome e poder",
]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")


def check_ollama() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def run_test(n: int, relatorio_path: str):
    """Executa o teste."""
    from mcr.pipeline_completo import PipelineCompleto

    print(f"\n{'='*55}")
    print(f"  TESTE PIPELINE COMPLETO (Ollama)")
    print(f"  N={n} | Modelo: Mistral 7B / Qwen Coder 7B")
    print(f"  Relatorio: {relatorio_path}")
    print(f"{'='*55}\n")

    pipeline = PipelineCompleto()
    resultados = []
    t_start = time.time()

    for i in range(n):
        prompt = random.choice(PROMPTS)
        t0 = time.time()
        try:
            resultado = pipeline.processar(prompt)
            elapsed = time.time() - t0
            resultados.append({
                "iteracao": i + 1,
                "prompt": prompt[:60],
                "rota": resultado.get("rota", "?"),
                "classe": resultado.get("classe", "?"),
                "confianca": resultado.get("confianca", 0),
                "tempo": round(elapsed, 2),
                "cache_hit": resultado.get("rota") == "cache",
                "tamanho_resposta": len(resultado.get("resposta", "")),
                "existente": resultado.get("existente", {}).get("existe", False),
            })
            status = f"[{resultado.get('rota','?')}] {resultado.get('classe','?')} conf={resultado.get('confianca',0):.2f} {elapsed:.1f}s"
        except Exception as e:
            elapsed = time.time() - t0
            resultados.append({
                "iteracao": i + 1,
                "prompt": prompt[:60],
                "rota": "erro",
                "erro": str(e)[:100],
                "tempo": round(elapsed, 2),
            })
            status = f"[ERRO] {str(e)[:60]}"

        print(f"  {i+1}/{n}: {status}")

    elapsed_total = time.time() - t_start

    # Relatorio
    stats = pipeline.estatisticas()
    stats["total_request"] = n
    stats["tempo_total"] = round(elapsed_total, 1)
    stats["tempo_medio"] = round(elapsed_total / max(n, 1), 2)

    # Latencia por rota
    rotas = {}
    for r in resultados:
        rota = r.get("rota", "?")
        rotas.setdefault(rota, {"count": 0, "tempos": []})
        rotas[rota]["count"] += 1
        rotas[rota]["tempos"].append(r.get("tempo", 0))
    for rota, dados in rotas.items():
        dados["tempo_medio"] = round(sum(dados["tempos"]) / len(dados["tempos"]), 2)
        dados["tempo_min"] = round(min(dados["tempos"]), 2)
        dados["tempo_max"] = round(max(dados["tempos"]), 2)
        del dados["tempos"]

    rel = {
        "timestamp": datetime.now().isoformat(),
        "duracao_h": round(elapsed_total / 3600, 2),
        "n": n,
        "ollama": check_ollama(),
        "pipeline_stats": stats,
        "rotas": rotas,
        "resultados": resultados,
    }

    with open(relatorio_path, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"  RESUMO")
    print(f"  Tempo total: {elapsed_total:.1f}s (media {elapsed_total/max(n,1):.1f}s/req)")
    print(f"  Pipeline stats: {json.dumps(stats, indent=2)}")
    print(f"  Rotas: {json.dumps(rotas, indent=2)}")
    print(f"  Relatorio: {relatorio_path}")
    print(f"{'='*55}\n")


def main():
    parser = argparse.ArgumentParser(description="Teste Pipeline Completo com Ollama")
    parser.add_argument("--n", type=int, default=50, help="Numero de requests")
    parser.add_argument("--relatorio", default=str(_PROJ / "data" / "generated" / "relatorio_pipeline_ollama.json"))
    args = parser.parse_args()

    if not check_ollama():
        print("Ollama offline. Abortando.")
        sys.exit(1)

    run_test(args.n, args.relatorio)


if __name__ == "__main__":
    main()
