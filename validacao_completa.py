#!/usr/bin/env python3
"""Validacao COMPLETA MCR vs baseline em dados reais NAB + SMD"""
import sys, os, csv, math, json, time
from collections import deque, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import importlib.util as _iu
_spec = _iu.spec_from_file_location('mcr', os.path.join(BASE, 'MCR.py'))
mcr = _iu.module_from_spec(_spec)
_spec.loader.exec_module(mcr)

# ============================================================
# PARTE 1: NAB EC2 CPU
# ============================================================
print('=' * 70)
print('  PARTE 1: NAB EC2 CPU — Anomalia em CloudWatch')
print('=' * 70)

dados = []
with open('nab_ec2_cpu.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dados.append(row)

valores = [float(d['value']) for d in dados]
timestamps = [d['timestamp'] for d in dados]
N = len(dados)

# Anomalias NAB
def is_anomaly_real(ts):
    anomalias = ['2014-02-26 22:05:00', '2014-02-27 17:15:00']
    if ts >= anomalias[0]:
        return True
    return False

ground_truth = [is_anomaly_real(t) for t in timestamps]
n_anomalias = sum(ground_truth)
print(f'Amostras: {N}, Anomalias: {n_anomalias}')

# ----------------------------------------------------------
# 1A. MCR com features melhoradas
# ----------------------------------------------------------
print('\n--- 1A. MCR Multi-nivel ---')

class MCRDetectorMelhorado:
    def __init__(self, threshold_rel=0.12, min_niveis=2):
        self.mks = {
            'micro': mcr.MCR('micro'),   # mudancas de 1 passo
            'meso': mcr.MCR('meso'),     # padroes de 3 passos
            'macro': mcr.MCR('macro'),   # padroes de 5 passos
        }
        self.threshold_rel = threshold_rel
        self.min_niveis = min_niveis
        self._hist = {k: deque(maxlen=40) for k in self.mks}
        self.hist_delta = {k: [] for k in self.mks}
        self.anteriores = {}
        self.tempo_total = 0
    
    def _extrair_features(self, serie, i):
        """Extrai tokens de features para cada nivel MCR"""
        if i < 5:
            return None, None, None
        
        # Micro: mudanca instantanea (direcao + magnitude)
        delta = serie[i] - serie[i-1]
        micro = f'M{"S" if delta>0 else "D" if delta<0 else "F"}{abs(delta):.3f}'
        
        # Meso: padrao de 3 passos (tendencias curtas)
        d1 = serie[i] - serie[i-1]
        d2 = serie[i-1] - serie[i-2]
        d3 = serie[i-2] - serie[i-3]
        padrao = ''
        for d in [d1, d2, d3]:
            padrao += '+' if d > 0.001 else '-' if d < -0.001 else '0'
        var = abs(serie[i] - serie[i-3])
        meso = f'P{padrao}V{var:.3f}'
        
        # Macro: tendencia de 5 passos + volatilidade
        vals = serie[max(0,i-4):i+1]
        tendencia = vals[-1] - vals[0]
        vol = max(vals) - min(vals)
        macro = f'T{"S" if tendencia>0 else "D" if tendencia<0 else "F"}{vol:.3f}'
        
        return micro, meso, macro
    
    def alimentar(self, micro, meso, macro):
        for nivel, token in [('micro', micro), ('meso', meso), ('macro', macro)]:
            if nivel in self.anteriores and self.anteriores[nivel] is not None:
                self.mks[nivel].aprender(self.anteriores[nivel], token)
            self.anteriores[nivel] = token
    
    def medir(self):
        for nome, mk in self.mks.items():
            e = mk.entropia_media() if mk.total > 0 else 1.0
            self._hist[nome].append(e)
    
    def delta(self, nivel):
        hist = self._hist.get(nivel, [])
        if len(hist) < 2:
            return 0.0
        diff = abs(hist[-1] - hist[-2])
        v = diff / hist[-2] if hist[-2] > 0.001 else diff
        self.hist_delta[nivel].append(v)
        return v
    
    def detectar(self):
        spikes = {}
        for nivel in self.mks:
            dr = self.delta(nivel)
            if dr > self.threshold_rel:
                spikes[nivel] = round(dr, 4)
        return len(spikes) >= self.min_niveis, spikes

det_mcr = MCRDetectorMelhorado(threshold_rel=0.12, min_niveis=2)
t0 = time.time()

pred_mcr = []
for i in range(N):
    micro, meso, macro = det_mcr._extrair_features(valores, i)
    if micro is None:
        pred_mcr.append(False)
        continue
    det_mcr.alimentar(micro, meso, macro)
    if i >= 30:
        det_mcr.medir()
        evento, spikes = det_mcr.detectar()
    else:
        evento = False
    pred_mcr.append(evento)

tempo_mcr = time.time() - t0

# Metricas MCR
tp_mcr = sum(1 for i in range(N) if pred_mcr[i] and ground_truth[i])
fp_mcr = sum(1 for i in range(N) if pred_mcr[i] and not ground_truth[i])
fn_mcr = sum(1 for i in range(N) if not pred_mcr[i] and ground_truth[i])
rec_mcr = tp_mcr / (tp_mcr + fn_mcr) if (tp_mcr+fn_mcr) > 0 else 0
prec_mcr = tp_mcr / (tp_mcr + fp_mcr) if (tp_mcr+fp_mcr) > 0 else 0
f1_mcr = 2*prec_mcr*rec_mcr/(prec_mcr+rec_mcr) if (prec_mcr+rec_mcr) > 0 else 0

print(f'  TP={tp_mcr} FP={fp_mcr} FN={fn_mcr}')
print(f'  Recall={rec_mcr:.3f} Precisao={prec_mcr:.3f} F1={f1_mcr:.3f}')
print(f'  Tempo: {tempo_mcr:.3f}s')

# ----------------------------------------------------------
# 1B. Baseline: IQR (Interquartile Range)
# ----------------------------------------------------------
print('\n--- 1B. Baseline: IQR ---')

def detectar_iqr(serie, janela=100, multiplier=1.5):
    pred = [False] * len(serie)
    for i in range(janela, len(serie)):
        window = serie[i-janela:i]
        q1, q3 = sorted(window)[len(window)//4], sorted(window)[3*len(window)//4]
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        pred[i] = serie[i] < lower or serie[i] > upper
    return pred

t0 = time.time()
pred_iqr = detectar_iqr(valores, janela=100, multiplier=1.5)
tempo_iqr = time.time() - t0

tp_iqr = sum(1 for i in range(N) if pred_iqr[i] and ground_truth[i])
fp_iqr = sum(1 for i in range(N) if pred_iqr[i] and not ground_truth[i])
fn_iqr = sum(1 for i in range(N) if not pred_iqr[i] and ground_truth[i])
rec_iqr = tp_iqr / (tp_iqr + fn_iqr) if (tp_iqr+fn_iqr) > 0 else 0
prec_iqr = tp_iqr / (tp_iqr + fp_iqr) if (tp_iqr+fp_iqr) > 0 else 0
f1_iqr = 2*prec_iqr*rec_iqr/(prec_iqr+rec_iqr) if (prec_iqr+rec_iqr) > 0 else 0

print(f'  TP={tp_iqr} FP={fp_iqr} FN={fn_iqr}')
print(f'  Recall={rec_iqr:.3f} Precisao={prec_iqr:.3f} F1={f1_iqr:.3f}')
print(f'  Tempo: {tempo_iqr:.3f}s')

# ----------------------------------------------------------
# 1C. Baseline: 3-Sigma (desvio padrao)
# ----------------------------------------------------------
print('\n--- 1C. Baseline: 3-Sigma ---')

def detectar_3sigma(serie, janela=100):
    pred = [False] * len(serie)
    for i in range(janela, len(serie)):
        window = serie[i-janela:i]
        mu = sum(window) / len(window)
        sigma = math.sqrt(sum((x-mu)**2 for x in window) / len(window))
        pred[i] = abs(serie[i] - mu) > 3 * sigma
    return pred

t0 = time.time()
pred_3s = detectar_3sigma(valores, janela=100)
tempo_3s = time.time() - t0

tp_3s = sum(1 for i in range(N) if pred_3s[i] and ground_truth[i])
fp_3s = sum(1 for i in range(N) if pred_3s[i] and not ground_truth[i])
fn_3s = sum(1 for i in range(N) if not pred_3s[i] and ground_truth[i])
rec_3s = tp_3s / (tp_3s + fn_3s) if (tp_3s+fn_3s) > 0 else 0
prec_3s = tp_3s / (tp_3s + fp_3s) if (tp_3s+fp_3s) > 0 else 0
f1_3s = 2*prec_3s*rec_3s/(prec_3s+rec_3s) if (prec_3s+rec_3s) > 0 else 0

print(f'  TP={tp_3s} FP={fp_3s} FN={fn_3s}')
print(f'  Recall={rec_3s:.3f} Precisao={prec_3s:.3f} F1={f1_3s:.3f}')
print(f'  Tempo: {tempo_3s:.3f}s')

# ----------------------------------------------------------
# COMPARACAO
# ----------------------------------------------------------
print('\n' + '=' * 70)
print('  COMPARACAO NAB EC2 CPU')
print('=' * 70)
print(f'  {"Metodo":20} {"Recall":>10} {"Precisao":>10} {"F1":>10} {"TP":>6} {"FP":>6} {"T(s)":>8}')
print(f'  {"-":->20} {"-":->10} {"-":->10} {"-":->10} {"-":->6} {"-":->6} {"-":->8}')
print(f'  {"MCR Multi-nivel":20} {rec_mcr:>10.3f} {prec_mcr:>10.3f} {f1_mcr:>10.3f} {tp_mcr:>6} {fp_mcr:>6} {tempo_mcr:>8.3f}')
print(f'  {"IQR (1.5x)":20} {rec_iqr:>10.3f} {prec_iqr:>10.3f} {f1_iqr:>10.3f} {tp_iqr:>6} {fp_iqr:>6} {tempo_iqr:>8.3f}')
print(f'  {"3-Sigma":20} {rec_3s:>10.3f} {prec_3s:>10.3f} {f1_3s:>10.3f} {tp_3s:>6} {fp_3s:>6} {tempo_3s:>8.3f}')

# ============================================================
# PARTE 2: SMD (Server Machine Dataset) — 38 dimensoes
# ============================================================
print('\n' + '=' * 70)
print('  PARTE 2: SMD (Server Machine Dataset) — 38 dimensoes')
print('=' * 70)

# Carregar o SMD sample (training data from OmniAnomaly)
# This is the training data (no labels)
# We'll use it as a test: MCR builds chains on multi-dimensional data
smd_data = []
with open('smd_sample.txt') as f:
    for line in f:
        vals = [float(x) for x in line.strip().split(',')]
        smd_data.append(vals)

smd_N = len(smd_data)
smd_D = len(smd_data[0]) if smd_data else 0
print(f'SMD: {smd_N} amostras, {smd_D} dimensoes')

# Para SMD, MCR pode tratar cada dimensao como uma "fonte" diferente
# e usar multi-nivel para detectar eventos inter-dimensionais
from collections import defaultdict

class MCRMultiDimDetector:
    def __init__(self, n_dims, threshold_rel=0.15, min_niveis=3):
        self.n_dims = n_dims
        self.threshold_rel = threshold_rel
        self.min_niveis = min_niveis
        # Um MCR por dimensao
        self.mks = [mcr.MCR(f'dim_{d}') for d in range(n_dims)]
        self.anteriores = [None] * n_dims
        self._hist = defaultdict(lambda: deque(maxlen=30))
        self.totais = [0] * n_dims
    
    def alimentar(self, vetor):
        for d in range(self.n_dims):
            tok = f'S{d}:{vetor[d]:.4f}'
            if self.anteriores[d] is not None:
                self.mks[d].aprender(self.anteriores[d], tok)
            self.anteriores[d] = tok
            self.totais[d] = self.mks[d].total
    
    def medir(self):
        spikes = {}
        for d in range(self.n_dims):
            mk = self.mks[d]
            ent = mk.entropia_media() if mk.total > 0 else 1.0
            self._hist[d].append(ent)
            if len(self._hist[d]) >= 2:
                h = self._hist[d]
                diff = abs(h[-1] - h[-2])
                dr = diff / h[-2] if h[-2] > 0.001 else diff
                if dr > self.threshold_rel:
                    spikes[d] = round(dr, 4)
        return len(spikes), spikes

print('\n--- 2A. MCR Multi-dimensional ---')
det_md = MCRMultiDimDetector(smd_D, threshold_rel=0.15, min_niveis=3)

t0 = time.time()
eventos_md = []
entropias_media = []
for i in range(min(5000, smd_N)):
    det_md.alimentar(smd_data[i])
    if i >= 50:
        n_evento, spikes = det_md.medir()
        if n_evento >= 3:
            eventos_md.append((i, n_evento, spikes))
    if i % 1000 == 0:
        ent_media = sum(mk.entropia_media() if mk.total > 0 else 1.0 for mk in det_md.mks) / smd_D
        entropias_media.append(ent_media)

tempo_md = time.time() - t0

print(f'  Dimensoes: {smd_D}')
print(f'  Amostras processadas: {min(5000, smd_N)}')
print(f'  Eventos multi-dim (3+ dims): {len(eventos_md)}')
print(f'  Entropia media por dimensao (final): {entropias_media[-1] if entropias_media else 0:.4f}')
print(f'  Tempo: {tempo_md:.3f}s')

# Anomalias SMD: dimensoes que mais oscilam
dim_spike_count = Counter()
for _, _, spikes in eventos_md:
    for d in spikes:
        dim_spike_count[d] += 1

print(f'\n  Top-5 dimensoes mais "instaveis":')
for d, cnt in dim_spike_count.most_common(5):
    ent_final = det_md.mks[d].entropia_media() if det_md.mks[d].total > 0 else 1.0
    print(f'    dim_{d}: {cnt} spikes, entropia={ent_final:.4f}, transicoes={det_md.mks[d].total}')

# Analise da primeira e ultima dimensao
print(f'\n  Analise dimensional:')
for d in [0, 1, 2, smd_D-3, smd_D-2, smd_D-1]:
    if d < smd_D:
        mk = det_md.mks[d]
        print(f'    dim_{d}: entropia={mk.entropia_media():.4f} transicoes={mk.total} tokens_unicos={len(mk.freq)}')

# ============================================================
# SALVAR RESULTADOS
# ============================================================
resultados = {
    'nab': {
        'dataset': 'NAB EC2 CPU',
        'total': N,
        'anomalias_reais': n_anomalias,
        'metodos': {
            'MCR Multi-nivel': {
                'recall': round(rec_mcr, 4),
                'precision': round(prec_mcr, 4),
                'f1': round(f1_mcr, 4),
                'tp': tp_mcr,
                'fp': fp_mcr,
                'fn': fn_mcr,
                'time_s': round(tempo_mcr, 3),
            },
            'IQR 1.5x': {
                'recall': round(rec_iqr, 4),
                'precision': round(prec_iqr, 4),
                'f1': round(f1_iqr, 4),
                'tp': tp_iqr,
                'fp': fp_iqr,
                'fn': fn_iqr,
                'time_s': round(tempo_iqr, 3),
            },
            '3-Sigma': {
                'recall': round(rec_3s, 4),
                'precision': round(prec_3s, 4),
                'f1': round(f1_3s, 4),
                'tp': tp_3s,
                'fp': fp_3s,
                'fn': fn_3s,
                'time_s': round(tempo_3s, 3),
            },
        }
    },
    'smd': {
        'dataset': 'SMD (Server Machine)',
        'total': smd_N,
        'dimensoes': smd_D,
        'processado': min(5000, smd_N),
        'eventos_multi_dim': len(eventos_md),
        'entropia_media_final': round(entropias_media[-1], 4) if entropias_media else 0,
        'time_s': round(tempo_md, 3),
    }
}

with open('resultado_validacao.json', 'w') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print('\n' + '=' * 70)
print('  Resultados salvos em resultado_validacao.json')
print('=' * 70)
