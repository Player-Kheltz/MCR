"""PASSO 2: Experimento comparativo — 3 fórmulas × 50 execuções."""
import sys, json, math, time
from collections import Counter

sys.path.insert(0, 'E:/MCR')
from mcr.paths import CACHE_DIR
from mcr.mcr import MCR

# Carrega dados
path = CACHE_DIR / 'mcr_execucoes.json'
with open(path, 'r', encoding='utf-8') as f:
    execucoes = json.load(f)

print('=' * 65)
print('  EXPERIMENTO COMPARATIVO — 3 FÓRMULAS × 50 AMOSTRAS')
print('=' * 65)
print(f'  Dados: {len(execucoes)} execuções carregadas')

# ─── FÓRMULA A: Atual (baseline) ───────────────────────────
def formula_atual(ex):
    """Equação atual: Jaccard + len/2000 + entropia, divisor 10."""
    entrada = ex.get('entrada', ex.get('estado', ''))
    saida = ex.get('codigo', '')
    # Divergência via fingerprint 8D
    from devia.kernel.mcr_kernel.signature import MCRFingerprint
    fp_e = MCRFingerprint.gerar(entrada) if entrada else [0]*8
    fp_s = MCRFingerprint.gerar(saida) if saida else [0]*8
    div = sum(abs(a-b)/10.0 for a,b in zip(fp_e, fp_s)) / max(len(fp_e),1)
    esp = min(1.0, len(saida) / 2000.0)
    prof = 0.0
    if saida:
        freq = Counter(saida)
        total = len(saida)
        h = -sum((c/total)*math.log2(c/total) for c in freq.values() if c>0)
        h_max = math.log2(max(len(freq), 2))
        prof = h / h_max if h_max > 0 else 0.0
    return (div*2 + esp*3 + prof*2) / 10.0  # bug: divisor 10, pesos 7

# ─── FÓRMULA B: Linear 4D ──────────────────────────────────
def formula_linear_4d(ex):
    """4 dimensões orgânicas, linear, divisor = soma dos pesos."""
    checks_raw = ex.get('checks', '[]')
    try: checks = json.loads(checks_raw)
    except: checks = []
    confianca = float(ex.get('confianca', 0.1))
    completude = sum(1 for c in checks if ':OK' in str(c)) / max(len(checks), 1)
    saida = ex.get('codigo', '')
    freq = Counter(saida) if saida else Counter()
    total = len(saida) if saida else 1
    h_out = -sum((c/total)*math.log2(c/total) for c in freq.values() if c>0)
    h_max = math.log2(max(len(freq), 2))
    informacao = h_out / h_max if h_max > 0 else 0.0
    # Entropia do Markov (usando confiança como proxy — quanto mais confiante, menos entropia)
    consistencia = confianca  # proxy: confiança alta = consistência alta
    pesos = {'certeza': 3, 'completude': 3, 'informacao': 2, 'consistencia': 2}
    d = {'certeza': confianca, 'completude': completude,
         'informacao': informacao, 'consistencia': consistencia}
    return sum(pesos[k]*d[k] for k in pesos) / sum(pesos.values())

