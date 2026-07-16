#!/usr/bin/env python3
"""test_producao_48h.py — Teste de Producao do MCR-DevIA (48 horas).

Uso:
  python mcr/test_producao_48h.py [--hours 48] [--sleep 1] [--relatorio relatorio.json]
"""
import sys, os, json, time, random, argparse, urllib.request, hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
sys.path.insert(0, str(_PROJ))
sys.path.insert(0, str(_PROJ / 'devia' / 'kernel'))

from mcr.cache_hierarquico import CacheHierarquico
from mcr.mcr_world_state import _carregar as ws_carregar
from mcr.world_anomaly_detector import WorldAnomalyDetector
from mcr_devia_v2 import MarkovDecider
from mcr.paths import DEVIA_KNOWLEDGE_DIR, SERVER_DIR

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")

PROMPTS_PIPELINE = [
    ("Crie um ferreiro anao chamado Brunin que vive nas minas de Kazordoon", "criar_npc"),
    ("Crie uma maga elfa que protege a floresta de Ab'Dendriel", "criar_npc"),
    ("Crie um mercador humano que viaja entre Thais e Carlin", "criar_npc"),
    ("Crie um guarda orc que cobra pedagio na ponte de Venore", "criar_npc"),
    ("Crie um alquimista misterioso que vive na torre de Edron", "criar_npc"),
    ("Crie um bardo que conta historias na taverna de Thais", "criar_npc"),
    ("Crie um cacador de recompensas que caca na selva de Tiquanda", "criar_npc"),
    ("Crie um curandeiro cego que vive no templo de Carlin", "criar_npc"),
    ("Crie um artesao que faz armaduras lendarias em Kazordoon", "criar_npc"),
    ("Crie um soldado desertor escondido nas minas de Kazordoon", "criar_npc"),
    ("Crie uma quest de coleta de ervas raras na floresta de Ab'Dendriel", "criar_quest"),
    ("Crie uma quest de eliminacao de goblins que infestam as minas", "criar_quest"),
    ("Crie uma quest de entrega de uma carta entre Thais e Carlin", "criar_quest"),
    ("Explique a origem da lenda do Lago das Chamas Eternas", "explicar_conceito"),
    ("Conte a historia da criacao da ilha de Rookgaard", "explicar_conceito"),
    ("Gere codigo Lua para um NPC guarda que patrulha porto", "criar_codigo"),
    ("Gere codigo Lua para um monster que solta fogo", "criar_codigo"),
    ("Gere SQL para criar tabela de itens magicos com nome e poder", "criar_sql"),
]

TEXTOS_ANOMALOS = [
    "rei governa com sabedoria castelo pedra magia",
    "mago invocou dragao de fogo cajado arcano",
    "guerreiro forjou espada de aco na forja Kazordoon",
    "nave espacial pousou reino lasers robos",        # anomalo
    "hacker invadiu castelo computador quantico",       # anomalo
    "presidente decretou toque recolher medieval",      # anomalo
    "dragao ciborgue atacou misseis teleguiados",       # anomalo
    "API REST conectar mago banco dados SQL",           # anomalo
    "buraco negro engoliu floresta Ab'Dendriel",        # anomalo
    "ferreiro instalou paineis solares forja energia",  # anomalo
]


def check_ollama() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


