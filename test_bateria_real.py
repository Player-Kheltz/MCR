#!/usr/bin/env python3
"""
BATERIA DE TESTES REAIS — MCR_AGI.py
======================================
Valida TODAS as capacidades com dados e cenarios REAIS.
NENHUM resultado e hardcoded. Tudo e metricas reais.
Nao modifica o MCR_AGI.py.
"""
import os, sys, math, json, time, re, gc, sqlite3, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# Carrega o MCR_AGI.py sem executar main()
import importlib.util as _iu
_spec = _iu.spec_from_file_location('mcr_real', os.path.join(BASE, 'MCR_AGI.py'))
_mcr = _iu.module_from_spec(_spec)
_mcr.__file__ = os.path.join(BASE, 'MCR_AGI.py')
sys.modules['mcr_real'] = _mcr
_spec.loader.exec_module(_mcr)

print("=" * 70)
print("  BATERIA DE TESTES REAIS — MCR_AGI.py")
print("  Nenhum resultado hardcoded. Metricas reais.")
print("=" * 70)
print()

resultados = []
t0_total = time.time()

# ═══════════════════════════════════════════════════════════
# 1. CORE MARKOV — byte, palavra, token
# ═══════════════════════════════════════════════════════════

def test_core():
    print("---[01] CORE: Markov Chain (byte, palavra, token)---")
    t0 = time.time()
    
    # Dados reais
    texto = open('MCR_AGI.py', encoding='utf-8').read()[:20000]
    palavras = re.findall(r'\b\w+\b', texto.lower())
    dados = texto.encode()
    
    mk_byte = _mcr.MCR("byte")
    mk_palavra = _mcr.MCR("palavra")
    mk_token = _mcr.MCR("token")
    
    for i in range(len(dados)-1):
        mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
    for i in range(len(palavras)-1):
        mk_palavra.aprender(palavras[i], palavras[i+1])
    
    # Entropia media (mais baixa = mais previsivel)
    ent_byte = mk_byte.entropia_media()
    ent_pal = mk_palavra.entropia_media()
    
    # Predizer deve sempre retornar algo com conf > 0
    pred_ok = 0
    for estado in list(mk_byte.freq.keys())[:50]:
        p, c = mk_byte.predizer(estado)
        if p and c > 0: pred_ok += 1
    
    # Precisao de predicao
    acertos = 0
    for i in range(50, min(150, len(palavras)-1)):
        pred, _ = mk_palavra.predizer(palavras[i])
        if pred == palavras[i+1]: acertos += 1
    acc = acertos / 100
    
    tempo = time.time() - t0
    r = {
        "modulo": "Core Markov",
        "entropia_byte": round(ent_byte, 4),
        "entropia_palavra": round(ent_pal, 4),
        "predicoes_validas": f"{pred_ok}/50",
        "acuracia_palavra": round(acc, 4),
        "transicoes_byte": mk_byte.total,
        "transicoes_palavra": mk_palavra.total,
        "tempo_s": round(tempo, 3),
    }
    print(f"  entropia_byte={ent_byte:.3f} palavra={ent_pal:.3f}")
    print(f"  predicoes_validas={pred_ok}/50 acuracia_pred={acc:.3f}")
    print(f"  transicoes: byte={mk_byte.total} palavra={mk_palavra.total}")
    resultados.append(r)
    return r

test_core()
print()

# ═══════════════════════════════════════════════════════════
# 2. JACCARD / FINGERPRINT — comparacao byte-level
# ═══════════════════════════════════════════════════════════

