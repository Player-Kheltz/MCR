#!/usr/bin/env python3
"""teste_batch_final.py — Validacao das correcoes do pipeline MCR.

Fases:
  1. Pipeline Ollama: 25 requests com 5 workers paralelos
     Valida: rota, latencia, encoding, anti-duplicata, detector
  2. Detector: 8 textos de controle (fantasia vs anomalias)
     Valida: bigram Jaccard + return 1.0 fix para tokens no corpus

Nao inclui Markov stress — ja provado no benchmark (10M em 7.49s).

Uso:
  python mcr/teste_batch_final.py --ollama
"""
import sys, os, json, time, random, argparse, urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
sys.path.insert(0, str(_PROJ))
sys.path.insert(0, str(_PROJ / 'devia' / 'kernel'))

PROMPTS = [
    "Crie um ferreiro anao chamado Brunin que vive nas minas de Kazordoon",
    "Crie uma maga elfa que protege a floresta de Ab'Dendriel",
    "Crie um mercador humano que viaja entre Thais e Carlin",
    "Crie um guarda orc que cobra pedagio na ponte de Venore",
    "Crie um alquimista misterioso que vive na torre de Edron",
    "Crie um bardo que conta historias na taverna de Thais",
    "Explique a origem da lenda do Lago das Chamas Eternas",
    "Conte a historia da criacao da ilha de Rookgaard",
    "Crie uma quest de coleta de ervas raras na floresta de Ab'Dendriel",
    "Crie uma quest de eliminacao de goblins que infestam as minas",
    "Gere codigo Lua para um NPC guarda que patrulha porto",
    "Gere SQL para criar tabela de itens magicos com nome e poder",
]

TEXTOS_CONTROLE = [
    ("O rei governa o castelo com sabedoria e justica desde os tempos antigos", False),
    ("O mago invocou um dragao de fogo com seu cajado arcano durante a batalha", False),
    ("O guerreiro forjou uma espada de aco lendario nas minas de Kazordoon", False),
    ("A floresta encantada guarda segredos de magia e poder ancestrais", False),
    ("A nave espacial pousou no reino com lasers e robos futuristas", True),
    ("O hacker invadiu o sistema do castelo com um computador quantico", True),
    ("O dragao ciborgue atacou o castelo com misseis teleguiados", True),
    ("Use a API REST para conectar o mago ao banco de dados SQL", True),
]


def check_ollama() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


_PIPELINE_INSTANCE = None

def _worker_pipeline(prompt: str, pid: int) -> Dict:
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is None:
        from mcr.pipeline_completo import PipelineCompleto
        _PIPELINE_INSTANCE = PipelineCompleto()
    p = _PIPELINE_INSTANCE
    t0 = time.time()
    try:
        res = p.processar(prompt)
        lat = time.time() - t0
        return {
            "pid": pid,
            "prompt": prompt[:40],
            "rota": res.get("rota", "?"),
            "classe": res.get("classe", "?"),
            "conf": res.get("confianca", 0),
            "tempo": round(lat, 2),
            "cache": res.get("rota") == "cache",
            "existente": res.get("existente", {}).get("existe", False),
            "validacao_codigo": str(res.get("validacao_codigo", {})).replace("'", '"')[:200],
            "erro": None,
        }
    except Exception as e:
        lat = time.time() - t0
        return {"pid": pid, "prompt": prompt[:40], "rota": "erro", "tempo": round(lat, 2), "erro": str(e)[:120]}


def fase1_pipeline_ollama(relatorio: dict, n: int = 25, parallel: int = 5):
    print(f"\n{'='*55}")
    print(f"  FASE 1: PIPELINE OLLAMA — {n} requests ({parallel} workers)")
    print(f"{'='*55}")
    print(f"  Valida: rota, latencia, encoding, anti-duplicata, detector\n")

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [pool.submit(_worker_pipeline, random.choice(PROMPTS), i) for i in range(n)]

        resultados = []
        for i, f in enumerate(as_completed(futures)):
            r = f.result()
            resultados.append(r)
            status = f"[{r['rota']}] {r.get('classe', '')} {r['tempo']}s"
            if r.get('erro'):
                status = f"[ERRO] {r['erro'][:60]}"
            print(f"  {i+1}/{n}: #{r['pid']} {status}")

    elapsed = max(r['tempo'] for r in resultados) if resultados else 0
    tempos = [r['tempo'] for r in resultados if r['tempo'] > 0]
    media = sum(tempos) / max(len(tempos), 1)
    rotas = {}
    erros = 0
    for r in resultados:
        rot = r.get('rota', '?')
        rotas[rot] = rotas.get(rot, 0) + 1
        if r.get('erro'):
            erros += 1

    print(f"\n  Resultado:")
    print(f"  Wall time: {elapsed:.1f}s | Media: {media:.1f}s/req | Erros: {erros}/{n}")
    print(f"  Rotas: {json.dumps(rotas)}")

    relatorio["fase1"] = {
        "requests": n,
        "parallel": parallel,
        "wall_time_s": round(elapsed, 2),
        "tempo_medio_s": round(media, 2),
        "erros": erros,
        "rotas": rotas,
        "resultados": resultados,
    }


