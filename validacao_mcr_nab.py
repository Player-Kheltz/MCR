#!/usr/bin/env python3
"""Validacao MCR em dados reais NAB (Numenta Anomaly Benchmark)"""
import sys, os, csv, math, json, time
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

sys.path.insert(0, BASE)
import importlib.util as _iu
_spec = _iu.spec_from_file_location('mcr', os.path.join(BASE, 'MCR.py'))
mcr = _iu.module_from_spec(_spec)
_spec.loader.exec_module(mcr)

# 1. CARREGAR NAB
dados = []
with open('nab_ec2_cpu.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dados.append(row)

valores = [float(d['value']) for d in dados]
timestamps = [d['timestamp'] for d in dados]
N = len(dados)

# Label real: True se for anomalia
def is_anomaly(ts):
    for w in ['2014-02-26 22:05:00', '2014-02-27 17:15:00']:
        if ts >= w:
            return True
    return False

# Discretizacao
N_BINS = 20
min_v, max_v = min(valores), max(valores)
rng = max_v - min_v if max_v > min_v else 1.0

def discretizar(v):
    bi = min(N_BINS-1, int((v - min_v) / rng * N_BINS))
    return f'C{bi:02d}'

class MCRAnomalyDetector:
    def __init__(self, janela=30, threshold_rel=0.08, min_niveis=2):
        self.mk_byte = mcr.MCR('byte')
        self.mk_pal = mcr.MCR('palavra')
        self.mk_tven = mcr.MCR('tven')
        self.janela = janela
        self.threshold_rel = threshold_rel
        self.min_niveis = min_niveis
        self._hist = {'byte': deque(maxlen=janela),
                      'palavra': deque(maxlen=janela),
                      'tven': deque(maxlen=janela)}
        self.historico_delta = {'byte': [], 'palavra': [], 'tven': []}
        self.estado_anterior_byte = None
        self.estado_anterior_pal = None
        self.estado_anterior_tven = None
    
    def alimentar(self, estado_byte, estado_pal='', estado_tven=''):
        if self.estado_anterior_byte is not None:
            self.mk_byte.aprender(self.estado_anterior_byte, estado_byte)
        self.estado_anterior_byte = estado_byte
        if estado_pal and self.estado_anterior_pal is not None:
            self.mk_pal.aprender(self.estado_anterior_pal, estado_pal)
        if estado_pal:
            self.estado_anterior_pal = estado_pal
        if estado_tven and self.estado_anterior_tven is not None:
            self.mk_tven.aprender(self.estado_anterior_tven, estado_tven)
        if estado_tven:
            self.estado_anterior_tven = estado_tven
    
    def medir(self):
        for nome, mk in [('byte', self.mk_byte), ('palavra', self.mk_pal), ('tven', self.mk_tven)]:
            e = mk.entropia_media() if mk.total > 0 else 1.0
            self._hist[nome].append(e)
    
    def delta(self, nivel):
        hist = self._hist.get(nivel, [])
        if len(hist) < 2:
            return 0.0
        diff = abs(hist[-1] - hist[-2])
        return diff / hist[-2] if hist[-2] > 0.001 else diff
    
    def detectar(self):
        spikes = {}
        for nivel in ['byte', 'palavra', 'tven']:
            dr = self.delta(nivel)
            self.historico_delta[nivel].append(dr)
            if dr > self.threshold_rel:
                spikes[nivel] = round(dr, 4)
        evento = len(spikes) >= self.min_niveis
        return evento, spikes

# 4. EXECUTAR
print('='*70)
print('  VALIDACAO MCR: NAB EC2 CPU (anomalia AWS CloudWatch)')
print('='*70)

detector = MCRAnomalyDetector(janela=30, threshold_rel=0.08, min_niveis=2)

anomalias_mcr = []
anomalias_reais = []
deltas_todos = []
fp_idx = []
tp_idx = []

print(f'Alimentando {N} amostras...')
t0 = time.time()

for i in range(N):
    v = valores[i]
    estado_byte = discretizar(v)
    
    if i > 0:
        diff_val = v - valores[i-1]
        diff_bin = 1 if abs(diff_val) > rng/N_BINS else 0
        estado_pal = f'{estado_byte}_{diff_bin}'
        if i > 1:
            estado_tven = f'{estado_byte}_{diff_bin}_{1 if abs(valores[i-1]-valores[i-2])>rng/N_BINS else 0}'
        else:
            estado_tven = estado_pal
    else:
        estado_pal = estado_byte
        estado_tven = estado_byte
    
    detector.alimentar(estado_byte, estado_pal, estado_tven)
    
    if i >= 10:
        detector.medir()
        evento, spikes = detector.detectar()
        
        is_real = is_anomaly(timestamps[i])
        if is_real:
            anomalias_reais.append(i)
        
        if evento:
            anomalias_mcr.append(i)
            if is_real:
                tp_idx.append(i)
            else:
                fp_idx.append(i)
        
        deltas_todos.append({
            'idx': i,
            'ts': timestamps[i],
            'byte': detector.historico_delta['byte'][-1],
            'palavra': detector.historico_delta['palavra'][-1],
            'tven': detector.historico_delta['tven'][-1],
            'evento': evento,
            'real': is_real,
            'valor': v
        })

tempo = time.time() - t0

# 5. METRICAS
print(f'Tempo: {tempo:.3f}s')
print(f'Amostras: {N}')
print(f'Anomalias reais: {len(anomalias_reais)} pontos')
print(f'Deteccoes MCR: {len(anomalias_mcr)}')

# TP no sentido de janela: acertou alguma deteccao dentro do periodo anomalo?
# Como NAB define janelas, vamos ver quantas deteccoes MCR caem nas janelas
tp = len(tp_idx)
fp = len(fp_idx)

# Recall: pontos reais que tiveram pelo menos uma deteccao
reais_detectados = len(set(anomalias_reais) & set(anomalias_mcr))
recall = reais_detectados / len(anomalias_reais) if anomalias_reais else 0
precisao = tp / (tp + fp) if (tp + fp) > 0 else 0
f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) > 0 else 0

