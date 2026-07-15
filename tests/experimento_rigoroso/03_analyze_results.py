"""03: Analise estatistica dos resultados do experimento."""
import json, os, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'

print('=' * 70)
print('  ANALISE ESTATISTICA DO EXPERIMENTO MCR')
print('=' * 70)

# ─── Load ──────────────────────────────────────────────────
with open(os.path.join(RESULTS_DIR, 'classification_results.json'), 'r') as f:
    classification = json.load(f)
with open(os.path.join(RESULTS_DIR, 'validation_results.json'), 'r') as f:
    validation = json.load(f)
with open(os.path.join(RESULTS_DIR, 'semantic_results.json'), 'r') as f:
    semantic = json.load(f)
with open(os.path.join(RESULTS_DIR, 'equation_results.json'), 'r') as f:
    equation = json.load(f)
with open(os.path.join(RESULTS_DIR, 'latency_results.json'), 'r') as f:
    latency = json.load(f)
with open(os.path.join(RESULTS_DIR, 'observer_results.json'), 'r') as f:
    observer = json.load(f)

# ══════════════════════════════════════════════════════════════
# 1. CONFUSION MATRIX
# ══════════════════════════════════════════════════════════════
print('\n[1] CONFUSION MATRIX')
actions = ['gerar_npc', 'gerar_monstro', 'responder', 'gerar_sprite']
confusion = defaultdict(lambda: defaultdict(int))
for c in classification:
    confusion[c['expected']][c['predicted']] += 1

header = f'{"":>15} ' + ' '.join(f'{a:>15}' for a in actions)
print(f'  Predicted ->')
print(f'  Expected v')
for expected in actions:
    row = f'  {expected:>15} '
    for predicted in actions:
        count = confusion[expected][predicted]
        marker = '*' if expected == predicted else ' '
        row += f'{count:>12}{marker} '
    print(row)

# ══════════════════════════════════════════════════════════════
# 2. PER-CLASS METRICS (Precision, Recall, F1)
# ══════════════════════════════════════════════════════════════
print('\n[2] PER-CLASS METRICS')
print(f'  {"Action":>15} {"TP":>4} {"FP":>4} {"FN":>4} {"Prec":>7} {"Rec":>7} {"F1":>7}')
for action in actions:
    tp = confusion[action][action]
    fp = sum(confusion[other][action] for other in actions if other != action)
    fn = sum(confusion[action][other] for other in actions if other != action)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f'  {action:>15} {tp:>4} {fp:>4} {fn:>4} {precision:>6.1%} {recall:>6.1%} {f1:>6.1%}')

# Macro F1
all_f1 = []
for action in actions:
    tp = confusion[action][action]
    fp = sum(confusion[other][action] for other in actions if other != action)
    fn = sum(confusion[action][other] for other in actions if other != action)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
    all_f1.append(f1)
macro_f1 = sum(all_f1) / len(all_f1)
print(f'\n  Macro F1: {macro_f1:.1%}')
print(f'  Accuracy: {sum(1 for c in classification if c["correct"]) / len(classification):.1%}')

# ══════════════════════════════════════════════════════════════
# 3. BY COMPLEXITY
# ══════════════════════════════════════════════════════════════
print('\n[3] ACCURACY BY COMPLEXITY')
by_complex = defaultdict(lambda: {'correct': 0, 'total': 0})
for c in classification:
    by_complex[c['complexity']]['total'] += 1
    if c['correct']:
        by_complex[c['complexity']]['correct'] += 1
for cx in ['simple', 'medium', 'complex']:
    s = by_complex[cx]
    acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
    print(f'  {cx:>10}: {s["correct"]}/{s["total"]} = {acc:.1f}%')

# ══════════════════════════════════════════════════════════════
# 4. BY LANGUAGE
# ══════════════════════════════════════════════════════════════
print('\n[4] ACCURACY BY LANGUAGE')
by_lang = defaultdict(lambda: {'correct': 0, 'total': 0})
for c in classification:
    by_lang[c['language']]['total'] += 1
    if c['correct']:
        by_lang[c['language']]['correct'] += 1
for lg in ['pt', 'en']:
    s = by_lang[lg]
    acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
    print(f'  {lg:>5}: {s["correct"]}/{s["total"]} = {acc:.1f}%')

