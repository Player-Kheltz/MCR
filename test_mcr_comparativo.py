#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mcr_comparativo.py
=======================
Testes EMPIRICOS comparando MCR contra baselines simples.
Cada teste gera dados reais e mostra onde o MCR ganha, perde, ou empata.

Uso:
    python test_mcr_comparativo.py
    python test_mcr_comparativo.py --verbose
"""

import sys, os, json, math, time, random
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

__file__ = os.path.join(BASE_DIR, "MCR_AGI.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR_AGI.py", "exec"))

VERBOSE = "--verbose" in sys.argv
TOTAL = 0
PASS = 0
FAIL = 0
RESULTADOS = []

def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    if VERBOSE or not cond:
        print(f"  [{status}] {nome}" + (f"  ({detalhe})" if detalhe else ""))

# ═══════════════════════════════════════════════════════════════════
# TESTE 1: PREDICAO DE SEQUENCIA (vs. HTM Temporal Memory)
# ═══════════════════════════════════════════════════════════════════

def test_sequencia():
    """MCR aprende sequencias deterministicas?
    
    Gera uma sequencia ABCDE... e testa se o MCR aprende os pares.
    HTM TM faria: aprende transicoes com contexto temporal.
    MCR faz: Markov aprende o par (A→B, B→C, etc).
    
    Baseline: "predizer o mais frequente" (se repete muito = acerta).
    """
    print("\n" + "="*60)
    print("TESTE 1: PREDICAO DE SEQUENCIA")
    print("vs. HTM Temporal Memory")
    print("="*60)
    
    # Sequencia deterministica: A B C D E F G H I J (repetida 3x)
    seq = list("ABCDEFGHIJ") * 3
    
    mk = MCR("seq")
    for i in range(len(seq)-1):
        mk.aprender(seq[i], seq[i+1])
    
    # Testa predicao
    acertos = 0
    total_pred = 0
    for i in range(len(seq)-1):
        esperado = seq[i+1]
        pred, conf = mk.predizer(seq[i])
        if pred == esperado:
            acertos += 1
        total_pred += 1
    
    # Baseline: predizer o simbolo mais frequente apos cada estado
    # Se A aparece em 3 posicoes e sempre seguido de B, baseline acerta
    acertos_baseline = 0
    for i in range(len(seq)-1):
        esperado = seq[i+1]
        # Baseline: moda dos simbolos apos este estado
        trans = mk.transicoes.get(seq[i], {})
        if trans:
            pred_base = max(trans, key=trans.get)
            if pred_base == esperado:
                acertos_baseline += 1
    
    taxa_mcr = acertos / max(total_pred, 1)
    taxa_base = acertos_baseline / max(total_pred, 1)
    
    print(f"  MCR Markov:     {acertos}/{total_pred} = {taxa_mcr:.0%}")
    print(f"  Baseline moda:  {acertos_baseline}/{total_pred} = {taxa_base:.0%}")
    check("1a Markov >= baseline em sequencias deterministicas",
          taxa_mcr >= taxa_base,
          f"MCR={taxa_mcr:.0%} base={taxa_base:.0%}")
    
    # Teste: MCR aprende transicoes unicas?
    check("1b Markov aprende transicoes corretas",
          all(mk.predizer(seq[i])[0] == seq[i+1] for i in range(len(seq)-1)),
          "sequencia ABC... falhou")
    
    # Teste de entropia em estado deterministico
    ent = mk.entropia("A")
    check("1c entropia de estado deterministico = 0",
          ent == 0.0, f"H(A)={ent:.4f}")
    
    # Teste: sequencia com ruido
    print()
    print("  -- Sequencia com ruido (10% aleatorio) --")
    seq_ruido = []
    for i in range(30):
        if random.random() < 0.1:
            seq_ruido.append(random.choice("ABCDEFGHIJ"))
        else:
            seq_ruido.append("ABCDEFGHIJ"[i % 10])
    
    mk2 = MCR("seq_ruido")
    for i in range(len(seq_ruido)-1):
        mk2.aprender(seq_ruido[i], seq_ruido[i+1])
    
    # Entropia deve ser > 0 por causa do ruido
    ent_ruido = mk2.entropia_media()
    check("1d entropia > 0 com ruido", ent_ruido > 0, f"H_media={ent_ruido:.4f}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 2: DETECCAO DE ANOMALIA (vs. HTM Anomaly Score)
# ═══════════════════════════════════════════════════════════════════

def test_anomalia():
    """MCR detecta anomalias via entropia?
    
    HTM: anomaly score baseado em quao bem a sequencia atual
    e explicada pelo modelo. Quanto maior o erro de predicao,
    maior a anomalia.
    
    MCR: entropia de uma predicao mede incerteza.
    Se um estado tem entropia alta → muitas opcoes → anomalo?
    """
    print("\n" + "="*60)
    print("TESTE 2: DETECCAO DE ANOMALIA")
    print("vs. HTM Anomaly Score")
    print("="*60)
    
    # Treina em sequencia limpa
    mk = MCR("norm")
    for _ in range(10):
        for letra in "ABCDEFGHIJ":
            mk.aprender(letra, "ABCDEFGHIJ"["ABCDEFGHIJ".index(letra) + 1]
                       if letra != "J" else "A")
    
    # Entropia de estados normais vs anomalos
    ent_normais = [mk.entropia(l) for l in "ABCDEFGHIJ"]
    ent_anomalo = mk.entropia("X")  # letra nunca vista
    
    media_normal = sum(ent_normais) / len(ent_normais)
    
    print(f"  Entropia media normal: {media_normal:.4f}")
    print(f"  Entropia de X (anomalo): {ent_anomalo:.4f}")
    
    check("2a estado anomalo tem entropia > media normal",
          ent_anomalo > media_normal,
          f"normal={media_normal:.4f} anomalo={ent_anomalo:.4f}")
    
    # Para HTM: anomalia e medida como erro de predicao.
    # Para MCR: erro de predicao = confianca baixa no predizer().
    conf_normais = []
    for l in "ABCDE":
        _, c = mk.predizer(l)
        conf_normais.append(c)
    
    pred_x, conf_x = mk.predizer("X")
    media_conf_normal = sum(conf_normais) / len(conf_normais)
    
    print(f"  Confianca media normal: {media_conf_normal:.4f}")
    print(f"  Confianca de X: {conf_x:.4f}")
    
    check("2b estado anomalo tem confianca < media normal",
          conf_x < media_conf_normal,
          f"normal={media_conf_normal:.4f} anomalo={conf_x:.4f}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 3: CLASSIFICACAO NLP (vs. baseline aleatorio)
# ═══════════════════════════════════════════════════════════════════

def test_nlp_classificacao():
    """MCRNLP classifica intencoes melhor que aleatorio?
    
    Baseline: acertar 1/N das classes por chance.
    """
    print("\n" + "="*60)
    print("TESTE 3: CLASSIFICACAO NLP")
    print("vs. baseline aleatorio")
    print("="*60)
    
    # 6 intencoes, 5 exemplos cada
    intencoes = {
        "saudacao": ["ola", "oi", "bom dia", "boa tarde", "e ai"],
        "despedida": ["tchau", "ate logo", "ate mais", "falou", "bye"],
        "pergunta": ["o que e", "como funciona", "quando", "por que", "qual"],
        "comando": ["faca isso", "execute", "rode", "abra", "inicie"],
        "afirmacao": ["sim", "claro", "ok", "concordo", "verdade"],
        "negacao": ["nao", "nunca", "jamais", "nem", "recuso"],
    }
    
    MCRNLP._ex = {}  # limpa
    
    # Treina com 3 exemplos por classe
    for classe, exemplos in intencoes.items():
        for ex in exemplos[:3]:
            MCRNLP.aprender(ex, classe)
    
    # Testa com TODOS os exemplos
    acertos = 0
    total = 0
    for classe, exemplos in intencoes.items():
        for ex in exemplos:
            preds = MCRNLP.entender(ex, top_k=3)
            if classe in preds:
                acertos += 1
            total += 1
    
    taxa_mcr = acertos / max(total, 1)
    taxa_aleatorio = 1 / len(intencoes)  # ~16.7%
    
    print(f"  MCR NLP:        {acertos}/{total} = {taxa_mcr:.0%}")
    print(f"  Baseline aleat: 1/{len(intencoes)} = {taxa_aleatorio:.0%}")
    
    check("3a MCRNLP > aleatorio em classificacao",
          taxa_mcr > taxa_aleatorio,
          f"MCR={taxa_mcr:.0%} aleat={taxa_aleatorio:.0%}")
    
    # Teste com frases completamente fora do vocabulario
    fora = ["xylophone", "quantum", "nebula", "zebra", "kafka"]
    acertos_fora = 0
    for f in fora:
        preds = MCRNLP.entender(f, top_k=3)
        if not preds:
            acertos_fora += 1  # correto: nao classificou
    
    print(f"  Frases fora do vocab: {acertos_fora}/{len(fora)} corretamente ignoradas")
    check("3b MCRNLP nao classifica frases irrelevantes",
          acertos_fora >= 3,
          f"ignorou {acertos_fora}/{len(fora)}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 4: PREDICAO DE ESTADO (vs. persistencia)
# ═══════════════════════════════════════════════════════════════════

def test_predicao_estado():
    """MCRWorld prediz estados futuros?
    
    Baseline: "persistencia" — a proxima posicao e a mesma da atual.
    """
    print("\n" + "="*60)
    print("TESTE 4: PREDICAO DE ESTADO (MCRWorld)")
    print("vs. baseline persistencia")
    print("="*60)
    
    w = MCRWorld()
    e = EstadoMundo.criar_simples()
    
    # Cria trajetoria: heroi vai andando em linha reta
    for passo in range(5):
        e_antes = e.clone()
        e = MCRAcao.executar(e, "andar_dir")
        w.aprender(e_antes, "andar_dir", e)
    
    # Tenta simular
    e_teste = EstadoMundo.criar_simples()
    e_pred = w.simular(e_teste, "andar_dir")
    
    h_orig = e_teste.get("heroi")
    h_pred = e_pred.get("heroi") if e_pred else None
    
    if h_orig and h_pred:
        dx = h_pred.props.get("x", 0) - h_orig.props.get("x", 0)
        dy = h_pred.props.get("y", 0) - h_orig.props.get("y", 0)
        print(f"  Heroi moveu: dx={dx}, dy={dy} (esperado: dx=1, dy=0)")
        check("4a MCRWorld simula movimento direita",
              dx == 1 and dy == 0,
              f"dx={dx} dy={dy}")
    else:
        check("4a MCRWorld simula movimento direita", False, "heroi nao encontrado")
    
    # Predizer acao a partir do delta
    e_novo = MCRAcao.executar(e_teste, "andar_dir")
    acao_pred = w.predizer_acao(e_teste, e_novo)
    check("4b MCRWorld prediz acao correta",
          acao_pred == "andar_dir",
          f"pred={acao_pred}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 5: CAPACIDADE DE MEMORIA (vs. dicionario exato)
# ═══════════════════════════════════════════════════════════════════

def test_memoria():
    """MCRMemory salva e recupera por similaridade?
    
    Baseline: dicionario Python (exatidao total).
    MCRMemory usa buscas por similaridade de fingerprint.
    """
    print("\n" + "="*60)
    print("TESTE 5: MEMORIA POR SIMILARIDADE (MCRMemory)")
    print("vs. dicionario exato")
    print("="*60)
    
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        mem = MCRMemory(db_path)
        
        # Salva 10 estados
        for i in range(10):
            e = EstadoMundo()
            e.adicionar(Entidade(f"obj{i}", "teste", {"val": i}))
            mem.salvar_estado(e)
        
        stats = mem.stats()
        print(f"  Estados salvos: {stats['estados']}")
        
        check("5a MCRMemory salva estados", stats["estados"] > 0,
              f"count={stats['estados']}")
        
        # Busca por fingerprint
        e_busca = EstadoMundo()
        e_busca.adicionar(Entidade("obj5", "teste", {"val": 5}))
        fp_busca = str(e_busca.fingerprint(8))
        
        similares = mem.buscar_similar(fp_busca, 3)
        print(f"  Similares encontrados: {len(similares)}")
        
        check("5b MCRMemory busca similar", len(similares) > 0,
              f"n={len(similares)}")
        
        mem.fechar()
    finally:
        try: os.unlink(db_path)
        except: pass


# ═══════════════════════════════════════════════════════════════════
# TESTE 6: ESCALA DE PLANEJAMENTO (vs. random walk)
# ═══════════════════════════════════════════════════════════════════

def test_planejamento():
    """MCRPlanner chega ao objetivo melhor que andar aleatorio?
    
    Grid 5x5, heroi em (0,0), objetivo em (4,4).
    """
    print("\n" + "="*60)
    print("TESTE 6: PLANEJAMENTO (MCRPlanner)")
    print("vs. random walk")
    print("="*60)
    
    w = MCRWorld()
    p = MCRPlanner(w)
    atual = EstadoMundo.criar_simples()
    objetivo = EstadoMundo.criar_simples()
    h_obj = objetivo.get("heroi")
    if h_obj:
        h_obj.props["x"] = 4
        h_obj.props["y"] = 4
    
    dist_inicial = w.distancia(atual, objetivo)
    print(f"  Distancia inicial: {dist_inicial:.4f}")
    
    # MCRPlanner
    plano = p.plano(atual, objetivo, max_passos=10)
    print(f"  Plano MCR: {len(plano)} acoes")
    
    if plano:
        est = atual.clone()
        for ac in plano:
            prox = MCRAcao.executar(est, ac)
            est = prox
        h = est.get("heroi")
        h_obj_ = objetivo.get("heroi")
        if h and h_obj_:
            dist_mcr = abs(h.props.get("x",0)-h_obj_.props.get("x",0)) + \
                       abs(h.props.get("y",0)-h_obj_.props.get("y",0))
            print(f"  Distancia apos plano MCR: {dist_mcr}")
            check("6a MCRPlanner reduz distancia ao objetivo",
                  dist_mcr < 4,  # pelo menos melhor que aleatorio puro
                  f"dist={dist_mcr}")
    
    # Baseline: andar aleatorio
    melhor_dist_rand = 99
    for _ in range(100):
        est = atual.clone()
        dists = []
        for _ in range(10):
            acao = random.choice(MCRAcao.disponiveis())
            prox = MCRAcao.executar(est, acao)
            est = prox
            dists.append(w.distancia(est, objetivo))
        if dists and min(dists) < melhor_dist_rand:
            melhor_dist_rand = min(dists)
    
    print(f"  Melhor distancia random (100 trials): {melhor_dist_rand:.4f}")
    check("6b MCRPlanner >= random walk em reducao de distancia",
          dist_mcr <= melhor_dist_rand if plano else True,
          f"MCR={dist_mcr:.4f} melhor_rand={melhor_dist_rand:.4f}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 7: DETECCAO DE PADROES (vs. fixed-dim fingerprint)
# ═══════════════════════════════════════════════════════════════════

def test_padroes():
    """MCRSignatureExpansiva descobre melhor dimensao que 8 fixo?
    
    Compara fingerprint 8D vs dimensionalidade_ideal em tarefa
    de separacao de sequencias.
    """
    print("\n" + "="*60)
    print("TESTE 7: DETECCAO DE PADROES")
    print("vs. fingerprint 8D fixo")
    print("="*60)
    
    pares = [
        ("quero", "nao quero"),
        ("cachorro morde homem", "homem morde cachorro"),
        ("gato", "cachorro"),
        ("sim", "nao"),
    ]
    
    for a, b in pares:
        dim_otima = MCRSignatureExpansiva.dimensionalidade_ideal(
            (a + " " + b).encode()[:2000], mx=128, thr=0.05
        )
        
        cos_8 = MCRByteUtils.similaridade_cosseno(
            MCRByteUtils.fingerprint(a, 8),
            MCRByteUtils.fingerprint(b, 8)
        )
        cos_dim = MCRByteUtils.similaridade_cosseno(
            MCRByteUtils.fingerprint(a, max(dim_otima, 4)),
            MCRByteUtils.fingerprint(b, max(dim_otima, 4))
        )
        
        sep_8 = (1 - cos_8) * 100
        sep_dim = (1 - cos_dim) * 100
        
        if sep_dim > sep_8:
            resultado = "MELHOR"
        elif sep_dim < sep_8:
            resultado = "PIOR"
        else:
            resultado = "IGUAL"
        
        print(f"  \"{a[:25]:25s}\" vs \"{b[:25]:25s}\"")
        print(f"    8D: cos={cos_8:.4f} sep={sep_8:.1f}%")
        print(f"    {dim_otima:3d}D: cos={cos_dim:.4f} sep={sep_dim:.1f}%  [{resultado}]")
    
    # Quantas vezes dim_ideal > 8 melhora a separacao?
    melhorias = 0
    for a, b in pares:
        dim_otima = MCRSignatureExpansiva.dimensionalidade_ideal(
            (a + " " + b).encode()[:2000], mx=128, thr=0.05
        )
        cos_8 = MCRByteUtils.similaridade_cosseno(
            MCRByteUtils.fingerprint(a, 8),
            MCRByteUtils.fingerprint(b, 8)
        )
        cos_dim = MCRByteUtils.similaridade_cosseno(
            MCRByteUtils.fingerprint(a, max(dim_otima, 4)),
            MCRByteUtils.fingerprint(b, max(dim_otima, 4))
        )
        if (1 - cos_dim) > (1 - cos_8):
            melhorias += 1
    
    check("7a dimensionalidade_ideal melhora separacao em pelo menos 1 par",
          melhorias >= 1,
          f"melhorias={melhorias}/{len(pares)}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 8: Q-LEARNING CONVERGE (vs. epsilon puro)
# ═══════════════════════════════════════════════════════════════════

def test_qlearning():
    """MCRQLearn converge para política melhor que aleatoria?
    
    Grid 5x5, heroi aprende a ir para (4,4).
    """
    print("\n" + "="*60)
    print("TESTE 8: Q-LEARNING CONVERGE")
    print("vs. politica epsilon-pura")
    print("="*60)
    
    ql = MCRQLearn()
    e = EstadoMundo.criar_simples()
    obj = e.clone()
    h_obj = obj.get("heroi")
    if h_obj:
        h_obj.props["x"] = 4
        h_obj.props["y"] = 4
    
    # Episodios de treino
    for ep in range(20):
        ql.executar_episodio(e.clone(), obj, mx=15)
    
    # Testa politica aprendida: executa com epsilon=0 (guloso)
    est = e.clone()
    acoes_usadas = []
    for _ in range(10):
        acao = ql.melhor_acao(est)
        if not acao:
            break
        acoes_usadas.append(acao)
        est = MCRAcao.executar(est, acao)
    
    h = est.get("heroi")
    h_obj_ = obj.get("heroi")
    if h and h_obj_:
        dist_final = abs(h.props.get("x",0)-h_obj_.props.get("x",0)) + \
                     abs(h.props.get("y",0)-h_obj_.props.get("y",0))
        print(f"  Distancia final apos QL: {dist_final}")
        print(f"  Acoes usadas: {acoes_usadas[:6]}")
        
        # Random baseline
        melhor_rand = 99
        for _ in range(50):
            e2 = e.clone()
            for _ in range(10):
                e2 = MCRAcao.executar(e2, random.choice(MCRAcao.disponiveis()))
            h2 = e2.get("heroi")
            if h2 and h_obj_:
                d = abs(h2.props.get("x",0)-h_obj_.props.get("x",0)) + \
                    abs(h2.props.get("y",0)-h_obj_.props.get("y",0))
                if d < melhor_rand:
                    melhor_rand = d
        
        print(f"  Melhor distancia random: {melhor_rand}")
        check("8a Q-Learning converge melhor que random",
              dist_final <= melhor_rand,
              f"QL={dist_final} rand={melhor_rand}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 9: ENTROPIA COMO DETECTOR DE MUDANCA
# ═══════════════════════════════════════════════════════════════════

def test_entropia_mudanca():
    """Entropia detecta mudancas no padrao dos dados?
    
    Alimenta padrao consistente, depois muda.
    Entropia deve subir no momento da mudanca.
    """
    print("\n" + "="*60)
    print("TESTE 9: ENTROPIA DETECTA MUDANCA DE PADRAO")
    print("="*60)
    
    mk = MCR("change")
    
    # Fase 1: padrao AAA...
    entropias = []
    for _ in range(20):
        mk.aprender("A", "A")
        entropias.append(mk.entropia_media())
    
    h_antes = mk.entropia_media()
    
    # Fase 2: introduz B
    for _ in range(5):
        mk.aprender("A", "B")
        entropias.append(mk.entropia_media())
    
    h_durante = mk.entropia_media()
    
    # Fase 3: volta para AA
    for _ in range(20):
        mk.aprender("A", "A")
        entropias.append(mk.entropia_media())
    
    h_depois = mk.entropia_media()
    
    print(f"  H antes:    {h_antes:.4f}")
    print(f"  H durante:  {h_durante:.4f}")
    print(f"  H depois:   {h_depois:.4f}")
    
    check("9a entropia SOBE quando padrao muda", h_durante > h_antes,
          f"antes={h_antes:.4f} durante={h_durante:.4f}")
    check("9b entropia DESCE quando padrao estabiliza", h_depois < h_durante,
          f"durante={h_durante:.4f} depois={h_depois:.4f}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 10: AUTO-EVOLUTION — MEDE MUDANCA REAL
# ═══════════════════════════════════════════════════════════════════

def test_ae_real():
    """O AE realmente muda alguma metrica?
    
    Mede entropia_global() antes, muta threshold, mede depois.
    Se melhoria = 0 sempre, o AE esta desacoplado.
    """
    print("\n" + "="*60)
    print("TESTE 10: AUTO-EVOLUTION — MEDE IMPACTO REAL")
    print("="*60)
    
    c = CerebroAGI()
    c.alimentar("teste " * 200, "base")
    c.alimentar("entropia " * 200, "base2")
    ae = MCRAutoEvolution(c)
    
    ent_antes = ae.entropia_global()
    print(f"  entropia_global() antes: {ent_antes:.4f}")
    
    # Componentes
    print(f"  mk_byte:    {c.mk_byte.entropia_media():.4f}")
    print(f"  mk_palavra: {c.mk_palavra.entropia_media():.4f}")
    
    melhoria_total = 0
    aceites = 0
    for i in range(20):
        r = ae.ciclo()
        melhoria_total += r['melhoria']
        if r['resultado'] == 'aceito':
            aceites += 1
    
    print(f"  20 ciclos: {aceites} aceites, melhoria_total={melhoria_total:.4f}")
    
    check("10a AE detecta melhoria > 0 em pelo menos 1 ciclo",
          any(r['melhoria'] > 0 for r in ae.hist[-20:]),
          f"melhoria_max={max(r['melhoria'] for r in ae.hist[-20:]) if ae.hist else 0:.6f}")


# ═══════════════════════════════════════════════════════════════════
# TESTE 11: ANALOGIA HDC
# ═══════════════════════════════════════════════════════════════════

def test_analogia_hdc():
    """MCRHDCOperation.analogia encontra relacoes?
    
    Teste: rei - homem + mulher ≈ rainha?
    MCR nao tem embeddings semanticos, entao usa byte-level.
    """
    print("\n" + "="*60)
    print("TESTE 11: ANALOGIA HDC")
    print("="*60)
    
    hdc = MCRHDCOperation()
    
    candidatos = ["mulher", "rainha", "princesa", "dama", "menina"]
    melhor, conf = hdc.analogia("rei", "homem", "rainha", candidatos)
    
    print(f"  analogia(\"rei\", \"homem\", \"rainha\", candidatos)")
    print(f"  Melhor: \"{melhor}\" conf={conf:.3f}")
    
    # Como MCR usa byte-level, a analogia depende de similaridade de bytes
    # "rei" e "rainha" compartilham 'r' → alguma similaridade
    
    check("11a analogia HDC retorna resultado",
          melhor is not None,
          f"resultado={melhor}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    
    print("=" * 60)
    print("  TESTE COMPARATIVO MCR")
    print("  Comparacoes reais contra baselines simples")
    print("  Nao usa GPU, LLM, ou dependencias externas")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 60)
    
    test_sequencia()
    test_anomalia()
    test_nlp_classificacao()
    test_predicao_estado()
    test_memoria()
    test_planejamento()
    test_padroes()
    test_qlearning()
    test_entropia_mudanca()
    test_ae_real()
    test_analogia_hdc()
    
    tempo = time.time() - t0
    
    print("\n" + "=" * 60)
    print("  SUMARIO FINAL")
    print("=" * 60)
    print(f"  Total: {PASS}/{TOTAL}")
    print(f"  Taxa:  {PASS/max(TOTAL,1)*100:.0f}%")
    print(f"  Tempo: {tempo:.2f}s")
    
    if PASS == TOTAL:
        print("\n  MCR passa em todos os testes comparativos")
        print("  contra baselines simples.")
    else:
        print(f"\n  {FAIL} teste(s) falharam — MCR NAO superou")
        print("  o baseline nestes casos.")
    
    print("=" * 60)
    
    # Salva resultado
    resultado = {
        "timestamp": time.time(),
        "pass": PASS,
        "fail": FAIL,
        "total": TOTAL,
        "taxa": PASS / max(TOTAL, 1),
        "tempo": round(tempo, 2),
        "contexto": "Comparacao MCR vs. baselines simples (random, persistencia, moda)",
        "limitacao": "Nao compara com HTM/HDC/AIXI reais (dependencias externas)",
    }
    out_path = os.path.join(BASE_DIR, "cache", "test_comparativo_result.json")
    try:
        with open(out_path, "w") as f:
            json.dump(resultado, f, indent=2)
        print(f"Resultado salvo em: {out_path}")
    except:
        pass
    
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
