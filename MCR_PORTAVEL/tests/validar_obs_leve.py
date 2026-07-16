"""VALIDAÇÃO LEVE: Observador com dados do execution log."""
import sys, json, time, random
sys.path.insert(0, 'E:/MCR')

from mcr.observador import ObservadorUniversal
from mcr.paths import CACHE_DIR

print('=' * 65)
print('  VALIDACAO — OBSERVADOR (dados do log)')
print('=' * 65)

log_path = CACHE_DIR / 'mcr_execucoes.json'
with open(log_path, 'r', encoding='utf-8') as f:
    execucoes = json.load(f)

print(f'\n[F1] {len(execucoes)} execucoes no log')
has_raw = sum(1 for e in execucoes if e.get('entrada_raw'))
print(f'  Com entrada_raw: {has_raw}/{len(execucoes)}')

# Usa estado como fallback se entrada_raw ausente
random.shuffle(execucoes)
n_treino = int(len(execucoes) * 0.8)
treino, teste = execucoes[:n_treino], execucoes[n_treino:]

obs = ObservadorUniversal("validacao")

for ex in treino:
    entrada = ex.get('entrada_raw') or ex.get('estado', '')[:100]
    acao = ex.get('acao', '?')
    succ = 'OK' if ex.get('sucesso') == 1 else 'FAIL'
    obs.observar(entrada, f"{acao}:{succ}")

print(f'\n[F2] {len(treino)} pares de treino')
obs.treinar()

# F3
print(f'\n[F3] Auto-expansao:')
fracos = obs.clusters_fracos()
print(f'  Clusters fracos: {len(fracos)}')
print(f'  Precisa expandir: {obs.precisa_expandir()}')

# F4 
print(f'\n[F4] Equacao:')
qual = obs.avaliar_qualidade()
for k, v in qual.items():
    print(f'  {k}: {v}')

# F5 
print(f'\n[F5] Predicoes ({len(teste)} teste):')
acertos = 0
for ex in teste:
    entrada = ex.get('entrada_raw') or ex.get('estado', '')[:100]
    real_acao = ex.get('acao', '?')
    pred, conf, H = obs.predizer_com_confianca(entrada)
    pred_str = f"CY{pred}" if pred is not None else "?"
    print(f'  real={real_acao:15s} pred={pred_str:8s} conf={conf:.2f} H={H:.2f}')

print(f'\n{"="*65}')
print(f'  Clusters: {len(set(obs._clusters_x.values()))}X/{len(set(obs._clusters_y.values()))}Y')
print(f'  dH: {obs.entropia_delta():.4f}')
print(f'  Cobertura: {obs.cobertura():.0%}')
print(f'  Pronto: {qual["pronto"]}')
print(f'{"="*65}')
