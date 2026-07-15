"""08: Autonomous Test — ColdStart sem dataset JSON externo.

MCR sobrevive sozinho: explora workspace, gera seeds, classifica, persiste.
Zero dataset_500.json. Prova de auto-suficiência.
"""
import sys, json, time, os, glob
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 65)
print('  AUTONOMOUS TEST — MCR sem dataset externo')
print('  Zero JSON. Auto-explora. Auto-seeds. Auto-tudo.')
print('=' * 65)

# Limpar
for pat in ['mcr/kernel/markov_*.json', 'mcr/markov_*.json']:
    for f in glob.glob(f'E:/MCR/{pat}'):
        try: os.remove(f)
        except: pass

import mcr.extrator_features as ef_mod
ef_mod._extrator = None

from mcr.mcr import MCR
mcr = MCR()
mcr._sem_llm = True

print(f'\n[ESTADO INICIAL]')
print(f'  MK decisao: {len(mcr.mk.transicoes)} est, {mcr.mk.total} total')
print(f'  MK palavra: {len(mcr.mk_palavra.transicoes)} est, {mcr.mk_palavra.total} total')
print(f'  Coupling: {mcr._coupling.estatisticas()}')
print(f'  Esfera: {mcr._esfera.estatisticas()["total"]} pares')
print(f'  Stopwords: {len(getattr(mcr, "_stopwords_cache", set()))}')
print(f'  Dataset externo: NAO')

# ── Testa roteamento cold ──
tests = [
    ('Crie um NPC ferreiro', 'npc'),
    ('Gere um monstro dragao', 'monstro'),
    ('O que e Markov?', 'responder'),
    ('Crie um sprite de sword', 'sprite'),
    ('Crie um NPC mago', 'npc'),
    ('Gere um monstro orc', 'monstro'),
    ('Como funciona entropia?', 'responder'),
    ('Faca um monstro demonio', 'monstro'),
]
print(f'\n[ROTEAMENTO COLD START]')
acertos = 0
for inp, exp in tests:
    est = mcr._perceber(inp)
    acao, conf = mcr._decidir(est, inp)
    acao_norm = str(acao).replace('_lua', '')
    ok = exp in acao_norm
    if ok: acertos += 1
    print(f'  {"OK" if ok else "ER"} {inp[:40]:40s} -> {acao_norm:20s} ({conf:.3f})')
acc = acertos / len(tests) * 100
print(f'  Cold routing: {acertos}/{len(tests)} ({acc:.0f}%)')

# ── Geração real ──
print(f'\n[GERACAO REAL]')
for inp in ['Crie um NPC ferreiro', 'Gere um monstro dragao']:
    r = mcr.processar(inp)
    acao = str(r.get('acao', '?')).replace('_lua', '')
    sucesso = r.get('sucesso', False)
    codigo = str(r.get('resultado', {}).get('codigo', ''))
    tam = len(codigo)
    ok_npc = 'npcType:register' in codigo
    ok_mon = 'mType:register' in codigo or 'monsterType:register' in codigo
    ok = ok_npc or ok_mon
    print(f'  {"OK" if ok else "ER"} {inp[:40]:40s} -> {acao} {tam}b {"npc" if ok_npc else "mon" if ok_mon else "?"}')

# ── Persistência ──
print(f'\n[PERSISTENCIA]')
mcr.mk.save()
mcr.mk_palavra.save()
jsons = glob.glob('E:/MCR/mcr/kernel/markov_*.json')
print(f'  JSONs: {len(jsons)}')
for j in jsons:
    sz = os.path.getsize(j)
    with open(j) as f:
        d = json.load(f)
    print(f'    {os.path.basename(j)}: {sz}b, {len(d.get("transicoes",{}))} est, {d.get("total",0)} total')

ef_mod._extrator = None
mcr2 = MCR()
mcr2._sem_llm = True
reload_ok = 0
for inp, exp in tests[:4]:
    ac, _ = mcr2._decidir(mcr2._perceber(inp), inp)
    if exp in str(ac).replace('_lua', ''): reload_ok += 1
print(f'  Roteamento pos-reload: {reload_ok}/4')

# ── Métricas finais ──
print(f'\n[ESTADO FINAL]')
print(f'  MK decisao: {len(mcr.mk.transicoes)} est, {mcr.mk.total} total')
print(f'  MK palavra: {len(mcr.mk_palavra.transicoes)} est, {mcr.mk_palavra.total} total')
print(f'  Coupling: {mcr._coupling.estatisticas()}')
print(f'  Esfera: {mcr._esfera.estatisticas()["total"]} pares')

print(f'\n{"="*65}')
print(f'  RESULTADO AUTONOMO')
print(f'  Routing: {acc:.0f}%')
print(f'  Geracao: {"SIM" if "npcType:register" in str(mcr._resultados if hasattr(mcr,"_resultados") else "") else "VERIFICAR"}')
print(f'  Persistencia: {"SIM" if len(jsons) >= 1 else "NAO"}')
print(f'  Dataset externo: NAO')
print(f'  LLM: NAO')
print(f'{"="*65}')

for f in glob.glob('E:/MCR/mcr/kernel/markov_*.json'):
    try: os.remove(f)
    except: pass