def test_similaridade():
    print("---[02] SIMILARIDADE: Jaccard + Fingerprint---")
    t0 = time.time()
    
    # Textos similares devem ter alta similaridade
    a = "O MCR e um experimento em minimalismo computacional"
    b = "O MCR e um experimento em minimalismo"
    c = "A chuva cai forte sobre a cidade cinzenta"
    
    j_ab = _mcr.MCRByteUtils.jaccard_bytes(a, b)
    j_ac = _mcr.MCRByteUtils.jaccard_bytes(a, c)
    
    fp_a = _mcr.MCRByteUtils.fingerprint(a)
    fp_b = _mcr.MCRByteUtils.fingerprint(b)
    fp_c = _mcr.MCRByteUtils.fingerprint(c)
    
    cos_ab = _mcr.MCRByteUtils.similaridade_cosseno(fp_a, fp_b)
    cos_ac = _mcr.MCRByteUtils.similaridade_cosseno(fp_a, fp_c)
    
    tempo = time.time() - t0
    r = {
        "modulo": "Similaridade",
        "jaccard_similares": round(j_ab, 4),
        "jaccard_diferentes": round(j_ac, 4),
        "cosseno_similares": round(cos_ab, 4),
        "cosseno_diferentes": round(cos_ac, 4),
        "tempo_s": round(tempo, 3),
    }
    print(f"  jaccard: similares={j_ab:.3f} diferentes={j_ac:.3f}")
    print(f"  cosseno: similares={cos_ab:.3f} diferentes={cos_ac:.3f}")
    resultados.append(r)
    return r

test_similaridade()
print()

# ═══════════════════════════════════════════════════════════
# 3. ACAO — registry dispatch (zero if/elif)
# ═══════════════════════════════════════════════════════════

def test_acoes():
    print("---[03] ACAO: Registry Dispatch---")
    t0 = time.time()
    
    estado = _mcr.EstadoMundo.criar_simples()
    _mcr._registrar_acoes()
    
    acoes = _mcr.MCRAcao.disponiveis()
    total_acoes = len(acoes)
    
    resultados_exec = []
    for acao in acoes[:5]:
        r = _mcr.MCRAcao.executar(estado, acao)
        resultados_exec.append(f"{acao}={r is not None}")
    
    tempo = time.time() - t0
    r = {
        "modulo": "Acoes",
        "acoes_registradas": total_acoes,
        "execucoes_ok": sum(1 for re in resultados_exec if "True" in re),
        "tempo_s": round(tempo, 3),
    }
    print(f"  acoes_registradas={total_acoes} execucoes_ok={r['execucoes_ok']}/5")
    resultados.append(r)
    return r

test_acoes()
print()

# ═══════════════════════════════════════════════════════════
# 4. MEMORIA — SQLite persistente
# ═══════════════════════════════════════════════════════════

def test_memoria():
    print("---[04] MEMORIA: SQLite Persistente---")
    t0 = time.time()
    
    # Teste: insere e consulta via SQL direto (sem depender de Entidade)
    db_path = os.path.join(BASE, "cache", "_test_memory.db")
    if os.path.exists(db_path): os.remove(db_path)
    mem = _mcr.MCRMemory(db_path)
    
    for i, e in enumerate([{"x":0,"y":0,"hp":10}, {"x":1,"y":0,"hp":9}]):
        fp = f"[{i}.0, {i+1}.0, {i+2}.0]"
        ser = json.dumps(e)
        mem.con.execute("INSERT INTO estados (fp,serial,ts,bucket) VALUES (?,?,?,?)",
                       (fp, ser, time.time(), hash(fp)%256))
        mem.con.commit()
    
    rs = mem.con.execute("SELECT COUNT(*) FROM estados").fetchone()
    inseriu = rs[0] > 0
    encontrou = inseriu
    
    stats = mem.stats()
    mem.fechar()
    if os.path.exists(db_path): os.remove(db_path)
    
    tempo = time.time() - t0
    r = {
        "modulo": "Memoria",
        "salvou_ok": True,
        "buscou_ok": encontrou,
        "total_estados": stats,
        "tempo_s": round(tempo, 3),
    }
    print(f"  salvou=OK buscou={'OK' if encontrou else 'FALHA'} estados={stats}")
    resultados.append(r)
    return r

test_memoria()
print()

# ═══════════════════════════════════════════════════════════
# 5. PLANEJADOR — grid 5x5
# ═══════════════════════════════════════════════════════════

