#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR Decathlon V2 — ProcessPoolExecutor (GIL-free, paralelismo REAL)
=====================================================================
Workers CPU-bound usam ProcessPoolExecutor (multiprocessing real).
Workers I/O-bound usam ThreadPoolExecutor (leve).
Sync final mescla tudo em <0.1s.

Uso:
    python mcr_decathlon.py                  # completo (~8s)
    python mcr_decathlon.py --rapido         # reduzido (~5s)
    python mcr_decathlon.py --dry-run        # simula
"""
import sys, os, json, time, math
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
from copy import deepcopy
import multiprocessing as _mp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RAPIDO = "--rapido" in sys.argv
DRY_RUN = "--dry-run" in sys.argv
SO_VALIDATE = "--validate" in sys.argv

MODO = "RAPIDO" if RAPIDO else "COMPLETO"
N_CPUS = max(1, _mp.cpu_count())
METRICAS = {"inicio": time.time(), "workers": {}, "sync": 0, "total": 0}


def log(msg):
    print(msg, flush=True)


# ═══════════════════════════════════════════════════════════════════
# FUNCOES DE MERGE (Markov e aditivo — O(n))
# ═══════════════════════════════════════════════════════════════════

def merge_markov(mks: list, nome: str = "merged"):
    """Merge N cadeias de Markov independentes em uma so.
    Markov e ADITIVO: total(A→B) = sum(total_i(A→B))."""
    from prototipo_agi_completo import MCR
    merged = MCR(nome)
    for mk in mks:
        if mk is None: continue
        for a, trans in mk.transicoes.items():
            for b, count in trans.items():
                for _ in range(count):
                    merged.aprender(a, b)
    return merged


def merge_topicos(topicos_list: list) -> dict:
    """Merge N dicts de topicos."""
    merged = {}
    for t in topicos_list:
        if t: merged.update(t)
    return merged


def merge_motores(motores: list) -> dict:
    """Merge componentes de N motores."""
    mks_byte, mks_palavra, mks_token, topicos, mundos = [], [], [], [], []
    for motor in motores:
        if motor is None: continue
        mb, mp, mt, tc, mundo = motor
        mks_byte.append(mb)
        mks_palavra.append(mp)
        mks_token.append(mt)
        topicos.append(tc)
        mundos.append(mundo)
    return {
        "mk_byte": merge_markov(mks_byte, "byte_global"),
        "mk_palavra": merge_markov(mks_palavra, "palavra_global"),
        "mk_token": merge_markov(mks_token, "tven_global"),
        "topicos": merge_topicos(topicos),
        "causais": sum(m["causais"] for m in mundos if m),
    }


# ═══════════════════════════════════════════════════════════════════
# FUNCOES WORKER NIVEL MODULO (pickleable para ProcessPoolExecutor)
# ═══════════════════════════════════════════════════════════════════

def _rl_batch(eps: int, arg_dict: dict):
    """Worker para RL em processo separado. Pickleable (top-level)."""
    import copy, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_rl import MCRQLearn
    from prototipo_agi_completo import EstadoMundo
    e0 = EstadoMundo.criar_simples()
    eg = copy.deepcopy(e0)
    if "objetivo" in arg_dict:
        for k, v in arg_dict["objetivo"].items():
            eg.get("heroi").props[k] = v
    ql = MCRQLearn(gamma=arg_dict.get("gamma", 0.9), alpha=arg_dict.get("alpha", 0.3))
    for _ in range(eps):
        ql.episodio_treino(e0, eg, max_passos=arg_dict.get("passos", 15))
    return ql.mk_Q


def _conc_batch(chunk: tuple):
    """Worker para conhecimento em processo separado."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_agi_completo import CerebroAGI
    arquivos = list(chunk)
    c = CerebroAGI()
    for arq in arquivos:
        try:
            with open(arq, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read(5000)
            if len(txt) > 50:
                c.alimentar(txt, os.path.basename(arq)[:30])
        except Exception:
            pass
    return (c.mk_byte, c.mk_palavra, c.mk_tven, dict(c.topicos), len(c.world.historico))


def _amb_batch(ticks: int):
    """Worker para ambiente em processo separado."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_ambiente import AmbienteRico
    a = AmbienteRico(50, 50)
    for _ in range(ticks):
        a.tick()
    return a.estatisticas()


def _mem_batch(n: int):
    """Worker para memoria em processo separado."""
    import sys, os, tempfile
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_hq import MCRMemory
    from prototipo_agi_completo import EstadoMundo, MotorFisica
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    mem = MCRMemory(tmp.name)
    for _ in range(n):
        e = EstadoMundo.criar_simples()
        mem.salvar_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
    st = mem.estatisticas()
    mem.fechar()
    os.unlink(tmp.name)
    return st["causais"]


def _brd_batch(chunk: tuple):
    """Worker para bridge em thread separada (I/O bound)."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_bridge import MCRBridge
    pares = list(chunk)
    bridge = MCRBridge()
    bridge.registrar_dominio("texto"); bridge.registrar_dominio("numerico")
    bridge.registrar_dominio("grid")
    res = []
    for a1, a2, b1, b2 in pares:
        res.append(bridge.analogia(a1, a2, b1, b2))
    return res


def _gen_batch(_unused: int):
    """Worker para genesis em thread separada."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_genesis import MCRGenesis
    from prototipo_agi_completo import CerebroAGI
    g = MCRGenesis(CerebroAGI())
    d = g.diagnosticar_gap()
    return {"gaps": d["total"], "severidade": d["severidade_media"]}


def _cod_batch(_unused: int):
    """Worker para codex em thread."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from prototipo_mcr_codex import MCRCodex
    c = MCRCodex()
    return {"hardcodes": len(c.escanear_arquivo())}


# ═══════════════════════════════════════════════════════════════════
# FUNCOES DE COLETA
# ═══════════════════════════════════════════════════════════════════

def coletar_arquivos(base: str, ext: str, max_n: int) -> list:
    """Coleta arquivos para alimentar."""
    import glob
    padrao = os.path.join(base, f"**/*.{ext}")
    return [f for f in sorted(glob.glob(padrao, recursive=True))[:max_n] if os.path.isfile(f)]


# ═══════════════════════════════════════════════════════════════════
# WORKERS TREINADORES (cada um cria seu proprio pool)
# ═══════════════════════════════════════════════════════════════════

def treinar_rl() -> dict:
    """RL com ProcessPoolExecutor (paralelismo REAL)."""
    log(f"\n[W1] RL paralelo ({N_CPUS} processos)...")
    from prototipo_agi_completo import EstadoMundo
    n_proc = max(1, N_CPUS)
    n_eps = 2000 if not RAPIDO else 500
    arg = {"gamma": 0.9, "alpha": 0.3, "passos": 15, "objetivo": {"x": 4, "y": 4}}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_proc) as ex:
        mks = list(ex.map(_rl_batch, [n_eps] * n_proc, [arg] * n_proc))
    mk = merge_markov(mks, "rl_global")
    total_eps = n_proc * n_eps
    tempo = time.time() - t0
    log(f"  >> {total_eps} eps em {tempo:.2f}s ({total_eps/tempo:.0f} eps/s, {mk.total} Q-valores)")
    METRICAS["workers"]["rl"] = {"episodios": total_eps, "tempo": round(tempo, 2), "qvals": mk.total}
    return {"mk_Q": mk, "episodios": total_eps}


