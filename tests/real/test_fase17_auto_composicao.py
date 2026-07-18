#!/usr/bin/env python3
"""test_fase17_auto_composicao.py — MCR que constrói MCRs.

Testa 5 capacidades de auto-composição:
1. Observar domínio — detectar clusters de ações via NMI
2. Criar especialista — gerar MCRCoupling para sub-domínio
3. Compor — construir equipe de especialistas automaticamente
4. Orquestrar — rotear input para o especialista certo
5. Avaliar — comparar composição vs MCR solo

E regressão: decidir() não deve quebrar.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.auto_composicao import AutoComposicao, EspecialistaMCR

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
print("  MCR FASE 17 -- AUTO-COMPOSICAO (MCR que constrói MCRs)")
print("=" * 70)

# === 1. OBSERVAR DOMÍNIO ===
print("\n--- 1. OBSERVAR DOMÍNIO (detectar clusters) ---")

ac = AutoComposicao(c)
dominio = ac.observar_dominio()

check("observar_dominio tem n_clusters",
      'n_clusters' in dominio and dominio['n_clusters'] > 0,
      f"n={dominio.get('n_clusters')}")

check("observar_dominio tem clusters (dict)",
      isinstance(dominio.get('clusters'), dict),
      f"clusters={list(dominio.get('clusters', {}).keys())}")

check("observar_dominio tem acoes (lista)",
      isinstance(dominio.get('acoes'), list) and len(dominio['acoes']) > 0,
      f"acoes={dominio.get('acoes')}")

check("observar_dominio tem threshold_nmi",
      'threshold_nmi' in dominio and dominio['threshold_nmi'] >= 0.0,
      f"th={dominio.get('threshold_nmi')}")

# Cada cluster deve ter pelo menos 1 ação
clusters_validos = all(len(acoes) > 0 for acoes in dominio['clusters'].values())
check("clusters tem pelo menos 1 acao cada",
      clusters_validos,
      f"clusters={dominio['clusters']}")

# === 2. CRIAR ESPECIALISTA ===
print("\n--- 2. CRIAR ESPECIALISTA (MCRCoupling para sub-dominio) ---")

esp = ac.criar_especialista("criador", ["criar"])

check("criar_especialista retorna EspecialistaMCR",
      isinstance(esp, EspecialistaMCR),
      f"type={type(esp).__name__}")

check("especialista tem nome",
      esp.nome == "criador",
      f"nome={esp.nome}")

check("especialista tem acoes",
      "criar" in esp.acoes,
      f"acoes={esp.acoes}")

# Especialista deve ter vocabulário
check("especialista tem vocabulario > 0",
      len(esp._coupling._palavra_acao) > 0,
      f"vocab={len(esp._coupling._palavra_acao)}")

# Especialista deve responder "criar" para "criar monstro"
acao_esp, conf_esp = esp.consultar("criar monstro")
check("especialista responde 'criar' para 'criar monstro'",
      acao_esp == "criar",
      f"acao={acao_esp}")

# Especialista com múltiplas ações
esp2 = ac.criar_especialista("editor_busca", ["editar", "buscar"])
check("criar especialista com multiplas acoes",
      isinstance(esp2, EspecialistaMCR) and len(esp2.acoes) == 2,
      f"acoes={esp2.acoes}")

# Estatísticas do especialista
stats_esp = esp.estatisticas()
check("especialista tem estatisticas",
      'nome' in stats_esp and 'taxa_acerto' in stats_esp,
      f"keys={list(stats_esp.keys())}")

# === 3. COMPOR ===
print("\n--- 3. COMPOR (equipe automatica) ---")

# Limpar especialistas anteriores para teste limpo
ac._especialistas.clear()

composicao = ac.compor()

check("compor retorna especialistas (lista)",
      isinstance(composicao.get('especialistas'), list),
      f"type={type(composicao.get('especialistas'))}")

check("compor retorna n_clusters",
      'n_clusters' in composicao and composicao['n_clusters'] > 0,
      f"n={composicao.get('n_clusters')}")

check("compor retorna status",
      composicao.get('status') == 'composto',
      f"status={composicao.get('status')}")

check("composicao tem pelo menos 1 especialista",
      len(ac._especialistas) > 0,
      f"n_esp={len(ac._especialistas)}")

# Listar especialistas
lista = ac.listar_especialistas()
check("listar_especialistas retorna lista",
      isinstance(lista, list) and len(lista) > 0,
      f"lista={lista}")

# Obter especialista
esp_obtido = ac.obter_especialista(lista[0])
check("obter_especialista retorna especialista",
      isinstance(esp_obtido, EspecialistaMCR),
      f"type={type(esp_obtido)}")

# Obter inexistente
esp_inex = ac.obter_especialista("inexistente")
check("obter_especialista inexistente = None",
      esp_inex is None,
      f"result={esp_inex}")

# === 4. ORQUESTRAR ===
print("\n--- 4. ORQUESTRAR (rotear para especialista certo) ---")

# Orquestrar input familiar
resultado = ac.orquestrar("criar monstro")

check("orquestrar tem acao",
      'acao' in resultado and resultado['acao'],
      f"acao={resultado.get('acao')}")

check("orquestrar tem confianca",
      'confianca' in resultado and 0.0 <= resultado['confianca'] <= 1.0,
      f"conf={resultado.get('confianca')}")

check("orquestrar tem especialista_usado",
      'especialista_usado' in resultado and resultado['especialista_usado'],
      f"esp={resultado.get('especialista_usado')}")

check("orquestrar tem nmi_por_especialista (dict)",
      isinstance(resultado.get('nmi_por_especialista'), dict),
      f"nmi={resultado.get('nmi_por_especialista')}")

# Orquestrar outro input
resultado2 = ac.orquestrar("fogo queima")
check("orquestrar funciona com outro input",
      'acao' in resultado2 and resultado2['acao'],
      f"acao={resultado2.get('acao')}")

# Orquestrar input desconhecido (deve usar MCR principal)
resultado3 = ac.orquestrar("xyzqwt desconhecido")
check("orquestrar com input desconhecido nao quebra",
      'acao' in resultado3,
      f"acao={resultado3.get('acao')}")

# Sem especialistas: orquestrar usa MCR principal
ac_sem = AutoComposicao(c)
resultado_sem = ac_sem.orquestrar("criar monstro")
check("sem especialistas: usa mcr_principal",
      resultado_sem['especialista_usado'] == 'mcr_principal',
      f"esp={resultado_sem['especialista_usado']}")

# Feedback
ac.feedback("criar monstro", "criar")
check("feedback nao quebra",
      True,
      "feedback executado")

# === 5. AVALIAR ===
print("\n--- 5. AVALIAR (composicao vs solo) ---")

dataset = [
    ("criar monstro", "criar"),
    ("gerar npc", "criar"),
    ("fazer item", "criar"),
    ("editar script", "editar"),
    ("modificar codigo", "editar"),
    ("buscar funcao", "buscar"),
    ("encontrar arquivo", "buscar"),
    ("aprender licao", "aprender"),
    ("estudar materia", "aprender"),
    ("fogo queima", "elementos"),
    ("agua molha", "elementos"),
    ("gato late", "animais"),
    ("cachorro corre", "animais"),
    ("carro acelera", "veiculos"),
    ("moto corre", "veiculos"),
]

avaliacao = ac.avaliar_composicao(dataset)

check("avaliar tem accuracy_orquestrado",
      'accuracy_orquestrado' in avaliacao and 0.0 <= avaliacao['accuracy_orquestrado'] <= 1.0,
      f"acc={avaliacao.get('accuracy_orquestrado')}")

check("avaliar tem accuracy_solo",
      'accuracy_solo' in avaliacao and 0.0 <= avaliacao['accuracy_solo'] <= 1.0,
      f"acc={avaliacao.get('accuracy_solo')}")

check("avaliar tem ganho",
      'ganho' in avaliacao and -1.0 <= avaliacao['ganho'] <= 1.0,
      f"ganho={avaliacao.get('ganho')}")

check("avaliar tem n_testes",
      avaliacao.get('n_testes') == len(dataset),
      f"n={avaliacao.get('n_testes')} esp={len(dataset)}")

check("avaliar tem n_correto_orquestrado",
      'n_correto_orquestrado' in avaliacao,
      f"n={avaliacao.get('n_correto_orquestrado')}")

# === 6. INTEGRAÇÃO NO COUPLING ===
print("\n--- 6. INTEGRACAO NO COUPLING ---")

me_ac = c.ativar_auto_composicao()
check("ativar_auto_composicao retorna AutoComposicao",
      isinstance(me_ac, AutoComposicao),
      f"type={type(me_ac).__name__}")

comp_c = c.compor_especialistas()
check("compor_especialistas via coupling funciona",
      isinstance(comp_c, dict) and 'n_clusters' in comp_c,
      f"n={comp_c.get('n_clusters')}")

orq_c = c.orquestrar_especialistas("criar monstro")
check("orquestrar_especialistas via coupling funciona",
      isinstance(orq_c, dict) and 'acao' in orq_c,
      f"acao={orq_c.get('acao')}")

aval_c = c.avaliar_composicao(dataset)
check("avaliar_composicao via coupling funciona",
      isinstance(aval_c, dict) and 'ganho' in aval_c,
      f"ganho={aval_c.get('ganho')}")

# === 7. ESTATÍSTICAS ===
print("\n--- 7. ESTATISTICAS ---")

stats = ac.estatisticas()
check("estatisticas tem n_especialistas",
      'n_especialistas' in stats and stats['n_especialistas'] > 0,
      f"n={stats.get('n_especialistas')}")

check("estatisticas tem especialistas (lista)",
      isinstance(stats.get('especialistas'), list),
      f"n={len(stats.get('especialistas', []))}")

check("estatisticas tem n_orquestracoes",
      'n_orquestracoes' in stats,
      f"n={stats.get('n_orquestracoes')}")

# === 8. REGRESSÃO ===
print("\n--- 8. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos auto-composicao",
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
