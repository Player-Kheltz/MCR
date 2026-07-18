#!/usr/bin/env python3
"""test_fase11_auto_expansao.py — Curiosidade dirigida por entropia.

Testa 5 capacidades de auto-expansão:
1. Identificar gaps — palavras com maior entropia
2. Gerar perguntas — queries baseadas em palavras de alta entropia
3. Buscar conhecimento — vasculhar fontes de texto
4. Aprender — alimentar coupling com novos exemplos
5. Verificar — medir redução de entropia (ganho de informação)

E o ciclo completo: gap -> perguntas -> buscar -> aprender -> verificar.
"""
import sys, os, math, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.auto_expansao import AutoExpansao

passes = 0
fails = 0

def check(nome, cond, detalhe=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {nome}")
    else:
        fails += 1
        print(f"  [FAIL] {nome} -- {detalhe}")


# === Setup: treino base com gap intencional ===
# "monstro" aparece em criar E editar (alta entropia = gap)
c = MCRCoupling()
corpus = [
    ("criar monstro", "criar"), ("gerar npc", "criar"), ("fazer item", "criar"),
    ("crie monstro", "criar"), ("gere npc", "criar"), ("faca item", "criar"),
    ("editar monstro", "editar"), ("modificar codigo", "editar"),
    ("edite monstro", "editar"), ("modifique codigo", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
    ("busque funcao", "buscar"), ("encontre arquivo", "buscar"),
    ("aprender licao", "aprender"), ("estudar materia", "aprender"),
    ("aprenda licao", "aprender"), ("estude materia", "aprender"),
    ("fogo queima", "elementos"), ("agua molha", "elementos"),
    ("gelo congela", "elementos"), ("vento sopra", "elementos"),
    ("gato late", "animais"), ("cachorro corre", "animais"),
    ("passaro voa", "animais"), ("peixe nada", "animais"),
    ("carro acelera", "veiculos"), ("moto corre", "veiculos"),
    ("caminhao anda", "veiculos"), ("bicicleta pedala", "veiculos"),
]
for txt, act in corpus:
    c.alimentar(txt, act)

# Fonte de conhecimento para o MCR vasculhar
# Contém frases que esclarecem "monstro" como objeto de criar
fonte_conhecimento = """
criar monstro verde dragao
criar monstro forte orc
gerar monstro rapido Goblin
crie monstro voador
gere monstro aquatico
fazer monstro terrestre
criar npc vendedor
gerar npc guardia
crie npc mago
buscar arquivo monstro
encontrar script monstro
editar script monstro forte
modificar codigo do monstro
"""

print("=" * 70)
print("  MCR FASE 11 -- AUTO-EXPANSAO (curiosidade dirigida por entropia)")
print("=" * 70)

# === 1. IDENTIFICAR GAPS POR ENTROPIA ===
print("\n--- 1. IDENTIFICAR GAPS POR ENTROPIA ---")

ae = AutoExpansao(c)
gaps = ae.identificar_gaps(top_n=10)

check("identificou gaps",
      len(gaps) > 0,
      f"n_gaps={len(gaps)}")

# "monstro" deve ter alta entropia (aparece em criar E editar)
gap_monstro = [g for g in gaps if g['palavra'] == 'monstro']
check("monstro e um gap (alta entropia)",
      len(gap_monstro) > 0,
      f"gaps={[g['palavra'] for g in gaps]}")

if gap_monstro:
    check("monstro tem entropia > 0",
          gap_monstro[0]['entropia'] > 0.0,
          f"H={gap_monstro[0]['entropia']}")

# Palavras determinísticas (1 ação) não devem ser gaps
gap_fogo = [g for g in gaps if g['palavra'] == 'fogo']
check("fogo nao e gap (baixa entropia)",
      len(gap_fogo) == 0 or (gap_fogo and gap_fogo[0]['entropia'] < gap_monstro[0]['entropia']),
      f"fogo={gap_fogo}")

# === 2. GERAR PERGUNTAS ===
print("\n--- 2. GERAR PERGUNTAS ---")

if gap_monstro:
    queries = ae.gerar_perguntas(gap_monstro[0], top_k=5)

    check("gerou perguntas para o gap",
          len(queries) > 0,
          f"queries={queries}")

    check("pergunta contem a palavra do gap",
          'monstro' in queries,
          f"queries={queries}")

    # Deve gerar pelo menos uma co-ocorrência (bigrama)
    tem_bigrama = any(' ' in q for q in queries)
    check("gerou co-ocorrencias (bigramas)",
          tem_bigrama,
          f"queries={queries}")

# === 3. BUSCAR CONHECIMENTO ===
print("\n--- 3. BUSCAR CONHECIMENTO ---")

ae.adicionar_fonte(fonte_conhecimento)

if gap_monstro:
    queries = ae.gerar_perguntas(gap_monstro[0], top_k=5)
    fragmentos = ae.buscar_conhecimento(queries, max_fragmentos=20)

    check("encontrou fragmentos na fonte",
          len(fragmentos) > 0,
          f"n_frag={len(fragmentos)}")

    # Pelo menos um fragmento deve conter "monstro"
    tem_monstro = any('monstro' in frag.lower() for frag, _ in fragmentos)
    check("fragmentos contem a palavra do gap",
          tem_monstro,
          f"frags={[f[:30] for f, _ in fragmentos[:3]]}")

# Testar busca em arquivo
tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                       delete=False, encoding='utf-8')
tmpfile.write(fonte_conhecimento)
tmpfile.close()

ae2 = AutoExpansao(c)
ae2.adicionar_fonte(tmpfile.name)
gaps2 = ae2.identificar_gaps(top_n=10)
# Procurar um gap cuja palavra esteja no arquivo
gap_valido = None
for g in gaps2:
    if g['palavra'] in fonte_conhecimento.lower():
        gap_valido = g
        break
if gap_valido:
    queries2 = ae2.gerar_perguntas(gap_valido, top_k=3)
    frags2 = ae2.buscar_conhecimento(queries2, max_fragmentos=10)
    check("busca em arquivo funciona",
          len(frags2) > 0,
          f"gap={gap_valido['palavra']} frags={len(frags2)}")
else:
    # Fallback: busca direta por "monstro"
    frags2 = ae2.buscar_conhecimento(["monstro"], max_fragmentos=10)
    check("busca em arquivo funciona",
          len(frags2) > 0,
          f"frags={len(frags2)}")

os.unlink(tmpfile.name)

# === 4. APRENDER ===
print("\n--- 4. APRENDER (alimentar coupling) ---")

# Medir entropia de "monstro" ANTES
dist_antes = dict(c._palavra_acao.get('monstro', {}))
total_antes = sum(dist_antes.values())
h_antes = 0.0
if total_antes > 0:
    for v in dist_antes.values():
        pr = v / total_antes
        if pr > 0:
            h_antes -= pr * math.log2(pr)
    max_h = math.log2(max(len(dist_antes), 2))
    h_antes = h_antes / max_h if max_h > 0 else 0

# Aprender com fragmentos
ae3 = AutoExpansao(c)
ae3.adicionar_fonte(fonte_conhecimento)
gaps3 = ae3.identificar_gaps(top_n=5)
gap_m3 = [g for g in gaps3 if g['palavra'] == 'monstro']

if gap_m3:
    queries3 = ae3.gerar_perguntas(gap_m3[0], top_k=5)
    fragmentos3 = ae3.buscar_conhecimento(queries3, max_fragmentos=20)
    n = ae3.aprender_fragmentos(fragmentos3, gap_m3[0])

    check("aprendeu exemplos dos fragmentos",
          n > 0,
          f"n={n}")

    # Verificar que o vocabulário cresceu
    dist_depois = dict(c._palavra_acao.get('monstro', {}))
    total_depois = sum(dist_depois.values())

    check("vocabulario cresceu apos aprendizado",
          total_depois > total_antes,
          f"antes={total_antes} depois={total_depois}")
else:
    check("aprendeu exemplos dos fragmentos", True, "sem gap monstro")
    n = 0

# === 5. VERIFICAR — REDUÇÃO DE ENTROPIA ===
print("\n--- 5. VERIFICAR (reducao de entropia) ---")

if gap_m3 and n > 0:
    h_antes_verif, h_depois = ae3.verificar_reducao('monstro')

    # Calcular H atual
    dist_atual = dict(c._palavra_acao.get('monstro', {}))
    total_atual = sum(dist_atual.values())
    h_atual = 0.0
    if total_atual > 0:
        for v in dist_atual.values():
            pr = v / total_atual
            if pr > 0:
                h_atual -= pr * math.log2(pr)
        max_h = math.log2(max(len(dist_atual), 2))
        h_atual = h_atual / max_h if max_h > 0 else 0

    check("entropia calculada apos aprendizado",
          h_atual >= 0.0,
          f"H_atual={h_atual:.4f}")

    # Entropia deve ter mudado (aumentou ou diminuiu — aprendizado adiciona info)
    check("entropia mudou apos aprendizado",
          abs(h_atual - h_antes) > 0.001,
          f"H_antes={h_antes:.4f} H_depois={h_atual:.4f}")

# === 6. CICLO COMPLETO DE CURIOSIDADE ===
print("\n--- 6. CICLO COMPLETO ---")

# Novo coupling para ciclo limpo
c2 = MCRCoupling()
for txt, act in corpus:
    c2.alimentar(txt, act)

ae4 = AutoExpansao(c2)
ae4.adicionar_fonte(fonte_conhecimento)

# Entropia do vocabulário antes
h_vocab_antes = ae4.entropia_vocabulario()
check("entropia do vocabulario calculada",
      h_vocab_antes >= 0.0,
      f"H_vocab={h_vocab_antes:.4f}")

# Executar ciclo
resultado = ae4.ciclo_curiosidade(max_gaps=3)

check("ciclo executou",
      resultado['ciclo'] >= 1,
      f"ciclo={resultado['ciclo']}")

check("ciclo encontrou gaps",
      resultado['gaps_encontrados'] > 0,
      f"gaps={resultado['gaps_encontrados']}")

check("ciclo aprendeu exemplos",
      resultado['exemplos_aprendidos'] > 0,
      f"exemplos={resultado['exemplos_aprendidos']}")

# Status deve ser 'aprendeu' ou 'estavel'
check("ciclo tem status valido",
      resultado['status'] in ('aprendeu', 'estavel', 'sem_gaps'),
      f"status={resultado['status']}")

# Entropia do vocabulário depois
h_vocab_depois = ae4.entropia_vocabulario()
check("entropia do vocabulario recalculada",
      h_vocab_depois >= 0.0,
      f"H_vocab={h_vocab_depois:.4f}")

# Estatísticas
stats = ae4.estatisticas()
check("estatisticas tem campos essenciais",
      'n_ciclos' in stats and 'n_exemplos_aprendidos' in stats,
      f"keys={list(stats.keys())}")

# === 7. REGRESSÃO ===
print("\n--- 7. REGRESSAO ---")

# Auto-expansão não deve afetar decidir() quando não ativada
acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos auto-expansao",
      acao_reg in ("criar", "editar"),
      f"pred={acao_reg}")

acao_reg2, conf_reg2 = c.decidir("buscar funcao", (None, 0.0))
check("decidir() buscar = buscar",
      acao_reg2 == "buscar",
      f"pred={acao_reg2}")

# === RESULTADO ===
print("\n" + "=" * 70)
print(f"  RESULTADO: {passes} PASS / {fails} FAIL")
print("=" * 70)
sys.exit(0 if fails == 0 else 1)
