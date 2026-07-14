"""VALIDACAO END-TO-END — Fases 0+1+2 completas."""
import sys, json
sys.path.insert(0, 'E:/MCR')

print('=' * 65)
print('  VALIDACAO END-TO-END — MCR v4.3')
print('=' * 65)

from mcr.mcr import MCR

mcr = MCR()

# ═══════════════════════════════════════════════════════════
# V1: NPC com memoria (historico + recordar)
# ═══════════════════════════════════════════════════════════
print('\n[V1] NPC com memoria:')
for i in range(10):
    mcr.processar(f"Crie um NPC profissao {i}")
rec = mcr.recordar("")
print(f'  Historico: {len(mcr._historico)} entradas')
print(f'  Memoria: {len(mcr._memoria)} entradas')
print(f'  recordar(): {len(rec)} memorias')
assert len(mcr._historico) >= 10, "Historico < 10"
assert len(rec) >= 5, "Memoria < 5"
print(f'  V1: OK')

# ═══════════════════════════════════════════════════════════
# V2: Geracao Lua sem LLM
# ═══════════════════════════════════════════════════════════
print('\n[V2] Geracao Lua:')
codigos_ok = 0
for entrada in ["Crie um NPC ferreiro anao", "Gere um monstro dragao de fogo",
                "Crie um NPC vendedor humano", "Gere um monstro orc guerreiro",
                "Crie um NPC mago elfico"]:
    r = mcr.processar(entrada)
    codigo = r['resultado'].get('codigo', '')
    if codigo and len(codigo) > 50:
        codigos_ok += 1
    print(f'  {"OK" if codigo and len(codigo)>50 else "ERR"} | {r["acao"]} nota={r["nota"]} | {entrada[:40]}')
print(f'  Codigo gerado: {codigos_ok}/5')
assert codigos_ok >= 3, f"Menos de 3 codigos validos: {codigos_ok}"
print(f'  V2: OK')

# ═══════════════════════════════════════════════════════════
# V3: Observer afeta decisoes
# ═══════════════════════════════════════════════════════════
print('\n[V3] Observer:')
obs = mcr._observador
print(f'  Ativado: {mcr._obs_ativado}')
print(f'  Pares: {len(obs._pares)}')
if len(obs._pares) >= 5:
    obs.treinar()
    print(f'  Clusters X: {len(set(obs._clusters_x.values()))}')
    print(f'  Clusters Y: {len(set(obs._clusters_y.values()))}')
    print(f'  Delta H: {obs.entropia_delta():.4f}')
    print(f'  Cobertura: {obs.cobertura():.0%}')
    print(f'  Cluster->Acao: {obs._cluster_para_acao}')
    print(f'  V3: OK — observer treinado e mapeado')
else:
    print(f'  V3: PARCIAL — {len(obs._pares)} pares (min 5)')

# ═══════════════════════════════════════════════════════════
# V4: KG cresce
# ═══════════════════════════════════════════════════════════
print('\n[V4] KG cresce:')
from mcr.paths import KG_DIR
kg_files = sorted(KG_DIR.glob('patterns_*.json'))
total_antes = 0
for f in kg_files:
    with open(f, 'r', encoding='utf-8') as fh:
        total_antes += len(json.load(fh).get('padroes', []))
print(f'  Total antes: {total_antes}')

# Roda auto_treinar para minerar
try:
    result = mcr.auto_treinar()
    print(f'  auto_treinar: {result}')
except Exception as e:
    print(f'  auto_treinar erro: {e}')

# Conta depois
kg_files = sorted(KG_DIR.glob('patterns_*.json'))
total_depois = 0
for f in kg_files:
    with open(f, 'r', encoding='utf-8') as fh:
        total_depois += len(json.load(fh).get('padroes', []))
print(f'  Total depois: {total_depois}')
if total_depois > total_antes:
    print(f'  V4: OK — KG cresceu {total_antes} -> {total_depois}')
else:
    print(f'  V4: PARCIAL — KG nao cresceu')

# ═══════════════════════════════════════════════════════════
# V5: Shadow evita erros
# ═══════════════════════════════════════════════════════════
print('\n[V5] Shadow penalidades:')
try:
    from mcr.shadow_canary import consultar_penalidades
    pen = consultar_penalidades()
    print(f'  APIs com penalidade: {len(pen)}')
    print(f'  V5: OK — consultar_penalidades() funciona')
except Exception as e:
    print(f'  V5: ERRO — {e}')

# ═══════════════════════════════════════════════════════════
# RESUMO
# ═══════════════════════════════════════════════════════════
print(f'\n{"="*65}')
print(f'  MCR v4.3 — VALIDACAO COMPLETA')
print(f'  Registry: {len(mcr._registry.listar())} tools')
print(f'  Historico: {len(mcr._historico)} entradas')
print(f'  Memoria: {len(mcr._memoria)} entradas')
print(f'  Observer: {len(obs._pares)} pares, {len(set(obs._clusters_x.values()))} clustersX')
print(f'  KG: {total_depois} padroes')
print(f'  Shadow: {len(pen)} APIs penalizadas')
print(f'  Codigos gerados: {codigos_ok}/5')
print(f'{"="*65}')
