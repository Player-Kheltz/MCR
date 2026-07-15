#!/usr/bin/env python3
"""
Experimento 1: Deteccao de Mudanca em Stream Nao-Estacionario
MCR (entropia multi-nivel) vs Page-Hinkley, CUSUM, ADWIN

Pergunta: MCR detecta mudancas de regime mais rapido que metodos classicos?
"""
import sys, os, math, json, time, random
from collections import deque, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, 'E:/MCR')

import mcr.mcr as mcr

random.seed(42)

print('='*70)
print('EXPERIMENTO 1: DETEccAO DE MUDANCA EM STREAM NAO-ESTACIONARIO')
print('='*70)

# ============================================================
# 1. GERAR STREAM MULTI-REGIME
# ============================================================
def gerar_stream(seed=42):
    rng = random.Random(seed)
    stream = []
    regimes = []
    change_points = []
    
    regimes_config = [
        ('A:uniforme', ['a','b','c','d','e']),
        ('B:skewed', ['a','a','a','a','a','b','c','d','e']),
        ('C:repetitivo', ['a','b','c']*3),
        ('D:alta_var', ['x','y','z','w','v','u','t']),
        ('E:sazonal', ['a','b','a','b','a','b','c','d']),
        ('F:baixa_var', ['a','a','a','b']*2),
    ]
    
    n_por_regime = 200
    for nome, alfabeto in regimes_config:
        change_points.append(len(stream))
        for _ in range(n_por_regime):
            stream.append(rng.choice(alfabeto))
            regimes.append(nome)
    
    print(f'Stream gerado: {len(stream)} amostras, {len(regimes_config)} regimes')
    print(f'Change points (indices): {change_points}')
    for cp, nome in zip(change_points, [r[0] for r in regimes_config]):
        print(f'  idx={cp:4d}: {nome}')
    
    return stream, regimes, change_points

stream, regimes, change_points_reais = gerar_stream()
N = len(stream)

# ============================================================
# 2. DETECTORES
# ============================================================

# --- 2A. MCR Multi-nivel ---
class DetectorMCR:
    def __init__(self, nome='mcr', janela=20, threshold_rel=0.08, min_niveis=2, cool_down=10):
        self.nome = nome
        self.mk_byte = mcr.MCR('byte')
        self.mk_pal = mcr.MCR('palavra')
        self.mk_tven = mcr.MCR('tven')
        self.janela = janela
        self.threshold_rel = threshold_rel
        self.min_niveis = min_niveis
        self.cool_down = cool_down
        self._hist = {'byte': deque(maxlen=janela), 'palavra': deque(maxlen=janela), 'tven': deque(maxlen=janela)}
        self.anterior_byte = None
        self.anterior_pal = None
        self.anterior_tven = None
        self.alarmes = []
        self.ultimo_alarme = -cool_down
    
    def alimentar(self, token):
        if self.anterior_byte is not None:
            self.mk_byte.aprender(self.anterior_byte, token)
        self.anterior_byte = token
    
    def medir(self, nivel='byte'):
        mk = self.mk_byte
        e = mk.entropia_media() if mk.total > 0 else 1.0
        self._hist['byte'].append(e)
    
    def delta_rel(self, nivel):
        hist = self._hist.get(nivel, [])
        if len(hist) < 2: return 0.0
        diff = abs(hist[-1] - hist[-2])
        return diff / hist[-2] if hist[-2] > 0.001 else diff
    
    def passo(self, idx, token):
        self.alimentar(token)
        if idx >= 10:
            self.medir()
            dr = self.delta_rel('byte')
            evento = dr > self.threshold_rel and (idx - self.ultimo_alarme) >= self.cool_down
            if evento:
                self.alarmes.append(idx)
                self.ultimo_alarme = idx
                return True, dr
        return False, 0.0

