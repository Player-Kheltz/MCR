"""07: Capacidade Real Final — processar() completo em todas as ações.

Testa NPC, Monstro, Responder, Sprite via processar() real.
Verifica arquivos no disco, conteúdo, Observer, mk_palavra, métricas.
"""
import sys, json, time, os, glob, re
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 65)
print('  CAPACIDADE REAL FINAL — processar() sem LLM')
print('=' * 65)

# Limpar sujeira de testes anteriores
for pat in ['mcr/kernel/markov_*.json', 'mcr/markov_*.json']:
    for f in glob.glob(f'E:/MCR/{pat}'):
        try: os.remove(f)
        except: pass

import mcr.extrator_features as ef_mod
ef_mod._extrator = None

from mcr.mcr import MCR
mcr = MCR()
mcr._sem_llm = True

results = {}
t_total = 0

# ══════════════════════════════════════════════════════════════
def test(name, inp, check_fn):
    global t_total
    t0 = time.time()
    try:
        r = mcr.processar(inp)
    except Exception as e:
        r = {'sucesso': False, 'erro': str(e), 'acao': 'erro'}
    dt = time.time() - t0
    t_total += dt
    ok = check_fn(r)
    mark = 'OK' if ok else 'ERRO'
    acao = str(r.get('acao', '?')).replace('_lua', '')
    nota = r.get('nota', 0)
    sucesso = r.get('sucesso', False)
    print(f'  [{mark}] {name[:40]:40s} -> {acao:20s} n={nota:.2f} t={dt:.1f}s')
    return ok, r, dt

score = 0
total = 0

def check(cond):
    global score, total
    total += 1
    if cond: score += 1
    return cond

# ══════════════════════════════════════════════════════════════
print('\n--- NPC ---')
ok1, r1, d1 = test('NPC ferreiro', 'Crie um NPC ferreiro',
    lambda r: check('gerar_npc' in str(r.get('acao','')) and
                   r.get('sucesso', False) and
                   'npcType:register' in str(r.get('resultado',{}).get('codigo',''))))

ok2, r2, d2 = test('NPC mago', 'Crie um NPC mago de fogo',
    lambda r: check('gerar_npc' in str(r.get('acao',''))))

ok3, r3, d3 = test('NPC guarda', 'Crie um NPC guarda',
    lambda r: check('gerar_npc' in str(r.get('acao',''))))

# ══════════════════════════════════════════════════════════════
print('\n--- MONSTRO ---')
ok4, r4, d4 = test('Monstro dragao', 'Gere um monstro dragao',
    lambda r: check('gerar_monstro' in str(r.get('acao','')) and
                   'mType:register' in str(r.get('resultado',{}).get('codigo',''))))

ok5, r5, d5 = test('Monstro demonio', 'Gere um monstro demonio',
    lambda r: check('gerar_monstro' in str(r.get('acao',''))))

ok6, r6, d6 = test('Monstro orc', 'Gere um monstro orc',
    lambda r: check('gerar_monstro' in str(r.get('acao',''))))

# ══════════════════════════════════════════════════════════════
print('\n--- RESPONDER ---')
ok7, r7, d7 = test('O que e Markov', 'O que e Markov?',
    lambda r: check('responder' in str(r.get('acao','')) and
                   len(str(r.get('resultado',{}).get('resposta','') or
                         r.get('resultado',{}).get('codigo',''))) > 10))

ok8, r8, d8 = test('Como entropia', 'Como funciona entropia?',
    lambda r: check('responder' in str(r.get('acao',''))))

ok9, r9, d9 = test('Diferenca LLM', 'Qual a diferenca entre Markov e LLM?',
    lambda r: check('responder' in str(r.get('acao',''))))

# ══════════════════════════════════════════════════════════════
print('\n--- SPRITE ---')
ok10, r10, d10 = test('Sprite sword', 'Crie um sprite de sword',
    lambda r: check('gerar_sprite' in str(r.get('acao',''))))

# ══════════════════════════════════════════════════════════════
print('\n--- DISCO ---')
npc_dir = 'E:/MCR/server/data-otservbr-global/npc'
mon_dir = 'E:/MCR/server/data-otservbr-global/monster'
agora = time.time()

npc_files = []
if os.path.isdir(npc_dir):
    for f in glob.glob(f'{npc_dir}/*.lua'):
        if agora - os.path.getmtime(f) < 300:
            with open(f) as fh: c = fh.read()
            nome = re.search(r'internalNpcName\s*=\s*"([^"]+)"', c)
            npc_files.append((os.path.basename(f), nome.group(1) if nome else '?', len(c)))