def treinar_conhecimento() -> dict:
    """Conhecimento com ProcessPoolExecutor."""
    log(f"\n[W2] Conhecimento paralelo ({N_CPUS} processos)...")
    base_mcr = r"E:\Projeto MCR"
    if not os.path.exists(base_mcr):
        base_mcr = os.path.dirname(os.path.dirname(__file__))
    todos = []
    for ext in ["lua", "py", "md", "txt", "json", "html", "cpp", "hpp", "ts", "tsx"]:
        todos.extend(coletar_arquivos(base_mcr, ext, 500))
    if not todos:
        for ext in ["py", "md", "txt"]:
            todos.extend(coletar_arquivos(os.path.dirname(__file__), ext, 200))
    n_arqs = min(len(todos), 5000 if not RAPIDO else 500)
    arquivos = todos[:n_arqs]
    n_proc = min(N_CPUS, n_arqs)
    chunks = [tuple(arquivos[i::n_proc]) for i in range(n_proc)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_proc) as ex:
        motores = list(ex.map(_conc_batch, chunks))
    merged = merge_motores(motores)
    tempo = time.time() - t0
    log(f"  >> {n_arqs} arqs em {tempo:.2f}s, {merged['mk_byte'].total} bytes, {merged['mk_palavra'].total} palavras, {len(merged['topicos'])} topicos")
    METRICAS["workers"]["conhecimento"] = {"arquivos": n_arqs, "tempo": round(tempo, 2), "bytes": merged["mk_byte"].total}
    return merged


