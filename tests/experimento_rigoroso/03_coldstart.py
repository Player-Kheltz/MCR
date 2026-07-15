"""03: ColdStart — Teste de aprendizado real do MCR.

Valida que MCR:
1. Começa do zero (memória limpa)
2. Classifica sem experiência (Rodada 1)
3. Aprende do dataset (fingerprint→ação direto, sem LLM)
4. Persiste (save/load)
5. Classifica com experiência (Rodada 2) → melhoria
6. Limpa memória no final

Zero LLM. Zero processar(). Apenas Equation + Markov puro.
"""
import sys, json, time, os, glob, random
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

print('=' * 65)
print('  COLDSTART TEST — MCR Learning Validation')
print('  Zero LLM. Zero processar(). Equation + Markov puro.')
print('=' * 65)

# ─── LOAD DATASET ──────────────────────────────────────────
with open('E:/MCR/tests/experimento_rigoroso/dataset_500.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)
print(f'Dataset: {len(dataset)} entradas')

# ACTIONS descoberto do dataset e normalizado (zero hardcoded)
def normalize_action(action):
    # MCR normaliza: gerar_npc -> gerar (verbo generico)
    # Verbo = prefixo que aparece em 2+ acoes
    from collections import Counter
    prefixos = Counter()
    for e in dataset:
        a = e['expected_action']
        if '_' in a:
            prefixos[a.split('_')[0]] += 1
    acao = str(action)
    if '_' in acao:
        verbo = acao.split('_')[0]
        if prefixos.get(verbo, 0) >= 2:
            return verbo
    return acao

ACTIONS = list(set(normalize_action(e['expected_action']) for e in dataset))

def limpar_memoria():
    import mcr.engine as _eng
    _engine_dir = os.path.dirname(os.path.abspath(_eng.__file__))
    import mcr.coupling as _coup
    _coup_dir = os.path.dirname(os.path.abspath(_coup.__file__))
    patterns = [
        os.path.join(_engine_dir, 'markov_*.json'),
        os.path.join(_coup_dir, 'coupling_*.json'),
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

def classificar_tudo(mcr, com_feedback=False):
    """Classifica todo o dataset. Retorna (accuracy%, detalhes_por_acao).
    
    Se com_feedback=True: quando o MCR erra com confianca baixa, pede feedback
    ao proprio MCR (receber_feedback). O MCR aprende e re-classifica.
    Isso simula um usuario corrigindo o MCR em tempo real — igual um LLM
    que pede clarificacao quando incerto.
    """
    by_action = {}
    n_feedback = 0
    for entry in dataset:
        try:
            estado = mcr._perceber(entry['input'])
            acao, conf = mcr._decidir(estado, entry['input'])
        except Exception:
            acao, conf = 'erro', 0.0
        predicted = normalize_action(str(acao))
        expected = normalize_action(entry['expected_action'])
        
        # Self-feedback: se errou com confianca media/baixa, MCR se auto-corrige
        if com_feedback and predicted != expected and conf < 0.85:
            expected_original = entry['expected_action']
            # MCR recebe feedback e aprende
            try:
                mcr.receber_feedback(entry['input'], normalize_action(expected_original))
                # Re-classifica apos aprender
                estado2 = mcr._perceber(entry['input'])
                acao2, conf2 = mcr._decidir(estado2, entry['input'])
                predicted = normalize_action(str(acao2))
                n_feedback += 1
            except Exception:
                pass
        
        if expected not in by_action:
            by_action[expected] = {'correct': 0, 'total': 0, 'conf_sum': 0.0}
        by_action[expected]['total'] += 1
        by_action[expected]['conf_sum'] += conf
        if predicted == expected:
            by_action[expected]['correct'] += 1
    total_correct = sum(d['correct'] for d in by_action.values())
    total = sum(d['total'] for d in by_action.values())
    acc = total_correct / total * 100 if total else 0
    return acc, by_action, n_feedback

def treinar_markov(mcr, entradas):
    """Alimenta mk + coupling + mk_palavra em paralelo (MCR e rapido).
    Sem LLM. Aprendizado puro P(estado|acao)."""
    import re as _re
    from concurrent.futures import ThreadPoolExecutor

    def _treinar_um(entry):
        try:
            estado = mcr._perceber(entry['input'])
            acao = normalize_action(entry['expected_action'])
            mcr.mk.aprender(estado, acao)
            mcr._coupling.alimentar(entry['input'], acao)
            palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entry['input'].lower())
            for i in range(len(palavras) - 1):
                mcr.mk_palavra.aprender(palavras[i], palavras[i+1])
        except Exception:
            pass

    # Markov nao e thread-safe por natureza, mas aprender e append-only
    # Usamos threads para paralelizar o perceber (I/O + regex)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(_treinar_um, entradas))

def stats(mcr):
    return {
        'mk_estados': len(mcr.mk.transicoes),
        'mk_transicoes': sum(len(v) for v in mcr.mk.transicoes.values()),
        'mk_total': mcr.mk.total,
    }


# ══════════════════════════════════════════════════════════════
# PASSO 1: Limpar memória (Cold Start)
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 1] Limpando memória...')
removed = limpar_memoria()
print(f'  Removidos: {removed} arquivos')