class SistemaTeste:
    """Estado compartilhado do teste para evitar recarregamentos."""

    def __init__(self):
        self.cache = CacheHierarquico()
        self.md = MarkovDecider()
        self.cache_snapshots: list = []
        self.detector_snapshots: list = []
        self.ws_snapshots: list = []
        self._last_snapshot_time = 0.0
        self._start = time.time()
        self._pipeline_stats = {"total": 0, "cache_hit": 0, "md_classify": 0,
                                 "md_learn": 0, "anomalias": 0}
        self._ollama = check_ollama()

    def tick(self):
        """Processa uma iteracao do pipeline Markov-only."""
        prompt, classe = random.choice(PROMPTS_PIPELINE)
        try:
            cls, conf = self.md.classificar(prompt)
            self._pipeline_stats["md_classify"] += 1
            self.md.aprender(prompt, classe)
            self._pipeline_stats["md_learn"] += 1
            resp = self.cache.buscar(prompt)
            if resp:
                self._pipeline_stats["cache_hit"] += 1
            else:
                self.cache.aprender(prompt, f"resposta_simulada_{hashlib.md5(prompt.encode()).hexdigest()[:8]}", classe)
        except Exception:
            pass
        self._pipeline_stats["total"] += 1

    def tick_anomalia(self, det: WorldAnomalyDetector):
        """Processa uma iteracao do detector de anomalias."""
        texto = random.choice(TEXTOS_ANOMALOS)
        try:
            r = det.validar(texto)
            if r["anomalias"]:
                self._pipeline_stats["anomalias"] += 1
                det.atualizar(texto)
        except Exception:
            pass

    def snapshot(self, label: str, det: Optional[WorldAnomalyDetector] = None):
        """Tira snapshot completo."""
        now = time.time()
        elapsed_h = round((now - self._start) / 3600, 2)

        # Cache
        cs = self.cache.estatisticas()
        self.cache_snapshots.append(cs)

        # World
        try:
            w = ws_carregar()
            ws = {"npcs": len(w.get("npcs", {})), "monstros": len(w.get("monstros", {})),
                  "lores": len(w.get("lores", {}))}
        except Exception as e:
            ws = {"erro": str(e)}
        self.ws_snapshots.append(ws)

        # Detector (soh quando fornecido)
        ds = {}
        if det:
            ds = {"entropia": round(det.entropia, 4), "limiar": round(det.limiar_anomalia, 4)}
        self.detector_snapshots.append(ds)

        # Print
        print(f"\n{'='*55}")
        print(f"  [{label}] {elapsed_h:.1f}h | Ollama: {'SIM' if self._ollama else 'NAO'}")
        print(f"  Cache: {cs.get('taxa_acerto',0)}% ({cs.get('l1_hit',0)}/{cs.get('l2_hit',0)}/{cs.get('l3_hit',0)}/{cs.get('miss',0)}) sz={cs.get('tamanho',0)}")
        print(f"  Detector: H={ds.get('entropia','?')} limiar={ds.get('limiar','?')}")
        print(f"  Mundo: {ws.get('npcs',0)}NPC {ws.get('monstros',0)}MON {ws.get('lores',0)}LOR")
        st = self._pipeline_stats
        print(f"  Pipeline: {st['total']}req cache={st['cache_hit']} md={st['md_classify']} anom={st['anomalias']}")
        print(f"{'='*55}\n")

        self._last_snapshot_time = now


