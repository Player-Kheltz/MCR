#!/usr/bin/env python3
"""test_fase12_meta_equacao.py — Auto-evolucao dos pesos 5D.

Testa 3 capacidades da Meta-Equacao:
1. Avaliar — mede qualidade de uma combinacao de pesos (accuracy + separacao)
2. Evoluir — hill climbing markoviano sobre o espaco de pesos
3. Aplicar — atualiza EQUACAO_5D global com os melhores pesos

E regressao: decidir() nao deve quebrar apos evolucao.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.meta_equacao import MetaEquacao
from mcr.equacao_mcr import EQUACAO_5D, avaliar_5d

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


# === Setup: treino base ===
c = MCRCoupling()
corpus_treino = [
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
for txt, act in corpus_treino:
    c.alimentar(txt, act)

# Dataset de validacao (frases nunca vistas no treino)
dataset_validacao = [
    ("criar dragao", "criar"),
    ("gerar item", "criar"),
    ("fazer npc", "criar"),
    ("editar texto", "editar"),
    ("modificar script", "editar"),
    ("buscar arquivo", "buscar"),
    ("procurar funcao", "buscar"),
    ("aprender materia", "aprender"),
    ("estudar licao", "aprender"),
    ("fogo queima floresta", "elementos"),
    ("agua molha chao", "elementos"),
    ("gato corre rapido", "animais"),
    ("cachorro late alto", "animais"),
    ("carro anda rua", "veiculos"),
    ("moto acelera estrada", "veiculos"),
]

print("=" * 70)
print("  MCR FASE 12 -- META-EQUACAO (auto-evolucao dos pesos 5D)")
print("=" * 70)

# === 1. AVALIAR ===
print("\n--- 1. AVALIAR (mede qualidade de pesos) ---")

me = MetaEquacao(c)
me.avaliar_dataset(dataset_validacao)

# Avaliar pesos padrao (todos = 2.0)
pesos_padrao = {d: 2.0 for d in MetaEquacao.DIMENSOES}
resultado_padrao = me.avaliar_pesos(pesos_padrao)

check("avaliar_pesos retorna accuracy",
      'accuracy' in resultado_padrao and resultado_padrao['accuracy'] >= 0.0,
      f"resultado={resultado_padrao}")

check("avaliar_pesos retorna separacao",
      'separacao' in resultado_padrao,
      f"resultado={resultado_padrao}")

check("avaliar_pesos retorna score",
      'score' in resultado_padrao,
      f"resultado={resultado_padrao}")

check("avaliar_pesos tem n_testes",
      resultado_padrao['n_testes'] == len(dataset_validacao),
      f"n={resultado_padrao['n_testes']} esperado={len(dataset_validacao)}")

# Avaliar pesos piores (peso 0.1 em certeza — confiança não importa)
pesos_piores = {d: 2.0 for d in MetaEquacao.DIMENSOES}
pesos_piores['certeza'] = 0.1
pesos_piores['completude'] = 0.1
resultado_pior = me.avaliar_pesos(pesos_piores)

# A accuracy não deve mudar (decidir() não usa 5D diretamente),
# mas o score deve ser calculável
check("avaliar_pesos com pesos diferentes nao quebra",
      resultado_pior['n_testes'] == len(dataset_validacao),
      f"n={resultado_pior['n_testes']}")

# === 2. EVOLUIR ===
print("\n--- 2. EVOLUIR (hill climbing markoviano) ---")

# Evoluir por 5 geracoes
me2 = MetaEquacao(c)
me2.avaliar_dataset(dataset_validacao)
resultado_evol = me2.evoluir(n_geracoes=5)

check("evoluir retorna melhores_pesos",
      'melhores_pesos' in resultado_evol,
      f"keys={list(resultado_evol.keys())}")

check("evoluir retorna melhor_score",
      'melhor_score' in resultado_evol,
      f"keys={list(resultado_evol.keys())}")

check("evoluir retorna historico",
      'historico' in resultado_evol and len(resultado_evol['historico']) > 0,
      f"n_hist={len(resultado_evol.get('historico', []))}")

check("evoluir retorna n_geracoes",
      resultado_evol.get('n_geracoes') == 5,
      f"n_gen={resultado_evol.get('n_geracoes')}")

# Melhores pesos devem ter 5 dimensoes
melhores = resultado_evol['melhores_pesos']
check("melhores_pesos tem 5 dimensoes",
      len(melhores) == 5,
      f"dims={list(melhores.keys())}")

# Cada peso deve estar no range [0.1, 10.0]
pesos_validos = all(0.1 <= v <= 10.0 for v in melhores.values())
check("pesos no range [0.1, 10.0]",
      pesos_validos,
      f"pesos={melhores}")

# Score apos evolucao deve ser >= score inicial
score_inicial = me2.avaliar_pesos(pesos_padrao)['score']
check("score apos evolucao >= inicial",
      resultado_evol['melhor_score'] >= score_inicial - 0.001,
      f"evol={resultado_evol['melhor_score']:.4f} inicial={score_inicial:.4f}")

# === 3. APLICAR ===
print("\n--- 3. APLICAR (atualiza EQUACAO_5D global) ---")

# Salvar pesos originais
pesos_originais = dict(EQUACAO_5D['pesos'])

# Aplicar novos pesos
me2.aplicar()
pesos_aplicados = dict(EQUACAO_5D['pesos'])

check("aplicar atualizou EQUACAO_5D",
      pesos_aplicados != pesos_originais or resultado_evol['melhor_score'] == score_inicial,
      f"antes={pesos_originais} depois={pesos_aplicados}")

# Verificar que avaliar_5d usa os novos pesos
nota = avaliar_5d(0.8, 0.7, 0.6, 0.5, 0.4)
check("avaliar_5d funciona apos aplicar",
      0.0 <= nota <= 1.0,
      f"nota={nota}")

# Reverter
me2.reverter()
pesos_revertidos = dict(EQUACAO_5D['pesos'])

check("reverter volta aos pesos padrao",
      all(pesos_revertidos[d] == 2.0 for d in MetaEquacao.DIMENSOES),
      f"pesos={pesos_revertidos}")

# === 4. ANALISE ===
print("\n--- 4. ANALISE ---")

# Melhor combinacao
melhor = me2.melhor_combinacao()
check("melhor_combinacao tem pesos e score",
      'pesos' in melhor and 'score' in melhor,
      f"keys={list(melhor.keys())}")

# Historico de evolucao
hist = me2.historico_evolucao()
check("historico_evolucao tem entradas",
      len(hist) > 0,
      f"n={len(hist)}")

# Trajetoria de uma dimensao
traj = me2.trajetoria_pesos('certeza')
check("trajetoria_pesos retorna lista",
      isinstance(traj, list) and len(traj) > 0,
      f"traj={traj}")

# Convergencia
check("convergiu retorna booleano",
      isinstance(me2.convergiu(), bool),
      f"convergiu={me2.convergiu()}")

# Estatisticas
stats = me2.estatisticas()
check("estatisticas tem campos essenciais",
      'n_avaliacoes' in stats and 'melhor_score' in stats,
      f"keys={list(stats.keys())}")

# === 5. INTEGRACAO NO COUPLING ===
print("\n--- 5. INTEGRACAO NO COUPLING ---")

# ativar_meta_equacao
me3 = c.ativar_meta_equacao()
check("ativar_meta_equacao retorna MetaEquacao",
      isinstance(me3, MetaEquacao),
      f"type={type(me3).__name__}")

# evoluir_equacao via coupling
resultado_c = c.evoluir_equacao(dataset=dataset_validacao, n_geracoes=3)
check("evoluir_equacao via coupling funciona",
      'melhores_pesos' in resultado_c or 'erro' in resultado_c,
      f"keys={list(resultado_c.keys())}")

# aplicar_equacao via coupling
aplicado = c.aplicar_equacao()
check("aplicar_equacao via coupling funciona",
      isinstance(aplicado, dict),
      f"type={type(aplicado).__name__}")

# reverter_equacao via coupling
revertido = c.reverter_equacao()
check("reverter_equacao via coupling funciona",
      all(revertido[d] == 2.0 for d in MetaEquacao.DIMENSOES),
      f"pesos={revertido}")

# estatisticas_equacao
stats_c = c.estatisticas_equacao()
check("estatisticas_equacao via coupling",
      isinstance(stats_c, dict),
      f"type={type(stats_c).__name__}")

# === 6. REGRESSAO ===
print("\n--- 6. REGRESSAO ---")

# Garantir que pesos estao revertidos
c.reverter_equacao()

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos meta-equacao",
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
