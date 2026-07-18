#!/usr/bin/env python3
"""test_fase19_abstracao.py — Conceitos emergentes de padroes de padroes.

Testa 5 capacidades de abstracao hierarquica:
1. Detectar conceitos — agrupar palavras por NMI de P(acao|palavra)
2. Construir hierarquia — conceitos de conceitos (n niveis)
3. Abstrair — converter texto em representacao conceitual
4. Decidir em conceito — classificar via conceitos (generaliza)
5. Generalizar — atribuir palavra nova ao conceito mais proximo

E regressao: decidir() nao deve quebrar.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.abstracao import AbstracaoHierarquica, Conceito

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


# === Setup: corpus com estrutura conceitual ===
# Conceito "criacao": criar, gerar, fazer, crie, gere, faca (mesma ação)
# Conceito "edicao": editar, modificar, edite, modifique
# Conceito "busca": buscar, encontrar, busque, encontre
# Conceito "elementos": fogo, agua, gelo, vento
# Conceito "animais": gato, cachorro, passaro, peixe
c = MCRCoupling()
corpus = [
    ("criar monstro", "criar"), ("gerar npc", "criar"), ("fazer item", "criar"),
    ("crie monstro", "criar"), ("gere npc", "criar"), ("faca item", "criar"),
    ("editar script", "editar"), ("modificar codigo", "editar"),
    ("edite script", "editar"), ("modifique codigo", "editar"),
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

print("=" * 70)
print("  MCR FASE 19 -- ABSTRACAO HIERARQUICA EMERGENTE")
print("=" * 70)

# === 1. DETECTAR CONCEITOS ===
print("\n--- 1. DETECTAR CONCEITOS (clusters via NMI) ---")

abstr = AbstracaoHierarquica(c)
conceitos = abstr.detectar_conceitos()

check("detectar_conceitos retorna lista",
      isinstance(conceitos, list) and len(conceitos) > 0,
      f"n={len(conceitos)}")

# Deve ter menos conceitos que palavras (agrupamento)
n_palavras = len(c._palavra_acao)
check("n_conceitos < n_palavras (houve agrupamento)",
      len(conceitos) < n_palavras,
      f"conceitos={len(conceitos)} palavras={n_palavras}")

# Cada conceito deve ter pelo menos 1 palavra
check("conceitos tem pelo menos 1 palavra",
      all(len(con.palavras) > 0 for con in conceitos),
      "ok")

# Verificar Conceito tem estrutura correta
if conceitos:
    c0 = conceitos[0]
    check("Conceito tem palavras (set)",
          isinstance(c0.palavras, set) and len(c0.palavras) > 0,
          f"palavras={c0.palavras}")

    check("Conceito tem distribuicao (dict)",
          isinstance(c0.distribuicao, dict) and len(c0.distribuicao) > 0,
          f"dist={list(c0.distribuicao.keys())}")

    check("Conceito tem nivel",
          c0.nivel == 1,
          f"nivel={c0.nivel}")

    check("Conceito tem nome",
          isinstance(c0.nome, str) and len(c0.nome) > 0,
          f"nome={c0.nome}")

    check("Conceito tem id",
          isinstance(c0.id, int) and c0.id > 0,
          f"id={c0.id}")

# Estatisticas do conceito
if conceitos:
    stats_c = conceitos[0].estatisticas()
    check("Conceito.estatisticas tem campos",
          'nome' in stats_c and 'n_palavras' in stats_c,
          f"keys={list(stats_c.keys())}")

# === 2. CONSTRUIR HIERARQUIA ===
print("\n--- 2. CONSTRUIR HIERARQUIA (conceitos de conceitos) ---")

hierarquia = abstr.construir_hierarquia(n_niveis=3)

check("construir_hierarquia retorna dict",
      isinstance(hierarquia, dict),
      f"type={type(hierarquia)}")

check("hierarquia tem nivel 1",
      1 in hierarquia and len(hierarquia[1]) > 0,
      f"n1={len(hierarquia.get(1, []))}")

check("hierarquia tem nivel 2",
      2 in hierarquia and len(hierarquia[2]) > 0,
      f"n2={len(hierarquia.get(2, []))}")

check("hierarquia tem nivel 3",
      3 in hierarquia and len(hierarquia[3]) > 0,
      f"n3={len(hierarquia.get(3, []))}")

# Nivel superior deve ter menos conceitos que inferior
check("nivel 2 <= nivel 1 (compresso)",
      len(hierarquia[2]) <= len(hierarquia[1]),
      f"n1={len(hierarquia[1])} n2={len(hierarquia[2])}")

check("nivel 3 <= nivel 2 (compresso)",
      len(hierarquia[3]) <= len(hierarquia[2]),
      f"n2={len(hierarquia[2])} n3={len(hierarquia[3])}")

# Profundidade
profundidade = abstr.profundidade_hierarquia()
check("profundidade_hierarquia == 3",
      profundidade == 3,
      f"prof={profundidade}")

# Listar conceitos por nivel
conceitos_n1 = abstr.listar_conceitos(nivel=1)
check("listar_conceitos(1) retorna lista",
      isinstance(conceitos_n1, list) and len(conceitos_n1) > 0,
      f"n={len(conceitos_n1)}")

conceitos_n2 = abstr.listar_conceitos(nivel=2)
check("listar_conceitos(2) retorna lista",
      isinstance(conceitos_n2, list) and len(conceitos_n2) > 0,
      f"n={len(conceitos_n2)}")

# Obter conceito de uma palavra
conceito_criar = abstr.obter_conceito("criar")
check("obter_conceito('criar') retorna Conceito",
      isinstance(conceito_criar, Conceito),
      f"type={type(conceito_criar)}")

conceito_inexistente = abstr.obter_conceito("xyzqwt")
check("obter_conceito inexistente retorna None",
      conceito_inexistente is None,
      f"result={conceito_inexistente}")

# Conceito deve conter a palavra
if conceito_criar:
    check("conceito de 'criar' contem 'criar'",
          conceito_criar.contem("criar"),
          f"palavras={conceito_criar.palavras}")

# Conceitos de nivel superior tem filhos
if hierarquia.get(2):
    c2 = hierarquia[2][0]
    check("conceito nivel 2 tem filhos",
          isinstance(c2.filhos, list),
          f"n_filhos={len(c2.filhos)}")

    # Filhos devem ser conceitos de nivel 1
    if c2.filhos:
        check("filhos sao nivel 1",
              c2.filhos[0].nivel == 1,
              f"nivel_filho={c2.filhos[0].nivel}")

# === 3. ABSTRAIR ===
print("\n--- 3. ABSTRAIR (texto -> conceitos) ---")

abst = abstr.abstrair("criar monstro")

check("abstrair tem texto",
      abst.get('texto') == 'criar monstro',
      f"texto={abst.get('texto')}")

check("abstrair tem conceitos (lista)",
      isinstance(abst.get('conceitos'), list) and len(abst['conceitos']) > 0,
      f"conceitos={abst.get('conceitos')}")

check("abstrair tem distribuicao (dict)",
      isinstance(abst.get('distribuicao'), dict),
      f"dist={abst.get('distribuicao')}")

check("abstrair tem cobertura",
      'cobertura' in abst and 0.0 <= abst['cobertura'] <= 1.0,
      f"cob={abst.get('cobertura')}")

check("abstrair tem palavras_conhecidas",
      isinstance(abst.get('palavras_conhecidas'), list),
      f"palavras={abst.get('palavras_conhecidas')}")

check("abstrair tem palavras_desconhecidas",
      isinstance(abst.get('palavras_desconhecidas'), list),
      f"desc={abst.get('palavras_desconhecidas')}")

# Abstrair texto familiar: cobertura alta
abst_fam = abstr.abstrair("criar monstro verde")
check("abstrair texto familiar: cobertura > 0",
      abst_fam['cobertura'] > 0.0,
      f"cob={abst_fam['cobertura']}")

# Abstrair texto desconhecido: cobertura baixa
abst_desc = abstr.abstrair("xyzqwt desconhecido")
check("abstrair texto desconhecido: cobertura baixa",
      abst_desc['cobertura'] < abst_fam['cobertura'],
      f"cob_desc={abst_desc['cobertura']} cob_fam={abst_fam['cobertura']}")

# === 4. DECIDIR EM CONCEITO ===
print("\n--- 4. DECIDIR EM CONCEITO (generaliza) ---")

acao, conf = abstr.decidir_em_conceito("criar monstro")
check("decidir_em_conceito retorna (acao, conf)",
      isinstance(acao, str) and 0.0 <= conf <= 1.0,
      f"acao={acao} conf={conf:.4f}")

# Palavras conhecidas: deve acertar
acao_criar, _ = abstr.decidir_em_conceito("criar monstro")
check("decidir_em_conceito: 'criar monstro' -> criar",
      acao_criar == "criar",
      f"acao={acao_criar}")

acao_editar, _ = abstr.decidir_em_conceito("editar script")
check("decidir_em_conceito: 'editar script' -> editar",
      acao_editar == "editar",
      f"acao={acao_editar}")

acao_fogo, _ = abstr.decidir_em_conceito("fogo queima")
check("decidir_em_conceito: 'fogo queima' -> elementos",
      acao_fogo == "elementos",
      f"acao={acao_fogo}")

# Palavras novas: deve generalizar
acao_gen, conf_gen = abstr.decidir_em_conceito("fabrique monstro")
check("decidir_em_conceito generaliza palavra nova (fabrique)",
      acao_gen == "criar",
      f"acao={acao_gen} (esperado criar)")

acao_gen2, conf_gen2 = abstr.decidir_em_conceito("modifique script")
check("decidir_em_conceito generaliza palavra nova (modifique)",
      acao_gen2 == "editar",
      f"acao={acao_gen2} (esperado editar)")

# === 5. GENERALIZAR ===
print("\n--- 5. GENERALIZAR (palavra nova -> conceito) ---")

# Palavra nova similar a "criar/gerar/fazer"
gen_fabrique = abstr.generalizar("fabrique")
check("generalizar 'fabrique' encontra conceito",
      gen_fabrique is not None,
      f"result={gen_fabrique}")

if gen_fabrique:
    check("conceito de 'fabrique' contem palavras similares",
          len(gen_fabrique.palavras) > 0,
          f"palavras={gen_fabrique.palavras}")

# Palavra nova similar a "editar/modificar"
gen_altere = abstr.generalizar("altere")
check("generalizar 'altere' encontra conceito",
      gen_altere is not None,
      f"result={gen_altere}")

# Palavra conhecida: retorna seu conceito
gen_criar = abstr.generalizar("criar")
check("generalizar palavra conhecida retorna conceito",
      gen_criar is not None and gen_criar.contem("criar"),
      f"contem={gen_criar.contem('criar') if gen_criar else 'N/A'}")

# Palavra totalmente desconhecida: pode ou não encontrar
gen_xyz = abstr.generalizar("xyzqwt")
check("generalizar palavra desconhecida nao quebra",
      gen_xyz is None or isinstance(gen_xyz, Conceito),
      f"result={gen_xyz}")

# === 6. INTEGRACAO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_abstr = c.ativar_abstracao()
check("ativar_abstracao retorna AbstracaoHierarquica",
      isinstance(me_abstr, AbstracaoHierarquica),
      f"type={type(me_abstr).__name__}")

conceitos_c = c.detectar_conceitos()
check("detectar_conceitos via coupling funciona",
      isinstance(conceitos_c, list) and len(conceitos_c) > 0,
      f"n={len(conceitos_c)}")

hierarquia_c = c.construir_hierarquia_conceitual(n_niveis=2)
check("construir_hierarquia_conceitual via coupling funciona",
      isinstance(hierarquia_c, dict) and 1 in hierarquia_c,
      f"niveis={list(hierarquia_c.keys())}")

abst_c = c.abstrair("criar monstro")
check("abstrair via coupling funciona",
      isinstance(abst_c, dict) and 'conceitos' in abst_c,
      f"conceitos={abst_c.get('conceitos')}")

acao_c, conf_c = c.decidir_em_conceito("criar monstro")
check("decidir_em_conceito via coupling funciona",
      isinstance(acao_c, str),
      f"acao={acao_c}")

gen_c = c.generalizar_palavra("fabrique")
check("generalizar_palavra via coupling funciona",
      isinstance(gen_c, dict),
      f"keys={list(gen_c.keys())}")

# === 7. ESTATISTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = abstr.estatisticas()
check("estatisticas tem n_conceitos",
      'n_conceitos' in stats and stats['n_conceitos'] > 0,
      f"n={stats.get('n_conceitos')}")

check("estatisticas tem profundidade",
      'profundidade' in stats and stats['profundidade'] > 0,
      f"prof={stats.get('profundidade')}")

check("estatisticas tem niveis (dict)",
      isinstance(stats.get('niveis'), dict),
      f"niveis={stats.get('niveis')}")

check("estatisticas tem conceitos_top (lista)",
      isinstance(stats.get('conceitos_top'), list),
      f"n={len(stats.get('conceitos_top', []))}")

check("estatisticas tem tamanho_medio_conceito",
      'tamanho_medio_conceito' in stats and stats['tamanho_medio_conceito'] > 0,
      f"tam={stats.get('tamanho_medio_conceito')}")

# === 8. REGRESSAO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos abstracao",
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