def main():
    parser = argparse.ArgumentParser(description="Teste de Producao MCR-DevIA (48h)")
    parser.add_argument("--hours", type=float, default=48)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--relatorio", default=str(_PROJ / "data" / "generated" / "relatorio_producao_48h.json"))
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  TESTE DE PRODUCAO MCR-DevIA")
    print(f"  Duracao: {args.hours}h | Sleep: {args.sleep}s")
    print(f"  Relatorio: {args.relatorio}")
    print(f"{'='*55}")

    ollama_up = check_ollama()
    print(f"  Ollama: {'DISPONIVEL' if ollama_up else 'OFFLINE (modo Markov-only)'}")

    total_s = args.hours * 3600
    n1 = max(100, int(total_s * 0.5 / args.sleep))
    n2 = max(50, int(total_s * 0.25 / args.sleep))
    n3 = max(50, int(total_s * 0.25 / args.sleep))

    print(f"  Fase 1 (Pipeline Markov): {n1}x")
    print(f"  Fase 2 (Rede Markov): {n2}x")
    print(f"  Fase 3 (Anomalias): {n3}x")
    print(f"{'='*55}\n")

    # Inicializa detector uma unica vez
    det = None
    try:
        det = WorldAnomalyDetector()
        det.carregar(
            scripts_dir=str(SERVER_DIR / "data" / "scripts"),
            world_state_path=str(DEVIA_KNOWLEDGE_DIR / "world_state.json"),
            kg_dir=str(DEVIA_KNOWLEDGE_DIR),
        )
    except Exception as e:
        print(f"  [!] Detector nao carregado: {e}")

    sistema = SistemaTeste()
    sistema.snapshot("INICIO", det)
    t0 = time.time()

    try:
        # Fase 1: Pipeline Markov
        print(f"\n{'='*55}\n  FASE 1: PIPELINE MARKOV — {n1}x\n{'='*55}\n")
        for i in range(n1):
            sistema.tick()
            if (i + 1) % 200 == 0:
                print(f"  F1: {i+1}/{n1}")
                sistema.snapshot(f"F1-{i+1}", det)
            time.sleep(args.sleep)
        sistema.snapshot("F1-FIM", det)
        print("  FASE 1 OK\n")

        # Fase 2: Rede Markov (expansao)
        print(f"\n{'='*55}\n  FASE 2: REDE MARKOV — {n2}x\n{'='*55}\n")
        temas = ["reino", "floresta", "montanha", "deserto", "costa"]
        for i in range(n2):
            prompt = f"Crie um NPC de {random.choice(temas)} para mundo de fantasia"
            try:
                sistema.md.classificar(prompt)
                sistema.md.aprender(prompt, "criar_npc")
                sistema._pipeline_stats["md_classify"] += 1
                sistema._pipeline_stats["md_learn"] += 1
                sistema._pipeline_stats["total"] += 1
                sistema.cache.buscar(prompt)
            except Exception:
                pass
            if (i + 1) % 200 == 0:
                print(f"  F2: {i+1}/{n2}")
                sistema.snapshot(f"F2-{i+1}", det)
            time.sleep(args.sleep)
        sistema.snapshot("F2-FIM", det)
        print("  FASE 2 OK\n")

        # Fase 3: Detector Stress
        print(f"\n{'='*55}\n  FASE 3: DETECTOR STRESS — {n3}x\n{'='*55}\n")
        if det:
            for i in range(n3):
                sistema.tick_anomalia(det)
                if (i + 1) % 200 == 0:
                    print(f"  F3: {i+1}/{n3}")
                    sistema.snapshot(f"F3-{i+1}", det)
                time.sleep(args.sleep)
        else:
            print("  [!] Detector nao disponivel, pulando Fase 3\n")
            for _ in range(n3):
                time.sleep(args.sleep)
        sistema.snapshot("F3-FIM", det)

    except KeyboardInterrupt:
        print("\n  [!] Interrompido")
        sistema.snapshot("INTERRUPCAO", det)

    elapsed = time.time() - t0
    sistema.snapshot("FIM", det)

    print(f"\n{'='*55}")
    print(f"  TESTE CONCLUIDO — {elapsed/3600:.1f}h ({elapsed:.0f}s)")
    print(f"  Snapshots: {len(sistema.cache_snapshots)}")
    print(f"  Resultado final:")
    cs = sistema.cache_snapshots[-1] if sistema.cache_snapshots else {}
    ws = sistema.ws_snapshots[-1] if sistema.ws_snapshots else {}
    ds = sistema.detector_snapshots[-1] if sistema.detector_snapshots else {}
    print(f"  Cache: {cs.get('taxa_acerto',0)}% hit ({cs.get('tamanho',0)} entradas)")
    print(f"  Detector: H={ds.get('entropia','?')} limiar={ds.get('limiar','?')}")
    print(f"  Mundo: {ws.get('npcs','?')}NPC {ws.get('monstros','?')}MON {ws.get('lores','?')}LOR")
    print(f"  Ollama: {'SIM' if sistema._ollama else 'NAO'}")
    print(f"{'='*55}\n")

    # Salva relatorio consolidado
    rel = {
        "duracao_h": round(elapsed / 3600, 2),
        "ollama": sistema._ollama,
        "pipeline_stats": sistema._pipeline_stats,
        "cache_snapshots": sistema.cache_snapshots,
        "detector_snapshots": sistema.detector_snapshots,
        "world_snapshots": sistema.ws_snapshots,
    }
    with open(args.relatorio, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)
    print(f"  Relatorio salvo: {args.relatorio}")


if __name__ == "__main__":
    main()