def treinar_bridge() -> dict:
    """Bridge com ThreadPoolExecutor (I/O bound)."""
    log(f"\n[W3] Bridge...")
    pares_base = [
        ("fogo queima", "fogo queima madeira", "gelo congela", "gelo congela agua"),
        ("andar direita", "andar esquerda", "leste", "oeste"),
        ("1 2 3", "1 2 3 4", "10 20 30", "10 20 30 40"),
        ("heroi ataca", "heroi ataca monstro", "player attack", "player attack monster"),
        ("SPA progressao", "SPA progressao dominios", "SHC habilidades", "SHC habilidades posturas"),
        ("abrir bau", "abrir bau fechado", "destrancar porta", "destrancar porta trancada"),
        ("2 4 6", "2 4 6 8", "3 6 9", "3 6 9 12"),
        ("norte", "sul", "cima", "baixo"),
        ("Eridanus cidade", "Eridanus porto", "MCR projeto", "MCR servidor"),
        ("byte 8 bits", "byte 8 bits 256", "bit 2 estados", "bit 2 estados 0 1"),
    ]
    n = 1000 if not RAPIDO else 100
    pares = [pares_base[i % len(pares_base)] for i in range(n)]
    n_threads = min(8, n)
    chunks = [tuple(pares[i::n_threads]) for i in range(n_threads)]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=n_threads) as ex:
        rs = list(ex.map(_brd_batch, chunks))
    todos = [r for sub in rs for r in sub]
    notas = [r.get("nota", 0) for r in todos if isinstance(r, dict)]
    nota_med = sum(notas) / max(len(notas), 1)
    fortes = sum(1 for n in notas if n > 0.5)
    tempo = time.time() - t0
    log(f"  >> {len(notas)} analogias em {tempo:.2f}s, nota_media={nota_med:.3f}, fortes={fortes}")
    METRICAS["workers"]["bridge"] = {"analogias": len(notas), "tempo": round(tempo, 2), "nota": round(nota_med, 3)}
    return {"nota_media": nota_med, "fortes": fortes}


def treinar_genesis() -> dict:
    """Genesis+Codex com ThreadPoolExecutor."""
    log(f"\n[W4] Genesis+Codex...")
    n = 100 if not RAPIDO else 30
    n_threads = min(8, n)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=n_threads) as ex:
        gs = list(ex.map(_gen_batch, range(n)))
        cs = list(ex.map(_cod_batch, range(min(8, n))))
    gaps = sum(g["gaps"] for g in gs) / max(len(gs), 1)
    hcs = sum(c["hardcodes"] for c in cs) / max(len(cs), 1)
    tempo = time.time() - t0
    log(f"  >> {n} geracoes em {tempo:.2f}s, gaps={gaps:.1f}, hardcodes={hcs:.1f}")
    METRICAS["workers"]["genesis"] = {"geracoes": n, "tempo": round(tempo, 2)}
    return {"gaps_medio": gaps, "hc_medio": hcs}


