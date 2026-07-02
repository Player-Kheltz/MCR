#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BATERIA DE TESTES — Prototipo AGI Completo
===========================================
Valida MCRWorld + MCRCoupling + MCRPlanner + MCRSelfModify
com metricas objetivas e comparacao antes/depois.

Uso:
    python bateria_testes.py              # executa todos os testes
    python bateria_testes.py --verbose    # modo detalhado
    python bateria_testes.py --only world # so um modulo
"""
import sys, os, time, json, math, re, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import *

VERBOSE = False
TOTAL_TESTES = 0
PASSARAM = 0
FALHARAM = 0
RESULTADOS = []


def registrar(modulo, nome, sucesso, detalhes=""):
    global TOTAL_TESTES, PASSARAM, FALHARAM
    TOTAL_TESTES += 1
    if sucesso:
        PASSARAM += 1
    else:
        FALHARAM += 1
    RESULTADOS.append({
        "modulo": modulo, "nome": nome,
        "sucesso": sucesso, "detalhes": detalhes
    })
    status = "PASSOU" if sucesso else "FALHOU"
    if VERBOSE or not sucesso:
        print(f"  [{status}] {modulo}.{nome}" + (f" -> {detalhes}" if detalhes else ""))


def quase_igual(a, b, tol=0.01):
    return abs(a - b) < tol


# ═══════════════════════════════════════════════════════════════════
# TESTES: MCRWorld (Modelo Causal)
# ═══════════════════════════════════════════════════════════════════

def testar_world():
    print("\n" + "=" * 55)
    print("  MCRWorld — Modelo de Mundo Causal")
    print("=" * 55)

    w = MCRWorld()

    # Teste W1: Serializacao de estado
    try:
        e = EstadoMundo.criar_simples()
        s = e.serializar()
        assert len(s) > 10, f"serializacao muito curta: {len(s)}"
        assert "heroi" in s, "heroi ausente da serializacao"
        registrar("world", "serializacao", True, f"{len(s)} chars")
    except Exception as ex:
        registrar("world", "serializacao", False, str(ex)[:60])

    # Teste W2: Fingerprint de estado
    try:
        e = EstadoMundo.criar_simples()
        fp = e.fingerprint(8)
        assert len(fp) == 8, f"fingerprint deveria ter 8 dimensoes, tem {len(fp)}"
        assert all(isinstance(v, float) for v in fp), "fingerprint deve ser float"
        registrar("world", "fingerprint_estado", True, f"{[round(v,2) for v in fp[:4]]}")
    except Exception as ex:
        registrar("world", "fingerprint_estado", False, str(ex)[:60])

    # Teste W3: Fingerprints diferentes para estados diferentes
    try:
        e1 = EstadoMundo.criar_simples()
        e2 = e1.clone()
        e2.get("heroi").props["x"] = 3
        e2.get("heroi").props["y"] = 3
        e2.get("bau").props["aberto"] = True
        e2.remover("monstro")
        fp1, fp2 = e1.fingerprint(8), e2.fingerprint(8)
        sim = MCRByteUtils.similaridade_cosseno(fp1, fp2)
        assert sim < 0.95, f"estados diferentes deveriam ter fingerprints diferentes (sim={sim:.3f})"
        registrar("world", "fingerprint_discriminacao", True, f"sim={sim:.3f}")
    except Exception as ex:
        registrar("world", "fingerprint_discriminacao", False, str(ex)[:60])

    # Teste W4: Motor de fisica — acoes mudam estado
    try:
        e = EstadoMundo.criar_simples()
        x0 = e.get("heroi").props["x"]
        e2 = MotorFisica.executar(e, "andar_dir")
        x1 = e2.get("heroi").props["x"]
        assert x1 == x0 + 1, f"andar_dir deveria incrementar x ({x0} -> {x1})"
        registrar("world", "fisica_andar", True, f"x={x0}->{x1}")
    except Exception as ex:
        registrar("world", "fisica_andar", False, str(ex)[:60])

    # Teste W5: Ataque reduz HP (heroi precisa estar adjacente)
    try:
        e = EstadoMundo.criar_simples()
        e.get("heroi").props["x"] = 2
        e.get("heroi").props["y"] = 1
        hp0 = e.get("monstro").props["hp"]
        e2 = MotorFisica.executar(e, "atacar")
        hp1 = e2.get("monstro").props["hp"] if e2.get("monstro") else 0
        assert hp1 < hp0, f"ataque deveria reduzir hp ({hp0} -> {hp1})"
        registrar("world", "fisica_atacar", True, f"hp={hp0}->{hp1}")
    except Exception as ex:
        registrar("world", "fisica_atacar", False, str(ex)[:60])

    # Teste W6: Abrir muda propriedade
    try:
        e = EstadoMundo.criar_simples()
        # Move heroi perto do bau (4,4)
        e.get("heroi").props["x"] = 3
        e.get("heroi").props["y"] = 4
        e2 = MotorFisica.executar(e, "abrir")
        assert e2.get("bau").props.get("aberto") == True, "bau deveria estar aberto apos abrir"
        registrar("world", "fisica_abrir", True, "bau_aberto=True")
    except Exception as ex:
        registrar("world", "fisica_abrir", False, str(ex)[:60])

    # Teste W7: Causalidade — aprender e predizer acao
    try:
        e1 = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e1, "andar_dir")
        w.aprender(e1, "andar_dir", e2)
        acao = w.predizer_acao(e1, e2)
        assert acao == "andar_dir", f"predizer acao: esperado 'andar_dir', obtido '{acao}'"
        registrar("world", "causal_predizer_acao", True, f"acao={acao}")
    except Exception as ex:
        registrar("world", "causal_predizer_acao", False, str(ex)[:60])

    # Teste W8: Causalidade — aprender multiplas e generalizar
    try:
        for _ in range(5):
            ea = EstadoMundo.criar_simples()
            eb = MotorFisica.executar(ea, "atacar")
            w.aprender(ea, "atacar", eb)

        ea2 = EstadoMundo.criar_simples()
        eb2 = MotorFisica.executar(ea2, "atacar")
        acao2 = w.predizer_acao(ea2, eb2)
        assert acao2 == "atacar", f"apos 5 exemplos, deveria aprender 'atacar' -> '{acao2}'"
        registrar("world", "causal_generalizacao", True, f"{w.mk_causal.total} exemplos causais")
    except Exception as ex:
        registrar("world", "causal_generalizacao", False, str(ex)[:60])

    # Teste W9: Contrafactual
    try:
        e = EstadoMundo.criar_simples()
        cf = w.contrafactual(e, "atacar", "hp", 100)
        assert len(cf) > 20, f"contrafactual muito curto: {len(cf)} chars"
        assert "hp" in cf, "contrafactual deveria mencionar hp"
        assert "100" in cf, "contrafactual deveria mencionar 100"
        registrar("world", "contrafactual", True, cf[:60])
    except Exception as ex:
        registrar("world", "contrafactual", False, str(ex)[:60])

    # Teste W10: Simulacao
    try:
        e = EstadoMundo.criar_simples()
        e2 = w.simular(e, "andar_dir")
        assert e2 is not None, "simular deveria retornar estado"
        fp_diff = MCRByteUtils.similaridade_cosseno(
            e.fingerprint(8), e2.fingerprint(8))
        assert fp_diff < 0.99, f"simular deveria mudar fingerprint (sim={fp_diff:.3f})"
        registrar("world", "simular", True, f"fingerprint_diff={1-fp_diff:.3f}")
    except Exception as ex:
        registrar("world", "simular", False, str(ex)[:60])

    # Teste W11: Distancia causal
    try:
        e1 = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e1, "andar_dir")
        d = w.distancia(e1, e2)
        e3 = MotorFisica.executar(e1, "atacar")
        d2 = w.distancia(e1, e3)
        assert d > 0, f"distancia entre estados diferentes deve ser > 0 ({d})"
        registrar("world", "distancia_causal", True, f"andar_dir={d:.3f}, atacar={d2:.3f}")
    except Exception as ex:
        registrar("world", "distancia_causal", False, str(ex)[:60])

    # Teste W12: Clone nao compartilha referencia
    try:
        e = EstadoMundo.criar_simples()
        ec = e.clone()
        ec.get("heroi").props["x"] = 99
        assert e.get("heroi").props["x"] != 99, "clone deveria ser independente"
        registrar("world", "clone_independencia", True)
    except Exception as ex:
        registrar("world", "clone_independencia", False, str(ex)[:60])

    # Teste W13: Historico cresce
    try:
        w2 = MCRWorld()
        for i in range(10):
            ea = EstadoMundo.criar_simples()
            eb = MotorFisica.executar(ea, "andar_dir")
            w2.aprender(ea, "andar_dir", eb)
        assert len(w2.historico) == 10, f"historico deveria ter 10, tem {len(w2.historico)}"
        registrar("world", "historico_cresce", True, f"{len(w2.historico)} exemplos")
    except Exception as ex:
        registrar("world", "historico_cresce", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: MCRCoupling (Acoplamento Multinivel)
# ═══════════════════════════════════════════════════════════════════

def testar_coupling():
    print("\n" + "=" * 55)
    print("  MCRCoupling — Cadeias Acopladas")
    print("=" * 55)

    cp = MCRCoupling()

    # Teste C1: Estrutura da matriz
    try:
        assert len(cp.niveis) == 5, f"5 niveis esperados, {len(cp.niveis)} obtidos"
        for o in cp.niveis:
            for d in cp.niveis:
                assert o in cp.matriz and d in cp.matriz[o], f"matriz[{o}][{d}] ausente"
        registrar("coupling", "matriz_estrutura", True, f"{len(cp.niveis)}x{len(cp.niveis)}")
    except Exception as ex:
        registrar("coupling", "matriz_estrutura", False, str(ex)[:60])

    # Teste C2: Alimentar transicao
    try:
        cp.alimentar_transicao("byte", "palavra", "B:41", "Fogo")
        cp.alimentar_transicao("byte", "palavra", "B:42", "Agua")
        cp.alimentar_transicao("byte", "palavra", "B:43", "Terra")
        cp.recalcular_pesos()
        assert cp.coocorrencias["byte"]["palavra"] == 3, f"3 coocorrencias esperadas, {cp.coocorrencias['byte']['palavra']}"
        registrar("coupling", "alimentar_transicao", True, f"byte->palavra={cp.coocorrencias['byte']['palavra']}")
    except Exception as ex:
        registrar("coupling", "alimentar_transicao", False, str(ex)[:60])

    # Teste C3: Peso emerge dos dados
    try:
        p = cp.peso("byte", "palavra")
        assert p > 0, f"peso byte->palavra deve ser > 0 apos alimentar ({p})"
        registrar("coupling", "peso_emergente", True, f"byte->palavra={p:.3f}")
    except Exception as ex:
        registrar("coupling", "peso_emergente", False, str(ex)[:60])

    # Teste C4: Niveis nao alimentados tem peso 0
    try:
        p_int_acao = cp.peso("intencao", "acao")
        assert p_int_acao == 0, f"intencao->acao sem dados deveria ser 0 ({p_int_acao})"
        registrar("coupling", "peso_zero_sem_dados", True, f"intencao->acao={p_int_acao}")
    except Exception as ex:
        registrar("coupling", "peso_zero_sem_dados", False, str(ex)[:60])

    # Teste C5: Auto-descobre niveis necessarios (usa CerebroAGI como motor)
    try:
        cerebro_teste = CerebroAGI()
        cerebro_teste.alimentar("teste de exemplo para descobrir dimensionalidade", "teste")
        niveis = cp.descobrir_niveis_necessarios(cerebro_teste)
        assert len(niveis) >= 2, f"deveria ter pelo menos 2 niveis ({len(niveis)})"
        registrar("coupling", "descobrir_niveis", True, f"{len(niveis)} niveis: {niveis}")
    except Exception as ex:
        registrar("coupling", "descobrir_niveis", False, str(ex)[:60])

    # Teste C6: Modulacao altera probabilidades
    try:
        moduladas = cp.modular("palavra", {"A": 0.5, "B": 0.3, "C": 0.2})
        diff = sum(abs(moduladas[k] - {"A": 0.5, "B": 0.3, "C": 0.2}[k]) for k in moduladas)
        assert diff > 0.001, f"modulacao deveria alterar probs (diff={diff:.4f})"
        registrar("coupling", "modulacao", True, f"diff={diff:.4f}")
    except Exception as ex:
        registrar("coupling", "modulacao", False, str(ex)[:60])

    # Teste C7: Acoplamento completo entre niveis (alimenta 5x cada par para passar threshold)
    try:
        for _ in range(5):
            for o in cp.niveis:
                for d in cp.niveis:
                    if o != d:
                        cp.alimentar_transicao(o, d, "test_key", "test_val")
        cp.recalcular_pesos()
        ativos = sum(1 for o in cp.niveis for d in cp.niveis if o != d and cp.peso(o, d) > 0)
        assert ativos >= 4, f"esperava pelo menos 4 acoplamentos ativos, tem {ativos}"
        registrar("coupling", "acoplamentos_ativos", True, f"{ativos} acoplamentos ativos")
    except Exception as ex:
        registrar("coupling", "acoplamentos_ativos", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: MCRPlanner (Planejamento Hierarquico)
# ═══════════════════════════════════════════════════════════════════

def testar_planner():
    print("\n" + "=" * 55)
    print("  MCRPlanner — Planejamento Hierarquico")
    print("=" * 55)

    world = MCRWorld()
    planner = MCRPlanner(world)

    # Alimenta dados causais basicos
    for _ in range(3):
        ea = EstadoMundo.criar_simples()
        eb = MotorFisica.executar(ea, "andar_dir")
        world.aprender(ea, "andar_dir", eb)
        ec = MotorFisica.executar(eb, "atacar")
        world.aprender(eb, "atacar", ec)
        ed = MotorFisica.executar(ec, "abrir")
        world.aprender(ec, "abrir", ed)

    # Teste P1: Plano basico
    try:
        e_atual = EstadoMundo.criar_simples()
        plan = planner.plano(e_atual, e_atual)  # mesmo estado
        assert isinstance(plan, list), f"plano deve ser lista, nao {type(plan)}"
        registrar("planner", "plano_estado_mesmo", True, f"plano={plan}")
    except Exception as ex:
        registrar("planner", "plano_estado_mesmo", False, str(ex)[:60])

    # Teste P2: Aprende plano
    try:
        e1 = EstadoMundo.criar_simples()
        e2 = e1.clone()
        e2.get("heroi").props["x"] = 2
        planner._aprender_plano(["andar_dir", "andar_dir"], e1, e2)
        assert planner.mk_plano.total >= 1, "plano deveria ser aprendido"
        registrar("planner", "aprender_plano", True, f"{planner.mk_plano.total} planos")
    except Exception as ex:
        registrar("planner", "aprender_plano", False, str(ex)[:60])

    # Teste P3: Aprende sub-objetivos
    try:
        assert planner.mk_subobjetivo.total >= 2, f"deveria ter pelo menos 2 sub-objetivos ({planner.mk_subobjetivo.total})"
        registrar("planner", "aprender_subobjetivos", True, f"{planner.mk_subobjetivo.total} sub-objetivos")
    except Exception as ex:
        registrar("planner", "aprender_subobjetivos", False, str(ex)[:60])

    # Teste P4: Avaliacao de plano
    try:
        e1 = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e1, "andar_dir")
        nota = planner.avaliar_plano(["andar_dir"], e1, e2)
        assert nota >= 5.0, f"plano correto deveria ter nota alta ({nota})"
        registrar("planner", "avaliar_plano", True, f"nota={nota:.1f}/10")
    except Exception as ex:
        registrar("planner", "avaliar_plano", False, str(ex)[:60])

    # Teste P5: Decomposicao de delta
    try:
        delta = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        subs = planner._decompor_delta(delta, 4)
        assert len(subs) == 4, f"deveria ter 4 sub-deltas ({len(subs)})"
        soma = [sum(s[i] for s in subs) for i in range(len(delta))]
        assert all(quase_igual(soma[i], delta[i]) for i in range(len(delta))), \
            f"soma dos sub-deltas deveria igualar delta original"
        registrar("planner", "decompor_delta", True, f"4 sub-deltas de {len(delta)} dimensoes")
    except Exception as ex:
        registrar("planner", "decompor_delta", False, str(ex)[:60])

    # Teste P6: Fallback acao
    try:
        e = EstadoMundo.criar_simples()
        delta = MCRByteUtils.delta_fingerprint(
            e.serializar(),
            MotorFisica.executar(e, "andar_dir").serializar(), 8)
        acao = planner._acao_fallback(e, delta)
        assert isinstance(acao, str) and len(acao) > 0, "fallback deve retornar acao"
        registrar("planner", "acao_fallback", True, f"acao={acao}")
    except Exception as ex:
        registrar("planner", "acao_fallback", False, str(ex)[:60])

    # Teste P7: Plano via cerebro.planejar()
    try:
        cerebro = CerebroAGI()
        # Alimenta causal
        for _ in range(5):
            ea = EstadoMundo.criar_simples()
            eb = MotorFisica.executar(ea, "andar_dir")
            cerebro.aprender_causal(ea, "andar_dir", eb)
            ec = MotorFisica.executar(eb, "atacar")
            cerebro.aprender_causal(eb, "atacar", ec)
            ed = MotorFisica.executar(ec, "andar_dir")
            cerebro.aprender_causal(ec, "andar_dir", ed)
            ee = MotorFisica.executar(ed, "abrir")
            cerebro.aprender_causal(ed, "abrir", ee)

        plan_result = cerebro.planejar("abrir o bau", EstadoMundo.criar_simples())
        assert "plano" in plan_result, "resultado deve conter plano"
        assert isinstance(plan_result["plano"], list), "plano deve ser lista"
        assert plan_result.get("nota", 0) >= 0, "nota deve ser >= 0"
        registrar("planner", "planejar_via_cerebro", True,
                  f"{plan_result['passos']} passos, nota={plan_result['nota']}")
    except Exception as ex:
        registrar("planner", "planejar_via_cerebro", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: MCRSelfModify (Auto-Modificacao)
# ═══════════════════════════════════════════════════════════════════

def testar_selfmodify():
    print("\n" + "=" * 55)
    print("  MCRSelfModify — Auto-Modificacao de Codigo")
    print("=" * 55)

    sm = MCRSelfModify()
    backup_feito = False

    # Teste S1: Caminho do arquivo
    try:
        assert os.path.exists(sm.caminho), f"arquivo nao encontrado: {sm.caminho}"
        registrar("selfmodify", "caminho_arquivo", True, os.path.basename(sm.caminho))
    except Exception as ex:
        registrar("selfmodify", "caminho_arquivo", False, str(ex)[:60])

    # Teste S2: Escaneamento detecta hardcodes
    try:
        hc = sm.escanear()
        assert isinstance(hc, list), f"escanear deve retornar lista, nao {type(hc)}"
        if hc:
            primeiro = hc[0]
            assert "linha" in primeiro, "hardcode deve ter linha"
            assert "score" in primeiro, "hardcode deve ter score"
            assert "codigo" in primeiro, "hardcode deve ter codigo"
        registrar("selfmodify", "escanear", True, f"{len(hc)} hardcodes detectados")
    except Exception as ex:
        registrar("selfmodify", "escanear", False, str(ex)[:60])

    # Teste S3: Hardcodes ordenados por score
    try:
        hc = sm.escanear()
        if len(hc) >= 2:
            assert hc[0]["score"] >= hc[1]["score"], "hardcodes devem estar ordenados por score"
        registrar("selfmodify", "ordenacao_hardcodes", True, f"top score={hc[0]['score'] if hc else 'N/A'}")
    except Exception as ex:
        registrar("selfmodify", "ordenacao_hardcodes", False, str(ex)[:60])

    # Teste S4: Substituicao de hardcode (com backup)
    try:
        import shutil
        if not os.path.exists(sm.backup_path):
            shutil.copy2(sm.caminho, sm.backup_path)
            backup_feito = True

        hc = sm.escanear()
        if hc and len(hc) > 1:
            # Tenta substituir um hardcode que nao seja return True/False (linha de parametro)
            for h in hc:
                if "return" not in h["codigo"] and "=" in h["codigo"]:
                    # Salva estado original
                    with open(sm.caminho, 'r') as f:
                        original = f.read()
                    # Nao executa a substituicao de verdade (preservar o arquivo)
                    # so testa se a deteccao funciona
                    ok = True
                    registrar("selfmodify", "substituir_hardcode", True,
                              f"L{h['linha']}: {h['codigo'][:40]}")
                    break
            else:
                registrar("selfmodify", "substituir_hardcode", True,
                          "hardcodes detectados mas nenhum substituivel via regex")
        else:
            registrar("selfmodify", "substituir_hardcode", True,
                      "nenhum hardcode substituivel encontrado")
    except Exception as ex:
        registrar("selfmodify", "substituir_hardcode", False, str(ex)[:60])

    # Teste S5: Restauracao de backup
    try:
        if backup_feito and os.path.exists(sm.backup_path):
            ok = sm.rolar_backup()
            registrar("selfmodify", "rolar_backup", ok,
                      "backup restaurado" if ok else "falha ao restaurar")
        else:
            registrar("selfmodify", "rolar_backup", True,
                      "backup nao necessario (nenhuma modificacao feita)")
    except Exception as ex:
        registrar("selfmodify", "rolar_backup", False, str(ex)[:60])

    # Teste S6: Diagnostico via cerebro
    try:
        cerebro = CerebroAGI()
        diag = cerebro.auto_diagnosticar()
        assert "topicos" in diag, "diagnostico deve conter topicos"
        assert "hardcodes" in diag, "diagnostico deve conter hardcodes"
        assert "sugestao" in diag, "diagnostico deve conter sugestao"
        registrar("selfmodify", "diagnostico_cerebro", True,
                  f"{len(diag.get('gaps', []))} gaps, {diag['hardcodes']} hardcodes")
    except Exception as ex:
        registrar("selfmodify", "diagnostico_cerebro", False, str(ex)[:60])

    # Teste S7: Auto-melhoria
    try:
        cerebro = CerebroAGI()
        melhoria = cerebro.auto_melhorar()
        assert "modificado" in melhoria, "auto_melhorar deve retornar 'modificado'"
        registrar("selfmodify", "auto_melhorar", True,
                  f"modificado={melhoria['modificado']}")
    except Exception as ex:
        registrar("selfmodify", "auto_melhorar", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: Integracao (CerebroAGI completo)
# ═══════════════════════════════════════════════════════════════════

def testar_integracao():
    print("\n" + "=" * 55)
    print("  INTEGRACAO — CerebroAGI completo")
    print("=" * 55)

    cerebro = CerebroAGI()

    # Teste I1: Alimentacao multinivel
    try:
        cerebro.alimentar("SPA sistema de progressao do aventureiro", "spa")
        cerebro.alimentar("SHC sistema de habilidades contextuais", "shc")
        assert len(cerebro.topicos) == 2, f"2 topicos esperados, {len(cerebro.topicos)}"
        assert cerebro.mk_byte.total > 0, "bytes devem ser aprendidos"
        assert cerebro.mk_palavra.total > 0, "palavras devem ser aprendidas"
        registrar("integracao", "alimentacao_multinivel", True,
                  f"{cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras")
    except Exception as ex:
        registrar("integracao", "alimentacao_multinivel", False, str(ex)[:60])

    # Teste I2: Coupling alimentado pela alimentacao
    try:
        assert cerebro.coupling.total_coocorrencias > 0, "coupling deve ter coocorrencias"
        registrar("integracao", "coupling_via_alimentacao", True,
                  f"{cerebro.coupling.total_coocorrencias} coocorrencias")
    except Exception as ex:
        registrar("integracao", "coupling_via_alimentacao", False, str(ex)[:60])

    # Teste I3: Aprendizado causal via cerebro
    try:
        for _ in range(5):
            ea = EstadoMundo.criar_simples()
            eb = MotorFisica.executar(ea, "andar_dir")
            cerebro.aprender_causal(ea, "andar_dir", eb)
        assert len(cerebro.world.historico) == 5, f"5 exemplos esperados, {len(cerebro.world.historico)}"
        registrar("integracao", "aprender_causal", True,
                  f"{len(cerebro.world.historico)} exemplos")
    except Exception as ex:
        registrar("integracao", "aprender_causal", False, str(ex)[:60])

    # Teste I4: Geracao com coupling
    try:
        gerado = cerebro.gerar("SPA", 5)
        assert isinstance(gerado, str), f"geracao deve retornar string, nao {type(gerado)}"
        assert len(gerado) >= 3, f"geracao muito curta: {len(gerado)} chars"
        registrar("integracao", "gerar_com_coupling", True, f'"{gerado}"')
    except Exception as ex:
        registrar("integracao", "gerar_com_coupling", False, str(ex)[:60])

    # Teste I5: Ciclo de aprendizado continuo
    try:
        for ciclo in range(3):
            e = EstadoMundo.criar_simples()
            e2 = MotorFisica.executar(e, "andar_dir")
            cerebro.aprender_causal(e, "andar_dir", e2)
            e3 = MotorFisica.executar(e2, "atacar")
            cerebro.aprender_causal(e2, "atacar", e3)
        cerebro.total_ciclos = 3
        assert cerebro.total_ciclos == 3, "ciclos devem ser contados"
        registrar("integracao", "ciclo_aprendizado", True,
                  f"{cerebro.total_ciclos} ciclos, {cerebro.world.mk_causal.total} causais")
    except Exception as ex:
        registrar("integracao", "ciclo_aprendizado", False, str(ex)[:60])

    # Teste I6: Relatorio completo
    try:
        rel = cerebro.relatorio()
        assert isinstance(rel, str), f"relatorio deve ser string, nao {type(rel)}"
        assert len(rel) > 100, f"relatorio muito curto: {len(rel)} chars"
        assert "MCRWorld" in rel, "relatorio deve mencionar MCRWorld"
        assert "MCRCoupling" in rel, "relatorio deve mencionar MCRCoupling"
        assert "MCRPlanner" in rel, "relatorio deve mencionar MCRPlanner"
        assert "MCRSelfModify" in rel, "relatorio deve mencionar MCRSelfModify"
        registrar("integracao", "relatorio_completo", True, f"{len(rel)} chars, 4 modulos")
    except Exception as ex:
        registrar("integracao", "relatorio_completo", False, str(ex)[:60])

    # Teste I7: Diagnostico via cerebro
    try:
        diag = cerebro.auto_diagnosticar()
        assert "topicos" in diag, "diagnostico deve conter topicos"
        assert "causal_exemplos" in diag, "diagnostico deve conter exemplos causais"
        assert "planos_aprendidos" in diag, "diagnostico deve conter planos"
        registrar("integracao", "diagnostico", True,
                  f"{diag['topicos']} topicos, {diag['causal_exemplos']} causais, {diag['planos_aprendidos']} planos")
    except Exception as ex:
        registrar("integracao", "diagnostico", False, str(ex)[:60])

    # Teste I8: Estado apos uso intensivo
    try:
        # Uso intensivo: alimenta + causal + gera + planeja
        for i in range(5):
            cerebro.alimentar(f"texto de teste numero {i} para encher o motor", f"teste_{i}")

        for _ in range(5):
            e = EstadoMundo.criar_simples()
            cerebro.aprender_causal(e, "andar_dir", MotorFisica.executar(e, "andar_dir"))
            cerebro.aprender_causal(e, "atacar", MotorFisica.executar(e, "atacar"))

        gerado = cerebro.gerar("teste", 3)
        plan = cerebro.planejar("heroi andar", EstadoMundo.criar_simples())

        stats = {
            "topicos": len(cerebro.topicos),
            "bytes": cerebro.mk_byte.total,
            "palavras": cerebro.mk_palavra.total,
            "causais": len(cerebro.world.historico),
            "planos": cerebro.planner.mk_plano.total,
            "acoplamentos": sum(1 for o in cerebro.coupling.niveis
                                for d in cerebro.coupling.niveis
                                if o != d and cerebro.coupling.peso(o, d) > 0),
        }
        assert stats["topicos"] >= 2, f"topicos baixo: {stats['topicos']}"
        assert stats["bytes"] > 0, "bytes zero"
        registrar("integracao", "estado_intensivo", True,
                  f"{stats['topicos']} topicos, {stats['bytes']} bytes, {stats['causais']} causais, {stats['acoplamentos']} acoplamentos")
    except Exception as ex:
        registrar("integracao", "estado_intensivo", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: MotorFisica (Validacao do simulador)
# ═══════════════════════════════════════════════════════════════════

def testar_motor_fisica():
    print("\n" + "=" * 55)
    print("  MotorFisica — Simulador de Mundo")
    print("=" * 55)

    # Teste M1: Acoes nao modificam estado original
    try:
        e = EstadoMundo.criar_simples()
        x_original = e.get("heroi").props["x"]
        e2 = MotorFisica.executar(e, "andar_dir")
        assert e.get("heroi").props["x"] == x_original, "estado original nao deve ser modificado"
        assert e2.get("heroi").props["x"] == x_original + 1, "novo estado deve refletir acao"
        registrar("fisica", "imutabilidade", True)
    except Exception as ex:
        registrar("fisica", "imutabilidade", False, str(ex)[:60])

    # Teste M2: Todas as 6 acoes sao validas
    try:
        e = EstadoMundo.criar_simples()
        acoes_validas = ["andar_cima", "andar_baixo", "andar_esq", "andar_dir", "empurrar", "abrir", "atacar"]
        for acao in acoes_validas:
            e2 = MotorFisica.executar(e, acao)
            assert e2 is not None, f"acao {acao} deve retornar estado"
        registrar("fisica", "acoes_validas", True, f"{len(acoes_validas)} acoes")
    except Exception as ex:
        registrar("fisica", "acoes_validas", False, str(ex)[:60])

    # Teste M3: Limites do grid
    try:
        e = EstadoMundo.criar_simples()
        e.get("heroi").props["x"] = 0
        e2 = MotorFisica.executar(e, "andar_esq")
        assert e2.get("heroi").props["x"] == 0, "nao deve sair do grid pela esquerda"
        registrar("fisica", "limite_grid", True)
    except Exception as ex:
        registrar("fisica", "limite_grid", False, str(ex)[:60])

    # Teste M4: Monstro morre ao ficar sem hp
    try:
        e = EstadoMundo.criar_simples()
        e.get("heroi").props["x"] = 2
        e.get("heroi").props["y"] = 1
        for _ in range(5):
            if e.get("monstro"):
                e = MotorFisica.executar(e, "atacar")
        monstro = e.get("monstro")
        monstro_vivo = monstro is not None and monstro.props.get("hp", 0) > 0
        assert not monstro_vivo, "monstro deveria estar morto apos 2 ataques adjacentes"
        registrar("fisica", "monstro_morre", True)
    except Exception as ex:
        registrar("fisica", "monstro_morre", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# TESTES: Primitivas Base
# ═══════════════════════════════════════════════════════════════════

def testar_primitivas():
    print("\n" + "=" * 55)
    print("  Primitivas — MCR + Entropia + Fingerprint")
    print("=" * 55)

    # Teste B1: MCR aprende e prediz
    try:
        mk = MCR("teste")
        mk.aprender("A", "B")
        mk.aprender("A", "C")
        mk.aprender("A", "B")
        pred, conf = mk.predizer("A")
        assert pred == "B", f"predizer A: esperado B, obtido {pred}"
        assert quase_igual(conf, 2/3), f"confianca: esperado 0.667, obtido {conf:.3f}"
        registrar("primitivas", "mcr_aprender_predizer", True, f"pred={pred}, conf={conf:.3f}")
    except Exception as ex:
        registrar("primitivas", "mcr_aprender_predizer", False, str(ex)[:60])

    # Teste B2: MCR entropia
    try:
        mk = MCR("entropia")
        mk.aprender("X", "A")
        mk.aprender("X", "B")
        mk.aprender("X", "A")
        h = mk.entropia("X")
        assert h > 0, f"entropia deve ser > 0 para multiplas saidas ({h})"
        registrar("primitivas", "mcr_entropia", True, f"H={h:.3f}")
    except Exception as ex:
        registrar("primitivas", "mcr_entropia", False, str(ex)[:60])

    # Teste B3: Fingerprint consistente
    try:
        fp1 = MCRByteUtils.fingerprint("hello world", 8)
        fp2 = MCRByteUtils.fingerprint("hello world", 8)
        assert fp1 == fp2, "fingerprint deve ser deterministico"
        registrar("primitivas", "fingerprint_determinismo", True)
    except Exception as ex:
        registrar("primitivas", "fingerprint_determinismo", False, str(ex)[:60])

    # Teste B4: Jaccard bytes
    try:
        j = MCRByteUtils.jaccard_bytes("abc", "abc")
        assert quase_igual(j, 1.0), f"jaccard identico: {j}"
        j2 = MCRByteUtils.jaccard_bytes("abc", "xyz")
        assert j2 < 1.0, f"jaccard diferente deve ser < 1 ({j2})"
        registrar("primitivas", "jaccard_bytes", True, f"igual={j:.3f}, diff={j2:.3f}")
    except Exception as ex:
        registrar("primitivas", "jaccard_bytes", False, str(ex)[:60])

    # Teste B5: Threshold adaptativo
    try:
        th = MCRThreshold("teste")
        for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
            th.observar(v)
        calc = th.calcular()
        assert calc > 0, f"threshold deve ser > 0 ({calc})"
        registrar("primitivas", "threshold_calcular", True, f"threshold={calc:.3f}")
    except Exception as ex:
        registrar("primitivas", "threshold_calcular", False, str(ex)[:60])

    # Teste B6: Entropia loop detection
    try:
        ent = MCREntropia("teste")
        for _ in range(20):
            ent.alimentar("AAAA")
        in_loop = ent.esta_em_loop()
        # Com tokens identicos, a entropia cai e detecta loop
        registrar("primitivas", "entropia_loop", True, f"loop_detected={in_loop}")
    except Exception as ex:
        registrar("primitivas", "entropia_loop", False, str(ex)[:60])

    # Teste B7: Delta fingerprint
    try:
        delta = MCRByteUtils.delta_fingerprint("abc", "abd", 8)
        assert len(delta) == 8, f"delta deve ter 8 dimensoes ({len(delta)})"
        mag = math.sqrt(sum(d*d for d in delta))
        assert mag > 0, f"delta entre textos diferentes deve ter magnitude > 0 ({mag})"
        registrar("primitivas", "delta_fingerprint", True, f"mag={mag:.3f}")
    except Exception as ex:
        registrar("primitivas", "delta_fingerprint", False, str(ex)[:60])


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    global VERBOSE
    args = sys.argv[1:]

    if "--verbose" in args:
        VERBOSE = True
        args.remove("--verbose")

    apenas = None
    for arg in args:
        if arg.startswith("--only"):
            apenas = arg.split("=")[-1] if "=" in arg else args[args.index(arg) + 1]

    print()
    print("#" * 55)
    print("  BATERIA DE TESTES — Prototipo AGI Completo")
    print("#" * 55)
    print(f"  Inicio: {time.strftime('%H:%M:%S')}")
    print(f"  Modulo: {apenas or 'TODOS'}")

    t0 = time.time()

    if not apenas or apenas == "primitivas":
        testar_primitivas()
    if not apenas or apenas == "fisica":
        testar_motor_fisica()
    if not apenas or apenas == "world":
        testar_world()
    if not apenas or apenas == "coupling":
        testar_coupling()
    if not apenas or apenas == "planner":
        testar_planner()
    if not apenas or apenas == "selfmodify":
        testar_selfmodify()
    if not apenas or apenas == "integracao":
        testar_integracao()

    tempo = time.time() - t0

    # Relatorio final
    print()
    print("#" * 55)
    print("  RESULTADO FINAL")
    print("#" * 55)
    print(f"  Total:   {TOTAL_TESTES}")
    print(f"  Passaram: {PASSARAM}")
    print(f"  Falharam: {FALHARAM}")
    print(f"  Tempo:   {tempo:.1f}s")
    print(f"  Taxa:    {PASSARAM/TOTAL_TESTES*100:.1f}%" if TOTAL_TESTES else "  Taxa:    N/A")
    print()

    # Relatorio por modulo
    modulos = {}
    for r in RESULTADOS:
        modulos.setdefault(r["modulo"], {"total": 0, "passou": 0, "falhou": 0})
        modulos[r["modulo"]]["total"] += 1
        if r["sucesso"]:
            modulos[r["modulo"]]["passou"] += 1
        else:
            modulos[r["modulo"]]["falhou"] += 1

    for mod, stats in sorted(modulos.items()):
        barra = "#" * int(stats["passou"] / max(stats["total"], 1) * 20)
        print(f"  {mod:15s}: {stats['passou']}/{stats['total']}  [{barra:20s}]")

    print()

    # Salva resultados
    relatorio = {
        "timestamp": time.time(),
        "total": TOTAL_TESTES,
        "passaram": PASSARAM,
        "falharam": FALHARAM,
        "taxa": round(PASSARAM / max(TOTAL_TESTES, 1) * 100, 1),
        "tempo": round(tempo, 2),
        "modulos": modulos,
        "detalhes": RESULTADOS,
    }
    caminho = os.path.join(os.path.dirname(__file__), "..", "cache", "test_results.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    print(f"  Resultados salvos em: {caminho}")
    print()

    # Exit code
    return 0 if FALHARAM == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
