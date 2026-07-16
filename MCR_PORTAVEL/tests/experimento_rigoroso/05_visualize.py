"""05: Visualizacao dos resultados do experimento."""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'

# Load all results
with open(os.path.join(RESULTS_DIR, 'classification_results.json'), 'r') as f:
    classification = json.load(f)
with open(os.path.join(RESULTS_DIR, 'analysis.json'), 'r') as f:
    analysis = json.load(f)

print('=' * 70)
print('  VISUALIZACAO DOS RESULTADOS')
print('=' * 70)

# ══════════════════════════════════════════════════════════════
# CONFUSION MATRIX HEATMAP (ASCII)
# ══════════════════════════════════════════════════════════════
print('\n  CONFUSION MATRIX (ASCII Heatmap)')
print('  ' + '-' * 65)

actions = ['gerar_npc', 'gerar_monstro', 'responder', 'gerar_sprite']
cm = analysis['confusion_matrix']

# Find max for normalization
max_val = max(max(v.values()) for v in cm.values())

print(f'  {"":>15} {"gerar_npc":>12} {"gerar_monstro":>14} {"responder":>12} {"gerar_sprite":>14}')
for exp in actions:
    row = f'  {exp:>15} '
    for pred in actions:
        val = cm.get(exp, {}).get(pred, 0)
        # Heat: * = correct, x = high error
        if exp == pred:
            block = f'[{val:>5}*]'
        elif val > max_val * 0.3:
            block = f'[{val:>5}x]'
        elif val > 0:
            block = f'[{val:>5} ]'
        else:
            block = f'[     ]'
        row += block + ' '
    print(row)

# ══════════════════════════════════════════════════════════════
# CLASSIFICATION BAR CHART
# ══════════════════════════════════════════════════════════════
print('\n  ACCURACY BY ACTION')
print('  ' + '-' * 50)

from collections import defaultdict
by_action = defaultdict(lambda: {'correct': 0, 'total': 0})
for c in classification:
    by_action[c['expected']]['total'] += 1
    if c['correct']:
        by_action[c['expected']]['correct'] += 1

for action in actions:
    s = by_action[action]
    acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
    bar_len = int(acc / 2)
    bar = '#' * bar_len + '.' * (50 - bar_len)
    print(f'  {action:>15} |{bar[:50]}| {acc:5.1f}% ({s["correct"]}/{s["total"]})')

# ══════════════════════════════════════════════════════════════
# ACCURACY BY COMPLEXITY
# ══════════════════════════════════════════════════════════════
print('\n  ACCURACY BY COMPLEXITY')
print('  ' + '-' * 50)

by_complex = defaultdict(lambda: {'correct': 0, 'total': 0})
for c in classification:
    by_complex[c['complexity']]['total'] += 1
    if c['correct']:
        by_complex[c['complexity']]['correct'] += 1

for cx in ['simple', 'medium', 'complex']:
    s = by_complex[cx]
    acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
    bar_len = int(acc / 2)
    bar = '#' * bar_len + '.' * (50 - bar_len)
    print(f'  {cx:>10} |{bar[:50]}| {acc:5.1f}% ({s["correct"]}/{s["total"]})')

# ══════════════════════════════════════════════════════════════
# CONFIDENCE VS CORRECTNESS
# ══════════════════════════════════════════════════════════════
print('\n  CONFIDENCE vs CORRECTNESS')
print('  ' + '-' * 50)

bins = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.01)]
for lo, hi in bins:
    in_bin = [c for c in classification if lo <= c['confidence'] < hi]
    correct = sum(1 for c in in_bin if c['correct'])
    acc = correct / len(in_bin) * 100 if in_bin else 0
    bar_len = int(acc / 2)
    bar = '#' * bar_len + '.' * (50 - bar_len)
    print(f'  [{lo:.1f}-{hi:.1f}) |{bar[:50]}| {acc:5.1f}% ({len(in_bin):>3} samples)')

# ══════════════════════════════════════════════════════════════
# TOP MISCLASSIFICATIONS
# ══════════════════════════════════════════════════════════════
print('\n  TOP MISCLASSIFICATIONS')
print('  ' + '-' * 65)

from collections import Counter
wrong = [c for c in classification if not c['correct']]
pairs = Counter((c['expected'], c['predicted']) for c in wrong)
for (exp, pred), count in pairs.most_common(6):
    print(f'  {exp:>15} -> {pred:<15}: {count:>3}x')

print('\n' + '=' * 70)
print('  VEREDITO HONESTO')
print('=' * 70)
print('  Classification: 33.3% (Macro F1: 20.2%) -- NOT USABLE')
print('  Code generation: 92.5% -- GOOD (when action is correct)')
print('  Semantic: 45.0% -- NEEDS WORK')
print('  Latency: 0.3ms -- EXCELLENT')
print('  ')
print('  ROOT CAUSE: Markov engine has 6 transitions, 0 history.')
print('  It was never trained on actual user inputs.')
print('  The system defaults to gerar_monstro (5 transitions)')
print('  because it has the most training data.')