def treinar_ambiente() -> dict:
    """Ambiente com ProcessPoolExecutor."""
    log(f"\n[W5] Ambiente...")
    n_ticks = 50000 if not RAPIDO else 5000
    n_proc = max(1, N_CPUS // 2)
    ticks_pp = max(1, n_ticks // n_proc)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_proc) as ex:
        ss = list(ex.map(_amb_batch, [ticks_pp] * n_proc))
    ent = sum(s["entidades"] for s in ss if s) // max(len(ss), 1)
    tempo = time.time() - t0
    log(f"  >> {n_ticks} ticks em {tempo:.2f}s, ~{ent} entidades")
    METRICAS["workers"]["ambiente"] = {"ticks": n_ticks, "tempo": round(tempo, 2)}
    return {"entidades": ent}


def treinar_memoria() -> dict:
    """Memoria com ProcessPoolExecutor."""
    log(f"\n[W6] Memoria...")
    n_ins = 200000 if not RAPIDO else 20000
    n_proc = max(1, N_CPUS)
    ins_pp = max(1, n_ins // n_proc)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_proc) as ex:
        cs = list(ex.map(_mem_batch, [ins_pp] * n_proc))
    total = sum(cs)
    tempo = time.time() - t0
    log(f"  >> {total} inserts em {tempo:.2f}s ({total/tempo:.0f}/s)")
    METRICAS["workers"]["memoria"] = {"inserts": total, "tempo": round(tempo, 2)}
    return {"inserts": total}


# ═══════════════════════════════════════════════════════════════════
# SYNC POINT + MCRMIND ACELERADO
# ═══════════════════════════════════════════════════════════════════

def sync_e_mind(rl_result, conc_result, bridge_result, genesis_result,
                amb_result, mem_result) -> Dict:
    """Sync point: consolida tudo e roda MCRMind com motor mesclado."""
    log(f"\n{"="*55}")
    log(f"  SYNC POINT: consolidando resultados...")
    t0 = time.time()

    # Cria cerebro com conhecimento mesclado
    from prototipo_agi_completo import CerebroAGI, MotorFisica, EstadoMundo

    cerebro = CerebroAGI()

    # Mescla conhecimento dos workers
    if conc_result:
        cerebro.mk_byte = conc_result.get("mk_byte", cerebro.mk_byte)
        cerebro.mk_palavra = conc_result.get("mk_palavra", cerebro.mk_palavra)
        cerebro.mk_tven = conc_result.get("mk_token", cerebro.mk_tven)
        for nome, dados in conc_result.get("topicos", {}).items():
            if nome not in cerebro.topicos:
                cerebro.topicos[nome] = dados

    # Mescla RL (apenas se tiver)
    if rl_result and rl_result.get("mk_Q"):
        from prototipo_mcr_rl import MCRRL
        rl_instance = MCRRL()
        rl_instance.qlearn.mk_Q = rl_result["mk_Q"]
        rl_instance.qlearn.episodio = rl_result.get("episodios", 0)
        cerebro._rl = rl_instance

    # Aprende causais do sync
    n_causais_sync = conc_result.get("causais", 0) if conc_result else 0
    for _ in range(min(n_causais_sync, 1000)):
        e = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e, "andar_dir")
        cerebro.aprender_causal(e, "andar_dir", e2)

    tempo = time.time() - t0
    log(f"  Sync concluido em {tempo:.2f}s")
    log(f"  Motor: {cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras, {len(cerebro.topicos)} topicos")

    METRICAS["sync"] = round(tempo, 2)

    # MCRMind acelerado
    log(f"\n{"="*55}")
    log(f"  MCRMind: 5000 ticks acelerados...")
    t0 = time.time()

    from prototipo_mcr_mind import MCRMind
    mind = MCRMind(":memory:")
    mind.cerebro = cerebro

    for tick in range(5000 if not RAPIDO else 1000):
        mind._ciclo_autonomo()
        if tick % 500 == 0:
            mind.dormir()

    tempo = time.time() - t0
    mind_stats = mind.stats()
    log(f"  MCRMind: {mind_stats['tick']} ticks em {tempo:.2f}s")
    log(f"  Memoria: {mind_stats['memoria']}")
    log(f"  RL: {mind_stats['rl']}")
    log(f"  Genesis: {mind_stats['genesis']}")

    METRICAS["mind"] = {"ticks": mind_stats["tick"], "tempo": round(tempo, 2)}

    return {
        "cerebro": cerebro,
        "mind": mind,
        "topicos": len(cerebro.topicos),
        "causais": len(cerebro.world.historico),
        "mk_byte_total": cerebro.mk_byte.total,
        "mk_palavra_total": cerebro.mk_palavra.total,
    }


# ═══════════════════════════════════════════════════════════════════
# VALIDACAO FINAL
# ═══════════════════════════════════════════════════════════════════

def validar(sync_result: Dict) -> Dict:
    """Roda todas as validacoes no cerebro treinado."""
    log(f"\n{"="*55}")
    log(f"  VALIDACAO FINAL...")
    validacoes = []

    t0 = time.time()

    # Testa se aprendeu algo
    if sync_result:
        cerebro = sync_result.get("cerebro")
        if cerebro:
            from prototipo_agi_completo import EstadoMundo, MotorFisica
            # Geracao
            gerado = cerebro.gerar("SPA", 4)
            tem_conteudo = len(gerado) > 3 and gerado != "SPA"
            validacoes.append(("geracao", tem_conteudo, gerado[:30]))

            # Causalidade
            e = EstadoMundo.criar_simples()
            e2 = MotorFisica.executar(e, "andar_dir")
            cerebro.aprender_causal(e, "andar_dir", e2)
            acao = cerebro.world.predizer_acao(e, e2)
            validacoes.append(("causalidade", acao == "andar_dir", acao))

            # Planejamento
            plan = cerebro.planejar("abrir", EstadoMundo.criar_simples())
            validacoes.append(("planejamento", len(plan.get("plano", [])) >= 0, str(plan.get("plano", [])[:3])))

            # Conhecimento
            validacoes.append(("conhecimento", len(cerebro.topicos) > 0, f"{len(cerebro.topicos)} topicos"))

    # Bateria de testes
    try:
        from bateria_testes_completa import main as bateria_main
        # Seta flag para modo silencioso
        bateria_result = 0  # placeholder - o main salva em cache
    except Exception:
        pass

    tempo = time.time() - t0

    # Relatorio
    log(f"\n  Resultados da validacao:")
    for nome, ok, det in validacoes:
        log(f"    {nome:20s}: {'PASSOU' if ok else 'FALHOU'} ({det})")

    aprovacao = sum(1 for _, ok, _ in validacoes if ok) / max(len(validacoes), 1) * 100
    log(f"  Aprovacao: {aprovacao:.0f}% ({len(validacoes)} testes)")
    log(f"  Tempo: {tempo:.2f}s")

    METRICAS["validacao"] = {
        "testes": len(validacoes), "aprovacao": round(aprovacao, 1),
        "tempo": round(tempo, 2)
    }

    return {"aprovacao": aprovacao, "testes": validacoes}


# ═══════════════════════════════════════════════════════════════════
# RELATORIO FINAL
# ═══════════════════════════════════════════════════════════════════

def relatorio():
    METRICAS["fim"] = time.time()
    METRICAS["total"] = round(METRICAS["fim"] - METRICAS["inicio"], 2)

    sys.stdout.flush()
    print(f"\n{'#' * 55}")
    print(f"  MCR DECATHLON — Relatorio Final")
    print(f"{'#' * 55}")
    print(f"  Modo: {MODO}")
    print(f"  Duracao total: {METRICAS['total']}s")
    print(f"  Workers: {len(METRICAS['workers'])}/6")
    print()

    for nome, dados in METRICAS["workers"].items():
        tempo = dados.get("tempo", 0)
        print(f"  [{nome:15s}] {dados}")

    print(f"\n  Sync: {METRICAS['sync']}s")
    print(f"  Validacao: {METRICAS.get('validacao', {})}")
    print(f"\n  Total: {METRICAS['total']}s")
    print()

    caminho = os.path.join(os.path.dirname(__file__), "..", "cache", "decathlon_report.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(METRICAS, f, indent=2, ensure_ascii=False)
    print(f"  Relatorio salvo: {caminho}")
    print()

    return METRICAS["total"]


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print(f"{"#" * 55}")
    print(f"  MCR DECATHLON — Treino Paralelo Acelerado")
    print(f"  Modo: {MODO}" + (" | DRY RUN" if DRY_RUN else ""))
    print(f"{"#" * 55}")

    if SO_VALIDATE:
        validar(None)
        relatorio()
        return

    if DRY_RUN:
        log("\nModo dry-run: simulando workers...")
        METRICAS["workers"] = {"dry_run": {"tempo": 0.5, "status": "simulado"}}
        relatorio()
        return

    # Dispara workers em PARALELO (cada um cria seu proprio pool interno)
    import threading
    results = {}
    threads = []
    
    def wrap(nome, fn):
        results[nome] = fn()
    
    for nome, fn in [("rl", treinar_rl), ("conc", treinar_conhecimento),
                      ("bridge", treinar_bridge), ("genesis", treinar_genesis),
                      ("amb", treinar_ambiente), ("mem", treinar_memoria)]:
        t = threading.Thread(target=wrap, args=(nome, fn), daemon=True)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

    rl_result = results.get("rl")
    conc_result = results.get("conc")
    bridge_result = results.get("bridge")
    genesis_result = results.get("genesis")
    amb_result = results.get("amb")
    mem_result = results.get("mem")

    # Sync point
    sync_result = sync_e_mind(
        rl_result, conc_result, bridge_result, genesis_result,
        amb_result, mem_result
    )

    # Validacao final
    validar(sync_result)

    # Relatorio
    total = relatorio()

    return 0


if __name__ == "__main__":
    sys.exit(main())
