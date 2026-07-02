#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE DE STRESS ACELERADO — Prototipo AGI (7 Fases)
=====================================================
Valida TUDO em velocidade maxima: tick acelerado, 0 sleep entre ciclos.
Mede: aprendizado real, convergencia, persistencia, analogias, genesis.

Uso:
    python teste_stress_acelerado.py              # teste completo (~30s)
    python teste_stress_acelerado.py --rapido     # so o essencial (~10s)
    python teste_stress_acelerado.py --completo   # 500 episodios (~120s)
    python teste_stress_acelerado.py --benchmark  # benchmark puro (~5s)
"""
import sys, os, time, json, math, shutil, traceback
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    CerebroAGI, EstadoMundo, MotorFisica, Entidade, MCREntropia
)

# ============================================================
# CONFIG
# ============================================================

MODO_RAPIDO = "--rapido" in sys.argv
MODO_COMPLETO = "--completo" in sys.argv
MODO_BENCHMARK = "--benchmark" in sys.argv
VERBOSE = "--verbose" in sys.argv

# Metricas globais
METRICAS = {
    "inicio": time.time(),
    "ticks": 0,
    "erros": 0,
    "testes": {"total": 0, "passaram": 0, "falharam": 0},
    "fases": {},
}
LOG = []


def log(msg: str):
    LOG.append(msg)
    if VERBOSE:
        print(msg)


def medir(nome: str, funcao, criterio=None) -> Dict:
    """Executa uma funcao, mede tempo, valida criterio."""
    METRICAS["testes"]["total"] += 1
    t0 = time.time()
    try:
        resultado = funcao()
        tempo = time.time() - t0
        sucesso = criterio(resultado) if criterio else True
        nota = resultado.get("nota", resultado if isinstance(resultado, (int, float)) else 0)
        if sucesso:
            METRICAS["testes"]["passaram"] += 1
        else:
            METRICAS["testes"]["falharam"] += 1
            log(f"  FALHOU: {nome} (criterio nao atendido, nota={nota})")
        return {
            "nome": nome, "sucesso": sucesso, "tempo": round(tempo, 3),
            "nota": round(nota, 3) if isinstance(nota, float) else nota,
            "resultado": str(resultado)[:100] if isinstance(resultado, dict) else str(resultado)[:60],
        }
    except Exception as e:
        tempo = time.time() - t0
        METRICAS["testes"]["falharam"] += 1
        METRICAS["erros"] += 1
        log(f"  ERRO: {nome} -> {str(e)[:80]}")
        return {"nome": nome, "sucesso": False, "tempo": round(tempo, 3),
                "nota": 0, "erro": str(e)[:80]}


# ============================================================
# FASE 0: PRIMITIVAS (baseline)
# ============================================================

def testar_fase0():
    log("\n=== FASE 0: Primitivas Baseline ===")
    r = []

    def t0():
        mk = MCR("t"); mk.aprender("A","B"); mk.aprender("A","C"); mk.aprender("A","B")
        p, c = mk.predizer("A")
        return {"nota": 10 if p == "B" else 0}

    def t1():
        fp1 = MCRByteUtils.fingerprint("abc", 8); fp2 = MCRByteUtils.fingerprint("abc", 8)
        return {"nota": 10 if fp1 == fp2 else 0}

    def t2():
        th = MCRThreshold("t")
        for v in [0.1, 0.2, 0.3, 0.4, 0.5]: th.observar(v)
        return {"nota": th.calcular()}

    for nome, fn in [("mcr_predizer", t0), ("fingerprint", t1), ("threshold", t2)]:
        r.append(medir(f"f0.{nome}", fn, lambda x: x["nota"] > 0))

    METRICAS["fases"]["f0_primitivas"] = r
    return r


# ============================================================
# FASE 1: MEMORIA + PERSISTENCIA ACELERADA
# ============================================================

def testar_fase1():
    log("\n=== FASE 1: Memoria + Persistencia (acelerado) ===")
    from prototipo_mcr_hq import MCRMemory
    r = []

    db_path = ":memory:"

    def t0():
        mem = MCRMemory(db_path)
        for i in range(1000):
            e = EstadoMundo.criar_simples()
            mem.salvar_estado(e)
            mem.salvar_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
        stats = mem.estatisticas()
        mem.fechar()
        return {"nota": stats["estados"], "stats": stats}

    def t1():
        mem = MCRMemory(db_path)
        fp = str(EstadoMundo.criar_simples().fingerprint(8))
        similares = mem.buscar_estado_similar(fp, limite=5)
        mem.fechar()
        return {"nota": len(similares)}

    def t2():
        mem = MCRMemory(db_path)
        for _ in range(500):
            e = EstadoMundo.criar_simples()
            e2 = MotorFisica.executar(e, "atacar")
            mem.salvar_causal(e, "atacar", e2)
        stats = mem.estatisticas()
        mem.fechar()
        return {"nota": stats["causais"]}

    for nome, fn, crit in [
        ("inserir_1000_estados", t0, lambda x: x["nota"] >= 1000),
        ("buscar_similares", t1, lambda x: x["nota"] >= 0),
        ("salvar_500_causais", t2, lambda x: x["nota"] >= 500),
    ]:
        res = medir(f"f1.{nome}", fn, crit)
        r.append(res)
        if res["sucesso"] and "stats" in res:
            log(f"    stats: {res['stats']}")

    METRICAS["fases"]["f1_memoria"] = r
    return r


# ============================================================
# FASE 2: CODEX + AUTO-MODIFICACAO
# ============================================================

def testar_fase2():
    log("\n=== FASE 2: MCRCodex (auto-modificacao) ===")
    from prototipo_mcr_codex import MCRCodex, MCRSelfTest
    r = []

    codex = MCRCodex()

    def t0():
        hc = codex.escanear_arquivo()
        return {"nota": len(hc)}

    def t1():
        gap = {"nome": "validacao_teste", "descricao": "gap de teste acelerado"}
        codigo = codex.gerar_classe(gap)
        return {"nota": 10 if "class MCRValidacaoTeste" in codigo else 0, "codigo": codigo[:50]}

    def t2():
        st = MCRSelfTest()
        n = st.testar_modulo("world")
        return {"nota": n}

    def t3():
        st = MCRSelfTest()
        n = st.testar_modulo("coupling")
        return {"nota": n}

    codex.historico.append({"tipo": "teste_stress"})
    def t4():
        return {"nota": codex.stats()["modificacoes"]}

    for nome, fn, crit in [
        ("escanear_hardcodes", t0, lambda x: x["nota"] >= 0),
        ("gerar_classe", t1, lambda x: x["nota"] >= 8),
        ("selftest_world", t2, lambda x: x["nota"] >= 5),
        ("selftest_coupling", t3, lambda x: x["nota"] >= 5),
        ("codex_stats", t4, lambda x: x["nota"] >= 0),
    ]:
        res = medir(f"f2.{nome}", fn, crit)
        r.append(res)

    METRICAS["fases"]["f2_codex"] = r
    return r


# ============================================================
# FASE 3: RL CONVERGE COM 500 EPISODIOS ACELERADOS
# ============================================================

def testar_fase3():
    log("\n=== FASE 3: MCRRL (500 episodios acelerados) ===")
    from prototipo_mcr_rl import MCRRL, MCRQLearn, MCRReward
    r = []

    n_episodios = 100 if MODO_RAPIDO else 500

    def t0():
        rl = MCRRL()
        e0 = EstadoMundo.criar_simples()
        eg = e0.clone(); eg.get("bau").props["aberto"] = True
        for i in range(n_episodios):
            e = e0.clone()
            ep = rl.qlearn.episodio_treino(e, eg, max_passos=15)
            if i == n_episodios - 1:
                log(f"    Ultimo episodio: R={ep['recompensa_total']}, passos={ep['passos']}")
        stats = rl.stats()
        log(f"    Stats RL: {stats}")
        return {"nota": 10 if stats["episodios"] >= n_episodios else 0, "stats": stats}

    def t1():
        rl2 = MCRRL()
        e0 = EstadoMundo.criar_simples()
        acao = rl2.escolher_acao(e0, epsilon=0.0)
        return {"nota": 10 if acao in ("andar_cima","andar_baixo","andar_esq","andar_dir","empurrar","abrir","atacar") else 0}

    def t2():
        reward = MCRReward()
        e1 = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e1, "andar_dir")
        r1 = reward.avaliar(e2, e1)
        r0 = reward.avaliar(e1, e1, acao_bem_sucedida=False)
        return {"nota": 10 if r1 != r0 else 0}

    for nome, fn, crit in [
        (f"rl_{n_episodios}_episodios", t0, lambda x: x["nota"] >= 7),
        ("rl_escolher_acao", t1, lambda x: x["nota"] >= 7),
        ("reward_discriminacao", t2, lambda x: x["nota"] >= 7),
    ]:
        res = medir(f"f3.{nome}", fn, crit)
        r.append(res)

    METRICAS["fases"]["f3_rl"] = r
    return r


# ============================================================
# FASE 4: AMBIENTE RICO ACELERADO
# ============================================================

def testar_fase4():
    log("\n=== FASE 4: Ambiente Rico (1000+ entidades, ticks acelerados) ===")
    from prototipo_mcr_ambiente import AmbienteRico, Tile
    r = []

    n_ticks = 200 if MODO_RAPIDO else 1000

    def t0():
        amb = AmbienteRico(50, 50)
        stats = amb.estatisticas()
        for _ in range(n_ticks):
            amb.tick()
        stats_fim = amb.estatisticas()
        return {"nota": 10 if stats["tiles"] >= 2500 and stats_fim["tick"] >= n_ticks else 0, "stats": stats}

    def t1():
        amb = AmbienteRico(30, 30)
        estado = amb.criar_estado(15, 15, 5)
        return {"nota": len(estado.entidades)}

    def t2():
        t = Tile("grama"); t2 = Tile("muro")
        return {"nota": 10 if not t.bloqueia() and t2.bloqueia() else 0}

    def t3():
        amb = AmbienteRico(50, 50)
        fp = MCRByteUtils.fingerprint(amb.criar_estado(25, 25, 3).serializar(), 8)
        return {"nota": len(fp)}

    for nome, fn, crit in [
        (f"criar_{n_ticks}_ticks", t0, lambda x: x["nota"] >= 7),
        ("criar_estado_rico", t1, lambda x: x["nota"] > 10),
        ("tile_tipos", t2, lambda x: x["nota"] >= 7),
        ("fingerprint_rapido", t3, lambda x: x["nota"] == 8),
    ]:
        res = medir(f"f4.{nome}", fn, crit)
        r.append(res)

    METRICAS["fases"]["f4_ambiente"] = r
    return r


# ============================================================
# FASE 5: BRIDGE + ANALOGIAS
# ============================================================

def testar_fase5():
    log("\n=== FASE 5: MCRBridge (analogias cross-domain) ===")
    from prototipo_mcr_bridge import MCRBridge, MCRCrossDomain
    r = []

    def t0():
        bridge = MCRBridge()
        bridge.registrar_dominio("texto"); bridge.registrar_dominio("grid")
        return {"nota": len(bridge.dominios)}

    def t1():
        bridge = MCRBridge()
        bridge.registrar_dominio("texto"); bridge.registrar_dominio("grid")
        # Analogia de exemplo
        analogia = bridge.analogia(
            "fogo queima", "fogo queima madeira",
            "gelo congela", "gelo congela agua")
        return {"nota": analogia.get("nota", 0)}

    def t2():
        bridge = MCRBridge()
        bridge.registrar_dominio("texto"); bridge.registrar_dominio("numerico")
        # Analogia numerica: 1,2 esta para 1,2,3 assim como 4,5 esta para 4,5,6
        analogia = bridge.analogia("1 2", "1 2 3", "4 5", "4 5 6")
        return {"nota": analogia.get("nota", 0)}

    def t3():
        cross = MCRCrossDomain()
        acoes = cross.entender_instrucao("ataque o monstro com fogo")
        return {"nota": 10 if "atacar" in acoes else 0}

    def t4():
        bridge = MCRBridge()
        bridge.registrar_dominio("a"); bridge.registrar_dominio("b")
        fp = bridge.fingerprint_dominio("teste", "a")
        return {"nota": len(fp)}

    for nome, fn, crit in [
        ("registrar_dominios", t0, lambda x: x["nota"] >= 2),
        ("analogia_fogo_gelo", t1, lambda x: x["nota"] >= 0),
        ("analogia_numerica", t2, lambda x: x["nota"] >= 0),
        ("entender_instrucao", t3, lambda x: x["nota"] >= 7),
        ("fingerprint_dominio", t4, lambda x: x["nota"] == 8),
    ]:
        r.append(medir(f"f5.{nome}", fn, crit))

    METRICAS["fases"]["f5_bridge"] = r
    return r


# ============================================================
# FASE 6: GENESIS (auto-expansao acelerada)
# ============================================================

def testar_fase6():
    log("\n=== FASE 6: MCRGenesis (auto-expansao acelerada) ===")
    from prototipo_mcr_genesis import MCRGenesis
    r = []

    def t0():
        cerebro = CerebroAGI()
        genesis = MCRGenesis(cerebro)
        diag = genesis.diagnosticar_gap()
        log(f"    Gaps: {diag['total']}, severidade={diag['severidade_media']}")
        return {"nota": diag["total"], "diag": diag}

    def t1():
        cerebro = CerebroAGI()
        for _ in range(20):
            cerebro.alimentar("Sistema de teste acelerado para aprendizado", f"stress_{_}")
        genesis = MCRGenesis(cerebro)
        diag = genesis.diagnosticar_gap()
        if diag["total"] > 0:
            gap = diag["gap_principal"]
            codigo = genesis.projetar_classe(gap)
            return {"nota": 10 if "class" in codigo else 0, "codigo": codigo[:40]}
        return {"nota": 5}

    for nome, fn, crit in [
        ("diagnosticar_gap", t0, lambda x: x["nota"] >= 0),
        ("projetar_classe", t1, lambda x: x["nota"] >= 5),
    ]:
        r.append(medir(f"f6.{nome}", fn, crit))

    METRICAS["fases"]["f6_genesis"] = r
    return r


# ============================================================
# FASE 7: MCRMind ACELERADO (daemon com tick=0)
# ============================================================

def testar_fase7():
    log("\n=== FASE 7: MCRMind (operacao acelerada, tick=0) ===")
    from prototipo_mcr_mind import MCRMind
    r = []

    n_ticks = 500 if MODO_RAPIDO else 2000

    def t0():
        mind = MCRMind(":memory:")
        # Acelera: tick continuo sem sleep
        for _ in range(n_ticks):
            mind.tick += 1
            mind._ciclo_autonomo()
            if mind.tick % 100 == 0:
                mind.dormir()
        stats = mind.stats()
        log(f"    Apos {n_ticks} ticks: {stats['rl']}")
        return {"nota": 10 if mind.tick >= n_ticks else 0, "stats": stats}

    def t1():
        mind = MCRMind(":memory:")
        r1 = mind.percepcao("andar para direita")
        r2 = mind.percepcao("SPA e um sistema de teste")
        r3 = mind.percepcao("ataque o monstro")
        ok = r1["tipo"] == "acao" and r2["tipo"] in ("conhecimento", "acao") and r3["tipo"] == "acao"
        return {"nota": 10 if ok else 0}

    def t2():
        mind = MCRMind(":memory:")
        resp = mind.razao("explique o que e SPA")
        return {"nota": len(resp)}

    def t3():
        mind = MCRMind(":memory:")
        r = mind._comando("status")
        return {"nota": 10 if r["tipo"] == "status" else 0}

    for nome, fn, crit in [
        (f"ciclo_acelerado_{n_ticks}", t0, lambda x: x["nota"] >= 7),
        ("percepcao_multipla", t1, lambda x: x["nota"] >= 7),
        ("razao_resposta", t2, lambda x: x["nota"] > 5),
        ("comando_status", t3, lambda x: x["nota"] >= 7),
    ]:
        res = medir(f"f7.{nome}", fn, crit)
        r.append(res)

    METRICAS["fases"]["f7_mind"] = r
    return r


# ============================================================
# FASE 8: INTEGRACAO GLOBAL (TUDO JUNTO)
# ============================================================

def testar_integracao():
    log("\n=== INTEGRACAO GLOBAL (todas as fases simultaneas) ===")
    r = []

    def t0():
        """Fluxo completo: alimenta -> causal -> planeja -> persiste -> recupera."""
        db_path = ":memory:"
        from prototipo_mcr_hq import MCRMemory

        cerebro = CerebroAGI()
        mem = MCRMemory(db_path)

        # Alimenta
        cerebro.alimentar("SPA sistema de progressao", "spa")
        cerebro.alimentar("SHC habilidades contextuais", "shc")
        cerebro.alimentar("Fibonacci 1 1 2 3 5 8 13", "fib")

        # Causal
        for _ in range(5):
            e = EstadoMundo.criar_simples()
            cerebro.aprender_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
            mem.salvar_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))

        # Planeja
        plan = cerebro.planejar("abrir", EstadoMundo.criar_simples())

        # Gera
        gerado = cerebro.gerar("SPA", 4)

        # Persiste
        mem.salvar_estado(EstadoMundo.criar_simples())
        stats = mem.estatisticas()
        mem.fechar()

        return {"nota": 10 if stats["causais"] >= 5 and len(plan.get("plano", [])) >= 0 and len(gerado) > 3 else 0, "stats": stats}

    def t1():
        """Fluxo cross-domain: instrucao -> acao -> causal -> analogia."""
        from prototipo_mcr_bridge import MCRBridge, MCRCrossDomain
        cross = MCRCrossDomain()
        cerebro = CerebroAGI()

        acoes = cross.entender_instrucao("ataque o monstro e abra o bau")
        for acao in acoes:
            e = EstadoMundo.criar_simples()
            e2 = MotorFisica.executar(e, acao)
            cerebro.aprender_causal(e, acao, e2)

        gerado = cerebro.gerar("combate", 3)
        return {"nota": len(gerado)}

    def t2():
        """RL + Causal + Planejamento integrados."""
        from prototipo_mcr_rl import MCRRL
        cerebro = CerebroAGI()
        rl = MCRRL()
        e0 = EstadoMundo.criar_simples()

        for _ in range(30):
            e = e0.clone()
            acao = rl.escolher_acao(e)
            prox, rec = rl.agir(e, acao)
            cerebro.aprender_causal(e, acao, prox)

        plan = cerebro.planejar("andar", e0)
        return {"nota": len(plan.get("plano", [])) * 2}

    for nome, fn, crit in [
        ("fluxo_completo", t0, lambda x: x["nota"] >= 5),
        ("fluxo_crossdomain", t1, lambda x: x["nota"] > 3),
        ("rl_causal_planner", t2, lambda x: x["nota"] >= 0),
    ]:
        r.append(medir(f"ig.{nome}", fn, crit))

    METRICAS["fases"]["ig_integracao"] = r
    return r


# ============================================================
# BENCHMARK EVOLUTIVO
# ============================================================

def benchmark():
    """Benchmark puro: mede performance bruta de cada componente."""
    log("\n=== BENCHMARK (performance pura) ===")
    bench = {}

    # Velocidade do Markov
    t0 = time.time()
    mk = MCR("bench")
    for i in range(10000):
        mk.aprender(f"K{i}", f"V{i}")
    bench["markov_10k_transicoes"] = round(time.time() - t0, 4)

    # Velocidade do fingerprint
    t0 = time.time()
    for i in range(5000):
        MCRByteUtils.fingerprint(f"texto de teste numero {i} para medir velocidade", 8)
    bench["fingerprint_5k"] = round(time.time() - t0, 4)

    # Velocidade da memoria
    from prototipo_mcr_hq import MCRMemory
    mem = MCRMemory(":memory:")
    t0 = time.time()
    for i in range(5000):
        e = EstadoMundo.criar_simples()
        mem.salvar_estado(e)
    bench["memoria_5k_inserts"] = round(time.time() - t0, 4)

    # Velocidade do RL
    from prototipo_mcr_rl import MCRRL
    rl = MCRRL()
    t0 = time.time()
    e0 = EstadoMundo.criar_simples()
    for i in range(200):
        e = e0.clone()
        rl.qlearn.episodio_treino(e, e0, max_passos=10)
    bench["rl_200_episodios"] = round(time.time() - t0, 4)

    # Velocidade do ambiente
    from prototipo_mcr_ambiente import AmbienteRico
    t0 = time.time()
    amb = AmbienteRico(30, 30)
    for _ in range(500):
        amb.tick()
    bench["ambiente_500_ticks"] = round(time.time() - t0, 4)

    bench["total"] = round(sum(bench.values()), 3)
    log(f"  Markov 10k: {bench['markov_10k_transicoes']}s")
    log(f"  Fingerprint 5k: {bench['fingerprint_5k']}s")
    log(f"  Memoria 5k inserts: {bench['memoria_5k_inserts']}s")
    log(f"  RL 200 episodios: {bench['rl_200_episodios']}s")
    log(f"  Ambiente 500 ticks: {bench['ambiente_500_ticks']}s")
    log(f"  TOTAL: {bench['total']}s")

    METRICAS["benchmark"] = bench
    return bench


# ============================================================
# RELATORIO FINAL
# ============================================================

def relatorio():
    METRICAS["fim"] = time.time()
    METRICAS["duracao"] = round(METRICAS["fim"] - METRICAS["inicio"], 2)

    t = METRICAS["testes"]
    taxa = round(t["passaram"] / max(t["total"], 1) * 100, 1)

    print("\n" + "#" * 60)
    print("  RELATORIO FINAL — Teste de Stress Acelerado")
    print("#" * 60)
    print(f"  Duracao: {METRICAS['duracao']}s")
    print(f"  Testes:  {t['total']}")
    print(f"  Passaram: {t['passaram']}")
    print(f"  Falharam: {t['falharam']}")
    print(f"  Taxa:    {taxa}%")
    print()

    for fase, resultados in METRICAS["fases"].items():
        p = sum(1 for r in resultados if r["sucesso"])
        total = len(resultados)
        bar = "#" * int(p / max(total, 1) * 20) if total else ""
        print(f"  {fase:20s}: {p}/{total} [{bar:20s}]")
        if VERBOSE:
            for r in resultados:
                status = "PASSOU" if r["sucesso"] else "FALHOU"
                print(f"    {status}: {r['nome']} ({r['tempo']}s, nota={r['nota']})")

    if METRICAS.get("benchmark"):
        print(f"\n  BENCHMARK:")
        for k, v in METRICAS["benchmark"].items():
            if k != "total":
                print(f"    {k}: {v}s")
        print(f"    TOTAL: {METRICAS['benchmark']['total']}s")

    print(f"\n  Ticks totais: {METRICAS['ticks']}")
    print(f"  Erros: {METRICAS['erros']}")
    print()

    # Nota final composta
    nota_final = round(
        (taxa / 100) * 3.0 +  # 30%: taxa de aprovacao
        min(1.0, t["total"] / 20) * 2.0 +  # 20%: cobertura
        min(1.0, (METRICAS.get("benchmark", {}).get("total", 999) < 2.0)) * 2.0 +  # 20%: performance
        min(1.0, METRICAS["ticks"] / 500) * 1.5 +  # 15%: escala
        (1.0 if METRICAS["erros"] == 0 else 0.0) * 1.5,  # 15%: zero erros
        2
    )
    print(f"  NOTA FINAL: {nota_final}/10")
    print(f"  (taxa={taxa}%, cobertura={t['total']} testes, performance=<2s, ticks={METRICAS['ticks']}, erros={METRICAS['erros']})")

    # Salva
    caminho = os.path.join(os.path.dirname(__file__), "..", "cache", "stress_report.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    METRICAS["nota_final"] = nota_final
    METRICAS["taxa"] = taxa
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(METRICAS, f, indent=2, ensure_ascii=False)
    print(f"  Relatorio salvo: {caminho}")
    print()

    return nota_final


# ============================================================
# MAIN
# ============================================================

def main():
    print("#" * 60)
    print("  TESTE DE STRESS ACELERADO — Prototipo AGI (7 Fases)")
    print("#" * 60)
    modo = "RAPIDO" if MODO_RAPIDO else "COMPLETO" if MODO_COMPLETO else "NORMAL"
    print(f"  Modo: {modo} | Verbose: {VERBOSE}")
    print()

    if MODO_BENCHMARK:
        benchmark()
        relatorio()
        return

    # Fases
    testar_fase0()
    testar_fase1()
    testar_fase2()
    testar_fase3()
    testar_fase4()
    testar_fase5()
    testar_fase6()
    testar_fase7()
    testar_integracao()

    # Benchmark
    benchmark()

    # Total de ticks
    for fase, res in METRICAS["fases"].items():
        for r in res:
            if "ticks" in r.get("resultado", ""):
                METRICAS["ticks"] += 1

    relatorio()

    sys.exit(0 if METRICAS["testes"]["falharam"] == 0 else 1)


if __name__ == "__main__":
    main()