# ─── FÓRMULA C: Sigmoide 5D ─────────────────────────────────
def formula_sigmoide_5d(ex):
    """5 dimensões + sigmoide + gaussiana. Parâmetros fixos (cold start)."""
    checks_raw = ex.get('checks', '[]')
    try: checks = json.loads(checks_raw)
    except: checks = []
    confianca = float(ex.get('confianca', 0.1))
    completude = sum(1 for c in checks if ':OK' in str(c)) / max(len(checks), 1)
    saida = ex.get('codigo', '')
    freq = Counter(saida) if saida else Counter()
    total = len(saida) if saida else 1
    h_out = -sum((c/total)*math.log2(c/total) for c in freq.values() if c>0)
    h_max_out = math.log2(max(len(freq), 2))
    informacao = h_out / h_max_out if h_max_out > 0 else 0.0
    # Gaussiana de estabilidade (proxy: confiança como H_M)
    h_m = 1.0 - confianca  # confiança alta → entropia baixa
    H_opt, sigma = 0.5, 0.2
    estabilidade = math.exp(-((h_m - H_opt) / sigma)**2)
    eficiencia = 1.0 / math.log2(2)  # 1 tool = eficiência 1.0
    d = {'certeza': confianca, 'completude': completude,
         'informacao': informacao, 'estabilidade': estabilidade,
         'eficiencia': eficiencia}
    pesos_sig = {'certeza': 3, 'completude': 3, 'informacao': 2,
                 'estabilidade': 2, 'eficiencia': 1}
    soma = sum(pesos_sig[k]*d[k] for k in d) / sum(pesos_sig.values())
    theta, tau = 3.0, 0.4
    return 1.0 / (1.0 + math.exp(-theta * (soma - tau)))

# ─── CALCULAR NOTAS ────────────────────────────────────────
notas_a, notas_b, notas_c = [], [], []
sucessos = []

for ex in execucoes:
    na = formula_atual(ex)
    nb = formula_linear_4d(ex)
    nc = formula_sigmoide_5d(ex)
    notas_a.append(na)
    notas_b.append(nb)
    notas_c.append(nc)
    sucessos.append(int(ex.get('sucesso', 0)))

# ─── ESTATÍSTICAS ──────────────────────────────────────────
def stats(notas, nome):
    s = sum(notas)/len(notas)
    mn = min(notas)
    mx = max(notas)
    spread = mx - mn
    print(f'\n  {nome}:')
    print(f'    Média={s:.4f}  Min={mn:.4f}  Max={mx:.4f}  Spread={spread:.4f}')

    # Distribuição
    bins = {f'{i/10:.1f}-{(i+1)/10:.1f}': 0 for i in range(10)}
    for n in notas:
        b = min(9, int(n * 10))
        k = f'{b/10:.1f}-{(b+1)/10:.1f}'
        bins[k] = bins.get(k, 0) + 1
    # Mostra só bins com dados
    for k, v in bins.items():
        if v > 0:
            bar = '#' * v
            print(f'    {k}: {v:2d} {bar}')

    # Correlação com sucesso
    tp = fp = tn = fn = 0
    threshold = 0.5
    for n, suc in zip(notas, sucessos):
        pred = 1 if n >= threshold else 0
        if pred == 1 and suc == 1: tp += 1
        elif pred == 1 and suc == 0: fp += 1
        elif pred == 0 and suc == 0: tn += 1
        elif pred == 0 and suc == 1: fn += 1
    # MCC
    denom = math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))
    mcc = ((tp*tn) - (fp*fn)) / denom if denom > 0 else 0.0
    acc = (tp+tn)/len(notas) if len(notas) > 0 else 0.0
    print(f'    Threshold={threshold}: TP={tp} FP={fp} TN={tn} FN={fn}')
    print(f'    Acurácia={acc:.3f}  MCC={mcc:.3f}')
    return mcc

print('\n' + '-' * 45)
mcc_a = stats(notas_a, 'A) EQUAÇÃO ATUAL (Jaccard+len/2000, div 10)')
mcc_b = stats(notas_b, 'B) LINEAR 4D (métricas orgânicas)')
mcc_c = stats(notas_c, 'C) SIGMOIDE 5D + GAUSSIANA')

print(f'\n{"="*65}')
print(f'  RESULTADO FINAL')
print(f'{"="*65}')
print(f'  MCC Atual:    {mcc_a:+.3f}')
print(f'  MCC Linear 4D: {mcc_b:+.3f}')
print(f'  MCC Sigmoide:  {mcc_c:+.3f}')
melhor = max((mcc_a, 'A - Atual'), (mcc_b, 'B - Linear 4D'), (mcc_c, 'C - Sigmoide 5D'))
print(f'\n  VENCEDOR: {melhor[1]} (MCC={melhor[0]:.3f})')
print(f'{"="*65}')
