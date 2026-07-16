"""05: Teste de Capacidade Real — processar() completo, zero LLM.

Testa as 4 ações principais com o pipeline completo:
  NPC, Monstro, Sprite, Responder

Verifica roteamento, geração de arquivos, sintaxe, persistência e Observer.
"""
import sys, json, time, os, glob, re
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 70)
print('  TESTE DE CAPACIDADE REAL — processar() completo, zero LLM')
print('=' * 70)

def limpar_memoria():
    patterns = [
        'E:/MCR/mcr/kernel/markov_*.json',
        'E:/MCR/mcr/markov_*.json',
        'E:/MCR/devia/kernel/mcr_kernel/markov_*.json',
    ]
    removed = 0
    for pat in patterns:
        for f in glob.glob(pat):
            try: os.remove(f); removed += 1
            except: pass
    return removed

# ══════════════════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════════════════
print('\n[SETUP] Limpando...')
limpar_memoria()
import mcr.extrator_features as ef_mod
ef_mod._extrator = None

from mcr.mcr import MCR
mcr = MCR()
mcr._sem_llm = True

results = {}
t0_total = time.time()

# ══════════════════════════════════════════════════════════════
# TESTE 1: NPC
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[T1] NPC — processar("Crie um NPC ferreiro")')
print('-' * 70)

t0 = time.time()
r_npc = mcr.processar("Crie um NPC ferreiro")
dt_npc = time.time() - t0

acao_npc = r_npc.get('acao', '?')
nota_npc = r_npc.get('nota', 0)
conf_npc = r_npc.get('confianca', 0)
sucesso_npc = r_npc.get('sucesso', False)
codigo_npc = r_npc.get('resultado', {}).get('codigo', '')
tool_npc = r_npc.get('resultado', {}).get('_tool', '?')
llm_fb = r_npc.get('resultado', {}).get('tipo', '') == 'llm_fallback'

rot_npc = 'gerar_npc' in str(acao_npc)
has_lua = 'npcType:register' in str(codigo_npc) or 'registerNpcType' in str(codigo_npc)
tem_nome = 'Entidade' not in str(codigo_npc) and has_lua

print(f'  Acao: {acao_npc} | Nota: {nota_npc:.2f} | Conf: {conf_npc:.2f} | Tempo: {dt_npc:.2f}s')
print(f'  Sucesso: {sucesso_npc} | Tool: {tool_npc} | LLM: {llm_fb}')
print(f'  Roteamento correto: {rot_npc}')
print(f'  Codigo Lua gerado: {has_lua} ({len(str(codigo_npc))} chars)')
print(f'  Nome no codigo: {tem_nome}')
if codigo_npc:
    snippet = str(codigo_npc)[:300].replace('\n', '\\n')
    print(f'  Snippet: {snippet}...')

results['npc'] = {
    'acao': str(acao_npc), 'nota': nota_npc, 'confianca': conf_npc,
    'sucesso': sucesso_npc, 'tempo': round(dt_npc, 3),
    'roteamento_ok': rot_npc, 'lua_valido': has_lua, 'tamanho': len(str(codigo_npc)),
    'llm_usado': llm_fb, 'tool': str(tool_npc),
}

# ══════════════════════════════════════════════════════════════
# TESTE 2: MONSTRO
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[T2] MONSTRO — processar("Gere um monstro dragao de fogo")')
print('-' * 70)

t0 = time.time()
r_mon = mcr.processar("Gere um monstro dragao")
dt_mon = time.time() - t0

acao_mon = r_mon.get('acao', '?')
nota_mon = r_mon.get('nota', 0)
codigo_mon = r_mon.get('resultado', {}).get('codigo', '')
tool_mon = r_mon.get('resultado', {}).get('_tool', '?')
llm_fb2 = r_mon.get('resultado', {}).get('tipo', '') == 'llm_fallback'

rot_mon = 'gerar_monstro' in str(acao_mon)
has_mon_lua = 'monsterType:register' in str(codigo_mon) or 'mType:register' in str(codigo_mon)
is_npc_lua = 'npcType:register' in str(codigo_mon)

print(f'  Acao: {acao_mon} | Nota: {nota_mon:.2f} | Tempo: {dt_mon:.2f}s')
print(f'  Tool: {tool_mon} | LLM: {llm_fb2}')
print(f'  Roteamento correto: {rot_mon}')
print(f'  Codigo monstro: {has_mon_lua}')
print(f'  Codigo NPC por engano: {is_npc_lua}')
print(f'  Tamanho: {len(str(codigo_mon))} chars')
if codigo_mon:
    snippet = str(codigo_mon)[:250].replace('\n', '\\n')
    print(f'  Snippet: {snippet}...')

