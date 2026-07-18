#!/usr/bin/env python3
"""test_fase15_planejamento.py — MCR planeja antes de agir.

Testa 5 capacidades de planejamento:
1. Simular — prever próximos N estados dado estado + ação
2. Planejar — busca em árvore, escolhe melhor sequência
3. Avaliar plano — score via Equação 5D
4. Replanificar — adapta plano quando estado muda
5. Heurística — diversidade, familiaridade, coerência

E regressão: decidir() não deve quebrar.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.planejador import Planejador

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


# === Setup ===
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
print("  MCR FASE 15 -- PLANEJAMENTO (MCR planeja antes de agir)")
print("=" * 70)

# === 1. SIMULAR ===
print("\n--- 1. SIMULAR (prever futuros) ---")

plan = Planejador(c)

# Simular: se "criar" for feito no estado "criar monstro", o que segue?
traj = plan.simular("criar monstro", "criar", n_passos=3)

check("simular retorna trajetoria",
      isinstance(traj, list) and len(traj) > 0,
      f"n={len(traj)}")

check("simular tem 3 passos",
      len(traj) == 3,
      f"n={len(traj)}")

if traj:
    p0 = traj[0]
    check("simular passo tem acao",
          'acao' in p0 and p0['acao'],
          f"acao={p0.get('acao')}")

    check("simular passo tem confianca",
          'confianca' in p0 and 0.0 <= p0['confianca'] <= 1.0,
          f"conf={p0.get('confianca')}")

    check("simular passo tem entropia",
          'entropia' in p0 and 0.0 <= p0['entropia'] <= 1.0,
          f"h={p0.get('entropia')}")

    check("simular passo tem numero",
          'passo' in p0 and p0['passo'] == 1,
          f"passo={p0.get('passo')}")

# Simular com 1 passo
traj1 = plan.simular("buscar funcao", "buscar", n_passos=1)
check("simular com 1 passo",
      len(traj1) == 1,
      f"n={len(traj1)}")

# === 2. PLANEJAR ===
print("\n--- 2. PLANEJAR (busca em arvore) ---")

plano = plan.planejar("criar monstro", profundidade=3, top_k=3)

check("planejar retorna plano",
      'plano' in plano and isinstance(plano['plano'], list),
      f"plano={plano.get('plano')}")

check("planejar retorna score",
      'score' in plano and 0.0 <= plano['score'] <= 1.0,
      f"score={plano.get('score')}")

check("planejar retorna alternativas",
      'alternativas' in plano and isinstance(plano['alternativas'], list),
      f"n_alt={len(plano.get('alternativas', []))}")

check("planejar retorna estado_inicial",
      plano.get('estado_inicial') == 'criar monstro',
      f"estado={plano.get('estado_inicial')}")

check("planejar retorna profundidade",
      plano.get('profundidade') == 3,
      f"prof={plano.get('profundidade')}")

check("planejar retorna n_caminhos_avaliados",
      'n_caminhos_avaliados' in plano and plano['n_caminhos_avaliados'] > 0,
      f"n={plano.get('n_caminhos_avaliados')}")

# Plano deve ter pelo menos 1 ação
check("plano tem pelo menos 1 acao",
      len(plano['plano']) >= 1,
      f"plano={plano['plano']}")

# Plano com profundidade 1
plano1 = plan.planejar("buscar funcao", profundidade=1, top_k=2)
check("planejar com profundidade 1",
      len(plano1['plano']) >= 1,
      f"plano={plano1['plano']}")

# === 3. AVALIAR PLANO ===
print("\n--- 3. AVALIAR PLANO (score 5D) ---")

# Avaliar plano manual
caminho_alto = [("criar", 0.9), ("gerar", 0.85), ("fazer", 0.8)]
score_alto = plan.avaliar_plano("criar monstro", caminho_alto)

check("avaliar_plano retorna score valido",
      0.0 <= score_alto <= 1.0,
      f"score={score_alto:.4f}")

# Plano com confiança alta deve ter score > plano com confiança baixa
caminho_baixo = [("criar", 0.1), ("editar", 0.05), ("buscar", 0.02)]
score_baixo = plan.avaliar_plano("criar monstro", caminho_baixo)

check("plano confianca alta > confianca baixa",
      score_alto > score_baixo,
      f"alto={score_alto:.4f} baixo={score_baixo:.4f}")

# Plano vazio retorna 0
score_vazio = plan.avaliar_plano("teste", [])
check("plano vazio tem score 0",
      score_vazio == 0.0,
      f"score={score_vazio}")

# Plano com 1 ação
caminho_1 = [("criar", 0.9)]
score_1 = plan.avaliar_plano("criar monstro", caminho_1)
check("avaliar plano com 1 acao",
      0.0 <= score_1 <= 1.0,
      f"score={score_1:.4f}")

# === 4. REPLANIFICAR ===
print("\n--- 4. REPLANIFICAR (adapta plano) ---")

# Plano anterior: [criar, gerar, fazer]
# Novo estado: "buscar funcao" — ação diferente
resultado_replan = plan.replanificar(
    "criar monstro", "buscar funcao",
    ["criar", "gerar", "fazer"],
    profundidade=2
)

check("replanificar retorna novo_plano",
      'novo_plano' in resultado_replan and isinstance(resultado_replan['novo_plano'], list),
      f"plano={resultado_replan.get('novo_plano')}")

check("replanificar retorna mudou (bool)",
      isinstance(resultado_replan.get('mudou'), bool),
      f"mudou={resultado_replan.get('mudou')}")

check("replanificar retorna razao",
      'razao' in resultado_replan and len(resultado_replan['razao']) > 0,
      f"razao={resultado_replan.get('razao', '')[:40]}")

check("replanificar retorna sobreposicao",
      'sobreposicao' in resultado_replan and resultado_replan['sobreposicao'] >= 0,
      f"sobreposicao={resultado_replan.get('sobreposicao')}")

# Estado similar: plano deve preservar parte
resultado_similar = plan.replanificar(
    "criar monstro", "criar monstro verde",
    ["criar", "gerar", "fazer"],
    profundidade=2
)
check("replanificar com estado similar",
      isinstance(resultado_similar.get('novo_plano'), list),
      f"plano={resultado_similar.get('novo_plano')}")

# === 5. HEURÍSTICAS ===
print("\n--- 5. HEURISTICAS (poda por NMI/entropia) ---")

heur = plan.heuristicas("criar monstro")

check("heuristicas tem diversidade",
      'diversidade' in heur and 0.0 <= heur['diversidade'] <= 1.0,
      f"div={heur.get('diversidade')}")

check("heuristicas tem familiaridade",
      'familiaridade' in heur and 0.0 <= heur['familiaridade'] <= 1.0,
      f"fam={heur.get('familiaridade')}")

check("heuristicas tem coerencia",
      'coerencia' in heur and 0.0 <= heur['coerencia'] <= 1.0,
      f"coe={heur.get('coerencia')}")

# Estado familiar deve ter familiaridade alta
heur_fam = plan.heuristicas("criar monstro verde")
check("estado familiar tem familiaridade > 0",
      heur_fam['familiaridade'] > 0.0,
      f"fam={heur_fam['familiaridade']}")

# Estado desconhecido deve ter familiaridade baixa
heur_desconh = plan.heuristicas("xyzqwt desconhecido")
check("estado desconhecido tem familiaridade ~ 0",
      heur_desconh['familiaridade'] < 0.5,
      f"fam={heur_desconh['familiaridade']}")

# === 6. INTEGRAÇÃO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_plan = c.ativar_planejador()
check("ativar_planejador retorna Planejador",
      isinstance(me_plan, Planejador),
      f"type={type(me_plan).__name__}")

plano_c = c.planejar("criar monstro", profundidade=2, top_k=2)
check("planejar via coupling funciona",
      isinstance(plano_c, dict) and 'plano' in plano_c,
      f"plano={plano_c.get('plano')}")

traj_c = c.simular_acao("criar monstro", "criar", n_passos=2)
check("simular_acao via coupling funciona",
      isinstance(traj_c, list) and len(traj_c) > 0,
      f"n={len(traj_c)}")

replan_c = c.replanificar("criar monstro", "buscar funcao",
                           ["criar", "gerar"], profundidade=2)
check("replanificar via coupling funciona",
      isinstance(replan_c, dict) and 'novo_plano' in replan_c,
      f"keys={list(replan_c.keys())}")

heur_c = c.heuristicas_estado("criar monstro")
check("heuristicas_estado via coupling funciona",
      isinstance(heur_c, dict) and 'diversidade' in heur_c,
      f"keys={list(heur_c.keys())}")

# === 7. ESTATÍSTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = plan.estatisticas()
check("estatisticas tem campos essenciais",
      'vocabulario' in stats and 'acoes_conhecidas' in stats,
      f"keys={list(stats.keys())}")

# === 8. REGRESSÃO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos planejador",
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
