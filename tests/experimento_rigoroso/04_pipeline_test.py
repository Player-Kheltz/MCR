"""04: Pipeline Test - Testa processar() real sem LLM.

Valida que o pipeline completo funciona:
  perceber -> decidir -> executar -> avaliar -> aprender

Sem LLM. Sem mk.aprender() direto. O MCR aprende via processar().
"""
import sys, json, time, os, glob
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 65)
print('  PIPELINE TEST - processar() real, zero LLM')
print('  perceber -> decidir -> executar -> avaliar -> aprender')
print('=' * 65)

with open('E:/MCR/tests/experimento_rigoroso/dataset_500.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)
print(f'Dataset: {len(dataset)} entradas')

ACTIONS = ['gerar_npc', 'gerar_monstro', 'gerar_quest', 'gerar_sprite', 'responder']
SUBSET_SIZE = 40

def limpar_memoria():
    patterns = [
        'E:/MCR/mcr/kernel/markov_*.json',
        'E:/MCR/mcr/markov_*.json',
        'E:/MCR/devia/kernel/mcr_kernel/markov_*.json',
    ]
    removed = 0
    for pat in patterns:
        for f in glob.glob(pat):
            try:
                os.remove(f)
                removed += 1
            except Exception:
                pass
    return removed

def normalize_action(action):
    return str(action).replace('_lua', '')

# ══════════════════════════════════════════════════════════════
# PASSO 1: Cold Start
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 1] Limpando memória...')
removed = limpar_memoria()
print(f'  Removidos: {removed} arquivos')

import mcr.extrator_features as ef_mod
ef_mod._extrator = None

print('[PASSO 2] Criando MCR (Cold Start, sem LLM)...')
from mcr.mcr import MCR
mcr = MCR()
mcr._sem_llm = True

# ══════════════════════════════════════════════════════════════
# PASSO 3: Medir accuracy antes de processar NADA
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 3] Classificação inicial (cold start)...')
t0 = time.time()
by_action_before = {a: {'correct': 0, 'total': 0} for a in ACTIONS}
for entry in dataset:
    estado = mcr._perceber(entry['input'])
    acao, conf = mcr._decidir(estado)
    expected = entry['expected_action']
    if expected in by_action_before:
        by_action_before[expected]['total'] += 1
        if normalize_action(acao) == expected:
            by_action_before[expected]['correct'] += 1
acc_before = sum(d['correct'] for d in by_action_before.values()) / max(sum(d['total'] for d in by_action_before.values()), 1) * 100
print(f'  Accuracy: {acc_before:.1f}%  ({time.time() - t0:.2f}s)')

# ══════════════════════════════════════════════════════════════
# PASSO 4: Processar N entradas (pipeline real)
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 4] Processando {SUBSET_SIZE} entradas (pipeline real, sem LLM)...')
# Pega uma amostra balanceada
amostra = []
for a in ACTIONS:
    grupo = [d for d in dataset if d['expected_action'] == a]
    n = min(len(grupo), max(3, SUBSET_SIZE // max(len(ACTIONS), 1)))
    amostra.extend(grupo[:n])
if len(amostra) < SUBSET_SIZE:
    amostra.extend(dataset[:SUBSET_SIZE - len(amostra)])

resultados = []
t0 = time.time()
for i, entry in enumerate(amostra[:SUBSET_SIZE]):
    try:
        r = mcr.processar(entry['input'])
        expected = entry['expected_action']
        predicted = normalize_action(r.get('acao', ''))
        acertou = predicted == expected
        r['_expected'] = expected
        r['_acertou'] = acertou
        resultados.append(r)
    except Exception as e:
        resultados.append({'sucesso': False, 'erro': str(e)[:100],
                          '_expected': entry['expected_action'], '_acertou': False})

tempo_total = time.time() - t0

sucessos = sum(1 for r in resultados if r.get('sucesso', False))
acertos = sum(1 for r in resultados if r.get('_acertou', False))
notas = [r.get('nota', 0) for r in resultados if 'nota' in r]
nota_media = sum(notas) / max(len(notas), 1)

print(f'  {sucessos}/{SUBSET_SIZE} execuções OK')
print(f'  {acertos}/{SUBSET_SIZE} classificações corretas')
print(f'  Nota média: {nota_media:.3f}')
print(f'  Tempo: {tempo_total:.2f}s')

# ══════════════════════════════════════════════════════════════
# PASSO 5: Medir accuracy DEPOIS de processar
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 5] Classificação pós-treino...')
t0 = time.time()
by_action_after = {a: {'correct': 0, 'total': 0} for a in ACTIONS}
for entry in dataset:
    estado = mcr._perceber(entry['input'])
    acao, conf = mcr._decidir(estado)
    expected = entry['expected_action']
    if expected in by_action_after:
        by_action_after[expected]['total'] += 1
        if normalize_action(acao) == expected:
            by_action_after[expected]['correct'] += 1
acc_after = sum(d['correct'] for d in by_action_after.values()) / max(sum(d['total'] for d in by_action_after.values()), 1) * 100
print(f'  Accuracy: {acc_after:.1f}%  ({time.time() - t0:.2f}s)')
print(f'  Delta: {acc_after - acc_before:+.1f}pp')

for a in ACTIONS:
    db = by_action_before[a]
    da = by_action_after[a]
    pct_b = db['correct'] / max(db['total'], 1) * 100 if db['total'] else 0
    pct_a = da['correct'] / max(da['total'], 1) * 100 if da['total'] else 0
    print(f'    {a}: {pct_b:.1f}% → {pct_a:.1f}%  ({pct_a-pct_b:+.1f}pp)')

# ══════════════════════════════════════════════════════════════
# PASSO 6: Métricas MCR
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 6] Métricas:')
print(f'  MK: {len(mcr.mk.transicoes)} estados, '
      f'{sum(len(v) for v in mcr.mk.transicoes.values())} transições')