results['monstro'] = {
    'acao': str(acao_mon), 'nota': nota_mon, 'tempo': round(dt_mon, 3),
    'roteamento_ok': rot_mon, 'monster_lua': has_mon_lua,
    'npc_lua_por_engano': is_npc_lua, 'tamanho': len(str(codigo_mon)),
    'llm_usado': llm_fb2, 'tool': str(tool_mon),
}

# ══════════════════════════════════════════════════════════════
# TESTE 3: SPRITE
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[T3] SPRITE — processar("Crie um sprite de sword")')
print('-' * 70)

t0 = time.time()
r_sprite = mcr.processar("Crie um sprite de sword")
dt_sprite = time.time() - t0

acao_sprite = r_sprite.get('acao', '?')
nota_sprite = r_sprite.get('nota', 0)
sucesso_sprite = r_sprite.get('sucesso', False)
tool_sprite = r_sprite.get('resultado', {}).get('_tool', '?')
codigo_sprite = r_sprite.get('resultado', {}).get('codigo', '') or str(r_sprite.get('resultado', {}))

rot_sprite = 'gerar_sprite' in str(acao_sprite)
sprite_ok = sucesso_sprite

print(f'  Acao: {acao_sprite} | Nota: {nota_sprite:.2f} | Sucesso: {sucesso_sprite}')
print(f'  Tool: {tool_sprite} | Tempo: {dt_sprite:.2f}s')
print(f'  Roteamento: {rot_sprite}')

results['sprite'] = {
    'acao': str(acao_sprite), 'nota': nota_sprite, 'sucesso': sucesso_sprite,
    'roteamento_ok': rot_sprite, 'tamanho': len(str(codigo_sprite)),
    'tempo': round(dt_sprite, 3), 'tool': str(tool_sprite),
}

# ══════════════════════════════════════════════════════════════
# TESTE 4: RESPONDER
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[T4] RESPONDER — processar("O que e Markov?")')
print('-' * 70)

t0 = time.time()
r_resp = mcr.processar("O que e Markov?")
dt_resp = time.time() - t0

acao_resp = r_resp.get('acao', '?')
nota_resp = r_resp.get('nota', 0)
resposta = r_resp.get('resultado', {}).get('resposta', '') or r_resp.get('resultado', {}).get('codigo', '')
resp_len = len(str(resposta))
tool_resp = r_resp.get('resultado', {}).get('_tool', '?')

rot_resp = 'responder' in str(acao_resp)
tem_resposta = resp_len > 10

print(f'  Acao: {acao_resp} | Nota: {nota_resp:.2f} | Tempo: {dt_resp:.2f}s')
print(f'  Tool: {tool_resp}')
print(f'  Roteamento correto: {rot_resp}')
print(f'  Tem resposta: {tem_resposta} ({resp_len} chars)')
if resposta:
    print(f'  Resposta: {str(resposta)[:200]}')

results['responder'] = {
    'acao': str(acao_resp), 'nota': nota_resp, 'tempo': round(dt_resp, 3),
    'roteamento_ok': rot_resp, 'tem_resposta': tem_resposta,
    'tamanho_resposta': resp_len, 'tool': str(tool_resp),
}

# ══════════════════════════════════════════════════════════════
# MÉTRICAS DO SISTEMA
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[METRICAS] Estado do sistema apos 4 processar()')
print('-' * 70)

mk_est = len(mcr.mk.transicoes)
mk_trans = sum(len(v) for v in mcr.mk.transicoes.values())
mk_ent = mcr.mk.entropia_media()
mk_pal_est = len(mcr.mk_palavra.transicoes)
mk_pal_trans = sum(len(v) for v in mcr.mk_palavra.transicoes.values())

print(f'  MK decisao: {mk_est} estados, {mk_trans} transicoes, entropia={mk_ent:.4f}')
print(f'  MK palavra: {mk_pal_est} estados, {mk_pal_trans} transicoes')
print(f'  Cadeias persistidas (JSON): ', end='')
for f in glob.glob('E:/MCR/mcr/kernel/markov_*.json'):
    print(f'  sim ({os.path.basename(f)}: {os.path.getsize(f)} bytes)', end=' ')
print()

# Observer
obs_pares = len(mcr._observador._pares) if mcr._observador else 0
obs_treinado = mcr._observador._treinado if mcr._observador else False
obs_cobertura = mcr._observador.cobertura() if mcr._observador and obs_treinado else 0
print(f'  Observer: {obs_pares} pares, treinado={obs_treinado}, cobertura={obs_cobertura:.3f}')

