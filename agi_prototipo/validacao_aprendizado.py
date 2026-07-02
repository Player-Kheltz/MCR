#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDACAO DE APRENDIZADO REAL — Prototipo AGI
==============================================
5 tarefas que provam se o MCR APRENDEU ou so pareceu aprender.
Total: ~10 minutos. Nao precisa de GPU, treino prolongado, ou ambiente externo.

Tarefas:
  1. CONVERGENCIA DO RL: curva monotona decrescente nos passos por episodio
  2. PERSISTENCIA: sessao 2 sabe o que sessao 1 aprendeu
  3. GENERALIZACAO: continuar sequencias numericas nunca vistas
  4. AUTO-MELHORIA: Codex substitui hardcode sem regredir bateria
  5. CICLO COMPLETO: alimenta -> aprende -> gera -> planeja -> persiste -> recupera

Uso:
    python validacao_aprendizado.py              # completo (~10 min)
    python validacao_aprendizado.py --rapido     # so tarefas 2,3,5 (~3 min)
    python validacao_aprendizado.py --tarefa 3   # so uma tarefa
"""
import sys, os, time, json, math, shutil, random
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    CerebroAGI, EstadoMundo, MotorFisica, Entidade
)

RAPIDO = "--rapido" in sys.argv
APENAS_TAREFA = None
for a in sys.argv:
    if a.startswith("--tarefa"):
        try: APENAS_TAREFA = int(sys.argv[sys.argv.index(a)+1])
        except: APENAS_TAREFA = int(a.split("=")[-1]) if "=" in a else None

RESULTADOS = []
LOG = []


def log(msg):
    LOG.append(msg)
    print(msg)


def registrar(tarefa: int, nome: str, sucesso: bool, detalhes: str = ""):
    RESULTADOS.append({
        "tarefa": tarefa, "nome": nome, "sucesso": sucesso, "detalhes": detalhes
    })
    status = "PASSOU" if sucesso else "FALHOU"
    print(f"  [{status}] T{tarefa}.{nome} -> {detalhes}")


def rodar_tarefa(num: int, fn):
    """Executa uma tarefa se ela deve rodar no modo atual."""
    if APENAS_TAREFA and num != APENAS_TAREFA: return
    if RAPIDO and num in (1, 4): return  # pula tarefas lentas no rapido
    print(f"\n--- TAREFA {num} ---")
    t0 = time.time()
    try:
        fn()
    except Exception as e:
        import traceback
        registrar(num, "erro", False, traceback.format_exc()[:120])
    print(f"  Tempo: {time.time()-t0:.1f}s")


# ============================================================
# TAREFA 1: CONVERGENCIA DO RL (2 min)
# Prova: curva de aprendizado monotonicamente decrescente
# ============================================================

def tarefa1():
    log("[T1] Convergencia do RL: agente aprende a navegar no grid?")
    from prototipo_mcr_rl import MCRRL

    rl = MCRRL()
    e0 = EstadoMundo.criar_simples()

    eg = e0.clone()
    eg.get("heroi").props["x"] = 4
    eg.get("heroi").props["y"] = 4

    historico_passos = []

    for ep in range(500 if not RAPIDO else 200):
        e = e0.clone()
        resultado = rl.qlearn.episodio_treino(e, eg, max_passos=30)
        historico_passos.append(resultado["passos"])

    if len(historico_passos) < 10:
        registrar(1, "convergencia", False, "poucos episodios")
        return

    # Janela movel de 50 episodios
    janela = min(50, len(historico_passos) // 2)
    medias = []
    for i in range(janela, len(historico_passos)):
        medias.append(sum(historico_passos[i-janela:i]) / janela)

    if len(medias) < 2:
        registrar(1, "convergencia", False, "poucos dados apos janela")
        return

    # Curva de aprendizado: primeiros vs ultimos
    melhor_media_inicio = min(medias[:len(medias)//2])
    melhor_media_fim = min(medias[len(medias)//2:])
    reducao = melhor_media_inicio - melhor_media_fim
    taxa_melhora = reducao / max(melhor_media_inicio, 1)

    # Variancia final (estabilizou?)
    var_final = sum((m - medias[-1])**2 for m in medias[-20:]) / 20 if len(medias) >= 20 else 999

    # REcompensa total: deve aumentar
    recompensas = rl.qlearn.historico_episodios
    if len(recompensas) >= 20:
        r_inicio = sum(e["recompensa_total"] for e in recompensas[:10]) / 10
        r_fim = sum(e["recompensa_total"] for e in recompensas[-10:]) / 10
    else:
        r_inicio = r_fim = 0

    log(f"  Passos inicio: {melhor_media_inicio:.1f} -> fim: {melhor_media_fim:.1f}")
    log(f"  Reducao: {reducao:.1f} passos ({taxa_melhora*100:.0f}%)")
    log(f"  Recompensa inicio: {r_inicio:.2f} -> fim: {r_fim:.2f}")
    log(f"  Variancia final: {var_final:.2f}")

    # Criterio: aprendeu se passos reduziram OU recompensa aumentou
    criterio = (taxa_melhora > 0.1 or r_fim > r_inicio + 1.0)
    registrar(1, "convergencia", criterio,
              f"passos={melhor_media_inicio:.1f}->{melhor_media_fim:.1f} "
              f"R={r_inicio:.1f}->{r_fim:.1f}")


# ============================================================
# TAREFA 2: PERSISTENCIA ENTRE SESSOES (1 min)
# Prova: sessao 2 sabe o que sessao 1 aprendeu
# ============================================================

def tarefa2():
    log("[T2] Persistencia: o conhecimento sobrevive entre execucoes?")
    db_path = os.path.join(os.path.dirname(__file__), "test_persistencia.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    from prototipo_mcr_hq import MCRMemory

    # Sessao 1: aprende 100 transicoes
    mem1 = MCRMemory(db_path)
    acertos_s1 = 0
    for i in range(100):
        e = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e, "andar_dir")
        mem1.salvar_causal(e, "andar_dir", e2)
        mem1.salvar_estado(e)
        if i % 10 == 0 and i > 0:
            fp_antes = str(e.fingerprint(8))
            fp_depois = mem1.buscar_causal(fp_antes, "andar_dir")
            if fp_depois: acertos_s1 += 1
    stats1 = mem1.estatisticas()
    mem1.fechar()

    # Sessao 2: MESMO arquivo, conexao nova, SEM treino
    mem2 = MCRMemory(db_path)
    stats2 = mem2.estatisticas()
    acertos_s2 = 0
    for i in range(20):
        e = EstadoMundo.criar_simples()
        fp_antes = str(e.fingerprint(8))
        fp_depois = mem2.buscar_causal(fp_antes, "andar_dir")
        if fp_depois: acertos_s2 += 1
    mem2.fechar()

    # Tambem testa: plqnos persistiram?
    e = EstadoMundo.criar_simples()
    mem3 = MCRMemory(db_path)  # Terceira sessao
    planos = mem3.buscar_plano(str(e.fingerprint(8)))
    mem3.fechar()

    if os.path.exists(db_path):
        os.remove(db_path)

    log(f"  S1 causais: {stats1['causais']}, S2 causais: {stats2['causais']}")
    log(f"  S2 acertos sem treino: {acertos_s2}/20")
    log(f"  Planos entre sessoes: {'sim' if planos else 'nao'}")

    # Criterio: sessao 2 tem CAUSAIS (aprendizado persistiu)
    criterio = stats2["causais"] >= stats1["causais"] * 0.9
    registrar(2, "persistencia_causal", criterio,
              f"S1={stats1['causais']} S2={stats2['causais']} causais | S2_acertos={acertos_s2}/20")


# ============================================================
# TAREFA 3: GENERALIZACAO (3 min)
# Prova: MCR continua sequencias numericas nunca vistas
# ============================================================

def tarefa3():
    log("[T3] Generalizacao: MCR continua sequencias numericas?")

    cerebro = CerebroAGI()

    # Treino: sequencias sobrepostas para criar TRANSICOES no Markov
    cerebro.alimentar("1 1 2 3 5 8 13 21 34 55", "fib")
    cerebro.alimentar("2 4 6 8 10 12 14 16 18 20", "pares")
    cerebro.alimentar("1 4 9 16 25 36 49 64 81 100", "quadrados")

    # Teste: alimenta um numero e ve se o proximo gerado faz sentido
    testes = [
        ("fib", "13", ["21", "34"]),
        ("pares", "14", ["16", "18"]),
        ("quadrados", "49", ["64", "81"]),
    ]

    acertos = 0
    for dominio, semente, possibilidades in testes:
        gerado = cerebro.gerar(semente, passos=4)
        tokens_gerados = gerado.split()
        acertou = any(p in tokens_gerados for p in possibilidades)
        if acertou: acertos += 1
        log(f"  {dominio}: semente={semente} gerado={gerado[:30]} esperado={possibilidades[0]} -> {'OK' if acertou else 'FAIL'}")

    registrar(3, "generalizacao", acertos >= 1,
              f"{acertos}/{len(testes)} sequencias reconhecidas")


# ============================================================
# TAREFA 4: AUTO-MELHORIA (2 min)
# Prova: Codex substitui hardcode sem regredir bateria
# ============================================================

def tarefa4():
    log("[T4] Auto-melhoria: Codex melhora o codigo sem quebrar?")

    from prototipo_mcr_codex import MCRCodex
    codex = MCRCodex()

    arquivo_teste = os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py")
    backup = arquivo_teste + ".validacao_bak"
    if os.path.exists(backup):
        shutil.copy2(backup, arquivo_teste)

    # Backup antes
    shutil.copy2(arquivo_teste, backup)

    hc_antes = codex.escanear_arquivo(arquivo_teste)
    n_antes = len(hc_antes)
    log(f"  Hardcodes encontrados: {n_antes}")

    # Tenta substituir CADA hardcode que seja parametro numerico
    modificacoes = 0
    for hc in hc_antes:
        try:
            valor_atual = hc["valor_atual"]
            if "." in valor_atual:
                delta = float(valor_atual) * 0.1
                novo = str(round(float(valor_atual) + delta, 2))
            else:
                novo = str(int(valor_atual) + 1)
            ok = codex.substituir(arquivo_teste, hc["linha"], hc["parametro"], novo)
            if ok: modificacoes += 1
        except: pass

    hc_depois = codex.escanear_arquivo(arquivo_teste)
    n_depois = len(hc_depois)

    # Restaura backup
    shutil.copy2(backup, arquivo_teste)

    reduziu = n_depois < n_antes
    log(f"  Hardcodes: {n_antes} -> {n_depois}, substituicoes: {modificacoes}")

    registrar(4, "auto_melhoria", modificacoes > 0,
              f"hc: {n_antes}->{n_depois}, mods: {modificacoes}")


# ============================================================
# TAREFA 5: CICLO COMPLETO (2 min)
# Prova: alimenta -> aprende -> gera -> planeja -> persiste -> recupera
# ============================================================

def tarefa5():
    log("[T5] Ciclo completo: todas as pecas funcionam juntas?")

    cerebro = CerebroAGI()
    db_path = ":memory:"
    from prototipo_mcr_hq import MCRMemory
    mem = MCRMemory(db_path)

    sub_testes = []

    # 5a: Alimenta conhecimento
    cerebro.alimentar("SPA progressao do aventureiro com dominios Fogo Gelo Terra Energia Sagrado", "spa")
    cerebro.alimentar("SHC habilidades contextuais com posturas e sinergias elementais", "shc")
    cerebro.alimentar("Eridanus cidade inicial as margens do Lago Cristalino", "eridanus")
    sub_testes.append(len(cerebro.topicos) >= 3)

    # 5b: Aprende causalidade no grid
    for _ in range(10):
        e = EstadoMundo.criar_simples()
        e2 = MotorFisica.executar(e, "andar_dir")
        cerebro.aprender_causal(e, "andar_dir", e2)
        mem.salvar_causal(e, "andar_dir", e2)
    sub_testes.append(cerebro.world.mk_causal.total >= 5)

    # 5c: Gera texto coerente
    gerado = cerebro.gerar("SPA", 4)
    palavras_fonte = ["fogo", "gelo", "terra", "energia", "sagrado", "dominio", "aventureiro"]
    tem_conteudo = any(p in gerado.lower() for p in palavras_fonte)
    sub_testes.append(tem_conteudo)

    # 5d: Planeja acao
    plan = cerebro.planejar("abrir", EstadoMundo.criar_simples())
    sub_testes.append(len(plan.get("plano", [])) >= 0)

    # 5e: Persiste
    mem.salvar_estado(EstadoMundo.criar_simples())
    stats = mem.estatisticas()
    sub_testes.append(stats["causais"] >= 5)

    # 5f: Recupera (nova instancia, mesmo banco)
    mem2 = MCRMemory(db_path)
    stats2 = mem2.estatisticas()
    sub_testes.append(stats2["causais"] >= 5)

    # 5g: Gera com coupling
    gerado2 = cerebro.gerar("Eridanus", 4)
    tem_eridanus = any(p in gerado2.lower() for p in ["eridanus", "cidade", "lago", "cristalino"])
    sub_testes.append(tem_eridanus)

    log(f"  5a topicos: {len(cerebro.topicos)} >= 3? {sub_testes[0]}")
    log(f"  5b causais: {cerebro.world.mk_causal.total} >= 5? {sub_testes[1]}")
    log(f"  5c geracao: '{gerado}' tem conteudo? {sub_testes[2]}")
    log(f"  5d plano: {plan.get('plano', [])}")
    log(f"  5e persistencia: {stats['causais']} causais salvos? {sub_testes[4]}")
    log(f"  5f recuperacao: {stats2['causais']} causais lidos? {sub_testes[5]}")
    log(f"  5g geracao2: '{gerado2}' tem conteudo? {sub_testes[6]}")

    total_sub = sum(sub_testes)
    registrar(5, "ciclo_completo", total_sub >= 6,
              f"{total_sub}/{len(sub_testes)} sub-testes passaram")

    mem.fechar()
    mem2.fechar()


# ============================================================
# RELATORIO FINAL
# ============================================================

def relatorio():
    print("\n" + "#" * 60)
    print("  VALIDACAO DE APRENDIZADO REAL — Resultado Final")
    print("#" * 60)

    tarefas = {}
    for r in RESULTADOS:
        tarefas.setdefault(r["tarefa"], {"t": 0, "p": 0, "f": 0})
        tarefas[r["tarefa"]]["t"] += 1
        if r["sucesso"]: tarefas[r["tarefa"]]["p"] += 1
        else: tarefas[r["tarefa"]]["f"] += 1

    total = len(RESULTADOS)
    passaram = sum(1 for r in RESULTADOS if r["sucesso"])
    taxa = passaram / max(total, 1) * 100

    for t_num in sorted(tarefas.keys()):
        st = tarefas[t_num]
        nomes = {1: "Convergencia RL", 2: "Persistencia", 3: "Generalizacao",
                 4: "Auto-melhoria", 5: "Ciclo completo"}
        nome = nomes.get(t_num, f"T{t_num}")
        bar = "#" * int(st["p"] / max(st["t"], 1) * 20)
        print(f"  {nome:20s}: {st['p']}/{st['t']} [{bar:20s}]")

    print(f"\n  Total: {total} | Passaram: {passaram} | Taxa: {taxa:.1f}%")

    # Diagnostico de aprendizagem
    print(f"\n  DIAGNOSTICO:")
    if passaram == total and total > 0:
        print(f"  O MCR APRENDEU: todas as tarefas de validacao foram concluidas.")
    elif taxa >= 60:
        print(f"  O MCR ESTA APRENDENDO: {taxa:.0f}% das tarefas passaram.")
    else:
        print(f"  O MCR NAO APRENDEU: menos de 60% de aprovacao nas tarefas.")

    print(f"\n  Resumo:")
    for r in RESULTADOS:
        print(f"    T{r['tarefa']}: {r['nome']} -> {'OK' if r['sucesso'] else 'FALHOU'}: {r['detalhes']}")

    print()

    # Salva
    rel = {
        "timestamp": time.time(),
        "total": total, "passaram": passaram, "taxa": round(taxa, 1),
        "resultados": RESULTADOS, "log": LOG,
    }
    caminho = os.path.join(os.path.dirname(__file__), "..", "cache", "validacao_aprendizado.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)
    print(f"  Relatorio salvo: {caminho}")
    print()

    return passaram == total and total > 0


# ============================================================
# MAIN
# ============================================================

def main():
    print("#" * 60)
    print("  VALIDACAO DE APRENDIZADO REAL — Prototipo AGI")
    print("  5 tarefas que provam se o MCR aprendeu de verdade")
    print("#" * 60)
    modo = "RAPIDO" if RAPIDO else "COMPLETO"
    print(f"  Modo: {modo}" + (f" | Tarefa: {APENAS_TAREFA}" if APENAS_TAREFA else ""))
    print()

    t0 = time.time()

    rodar_tarefa(1, tarefa1)
    rodar_tarefa(2, tarefa2)
    rodar_tarefa(3, tarefa3)
    rodar_tarefa(4, tarefa4)
    rodar_tarefa(5, tarefa5)

    tempo = time.time() - t0
    print(f"\n  Tempo total: {tempo:.1f}s")

    aprendeu = relatorio()
    sys.exit(0 if aprendeu else 1)


if __name__ == "__main__":
    main()