print()
print('=== METRICAS ===')
print(f'  Recall (taxa de acerto em pontos anomalos): {recall:.3f} ({reais_detectados}/{len(anomalias_reais)})')
print(f'  Precisao (TP/(TP+FP)): {precisao:.3f} ({tp}/{tp+fp})')
print(f'  F1: {f1:.3f}')

# Eventos mais fortes
print()
print('=== TOP 10 EVENTOS MCR (maior delta soma) ===')
sorted_deltas = sorted(deltas_todos, key=lambda x: x['byte']+x['palavra']+x['tven'], reverse=True)
for d in sorted_deltas[:10]:
    soma = d['byte']+d['palavra']+d['tven']
    print(f'  idx={d["idx"]:4d} valor={d["valor"]:.3f} byte={d["byte"]:.4f} pal={d["palavra"]:.4f} tven={d["tven"]:.4f} soma={soma:.4f} real={d["real"]}')

# Falsos positivos
if fp_idx:
    print()
    print(f'=== FALSOS POSITIVOS ({len(fp_idx)}) ===')
    for idx in fp_idx[:15]:
        d = deltas_todos[idx-10]
        print(f'  idx={idx} {timestamps[idx]} valor={valores[idx]:.3f}')

# Verdadeiros positivos
if tp_idx:
    print()
    print(f'=== VERDADEIROS POSITIVOS ({len(tp_idx)}) ===')
    for idx in tp_idx[:15]:
        print(f'  idx={idx} {timestamps[idx]} valor={valores[idx]:.3f}')

with open('resultado_nab_mcr.json', 'w') as f:
    json.dump({
        'dataset': 'NAB ec2_cpu_utilization_24ae8d',
        'total_samples': N,
        'real_anomalies': len(anomalias_reais),
        'mcr_detections': len(anomalias_mcr),
        'tp': tp,
        'fp': fp,
        'recall': recall,
        'precision': precisao,
        'f1': f1,
        'time_s': round(tempo, 3)
    }, f, indent=2, ensure_ascii=False)

print()
print('Resultado salvo em resultado_nab_mcr.json')
print('='*70)