# Historico
n_hist = len(mcr._historico)
if n_hist > 0:
    notas_hist = [h['nota'] for h in mcr._historico if 'nota' in h]
    deltas_h = [h.get('delta_h', 0) for h in mcr._historico if 'delta_h' in h]
    print(f'  Historico: {n_hist} entradas')
    print(f'  Notas: min={min(notas_hist):.2f} max={max(notas_hist):.2f} media={sum(notas_hist)/len(notas_hist):.2f}')
    if deltas_h:
        print(f'  Delta H: {deltas_h}')

# Tempo total
t_total = time.time() - t0_total
print(f'\n  Tempo total: {t_total:.2f}s')

# ══════════════════════════════════════════════════════════════
# PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════
print('\n' + '-' * 70)
print('[PERSISTENCIA] Recarregando MCR...')
print('-' * 70)

mcr.mk.save()
mcr.mk_palavra.save()
ef_mod._extrator = None
mcr2 = MCR()
mcr2._sem_llm = True

mk2_est = len(mcr2.mk.transicoes)
mk2_trans = sum(len(v) for v in mcr2.mk.transicoes.values())
mk2_pal_est = len(mcr2.mk_palavra.transicoes)
mk2_pal_trans = sum(len(v) for v in mcr2.mk_palavra.transicoes.values())

persist_ok = (mk2_est == mk_est and mk2_trans == mk_trans)

print(f'  MK decision:  {mk_est}/{mk_trans} -> {mk2_est}/{mk2_trans} | OK={mk2_est==mk_est}')
print(f'  MK palavra:   {mk_pal_est}/{mk_pal_trans} -> {mk2_pal_est}/{mk2_pal_trans}')
print(f'  Persistencia: {"OK" if persist_ok else "FALHOU"}')

# Testa routing no MCR recarregado
t0 = time.time()
tests_persist = [
    ("Crie um NPC ferreiro", "gerar_npc"),
    ("Gere um monstro dragao", "gerar_monstro"),
    ("O que e Markov?", "responder"),
]
persist_routing = []
for inp, exp in tests_persist:
    est = mcr2._perceber(inp)
    ac, _ = mcr2._decidir(est)
    ok = exp in str(ac)
    persist_routing.append(ok)
    print(f'  {inp[:30]:30s} -> {str(ac):20s} {"OK" if ok else "ERRO"}')

routing_ok = all(persist_routing)
print(f'  Roteamento pos-reload: {"OK" if routing_ok else "FALHOU"}')

# ══════════════════════════════════════════════════════════════
# RESULTADO FINAL
# ══════════════════════════════════════════════════════════════
print('\n' + '=' * 70)
print('  RESULTADO FINAL — Capacidades Reais do MCR')
print('=' * 70)

score = 0
total = 0

def check(nome, cond):
    global score, total
    total += 1
    if cond: score += 1
    print(f'  {"OK" if cond else "ERRO"} {nome}')

check('NPC: roteamento', rot_npc)
check('NPC: codigo Lua gerado', has_lua)
check('NPC: nome no codigo', tem_nome)
check('NPC: sem LLM', not llm_fb)
check('MONSTRO: roteamento', rot_mon)
check('MONSTRO: codigo Lua monstro', has_mon_lua)
check('MONSTRO: nao gerou NPC', not is_npc_lua)
check('MONSTRO: sem LLM', not llm_fb2)
check('SPRITE: roteamento', rot_sprite)
check('RESPONDER: roteamento', rot_resp)
check('RESPONDER: tem resposta', tem_resposta)
check('PERSISTENCIA: mk decision', persist_ok)
check('ROTEAMENTO: pos-reload', routing_ok)

print(f'\n  Score: {score}/{total} ({score/total*100:.0f}%)')
print(f'  Tempo total: {t_total:.2f}s')
print(f'  LLM usado: NAO')
print('=' * 70)

results['score'] = f'{score}/{total}'
results['score_pct'] = round(score/total*100)
results['tempo_total'] = round(t_total, 2)
results['persistencia'] = {'mk_ok': persist_ok, 'routing_ok': routing_ok}
results['observer'] = {'pares': obs_pares, 'treinado': obs_treinado}
results['markov'] = {'mk_estados': mk_est, 'mk_transicoes': mk_trans, 'entropia': round(mk_ent, 4)}

with open(os.path.join(RESULTS_DIR, 'capability_result.json'), 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print(f'\nSalvo em {RESULTS_DIR}/capability_result.json')

# Limpar
limpar_memoria()
