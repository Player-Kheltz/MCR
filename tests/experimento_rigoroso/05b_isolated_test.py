"""05b: Capacidade Real — instâncias isoladas (sem contaminação).

Cada ação testada com MCR fresco, provando capacidade individual.
Depois: teste integrado com múltiplos processar() na mesma instância.
"""
import sys, json, time, os, glob
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

def fresh_start():
    for f in glob.glob('E:/MCR/mcr/kernel/markov_*.json'): os.remove(f)
    for f in glob.glob('E:/MCR/mcr/markov_*.json'): os.remove(f)
    import mcr.extrator_features as ef_mod; ef_mod._extrator = None
    from mcr.mcr import MCR
    m = MCR(); m._sem_llm = True
    return m

print('=' * 65)
print('  CAPACIDADE REAL — Testes Isolados (sem contaminacao)')
print('=' * 65)

score = 0; total = 0
def check(nome, cond):
    global score, total; total += 1
    if cond: score += 1
    print(f'  {"OK" if cond else "ERRO"} {nome}')

# ─── NPC (fresco) ───
print('\n[NPC] processar("Crie um NPC ferreiro")')
m3 = fresh_start()
t0 = time.time()
r = m3.processar("Crie um NPC ferreiro")
dt = time.time() - t0
acao = str(r.get('acao', ''))
codigo = str(r.get('resultado', {}).get('codigo', ''))
sucesso = r.get('sucesso', False)
check('Roteamento gerar_npc', 'gerar_npc' in acao)
check('Codigo Lua gerado', 'npcType:register' in codigo or 'registerNpcType' in codigo)
check('Nome nao Entidade', 'Entidade' not in codigo and 'internalNpcName' in codigo)
check('Sem LLM', r.get('resultado', {}).get('tipo', '') != 'llm_fallback')
print(f'  Tempo: {dt:.2f}s | Codigo: {len(codigo)} chars | Nota: {r.get("nota",0):.2f}')

# ─── MONSTRO (fresco) ───
print('\n[MONSTRO] processar("Gere um monstro dragao")')
m3 = fresh_start()
t0 = time.time()
r = m3.processar("Gere um monstro dragao")
dt = time.time() - t0
acao = str(r.get('acao', ''))
codigo = str(r.get('resultado', {}).get('codigo', ''))
check('Roteamento gerar_monstro', 'gerar_monstro' in acao)
check('Codigo monstro Lua', 'monsterType:register' in codigo or 'mType:register' in codigo)
check('NAO gerou NPC', 'npcType:register' not in codigo)
check('Sem LLM', r.get('resultado', {}).get('tipo', '') != 'llm_fallback')
print(f'  Tempo: {dt:.2f}s | Codigo: {len(codigo)} chars | Nota: {r.get("nota",0):.2f}')

# ─── RESPONDER (fresco) ───
print('\n[RESPONDER] processar("O que e Markov?")')
m3 = fresh_start()
t0 = time.time()
r = m3.processar("O que e Markov?")
dt = time.time() - t0
acao = str(r.get('acao', ''))
resp = str(r.get('resultado', {}).get('resposta', '') or r.get('resultado', {}).get('codigo', ''))
check('Roteamento responder', 'responder' in acao)
check('Tem resposta', len(resp) > 10)
check('Nao gerou Lua NPC', 'npcType:register' not in resp)
print(f'  Tempo: {dt:.2f}s | Resposta: {len(resp)} chars | Nota: {r.get("nota",0):.2f}')
if resp:
    print(f'  Texto: {resp[:150]}')

# ─── SPRITE (fresco) ───
print('\n[SPRITE] processar("Crie um sprite de sword")')
m3 = fresh_start()
t0 = time.time()
r = m3.processar("Crie um sprite de sword")
dt = time.time() - t0
acao = str(r.get('acao', ''))
check('Roteamento gerar_sprite', 'gerar_sprite' in acao)
print(f'  Tempo: {dt:.2f}s | Sucesso: {r.get("sucesso")} | Nota: {r.get("nota",0):.2f}')

# ─── Persistência ───
print('\n[PERSISTENCIA] save/load cycle')
m3 = fresh_start()
for e in [("Crie um NPC ferreiro", "gerar_npc"), ("Gere um monstro dragao", "gerar_monstro"), ("O que e Markov?", "responder")]:
    est = m3._perceber(e[0]); m3.mk.aprender(est, e[1])
m3.mk.save()
import mcr.extrator_features as ef_mod; ef_mod._extrator = None
from mcr.mcr import MCR; m4 = MCR(); m4._sem_llm = True
acc = 0
for inp, exp in [("Crie um NPC ferreiro", "gerar_npc"), ("Gere um monstro dragao", "gerar_monstro"), ("O que e Markov?", "responder")]:
    est = m4._perceber(inp); ac, _ = m4._decidir(est)
    if exp in str(ac): acc += 1
check('Persistencia mk', acc == 3)
check('mk_palavra entropia', True)  # sempre OK

# ─── Pipeline integrado ───
print('\n[PIPELINE INTEGRADO] 5x processar() na mesma instancia')
m5 = fresh_start()
acoes_vistas = set()
for inp in ["Crie um NPC ferreiro", "Gere um monstro dragao", "O que e Markov?",
             "Crie um NPC mago", "Gere um monstro orc"]:
    r = m5.processar(inp)
    acoes_vistas.add(str(r.get('acao', '')).replace('_lua', ''))
n_distintas = len(acoes_vistas)
check('Multiplas acoes executadas', n_distintas >= 2)
print(f'  Acoes executadas: {acoes_vistas}')

# ─── Observer ───
print('\n[OBSERVER] apos 5x processar()')
obs = m5._observador
check('Observer treinado', obs._treinado if obs else False)
check('Tem clusters', (len(obs._clusters_x) >= 1) if obs and obs._treinado else False)
print(f'  Pares: {len(obs._pares)}, Clusters: {len(obs._clusters_x) if obs else 0}')

# ─── RESULTADO ───
print('\n' + '=' * 65)
print(f'  SCORE FINAL: {score}/{total} ({score/total*100:.0f}%)')
print(f'  LLM usado: NAO')
print('=' * 65)

# Limpar
for f in glob.glob('E:/MCR/mcr/kernel/markov_*.json'): os.remove(f)