# --- 2B. Detector MCR Multi-nivel COMPLETO (byte+palavra+tven) ---
class DetectorMCRCompleto:
    def __init__(self, janela=20, threshold_rel=0.08, min_niveis=2, cool_down=10):
        self.mk_byte = mcr.MCR('byte')
        self.mk_pal = mcr.MCR('palavra')
        self.mk_tven = mcr.MCR('tven')
        self.janela = janela
        self.threshold_rel = threshold_rel
        self.min_niveis = min_niveis
        self.cool_down = cool_down
        self._hist = {'byte': deque(maxlen=janela), 'palavra': deque(maxlen=janela), 'tven': deque(maxlen=janela)}
        self.ant = {'byte': None, 'palavra': None, 'tven': None}
        self.alarmes = []
        self.ultimo_alarme = -cool_down
    
    def tokenizar(self, stream, i):
        """Gera tokens byte, palavra, tven do stream"""
        c = stream[i]
        if i < 3: return c, None, None
        # byte: o proprio caractere
        # palavra: bigrama
        pal = stream[i-1] + c
        # tven: trigrama  
        tven = stream[i-2] + stream[i-1] + c
        return c, pal, tven
    
    def passo(self, idx, stream):
        tok, pal, tven = self.tokenizar(stream, idx)
        if pal is None:
            self.ant['byte'] = tok
            return False, 0.0
        
        _map_nivel = {'byte': 'byte', 'palavra': 'pal', 'tven': 'tven'}
        for nivel, token in [('byte', tok), ('palavra', pal), ('tven', tven)]:
            mk = getattr(self, f'mk_{_map_nivel[nivel]}')
            if self.ant[nivel] is not None:
                mk.aprender(self.ant[nivel], token)
            self.ant[nivel] = token
        
        if idx >= 20:
            spikes = {}
            for nivel in ['byte', 'palavra', 'tven']:
                mk = getattr(self, f'mk_{_map_nivel[nivel]}')
                e = mk.entropia_media() if mk.total > 0 else 1.0
                self._hist[nivel].append(e)
                h = self._hist[nivel]
                if len(h) >= 2:
                    diff = abs(h[-1] - h[-2])
                    dr = diff / h[-2] if h[-2] > 0.001 else diff
                    if dr > self.threshold_rel:
                        spikes[nivel] = dr
            
            evento = len(spikes) >= self.min_niveis and (idx - self.ultimo_alarme) >= self.cool_down
            if evento:
                self.alarmes.append(idx)
                self.ultimo_alarme = idx
                return True, spikes
        return False, {}

# --- 2C. Page-Hinkley ---
class DetectorPageHinkley:
    def __init__(self, delta=0.005, lambda_=50, alpha=0.9999):
        self.delta = delta
        self.lambda_ = lambda_
        self.alpha = alpha
        self.mean = 0.0
        self.n = 0
        self.sum = 0.0
        self.mT = 0.0
        self.MT = 0.0
        self.ph_pos = 0.0
        self.ph_neg = 0.0
        self.alarmes = []
        self.cool_down = 10
        self.ultimo_alarme = -self.cool_down
    
    def passo(self, idx, valor):
        # Mapear char para float (0-25)
        x = ord(valor) - 97 if 'a' <= valor <= 'z' else 10.0
        self.n += 1
        self.mean = self.alpha * self.mean + (1 - self.alpha) * x
        self.sum += x - self.mean - self.delta
        self.ph_pos = max(0, self.ph_pos + x - self.mean - self.delta)
        self.ph_neg = max(0, self.ph_neg - x + self.mean - self.delta)
        
        alarme = False
        if self.ph_pos > self.lambda_ or self.ph_neg > self.lambda_:
            if (idx - self.ultimo_alarme) >= self.cool_down:
                self.alarmes.append(idx)
                self.ultimo_alarme = idx
                alarme = True
                self.ph_pos = 0
                self.ph_neg = 0
        return alarme

# --- 2D. CUSUM ---
class DetectorCUSUM:
    def __init__(self, threshold=5.0, drift=0.005):
        self.threshold = threshold
        self.drift = drift
        self.mean = 0.0
        self.n = 0
        self.cusum_pos = 0.0
        self.cusum_neg = 0.0
        self.alarmes = []
        self.cool_down = 10
        self.ultimo_alarme = -self.cool_down
    
    def passo(self, idx, valor):
        x = ord(valor) - 97 if 'a' <= valor <= 'z' else 10.0
        self.n += 1
        self.mean += (x - self.mean) / min(self.n, 100)
        self.cusum_pos = max(0, self.cusum_pos + x - self.mean - self.drift)
        self.cusum_neg = max(0, self.cusum_neg - x + self.mean - self.drift)
        
        alarme = False
        if self.cusum_pos > self.threshold or self.cusum_neg > self.threshold:
            if (idx - self.ultimo_alarme) >= self.cool_down:
                self.alarmes.append(idx)
                self.ultimo_alarme = idx
                alarme = True
                self.cusum_pos = 0
                self.cusum_neg = 0
        return alarme

