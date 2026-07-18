#!/usr/bin/env python3
"""test_fase16_teoria_da_mente.py — Modelar outros agentes.

Testa 5 capacidades de teoria da mente:
1. Modelar agente — criar agente simulado com conhecimento próprio
2. Predizer ação — o que o agente faria?
3. Atribuir crenças — o que o agente acredita?
4. Crença falsa — agente com conhecimento errado (Sally-Anne)
5. Perspectiva — comparar visões de múltiplos agentes

E regressão: decidir() não deve quebrar.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.teoria_da_mente import TeoriaDaMente, AgenteMental

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


# === Setup: MCR principal (realidade completa) ===
c = MCRCoupling()
corpus_completo = [
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
for txt, act in corpus_completo:
    c.alimentar(txt, act)

print("=" * 70)
print("  MCR FASE 16 -- TEORIA DA MENTE (modelar outros agentes)")
print("=" * 70)

# === 1. MODELAR AGENTE ===
print("\n--- 1. MODELAR AGENTE (criar agente simulado) ---")

tom = TeoriaDaMente(c)

# Sally conhece apenas "criar" (subset do conhecimento)
corpus_sally = [
    ("criar monstro", "criar"), ("gerar npc", "criar"), ("fazer item", "criar"),
    ("crie monstro", "criar"), ("gere npc", "criar"), ("faca item", "criar"),
]
sally = tom.criar_agente("sally", corpus_sally)

check("criar_agente retorna AgenteMental",
      isinstance(sally, AgenteMental),
      f"type={type(sally).__name__}")

check("agente tem nome",
      sally.nome == "sally",
      f"nome={sally.nome}")

# Anne conhece "editar" (diferente de Sally)
corpus_anne = [
    ("editar script", "editar"), ("modificar codigo", "editar"),
    ("edite script", "editar"), ("modifique codigo", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
]
anne = tom.criar_agente("anne", corpus_anne)

check("criou segundo agente (anne)",
      isinstance(anne, AgenteMental) and anne.nome == "anne",
      f"nome={anne.nome}")

# Listar agentes
agentes = tom.listar_agentes()
check("listar_agentes retorna lista",
      isinstance(agentes, list) and "sally" in agentes and "anne" in agentes,
      f"agentes={agentes}")

# Agente com conhecimento compartilhado
bob = tom.criar_agente("bob", conhecimento_compartilhado=True)
check("agente com conhecimento compartilhado",
      isinstance(bob, AgenteMental),
      f"type={type(bob).__name__}")

# Obter agente existente
sally_get = tom.obter_agente("sally")
check("obter_agente retorna agente correto",
      sally_get is not None and sally_get.nome == "sally",
      f"agente={sally_get}")

# Obter agente inexistente
inexistente = tom.obter_agente("inexistente")
check("obter_agente inexistente retorna None",
      inexistente is None,
      f"result={inexistente}")

# === 2. PREDIZER AÇÃO ===
print("\n--- 2. PREDIZER AÇÃO (o que o agente faria?) ---")

# Sally conhece "criar" — deve predizer "criar" para "criar monstro"
pred_sally = tom.predizer_acao(sally, "criar monstro")

check("predizer_acao tem agente",
      pred_sally.get('agente') == 'sally',
      f"agente={pred_sally.get('agente')}")

check("predizer_acao tem acao_agente",
      'acao_agente' in pred_sally,
      f"acao={pred_sally.get('acao_agente')}")

check("predizer_acao tem acao_realidade",
      'acao_realidade' in pred_sally,
      f"acao={pred_sally.get('acao_realidade')}")

check("predizer_acao tem concordam (bool)",
      isinstance(pred_sally.get('concordam'), bool),
      f"concordam={pred_sally.get('concordam')}")

check("predizer_acao tem divergencia",
      'divergencia' in pred_sally and pred_sally['divergencia'] >= 0.0,
      f"div={pred_sally.get('divergencia')}")

# Sally NÃO conhece "editar" — deve divergir da realidade
pred_sally_editar = tom.predizer_acao(sally, "editar script")
check("sally diverge em 'editar script' (nao conhece)",
      not pred_sally_editar['concordam'] or pred_sally_editar['acao_agente'] != 'editar',
      f"agente={pred_sally_editar['acao_agente']} realidade={pred_sally_editar['acao_realidade']}")

# Bob (conhecimento compartilhado) deve concordar com realidade
pred_bob = tom.predizer_acao(bob, "criar monstro")
check("bob (conhecimento compartilhado) concorda com realidade",
      pred_bob['concordam'],
      f"bob={pred_bob['acao_agente']} realidade={pred_bob['acao_realidade']}")

# === 3. ATRIBUIR CRENÇAS ===
print("\n--- 3. ATRIBUIR CRENCAS (o que o agente acredita?) ---")

# Atribuir crença explícita
sally.acredita("bola_localizacao", "cesta")
check("atribuir_crenca: agente tem crenca",
      sally.obter_crenca("bola_localizacao") == "cesta",
      f"crenca={sally.obter_crenca('bola_localizacao')}")

# Crença inexistente
check("atribuir_crenca: crenca inexistente retorna None",
      sally.obter_crenca("inexistente") is None,
      f"result={sally.obter_crenca('inexistente')}")

# Inferir crença
crencas_sally = tom.inferir_crenca(sally, "criar monstro")

check("inferir_crenca tem palavras_conhecidas",
      'palavras_conhecidas' in crencas_sally and isinstance(crencas_sally['palavras_conhecidas'], list),
      f"keys={list(crencas_sally.keys())}")

check("inferir_crenca tem cobertura",
      'cobertura' in crencas_sally and 0.0 <= crencas_sally['cobertura'] <= 1.0,
      f"cob={crencas_sally.get('cobertura')}")

check("inferir_crenca tem acoes_conhecidas",
      'acoes_conhecidas' in crencas_sally and isinstance(crencas_sally['acoes_conhecidas'], list),
      f"acoes={crencas_sally.get('acoes_conhecidas')}")

check("inferir_crenca tem crencas_explicitas",
      'crencas_explicitas' in crencas_sally,
      f"crencas={crencas_sally.get('crencas_explicitas')}")

# Sally conhece "criar" e "monstro" — cobertura alta para "criar monstro"
check("sally tem cobertura > 0 para 'criar monstro'",
      crencas_sally['cobertura'] > 0.0,
      f"cob={crencas_sally['cobertura']}")

# Sally NÃO conhece "editar" — cobertura baixa para "editar script"
crencas_sally_editar = tom.inferir_crenca(sally, "editar script")
check("sally tem cobertura baixa para 'editar script'",
      crencas_sally_editar['cobertura'] < crencas_sally['cobertura'],
      f"cob_criar={crencas_sally['cobertura']} cob_editar={crencas_sally_editar['cobertura']}")

# Definir intenção
sally.definir_intencao("encontrar bola")
check("definir_intencao funciona",
      sally.intencao == "encontrar bola",
      f"intencao={sally.intencao}")

# Contagem de crenças
check("crenca_count >= 1",
      sally.crenca_count >= 1,
      f"count={sally.crenca_count}")

# === 4. CRENÇA FALSA (Sally-Anne) ===
print("\n--- 4. CRENCA FALSA (Sally-Anne) ---")

# Sally conhece apenas "criar". Realidade tem "editar" também.
# Para "editar script", Sally não sabe o que fazer → crença falsa
cf = tom.teste_crenca_falsa(sally, "editar script", "editar")

check("teste_crenca_falsa tem agente",
      cf.get('agente') == 'sally',
      f"agente={cf.get('agente')}")

check("teste_crenca_falsa tem acao_agente",
      'acao_agente' in cf,
      f"acao={cf.get('acao_agente')}")

check("teste_crenca_falsa tem acao_realidade",
      'acao_realidade' in cf,
      f"acao={cf.get('acao_realidade')}")

check("teste_crenca_falsa tem tem_crenca_falsa (bool)",
      isinstance(cf.get('tem_crenca_falsa'), bool),
      f"falsa={cf.get('tem_crenca_falsa')}")

check("teste_crenca_falsa tem cobertura_agente",
      'cobertura_agente' in cf and 0.0 <= cf['cobertura_agente'] <= 1.0,
      f"cob={cf.get('cobertura_agente')}")

check("teste_crenca_falsa tem explicacao",
      'explicacao' in cf and len(cf['explicacao']) > 10,
      f"exp={cf.get('explicacao', '')[:40]}")

# Bob (conhecimento completo) não deve ter crença falsa
cf_bob = tom.teste_crenca_falsa(bob, "criar monstro", "criar")
check("bob (conhecimento completo) sem crença falsa",
      not cf_bob['tem_crenca_falsa'],
      f"falsa={cf_bob['tem_crenca_falsa']} acao_agente={cf_bob['acao_agente']} realidade={cf_bob['acao_realidade']}")

# === 5. PERSPECTIVA — comparar múltiplos agentes ===
print("\n--- 5. PERSPECTIVA (comparar visoes) ---")

persp = tom.comparar_perspectivas("criar monstro")

check("comparar_perspectivas tem perspectivas (lista)",
      isinstance(persp.get('perspectivas'), list) and len(persp['perspectivas']) > 0,
      f"n={len(persp.get('perspectivas', []))}")

check("comparar_perspectivas tem consenso",
      'consenso' in persp and persp['consenso'],
      f"consenso={persp.get('consenso')}")

check("comparar_perspectivas tem taxa_consenso",
      'taxa_consenso' in persp and 0.0 <= persp['taxa_consenso'] <= 1.0,
      f"taxa={persp.get('taxa_consenso')}")

check("comparar_perspectivas tem divergencia_max",
      'divergencia_max' in persp and persp['divergencia_max'] >= 0.0,
      f"div={persp.get('divergencia_max')}")

check("comparar_perspectivas tem n_perspectivas",
      persp.get('n_perspectivas', 0) >= 2,
      f"n={persp.get('n_perspectivas')}")

# Perspectiva inclui realidade
tem_realidade = any(p['agente'] == 'realidade' for p in persp['perspectivas'])
check("perspectivas inclui realidade",
      tem_realidade,
      f"agentes={[p['agente'] for p in persp['perspectivas']]}")

# Predizer interação entre Sally e Anne
interacao = tom.predizer_interacao(sally, anne, "criar monstro")

check("predizer_interacao tem agente_a e agente_b",
      interacao.get('agente_a') == 'sally' and interacao.get('agente_b') == 'anne',
      f"a={interacao.get('agente_a')} b={interacao.get('agente_b')}")

check("predizer_interacao tem acao_a e acao_b",
      'acao_a' in interacao and 'acao_b' in interacao,
      f"a={interacao.get('acao_a')} b={interacao.get('acao_b')}")

check("predizer_interacao tem concordam (bool)",
      isinstance(interacao.get('concordam'), bool),
      f"concordam={interacao.get('concordam')}")

check("predizer_interacao tem dinamica",
      interacao.get('dinamica') in ('cooperacao', 'conflito', 'independencia'),
      f"dinamica={interacao.get('dinamica')}")

# === 6. INTEGRAÇÃO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_tom = c.ativar_teoria_da_mente()
check("ativar_teoria_da_mente retorna TeoriaDaMente",
      isinstance(me_tom, TeoriaDaMente),
      f"type={type(me_tom).__name__}")

agente_c = c.criar_agente("agente_teste", corpus_sally)
check("criar_agente via coupling funciona",
      isinstance(agente_c, AgenteMental) and agente_c.nome == "agente_teste",
      f"nome={agente_c.nome}")

pred_c = c.predizer_acao_agente(agente_c, "criar monstro")
check("predizer_acao_agente via coupling funciona",
      isinstance(pred_c, dict) and 'acao_agente' in pred_c,
      f"acao={pred_c.get('acao_agente')}")

cf_c = c.teste_crenca_falsa(agente_c, "editar script", "editar")
check("teste_crenca_falsa via coupling funciona",
      isinstance(cf_c, dict) and 'tem_crenca_falsa' in cf_c,
      f"falsa={cf_c.get('tem_crenca_falsa')}")

persp_c = c.comparar_perspectivas("criar monstro")
check("comparar_perspectivas via coupling funciona",
      isinstance(persp_c, dict) and 'perspectivas' in persp_c,
      f"n={persp_c.get('n_perspectivas')}")

# === 7. ESTATÍSTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = tom.estatisticas()
check("estatisticas tem n_agentes",
      'n_agentes' in stats and stats['n_agentes'] > 0,
      f"n={stats.get('n_agentes')}")

check("estatisticas tem agentes (lista)",
      isinstance(stats.get('agentes'), list),
      f"agentes={stats.get('agentes')}")

# === 8. REGRESSÃO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos teoria da mente",
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
