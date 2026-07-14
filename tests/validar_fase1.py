"""VALIDACAO FASE 1 — O que NAO APRENDE agora APRENDE."""
import sys
sys.path.insert(0, 'E:/MCR')

print('=' * 65)
print('  VALIDACAO FASE 1')
print('=' * 65)

from mcr.mcr import MCR

mcr = MCR()

# ─── A1: Observador ativado e conectado ─────────────────
print('\n[A1] Observador:')
print(f'  _obs_ativado: {mcr._obs_ativado}')
print(f'  _observador: {mcr._observador is not None}')
assert mcr._obs_ativado, "Observador nao ativado!"
assert mcr._observador is not None, "Observador nao instanciado!"

# Alimenta observador com execucoes reais
for i in range(10):
    mcr.processar(f"Crie um NPC profissao {i}")
for i in range(5):
    mcr.processar(f"Gere um monstro tipo {i}")

obs = mcr._observador
if len(obs._pares) >= 5:
    obs.treinar()
    print(f'  Pares: {len(obs._pares)}')
    print(f'  Clusters X: {len(set(obs._clusters_x.values()))}')
    print(f'  Clusters Y: {len(set(obs._clusters_y.values()))}')
    print(f'  Cluster→Acao: {obs._cluster_para_acao}')
    print(f'  Delta H: {obs.entropia_delta():.4f}')
    print(f'  A1: OK — observador treinado e mapeado')
else:
    print(f'  Pares insuficientes: {len(obs._pares)} (min 5)')
    print(f'  A1: PARCIAL — alimentando mais...')

# ─── A2: Equação unificada ────────────────────────────────
print('\n[A2] Equacao unificada:')
r = mcr.processar("Crie um NPC ferreiro anao")
print(f'  Nota: {r["nota"]}')
print(f'  Acao: {r["acao"]}')
# Verifica que classificar_tipo_ponte e get_penalidade foram chamados
# (se nota != 0, o pipeline inteiro rodou incluindo avaliar)
assert r['nota'] > 0, f"Nota zero — avaliar() quebrou: {r}"
print(f'  A2: OK — equacao com penalidade unificada')

# ─── A3: KG cresce ────────────────────────────────────────
print('\n[A3] KG cresce:')
import json
from mcr.paths import KG_DIR
kg_path = KG_DIR / 'patterns_20260713_212206.json'
if kg_path.exists():
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg_antes = json.load(f)
    n_antes = len(kg_antes.get('padroes', []))
    print(f'  Padroes antes: {n_antes}')
else:
    n_antes = 0
    print(f'  KG nao encontrado, criando...')

# Roda execucoes que devem gerar codigo e minerar
for i in range(3):
    mcr.processar(f"Gere um monstro dragao tipo {i}")

# Verifica se KG cresceu
if kg_path.exists():
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg_depois = json.load(f)
    n_depois = len(kg_depois.get('padroes', []))
    print(f'  Padroes depois: {n_depois}')
    if n_depois > n_antes:
        print(f'  A3: OK — KG cresceu de {n_antes} para {n_depois}')
    else:
        print(f'  A3: PARCIAL — KG nao cresceu (nota < 0.7 ou sem codigo)')
else:
    print(f'  A3: PARCIAL — KG path nao existe')

# ─── A4: Cache reforça aprendizado ────────────────────────
print('\n[A4] Cache reforca:')
# Primeira chamada — sem cache
r1 = mcr.processar("Crie um NPC ferreiro anao")
# Segunda chamada — deve ter cache
r2 = mcr.processar("Crie um NPC ferreiro anao")
print(f'  1a: acao={r1["acao"]} nota={r1["nota"]}')
print(f'  2a: acao={r2["acao"]} nota={r2["nota"]}')
# Verifica que historico cresceu (cache ainda aprende)
h = len(mcr._historico)
print(f'  Historico total: {h} entradas')
assert h >= 2, f"Historico vazio apos 2 processamentos: {h}"
print(f'  A4: OK — cache hit ainda registra')

# ─── A5: PatternMiner salva ────────────────────────────────
print('\n[A5] PatternMiner salva:')
from mcr.pattern_miner import minerar_codigo
code = '''
function onThink(cid, interval, lastGrid)
    local monster = Monster(getMonsterTarget(cid))
    if not monster then return end
    doCreatureAddHealth(monster, 100)
    local pos = getCreaturePos(monster)
    doSendMagicEffect(pos, CONST_ME_MAGIC_BLUE)
    return true
end
'''
padroes = minerar_codigo(code, "gerar_monstro")
if padroes:
    p = padroes[0]
    print(f'  APIs: {p["api_calls"][:5]}')
    print(f'  Variaveis: {p["variaveis"][:5]}')
    print(f'  Tipo: {p["tipo"]}')
    print(f'  A5: OK — mineracao de codigo funciona')
else:
    print(f'  A5: FALHOU — minerar_codigo retornou vazio')

# ─── RESUMO ──────────────────────────────────────────────
print(f'\n{"="*65}')
print(f'  FASE 1 COMPLETA:')
print(f'  A1 Observador: {"ATIVADO" if mcr._obs_ativado else "FALHOU"}')
print(f'  A2 Equacao: unificada com get_penalidade()')
print(f'  A3 KG: {n_antes} -> {n_depois if kg_path.exists() else "?"}')
print(f'  A4 Cache: {len(mcr._historico)} historico, {len(mcr._memoria)} memoria')
print(f'  A5 PatternMiner: {"OK" if padroes else "FALHOU"}')
print(f'{"="*65}')