# --- 2E. ADWIN (Adaptive Windowing simplificado) ---
class DetectorADWIN:
    def __init__(self, delta=0.002, max_buckets=10):
        self.delta = delta
        self.max_buckets = max_buckets
        self.window = deque()
        self.alarmes = []
        self.cool_down = 10
        self.ultimo_alarme = -self.cool_down
    
    def passo(self, idx, valor):
        x = ord(valor) - 97 if 'a' <= valor <= 'z' else 10.0
        self.window.append(x)
        
        alarme = False
        if len(self.window) > 30:
            # Simples: compara media das duas metades
            meio = len(self.window) // 2
            m1 = sum(list(self.window)[:meio]) / meio
            m2 = sum(list(self.window)[meio:]) / (len(self.window) - meio)
            eps = math.sqrt(1.0 / (2 * meio) * math.log(4.0 / self.delta)) if meio > 0 else 0
            
            if abs(m1 - m2) > eps:
                if (idx - self.ultimo_alarme) >= self.cool_down:
                    self.alarmes.append(idx)
                    self.ultimo_alarme = idx
                    alarme = True
                    # Dropar metade mais velha
                    for _ in range(meio):
                        if self.window: self.window.popleft()
        
        return alarme

# ============================================================
# 3. EXECUTAR TODOS OS DETECTORES
# ============================================================
print('\n' + '-'*70)
print('Executando detectores...')
print('-'*70)

detectores = {
    'MCR (byte)': DetectorMCR(),
    'MCR (byte+pal+tven)': DetectorMCRCompleto(),
    'Page-Hinkley': DetectorPageHinkley(),
    'CUSUM': DetectorCUSUM(),
    'ADWIN': DetectorADWIN(),
}

tempos = {}
resultados_detectores = {}

for nome, det in detectores.items():
    t0 = time.time()
    for idx in range(N):
        if isinstance(det, DetectorMCRCompleto):
            det.passo(idx, stream)
        else:
            det.passo(idx, stream[idx])
    tempos[nome] = time.time() - t0
    resultados_detectores[nome] = list(det.alarmes)
    print(f'  {nome:25}: {len(det.alarmes)} alarmes em {tempos[nome]:.3f}s')

# ============================================================
# 4. MÉTRICAS
# ============================================================
def avaliar(alarmes, change_points, N):
    """
    Delay medio: amostras entre change point e primeiro alarme apos ele
    Falsos positivos: alarmes fora da janela de tolerancia (20 amostras) apos change point
    """
    TP = 0
    delays = []
    janela_tol = 30
    
    # Para cada change point, ve se tem alarme na janela
    alarmes_usados = set()
    for cp in change_points:
        melhor_delay = None
        for a in alarmes:
            if a >= cp and a < cp + janela_tol and a not in alarmes_usados:
                delay = a - cp
                if melhor_delay is None or delay < melhor_delay:
                    melhor_delay = delay
                    melhor_alarme = a
        if melhor_delay is not None:
            TP += 1
            delays.append(melhor_delay)
            alarmes_usados.add(melhor_alarme)
    
    # Falsos positivos: alarmes que nao estao em nenhuma janela
    alarmes_em_janela = set()
    for cp in change_points:
        for a in alarmes:
            if cp <= a < cp + janela_tol:
                alarmes_em_janela.add(a)
    FP = len(alarmes) - len(alarmes_em_janela)
    
    # Falso negativos
    FN = len(change_points) - TP
    
    delay_medio = sum(delays) / len(delays) if delays else float('inf')
    delay_min = min(delays) if delays else float('inf')
    delay_max = max(delays) if delays else float('inf')
    
    return {
        'TP': TP,
        'FP': FP,
        'FN': FN,
        'n_change_points': len(change_points),
        'n_alarmes': len(alarmes),
        'recall': TP / len(change_points) if change_points else 0,
        'precisao': TP / (TP + FP) if (TP + FP) > 0 else 0,
        'f1': 2 * TP / (2 * TP + FP + FN) if (2*TP+FP+FN) > 0 else 0,
        'delay_medio': round(delay_medio, 2) if delays else float('inf'),
        'delay_min': delay_min,
        'delay_max': delay_max,
        'alarmes_indices': alarmes,
    }

print('\n' + '-'*70)
print('AVALIACAO:')
print('-'*70)

metricas = {}
for nome, alarmes in resultados_detectores.items():
    m = avaliar(alarmes, change_points_reais, N)
    metricas[nome] = m
    
    print(f'\n{nome}:')
    print(f'  TP={m["TP"]}/{m["n_change_points"]} FP={m["FP"]} FN={m["FN"]}')
    print(f'  Recall={m["recall"]:.3f} Precisao={m["precisao"]:.3f} F1={m["f1"]:.3f}')
    if m['delay_medio'] != float('inf'):
        print(f'  Delay medio: {m["delay_medio"]} amostras (min={m["delay_min"]}, max={m["delay_max"]})')
    print(f'  Alarmes: {m["alarmes_indices"][:10]}{"..." if len(m["alarmes_indices"])>10 else ""}')

