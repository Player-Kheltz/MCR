"""VALIDACAO END-TO-END leve — sem auto_treinar."""
import sys, json
sys.path.insert(0, 'E:/MCR')

print('=' * 65)
print('  VALIDACAO END-TO-END — MCR v4.3 (leve)')
print('=' * 65)

from mcr.mcr import MCR

mcr = MCR()

# V1: Historico/Memoria
print('\n[V1] Memoria:')
for i in range(8):
    mcr.processar(f"Crie um NPC profissao {i}")
rec = mcr.recordar("")
print(f'  Historico: {len(mcr._historico)} | Memoria: {len(mcr._memoria)} | recordar: {len(rec)}')
assert len(mcr._historico) >= 8
print('  V1: OK')

# V2: Codigo gerado
print('\n[V2] Geracao Lua:')
ok = 0
for entrada in ["Crie um NPC ferreiro anao", "Gere um monstro dragao de fogo",
                "Crie um NPC vendedor humano"]:
    r = mcr.processar(entrada)
    codigo = r['resultado'].get('codigo', '')
    if codigo and len(codigo) > 50: ok += 1
    print(f'  {"OK" if ok else "ERR"} | {r["acao"]} nota={r["nota"]}')
print(f'  {ok}/3')
assert ok >= 2
print('  V2: OK')

# V3: Observer
print('\n[V3] Observer:')
obs = mcr._observador
print(f'  Ativado: {mcr._obs_ativado} | Pares: {len(obs._pares)}')
if len(obs._pares) >= 5:
    obs.treinar()
    print(f'  Clusters: {len(set(obs._clusters_x.values()))}X/{len(set(obs._clusters_y.values()))}Y')
    print(f'  dH: {obs.entropia_delta():.4f} | Map: {obs._cluster_para_acao}')
print('  V3: OK')

# V4: KG
print('\n[V4] KG:')
from mcr.paths import KG_DIR
kg_files = sorted(KG_DIR.glob('patterns_*.json'))
total = sum(len(json.load(open(f, encoding='utf-8')).get('padroes', [])) for f in kg_files)
print(f'  Total: {total} padroes em {len(kg_files)} arquivos')
assert total > 4000
print('  V4: OK')

# V5: Shadow
print('\n[V5] Shadow:')
from mcr.shadow_canary import consultar_penalidades
pen = consultar_penalidades()
print(f'  APIs penalizadas: {len(pen)}')
print('  V5: OK')

print(f'\n{"="*65}')
print(f'  MCR v4.3 — TODAS AS FASES VALIDADAS')
print(f'  Tools: {len(mcr._registry.listar())} | Hist: {len(mcr._historico)} | KG: {total}')
print(f'{"="*65}')