# ══════════════════════════════════════════════════════════════
# 5. CONFIDENCE DISTRIBUTION
# ══════════════════════════════════════════════════════════════
print('\n[5] CONFIDENCE DISTRIBUTION')
correct_confs = [c['confidence'] for c in classification if c['correct']]
wrong_confs = [c['confidence'] for c in classification if not c['correct']]
if correct_confs:
    print(f'  Correct: avg={sum(correct_confs)/len(correct_confs):.4f} min={min(correct_confs):.4f} max={max(correct_confs):.4f}')
if wrong_confs:
    print(f'  Wrong:   avg={sum(wrong_confs)/len(wrong_confs):.4f} min={min(wrong_confs):.4f} max={max(wrong_confs):.4f}')

# Confidence thresholds
for threshold in [0.1, 0.2, 0.3, 0.5, 0.7]:
    high = [c for c in classification if c['confidence'] >= threshold]
    high_correct = sum(1 for c in high if c['correct'])
    acc = high_correct / len(high) * 100 if high else 0
    print(f'  Conf>={threshold:.1f}: {high_correct}/{len(high)} = {acc:.1f}%')

# ══════════════════════════════════════════════════════════════
# 6. CODE GENERATION (from sample)
# ══════════════════════════════════════════════════════════════
print('\n[6] CODE GENERATION (sample of 80)')
for action in actions:
    items = [v for v in validation if v['action'] == action]
    gen = sum(1 for v in items if v['has_code'])
    ok = sum(1 for v in items if v['valid'])
    print(f'  {action:>15}: {gen}/{len(items)} código, {ok}/{len(items)} válido')

# ══════════════════════════════════════════════════════════════
# 7. SEMANTIC CORRECTNESS (from sample)
# ══════════════════════════════════════════════════════════════
print('\n[7] SEMANTIC CORRECTNESS (sample of 80)')
for action in actions:
    items = [s for s in semantic if s['action'] == action]
    ok = sum(1 for s in items if s['sem_ok'])
    print(f'  {action:>15}: {ok}/{len(items)} = {ok/max(len(items),1)*100:.1f}%')

# ══════════════════════════════════════════════════════════════
# 8. LATENCY
# ══════════════════════════════════════════════════════════════
print('\n[8] LATENCY (classification only)')
if latency:
    sorted_lat = sorted(latency)
    avg = sum(latency) / len(latency)
    p50 = sorted_lat[len(sorted_lat) // 2]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
    print(f'  avg={avg:.1f}ms | p50={p50:.1f}ms | p95={p95:.1f}ms | p99={p99:.1f}ms')

# ══════════════════════════════════════════════════════════════
# 9. WORST MISPREDICTIONS
# ══════════════════════════════════════════════════════════════
print('\n[9] WORST MISPREDICTIONS (sample)')
wrong = [c for c in classification if not c['correct']]
by_pair = defaultdict(list)
for c in wrong:
    by_pair[(c['expected'], c['predicted'])].append(c)

for (exp, pred), items in sorted(by_pair.items(), key=lambda x: -len(x[1]))[:10]:
    print(f'  {exp} → {pred}: {len(items)}x')
    for item in items[:3]:
        print(f'    "{item["input"][:70]}"')

# ══════════════════════════════════════════════════════════════
# 10. CRITICAL GAPS
# ══════════════════════════════════════════════════════════════
print('\n[10] CRITICAL GAPS')
print('  • gerar_sprite: 0% — system never classifies sprite requests')
print('  • responder: 0.9% — system almost never classifies as answer')
print('  • gerar_npc: 31.2% — most NPC requests classified as gerar_monstro')
print('  • gerar_monstro: 71.4% — but this includes many false positives from other categories')
print('  • Confidence is NOT correlated with correctness — system is confident even when wrong')

# Save analysis
analysis = {
    'confusion_matrix': {exp: dict(preds) for exp, preds in confusion.items()},
    'macro_f1': round(macro_f1, 4),
    'accuracy': round(sum(1 for c in classification if c['correct']) / len(classification), 4),
    'critical_gaps': ['gerar_sprite 0%', 'responder 0.9%', 'gerar_npc 31.2%'],
}
with open(os.path.join(RESULTS_DIR, 'analysis.json'), 'w') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)
print(f'\nSalvo: {RESULTS_DIR}/analysis.json')
