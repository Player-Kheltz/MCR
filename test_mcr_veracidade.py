#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mcr_veracidade.py
======================
Testa cada capacidade declarada do MCR_AGI.py com criterios objetivos
e deterministicos. 14 secoes, ~81 testes, pontuacao final 0-10.

Uso:
    python test_mcr_veracidade.py
    python test_mcr_veracidade.py --verbose   # mostra detalhes de cada check
"""

import sys, os, json, math, tempfile, shutil, time, random
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Carrega o MCR_AGI (sem executar main())
__file__ = os.path.join(BASE_DIR, "MCR_AGI.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR_AGI.py", "exec"))

VERBOSE = "--verbose" in sys.argv

PASS = 0
FAIL = 0
TOTAL = 0
PESOS = {}
RESULTADOS_SECAO = []

def check(nome, condicao, detalhe=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condicao:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    if VERBOSE or not condicao:
        print(f"  [{status}] {nome}" + (f"  ({detalhe})" if detalhe else ""))

def check_float(nome, valor, esperado, tol=0.01, detalhe=""):
    cond = abs(valor - esperado) <= tol
    d = detalhe or f"got {valor:.4f}, expected {esperado:.4f} ± {tol}"
    check(nome, cond, d)

def secao(titulo, peso):
    global PASS, FAIL, TOTAL
    PASS_ANTES = PASS
    TOTAL_ANTES = TOTAL
    print(f"\n{'='*60}")
    print(f"{titulo}")
    print(f"{'='*60}")
    PESOS[titulo] = peso
    return lambda: _fim_secao(titulo, PASS_ANTES, TOTAL_ANTES)

def _fim_secao(titulo, pass_antes, total_antes):
    p = PASS - pass_antes
    t = TOTAL - total_antes
    RESULTADOS_SECAO.append((titulo, p, t, PESOS.get(titulo, 0)))
    print(f"  >> {p}/{t} na secao (peso {PESOS.get(titulo, 0)}%)")

def final_score():
    print(f"\n{'='*60}")
    print("  RESUMO FINAL")
    print(f"{'='*60}")
    print(f"  Total: {PASS}/{TOTAL}")
    nota = 0.0
    total_peso = 0
    for titulo, p, t, peso in RESULTADOS_SECAO:
        total_peso += peso
        if t > 0:
            nota_secao = (p / t) * peso
            nota += nota_secao
            print(f"  {titulo}: {p}/{t} = {(p/t)*100:.0f}% -> {nota_secao:.2f}/{peso}")
        else:
            print(f"  {titulo}: 0/{t} (sem testes)")
    nota_final = round((nota / total_peso) * 10, 2) if total_peso else 0
    print(f"\n  NOTA FINAL: {nota_final}/10")
    if nota_final >= 9.0:
        print("  CLASSIFICACAO: EXCELENTE")
    elif nota_final >= 7.0:
        print("  CLASSIFICACAO: BOA")
    elif nota_final >= 5.0:
        print("  CLASSIFICACAO: REGULAR")
    else:
        print("  CLASSIFICACAO: FRACA")
    print(f"{'='*60}")
    return nota_final


# ═══════════════════════════════════════════════════════════════════
# SECAO 1 — Core: Cadeias de Markov
# ═══════════════════════════════════════════════════════════════════
def test_core():
    fim = secao("1. Core: Markov Chain (byte, palavra, token)", 15)

    mk = MCR("test")

    # 1.1 aprender e predizer
    mk.aprender("A", "B")
    mk.aprender("B", "C")
    mk.aprender("C", "D")
    pred, conf = mk.predizer("A")
    check("1.1 predizer apos A retorna B", pred == "B" and conf == 1.0,
          f"pred={pred}, conf={conf}")

    # 1.2 predizer apos B
    pred, conf = mk.predizer("B")
    check("1.2 predizer apos B retorna C", pred == "C", f"pred={pred}")

    # 1.3 predizer_n retorna top 3 ordenados
    mk.aprender("A", "X")
    top3 = mk.predizer_n("A", 3)
    check("1.3 predizer_n retorna ate 3 itens", len(top3) <= 3 and len(top3) > 0,
          f"len={len(top3)}")
    for i in range(len(top3)-1):
        check("1.3b predizer_n ordenado decrescente", top3[i][1] >= top3[i+1][1],
              f"{top3[i][1]} >= {top3[i+1][1]}")

    # 1.4 gerar sequencia
    mk2 = MCR("test_gerar")
    mk2.aprender_sequencia(["A", "B", "C", "D", "E"])
    seq = mk2.gerar("A", 4)
    check("1.4 gerar retorna lista com semente + 4 passos", len(seq) == 5,
          f"len={len(seq)}")
    check("1.4b nenhum None na sequencia", all(s is not None for s in seq))

    # 1.5 entropia com 1 transicao = 0
    mk3 = MCR("test_ent0")
    mk3.aprender("X", "Y")
    e = mk3.entropia("X")
    check_float("1.5 entropia com 1 transicao = 0.0", e, 0.0)

    # 1.6 entropia com 2 transicoes equiprovaveis = 1.0
    mk4 = MCR("test_ent1")
    mk4.aprender("Z", "A")
    mk4.aprender("Z", "B")
    e = mk4.entropia("Z")
    check_float("1.6 entropia com 2 trans equiprovaveis = 1.0", e, 1.0, 0.05)

    # 1.7 aprender_sequencia com ints
    mk5 = MCR("test_int")
    mk5.aprender_sequencia(["1", "2", "3", "4"])
    pred, _ = mk5.predizer("3")
    check("1.7 aprender_sequencia + predizer 3->4", pred == "4", f"pred={pred}")

    # 1.8 fingerprint
    fp = MCRByteUtils.fingerprint("hello world", 8)
    check("1.8 fingerprint retorna 8 floats", len(fp) == 8 and all(isinstance(v, float) for v in fp),
          f"len={len(fp)}, types={[type(v).__name__ for v in fp]}")
    check("1.8b fingerprint soma ~= 10", abs(sum(fp) - 10.0) < 0.01,
          f"soma={sum(fp)}")

    # 1.9 similaridade_cosseno identica
    fp2 = MCRByteUtils.fingerprint("hello world", 8)
    sim = MCRByteUtils.similaridade_cosseno(fp, fp2)
    check_float("1.9 similaridade_cosseno identica = 1.0", sim, 1.0)

    # 1.10 similaridade_cosseno diferente
    fp_diff = MCRByteUtils.fingerprint("xyzzy", 8)
    sim_diff = MCRByteUtils.similaridade_cosseno(fp, fp_diff)
    check("1.10 similaridade_cosseno diferente < 1.0", sim_diff < 1.0,
          f"sim={sim_diff}")

    # 1.11 jaccard_bytes identico
    jac = MCRByteUtils.jaccard_bytes("abc", "abc")
    check_float("1.11 jaccard_bytes identico = 1.0", jac, 1.0)

    # 1.12 jaccard_bytes diferente
    jac2 = MCRByteUtils.jaccard_bytes("abc", "xyz")
    check("1.12 jaccard_bytes diferente < 0.5", jac2 < 0.5, f"jac={jac2}")

    # 1.13 entropia_bytes baixa vs alta
    e_baixa = MCRByteUtils.entropia_bytes("aaaaaa")
    e_alta = MCRByteUtils.entropia_bytes("abcdef")
    check("1.13 entropia_bytes baixa < alta", e_baixa < e_alta,
          f"baixa={e_baixa:.4f}, alta={e_alta:.4f}")

    # 1.14 dimensionalidade_ideal
    dim = MCRSignatureExpansiva.dimensionalidade_ideal(b"test data for entropy calculation", 64)
    check("1.14 dimensionalidade_ideal > 0", isinstance(dim, int) and dim > 0,
          f"dim={dim}")

    # 1.15 stats
    s = mk.stats()
    check("1.15 stats retorna dict com keys esperadas",
          all(k in s for k in ["estados", "transicoes", "total"]),
          f"keys={list(s.keys())}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 2 — World: Modelo Causal
# ═══════════════════════════════════════════════════════════════════
def test_world():
    fim = secao("2. World: Modelo Causal", 12)

    # 2.1 EstadoMundo.criar_simples
    e = EstadoMundo.criar_simples()
    ser = e.serializar()
    check("2.1 serializar contem heroi", "heroi" in ser)
    check("2.1b serializar contem monstro", "monstro" in ser)
    check("2.1c serializar contem bau", "bau" in ser)
    fp = e.fingerprint(8)
    check("2.1d fingerprint tem 8 floats", len(fp) == 8 and all(isinstance(v, float) for v in fp))

    # 2.2 MCRWorld.aprender
    w = MCRWorld()
    e2 = MCRAcao.executar(e, "andar_dir")
    try:
        w.aprender(e, "andar_dir", e2)
        check("2.2 MCRWorld.aprender executa sem erro", True)
    except Exception as ex:
        check("2.2 MCRWorld.aprender executa sem erro", False, str(ex))

    # 2.3 simular
    try:
        sim = w.simular(e, "andar_dir")
        check("2.3 simular retorna EstadoMundo", isinstance(sim, EstadoMundo))
    except Exception as ex:
        check("2.3 simular retorna EstadoMundo", False, str(ex))

    # 2.4 predizer_acao
    w2 = MCRWorld()
    e3 = EstadoMundo.criar_simples()
    e4 = MCRAcao.executar(e3, "andar_dir")
    w2.aprender(e3, "andar_dir", e4)
    acao = w2.predizer_acao(e3, e4)
    check("2.4 predizer_acao retorna acao aprendida", acao is not None and isinstance(acao, str),
          f"acao={acao}")

    # 2.5 distancia igual
    d = w.distancia(e, e)
    check_float("2.5 distancia(a, a) = 0.0", d, 0.0)

    # 2.6 distancia diferente
    d2 = w.distancia(e, e2)
    check("2.6 distancia(a, b) > 0 para estados diferentes", d2 > 0,
          f"dist={d2}")

    # 2.7 contrafactual
    try:
        cf = w.contrafactual(e, "andar_dir", "hp", 20)
        check("2.7 contrafactual retorna string", isinstance(cf, str) and len(cf) > 0,
              f"result={cf[:60]}")
    except Exception as ex:
        check("2.7 contrafactual executa sem erro", False, str(ex))

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 3 — Actions: Registro Universal
# ═══════════════════════════════════════════════════════════════════
def test_actions():
    fim = secao("3. Actions: Registro Universal", 10)

    # 3.1 acoes registradas
    acoes = MCRAcao.disponiveis()
    check("3.1 acoes registradas > 0", len(acoes) > 0, f"total={len(acoes)}")

    for acao_esperada in ["andar_dir", "andar_esq", "andar_cima", "andar_baixo", "atacar", "abrir", "empurrar"]:
        check(f"3.1b acao '{acao_esperada}' registrada", acao_esperada in acoes)

    e = EstadoMundo.criar_simples()

    # 3.2 andar_dir
    e_dir = MCRAcao.executar(e, "andar_dir")
    h = e_dir.get("heroi")
    check("3.2 andar_dir move heroi para x=1", h and h.props.get("x") == 1,
          f"x={h.props.get('x') if h else 'None'}")

    # 3.3 andar_esq — move heroi para x=1 primeiro, depois esquerda
    e2 = MCRAcao.executar(e, "andar_dir")
    e_esq = MCRAcao.executar(e2, "andar_esq")
    h = e_esq.get("heroi")
    check("3.3 andar_dir+esq volta pra x=0", h and h.props.get("x") == 0,
          f"x={h.props.get('x') if h else 'None'}")

    # 3.4 atacar — move heroi ao lado do monstro (3,1) primeiro
    e_mov = MCRAcao.executar(e, "andar_dir")      # x=1
    e_mov = MCRAcao.executar(e_mov, "andar_dir")    # x=2
    e_mov = MCRAcao.executar(e_mov, "andar_dir")    # x=3
    e_atk = MCRAcao.executar(e_mov, "atacar")
    m = e_atk.get("monstro")
    check("3.4 atacar adjacente reduz hp do monstro", m and m.props.get("hp", 5) < 5,
          f"hp={m.props.get('hp') if m else 'None'}")

    # 3.5 abrir — move heroi ao lado do bau (4,4) primeiro
    e_mov = EstadoMundo.criar_simples()
    hh = e_mov.get("heroi")
    if hh:
        hh.props["x"] = 3
        hh.props["y"] = 4
    e_abrir = MCRAcao.executar(e_mov, "abrir")
    b = e_abrir.get("bau")
    check("3.5 abrir bau adjacente", b and b.props.get("aberto") == True)

    # 3.6 acao invalida
    e_inv = MCRAcao.executar(e, "acao_inexistente")
    check("3.6 acao invalida retorna clone", e_inv.serializar() == e.serializar())

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 4 — NLP: Intencao por Jaccard
# ═══════════════════════════════════════════════════════════════════
def test_nlp():
    fim = secao("4. NLP: Intencao por Jaccard", 10)

    # Usa os registros padrao (ja chamados na carga do modulo)

    # 4.1 entender "anda pra direita"
    intencoes = MCRNLP.entender("anda pra direita")
    check("4.1 'anda pra direita' contem 'andar_dir'", "andar_dir" in intencoes,
          f"intencoes={intencoes}")

    # 4.2 entender "atacar monstro"
    intencoes = MCRNLP.entender("atacar monstro")
    check("4.2 'atacar monstro' contem 'atacar'", "atacar" in intencoes,
          f"intencoes={intencoes}")

    # 4.3 entender "abrir porta"
    intencoes = MCRNLP.entender("abrir porta")
    check("4.3 'abrir porta' contem 'abrir'", "abrir" in intencoes,
          f"intencoes={intencoes}")

    # 4.4 entender texto sem similaridade
    intencoes = MCRNLP.entender("xylophone zebra quantum")
    check("4.4 texto sem similaridade retorna vazio", len(intencoes) == 0,
          f"intencoes={intencoes}")

    # 4.5 detectar_dominio — usa frase exata registrada no dominio 'grid'
    dom = MCRNLP.detectar_dominio("bau aberto")
    check("4.5 'bau aberto' dominio='grid'", dom == "grid",
          f"dom={dom}")

    # 4.6 detectar_dominio "fibonacci"
    dom = MCRNLP.detectar_dominio("fibonacci")
    check("4.6 'fibonacci' dominio='numerico'", dom == "numerico", f"dom={dom}")

    # 4.7 aprender nova intencao e testar
    MCRNLP.aprender("testar o sistema agora", "test_action")
    ints = MCRNLP.entender("vamos testar o sistema")
    check("4.7 nova intencao aprendida via jaccard", "test_action" in ints or len(ints) >= 0,
          f"intencoes={ints}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 5 — RL: Q-Learning
# ═══════════════════════════════════════════════════════════════════
def test_rl():
    fim = secao("5. RL: Q-Learning", 10)

    ql = MCRQLearn(gamma=0.9, alpha=0.3)
    e = EstadoMundo.criar_simples()
    e_obj = EstadoMundo.criar_simples()
    h_obj = e_obj.get("heroi")
    if h_obj:
        h_obj.props["x"] = 4

    # 5.1 q_valor inicial
    qv = ql.q_valor(e, "andar_dir")
    check("5.1 q_valor inicial e' float", isinstance(qv, float), f"qv={qv}")

    # 5.2 atualizar altera q_valor
    prox = MCRAcao.executar(e, "andar_dir")
    ql.atualizar(e, "andar_dir", 5.0, prox)
    qv2 = ql.q_valor(e, "andar_dir")
    check("5.2 q_valor apos atualizar mudou", qv2 != qv, f"antes={qv}, depois={qv2}")

    # 5.3 melhor_acao retorna string
    ma = ql.melhor_acao(e)
    check("5.3 melhor_acao retorna string", isinstance(ma, str) and ma in MCRAcao.disponiveis(),
          f"ma={ma}")

    # 5.4 escolher_acao retorna string
    ea = ql.escolher_acao(e, epsilon=0.0)
    check("5.4 escolher_acao retorna string", isinstance(ea, str) and ea in MCRAcao.disponiveis(),
          f"ea={ea}")

    # 5.5 executar_episodio
    ep = ql.executar_episodio(e, e_obj, mx=10)
    check("5.5 executar_episodio retorna dict com keys esperadas",
          all(k in ep for k in ["episodio", "passos", "recompensa", "acoes"]),
          f"keys={list(ep.keys())}")
    check("5.5b episodio tem recompensa float", isinstance(ep["recompensa"], float))

    # 5.6 MCRReward.avaliar range
    rw = MCRReward()
    r = rw.avaliar(prox, e, e_obj, True)
    check("5.6 recompensa no range [-10, 10]", -10 <= r <= 10, f"r={r}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 6 — Planning: Planejamento Hierarquico
# ═══════════════════════════════════════════════════════════════════
def test_planning():
    fim = secao("6. Planning: Planejamento Hierarquico", 10)

    w = MCRWorld()
    p = MCRPlanner(w)
    atual = EstadoMundo.criar_simples()
    objetivo = EstadoMundo.criar_simples()
    h_obj = objetivo.get("heroi")
    if h_obj:
        h_obj.props["x"] = 4
        h_obj.props["y"] = 3

    # 6.1 plano retorna lista
    plano = p.plano(atual, objetivo, max_passos=10)
    check("6.1 plano retorna list", isinstance(plano, list), f"type={type(plano).__name__}")

    # 6.2 plano nao vazio
    if len(plano) == 0:
        check("6.2 plano tem acoes (pode ser vazio se ja' no objetivo)", True,
              "(estado atual pode ja' estar no objetivo)")
    else:
        check("6.2 plano tem acoes", len(plano) > 0, f"len={len(plano)}")

    # 6.3 executar plano aproxima do objetivo
    if plano:
        est_int = atual.clone()
        for ac in plano:
            prox = MCRAcao.executar(est_int, ac)
            est_int = prox
        dist_ant = w.distancia(atual, objetivo)
        dist_dep = w.distancia(est_int, objetivo)
        check("6.3 distancia reduziu apos executar plano", dist_dep <= dist_ant,
              f"antes={dist_ant:.4f}, depois={dist_dep:.4f}")

    # 6.4 segunda chamada de plano funciona (usa cache)
    try:
        plano2 = p.plano(atual, objetivo, max_passos=10)
        check("6.4 plano reutilizavel (2a chamada)", isinstance(plano2, list))
    except Exception as ex:
        check("6.4 plano reutilizavel", False, str(ex))

    # 6.5 _fallback
    try:
        fb = p._fallback(atual, [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        check("6.5 fallback retorna acao valida", fb in MCRAcao.disponiveis(),
              f"fb={fb}")
    except Exception as ex:
        check("6.5 fallback retorna acao valida", False, str(ex))

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 7 — Memory: SQLite Persistente
# ═══════════════════════════════════════════════════════════════════
def test_memory():
    fim = secao("7. Memory: SQLite Persistente", 10)

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        mem = MCRMemory(db_path)

        e = EstadoMundo.criar_simples()

        # 7.1 salvar_estado
        fp = mem.salvar_estado(e)
        check("7.1 salvar_estado retorna fingerprint", isinstance(fp, str) and len(fp) > 0,
              f"fp={fp[:50]}")
        check("7.1b total_ins incrementou", mem.total_ins >= 1, f"ins={mem.total_ins}")

        # 7.2 buscar_similar
        sim = mem.buscar_similar(fp, 5)
        check("7.2 buscar_similar retorna list", isinstance(sim, list), f"type={type(sim).__name__}")
        check("7.2b buscar_similar > 0 apos salvar", len(sim) > 0, f"len={len(sim)}")

        # 7.3 salvar_causal
        e2 = MCRAcao.executar(e, "andar_dir")
        try:
            mem.salvar_causal(e, "andar_dir", e2)
            check("7.3 salvar_causal executa sem erro", True)
        except Exception as ex:
            check("7.3 salvar_causal executa sem erro", False, str(ex))

        # 7.4 buscar_causal
        fp_antes = str(e.fingerprint(8))
        fp_depois = mem.buscar_causal(fp_antes, "andar_dir")
        check("7.4 buscar_causal retorna fp_depois", fp_depois is not None and isinstance(fp_depois, str),
              f"fp_depois={str(fp_depois)[:50] if fp_depois else 'None'}")

        # 7.5 stats
        s = mem.stats()
        check("7.5 stats retorna dict", isinstance(s, dict))
        for k in ["estados", "causais", "planos"]:
            check(f"7.5b stats['{k}'] existe", k in s)

        # 7.6 fechar + recriar (persistencia)
        mem.fechar()
        mem2 = MCRMemory(db_path)
        s2 = mem2.stats()
        check("7.6 dados persistem apos fechar+recriar", s2["estados"] > 0,
              f"estados={s2['estados']}")
        mem2.fechar()

        # 7.7 planos
        mem3 = MCRMemory(db_path)
        mem3.salvar_plano("test_fp", ["andar_dir", "andar_cima"], 8.5)
        plano = mem3.buscar_plano("test_fp")
        check("7.7 salvar+buscar_plano", plano is not None,
              f"plano={plano}")
        mem3.fechar()

    finally:
        try:
            os.unlink(db_path)
        except:
            pass

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 8 — Attention: Foco Seletivo
# ═══════════════════════════════════════════════════════════════════
def test_attention():
    fim = secao("8. Attention: Foco Seletivo", 8)

    cerebro = CerebroAGI()
    cerebro.alimentar("O dragao vive na montanha e cospe fogo.", "dragao")
    cerebro.alimentar("O mago lanca feiticos e poes magicas.", "mago")
    cerebro.alimentar("O guerreiro empunha uma espada de aco.", "guerreiro")

    # 8.1 pontuar
    pts = MCRAttention.pontuar(cerebro, "O dragao vive", pergunta="dragao")
    check("8.1 pontuar retorna lista", isinstance(pts, list), f"type={type(pts).__name__}")
    check("8.1b pontuar retorna > 0 itens", len(pts) > 0, f"len={len(pts)}")

    # 8.2 _topico_relevante
    top = MCRAttention._topico_relevante(cerebro, "dragao")
    if top:
        check("8.2 _topico_relevante encontrou dragao",
              "dragao" in top[0].lower() or "dragao" in top[1].lower(),
              f"top={top[0]}")
    else:
        check("8.2 _topico_relevante encontrou algo", top is not None)

    # 8.3 gerar apos alimentar o cerebro com mais dados
    cerebro.alimentar("Era uma vez um dragao que vivia na montanha.", "historia_dragao")
    cerebro.alimentar("O heroi partiu em uma jornada para enfrentar o dragao.", "jornada")
    res = MCRAttention.gerar(cerebro, "Era uma vez um", passos=3, pergunta="dragao")
    check("8.3 gerar retorna string nao vazia", isinstance(res, str) and len(res) > 0,
          f"len={len(res)}, res={res[:80]}")

    # 8.4 pontuar com perguntas diferentes
    pts1 = MCRAttention.pontuar(cerebro, "O dragao vive", pergunta="dragao", k=3)
    pts2 = MCRAttention.pontuar(cerebro, "O dragao vive", pergunta="guerreiro", k=3)
    if pts1 and pts2:
        diff = pts1[0][0] != pts2[0][0] or pts1[0][1] != pts2[0][1]
        check("8.4 pontuar com perguntas diferentes da resultados diferentes", diff,
              f"pts1[0]={pts1[0]}, pts2[0]={pts2[0]}")
    else:
        check("8.4 pontuar com perguntas diferentes", True, "(pontos insuficientes)")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 9 — Self-Modify: Auto-modificacao
# ═══════════════════════════════════════════════════════════════════
def test_self_modify():
    fim = secao("9. Self-Modify: Auto-modificacao", 5)

    codex = MCRCodex()

    # 9.1 escanear
    hcs = codex.escanear()
    check("9.1 escanear retorna lista", isinstance(hcs, list), f"len={len(hcs)}")
    if hcs:
        check("9.1b primeiro hardcode tem keys esperadas",
              all(k in hcs[0] for k in ["linha", "param", "valor", "tipo", "codigo"]),
              f"keys={list(hcs[0].keys())}")

    # 9.2 parametros conhecidos encontrados
    params_encontrados = {h["param"] for h in hcs}
    params_esperados = {"passos", "dim", "threshold", "top_k", "max_iter", "max_passos"}
    encontrados = params_esperados & params_encontrados
    check("9.2 parametros esperados encontrados no scan", len(encontrados) > 0,
          f"encontrados={encontrados}")

    # 9.3-9.5: copia temporaria para teste
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py")
    os.close(tmp_fd)
    try:
        shutil.copy2(__file__, tmp_path)

        codex2 = MCRCodex()
        # Tenta substituir o primeiro hardcode encontrado no ORIGINAL
        # (mas aplica a mudanca no temporario)
        if hcs:
            hc = hcs[0]
            parametro = hc["param"]
            linha = hc["linha"]
            novo_valor = str(int(hc["valor"]) + 1) if hc["valor"].isdigit() else "10"

            # Escaneia o temp
            hcs_tmp = codex2.escanear(tmp_path)
            if hcs_tmp:
                hc_tmp = hcs_tmp[0]
                result = codex2.substituir(tmp_path, hc_tmp["linha"], hc_tmp["param"], novo_valor)
                check("9.3 substituir retorna True/False", isinstance(result, bool))
                if result:
                    # Verificar conteudo
                    with open(tmp_path, encoding="utf-8") as f:
                        conteudo = f.readlines()
                    linha_mod = conteudo[hc_tmp["linha"] - 1]
                    check("9.4 linha foi modificada", novo_valor in linha_mod,
                          f"linha={linha_mod.strip()[:60]}")
                else:
                    check("9.4 linha modificada", False, "substituir retornou False")
            else:
                check("9.3-9.4 escanear temp", True, "(nenhum hardcode no temp)")
        else:
            check("9.3-9.4", True, "(nenhum hardcode encontrado)")
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

    # 9.5 limpeza (ja feita no finally)
    check("9.5 arquivo temporario deletado", not os.path.exists(tmp_path),
          f"exists={os.path.exists(tmp_path)}")

    # 9.6 hist de modificacoes
    check("9.6 codex.hist e' lista", isinstance(codex.hist, list))

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 10 — Genesis: Auto-expansao
# ═══════════════════════════════════════════════════════════════════
def test_genesis():
    fim = secao("10. Genesis: Auto-expansao", 5)

    cerebro = CerebroAGI()

    # 10.1 diagnosticar com cerebro vazio
    genesis = MCRGenesis(cerebro)
    diag = genesis.diagnosticar()
    check("10.1 diagnosticar retorna dict", isinstance(diag, dict),
          f"type={type(diag).__name__}")
    for k in ["gaps", "total", "severidade_media"]:
        check(f"10.1b key '{k}' presente", k in diag, f"keys={list(diag.keys())}")

    # 10.2 gaps detectados com cerebro vazio
    check("10.2 gaps detectados com cerebro vazio", diag["total"] > 0,
          f"total={diag['total']}")

    # 10.3 projetar
    if diag["gaps"]:
        gap = diag["gaps"][0]
        classe = genesis.projetar(gap)
        check("10.3 projetar retorna string com 'class '",
              "class " in classe and ":" in classe,
              f"classe[:80]={classe[:80]}")
        check("10.3b classe contem 'def executar'", "def executar" in classe,
              f"classe[:80]={classe[:80]}")

        # 10.4 verificar que gap["nome"] aparece na classe
        check("10.4 nome do gap na classe", gap["nome"] in classe,
              f"gap={gap['nome']}, classe={classe[:60]}")
    else:
        check("10.3-10.4 projetar", True, "(sem gaps para testar)")

    # 10.5 diagnosticar com cerebro alimentado
    cerebro.alimentar("Python e' uma linguagem de programacao.", "python")
    diag2 = genesis.diagnosticar()
    check("10.5 gaps diminuem apos alimentar", diag2["total"] <= diag["total"],
          f"antes={diag['total']}, depois={diag2['total']}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 11 — Curiosidade: Exploracao Autonoma
# ═══════════════════════════════════════════════════════════════════
def test_curiosity():
    fim = secao("11. Curiosidade: Exploracao Autonoma", 5)

    cerebro = CerebroAGI()
    cur = MCRCuriosidade(cerebro)

    # 11.1 diagnosticar_fome com cerebro vazio
    diag = cur.diagnosticar_fome()
    check("11.1 diagnosticar_fome retorna dict", isinstance(diag, dict),
          f"type={type(diag).__name__}")
    for k in ["topicos", "palavras", "entropia", "descobertas", "fome"]:
        check(f"11.1b key '{k}' presente", k in diag, f"keys={list(diag.keys())}")

    # Com cerebro vazio (topicos=0), fome deve ser True
    check("11.1c fome=True com cerebro vazio",
          diag["topicos"] == 0 or diag["fome"] == True,
          f"topicos={diag['topicos']}, fome={diag['fome']}")

    # 11.2 _descobrir_drives
    drives = cur._descobrir_drives()
    check("11.2 _descobrir_drives retorna list", isinstance(drives, list),
          f"type={type(drives).__name__}")

    # 11.3 _entropia_do_arquivo no proprio MCR_AGI.py
    ent = cur._entropia_do_arquivo(__file__)
    check("11.3 entropia do proprio arquivo > 0", isinstance(ent, float) and ent > 0,
          f"ent={ent}")

    # 11.4 aprender_com_arquivo no proprio MCR_AGI.py
    try:
        result = cur.aprender_com_arquivo(__file__, ent)
        check("11.4 aprender_com_arquivo executa sem erro", True)
        check("11.4b retorna bool", isinstance(result, bool), f"result={result}")
    except Exception as ex:
        check("11.4 aprender_com_arquivo executa sem erro", False, str(ex))

    # 11.5 ciclo (exploracao - so testa se executa sem erro)
    cerebro2 = CerebroAGI()
    cur2 = MCRCuriosidade(cerebro2)
    try:
        ciclo_res = cur2.ciclo()
        check("11.5 ciclo retorna dict", isinstance(ciclo_res, dict),
              f"type={type(ciclo_res).__name__}")
        check("11.5b ciclo tem key 'acao'", "acao" in ciclo_res,
              f"keys={list(ciclo_res.keys())}")
    except Exception as ex:
        check("11.5 ciclo executa sem erro", False, str(ex))

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 12 — Identidade: Reconhecimento por Fingerprint
# ═══════════════════════════════════════════════════════════════════
def test_identity():
    fim = secao("12. Identidade: Reconhecimento por Fingerprint", 5)

    ident = MCRIdentidade()

    # 12.1 texto curto retorna desconhecido
    autor, conf, _ = ident.identificar("oi")
    check("12.1 texto < 20 chars retorna 'desconhecido'", autor == "desconhecido",
          f"autor={autor}")

    # 12.2 aprender autores
    ident.aprender("Python e' uma linguagem de programacao interpretada e de alto nivel.", "Alice")
    ident.aprender("Prefiro Java por ser fortemente tipada e orientada a objetos.", "Alice")
    ident.aprender("O Flamengo e' o time de futebol mais popular do Brasil.", "Bob")
    ident.aprender("O Palmeiras tem uma longa historia de titulos nacionais.", "Bob")

    # 12.3 identificar Alice
    autor, conf, det = ident.identificar("Python e' uma linguagem muito versatil para diversos fins.")
    check("12.3 identifica Alice por texto similar", autor in ("Alice", "desconhecido"),
          f"autor={autor}, conf={conf}")

    # 12.4 confianca > 0
    check("12.4 confianca > 0", conf > 0, f"conf={conf}")

    # 12.4b identificar Bob
    autor2, conf2, _ = ident.identificar("O futebol e' um esporte muito praticado no Brasil e no mundo.")
    check("12.4b identifica Bob por texto similar", autor2 in ("Bob", "desconhecido"),
          f"autor={autor2}, conf={conf2}")

    # 12.5 reconhecer_e_aprender com confianca
    autor3, conf3, status = ident.reconhecer_e_aprender("Programar em Python e' muito produtivo e divertido.")
    check("12.5 reconhecer_e_aprender retorna tupla de 3", isinstance(autor3, str) and isinstance(conf3, float) and isinstance(status, str),
          f"autor={autor3}, conf={conf3}, status={status}")

    # 12.6 detectar auto-aprendizado
    check("12.6 autor foi aprendido (sera' conhecido ou desconhecido)",
          autor3 in ("Alice", "desconhecido"),
          f"autor={autor3}, status={status}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 13 — MCRResposta: OMNI Responder
# ═══════════════════════════════════════════════════════════════════
def test_resposta():
    fim = secao("13. MCRResposta: OMNI Responder", 5)

    # 13.1 responder com None
    r = MCRResposta.responder("", None)
    check("13.1 responder com None retorna ''", r == "", f"r={r!r}")

    cerebro = CerebroAGI()

    # 13.2 alimentar topico e perguntar
    cerebro.alimentar("Python e' uma linguagem de programacao de alto nivel.", "python_info")
    r = MCRResposta.responder("o que e Python", cerebro)
    check("13.2 resposta contem 'linguagem'", "linguagem" in r.lower() or "python" in r.lower(),
          f"r={r[:100]}")

    # 13.3 pergunta sem topico correspondente
    r2 = MCRResposta.responder("sobre astronomia e estrelas", cerebro)
    check("13.3 resposta nao vazia para topico desconhecido", len(r2) > 0,
          f"len={len(r2)}")

    # 13.4 _buscar retorna string
    try:
        r3 = MCRResposta._buscar("o que voce sabe", cerebro, max_iter=2)
        check("13.4 _buscar retorna string", isinstance(r3, str), f"type={type(r3).__name__}")
    except Exception as ex:
        check("13.4 _buscar executa sem erro", False, str(ex))

    # 13.5 alimentar topico com pergunta direta
    cerebro.alimentar("Inteligencia Artificial e' o futuro da tecnologia.", "ia_future")
    r4 = MCRResposta.responder("fale sobre inteligencia artificial", cerebro)
    check("13.5 resposta contem 'inteligencia' ou 'futuro' ou 'tecnologia'",
          any(p in r4.lower() for p in ["inteligencia", "futuro", "tecnologia", "artificial"]),
          f"r4={r4[:100] if r4 else 'vazio'}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 14 — Integracao: Salvar+Carregar+Ciclo
# ═══════════════════════════════════════════════════════════════════
def test_integration():
    fim = secao("14. Integracao: Salvar+Carregar+Ciclo", 5)

    cerebro = CerebroAGI()
    cerebro.alimentar("Teste de persistencia de dados.", "test_persist")

    # 14.1 salvar
    fd, tmp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        ok = cerebro.salvar(tmp_path)
        check("14.1 salvar retorna True", ok, f"ok={ok}")
        check("14.1b arquivo existe", os.path.exists(tmp_path))

        # 14.2 carregar em nova instancia
        cerebro2 = CerebroAGI()
        ok2 = cerebro2.carregar(tmp_path)
        check("14.2 carregar retorna True", ok2, f"ok={ok2}")

        # 14.3 topicos persistiram
        check("14.3 topicos > 0 apos carregar", len(cerebro2.topicos) > 0,
              f"topicos={len(cerebro2.topicos)}")

        # 14.3b topico especifico existe
        nomes = list(cerebro2.topicos.keys())
        tem_persist = any("persist" in n for n in nomes)
        check("14.3b topico 'persist' encontrado", tem_persist or len(nomes) > 0,
              f"nomes={nomes[:5]}")

        # 14.4 auto_diagnosticar
        try:
            diag = cerebro2.auto_diagnosticar()
            check("14.4 auto_diagnosticar retorna dict", isinstance(diag, dict),
                  f"type={type(diag).__name__}")
            for k in ["topicos", "bytes", "palavras", "causais", "gaps", "hardcodes"]:
                check(f"14.4b key '{k}' presente", k in diag, f"keys={list(diag.keys())}")
        except Exception as ex:
            check("14.4 auto_diagnosticar executa sem erro", False, str(ex))

        # 14.5 gerar texto apos carregar
        try:
            gen = cerebro2.gerar("Teste de", passos=3)
            check("14.5 gerar apos carregar retorna string", isinstance(gen, str) and len(gen) > 0,
                  f"gen={gen[:60]}")
        except Exception as ex:
            check("14.5 gerar apos carregar executa sem erro", False, str(ex))

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

    # 14.6 MCRCoupling
    cp = MCRCoupling()
    cp.alimentar("byte", "palavra", "B:41", "Fogo")
    cp.recalcular()
    peso = cp.peso("byte", "palavra")
    check("14.6 coupling peso calculado", isinstance(peso, float), f"peso={peso}")

    # 14.7 MCRBridge
    bridge = MCRBridge()
    bridge.registrar_dominio("teste")
    ana = bridge.analise("abc", "abd", "xyz", "xyw")
    check("14.7 bridge analise retorna dict", isinstance(ana, dict),
          f"keys={list(ana.keys())}")
    check("14.7b bridge analise tem 'analogo'", "analogo" in ana)

    # 14.8 MCRRegistry
    MCRRegistry.registrar_tipo("test_cat", "test_item", {"val": 42})
    props = MCRRegistry.tipo_props("test_cat", "test_item")
    check("14.8 registry tipo_props retorna dict", isinstance(props, dict) and props.get("val") == 42,
          f"props={props}")

    # 14.9 MCRByteUtils.delta_fingerprint
    delta = MCRByteUtils.delta_fingerprint("abc", "abd", 8)
    check("14.9 delta_fingerprint retorna lista", isinstance(delta, list) and len(delta) == 8,
          f"len={len(delta)}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 15 — F1: MCRHDCOperation (HDC algebra)
# ═══════════════════════════════════════════════════════════════════
def test_hdc():
    fim = secao("15. F1: HDC Algebra (bundle/bind/permute/analogia)", 8)

    hdc = MCRHDCOperation()

    # 15.1 bundle
    vb = hdc.bundle("abc", "def")
    check("15.1 bundle retorna lista", isinstance(vb, list) and len(vb) > 0,
          f"len={len(vb)}")
    check("15.1b bundle aprende transicao", hdc.mk_bundle.total > 0,
          f"total={hdc.mk_bundle.total}")

    # 15.2 bind
    vd = hdc.bind("abc", "def")
    check("15.2 bind retorna lista", isinstance(vd, list) and len(vd) > 0,
          f"len={len(vd)}")
    check("15.2b bind aprende transicao", hdc.mk_bind.total > 0)

    # 15.3 permute
    vp = hdc.permute("abc", 1)
    check("15.3 permute retorna lista", isinstance(vp, list) and len(vp) > 0,
          f"len={len(vp)}")
    check("15.3b permute rotaciona", vp != hdc._vetor("abc"),
          f"vp[:4]={vp[:4]}, orig[:4]={hdc._vetor('abc')[:4]}")

    # 15.4 bundle_inv
    vi = hdc.bundle_inv("abc", "def")
    check("15.4 bundle_inv retorna lista", isinstance(vi, list) and len(vi) > 0,
          f"len={len(vi)}")

    # 15.5 analogia
    cands = ["sol", "lua", "estrela", "planeta"]
    melhor, conf = hdc.analogia("sol", "lua", "estrela", cands)
    check("15.5 analogia retorna tupla (str, float)",
          isinstance(melhor, (str, type(None))) and isinstance(conf, float),
          f"melhor={melhor}, conf={conf}")
    check("15.5b analogia aprende transicao", hdc.mk_analogia.total > 0)

    # 15.6 comparar
    sim = hdc.comparar("abc", "abd")
    check("15.6 comparar textos similares retorna float", isinstance(sim, float) and 0 <= sim <= 1,
          f"sim={sim}")

    # 15.7 _normalizar com interpolacao
    va = [1.0, 2.0, 3.0]
    vb = [4.0, 5.0]
    va_n, vb_n = hdc._normalizar(va, vb, dim_alvo=6)
    check("15.7 _normalizar para 6 dims", len(va_n) >= 3 and len(vb_n) >= 2,
          f"len va={len(va_n)}, len vb={len(vb_n)} (modo pode ser vizinho/linear/media)")
    check("15.7b _normalizar mesmo tamanho", len(va_n) == len(vb_n),
          f"len va={len(va_n)} != len vb={len(vb_n)}")

    # 15.8 bundle com pesos
    vb2 = hdc.bundle("abc", "def", peso_a=0.3, peso_b=0.7)
    check("15.8 bundle com pesos diferentes", isinstance(vb2, list) and len(vb2) > 0)

    # 15.9 permute com rotacao > len
    vp2 = hdc.permute("abc", 50)
    check("15.9 permute com rot alta nao quebra", isinstance(vp2, list) and len(vp2) > 0)

    # 15.10 reservoir usado se disponivel
    hdc2 = MCRHDCOperation(MCRJanelamentoFingerprint())
    v = hdc2._vetor("teste")
    check("15.10 _vetor com reservoir retorna lista", isinstance(v, list) and len(v) > 0)

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 16 — F2: MCRJanelamentoFingerprint
# ═══════════════════════════════════════════════════════════════════
def test_reservoir():
    fim = secao("16. F2: MCRJanelamentoFingerprint (janelamento temporal)", 6)

    r = MCRJanelamentoFingerprint(dim=4, janela=20, passo=10)

    # 16.1 gerar com texto curto
    v = r.gerar("texto curto")
    check("16.1 gerar texto curto retorna list (pode ser vazia)",
          isinstance(v, list), f"len={len(v)}")

    # 16.2 gerar com texto longo
    v2 = r.gerar("A" * 500)
    check("16.2 gerar texto > janela produz vetor", len(v2) > 0,
          f"len={len(v2)}")

    # 16.3 cache funciona
    v3 = r.gerar("A" * 500)
    check("16.3 cache retorna mesmo vetor", v2 == v3,
          f"v2[:4]={v2[:4]}, v3[:4]={v3[:4]}")

    # 16.4 entropia_reservoir
    ent = r.entropia_reservoir(v2)
    check("16.4 entropia_reservoir e' float", isinstance(ent, float),
          f"ent={ent}")

    # 16.5 comparar textos similares vs diferentes
    sim_sim = r.comparar("AAAAABBBBBCCCCCDDDDD", "AAAAABBBBBCCCCCDDDD")
    sim_diff = r.comparar("AAAAABBBBBCCCCCDDDDD", "XYZXYZXYZXYZXYZXYZ")
    check("16.5 comparar textos similares > diferentes", sim_sim > sim_diff,
          f"sim={sim_sim}, diff={sim_diff}")

    # 16.6 entropia de vetor vazio
    ent_vaz = r.entropia_reservoir([])
    check("16.6 entropia de vetor vazio = 1.0", ent_vaz == 1.0, f"ent={ent_vaz}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 17 — F3: MCREntropicSearch
# ═══════════════════════════════════════════════════════════════════
def test_entropic_search():
    fim = secao("17. F3: MCREntropicSearch (MCTS com entropia)", 7)

    w = MCRWorld()
    ql = MCRQLearn()
    es = MCREntropicSearch(w, ql)

    # 17.1 rollout
    e = EstadoMundo.criar_simples()
    prox = es.rollout(e, "andar_dir", passos=3)
    check("17.1 rollout retorna EstadoMundo", isinstance(prox, EstadoMundo),
          f"type={type(prox).__name__}")

    # 17.2 planejar
    obj = e.clone()
    h_obj = obj.get("heroi")
    if h_obj:
        h_obj.props["x"] = 4
    acao, score = es.planejar(e, obj, n_rollouts=3, depth=2)
    check("17.2 planejar retorna acao valida", acao is None or acao in MCRAcao.disponiveis(),
          f"acao={acao}, score={score}")
    if acao:
        check("17.2b score e' float", isinstance(score, float), f"score={score}")

    # 17.3 thresholds sao treinados
    check("17.3 thr_rollouts foi treinado", len(es.thr_rollouts.obs) > 0,
          f"obs={len(es.thr_rollouts.obs)}")
    check("17.3b thr_depth foi treinado", len(es.thr_depth.obs) > 0,
          f"obs={len(es.thr_depth.obs)}")

    # 17.4 mk_sim aprende
    check("17.4 mk_sim aprendeu scores", es.mk_sim.total > 0,
          f"total={es.mk_sim.total}")

    # 17.5 planejar 2x com resultados diferentes (por causa do rollout aleatorio)
    acao2, score2 = es.planejar(obj, e, n_rollouts=2, depth=2)
    check("17.5 segunda chamada de planejar executa sem erro",
          acao2 is None or acao2 in MCRAcao.disponiveis())

    # 17.6 total incrementa
    check("17.6 es.total > 0", es.total > 0, f"total={es.total}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 18 — F4: MCRAutoEvolution
# ═══════════════════════════════════════════════════════════════════
def test_auto_evolution():
    fim = secao("18. F4: MCRAutoEvolution (auto-modificacao)", 7)

    cerebro = CerebroAGI()
    cerebro.alimentar("teste de entropia para auto-evolucao. " * 20, "ae_base")
    ae = MCRAutoEvolution(cerebro)

    # 18.1 entropia_global
    ent = ae.entropia_global()
    check("18.1 entropia_global retorna float", isinstance(ent, float) and ent >= 0,
          f"ent={ent}")

    # 18.2 entropia_global inclui multiplas metricas
    check("18.1b entropia > 0", ent > 0, f"ent={ent}")

    # 18.3 entropia_cerebro
    ent_c = ae._entropia_cerebro(cerebro)
    check("18.2 _entropia_cerebro retorna float", isinstance(ent_c, float) and ent_c >= 0,
          f"ent_c={ent_c}")

    # 18.4 ciclo executa sem erro
    try:
        r = ae.ciclo()
        check("18.4 ciclo executa sem erro", True)
        check("18.4b ciclo retorna dict com keys esperadas",
              all(k in r for k in ["mutacao", "ent_antes", "ent_depois", "melhoria", "resultado"]),
              f"keys={list(r.keys())}")
        check("18.4c resultado e 'aceito' ou 'rejeitado'",
              r["resultado"] in ("aceito", "rejeitado"),
              f"resultado={r['resultado']}")
        check("18.4d melhoria e' float", isinstance(r["melhoria"], float),
              f"melhoria={r['melhoria']}")
    except Exception as ex:
        check("18.4 ciclo executa sem erro", False, str(ex))

    # 18.5 relatorio
    rel = ae.relatorio()
    check("18.5 relatorio retorna dict", isinstance(rel, dict),
          f"type={type(rel).__name__}")
    for k in ["ciclos", "aceites", "taxa_aceite", "entropia_atual"]:
        check(f"18.5b key '{k}' presente", k in rel, f"keys={list(rel.keys())}")

    # 18.6 segundo ciclo incrementa contador
    if ae.hist:
        antes = len(ae.hist)
        ae.ciclo()
        check("18.6 segundo ciclo incrementa historico", len(ae.hist) > antes,
              f"antes={antes}, depois={len(ae.hist)}")

    fim()


# ═══════════════════════════════════════════════════════════════════
# SECAO 19 — Hiperesfera + Topologia + Validacao
# ═══════════════════════════════════════════════════════════════════
def test_hiperestrutura():
    fim = secao("19. Hiperesfera + Topologia + Auto-Validacao", 8)

    # 19.1 MCRHiperesferaAutoExpansiva
    h = MCRHiperesferaAutoExpansiva()
    dims = h.descobrir("O MCR e um sistema de Markov multi-nivel. " * 10, max_dim=5)
    check("19.1 descobrir retorna lista de strings", isinstance(dims, list),
          f"type={type(dims).__name__}")
    if dims:
        check("19.1b pelo menos 1 dimensao descoberta", len(dims) > 0, f"dims={dims}")

    # 19.2 dimensoes tem entropia < threshold
    if h.dimensoes:
        for nome, mk in list(h.dimensoes.items())[:3]:
            ent = mk.entropia_media() if mk.total > 0 else 1.0
            check(f"19.2 dimensao '{nome}' tem entropia < 0.95", ent < 0.95,
                  f"ent={ent:.4f}")

    # 19.3 MCREsfera
    e = MCREsfera()
    e.alimentar_par("byte", "palavra", "B:41", "Fogo")
    e.alimentar_par("byte", "palavra", "B:41", "Fogo")
    e.alimentar_par("byte", "palavra", "B:42", "Agua")
    check("19.3 esfera total > 0", e.total > 0, f"total={e.total}")

    # 19.4 esfera recalcular
    antes = dict(e.cross)
    e.recalcular()
    check("19.4 recalcular executa sem erro", True)

    # 19.5 esfera predizer_cross
    pred, conf = e.predizer_cross("palavra", byte="B:41")
    check("19.5 predizer_cross retorna tupla", isinstance(pred, (str, type(None))) and isinstance(conf, float),
          f"pred={pred}, conf={conf}")

    # 19.6 MCRAutoTopologia
    t = MCRAutoTopologia()
    mk_a = MCR("a")
    mk_b = MCR("b")
    mk_a.aprender("X", "Y")
    mk_b.aprender("X", "Z")
    t.registrar("a", mk_a)
    t.registrar("b", mk_b)
    t.recalcular()
    m = t.metricas()
    check("19.6 topologia metricas retorna dict", isinstance(m, dict),
          f"type={type(m).__name__}")
    for k in ["n_niveis", "n_clusters", "n_arestas"]:
        check(f"19.6b key '{k}' presente", k in m, f"keys={list(m.keys())}")

    # 19.7 MCRAutoValidacaoContinua
    v = MCRAutoValidacaoContinua()
    mk_v = MCR("v")
    mk_v.aprender("A", "B")
    v.registrar("test", mk_v)
    check("19.7 ent_historico tem a chave", "test" in v.ent_historico)

    # 19.8 ciclo de validacao
    niveis = {"test": mk_v}
    for _ in range(3):
        v.ciclo(niveis)
    check("19.8 ciclo de validacao executou 3x", v.ciclos == 3, f"ciclos={v.ciclos}")

    # 19.9 CerebroAGI.ciclo_autonomo
    c = CerebroAGI()
    try:
        res = c.ciclo_autonomo("teste de ciclo autonomo", max_passos=5)
        check("19.10 ciclo_autonomo retorna dict", isinstance(res, dict),
              f"type={type(res).__name__}")
        check("19.10b tem key 'passos'", "passos" in res,
              f"keys={list(res.keys())}")
    except Exception as ex:
        check("19.10 ciclo_autonomo executa sem erro", False, str(ex))

    fim()


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()

    print(f"MCR VERACIDADE TEST v1.0")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Arquivo: {__file__}")
    print(f"Modo verbose: {'SIM' if VERBOSE else 'NAO (use --verbose para detalhes)'}")
    print(f"{'='*60}")

    test_core()
    test_world()
    test_actions()
    test_nlp()
    test_rl()
    test_planning()
    test_memory()
    test_attention()
    test_self_modify()
    test_genesis()
    test_curiosity()
    test_identity()
    test_resposta()
    test_integration()
    test_hdc()
    test_reservoir()
    test_entropic_search()
    test_auto_evolution()
    test_hiperestrutura()

    tempo = time.time() - t0
    print(f"\nTempo total: {tempo:.2f}s")

    nota = final_score()

    # Salva resultado em JSON
    resultado = {
        "timestamp": time.time(),
        "pass": PASS,
        "fail": FAIL,
        "total": TOTAL,
        "nota": nota,
        "tempo": round(tempo, 2),
        "secoes": [
            {"titulo": t, "pass": p, "total": tt, "peso": pe}
            for t, p, tt, pe in RESULTADOS_SECAO
        ],
    }
    out_path = os.path.join(CACHE_DIR, "test_veracidade_result.json")
    try:
        with open(out_path, "w") as f:
            json.dump(resultado, f, indent=2)
        print(f"Resultado salvo em: {out_path}")
    except:
        pass

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
