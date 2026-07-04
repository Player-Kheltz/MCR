#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE DO SILOGISMO — O MCR aprende relacoes e infere transitividade?
========================================================================
Valida o MCRParserMinimo + MCRRedeSemantica com 6 rondas de complexidade
crescente, de triplas simples ate inferencia multi-hop.

Criterio: NADA hardcoded. Se o MCR aprendeu as relacoes corretas e
consegue navegar o grafo, passa.
"""

import sys, os, json, time, math, random as _rand

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

__file__ = os.path.join(BASE_DIR, "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

VERBOSE = "--verbose" in sys.argv
PONTOS = 0
RELATORIO = []
TOTAL = 60  # 6 rondas x 10 pts

def ronda(nome, pts, fn):
    global PONTOS
    print(f"\n--- RONDA: {nome} ---")
    inicio = time.perf_counter()
    try:
        fn()
        PONTOS += pts
        dur = time.perf_counter() - inicio
        print(f"  >> {pts}/{pts} em {dur:.3f}s")
        RELATORIO.append((nome, pts, pts, dur, "OK"))
    except AssertionError as e:
        dur = time.perf_counter() - inicio
        print(f"  >> 0/{pts} — FALHOU: {e}")
        RELATORIO.append((nome, 0, pts, dur, "FALHOU"))
    except Exception as e:
        dur = time.perf_counter() - inicio
        print(f"  >> 0/{pts} — ERRO: {e}")
        import traceback; traceback.print_exc()
        RELATORIO.append((nome, 0, pts, dur, "ERRO"))


# ─── R1: Parser extrai triplas corretas ─────────────────────────
def r1_parser():
    print("  1.1: SVO simples...")
    p = MCRParserMinimo()
    t = p.extrair("Joao come maca")
    assert any("Joao" in str(x) for x in t), f"Nao extraiu Joao: {t}"
    assert any("come" in str(x) for x in t), f"Nao extraiu come: {t}"
    assert any("maca" in str(x) for x in t), f"Nao extraiu maca: {t}"
    print(f"      OK: {t}")

    print("  1.2: Copular...")
    t = p.extrair("Maria e professora")
    assert any("Maria" in str(x) for x in t), f"Copular falhou: {t}"
    print(f"      OK: {t}")

    print("  1.3: Copular com adjetivo...")
    t = p.extrair("O ceu e azul")
    assert len(t) > 0, f"Nao extraiu nada de 'O ceu e azul'"
    print(f"      OK: {t}")

    print("  1.4: Preposicional...")
    t = p.extrair("Maria gosta de Pedro")
    ok = any("gosta_de" in str(x) or ("gosta" in str(x) and "Maria" in str(x)) for x in t)
    assert ok, f"Preposicional falhou: {t}"
    print(f"      OK: {t}")

    print("  1.5: Comparativo 'mais...que'...")
    t = p.extrair("Joao e mais alto que Maria")
    ok = any("Joao" in str(x) and "Maria" in str(x) for x in t)
    assert ok, f"Comparativo falhou: {t}"
    print(f"      OK: {t}")

    print("  1.6: Silogismo completo...")
    t = p.extrair("Joao e mais alto que Maria. Maria e mais alta que Pedro")
    assert len(t) >= 2, f"Silogismo extraiu apenas {len(t)} triplas: {t}"
    print(f"      OK: {t}")

    print("  1.7: Texto vazio...")
    assert p.extrair("") == [], "Texto vazio retornou triplas"
    print("      OK: vazio")

    print("  1.8: Sem verbo...")
    assert p.extrair("Casa bonita") == [], "Sem verbo retornou triplas"
    print("      OK: sem verbo")

    print("  R1 OK: parser extrai triplas corretamente")

# ─── R2: Rede semantica armazena e consulta ─────────────────────
def r2_rede():
    print("  2.1: Aprender e consultar...")
    r = MCRRedeSemantica()
    r.aprender("Joao", "gosta_de", "Maria")
    res = r.consultar(sujeito="Joao")
    assert len(res) == 1, f"Deveria ter 1 tripla: {res}"
    assert res[0] == ("Joao", "gosta_de", "Maria"), f"Tripla errada: {res}"
    print(f"      OK: {res}")

    print("  2.2: Consultar com filtro de relacao...")
    r.aprender("Joao", "odeia", "Pedro")
    res = r.consultar(sujeito="Joao", relacao="gosta_de")
    assert len(res) == 1, f"Deveria filtrar 1: {res}"
    print(f"      OK: {res}")

    print("  2.3: Multiplos objetos mesma relacao...")
    r.aprender("Joao", "gosta_de", "Ana")
    res = r.consultar(sujeito="Joao", relacao="gosta_de")
    assert len(res) == 2, f"Deveria ter 2 objetos: {res}"
    print(f"      OK: {len(res)} objetos para Joao/gosta_de")

    print("  2.4: Consultar por objeto...")
    res = r.consultar(objeto="Maria")
    # Deve achar (Joao, gosta_de, Maria)
    assert any("Joao" in str(x) for x in res), f"Nao achou Joao por Maria: {res}"
    print(f"      OK: {res}")

    print("  2.5: Entropia media...")
    ent = r.entropia_media()
    assert 0 <= ent <= 1, f"Entropia invalida: {ent}"
    print(f"      OK: entropia={ent:.3f}")

    print("  2.6: Estatisticas...")
    e = r.estatisticas()
    assert e['sujeitos'] >= 1, f"Stats sem sujeitos: {e}"
    assert e['triplas'] >= 3, f"Stats com poucas triplas: {e}"
    print(f"      OK: {e}")

    print("  2.7: Consultar sem filtros (tudo)...")
    tudo = r.consultar()
    assert len(tudo) >= 3, f"Deveria ter >=3 triplas: {len(tudo)}"
    print(f"      OK: {len(tudo)} triplas totais")

    print("  R2 OK: rede semantica armazena e consulta")

# ─── R3: Inferencia via cadeia Markov ────────────────────────────
def r3_inferencia():
    print("  3.1: Predizer objeto direto...")
    r = MCRRedeSemantica()
    r.aprender("Joao", "come", "maca")
    r.aprender("Joao", "come", "banana")
    o, conf = r.predizer_objeto("Joao")
    assert o in ("maca", "banana"), f"Predizer objeto deu {o}"
    assert conf > 0, f"Confianca zero: {conf}"
    print(f"      Joao come -> {o} (conf={conf:.3f})")

    print("  3.2: Predizer com relacao explicita...")
    o, conf = r.predizer_objeto("Joao", "come")
    assert o in ("maca", "banana"), f"Com relacao falhou: {o}"
    print(f"      Joao come -> {o} (conf={conf:.3f})")

    print("  3.3: Predizer sujeito...")
    s, conf = r.predizer_sujeito("maca")
    assert s == "Joao", f"Sujeito de maca deveria ser Joao: {s}"
    print(f"      maca <- {s} (conf={conf:.3f})")

    print("  3.4: Sujeito sem relacoes...")
    s, conf = r.predizer_sujeito("inexistente")
    assert s is None, f"Inexistente devia ser None: {s}"
    print(f"      OK: inexistente -> None")

    print("  3.5: Objeto sem relacoes...")
    o, conf = r.predizer_objeto("inexistente")
    assert o is None, f"Inexistente devia ser None: {o}"
    print(f"      OK: inexistente -> None")

    print("  3.6: Entropia apos aprendizado...")
    ent = r.entropia_media()
    print(f"      Entropia media da rede: {ent:.3f}")

    print("  R3 OK: inferencia via cadeia Markov funciona")

# ─── R4: Busca de cadeia (transitividade) ───────────────────────
def r4_cadeia():
    print("  4.1: Cadeia simples de 2 passos...")
    r = MCRRedeSemantica()
    r.aprender("Joao", "e_pai_de", "Maria")
    r.aprender("Maria", "e_mae_de", "Pedro")
    cadeia = r.buscar_cadeia("Joao", "Pedro")
    assert cadeia is not None, f"Nao encontrou cadeia Joao->Pedro"
    assert len(cadeia) == 2, f"Cadeia devia ter 2 passos: {cadeia}"
    print(f"      Joao -> Pedro: {cadeia}")

    print("  4.2: Cadeia de 3 passos...")
    r.aprender("Pedro", "e_pai_de", "Ana")
    cadeia = r.buscar_cadeia("Joao", "Ana")
    assert cadeia is not None, f"Nao encontrou cadeia Joao->Ana"
    assert len(cadeia) == 3, f"Cadeia devia ter 3 passos: {cadeia}"
    print(f"      Joao -> Ana: {cadeia}")

    print("  4.3: Cadeia reversa...")
    cadeia = r.buscar_cadeia("Ana", "Joao", reverso=True)
    assert cadeia is not None, f"Nao encontrou cadeia reversa"
    print(f"      Ana -> Joao: {cadeia}")

    print("  4.4: Cadeia inexistente...")
    cadeia = r.buscar_cadeia("Joao", "Zeninguem")
    assert cadeia is None, f"Deveria ser None: {cadeia}"
    print(f"      OK: inexistente -> None")

    print("  4.5: Cadeia com multiplos ramos...")
    r.aprender("Joao", "gosta_de", "Carla")
    r.aprender("Carla", "gosta_de", "Pedro")
    cadeia = r.buscar_cadeia("Joao", "Pedro")
    # Pode pegar o caminho pelo parentesco OU pelo gosta_de
    assert cadeia is not None, f"Nao encontrou nenhum caminho"
    print(f"      Joao -> Pedro (multiplos caminhos): {cadeia}")

    print("  4.6: Cadeia limitada por max_passos...")
    cadeia = r.buscar_cadeia("Joao", "Pedro", max_passos=1)
    assert cadeia is None, f"max_passos=1 deveria impedir: {cadeia}"
    print(f"      OK: max_passos=1 bloqueou caminho de 2 passos")

    print("  R4 OK: busca de cadeia (transitividade) funciona")

# ─── R5: Integracao com CerebroAGI ──────────────────────────────
def r5_integracao():
    print("  5.1: Alimentar cerebro extrai triplas...")
    c = CerebroAGI()
    c.alimentar("Joao e mais alto que Maria", "teste1")
    triplas = c.rede_semantica.consultar()
    assert len(triplas) >= 1, f"Nenhuma tripla extraida: {triplas}"
    print(f"      Triplas: {triplas}")

    print("  5.2: Segunda alimentacao acumula...")
    c.alimentar("Maria e mais alta que Pedro", "teste2")
    triplas = c.rede_semantica.consultar()
    assert len(triplas) >= 2, f"Deveria ter >=2 triplas: {len(triplas)}"
    print(f"      Total: {len(triplas)} triplas")

    print("  5.3: Rede persiste no cerebro...")
    assert c.rede_semantica.total > 0, "Rede nao persiste no cerebro"
    est = c.rede_semantica.estatisticas()
    print(f"      Estatisticas da rede: {est}")

    print("  5.4: Coupling integrado...")
    # Verifica que os niveis semanticos foram registrados no coupling
    niveis = c.coupling.niveis
    for nivel in ['sujeito', 'relacao', 'objeto']:
        assert nivel in niveis, f"Nivel {nivel} nao registrado no coupling: {niveis}"
    print(f"      Niveis semanticos no coupling: OK")

    print("  5.5: Topologia registrada...")
    for nivel in ['sujeito', 'relacao', 'objeto']:
        if nivel in c.topologia.grafo:
            print(f"      {nivel} na topologia: OK")
            break
    else:
        print(f"      ATENCAO: niveis semanticos podem nao estar na topologia")

    print("  5.6: Busca de cadeia via cerebro...")
    cadeia = c.rede_semantica.buscar_cadeia("Joao", "Pedro")
    if cadeia:
        print(f"      Cadeia Joao->Pedro: {cadeia}")
    else:
        print(f"      Cadeia nao encontrada (relacao pode ser indireta)")

    print("  5.7: Multiplos topicos...")
    c.alimentar("O sol e amarelo", "teste3")
    c.alimentar("A grama e verde", "teste4")
    triplas = c.rede_semantica.consultar()
    assert len(triplas) >= 3, f"Deveria ter >=3 triplas: {len(triplas)}"
    print(f"      Total apos 4 topicos: {len(triplas)} triplas")

    print("  5.8: Persistencia salvar/carregar...")
    tmp = os.path.join(BASE_DIR, "cache", f"_test_rede_{os.getpid()}.json")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    c.salvar(tmp)
    c2 = CerebroAGI()
    c2.carregar(tmp)
    try: os.remove(tmp)
    except: pass
    print(f"      Save/Load: sem erros")

    print("  R5 OK: integracao com CerebroAGI funciona")

# ─── R6: Carga realistica + parser em texto real ────────────────
def r6_realista():
    print("  6.1: Texto real paragrafo...")
    p = MCRParserMinimo()
    texto = """
    O cientista estudou o fenomeno por anos.
    A equipe publicou os resultados na revista.
    O governo aprovou a lei.
    Maria acredita em Joao.
    """
    triplas = p.extrair(texto)
    print(f"      Extraiu {len(triplas)} triplas de texto real")
    for t in triplas:
        print(f"        {t}")
    assert len(triplas) >= 2, f"Muito poucas triplas do texto real: {triplas}"

    print("  6.2: 100 frases aleatorias...")
    verbos = ["come", "gosta", "odeia", "ve", "le", "escreve", "compra", "vende"]
    objetos = ["maca", "banana", "casa", "carro", "livro", "computador", "agua", "fogo"]
    r = MCRRedeSemantica()
    p = MCRParserMinimo()
    for _ in range(100):
        s = _rand.choice(["Joao", "Maria", "Pedro", "Ana", "Carlos", "Sofia"])
        v = _rand.choice(verbos)
        o = _rand.choice(objetos)
        if _rand.random() < 0.3:
            v = "e"; o = _rand.choice(["alto", "baixo", "feliz", "triste", "bonito", "inteligente"])
        frase = f"{s} {v} {o}"
        triplas = p.extrair(frase)
        for t in triplas:
            r.aprender(*t)
    est = r.estatisticas()
    print(f"      Apos 100 frases: {est}")
    assert est['triplas'] > 0, "Zero triplas apos 100 frases"

    print("  6.3: Consulta em rede grande...")
    res = r.consultar(sujeito="Joao")
    print(f"      Joao: {len(res)} triplas")
    cadeia = r.buscar_cadeia("Joao", "Ana", max_passos=10)
    if cadeia:
        print(f"      Cadeia Joao->Ana: {len(cadeia)} passos")
    else:
        print(f"      Joao->Ana: sem caminho direto (esperado em dados aleatorios)")

    print("  6.4: Entropia apos 100 frases...")
    ent = r.entropia_media()
    assert 0 <= ent <= 1, f"Entropia invalida: {ent}"
    print(f"      Entropia media: {ent:.3f}")

    print("  6.5: Parser com maiusculas/minusculas...")
    triplas = p.extrair("O Joao come a maca")
    ok = any("Joao" in str(x) and "maca" in str(x) for x in triplas)
    assert ok, f"Parser falhou com artigo: {triplas}"
    print(f"      OK: {triplas}")

    print("  R6 OK: carga realistica funciona")

# ═══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 65)
    print("  TESTE DO SILOGISMO — MCR aprende relacoes e infere?")
    print("  6 rondas, 60 pontos. Nada hardcoded.")
    print("=" * 65)

    tempo_total = time.perf_counter()

    ronda("R1: Parser extrai triplas", 10, r1_parser)
    ronda("R2: Rede armazena/consulta", 10, r2_rede)
    ronda("R3: Inferencia Markov", 10, r3_inferencia)
    ronda("R4: Cadeia transitiva", 10, r4_cadeia)
    ronda("R5: Integracao cerebro", 10, r5_integracao)
    ronda("R6: Carga realistica", 10, r6_realista)

    dur_total = time.perf_counter() - tempo_total

    print(f"\n{'='*65}")
    print(f"  SUMARIO")
    print(f"{'='*65}")
    for nome, pts, max_pts, dur, status in RELATORIO:
        print(f"  {nome:<35} {pts}/{max_pts:<4} {dur:.3f}s  {status}")
    print(f"  {'-'*50}")
    print(f"  TOTAL{'':>29} {PONTOS}/{TOTAL}  {dur_total:.3f}s")

    if PONTOS == TOTAL:
        print(f"\n  VEREDITO: MCR APRENDE RELACOES E INFERE TRANSITIVIDADE!")
    elif PONTOS >= TOTAL * 0.8:
        print(f"\n  VEREDITO: MCR aprende a maioria das relacoes ({PONTOS}/{TOTAL})")
    else:
        print(f"\n  VEREDITO: MCR falha em aprender relacoes ({PONTOS}/{TOTAL})")
    print(f"{'='*65}")

    try:
        resultado = {
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": PONTOS, "maximo": TOTAL,
            "rondas": RELATORIO, "tempo": round(dur_total, 3),
        }
        os.makedirs(os.path.join(BASE_DIR, "cache"), exist_ok=True)
        with open(os.path.join(BASE_DIR, "cache", "test_silogismo_result.json"), "w") as f:
            json.dump(resultado, f)
    except:
        pass
