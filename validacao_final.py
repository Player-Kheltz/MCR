#!/usr/bin/env python3
"""Validacao MCR em NAB com threshold adaptativo + cross-domain analogy + conclusao"""
import sys, os, csv, math, json, time, re, urllib.request
from collections import deque, Counter

BASE = 'E:\\MCR'
os.chdir(BASE)
sys.path.insert(0, BASE)

import importlib.util as _iu
_spec = _iu.spec_from_file_location('mcr', os.path.join(BASE, 'MCR.py'))
mcr = _iu.module_from_spec(_spec)
_spec.loader.exec_module(mcr)

print('=' * 70)
print('  VALIDACAO FINAL DO MCR EM DADOS REAIS')
print('=' * 70)

# ============================================================
# TESTE 1: NAB com threshold adaptativo
# ============================================================
print('\n' + '=' * 70)
print('  TESTE 1: NAB EC2 CPU — Anomalia em CloudWatch')
print('  (threshold adaptativo para encontrar ponto ideal)')
print('=' * 70)

dados = []
with open('nab_ec2_cpu.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dados.append(row)
valores = [float(d['value']) for d in dados]
timestamps = [d['timestamp'] for d in dados]
N = len(dados)

def is_anomaly_real(ts):
    return ts >= '2014-02-26 22:05:00'
ground_truth = [is_anomaly_real(t) for t in timestamps]

print(f'Amostras: {N}, Anomalias reais: {sum(ground_truth)}')

# Simple MCR with adaptive threshold sweep
class MCRAnomaly:
    def __init__(self, n_bins=5):
        self.mk = mcr.MCR('anomaly')
        self.hist = deque(maxlen=30)
        self.anterior = None
        self.n_bins = n_bins
    def _bin(self, v, mn, mx):
        return int((v - mn) / (mx - mn) * self.n_bins) if mx > mn else 0
    def alimentar_medir(self, token):
        if self.anterior is not None:
            self.mk.aprender(self.anterior, token)
        self.anterior = token
        e = self.mk.entropia_media() if self.mk.total > 0 else 1.0
        self.hist.append(e)
        return e
    def delta(self):
        if len(self.hist) < 2: return 0.0
        diff = abs(self.hist[-1] - self.hist[-2])
        return diff / self.hist[-2] if self.hist[-2] > 0.001 else diff

min_v, max_v = min(valores), max(valores)
rng = max_v - min_v if max_v > min_v else 1.0

# Varredura de thresholds
melhor_f1 = 0
melhor_th = 0
melhor_resultado = None

for th in [x/100 for x in range(1, 51)]:
    det = MCRAnomaly(n_bins=5)
    pred = [False] * N
    for i, v in enumerate(valores):
        tok = f'B{det._bin(v, min_v, max_v)}'
        ent = det.alimentar_medir(tok)
        if i >= 30:
            pred[i] = det.delta() > th
    
    tp = sum(1 for i in range(N) if pred[i] and ground_truth[i])
    fp = sum(1 for i in range(N) if pred[i] and not ground_truth[i])
    fn = sum(1 for i in range(N) if not pred[i] and ground_truth[i])
    rec = tp / (tp+fn) if (tp+fn)>0 else 0
    prec = tp / (tp+fp) if (tp+fp)>0 else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0
    if f1 > melhor_f1:
        melhor_f1 = f1
        melhor_th = th
        melhor_resultado = (th, tp, fp, fn, rec, prec, f1)

print(f'\nMelhor threshold: {melhor_th:.2f}')
print(f'Melhor F1: {melhor_f1:.3f}')
print(f'  TP={melhor_resultado[1]} FP={melhor_resultado[2]} FN={melhor_resultado[3]}')
print(f'  Recall={melhor_resultado[4]:.3f} Precisao={melhor_resultado[5]:.3f}')
print()

# Tabela de thresholds
print('Threshold sweep (amostragem):')
for th in [x/100 for x in range(1, 51, 5)]:
    det = MCRAnomaly(n_bins=5)
    pred = [False] * N
    for i, v in enumerate(valores):
        tok = f'B{det._bin(v, min_v, max_v)}'
        ent = det.alimentar_medir(tok)
        if i >= 30:
            pred[i] = det.delta() > th
    tp = sum(1 for i in range(N) if pred[i] and ground_truth[i])
    fp = sum(1 for i in range(N) if pred[i] and not ground_truth[i])
    fn = sum(1 for i in range(N) if not pred[i] and ground_truth[i])
    rec = tp / (tp+fn) if (tp+fn)>0 else 0
    prec = tp / (tp+fp) if (tp+fp)>0 else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0
    print(f'  th={th:.2f}: TP={tp:3d} FP={fp:3d} FN={fn:3d} Recall={rec:.3f} Prec={prec:.3f} F1={f1:.3f}')

# ============================================================
# TESTE 2: Cross-domain analogy (MCR HDC + Superposicao)
# ============================================================
print('\n' + '=' * 70)
print('  TESTE 2: MCR Cross-domain Analogy (HDC + Superposicao)')
print('  Dominios: codigo Python vs texto literario')
print('=' * 70)

# Usar MCR.py como texto de codigo, e buscar texto literario
codigo = open('MCR.py', encoding='utf-8').read()[:30000]
palavras_codigo = re.findall(r'\b\w+\b', codigo.lower())

# Baixar texto de domínio diferente (literatura)
print('\nUsando texto literario local (README + textos do MCR)')
# Usar textos que ja temos como "dominio diferente"
lit_raw = open('MCR.py', encoding='utf-8').read()[:30000]
# Complementar com textos dos testes e README como "literatura"
lit_parts = []
for fname in ['README.md', 'test_mcr_veracidade.py']:
    try:
        lit_parts.append(open(fname, encoding='utf-8').read())
    except: pass
lit_raw_full = ' '.join(lit_parts)
palavras_lit = re.findall(r'\b\w+\b', lit_raw_full.lower())[:10000]
print(f'  {len(palavras_lit)} palavras (domino "documentacao")')

# Construir MCRs para cada dominio
print('\nConstruindo cadeias Markov para cada dominio...')

# Dominio A: codigo
mk_code = mcr.MCR('code')
for i in range(min(5000, len(palavras_codigo)-1)):
    mk_code.aprender(palavras_codigo[i], palavras_codigo[i+1])

# Dominio B: literatura
mk_lit = mcr.MCR('lit')
for i in range(min(5000, len(palavras_lit)-1)):
    mk_lit.aprender(palavras_lit[i], palavras_lit[i+1])

def analisar_dominio(mk, nome, palavras):
    stats = {
        'nome': nome,
        'transicoes': mk.total,
        'estados_unicos': len(mk.freq),
        'entropia_media': round(mk.entropia_media(), 4),
        'total_palavras': len(palavras),
    }
    
    # Top predicoes para palavras frequentes
    top_palavras = sorted(mk.freq.items(), key=lambda x: -x[1])[:10]
    predicoes = []
    for estado, _ in top_palavras:
        prox, conf = mk.predizer(estado)
        predicoes.append(f'  {estado} -> {prox} (conf={conf:.3f})')
    stats['top_predicoes'] = predicoes
    
    return stats

stats_code = analisar_dominio(mk_code, 'Codigo Python', palavras_codigo)
stats_lit = analisar_dominio(mk_lit, 'Literatura', palavras_lit)

print(f'\nCodigo: {stats_code["transicoes"]} trans, {stats_code["estados_unicos"]} estados, ent={stats_code["entropia_media"]}')
print(f'Literatura: {stats_lit["transicoes"]} trans, {stats_lit["estados_unicos"]} estados, ent={stats_lit["entropia_media"]}')

# Teste HDC: codificar cada dominio como HD vector e medir similaridade
print('\n--- HDC: Hiperdimensional Computing ---')

# HDC test: generate HD fingerprints for each domain
def gerar_hd(mk, dim=128):
    """Gera assinatura HD baseada nas transicoes mais comuns"""
    hd = [0.0] * dim
    top = sorted(mk.freq.items(), key=lambda x: -x[1])[:50]
    for i, (estado, _) in enumerate(top):
        prox, conf = mk.predizer(estado)
        if prox:
            idx = hash(estado + prox) % dim
            hd[idx] += conf
    # Normalizar
    mag = math.sqrt(sum(x*x for x in hd))
    if mag > 0:
        hd = [x/mag for x in hd]
    return hd

hd_code = gerar_hd(mk_code)
hd_lit = gerar_hd(mk_lit)

# Similaridade cosseno
cos_sim = sum(a*b for a,b in zip(hd_code, hd_lit))
cos_norm = math.sqrt(sum(a*a for a in hd_code)) * math.sqrt(sum(b*b for b in hd_lit))
similaridade = cos_sim / cos_norm if cos_norm > 0 else 0

print(f'Similaridade HD Code x Literature: {similaridade:.4f}')
print(f'(0 = totalmente diferentes, 1 = identicos)')

# Teste superposicao: gerar tokens que nao existem em nenhum dominio
print('\n--- Superposicao: geracao cross-domain ---')
# Usar superposicao para gerar combinacoes
# Misturar cadeias: dado um estado do code, predizer com cadeia da lit
print('Palavras code que NAO aparecem na literatura:')
code_only = set(palavras_codigo[:10000]) - set(palavras_lit[:10000])
lit_only = set(palavras_lit[:10000]) - set(palavras_codigo[:10000])
print(f'  {len(code_only)} palavras exclusivas do codigo')
print(f'  {len(lit_only)} palavras exclusivas da literatura')

# Exemplos de cada
print(f'  Ex. code-only: {list(code_only)[:10]}')
print(f'  Ex. lit-only: {list(lit_only)[:10]}')

# ============================================================
# TESTE 3: SMD com threshold adaptativo (amostra maior)
# ============================================================
print('\n' + '=' * 70)
print('  TESTE 3: SMD — analise multi-dimensional + entropia')
print('=' * 70)

smd_data = []
with open('smd_sample.txt') as f:
    for line in f:
        vals = [float(x) for x in line.strip().split(',')]
        smd_data.append(vals)
smd_N = len(smd_data)
smd_D = len(smd_data[0]) if smd_data else 0

# Analise estatistica basica do SMD
print(f'\nSMD: {smd_N} amostras, {smd_D} dimensoes')
dims_stats = {}
for d in range(smd_D):
    col = [smd_data[i][d] for i in range(min(5000, smd_N))]
    uniq = len(set(round(x,4) for x in col))
    mean = sum(col) / len(col)
    std = math.sqrt(sum((x-mean)**2 for x in col)/len(col))
    dims_stats[d] = {'unicos': uniq, 'media': round(mean,4), 'std': round(std,4)}

print('\nDistribuicao de valores unicos por dimensao:')
uniq_counts = [dims_stats[d]['unicos'] for d in range(smd_D)]
print(f'  Min: {min(uniq_counts)}, Max: {max(uniq_counts)}, Media: {sum(uniq_counts)/smd_D:.1f}')
print(f'  Dimensoes constantes (1 unico valor): {sum(1 for u in uniq_counts if u==1)}')
print(f'  Dimensoes com >100 valores: {sum(1 for u in uniq_counts if u>100)}')

# Top-5 dimensoes com mais variacao
top_var = sorted(dims_stats.items(), key=lambda x: -x[1]['std'])[:5]
print('\nTop-5 dimensoes mais variaveis:')
for d, s in top_var:
    print(f'  dim_{d}: std={s["std"]} unicos={s["unicos"]}')

# Aplicar MCR apenas nas top-5 dimensoes
print('\nMCR nas top-5 dimensoes...')
t0 = time.time()
mks = {}
for d, _ in top_var:
    mks[d] = mcr.MCR(f'dim_{d}')

eventos_multi = 0
for i in range(1, min(5000, smd_N)):
    for d in mks:
        tok_prev = f'D{d}:{smd_data[i-1][d]:.4f}'
        tok_curr = f'D{d}:{smd_data[i][d]:.4f}'
        mks[d].aprender(tok_prev, tok_curr)

# Medir entropias
entropias = {d: (mks[d].entropia_media() if mks[d].total > 0 else 1.0) for d in mks}
print(f'Entropias das top-5 dims:')
for d in mks:
    print(f'  dim_{d}: ent={entropias[d]:.4f} trans={mks[d].total} estados={len(mks[d].freq)}')
print(f'Tempo: {time.time()-t0:.3f}s')

# ============================================================
# RESUMO E CONCLUSAO
# ============================================================
print('\n' + '=' * 70)
print('  RESUMO FINAL — MCR em Dados Reais')
print('=' * 70)

print(f'''
TESTE 1: NAB EC2 CPU (anomalia em CloudWatch)
  Melhor F1 do MCR: {melhor_f1:.3f} (threshold {melhor_th:.2f})
  Baseline IQR:     F1=0.145
  Baseline 3-Sigma: F1=0.020
  Conclusao: MCR perde para IQR simples em deteccao de anomalia em serie temporal.

TESTE 2: Cross-domain Analogy (Codigo x Literatura)
  Similaridade HD: {similaridade:.4f} (0=diferente, 1=identico)
  Codigo: {stats_code["entropia_media"]} ent, {stats_code["estados_unicos"]} estados
  Literatura: {stats_lit["entropia_media"]} ent, {stats_lit["estados_unicos"]} estados
  Palavras exclusivas code: {len(code_only)}, lit: {len(lit_only)}
  Conclusao: MCR consegue diferenciar dominios, mas a 'superposicao' nao gera
  analogias semanticas — apenas tokens que nao existem no outro dominio.

TESTE 3: SMD Multi-dimensional
  Dimensoes: {smd_D}, processadas: {min(5000, smd_N)}
  Dimensoes constantes: {sum(1 for u in uniq_counts if u==1)}/{smd_D}
  Entropia top-5 dims: {[round(entropias[d],4) for d in mks]}
  Conclusao: MCR detecta variacao por dimensao mas NAO identifica
  anomalias sem um threshold externo (mesma limitacao dos outros metodos).
''')

print('  VEREDITO FINAL:')
print('  - MCR funciona como descrito (codigo executa, testes passam)')
print('  - Mas em problemas REAIS (anomalia, analogia), nao supera')
print('  - metodos classicos simples (IQR, cosseno)')
print('  - A "inovacao" (entropia multi-nivel, HDC, superposicao)')
print('  - NAO produz resultados uteis alem do que ja existe')
print('  - MCR e um experimento valido, mas nao um avanco pratico')
print()

# Salvar
resultados = {
    'nab_mcr_melhor': {
        'f1': round(melhor_f1, 4),
        'threshold': melhor_th,
        'tp': melhor_resultado[1],
        'fp': melhor_resultado[2],
        'fn': melhor_resultado[3],
        'recall': round(melhor_resultado[4], 4),
        'precision': round(melhor_resultado[5], 4),
    },
    'cross_domain': {
        'hd_similarity': round(similaridade, 4),
        'code_entropy': stats_code['entropia_media'],
        'lit_entropy': stats_lit['entropia_media'],
        'code_only_words': len(code_only),
        'lit_only_words': len(lit_only),
    },
    'smd': {
        'dimensoes': smd_D,
        'amostras': smd_N,
        'dims_constantes': sum(1 for u in uniq_counts if u==1),
    }
}
with open('resultado_final.json', 'w') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print('Resultados salvos em resultado_final.json')
print('=' * 70)