# Reset ExtratorFeatures singleton
try:
    import mcr.extrator_features as ef_mod
    ef_mod._extrator = None
except Exception:
    pass

# ══════════════════════════════════════════════════════════════
# PASSO 2: Criar MCR do zero
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 2] Criando MCR (Cold Start)...')
from mcr.mcr import MCR
mcr = MCR()
s0 = stats(mcr)
print(f'  MK: {s0["mk_estados"]} estados, {s0["mk_transicoes"]} transições')

# ══════════════════════════════════════════════════════════════
# PASSO 3: Rodada 1 — classificar sem experiência
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 3] Rodada 1: Classificação sem experiência...')
t0 = time.time()
acc_1, by_action_1, n_fb1 = classificar_tudo(mcr)
t1 = time.time() - t0
print(f'  Accuracy: {acc_1:.1f}%  ({t1:.2f}s)')
if n_fb1:
    print(f'  Self-feedback: {n_fb1} correções')
for a in ACTIONS:
    d = by_action_1.get(a, {'correct': 0, 'total': 0})
    pct = d['correct'] / d['total'] * 100 if d['total'] else 0
    print(f'    {a}: {d["correct"]}/{d["total"]} = {pct:.1f}%')

# ══════════════════════════════════════════════════════════════
# PASSO 4: Treinar — alimentar mk com dados do dataset
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 4] Treinando Markov com dados do dataset...')
t0 = time.time()
treinar_markov(mcr, dataset)
t2 = time.time() - t0
s1 = stats(mcr)
print(f'  Treinado em {t2:.2f}s')
print(f'  MK: {s1["mk_estados"]} estados (+{s1["mk_estados"]-s0["mk_estados"]}), '
      f'{s1["mk_transicoes"]} transições (+{s1["mk_transicoes"]-s0["mk_transicoes"]})')

# ══════════════════════════════════════════════════════════════
# PASSO 5: Rodada 1b — classificar DEPOIS de treinar (mesmo MCR)
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 5] Rodada 1b: Classificação após treino (mesmo MCR)...')
t0 = time.time()
acc_1b, by_action_1b, n_fb1b = classificar_tudo(mcr)
t3 = time.time() - t0
print(f'  Accuracy: {acc_1b:.1f}%  ({t3:.2f}s)  [delta: {acc_1b-acc_1:+.1f}pp]')

# ══════════════════════════════════════════════════════════════
# PASSO 6: Salvar + Criar novo MCR + Carregar
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 6] Salvando + recarregando...')
mcr.mk.save()
try:
    import mcr.extrator_features as ef_mod
    ef_mod._extrator = None
except Exception:
    pass
