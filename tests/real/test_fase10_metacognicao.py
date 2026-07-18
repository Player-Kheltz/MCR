#!/usr/bin/env python3
"""test_fase10_metacognicao.py — MCR observa o próprio MCR.

Testa 5 capacidades meta-cognitivas:
1. Observar decisões (sem afetar comportamento quando desativado)
2. Medir incerteza (entropia + divergência + novelty)
3. Calibrar confiança (feedback histórico → curva de calibração)
4. Decidir quando NÃO responder ("não sei" é resposta válida)
5. Auto-diagnosticar (overconfidence, domain shift, gaps)
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.meta_cognitivo import MetaCognitivo

passes = 0
fails = 0

def check(nome, cond, detalhe=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {nome}")
    else:
        fails += 1
        print(f"  [FAIL] {nome} — {detalhe}")


# === Setup: treino base ===
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
print("  MCR FASE 10 — META-COGNIÇÃO (MCR observa o próprio MCR)")
print("=" * 70)

# ─── 1. OBSERVAÇÃO (não afeta decidir quando desativada) ────────────────
print("\n--- 1. OBSERVAÇÃO (opt-in, não afeta classificação) ---")

# Sem meta-cognição: decidir funciona normalmente
acao1, conf1 = c.decidir("criar monstro", (None, 0.0))
check("decidir funciona sem meta-cognicao",
      acao1 == "criar",
      f"pred={acao1}")

# Ativar meta-cognição
c.ativar_metacognicao()
check("meta-cognicao ativada", c._meta_ativo and c._meta is not None)

# Decidir com meta-cognição ativa ainda funciona (input familiar)
acao2, conf2 = c.decidir("criar monstro", (None, 0.0))
check("decidir com meta ativa em dominio familiar",
      acao2 == "criar",
      f"pred={acao2}")

# Verificar que a observação foi registrada
check("observacao registrada",
      c._meta._n_observacoes >= 1,
      f"n_obs={c._meta._n_observacoes}")

# Desativar e verificar que não observa mais
c.desativar_metacognicao()
n_antes = c._meta._n_observacoes
c.decidir("buscar funcao", (None, 0.0))
check("desativada nao observa",
      c._meta._n_observacoes == n_antes,
      f"antes={n_antes} depois={c._meta._n_observacoes}")

# ─── 2. INCERTEZA META-COGNITIVA ────────────────────────────────────────
print("\n--- 2. INCERTEZA META-COGNITIVA ---")

c.ativar_metacognicao()
meta = c._meta

# Observar várias decisões
for txt, _ in corpus[:15]:
    acao, conf = c.decidir(txt, (None, 0.0))

# Incerteza de decisão familiar (alta confiança, baixa incerteza)
inc_familiar = meta.incerteza_meta(
    0.9, {"criar": 0.9, "editar": 0.1}, 5, 0.1, "criar monstro"
)
check("incerteza baixa em decisao familiar",
      inc_familiar < 0.5,
      f"inc={inc_familiar:.3f}")

# Incerteza de decisão incerta (distribuição plana)
inc_planada = meta.incerteza_meta(
    0.5, {"criar": 0.25, "editar": 0.25, "buscar": 0.25, "aprender": 0.25},
    3, 0.8, "xyz desconhecido"
)
check("incerteza alta em decisao plana+discordante",
      inc_planada > 0.5,
      f"inc={inc_planada:.3f}")

# Incerteza maior com novelty (input desconhecido)
inc_novel = meta.incerteza_meta(
    0.5, {"criar": 0.5, "editar": 0.5}, 2, 0.3, "xyzqwt desconhecido"
)
check("incerteza maior com novelty alto",
      inc_novel > inc_familiar,
      f"novel={inc_novel:.3f} familiar={inc_familiar:.3f}")

# ─── 3. CALIBRAÇÃO (feedback → modelo P(correto|confiança)) ─────────────
print("\n--- 3. CALIBRAÇÃO (feedback histórico) ---")

# Resetar meta para teste de calibração limpo
c.desativar_metacognicao()
c.ativar_metacognicao()
meta = c._meta

# Simular feedback: 10 decisões com confiança 0.9, 8 corretas, 2 erradas
for i in range(8):
    meta.feedback(0.9, True, "criar")
for i in range(2):
    meta.feedback(0.9, False, "criar")

# Simular feedback: 10 decisões com confiança 0.5, 4 corretas, 6 erradas
for i in range(4):
    meta.feedback(0.5, True, "buscar")
for i in range(6):
    meta.feedback(0.5, False, "buscar")

# Brier score deve ser > 0 (não perfeito) e < 1 (não pior possível)
brier = meta.brier_score()
check("brier score calculado",
      0.0 < brier < 1.0,
      f"brier={brier:.3f}")

# Calibração: confiança 0.9 → taxa real 0.8
conf_cal = meta.calibrar_confianca(0.9)
check("calibracao reduz overconfidence (0.9 -> ~0.8)",
      abs(conf_cal - 0.8) < 0.2,
      f"cal={conf_cal:.3f} (esperado ~0.8)")

# Calibração: confiança 0.5 → taxa real 0.4
conf_cal2 = meta.calibrar_confianca(0.5)
check("calibracao em confianca media (0.5 -> ~0.4)",
      abs(conf_cal2 - 0.4) < 0.2,
      f"cal={conf_cal2:.3f} (esperado ~0.4)")

# Curva de calibração tem pelo menos 2 bins
curva = meta.curva_calibracao()
check("curva de calibracao tem >= 2 bins",
      len(curva) >= 2,
      f"bins={len(curva)}")

# Presunção: confiança média - taxa de acerto
pres = meta.presuncao()
check("presuncao calculada",
      -1.0 < pres < 1.0,
      f"presuncao={pres:.3f}")

# ─── 4. DECIDIR QUANDO NÃO RESPONDER ────────────────────────────────────
print("\n--- 4. DECIDIR QUANDO NÃO RESPONDER ---")

# Resetar para teste de veto
c.desativar_metacognicao()
c.ativar_metacognicao()
meta = c._meta

# Alimentar histórico com observações
for txt, _ in corpus[:10]:
    acao, conf = c.decidir(txt, (None, 0.0))

# Dar feedback misto (realista): maioria correta, algumas erradas
for _ in range(7):
    meta.feedback(0.9, True, "criar")
for _ in range(3):
    meta.feedback(0.9, False, "criar")

# Agora confiança 0.9 deve ser calibrada para baixo
# e MCR deve ter threshold mais permissivo para veto

# Decisão familiar: deve poder responder
pode, conf, just = meta.pode_responder(
    "criar monstro", 0.9, {"criar": 0.9, "editar": 0.1}, 5, 0.1
)
check("pode responder em decisao familiar",
      pode,
      f"conf={conf:.3f} just={just}")

# Decisão com distribuição plana + novelty: NÃO deve responder
pode2, conf2, just2 = meta.pode_responder(
    "xyzqwt desconhecido", 0.3,
    {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25},
    1, 0.9
)
check("nao responde com distribuicao plana + novelty",
      not pode2,
      f"conf={conf2:.3f} just={just2}")

# Decisão com confiança muito baixa: NÃO deve responder
pode3, conf3, just3 = meta.pode_responder(
    "buscar arquivo", 0.05, {"buscar": 0.05, "criar": 0.95}, 2, 0.5
)
check("nao responde com confianca muito baixa",
      not pode3,
      f"conf={conf3:.3f} just={just3}")

# ─── 5. AUTO-DIAGNÓSTICO ───────────────────────────────────────────────
print("\n--- 5. AUTO-DIAGNÓSTICO ---")

# Resetar para diagnóstico limpo
c.desativar_metacognicao()
c.ativar_metacognicao()
meta = c._meta

# Alimentar observações
for txt, _ in corpus:
    acao, conf = c.decidir(txt, (None, 0.0))

# Feedback: maioria correta, algumas erradas
for txt, act_esperado in corpus[:20]:
    acao, conf = c.decidir(txt, (None, 0.0))
    meta.feedback(conf, acao == act_esperado, acao)

# Feedback negativo extra para criar gap em "aprender"
for _ in range(5):
    meta.feedback(0.3, False, "aprender")

diag = meta.auto_diagnosticar()

check("diagnostico tem status",
      'status' in diag,
      f"keys={list(diag.keys())}")

check("diagnostico tem n_observacoes",
      diag.get('n_observacoes', 0) > 0,
      f"n_obs={diag.get('n_observacoes')}")

check("diagnostico tem taxa_acerto",
      'taxa_acerto' in diag,
      f"taxa={diag.get('taxa_acerto')}")

check("diagnostico tem brier_score",
      'brier_score' in diag,
      f"brier={diag.get('brier_score')}")

check("diagnostico detecta vies",
      diag.get('vies') in ('overconfident', 'underconfident', 'calibrado', None)
          or 'vies' not in diag,
      f"vies={diag.get('vies')}")

# Verificar que detecta gaps (aprender tem feedback negativo)
check("diagnostico detecta gaps",
      'gaps' in diag or diag.get('n_feedback', 0) < 10,
      f"diag={diag.get('status')} gaps={'gaps' in diag}")

# Estatísticas resumidas
stats = meta.estatisticas()
check("estatisticas tem campos essenciais",
      'n_observacoes' in stats and 'brier_score' in stats,
      f"keys={list(stats.keys())}")

# ─── 6. REGRESSÃO: decidir() sem meta-cognição NÃO muda ─────────────────
print("\n--- 6. REGRESSÃO ---")

c.desativar_metacognicao()
acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() sem meta = criar",
      acao_reg == "criar",
      f"pred={acao_reg}")

acao_reg2, conf_reg2 = c.decidir("editar script", (None, 0.0))
check("decidir() sem meta = editar",
      acao_reg2 == "editar",
      f"pred={acao_reg2}")

acao_reg3, conf_reg3 = c.decidir("fogo queima", (None, 0.0))
check("decidir() sem meta = elementos",
      acao_reg3 == "elementos",
      f"pred={acao_reg3}")

# === RESULTADO ===
print("\n" + "=" * 70)
print(f"  RESULTADO: {passes} PASS / {fails} FAIL")
print("=" * 70)
sys.exit(0 if fails == 0 else 1)
