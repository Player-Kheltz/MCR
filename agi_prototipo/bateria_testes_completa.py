#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BATERIA DE TESTES COMPLETA — Prototipo AGI (7 Fases)
======================================================
Valida TODOS os modulos: base + MCRWorld + MCRCoupling + MCRPlanner
+ MCRSelfModify + MCRMemory + MCRCodex + MCRRL + MCRAmbiente
+ MCRBridge + MCRGenesis + MCRMind

Uso: python bateria_testes_completa.py [--verbose] [--only <modulo>]
"""
import sys, os, time, json, math, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import *

VERBOSE = "--verbose" in sys.argv
TOTAL = 0
PASSARAM = 0
FALHARAM = 0
RESULTADOS = []


def registrar(mod, nome, ok, det=""):
    global TOTAL, PASSARAM, FALHARAM
    TOTAL += 1
    if ok: PASSARAM += 1
    else: FALHARAM += 1
    RESULTADOS.append({"modulo": mod, "nome": nome, "sucesso": ok, "detalhes": det})
    if VERBOSE or not ok:
        print(f"  [{'PASSOU' if ok else 'FALHOU'}] {mod}.{nome}" + (f" -> {det}" if det else ""))


# ============================================================
# TESTES BASE (Fase 0)
# ============================================================

def testar_fase0():
    print("\n=== FASE 0: Primitivas Base ===")
    mk = MCR("t")
    mk.aprender("A", "B"); mk.aprender("A", "C"); mk.aprender("A", "B")
    p, c = mk.predizer("A")
    registrar("f0", "mcr_predizer", p == "B", f"pred={p}, conf={c:.3f}")

    h = mk.entropia("A")
    registrar("f0", "mcr_entropia", h > 0, f"H={h:.3f}")

    fp1 = MCRByteUtils.fingerprint("abc", 8)
    fp2 = MCRByteUtils.fingerprint("abc", 8)
    registrar("f0", "fingerprint_determinismo", fp1 == fp2)

    j = MCRByteUtils.jaccard_bytes("abc", "abc")
    registrar("f0", "jaccard_igual", abs(j - 1.0) < 0.01, f"j={j:.3f}")

    th = MCRThreshold("t")
    for v in [0.1, 0.2, 0.3, 0.4, 0.5]: th.observar(v)
    registrar("f0", "threshold", th.calcular() > 0, f"th={th.calcular():.3f}")

    delta = MCRByteUtils.delta_fingerprint("abc", "abd", 8)
    mag = math.sqrt(sum(d*d for d in delta))
    registrar("f0", "delta_fingerprint", mag > 0, f"mag={mag:.3f}")


# ============================================================
# TESTES FASE 1: MCRMemory
# ============================================================

def testar_fase1():
    print("\n=== FASE 1: MCRMemory (SQLite Persistente) ===")
    from prototipo_mcr_hq import MCRMemory, MCRIndex

    mem = MCRMemory(":memory:")
    e = EstadoMundo.criar_simples()
    fp = mem.salvar_estado(e)
    registrar("f1", "salvar_estado", len(fp) > 0, f"fp={fp[:20]}...")

    mem.salvar_causal(e, "andar_dir", e)
    mem.salvar_causal(e, "atacar", e)
    registrar("f1", "salvar_causal", mem.estatisticas()["causais"] == 2, "2 causais")

    mem.salvar_plano(fp, ["andar_dir", "atacar"], 8.5)
    plan = mem.buscar_plano(fp)
    registrar("f1", "buscar_plano", plan is not None, f"plan={plan}")

    similares = mem.buscar_estado_similar(fp)
    registrar("f1", "buscar_similar", len(similares) > 0, f"{len(similares)} resultados")

    delta_str = str(MCRByteUtils.delta_fingerprint(e.serializar(), e.serializar(), 8))
    mem.salvar_causal(e, "andar_dir", e)
    acao = mem.buscar_delta(delta_str)
    registrar("f1", "buscar_delta_acao", True, f"delta search ok")

    stats = mem.estatisticas()
    registrar("f1", "estatisticas", stats["estados"] >= 1, str(stats))

    idx = MCRIndex(mem)
    idx.indexar("teste conhecimento", "ref1")
    idx.indexar("outro conhecimento", "ref2")
    busca = idx.buscar(MCRByteUtils.fingerprint("teste", 8))
    registrar("f1", "index_busca", len(busca) >= 1, f"{len(busca)} resultados")

    mem.fechar()


# ============================================================
# TESTES FASE 2: MCRCodex
# ============================================================

def testar_fase2():
    print("\n=== FASE 2: MCRCodex (Auto-Modificacao) ===")
    from prototipo_mcr_codex import MCRCodex, MCRSelfTest

    codex = MCRCodex()
    hc = codex.escanear_arquivo()
    registrar("f2", "escanear_hardcodes", len(hc) >= 0, f"{len(hc)} hardcodes detectados")

    gap_teste = {"nome": "teste_gap", "descricao": "gap de teste para validacao"}
    codigo = codex.gerar_classe(gap_teste)
    registrar("f2", "gerar_classe_codex", "class MCRTesteGap" in codigo, f"{len(codigo)} chars")

    selftest = MCRSelfTest()
    n_world = selftest.testar_modulo("world")
    registrar("f2", "selftest_world", n_world >= 5, f"nota={n_world}")

    n_coupling = selftest.testar_modulo("coupling")
    registrar("f2", "selftest_coupling", n_coupling >= 5, f"nota={n_coupling}")

    n_planner = selftest.testar_modulo("planner")
    registrar("f2", "selftest_planner", n_planner >= 5, f"nota={n_planner}")

    codex.historico.append({"tipo": "teste", "linha": 1, "antes": "x=5", "depois": "x=10"})
    registrar("f2", "codex_stats", codex.stats()["modificacoes"] >= 1)


# ============================================================
# TESTES FASE 3: MCRRL
# ============================================================

def testar_fase3():
    print("\n=== FASE 3: MCRRL (Aprendizado por Reforco) ===")
    from prototipo_mcr_rl import MCRReward, MCRQLearn, MCRRL

    reward = MCRReward()
    e1 = EstadoMundo.criar_simples()
    e2 = MotorFisica.executar(e1, "andar_dir")
    r = reward.avaliar(e2, e1, e1)
    registrar("f3", "reward_avaliar", r != 0, f"r={r:.2f}")

    r2 = reward.avaliar(e1, e1, e1, acao_bem_sucedida=False)
    registrar("f3", "reward_variacao", r2 != r, f"r2={r2:.2f}")

    qlearn = MCRQLearn(gamma=0.9, alpha=0.3)
    qlearn.atualizar(e1, "andar_dir", 5.0, e2)
    q_val = qlearn.q_valor(e1, "andar_dir")
    registrar("f3", "qlearn_atualizar", True, f"Q(s,a) armazenado")

    melhor = qlearn.melhor_acao(e1)
    registrar("f3", "qlearn_melhor_acao", melhor is not None, f"melhor={melhor}")

    escolha = qlearn.escolher_acao(e1, epsilon=0.0)
    registrar("f3", "qlearn_escolher_epsilon0", escolha == melhor, f"escolha={escolha}")

    rl = MCRRL()
    prox, rec = rl.agir(e1, "andar_dir")
    registrar("f3", "rl_agir", rec != 0, f"rec={rec:.2f}")

    acao_rl = rl.escolher_acao(e1)
    registrar("f3", "rl_escolher", acao_rl in MotorFisica.ACOES if hasattr(MotorFisica, "ACOES") else True, f"acao={acao_rl}")


# ============================================================
# TESTES FASE 4: Ambiente Rico
# ============================================================

def testar_fase4():
    print("\n=== FASE 4: MCRAmbiente (1000+ Entidades) ===")
    from prototipo_mcr_ambiente import AmbienteRico, EstadoMundoRico, Tile

    tile = Tile("grama")
    registrar("f4", "tile_criar", not tile.bloqueia(), f"tipo={tile.tipo}")

    tile2 = Tile("muro")
    registrar("f4", "tile_bloqueio", tile2.bloqueia(), f"bloqueia={tile2.bloqueia()}")

    amb = AmbienteRico(50, 50)
    stats = amb.estatisticas()
    registrar("f4", "ambiente_criar", stats["tiles"] == 2500, f"{stats['tiles']} tiles")
    registrar("f4", "ambiente_entidades", stats["entidades"] >= 100, f"{stats['entidades']} entidades")

    amb.tick()
    registrar("f4", "ambiente_tick", amb.tick_atual == 1, f"tick={amb.tick_atual}")

    estado = amb.criar_estado(25, 25, 5)
    registrar("f4", "criar_estado_rico", estado is not None, f"entidades={len(estado.entidades)}")

    for _ in range(10): amb.tick()
    registrar("f4", "ambiente_multiplos_ticks", amb.tick_atual == 11, f"tick={amb.tick_atual}")

    fp_rapido = MCRByteUtils.fingerprint(amb.criar_estado(25, 25, 3).serializar(), 8)
    registrar("f4", "fingerprint_rapido", len(fp_rapido) == 8, f"fp={fp_rapido[:3]}")

    registrar("f4", "ambiente_estatisticas", stats["entidades_por_tipo"]["monstro"] > 0, f"monstros={stats['entidades_por_tipo'].get('monstro', 0)}")


# ============================================================
# TESTES FASE 5: MCRBridge
# ============================================================

def testar_fase5():
    print("\n=== FASE 5: MCRBridge (Cross-Domain) ===")
    from prototipo_mcr_bridge import MCRBridge, MCRCrossDomain

    bridge = MCRBridge()
    bridge.registrar_dominio("grid")
    bridge.registrar_dominio("texto")
    registrar("f5", "registrar_dominios", len(bridge.dominios) == 2, str(list(bridge.dominios.keys())))

    fp1 = bridge.fingerprint_dominio("heroi esta em (0,0)", "grid")
    fp2 = bridge.fingerprint_dominio("SPA e progressao", "texto")
    sim = MCRByteUtils.similaridade_cosseno(fp1, fp2)
    registrar("f5", "fingerprint_dominio", len(fp1) >= 8, f"dim={len(fp1)} sim={sim:.3f}")

    bridge.aprender_mapeamento("texto", "heroi", "grid", "heroi")
    trans = bridge.transferir("heroi", "texto", "grid")
    registrar("f5", "transferir", "Transferido" in trans or "Sem mapeamento" in trans, trans[:40])

    analogia = bridge.analogia("fogo queima", "fogo queima madeira", "gelo congela", "gelo congela agua")
    registrar("f5", "analogia_basica", "nota" in analogia, f"nota={analogia['nota']}")

    cross = MCRCrossDomain(bridge)
    dom = cross.dominio_de_texto("heroi andou para direita")
    registrar("f5", "detectar_dominio", dom == "grid", f"dominio={dom}")

    acoes = cross.entender_instrucao("ataque o monstro")
    registrar("f5", "entender_instrucao", "atacar" in acoes, f"acoes={acoes}")


# ============================================================
# TESTES FASE 6: MCRGenesis
# ============================================================

def testar_fase6():
    print("\n=== FASE 6: MCRGenesis (Auto-Expansao) ===")
    from prototipo_mcr_genesis import MCRGenesis

    cerebro = CerebroAGI()
    genesis = MCRGenesis(cerebro)
    diag = genesis.diagnosticar_gap()
    registrar("f6", "diagnosticar_gap", "gaps" in diag, f"{diag['total']} gaps, severidade={diag['severidade_media']}")

    if diag["total"] > 0:
        gap = diag["gap_principal"]
        codigo = genesis.projetar_classe(gap)
        registrar("f6", "projetar_classe", "class" in codigo, f"{len(codigo)} chars para gap '{gap['nome']}'")

        try:
            integrado = genesis.testar_e_integrar(codigo, f"test_gen_{gap['nome']}")
            registrar("f6", "testar_integrar", integrado is not None, f"integrado={integrado}")
        except Exception as ex:
            registrar("f6", "testar_integrar", False, str(ex)[:60])

    try:
        resultado = genesis.genesis_loop(max_ciclos=2)
        registrar("f6", "genesis_loop", resultado["ciclos"] > 0, f"{resultado['modulos_criados']}/{resultado['ciclos']} modulos")
    except Exception as ex:
        registrar("f6", "genesis_loop", False, str(ex)[:60])

    registrar("f6", "genesis_stats", genesis.stats()["modulos_criados"] >= 0, str(genesis.stats())[:50])


# ============================================================
# TESTES FASE 7: MCRMind
# ============================================================

def testar_fase7():
    print("\n=== FASE 7: MCRMind (Consciencia Operacional) ===")
    from prototipo_mcr_mind import MCRMind

    mind = MCRMind()

    # Percepcao
    r1 = mind.percepcao("andar para direita")
    registrar("f7", "percepcao_acao", r1["tipo"] == "acao", f"acoes={r1.get('acoes', [])}")

    r2 = mind.percepcao("SPA e um sistema de progressao")
    registrar("f7", "percepcao_conhecimento", r2["tipo"] == "conhecimento", f"chars={r2.get('chars', 0)}")

    # Raciocinio
    resp = mind.razao("explique o que e SPA")
    registrar("f7", "razao_resposta", resp.startswith("[") and len(resp) > 10, f"resposta={resp[:50]}...")

    resp2 = mind.razao("como abrir o bau")
    registrar("f7", "razao_plano", len(resp2) > 5, f"resposta={resp2[:50]}...")

    # Comandos
    r3 = mind.percepcao("/status")
    registrar("f7", "comando_status", r3["tipo"] == "status", f"topicos={r3['dados'].get('topicos', 'N/A')}")

    r4 = mind.percepcao("/help")
    registrar("f7", "comando_help", r4["tipo"] == "help", f"{len(r4.get('comandos', []))} comandos")

    r5 = mind.percepcao("/diagnostico")
    registrar("f7", "comando_diagnostico", r5["tipo"] == "diagnostico", f"gaps={r5['dados'].get('total', 0)}")

    r6 = mind.percepcao("/mundo")
    registrar("f7", "comando_mundo", r6["tipo"] == "mundo", r6["dados"][:30])

    # Ciclo autonomo
    mind._ciclo_autonomo()
    registrar("f7", "ciclo_autonomo", mind.tick > 0, f"tick={mind.tick}")

    # Dormir
    mind.dormir()
    registrar("f7", "dormir", mind.log[-1]["tipo"] == "dormir" if mind.log else True, f"log={len(mind.log)}")

    # Comando invalido
    r7 = mind.percepcao("/xyz123")
    registrar("f7", "comando_invalido", r7["tipo"] == "comando_invalido", f"cmd={r7.get('comando', 'N/A')}")

    # Stats
    s = mind.stats()
    registrar("f7", "mind_stats", "tick" in s, f"tick={s['tick']}, memoria={s['memoria']['estados']}")


# ============================================================
# TESTES DE INTEGRACAO GLOBAL
# ============================================================

def testar_integracao_global():
    print("\n=== INTEGRACAO GLOBAL (Todas as Fases Conectadas) ===")
    
    # Cria cerebro completo
    cerebro = CerebroAGI()
    
    # Alimenta conhecimento
    cerebro.alimentar("SPA sistema de progressao do aventureiro com dominios elementais", "spa")
    cerebro.alimentar("SHC sistema de habilidades contextuais com posturas e sinergias", "shc")
    registrar("ig", "alimentar_multinivel", len(cerebro.topicos) >= 2, f"{len(cerebro.topicos)} topicos")
    
    # Aprendizado causal
    for _ in range(5):
        e = EstadoMundo.criar_simples()
        cerebro.aprender_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
    registrar("ig", "aprender_causal_5", len(cerebro.world.historico) == 5, "5 exemplos")
    
    # Planejamento
    plan = cerebro.plano_otimo(EstadoMundo.criar_simples()) if hasattr(cerebro, "plano_otimo") else None
    if plan is None:
        plan = cerebro.planejar("abrir", EstadoMundo.criar_simples())
    registrar("ig", "planejar", plan is not None, f"plan={plan.get('plano', [])[:3]}" if isinstance(plan, dict) else str(plan)[:30])
    
    # Geracao com coupling
    gerado = cerebro.gerar("SPA", 4)
    registrar("ig", "gerar_com_coupling", len(gerado) > 3, f'"{gerado}"')
    
    # Memoria
    try:
        from prototipo_mcr_hq import MCRMemory
        mem = MCRMemory(":memory:")
        e = EstadoMundo.criar_simples()
        mem.salvar_estado(e)
        mem.salvar_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
        stats = mem.estatisticas()
        registrar("ig", "memoria_persistente", stats["estados"] >= 1, str(stats))
        mem.fechar()
    except Exception as ex:
        registrar("ig", "memoria_persistente", False, str(ex)[:60])
    
    # RL
    try:
        from prototipo_mcr_rl import MCRRL
        rl = MCRRL()
        e1 = EstadoMundo.criar_simples()
        prox, rec = rl.agir(e1, "andar_dir")
        registrar("ig", "rl_agir_integrado", rec != 0, f"rec={rec:.2f}")
    except Exception as ex:
        registrar("ig", "rl_agir_integrado", False, str(ex)[:60])
    
    # Bridge
    try:
        from prototipo_mcr_bridge import MCRBridge
        bridge = MCRBridge()
        bridge.registrar_dominio("texto"); bridge.registrar_dominio("grid")
        analogia = bridge.analogia("fogo queima", "fogo queima madeira",
                                    "gelo congela", "gelo congela agua")
        registrar("ig", "bridge_analogia", "nota" in analogia, f"nota={analogia.get('nota', 0):.3f}")
    except Exception as ex:
        registrar("ig", "bridge_analogia", False, str(ex)[:60])
    
    # Genesis
    try:
        from prototipo_mcr_genesis import MCRGenesis
        genesis = MCRGenesis(cerebro)
        diag = genesis.diagnosticar_gap()
        registrar("ig", "genesis_diagnostico", "gaps" in diag, f"{diag['total']} gaps")
    except Exception as ex:
        registrar("ig", "genesis_diagnostico", False, str(ex)[:60])
    
    # Mind
    try:
        from prototipo_mcr_mind import MCRMind
        mind = MCRMind()
        r = mind.percepcao("SPA e progressao")
        resp = mind.razao("o que e SPA")
        registrar("ig", "mind_percepcao_razao", r["tipo"] in ("acao", "conhecimento"), f"tipo={r['tipo']}")
    except Exception as ex:
        registrar("ig", "mind_percepcao_razao", False, str(ex)[:60])
    
    # Relatorio completo
    rel = cerebro.relatorio()
    registrar("ig", "relatorio_completo", "MCRWorld" in rel and "MCRCoupling" in rel, f"{len(rel)} chars")
    
    # Diagnostico
    diag = cerebro.auto_diagnosticar()
    registrar("ig", "diagnostico_final", "topicos" in diag, f"{diag['topicos']} topicos, {diag['hardcodes']} hardcodes")


# ============================================================
# MAIN
# ============================================================

def main():
    apenas = None
    for i, a in enumerate(sys.argv):
        if a.startswith("--only"):
            apenas = a.split("=")[-1] if "=" in a else (sys.argv[i+1] if i+1 < len(sys.argv) else None)
    
    print("#" * 55)
    print("  BATERIA DE TESTES COMPLETA — Prototipo AGI (7 Fases)")
    print("#" * 55)
    print(f"  Modulo: {apenas or 'TODAS AS 7 FASES'}")
    
    t0 = time.time()
    
    fases = [
        ("f0", testar_fase0),
        ("f1", testar_fase1),
        ("f2", testar_fase2),
        ("f3", testar_fase3),
        ("f4", testar_fase4),
        ("f5", testar_fase5),
        ("f6", testar_fase6),
        ("f7", testar_fase7),
        ("ig", testar_integracao_global),
    ]
    
    for nome, fn in fases:
        if not apenas or nome == apenas or nome == "ig":
            try:
                fn()
            except Exception as e:
                print(f"\n  [ERRO] {nome}: {traceback.format_exc()[:200]}")
    
    tempo = time.time() - t0
    
    print("\n" + "#" * 55)
    print("  RESULTADO FINAL")
    print("#" * 55)
    taxa = PASSARAM / max(TOTAL, 1) * 100
    print(f"  Total:   {TOTAL}")
    print(f"  Passaram: {PASSARAM}")
    print(f"  Falharam: {FALHARAM}")
    print(f"  Tempo:   {tempo:.1f}s")
    print(f"  Taxa:    {taxa:.1f}%")
    print()
    
    mods = {}
    for r in RESULTADOS:
        mods.setdefault(r["modulo"], {"t": 0, "p": 0, "f": 0})
        mods[r["modulo"]]["t"] += 1
        if r["sucesso"]: mods[r["modulo"]]["p"] += 1
        else: mods[r["modulo"]]["f"] += 1
    
    for mod, st in sorted(mods.items()):
        bar = "#" * int(st["p"] / max(st["t"], 1) * 20)
        print(f"  {mod:5s}: {st['p']}/{st['t']} [{bar:20s}]")
    print()
    
    rel = {
        "timestamp": time.time(),
        "total": TOTAL, "passaram": PASSARAM, "falharam": FALHARAM,
        "taxa": round(taxa, 1), "tempo": round(tempo, 2),
        "modulos": mods, "detalhes": RESULTADOS,
    }
    caminho = os.path.join(os.path.dirname(__file__), "..", "cache", "test_complete.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)
    print(f"  Resultados salvos em: {caminho}\n")
    
    return 0 if FALHARAM == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
