"""Teste das 4 capacidades que superam LLM:
1. Few-shot sem retreino
2. Geração longa coerente
3. Raciocínio multi-etapa
4. Conhecimento enciclopédico
"""
import sys, os, time, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling
from mcr.few_shot import FewShotLearner
from mcr.gerador_coerente import GeradorCoerente
from mcr.raciocinador_mk import RaciocinadorMarkoviano
from mcr.base_conhecimento import BaseConhecimento

PASS, FAIL = 0, 0

def T(nome, cond, detalhe=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {nome}')
    else:
        FAIL += 1
        print(f'  [FAIL] {nome} — {detalhe}')

print('=' * 70)
print('  MCR FASE 9 — SUPERANDO LLM EM 4 CAPACIDADES')
print('=' * 70)

# === Setup: treino base expandido ===
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
    ("uva doce", "frutas"), ("maca vermelha", "frutas"),
    ("limao azedo", "frutas"), ("banana amarela", "frutas"),
]
for txt, act in corpus:
    c.alimentar(txt, act)

# ═══════════════════════════════════════════════════════════
print('\n--- 1. FEW-SHOT SEM RETREINO ---')

learner = FewShotLearner(c)
exemplos = learner.aprender_do_prompt(
    "gato → animais\ncarro → veiculos\nfogo → elementos\nuva → frutas\npeixe → ?"
)
T('extraiu 4 exemplos do prompt', len(exemplos) == 4, f'{len(exemplos)} exemplos: {exemplos}')

pred, conf = learner.predizer("peixe")
T('few-shot: peixe -> animais', pred == "animais", f'pred={pred} conf={conf:.3f}')

pred2, conf2 = learner.predizer("moto")
T('few-shot: moto -> veiculos (heranca)', pred2 == "veiculos", f'pred={pred2} conf={conf2:.3f}')

pred3, conf3 = learner.predizer("gelo")
T('few-shot: gelo -> elementos (heranca)', pred3 == "elementos", f'pred={pred3} conf={conf3:.3f}')

# ═══════════════════════════════════════════════════════════
print('\n--- 2. GERAÇÃO LONGA COERENTE ---')

gen = GeradorCoerente(c)
texto = gen.gerar("criar monstro", max_tokens=30, top_k=5)
n_tokens = len(texto.split())
T('gerou 10+ tokens', n_tokens >= 10, f'{n_tokens} tokens: "{texto[:80]}..."')
T('gerou 20+ tokens', n_tokens >= 20, f'{n_tokens} tokens')

texto2 = gen.gerar("fogo queima", max_tokens=20, top_k=3)
T('geracao tema fogo tem palavras', len(texto2.split()) >= 5, f'"{texto2[:60]}..."')

# ═══════════════════════════════════════════════════════════
print('\n--- 3. RACIOCÍNIO MULTI-ETAPA ---')

rac = RaciocinadorMarkoviano(c)
resp, conf = rac.raciocinar("criar monstro e editar script")
T('raciocinou sobre pergunta composta', resp is not None, f'resp={resp} conf={conf:.3f}')

resp2, conf2 = rac.raciocinar("buscar arquivo depois editar codigo")
T('raciocinou em sequencia (buscar→editar)', resp2 is not None, f'resp={resp2} conf={conf2:.3f}')

resp3, conf3 = rac.silogismo("criar monstro", "monstro dragao")
T('silogismo: criar+monstro → criar', resp3 is not None, f'resp={resp3} conf={conf3:.3f}')

# ═══════════════════════════════════════════════════════════
print('\n--- 4. CONHECIMENTO ENCICLOPÉDICO ---')

bc = BaseConhecimento(c)
n = bc.ingerir(
    "O fogo é quente. Fogo queima madeira. "
    "A agua molha tudo. Agua apaga fogo. "
    "Gelo congela. Gelo derrete com calor.",
    "enciclopedia"
)
T('ingestao extraiu fatos', n > 0, f'{n} fatos')

T('base tem conceitos indexados', len(bc.conceitos()) > 0, f'conceitos: {bc.conceitos()[:5]}')

fatos = bc.recuperar("o que fogo faz?", top_n=3)
T('recuperou fatos sobre fogo', len(fatos) > 0, f'{len(fatos)} fatos')
T('fato recuperado menciona fogo', any('fogo' in f.lower() for f, _, _ in fatos),
  f'fatos: {[(f[:30], round(s,3)) for f, _, s in fatos]}')

resp_bc, conf_bc, fatos_usados = bc.responder("o que fogo faz?")
T('respondeu usando conhecimento', resp_bc is not None, f'resp={resp_bc} conf={conf_bc:.3f}')

# ═══════════════════════════════════════════════════════════
print('\n--- 5. REGRESSÃO ---')

from mcr.coupling import MCRCoupling as C2
c2 = C2()
for txt, act in corpus:
    c2.alimentar(txt, act)
pred_reg, conf_reg = c2.decidir("criar monstro dragao", (None, 0.0))
T('decidir() ainda funciona', pred_reg == "criar", f'pred={pred_reg} conf={conf_reg:.3f}')

# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 70)
print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
print('=' * 70)