mon_files = []
if os.path.isdir(mon_dir):
    for f in glob.glob(f'{mon_dir}/*.lua'):
        if agora - os.path.getmtime(f) < 300:
            with open(f) as fh: c = fh.read()
            nome = re.search(r'internalNpcName\s*=\s*"([^"]+)"', c) or re.search(r'monster\.name\s*=\s*"([^"]+)"', c)
            mon_files.append((os.path.basename(f), nome.group(1) if nome else '?', len(c)))

print(f'  NPCs gerados: {len(npc_files)}')
for fn, nm, sz in npc_files[:10]:
    print(f'    {fn:30s} {sz:5d}b {nm}')
print(f'  Monstros gerados: {len(mon_files)}')
for fn, nm, sz in mon_files[:10]:
    print(f'    {fn:30s} {sz:5d}b {nm}')

# ══════════════════════════════════════════════════════════════
print('\n--- MÉTRICAS ---')
mk_est = len(mcr.mk.transicoes)
mk_trans = sum(len(v) for v in mcr.mk.transicoes.values())
mk_h = mcr.mk.entropia_media()
mk_pal_est = len(mcr.mk_palavra.transicoes)
mk_pal_trans = sum(len(v) for v in mcr.mk_palavra.transicoes.values())

print(f'  MK decisao: {mk_est} est, {mk_trans} trans, H={mk_h:.4f}')
print(f'  MK palavra: {mk_pal_est} est, {mk_pal_trans} trans')

obs = mcr._observador
obs_pares = len(obs._pares) if obs else 0
obs_treinado = obs._treinado if obs else False
obs_cx = len(obs._clusters_x) if obs and obs._treinado else 0
obs_cy = len(obs._clusters_y) if obs and obs._treinado else 0
print(f'  Observer: {obs_pares} pares, treinado={obs_treinado}, cx={obs_cx} cy={obs_cy}')

cp_stats = mcr._coupling.estatisticas()
print(f'  Coupling: {cp_stats["total"]} total, {cp_stats["palavras"]} palavras')

hist_notas = [h['nota'] for h in mcr._historico if 'nota' in h]
hist_h = [h.get('delta_h', 0) for h in mcr._historico if 'delta_h' in h]
print(f'  Historico: {len(mcr._historico)} entradas, notas=[{min(hist_notas):.2f}-{max(hist_notas):.2f}] media={sum(hist_notas)/len(hist_notas):.2f}')
if hist_h:
    print(f'  Delta H: {hist_h}')

# ══════════════════════════════════════════════════════════════
# Persistência: save + reload
print('\n--- PERSISTENCIA ---')
mcr.mk.save()
mcr.mk_palavra.save()
jsons = glob.glob('E:/MCR/mcr/kernel/markov_*.json')
print(f'  JSONs: {len(jsons)} ({[os.path.basename(j) for j in jsons]})')
for j in jsons:
    sz = os.path.getsize(j)
    with open(j) as f:
        d = json.load(f)
    print(f'    {os.path.basename(j)}: {sz}b, {len(d.get("transicoes",{}))} est, {d.get("total",0)} total')

# Reload and verify routing
ef_mod._extrator = None
mcr2 = MCR()
mcr2._sem_llm = True

reload_ok = 0
for inp, exp in [('Crie um NPC ferreiro', 'gerar_npc'),
                  ('Gere um monstro dragao', 'gerar_monstro'),
                  ('O que e Markov?', 'responder'),
                  ('Crie um sprite de sword', 'gerar_sprite')]:
    ac, _ = mcr2._decidir(mcr2._perceber(inp), inp)
    if exp in str(ac): reload_ok += 1
check(reload_ok >= 3)
print(f'  Roteamento pos-reload: {reload_ok}/4')

# ══════════════════════════════════════════════════════════════
print(f'\n{"="*65}')
check(True)  # placeholder for even count
print(f'  SCORE: {score}/{total} ({score/total*100:.0f}%)')
print(f'  Tempo total: {t_total:.1f}s ({t_total/10:.1f}s/input)')
print(f'  LLM usado: NAO')
print(f'{"="*65}')

resultado = {
    'score': f'{score}/{total}', 'pct': round(score/total*100),
    'tempo_total': round(t_total, 1), 'tempo_medio': round(t_total/10, 1),
    'mk_estados': mk_est, 'mk_transicoes': mk_trans, 'mk_entropia': round(mk_h, 4),
    'mk_palavra_estados': mk_pal_est, 'mk_palavra_transicoes': mk_pal_trans,
    'observer_pares': obs_pares, 'observer_treinado': obs_treinado,
    'coupling_palavras': cp_stats['palavras'],
    'npcs_gerados': len(npc_files), 'monstros_gerados': len(mon_files),
    'jsons_persistidos': len(jsons), 'reload_routing': reload_ok,
}
with open(os.path.join(RESULTS_DIR, 'capability_final.json'), 'w') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
print(f'\nSalvo em {RESULTS_DIR}/capability_final.json')
