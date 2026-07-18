#!/usr/bin/env python3
"""test_fase13_causalidade.py — P(B|do(A)) vs P(B|A).

Testa 5 capacidades de inferencia causal:
1. Confounders — identificar variaveis que afetam A e B
2. Intervir (do) — P(B|do(A)) via backdoor adjustment
3. Efeito causal — magnitude do confounding (causal vs espurio)
4. Cadeia causal — A -> B -> C
5. d-separacao — A e B independentes dado C?

E regressao: decidir() nao deve quebrar.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.causalidade import Causalidade

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


# === Setup: treino base com estrutura causal ===
# "criar" -> "monstro" (causal: criar causa monstro a aparecer)
# "monstro" -> "atacar" (causal: monstro causa atacar)
# "dragao" e confounder: aparece tanto com criar quanto com monstro
c = MCRCoupling()
corpus = [
    # Cadeia: criar -> monstro -> atacar
    ("criar monstro", "criar"), ("criar monstro verde", "criar"),
    ("criar monstro forte", "criar"), ("criar monstro dragao", "criar"),
    ("gerar monstro", "criar"), ("fazer monstro", "criar"),
    ("crie monstro", "criar"), ("gere monstro", "criar"),
    ("monstro atacar", "atacar"), ("monstro atacar inimigo", "atacar"),
    ("monstro atacar forte", "atacar"), ("monstro lutar", "atacar"),
    # Dragao e confounder: aparece com criar e com monstro
    ("criar dragao", "criar"), ("criar dragao verde", "criar"),
    ("dragao monstro", "criar"), ("dragao atacar", "atacar"),
    # Outras acoes (sem confounder)
    ("editar script", "editar"), ("modificar codigo", "editar"),
    ("edite script", "editar"), ("modifique codigo", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
    ("busque funcao", "buscar"), ("encontre arquivo", "buscar"),
    ("fogo queima", "elementos"), ("agua molha", "elementos"),
    ("gato late", "animais"), ("cachorro corre", "animais"),
    ("carro acelera", "veiculos"), ("moto corre", "veiculos"),
]
for txt, act in corpus:
    c.alimentar(txt, act)

print("=" * 70)
print("  MCR FASE 13 -- CAUSALIDADE (P(B|do(A)) vs P(B|A))")
print("=" * 70)

# === 1. CONFOUNDERS ===
print("\n--- 1. CONFOUNDERS (variaveis que afetam A e B) ---")

causal = Causalidade(c)

# "criar" e "monstro" devem ter confounders (dragao aparece com ambos)
confounders = causal.identificar_confounders("criar", "monstro")

check("identificou confounders para criar/monstro",
      len(confounders) > 0,
      f"n={len(confounders)} confounders={[cf['confounder'] for cf in confounders[:3]]}")

# Confounders devem ter forca > 1 (lift > 1)
if confounders:
    check("confounder tem forca > 1",
          confounders[0]['forca'] > 1.0,
          f"forca={confounders[0]['forca']} conf={confounders[0]['confounder']}")

# "editar" e "buscar" nao devem ter confounders (independentes)
conf_indep = causal.identificar_confounders("editar", "buscar")
check("editar/buscar tem poucos ou nenhum confounder",
      len(conf_indep) <= 2,
      f"n={len(conf_indep)}")

# Confounders retornam estrutura correta
if confounders:
    cf = confounders[0]
    check("confounder tem campos essenciais",
          'confounder' in cf and 'p_a_dado_c' in cf and 'p_b_dado_c' in cf,
          f"keys={list(cf.keys())}")

# === 2. INTERVIR (do) — P(B|do(A)) ===
print("\n--- 2. INTERVIR (P(B|do(A))) ---")

# P(monstro|do(criar)) — efeito causal de criar sobre monstro
p_do = causal.intervir("criar", "monstro")
check("intervir retorna probabilidade valida",
      0.0 <= p_do <= 1.0,
      f"P(monstro|do(criar))={p_do:.4f}")

# P(monstro|criar) — correlacao observacional
p_obs = causal._prob_condicional("monstro", "criar")
check("P(B|A) calculada",
      0.0 <= p_obs <= 1.0,
      f"P(monstro|criar)={p_obs:.4f}")

# Sem confounders: P(B|do(A)) = P(B|A)
p_do_indep = causal.intervir("editar", "buscar")
p_obs_indep = causal._prob_condicional("buscar", "editar")
check("sem confounders: P(B|do(A)) ~ P(B|A)",
      abs(p_do_indep - p_obs_indep) < 0.3,
      f"do={p_do_indep:.4f} obs={p_obs_indep:.4f}")

# === 3. EFEITO CAUSAL ===
print("\n--- 3. EFEITO CAUSAL (correlacao vs causalidade) ---")

efeito = causal.efeito_causal("criar", "monstro")

check("efeito_causal tem p_b_dado_a",
      'p_b_dado_a' in efeito,
      f"keys={list(efeito.keys())}")

check("efeito_causal tem p_b_dado_do_a",
      'p_b_dado_do_a' in efeito,
      f"keys={list(efeito.keys())}")

check("efeito_causal tem diferenca",
      'diferenca' in efeito,
      f"keys={list(efeito.keys())}")

check("efeito_causal tem tipo",
      efeito.get('tipo') in ('causal', 'confundido', 'espurio'),
      f"tipo={efeito.get('tipo')}")

check("diferenca >= 0",
      efeito['diferenca'] >= 0.0,
      f"diff={efeito['diferenca']}")

# === 4. CADEIA CAUSAL ===
print("\n--- 4. CADEIA CAUSAL (A -> B -> C) ---")

# criar -> monstro -> atacar
cadeia = causal.cadeia_causal("criar", "monstro", "atacar")

check("cadeia_causal tem a, b, c",
      cadeia.get('a') == 'criar' and cadeia.get('b') == 'monstro' and cadeia.get('c') == 'atacar',
      f"a={cadeia.get('a')} b={cadeia.get('b')} c={cadeia.get('c')}")

check("cadeia_causal tem e_mediado",
      'e_mediado' in cadeia,
      f"keys={list(cadeia.keys())}")

check("cadeia_causal tem e_direto",
      'e_direto' in cadeia,
      f"keys={list(cadeia.keys())}")

check("cadeia_causal tem e_cadeia (bool)",
      isinstance(cadeia.get('e_cadeia'), bool),
      f"e_cadeia={cadeia.get('e_cadeia')}")

check("cadeia_causal tem ratio_mediacao",
      'ratio_mediacao' in cadeia and cadeia['ratio_mediacao'] >= 0.0,
      f"ratio={cadeia.get('ratio_mediacao')}")

# === 5. d-SEPARACAO ===
print("\n--- 5. d-SEPARACAO (A independente de B dado C?) ---")

# editar e buscar sao independentes (sem relacao causal)
d_sep = causal.d_separacao("editar", "buscar", "script")

check("d_separacao tem a, b, c",
      d_sep.get('a') == 'editar' and d_sep.get('b') == 'buscar',
      f"a={d_sep.get('a')} b={d_sep.get('b')}")

check("d_separacao tem p_b_dado_c",
      'p_b_dado_c' in d_sep,
      f"keys={list(d_sep.keys())}")

check("d_separacao tem p_b_dado_a_c",
      'p_b_dado_a_c' in d_sep,
      f"keys={list(d_sep.keys())}")

check("d_separacao tem independentes (bool)",
      isinstance(d_sep.get('independentes'), bool),
      f"indep={d_sep.get('independentes')}")

check("d_separacao tem diferenca",
      'diferenca' in d_sep and d_sep['diferenca'] >= 0.0,
      f"diff={d_sep.get('diferenca')}")

# === 6. INTEGRACAO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_c = c.ativar_causalidade()
check("ativar_causalidade retorna Causalidade",
      isinstance(me_c, Causalidade),
      f"type={type(me_c).__name__}")

efeito_c = c.efeito_causal("criar", "monstro")
check("efeito_causal via coupling funciona",
      isinstance(efeito_c, dict) and 'tipo' in efeito_c,
      f"tipo={efeito_c.get('tipo')}")

conf_c = c.confounders("criar", "monstro")
check("confounders via coupling funciona",
      isinstance(conf_c, list),
      f"n={len(conf_c)}")

p_do_c = c.intervir("criar", "monstro")
check("intervir via coupling funciona",
      0.0 <= p_do_c <= 1.0,
      f"p={p_do_c:.4f}")

cadeia_c = c.cadeia_causal("criar", "monstro", "atacar")
check("cadeia_causal via coupling funciona",
      isinstance(cadeia_c, dict) and 'e_cadeia' in cadeia_c,
      f"keys={list(cadeia_c.keys())}")

dsep_c = c.d_separacao("editar", "buscar", "script")
check("d_separacao via coupling funciona",
      isinstance(dsep_c, dict) and 'independentes' in dsep_c,
      f"indep={dsep_c.get('independentes')}")

# === 7. ESTATISTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = causal.estatisticas()
check("estatisticas tem campos essenciais",
      'vocabulario' in stats and 'transicoes' in stats,
      f"keys={list(stats.keys())}")

# === 8. REGRESSAO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos causalidade",
      acao_reg in ("criar", "editar"),
      f"pred={acao_reg}")

acao_reg2, conf_reg2 = c.decidir("buscar funcao", (None, 0.0))
check("decidir() buscar = buscar",
      acao_reg2 == "buscar",
      f"pred={acao_reg2}")

acao_reg3, conf_reg3 = c.decidir("fogo queima", (None, 0.0))
check("decidir() fogo = elementos",
      acao_reg3 == "elementos",
      f"pred={acao_reg3}")

# === RESULTADO ===
print("\n" + "=" * 70)
print(f"  RESULTADO: {passes} PASS / {fails} FAIL")
print("=" * 70)
sys.exit(0 if fails == 0 else 1)