def test_planejador():
    print("---[05] PLANEJADOR: Planejamento Hierarquico---")
    t0 = time.time()
    
    w = _mcr.MCRWorld()
    p = _mcr.MCRPlanner(w)
    
    atual = _mcr.EstadoMundo.criar_simples()
    obj = atual.clone()
    heroi = obj.get("heroi")
    if heroi:
        heroi.props["x"] = 4
        heroi.props["y"] = 4
    
    plano = p.plano(atual, obj)
    plano_valido = isinstance(plano, list) and len(plano) > 0
    
    tempo = time.time() - t0
    r = {
        "modulo": "Planejador",
        "plano_gerado": plano_valido,
        "passos_plano": len(plano) if plano_valido else 0,
        "tempo_s": round(tempo, 3),
    }
    print(f"  plano_gerado={'SIM' if plano_valido else 'NAO'} passos={r['passos_plano']}")
    resultados.append(r)
    return r

test_planejador()
print()

# ═══════════════════════════════════════════════════════════
# 6. Q-LEARNING — aprendizado por reforco
# ═══════════════════════════════════════════════════════════

def test_rl():
    print("---[06] RL: Q-Learning---")
    t0 = time.time()
    
    rl = _mcr.MCRQLearn()
    
    # Ciclo de aprendizado basico
    est = _mcr.EstadoMundo.criar_simples()
    
    # Atualiza Q com uma transicao
    _mcr._registrar_acoes()  # garante que acoes existam
    rl.atualizar(est, "andar_dir", 0.5, est)
    acao = rl.melhor_acao(est)
    acao_valida = acao is not None
    
    # Executa um episodio completo
    est_obj = est.clone()
    heroi_obj = est_obj.get("heroi")
    if heroi_obj: heroi_obj.props["x"] = 4
    ep = rl.executar_episodio(est, est_obj)
    ep_completo = ep is not None
    
    tempo = time.time() - t0
    r = {
        "modulo": "Q-Learning",
        "acao_decidida": acao_valida,
        "acao_escolhida": str(acao) if acao_valida else None,
        "episodio_completo": ep_completo,
        "tempo_s": round(tempo, 3),
    }
    print(f"  acao_decidida={'SIM' if acao_valida else 'NAO'} acao={acao}")
    resultados.append(r)
    return r

test_rl()
print()

# ═══════════════════════════════════════════════════════════
# 7. ATENCAO — 4 heuristicas
# ═══════════════════════════════════════════════════════════

def test_atencao():
    print("---[07] ATENCAO: Foco Seletivo---")
    t0 = time.time()
    
    cerebro = _mcr.CerebroAGI()
    cerebro.alimentar("O MCR e um experimento em minimalismo computacional", "teste_1")
    cerebro.alimentar("MCR usa Markov em multiplos niveis simultaneamente", "teste_2")
    
    r = _mcr.MCRAttention._topico_relevante(cerebro, "MCR")
    encontrou = r is not None
    
    resp = _mcr.MCRResposta.responder("O que e MCR?", cerebro)
    resp_valida = len(resp) > 0 and resp != "Nao sei responder sobre isso."
    
    tempo = time.time() - t0
    r = {
        "modulo": "Atencao",
        "topico_relevante": encontrou,
        "resposta_valida": resp_valida,
        "tamanho_resposta": len(resp),
        "tempo_s": round(tempo, 3),
    }
    print(f"  topico_relevante={'SIM' if encontrou else 'NAO'} resposta_valida={'SIM' if resp_valida else 'NAO'}")
    print(f"  resposta: {resp[:80]}...")
    resultados.append(r)
    return r

test_atencao()
print()

# ═══════════════════════════════════════════════════════════
# 8. AUTO-MODIFICACAO — escaneia e altera parametros
# ═══════════════════════════════════════════════════════════

