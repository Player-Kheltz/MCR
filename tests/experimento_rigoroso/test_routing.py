# -*- coding: utf-8 -*-
"""Quick diagnostic: 10 sample inputs through _perceber + _decidir."""
import sys, json, re
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR

mcr = MCR()

from mcr.extrator_features import get_extrator
ext = get_extrator()

print('=' * 70)
print('  EXTRATOR FEATURES DIAGNOSTIC')
print('=' * 70)
print('  Clusters: {}'.format(len(ext._clusters)))
print('  Token->Cluster mappings: {}'.format(len(ext._token_para_cluster)))
print('  Significant positions: {}'.format(ext._posicoes_significativas))
print()

for cid, info in sorted(ext._clusters.items()):
    anchors = info.get('ancoras', [])
    anchor_parts = []
    for a in anchors[:5]:
        if isinstance(a, tuple):
            anchor_parts.append('{}({:.2f})'.format(a[0], a[1]))
        else:
            anchor_parts.append(str(a))
    anchor_str = ', '.join(anchor_parts)
    print('  C{} [{}] {} | anchors: {}'.format(cid, info['nivel'], info.get('nome','?')[:50], anchor_str))

print()
print('=' * 70)
print('  MARKOV ENGINE STATE')
print('=' * 70)
stats = mcr.mk.stats()
print('  States: {}'.format(stats['estados']))
print('  Transitions: {}'.format(stats['transicoes']))
print('  Avg entropy: {}'.format(stats['entropia']))
print()

print('  Learned transitions (state -> action:count):')
for state in sorted(mcr.mk.transicoes.keys()):
    targets = mcr.mk.transicoes[state]
    target_str = ', '.join('{}:{}'.format(a, c) for a, c in sorted(targets.items(), key=lambda x: -x[1]))
    print('    {}'.format(state[:80]))
    print('      -> {}'.format(target_str))

print()
print('=' * 70)
print('  TEST INPUTS')
print('=' * 70)

test_inputs = [
    'crie um npc ferreiro',
    'gere um monstro dragao',
    'crie uma quest',
    'crie um sprite de espada',
    'o que e markov',
    'Crie um NPC alquimista que vende varinhas',
    'gere um NPC orc',
    'Generate a behemoth monster',
    'arco encantado',
    'Como funciona a equacao MCR',
]

for entrada in test_inputs:
    estado = mcr._perceber(entrada)
    acao, conf = mcr._decidir(estado)
    tokens = re.findall(r'[a-z\xe0-\xff0-9]{2,}', entrada.lower().strip())

    assignments = []
    for i, tok in enumerate(tokens[:8]):
        cid = ext._token_para_cluster.get(tok)
        if cid is not None:
            assignments.append('{}'.format(tok))
        else:
            assignments.append('{}->?'.format(tok))

    print('')
    print('  INPUT: "{}"'.format(entrada))
    print('    Tokens: {}'.format(tokens[:8]))
    print('    STATE: {}'.format(estado))
    print('    PREDICTED: {} (confidence: {:.4f})'.format(acao, conf))
    exists = estado in mcr.mk.transicoes
    print('    State in Markov table: {}'.format(exists))

print()
print('=' * 70)
print('  CONFUSION ANALYSIS')
print('=' * 70)

with open('E:/MCR/tests/experimento_rigoroso/results/analysis.json', 'r') as f:
    analysis = json.load(f)

cm = analysis['confusion_matrix']
for expected in sorted(cm.keys()):
    predictions = cm[expected]
    total = sum(predictions.values())
    print('')
    print('  Expected {} ({} samples):'.format(expected, total))
    for pred in sorted(predictions.keys(), key=lambda x: -predictions[x]):
        count = predictions[pred]
        pct = count / total * 100 if total > 0 else 0
        marker = ' <-- correct' if pred == expected else ''
        print('    -> {:20s}: {:3d} ({:5.1f}%){}'.format(pred, count, pct, marker))

print()
print('=' * 70)
print('  LOW CONFIDENCE FALLBACK ANALYSIS')
print('=' * 70)

with open('E:/MCR/tests/experimento_rigoroso/results/classification_results.json', 'r') as f:
    classification = json.load(f)

low_conf = [c for c in classification if c['confidence'] <= 0.1]
low_conf_correct = sum(1 for c in low_conf if c['correct'])
print('  Low-confidence predictions (<=0.1): {} / {}'.format(len(low_conf), len(classification)))
print('  Low-confidence correct: {}'.format(low_conf_correct))

low_conf_by_expected = {}
for c in low_conf:
    ea = c['expected']
    if ea not in low_conf_by_expected:
        low_conf_by_expected[ea] = 0
    low_conf_by_expected[ea] += 1
print('  Low-confidence by expected action:')
for a, cnt in sorted(low_conf_by_expected.items(), key=lambda x: -x[1]):
    print('    {}: {}'.format(a, cnt))

print()
print('  All low-conf predicted as: gerar_npc (the hardcoded fallback)')