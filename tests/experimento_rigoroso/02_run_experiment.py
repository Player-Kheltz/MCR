"""02: Roda experimento — classificação rápida (480) + amostra completa (80).
FASE 1: 480 inputs → perceber+decidir (~25s) → accuracy, confidence, latency
FASE 2: 80 inputs → processar completo → code quality, semantic
FASE 3: Observer test
FASE 4: KG coverage test
"""
import sys, json, time, os, random
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 65)
print('  EXPERIMENTO MCR')
print('=' * 65)

# ─── LOAD DATASET ──────────────────────────────────────────
with open('E:/MCR/tests/experimento_rigoroso/dataset_500.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)
print(f'Dataset: {len(dataset)} entradas')

# ─── INIT MCR ──────────────────────────────────────────────
mcr = MCR()
print('[MCR] Pronto.')

def normalize_action(action):
    return action.replace('_lua', '').replace('gerar_npc_lua', 'gerar_npc').replace('gerar_monstro_lua', 'gerar_monstro')


# ══════════════════════════════════════════════════════════════
# FASE 1: CLASSIFICAÇÃO RÁPIDA (480 inputs)
# ══════════════════════════════════════════════════════════════
print('\n[FASE 1] Classificando 480 entradas (rápido)...')
classification = []
latency = []
t_total = time.time()

for i, entry in enumerate(dataset):
    t0 = time.time()
    try:
        estado = mcr._perceber(entry['input'])
        acao, confianca = mcr._decidir(estado)
    except Exception as e:
        acao, confianca = 'erro', 0.0
    elapsed = time.time() - t0

    predicted = normalize_action(str(acao))
    expected = entry['expected_action']
    correct = predicted == expected

    classification.append({
        'id': entry['id'], 'input': entry['input'][:100],
        'predicted': predicted, 'expected': expected,
        'correct': correct, 'confidence': round(confianca, 4),
        'language': entry['language'], 'complexity': entry['complexity'],
    })
    latency.append(round(elapsed * 1000, 1))

    if (i + 1) % 100 == 0:
        print(f'  {i+1}/{len(dataset)} classificados...', flush=True)

elapsed_classif = time.time() - t_total
print(f'  Classificação: {len(dataset)} em {elapsed_classif:.1f}s ({elapsed_classif/len(dataset)*1000:.0f}ms/input)')

# Métricas de classificação
correct_total = sum(1 for c in classification if c['correct'])
accuracy = correct_total / len(classification) * 100
print(f'  Accuracy: {correct_total}/{len(classification)} = {accuracy:.1f}%')

# Por ação
by_action = {}
for c in classification:
    a = c['expected']
    if a not in by_action:
        by_action[a] = {'correct': 0, 'total': 0, 'predictions': {}}
    by_action[a]['total'] += 1
    if c['correct']:
        by_action[a]['correct'] += 1
    pred = c['predicted']
    by_action[a]['predictions'][pred] = by_action[a]['predictions'].get(pred, 0) + 1

for action, stats in sorted(by_action.items()):
    acc = stats['correct'] / stats['total'] * 100
    print(f'    {action}: {stats["correct"]}/{stats["total"]} = {acc:.1f}%')

# Por complexidade
by_complex = {}
for c in classification:
    cx = c['complexity']
    if cx not in by_complex:
        by_complex[cx] = {'correct': 0, 'total': 0}
    by_complex[cx]['total'] += 1
    if c['correct']:
        by_complex[cx]['correct'] += 1

for cx, stats in sorted(by_complex.items()):
    acc = stats['correct'] / stats['total'] * 100
    print(f'    {cx}: {stats["correct"]}/{stats["total"]} = {acc:.1f}%')

# Por idioma
by_lang = {}
for c in classification:
    lg = c['language']
    if lg not in by_lang:
        by_lang[lg] = {'correct': 0, 'total': 0}
    by_lang[lg]['total'] += 1
    if c['correct']:
        by_lang[lg]['correct'] += 1

for lg, stats in sorted(by_lang.items()):
    acc = stats['correct'] / stats['total'] * 100
    print(f'    {lg}: {stats["correct"]}/{stats["total"]} = {acc:.1f}%')

avg_latency = sum(latency) / len(latency)
p95_latency = sorted(latency)[int(len(latency) * 0.95)]
print(f'  Latency: avg={avg_latency:.1f}ms p95={p95_latency:.1f}ms')


# ══════════════════════════════════════════════════════════════
# FASE 2: AMOSTRA COMPLETA (80 inputs — 20/categoria)
# ══════════════════════════════════════════════════════════════
print('\n[FASE 2] Processamento completo — amostra de 80...')
random.seed(42)
sample = []
for action_type in ['gerar_npc', 'gerar_monstro', 'responder', 'gerar_sprite']:
    candidates = [e for e in dataset if e['expected_action'] == action_type]
    sample.extend(random.sample(candidates, min(20, len(candidates))))

validation = []
semantic = []
equation = []
llm_fallbacks = 0

for i, entry in enumerate(sample):
    t0 = time.time()
    try:
        result = mcr.processar(entry['input'])
    except Exception as e:
        result = {'sucesso': False, 'acao': 'erro', 'nota': 0, 'confianca': 0,
                  'resultado': {'erro': str(e)}, 'tempo': 0, 'entrada': entry['input'][:200]}
    elapsed = time.time() - t0

    predicted = normalize_action(result['acao'])
    expected = entry['expected_action']

    # Validation
    valid = result.get('resultado', {}).get('sucesso', False)
    has_code = bool(result.get('resultado', {}).get('codigo', ''))
    validation.append({
        'id': entry['id'], 'action': expected,
        'predicted': predicted, 'valid': valid, 'has_code': has_code,
    })

    # Semantic
    sem_ok = False
    if expected == 'gerar_npc':
        code = str(result.get('resultado', {}).get('codigo', ''))
        prof = entry.get('semantic_fields', {}).get('profession', '')
        sem_ok = prof.lower() in code.lower() if prof and prof != 'unknown' else len(code) > 50
    elif expected == 'gerar_monstro':
        code = str(result.get('resultado', {}).get('codigo', ''))
        creature = entry.get('semantic_fields', {}).get('creature_type', '')
        sem_ok = creature.lower() in code.lower() if creature and creature != 'unknown' else len(code) > 50
    elif expected == 'responder':
        resp = str(result.get('resultado', {}).get('resposta', ''))
        keywords = entry.get('semantic_fields', {}).get('expected_keywords', [])
        if keywords:
            hits = sum(1 for k in keywords if k.lower() in resp.lower())
            sem_ok = hits / len(keywords) > 0.15
        else:
            sem_ok = len(resp) > 5
    elif expected == 'gerar_sprite':
        sem_ok = result.get('sucesso', False)

    semantic.append({
        'id': entry['id'], 'action': expected, 'sem_ok': sem_ok,
        'predicted': predicted, 'input': entry['input'][:80],
    })

    equation.append({
        'id': entry['id'], 'nota': round(result.get('nota', 0), 4),
        'confianca': round(result.get('confianca', 0), 4),
    })

    if result.get('resultado', {}).get('_tool') == 'pipeline_completo':
        llm_fallbacks += 1

    if (i + 1) % 20 == 0:
        print(f'  Amostra {i+1}/{len(sample)} processada...', flush=True)

valid_total = len(validation)
valid_ok = sum(1 for v in validation if v['valid'])
code_total = sum(1 for v in validation if v['action'] in ('gerar_npc', 'gerar_monstro'))
code_ok = sum(1 for v in validation if v['action'] in ('gerar_npc', 'gerar_monstro') and v['has_code'])
sem_total = len(semantic)
sem_ok_count = sum(1 for s in semantic if s['sem_ok'])

print(f'  Validação: {valid_ok}/{valid_total} ({valid_ok/max(valid_total,1)*100:.1f}%)')
print(f'  Código gerado: {code_ok}/{code_total} ({code_ok/max(code_total,1)*100:.1f}%)')
print(f'  Semântico: {sem_ok_count}/{sem_total} ({sem_ok_count/max(sem_total,1)*100:.1f}%)')
print(f'  LLM fallbacks: {llm_fallbacks}')


# ══════════════════════════════════════════════════════════════
# FASE 3: OBSERVER
# ══════════════════════════════════════════════════════════════
print('\n[FASE 3] Observador...')
obs = mcr._observador
observer_results = []
if len(obs._pares) >= 5:
    obs.treinar()
    for entry in dataset:
        pred, conf, H = obs.predizer_com_confianca(entry['input'])
        action_pred = obs._mapear_cluster_para_acao(pred) if pred else None
        observer_results.append({
            'id': entry['id'],
            'predicted_action': action_pred,
            'expected': entry['expected_action'],
            'confidence': round(conf, 4),
            'correct': action_pred == entry['expected_action'] if action_pred else False,
        })
    obs_correct = sum(1 for r in observer_results if r['correct'])
    obs_total = sum(1 for r in observer_results if r['predicted_action'] is not None)
    print(f'  Pares: {len(obs._pares)} | Clusters X: {len(set(obs._clusters_x.values()))} | Clusters Y: {len(set(obs._clusters_y.values()))}')
    print(f'  Observer acertou: {obs_correct}/{obs_total} ({obs_correct/max(obs_total,1)*100:.1f}%)')
else:
    print(f'  Pares insuficientes: {len(obs._pares)}')


# ══════════════════════════════════════════════════════════════
# FASE 4: KG COVERAGE
# ══════════════════════════════════════════════════════════════
print('\n[FASE 4] KG Coverage...')
kg_results = []
try:
    from mcr.metacognicao import Metacognicao
    meta = Metacognicao()
    for entry in dataset:
        score, just = meta.calcular_confianca(entry['input'])
        kg_results.append({
            'id': entry['id'], 'action': entry['expected_action'],
            'score': round(score, 4), 'above_threshold': score > 0.3,
        })
    kg_above = sum(1 for r in kg_results if r['above_threshold'])
    print(f'  KG cobre: {kg_above}/{len(kg_results)} ({kg_above/len(kg_results)*100:.1f}%)')
except Exception as e:
    kg_above = 0
    print(f'  KG erro: {e}')


# ══════════════════════════════════════════════════════════════
# SALVAR RESULTADOS
# ══════════════════════════════════════════════════════════════
print('\n[SALVANDO] Resultados...')
for name, data in [
    ('classification', classification),
    ('validation', validation),
    ('semantic', semantic),
    ('equation', equation),
    ('latency', latency),
    ('observer', observer_results),
    ('kg', kg_results),
]:
    path = os.path.join(RESULTS_DIR, f'{name}_results.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

obs_correct = sum(1 for r in observer_results if r['correct']) if observer_results else 0
obs_total = sum(1 for r in observer_results if r['predicted_action'] is not None) if observer_results else 0

summary = {
    'total_inputs': len(dataset),
    'classification': {
        'accuracy_pct': round(accuracy, 1),
        'correct': correct_total,
        'total': len(classification),
        'by_action': {a: round(s['correct']/s['total']*100, 1) for a, s in by_action.items()},
        'by_complexity': {a: round(s['correct']/s['total']*100, 1) for a, s in by_complex.items()},
        'by_language': {a: round(s['correct']/s['total']*100, 1) for a, s in by_lang.items()},
    },
    'latency': {
        'avg_ms': round(avg_latency, 1),
        'p95_ms': round(p95_latency, 1),
        'elapsed_seconds': round(elapsed_classif, 1),
    },
    'sample_full': {
        'validation_pct': round(valid_ok/max(valid_total,1)*100, 1),
        'code_gen_pct': round(code_ok/max(code_total,1)*100, 1),
        'semantic_pct': round(sem_ok_count/max(sem_total,1)*100, 1),
        'llm_fallbacks': llm_fallbacks,
        'sample_size': len(sample),
    },
    'observer': {
        'accuracy_pct': round(obs_correct/max(obs_total,1)*100, 1) if obs_total > 0 else 0,
        'pairs': len(obs._pares),
        'predictions_made': obs_total,
    },
    'kg': {
        'answerable_pct': round(kg_above / max(len(kg_results), 1) * 100, 1),
        'total_patterns': len(kg_results),
    },
}
with open(os.path.join(RESULTS_DIR, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print('\n' + '=' * 65)
print('  RESUMO')
print('=' * 65)
print(f'  Classification accuracy: {accuracy:.1f}%')
print(f'  Code generation: {code_ok}/{code_total} ({code_ok/max(code_total,1)*100:.1f}%)')
print(f'  Semantic correctness: {sem_ok_count}/{sem_total} ({sem_ok_count/max(sem_total,1)*100:.1f}%)')
print(f'  Observer accuracy: {obs_correct}/{obs_total} ({obs_correct/max(obs_total,1)*100:.1f}%)')
print(f'  KG coverage: {kg_above}/{len(kg_results)} ({kg_above/max(len(kg_results),1)*100:.1f}%)')
print(f'  Latency: avg={avg_latency:.1f}ms p95={p95_latency:.1f}ms')
print(f'  LLM fallbacks: {llm_fallbacks}')
print(f'\nSalvo em: {RESULTS_DIR}/')