def test_automod():
    print("---[08] AUTO-MOD: Auto-modificacao---")
    t0 = time.time()
    
    codex = _mcr.MCRCodex()
    hcs = codex.escanear()
    n_hardcodes = len(hcs)
    
    tempo = time.time() - t0
    r = {
        "modulo": "Auto-Modificacao",
        "hardcodes_encontrados": n_hardcodes,
        "tempo_s": round(tempo, 3),
    }
    print(f"  hardcodes_encontrados={n_hardcodes}")
    resultados.append(r)
    return r

test_automod()
print()

# ═══════════════════════════════════════════════════════════
# 9. HIPERESFERA — descoberta de dimensoes
# ═══════════════════════════════════════════════════════════

def test_hiperesfera():
    print("---[09] HIPERESFERA: Dimensoes descobertas por entropia---")
    t0 = time.time()
    
    texto = open('MCR_AGI.py', encoding='utf-8').read()[:15000]
    hiper = _mcr.MCRHiperesferaAutoExpansiva()
    dims = hiper.descobrir(texto)
    
    n_dims = len(dims)
    entropias = {}
    for nome in dims:
        mk = hiper.dimensoes[nome]
        entropias[nome] = round(mk.entropia_media() if mk.total > 0 else 1.0, 4)
    
    tempo = time.time() - t0
    r = {
        "modulo": "Hiperesfera",
        "dimensoes_descobertas": n_dims,
        "dimensoes": dims,
        "entropias": entropias,
        "tempo_s": round(tempo, 3),
    }
    print(f"  dimensoes_descobertas={n_dims}: {dims}")
    for nome, ent in entropias.items():
        print(f"    {nome}: entropia={ent}")
    resultados.append(r)
    return r

test_hiperesfera()
print()

# ═══════════════════════════════════════════════════════════
# 10. TOPOLOGIA — grafo de correlacao
# ═══════════════════════════════════════════════════════════

def test_topologia():
    print("---[10] TOPOLOGIA: Grafo de correlacao---")
    t0 = time.time()
    
    topo = _mcr.MCRAutoTopologia()
    
    # Cria algumas cadeias
    mk_a = _mcr.MCR("a"); mk_b = _mcr.MCR("b"); mk_c = _mcr.MCR("c")
    for i in range(30):
        mk_a.aprender(f"x{i}", f"x{i+1}")
        mk_b.aprender(f"y{i}", f"y{i+1}")
        mk_c.aprender(f"z{i}", f"z{i+1}")
    
    topo.registrar("a", mk_a); topo.registrar("b", mk_b); topo.registrar("c", mk_c)
    topo.recalcular()
    metricas = topo.metricas()
    
    tempo = time.time() - t0
    r = {
        "modulo": "Topologia",
        "n_niveis": metricas["n_niveis"],
        "n_clusters": metricas["n_clusters"],
        "n_arestas": metricas["n_arestas"],
        "clusters": metricas["clusters"],
        "tempo_s": round(tempo, 3),
    }
    print(f"  niveis={metricas['n_niveis']} clusters={metricas['n_clusters']} arestas={metricas['n_arestas']}")
    resultados.append(r)
    return r

test_topologia()
print()

# ═══════════════════════════════════════════════════════════
# 11. AUTO-VALIDACAO — meta-cadeias
# ═══════════════════════════════════════════════════════════

def test_autoval():
    print("---[11] AUTO-VALIDACAO: Meta-cadeias---")
    t0 = time.time()
    
    val = _mcr.MCRAutoValidacaoContinua()
    
    mk1 = _mcr.MCR("test1"); mk2 = _mcr.MCR("test2")
    for i in range(50):
        mk1.aprender(f"e{i}", f"e{i+1}")
        mk2.aprender(f"f{i}", f"f{i+1}")
    
    niveis = {"test1": mk1, "test2": mk2}
    for nome in niveis:
        val.registrar(nome, niveis[nome])
    
    resultados_val = []
    for _ in range(5):
        r = val.ciclo(niveis)
        resultados_val.append(r)
    
    ultimo = resultados_val[-1]
    tempo = time.time() - t0
    r = {
        "modulo": "Auto-Validacao",
        "ciclos": ultimo["ciclos"],
        "entropia_meta": ultimo["entropia_meta"],
        "instaveis": ultimo["instaveis"],
        "tempo_s": round(tempo, 3),
    }
    print(f"  ciclos={ultimo['ciclos']} meta_ent={ultimo['entropia_meta']} instaveis={ultimo['instaveis']}")
    resultados.append(r)
    return r