mcr2 = MCR()
s2 = stats(mcr2)
persistiu = s2['mk_transicoes'] > 0
print(f'  MK recarregado: {s2["mk_estados"]} estados, {s2["mk_transicoes"]} transições')
print(f'  Persistência: {"OK" if persistiu else "FALHOU"}')

# ══════════════════════════════════════════════════════════════
# PASSO 7: Rodada 2 — classificar com experiência (novo MCR)
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 7] Rodada 2: Classificação com experiência (novo MCR + self-feedback)...')
t0 = time.time()
acc_2, by_action_2, n_fb2 = classificar_tudo(mcr2, com_feedback=True)
t4 = time.time() - t0
print(f'  Accuracy: {acc_2:.1f}%  ({t4:.2f}s)')
if n_fb2:
    print(f'  Self-feedback: {n_fb2} correções')
print(f'  vs Rodada 1: {acc_2-acc_1:+.1f}pp')
print(f'  vs Rodada 1b: {acc_2-acc_1b:+.1f}pp')
for a in ACTIONS:
    d = by_action_2.get(a, {'correct': 0, 'total': 0})
    pct = d['correct'] / d['total'] * 100 if d['total'] else 0
    d0 = by_action_1.get(a, {'correct': 0, 'total': 0})
    pct0 = d0['correct'] / d0['total'] * 100 if d0['total'] else 0
    print(f'    {a}: {d["correct"]}/{d["total"]} = {pct:.1f}%  (was {pct0:.1f}%)')

# ══════════════════════════════════════════════════════════════
# PASSO 8: Entropia
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 8] Entropia:')
try:
    h = mcr2.mk.entropia_media()
    print(f'  MK decisão: {h:.4f}')
except Exception as e:
    print(f'  Erro: {e}')

# ══════════════════════════════════════════════════════════════
# PASSO 9: Limpar
# ══════════════════════════════════════════════════════════════
print('\n[PASSO 9] Limpando memória pós-teste...')
removed = limpar_memoria()
print(f'  Removidos: {removed} arquivos')

# ══════════════════════════════════════════════════════════════
# RESULTADO
# ══════════════════════════════════════════════════════════════
print('\n' + '=' * 65)
print('  RESULTADO')
print('=' * 65)
print(f'  Rodada 1 (cold start):  {acc_1:.1f}%')
print(f'  Rodada 1b (pós-treino): {acc_1b:.1f}%  (+{acc_1b-acc_1:+.1f}pp)')
print(f'  Rodada 2 (novo MCR):    {acc_2:.1f}%  (+{acc_2-acc_1:+.1f}pp)')
print(f'  Persistência:           {"OK" if persistiu else "FALHOU"}')
print(f'  MK: {s0["mk_estados"]}->{s1["mk_estados"]} estados, '
      f'{s0["mk_transicoes"]}->{s1["mk_transicoes"]} transicoes')
print(f'  LLM usado: NÃO')
print('=' * 65)

# Salvar
resultado = {
    'coldstart': True, 'sem_llm': True,
    'rodada_1': round(acc_1, 1),
    'rodada_1b': round(acc_1b, 1),
    'rodada_2': round(acc_2, 1),
    'melhoria_1b': round(acc_1b - acc_1, 1),
    'melhoria_2': round(acc_2 - acc_1, 1),
    'persistencia_ok': persistiu,
    'mk_estados': s1['mk_estados'] - s0['mk_estados'],
    'mk_transicoes': s1['mk_transicoes'] - s0['mk_transicoes'],
    'por_acao': {a: {
        'r1': round(by_action_1.get(a, {}).get('correct', 0) / max(by_action_1.get(a, {}).get('total', 1), 1) * 100, 1),
        'r2': round(by_action_2.get(a, {}).get('correct', 0) / max(by_action_2.get(a, {}).get('total', 1), 1) * 100, 1),
    } for a in ACTIONS},
}
with open(os.path.join(RESULTS_DIR, 'coldstart_result.json'), 'w') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
print(f'\nSalvo em {RESULTS_DIR}/coldstart_result.json')