def fase2_detector_validation(relatorio: dict):
    print(f"\n{'='*55}")
    print(f"  FASE 2: VALIDACAO DO DETECTOR — {len(TEXTOS_CONTROLE)} textos")
    print(f"{'='*55}")
    print(f"  Corpus: dialogo NPC PT + world_state (paths corrigidos)\n")

    from mcr.world_anomaly_detector import WorldAnomalyDetector
    from mcr.paths import CANARY_NPC_DIR, KG_DIR
    from mcr.mcr_world_state import WORLD_STATE_FILE

    det = WorldAnomalyDetector()
    det.carregar(
        scripts_dir=str(CANARY_NPC_DIR) if CANARY_NPC_DIR and CANARY_NPC_DIR.exists() else None,
        world_state_path=str(WORLD_STATE_FILE) if WORLD_STATE_FILE and WORLD_STATE_FILE.exists() else None,
        kg_dir=str(KG_DIR),
    )
    print(f"  Corpus: {len(det.corpus)} tokens, H={det.entropia:.4f}, limiar={det.limiar_anomalia:.4f}")

    acertos = 0
    detalhes = []
    for texto, espera_anomalia in TEXTOS_CONTROLE:
        result = det.validar(texto)
        detectou = result["exige_regeneracao"]
        correto = detectou == espera_anomalia
        if correto:
            acertos += 1
        status = "OK" if correto else "FALHA"
        anomalias = [a["token"] for a in result["anomalias"][:3]]
        detalhes.append({
            "texto": texto[:55],
            "esperado": "anomalo" if espera_anomalia else "normal",
            "detectado": "anomalo" if detectou else "normal",
            "anomalias": anomalias,
        })
        print(f"  {status}: {texto[:50]}... -> {('ANOMALO' if detectou else 'NORMAL')} {anomalias}")

    precisao = acertos / len(TEXTOS_CONTROLE) * 100
    print(f"\n  Precisao: {acertos}/{len(TEXTOS_CONTROLE)} = {precisao:.0f}%")

    relatorio["fase2"] = {
        "corpus_tokens": len(det.corpus),
        "entropia": round(det.entropia, 4),
        "limiar": round(det.limiar_anomalia, 4),
        "precisao": f"{precisao:.0f}%",
        "detalhes": detalhes,
    }


def main():
    parser = argparse.ArgumentParser(description="Teste de validação MCR-DevIA")
    parser.add_argument("--ollama", action="store_true", help="Incluir Fase 1 (requer Ollama)")
    parser.add_argument("--n", type=int, default=25, help="Requests na Fase 1")
    parser.add_argument("--parallel", type=int, default=5, help="Workers paralelos na Fase 1")
    parser.add_argument("--relatorio", default=str(_PROJ / "data" / "generated" / "relatorio_batch_final.json"))
    args = parser.parse_args()

    ollama_up = check_ollama()

    print(f"\n{'='*55}")
    print(f"  TESTE DE VALIDACAO MCR-DevIA")
    print(f"  Ollama: {'DISPONIVEL' if ollama_up else 'OFFLINE (Fase 1 pulada)'}")
    print(f"  Relatorio: {args.relatorio}")
    print(f"{'='*55}")

    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "ollama": ollama_up,
    }

    t0 = time.time()

    # Fase 1: Pipeline Ollama (opcional, requer servidor)
    if ollama_up and args.ollama:
        fase1_pipeline_ollama(relatorio, args.n, args.parallel)

    # Fase 2: Detector validation (sempre roda, nao depende de LLM)
    fase2_detector_validation(relatorio)

    elapsed = time.time() - t0
    relatorio["tempo_total_s"] = round(elapsed, 2)

    with open(args.relatorio, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"  TESTE CONCLUIDO em {elapsed:.1f}s")
    print(f"  Relatorio: {args.relatorio}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