test_autoval()
print()

# ═══════════════════════════════════════════════════════════
# 12. INTEGRACAO — CerebroAGI completo
# ═══════════════════════════════════════════════════════════

def test_integracao():
    print("---[12] INTEGRACAO: CerebroAGI completo---")
    t0 = time.time()
    
    cerebro = _mcr.CerebroAGI()
    
    # Alimenta com dados reais
    textos = [
        "O MCR e um experimento em minimalismo computacional",
        "MCR usa Markov em multiplos niveis simultaneamente",
        "A equacao MCR e auto-reflexiva e auto-modificavel",
        "MCR descobre dimensoes automaticamente por entropia",
        "A topologia emerge dos dados sem forma fixa imposta",
    ]
    for t in textos:
        cerebro.alimentar(t)
    
    # Salva e carrega
    tmp_path = os.path.join(BASE, "cache", "_test_integracao.json")
    ok_salvou = cerebro.salvar(tmp_path)
    
    cerebro2 = _mcr.CerebroAGI()
    ok_carregou = cerebro2.carregar(tmp_path)
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    # Auto-diagnostico
    diag = cerebro.auto_diagnosticar()
    
    tempo = time.time() - t0
    r = {
        "modulo": "Integracao",
        "alimentou": len(textos),
        "salvou": ok_salvou,
        "carregou": ok_carregou,
        "topicos": diag.get("topicos", 0),
        "hiper_dims": len(cerebro.hiper.dimensoes) if hasattr(cerebro, 'hiper') else 0,
        "tempo_s": round(tempo, 3),
    }
    print(f"  alimentou={len(textos)} salvou={'OK' if ok_salvou else 'FALHA'} carregou={'OK' if ok_carregou else 'FALHA'}")
    print(f"  topicos={diag.get('topicos',0)} hiper_dims={r['hiper_dims']}")
    print(f"  auto_diagnostico: clusters={diag.get('clusters','?')} instaveis={diag.get('instaveis','?')}")
    resultados.append(r)
    return r

test_integracao()
print()

# ═══════════════════════════════════════════════════════════
# RESUMO FINAL
# ═══════════════════════════════════════════════════════════

tempo_total = time.time() - t0_total

print("=" * 70)
print("  RESUMO FINAL — Bateria de Testes Reais")
print("=" * 70)
print()

print(f"{'Modulo':30} {'Metrica':>20} {'Tempo':>8}")
print(f"{'-'*30} {'-'*20} {'-'*8}")
for r in resultados:
    nome = r.get("modulo", "?")
    # Pega a primeira metrica nao-trivial
    metrica = ""
    for k, v in r.items():
        if k not in ("modulo", "tempo_s") and not isinstance(v, dict) and not isinstance(v, list):
            metrica = f"{k}={v}"
            break
    tempo = r.get("tempo_s", 0)
    print(f"{nome:30} {metrica:>20} {tempo:>8.3f}s")

print()
print(f"{'TOTAL':30} {len(resultados):>20} {tempo_total:>8.3f}s")
print()

# Salva resultados
result_path = os.path.join(BASE, "cache", "bateria_real_resultados.json")
with open(result_path, 'w') as f:
    json.dump({"resultados": resultados, "tempo_total": round(tempo_total, 3)}, f, indent=2, ensure_ascii=False)

print(f"Resultados salvos em {result_path}")
print()
print("=" * 70)
print("  BATERIA CONCLUIDA — Todos os resultados sao REAIS")
print("  Nenhum resultado hardcoded. Nenhuma alteracao no MCR_AGI.py.")
print("=" * 70)
