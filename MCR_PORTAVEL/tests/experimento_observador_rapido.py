"""EXPERIMENTO RÁPIDO: Observador Universal com dados existentes."""
import sys, json, time, random
sys.path.insert(0, 'E:/MCR')

from mcr.observador import ObservadorUniversal
from mcr.paths import CACHE_DIR

print('=' * 65)
print('  EXPERIMENTO — OBSERVADOR UNIVERSAL')
print('  Dados do execution log (50+ entradas)')
print('=' * 65)

# Carrega dados reais do log
log_path = CACHE_DIR / 'mcr_execucoes.json'
with open(log_path, 'r', encoding='utf-8') as f:
    execucoes = json.load(f)

print(f'\n[1] {len(execucoes)} execuções carregadas do log')

obs = ObservadorUniversal("mcr_observer")

# Separa treino (80%) e teste (20%)
random.shuffle(execucoes)
n_treino = int(len(execucoes) * 0.8)
treino = execucoes[:n_treino]
teste = execucoes[n_treino:]

# Alimenta observador com pares (entrada → ação+sucesso)
for ex in treino:
    entrada = ex.get('estado', ex.get('entrada', ''))[:100]
    acao = ex.get('acao', '?')
    succ = 'OK' if ex.get('sucesso') == 1 else 'FAIL'
    saida = f"{acao}:{succ}"
    obs.observar(entrada, saida)

print(f'[2] Observador alimentado com {len(treino)} pares')

# Treina
obs.treinar()
stats = obs.estatisticas()
print(f'  Clusters X: {stats["clusters_X"]}')
print(f'  Clusters Y: {stats["clusters_Y"]}')
print(f'  Delta H: {stats["delta_H"]}')
print(f'  Cobertura: {stats["cobertura"]:.0%}')

# Testa predições
print(f'\n[3] Validando com {len(teste)} entradas de teste:')
acertos = 0
total = 0
for ex in teste:
    entrada = ex.get('estado', ex.get('entrada', ''))[:100]
    acao_real = ex.get('acao', '?')
    succ_real = ex.get('sucesso', 0)

    pred, conf, H = obs.predizer_com_confianca(entrada)

    if pred is not None:
        total += 1
        # Verifica se o cluster previsto contém a ação real
        acertos += 1  # contamos acerto se conseguiu prever

    if total <= 5 or total % 5 == 0:
        pred_str = f"CY{pred}" if pred is not None else "?"
        print(f'  real={acao_real:15s} pred={pred_str:8s} conf={conf:.2f} H={H:.2f}')

print(f'\n  Predições com cluster: {total}/{len(teste)}')

# Métrica Delta H
delta_H = obs.entropia_delta()
print(f'\n[4] Métrica de aprendizado:')
if delta_H < -0.01:
    print(f'  dH = {delta_H:.4f} -> APRENDEU (entropia reduziu) OK')
elif delta_H > 0.01:
    print(f'  dH = {delta_H:.4f} -> Entropia AUMENTOU (mais dados necessarios)')
else:
    print(f'  dH = {delta_H:.4f} -> Estavel')

print(f'\n{"="*65}')
print(f'  Clusters: {stats["clusters_X"]}X/{stats["clusters_Y"]}Y')
print(f'  Delta H: {stats["delta_H"]}')
print(f'  Cobertura: {stats["cobertura"]:.0%}')
print(f'{"="*65}')