print(f'  Tempo médio/input: {tempo_total / SUBSET_SIZE:.2f}s')

h = mcr.mk.entropia_media()
print(f'  Entropia MK: {h:.4f}')

if mcr._historico:
    deltas_h = [e.get('delta_h', 0) for e in mcr._historico if 'delta_h' in e]
    if deltas_h:
        print(f'  Delta H médio: {sum(deltas_h) / len(deltas_h):.4f} '
              f'({deltas_h[-10:] if len(deltas_h) > 10 else deltas_h})')

# ══════════════════════════════════════════════════════════════
# PASSO 7: Salvar + recarregar → validar persistência
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 7] Persistência...')
mcr.mk.save()
mk_est = len(mcr.mk.transicoes)
mk_trans = sum(len(v) for v in mcr.mk.transicoes.values())

ef_mod._extrator = None
mcr2 = MCR()
mcr2._sem_llm = True
mk2_est = len(mcr2.mk.transicoes)
mk2_trans = sum(len(v) for v in mcr2.mk.transicoes.values())
persistiu = mk2_trans > 0 and mk2_est == mk_est
print(f'  Antes: {mk_est} est, {mk_trans} trans')
print(f'  Depois: {mk2_est} est, {mk2_trans} trans')
print(f'  Persistência: {"OK" if persistiu else "FALHOU"}')

if persistiu:
    acc_persist = 0
    acc_total = 0
    for entry in dataset:
        estado = mcr2._perceber(entry['input'])
        acao, _ = mcr2._decidir(estado)
        if normalize_action(acao) == entry['expected_action']:
            acc_persist += 1
        acc_total += 1
    acc_p = acc_persist / max(acc_total, 1) * 100
    print(f'  Accuracy recarregado: {acc_p:.1f}%')

# ══════════════════════════════════════════════════════════════
# PASSO 8: Limpar
# ══════════════════════════════════════════════════════════════
print(f'\n[PASSO 8] Limpando...')
removed = limpar_memoria()
print(f'  Removidos: {removed} arquivos')

# ══════════════════════════════════════════════════════════════
print('\n' + '=' * 65)
print('  RESULTADO')
print('=' * 65)
print(f'  Accuracy antes:  {acc_before:.1f}%')
print(f'  Accuracy depois: {acc_after:.1f}%  (+{acc_after-acc_before:+.1f}pp)')
print(f'  Entropia MK:     {h:.4f}')
print(f'  Nota média:      {nota_media:.3f}')
print(f'  LLM usado:       NÃO')
print(f'  Pipeline testado: perceber -> decidir -> executar -> avaliar -> aprender')
print('=' * 65)

resultado = {
    'pipeline_test': True, 'sem_llm': True,
    'acc_before': round(acc_before, 1),
    'acc_after': round(acc_after, 1),
    'delta': round(acc_after - acc_before, 1),
    'entropia': round(h, 4),
    'nota_media': round(nota_media, 3),
    'n_processados': SUBSET_SIZE,
    'n_sucessos': sucessos,
    'tempo_total': round(tempo_total, 2),
    'persistencia_ok': persistiu,
}
with open(os.path.join(RESULTS_DIR, 'pipeline_result.json'), 'w') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
print(f'\nSalvo em {RESULTS_DIR}/pipeline_result.json')
