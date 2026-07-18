#!/usr/bin/env python3
"""test_fase14_contrafactual.py — "O que aconteceria se...?"

Testa 5 capacidades de raciocinio contrafactual (3o degrau de Pearl):
1. Contrafactual: "se A fosse a', qual seria B?"
2. Necessidade causal: "A foi necessario para B?"
3. Suficiencia causal: "A foi suficiente para B?"
4. Cenarios hipoteticos: multiplos contrafactuais
5. Propagacao contrafactual em cadeia (A -> B -> C)

E regressao: decidir() nao deve quebrar.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.contrafactual import Contrafactual

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


# === Setup: treino com estrutura causal ===
# Cadeia: criar -> monstro -> atacar
# Confounder: dragao (aparece com criar e monstro)
c = MCRCoupling()
corpus = [
    ("criar monstro", "criar"), ("criar monstro verde", "criar"),
    ("criar monstro forte", "criar"), ("criar monstro dragao", "criar"),
    ("gerar monstro", "criar"), ("fazer monstro", "criar"),
    ("crie monstro", "criar"), ("gere monstro", "criar"),
    ("monstro atacar", "atacar"), ("monstro atacar inimigo", "atacar"),
    ("monstro atacar forte", "atacar"), ("monstro lutar", "atacar"),
    ("criar dragao", "criar"), ("criar dragao verde", "criar"),
    ("dragao monstro", "criar"), ("dragao atacar", "atacar"),
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
print("  MCR FASE 14 -- RACIOCINIO CONTRAFACTUAL (\"o que aconteceria se...?\")")
print("=" * 70)

# === 1. CONTRAFACTUAL ===
print("\n--- 1. CONTRAFACTUAL (\"se A fosse a', qual seria B?\") ---")

contra = Contrafactual(c)

# "se 'criar' fosse 'editar', o que aconteceria com 'monstro'?"
cf = contra.o_que_se("criar", "monstro", "editar")

check("o_que_se retorna a_observado",
      cf.get('a_observado') == 'criar',
      f"a={cf.get('a_observado')}")

check("o_que_se retorna a_contrafactual",
      cf.get('a_contrafactual') == 'editar',
      f"a'={cf.get('a_contrafactual')}")

check("o_que_se retorna p_b_original",
      'p_b_original' in cf and 0.0 <= cf['p_b_original'] <= 1.0,
      f"p={cf.get('p_b_original')}")

check("o_que_se retorna p_b_contrafactual",
      'p_b_contrafactual' in cf and 0.0 <= cf['p_b_contrafactual'] <= 1.0,
      f"p={cf.get('p_b_contrafactual')}")

check("o_que_se retorna delta",
      'delta' in cf and cf['delta'] >= 0.0,
      f"delta={cf.get('delta')}")

check("o_que_se retorna acao_mudou (bool)",
      isinstance(cf.get('acao_mudou'), bool),
      f"mudou={cf.get('acao_mudou')}")

check("o_que_se tem interpretacao",
      'interpretacao' in cf and len(cf['interpretacao']) > 0,
      f"interp={cf.get('interpretacao', '')[:50]}")

check("o_que_se tem confounders_abduzidos",
      'confounders_abduzidos' in cf,
      f"keys={list(cf.keys())}")

# Contrafactual com mesma palavra: delta ~ 0
cf_mesmo = contra.o_que_se("criar", "monstro", "criar")
check("contrafactual com mesma palavra: delta ~ 0",
      cf_mesmo['delta'] < 0.1,
      f"delta={cf_mesmo['delta']}")

# === 2. NECESSIDADE CAUSAL ===
print("\n--- 2. NECESSIDADE CAUSAL (\"A foi necessario para B?\") ---")

nec = contra.necessidade_causal("criar", "monstro")

check("necessidade tem a e b",
      nec.get('a') == 'criar' and nec.get('b') == 'monstro',
      f"a={nec.get('a')} b={nec.get('b')}")

check("necessidade tem alternativa",
      'alternativa' in nec and nec['alternativa'] is not None,
      f"alt={nec.get('alternativa')}")

check("necessidade tem p_b_com_a",
      'p_b_com_a' in nec and 0.0 <= nec['p_b_com_a'] <= 1.0,
      f"p={nec.get('p_b_com_a')}")

check("necessidade tem p_b_sem_a",
      'p_b_sem_a' in nec and 0.0 <= nec['p_b_sem_a'] <= 1.0,
      f"p={nec.get('p_b_sem_a')}")

check("necessidade tem necessario (bool)",
      isinstance(nec.get('necessario'), bool),
      f"nec={nec.get('necessario')}")

check("necessidade tem interpretacao",
      'interpretacao' in nec and len(nec['interpretacao']) > 0,
      f"interp len={len(nec.get('interpretacao', ''))}")

# === 3. SUFICIENCIA CAUSAL ===
print("\n--- 3. SUFICIENCIA CAUSAL (\"A foi suficiente para B?\") ---")

suf = contra.suficiencia_causal("criar", "monstro")

check("suficiencia tem a e b",
      suf.get('a') == 'criar' and suf.get('b') == 'monstro',
      f"a={suf.get('a')} b={suf.get('b')}")

check("suficiencia tem p_b_observacional",
      'p_b_observacional' in suf and 0.0 <= suf['p_b_observacional'] <= 1.0,
      f"p={suf.get('p_b_observacional')}")

check("suficiencia tem p_b_intervencional",
      'p_b_intervencional' in suf and 0.0 <= suf['p_b_intervencional'] <= 1.0,
      f"p={suf.get('p_b_intervencional')}")

check("suficiencia tem suficiente (bool)",
      isinstance(suf.get('suficiente'), bool),
      f"suf={suf.get('suficiente')}")

check("suficiencia tem razao",
      'razao' in suf and suf['razao'] >= 0.0,
      f"razao={suf.get('razao')}")

check("suficiencia tem interpretacao",
      'interpretacao' in suf and len(suf['interpretacao']) > 0,
      f"interp len={len(suf.get('interpretacao', ''))}")

# === 4. CENARIOS HIPOTETICOS ===
print("\n--- 4. CENARIOS HIPOTETICOS (multiplos contrafactuais) ---")

cens = contra.cenarios("criar", "monstro", ["editar", "buscar", "fogo"])

check("cenarios retorna lista",
      isinstance(cens, list) and len(cens) > 0,
      f"n={len(cens)}")

check("cenarios exclui a_observado",
      all(c['a_contrafactual'] != 'criar' for c in cens),
      f"alts={[c['a_contrafactual'] for c in cens]}")

# Melhor cenario
melhor = contra.melhor_cenario("criar", "monstro",
                                ["editar", "buscar", "fogo", "gerar"])

check("melhor_cenario retorna dict",
      isinstance(melhor, dict) and 'p_b_contrafactual' in melhor,
      f"keys={list(melhor.keys()) if isinstance(melhor, dict) else 'N/A'}")

check("melhor_cenario tem melhor_alternativa",
      melhor.get('melhor_alternativa') == True if 'erro' not in melhor else True,
      f"melhor={melhor.get('melhor_alternativa')}")

# === 5. PROPAGACAO CONTRAFACTUAL EM CADEIA ===
print("\n--- 5. PROPAGACAO CONTRAFACTUAL (A -> B -> C) ---")

prop = contra.propagar_contrafactual("criar", "monstro", "atacar", "editar")

check("propagar tem a, b, c observados",
      prop.get('a_observado') == 'criar' and
      prop.get('b_observado') == 'monstro' and
      prop.get('c_observado') == 'atacar',
      f"a={prop.get('a_observado')} b={prop.get('b_observado')} c={prop.get('c_observado')}")

check("propagar tem a_contrafactual",
      prop.get('a_contrafactual') == 'editar',
      f"a'={prop.get('a_contrafactual')}")

check("propagar tem b_contrafactual_prob",
      'b_contrafactual_prob' in prop and 0.0 <= prop['b_contrafactual_prob'] <= 1.0,
      f"p={prop.get('b_contrafactual_prob')}")

check("propagar tem c_original_prob",
      'c_original_prob' in prop and 0.0 <= prop['c_original_prob'] <= 1.0,
      f"p={prop.get('c_original_prob')}")

check("propagar tem c_contrafactual_prob",
      'c_contrafactual_prob' in prop and 0.0 <= prop['c_contrafactual_prob'] <= 1.0,
      f"p={prop.get('c_contrafactual_prob')}")

check("propagar tem delta_c",
      'delta_c' in prop and prop['delta_c'] >= 0.0,
      f"delta_c={prop.get('delta_c')}")

check("propagar tem propagou (bool)",
      isinstance(prop.get('propagou'), bool),
      f"propagou={prop.get('propagou')}")

check("propagar tem cf_a_b (contrafactual A->B)",
      'cf_a_b' in prop and isinstance(prop['cf_a_b'], dict),
      f"tem cf_a_b={'cf_a_b' in prop}")

# === 6. INTEGRACAO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_c = c.ativar_contrafactual()
check("ativar_contrafactual retorna Contrafactual",
      isinstance(me_c, Contrafactual),
      f"type={type(me_c).__name__}")

cf_c = c.o_que_se("criar", "monstro", "editar")
check("o_que_se via coupling funciona",
      isinstance(cf_c, dict) and 'delta' in cf_c,
      f"delta={cf_c.get('delta')}")

nec_c = c.necessidade_causal("criar", "monstro")
check("necessidade_causal via coupling funciona",
      isinstance(nec_c, dict) and 'necessario' in nec_c,
      f"nec={nec_c.get('necessario')}")

suf_c = c.suficiencia_causal("criar", "monstro")
check("suficiencia_causal via coupling funciona",
      isinstance(suf_c, dict) and 'suficiente' in suf_c,
      f"suf={suf_c.get('suficiente')}")

cens_c = c.cenarios_contrafactuais("criar", "monstro",
                                    ["editar", "buscar"])
check("cenarios_contrafactuais via coupling funciona",
      isinstance(cens_c, list) and len(cens_c) > 0,
      f"n={len(cens_c)}")

# === 7. ESTATISTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = contra.estatisticas()
check("estatisticas tem campos essenciais",
      'vocabulario' in stats and 'causalidade' in stats,
      f"keys={list(stats.keys())}")

# === 8. REGRESSAO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos contrafactual",
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