# ============================================================
# 5. TABELA COMPARATIVA
# ============================================================
print('\n' + '='*70)
print('TABELA COMPARATIVA')
print('='*70)
print(f'{"Metodo":25} {"Recall":>8} {"Precisao":>10} {"F1":>8} {"Delay":>8} {"FP":>6} {"T(s)":>8}')
print(f'{"-":-<25} {"-":->8} {"-":->10} {"-":->8} {"-":->8} {"-":->6} {"-":->8}')

for nome in sorted(metricas.keys()):
    m = metricas[nome]
    delay = f'{m["delay_medio"]:.0f}' if m['delay_medio'] != float('inf') else '-'
    print(f'{nome:25} {m["recall"]:>8.3f} {m["precisao"]:>10.3f} {m["f1"]:>8.3f} {delay:>8} {m["FP"]:>6} {tempos[nome]:>8.3f}')

# ============================================================
# 6. ANALISE MCR-SPECIFIC: entropia como coordenada
# ============================================================
print('\n' + '='*70)
print('ANALISE MCR-SPECIFIC: entropia como coordenada intrinseca')
print('='*70)

# Re-roda MCR completo e captura evolucao da entropia
det_mcr = DetectorMCRCompleto()
entropias_byte = []
entropias_pal = []
entropias_tven = []

for idx in range(N):
    tok, pal, tven = det_mcr.tokenizar(stream, idx)
    if pal is None:
        det_mcr.ant['byte'] = tok
        continue
    
    _map_nivel2 = {'byte': 'byte', 'palavra': 'pal', 'tven': 'tven'}
    for nivel, token in [('byte', tok), ('palavra', pal), ('tven', tven)]:
        mk = getattr(det_mcr, f'mk_{_map_nivel2[nivel]}')
        if det_mcr.ant[nivel] is not None:
            mk.aprender(det_mcr.ant[nivel], token)
        det_mcr.ant[nivel] = token
    
    if idx >= 10:
        e_byte = det_mcr.mk_byte.entropia_media() if det_mcr.mk_byte.total > 0 else 1.0
        e_pal = det_mcr.mk_pal.entropia_media() if det_mcr.mk_pal.total > 0 else 1.0
        e_tven = det_mcr.mk_tven.entropia_media() if det_mcr.mk_tven.total > 0 else 1.0
        entropias_byte.append(e_byte)
        entropias_pal.append(e_pal)
        entropias_tven.append(e_tven)

print(f'\nEvolucao da entropia nos change points:')
for cp in change_points_reais:
    if cp < len(entropias_byte):
        e_b = entropias_byte[cp]
        e_p = entropias_pal[cp] if cp < len(entropias_pal) else 0
        e_t = entropias_tven[cp] if cp < len(entropias_tven) else 0
        print(f'  idx={cp:4d}: byte={e_b:.3f} palavra={e_p:.3f} tven={e_t:.3f}')

# Mostra variacao de entropia nos change points
print(f'\nVariacao de entropia nos change points (absoluta):')
for cp in change_points_reais:
    if cp > 0 and cp < len(entropias_byte)-1:
        d_byte = abs(entropias_byte[cp] - entropias_byte[cp-1])
        d_pal = abs(entropias_pal[cp] - entropias_pal[cp-1])
        d_tven = abs(entropias_tven[cp] - entropias_tven[cp-1])
        print(f'  idx={cp:4d}: d_byte={d_byte:.4f} d_pal={d_pal:.4f} d_tven={d_tven:.4f}')

# Variacao media entropia em pontos NORMAIS vs CHANGE POINTS
deltas_normais = []
deltas_change = []
for i in range(1, len(entropias_byte)):
    d = abs(entropias_byte[i] - entropias_byte[i-1])
    if i in change_points_reais:
        deltas_change.append(d)
    else:
        deltas_normais.append(d)

media_normal = sum(deltas_normais) / len(deltas_normais) if deltas_normais else 0
media_change = sum(deltas_change) / len(deltas_change) if deltas_change else 0
print(f'\nVariacao MEDIA da entropia byte:')
print(f'  Pontos normais: {media_normal:.6f}')
print(f'  Change points:  {media_change:.6f}')
print(f'  Razio change/normal: {media_change/media_normal:.2f}x' if media_normal > 0 else '')

# ============================================================
# 7. SALVAR
# ============================================================
resultados = {
    'config': {
        'stream_size': N,
        'n_regimes': len(change_points_reais),
        'change_points': change_points_reais,
    },
    'resultados': metricas,
    'tempos': tempos,
    'analise_entropia': {
        'delta_medio_normal': round(media_normal, 6),
        'delta_medio_change': round(media_change, 6),
        'razao': round(media_change/media_normal, 2) if media_normal > 0 else None,
    }
}

with open('resultado_exp1.json', 'w') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print(f'\nResultados salvos em resultado_exp1.json')
print('='*70)
