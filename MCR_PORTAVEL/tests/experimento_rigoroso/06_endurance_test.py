"""06: Endurance Test — MCR em produção real.

Roda 30 processar() variados sem limpar memória.
Verifica arquivos gerados no disco, roteamento, persistência.
"""
import sys, json, time, os, glob, re
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, 'E:/MCR')

# NÃO limpar — vamos preservar os Markov JSONs
# Só limpar sujeira de testes anteriores
for f in glob.glob('E:/MCR/mcr/kernel/markov_mcr_cognicao.json'):
    os.remove(f)
for f in glob.glob('E:/MCR/mcr/kernel/markov_mcr_palavra.json'):
    os.remove(f)

import mcr.extrator_features as ef_mod
ef_mod._extrator = None

from mcr.mcr import MCR
mcr = MCR()
mcr._sem_llm = True

print('=' * 65)
print('  ENDURANCE TEST — 30 processar() sem limpeza')
print('=' * 65)

INPUTS = [
    ("Crie um NPC ferreiro", "gerar_npc"),
    ("Gere um monstro dragao", "gerar_monstro"),
    ("O que e Markov?", "responder"),
    ("Crie um NPC mago", "gerar_npc"),
    ("Gere um monstro demonio", "gerar_monstro"),
    ("Crie um NPC guarda", "gerar_npc"),
    ("Como funciona entropia?", "responder"),
    ("Gere um monstro orc", "gerar_monstro"),
    ("Crie um sprite de sword", "gerar_sprite"),
    ("Crie um NPC vendedor", "gerar_npc"),
    ("Gere um monstro dragao ancião", "gerar_monstro"),
    ("O que e equacao MCR?", "responder"),
    ("Crie um NPC alquimista", "gerar_npc"),
    ("Gere um monstro esqueleto", "gerar_monstro"),
    ("Crie um NPC cozinheiro", "gerar_npc"),
    ("Gere um sprite de shield", "gerar_sprite"),
    ("Explique cadeia de Markov", "responder"),
    ("Gere um monstro lobo", "gerar_monstro"),
    ("Crie um NPC ferreiro anão", "gerar_npc"),
    ("Gere um monstro vampiro", "gerar_monstro"),
    ("O que e entropia Shannon?", "responder"),
    ("Crie um NPC arqueiro", "gerar_npc"),
    ("Gere um monstro ciclope", "gerar_monstro"),
    ("Crie um NPC pescador", "gerar_npc"),
    ("Gere um monstro dragao vermelho", "gerar_monstro"),
    ("Crie um sprite de armor", "gerar_sprite"),
    ("Como gerar um NPC no MCR?", "responder"),
    ("Gere um monstro golem", "gerar_monstro"),
    ("Crie um NPC taberneiro", "gerar_npc"),
    ("Qual a diferenca entre Markov e LLM?", "responder"),
]

RESULTS_DIR = 'E:/MCR/tests/experimento_rigoroso/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── Executar ────────────────────────────────────────────
t_total = 0
acertos_rot = 0
acertos_exec = 0
falhas = 0
acoes_vistas = set()

print(f'\nProcessando {len(INPUTS)} entradas...')
for i, (inp, expected) in enumerate(INPUTS):
    t0 = time.time()
    try:
        r = mcr.processar(inp)
    except Exception as e:
        r = {'sucesso': False, 'acao': 'erro', 'erro': str(e), 'nota': 0}
    dt = time.time() - t0
    t_total += dt

    acao = str(r.get('acao', '?')).replace('_lua', '')
    sucesso = r.get('sucesso', False)
    nota = r.get('nota', 0)
    tool = r.get('resultado', {}).get('_tool', '?')

    rot_ok = expected in acao
    if rot_ok: acertos_rot += 1
    if sucesso: acertos_exec += 1
    if not sucesso and not rot_ok: falhas += 1
    acoes_vistas.add(acao)

    status = 'OK' if rot_ok else 'ER'
    if i < 5 or i % 10 == 0:
        print(f'  [{i+1:2d}] {status} {inp[:40]:40s} -> {acao:18s} n={nota:.2f} t={dt:.1f}s')

# ─── Verificar disco ────────────────────────────────────
print(f'\n{"-"*65}')
print('VERIFICACAO DO DISCO')

npc_dir = 'E:/MCR/server/data-otservbr-global/npc'
mon_dir = 'E:/MCR/server/data-otservbr-global/monster'

# Arquivos recentes (últimos 30 min)
import datetime
agora = time.time()
recentes_npc = []
recentes_mon = []
if os.path.isdir(npc_dir):
    for f in glob.glob(f'{npc_dir}/*.lua'):
        mtime = os.path.getmtime(f)
        if agora - mtime < 1800:  # 30 min
            recentes_npc.append((os.path.basename(f), f, mtime))
if os.path.isdir(mon_dir):
    for f in glob.glob(f'{mon_dir}/*.lua'):
        mtime = os.path.getmtime(f)
        if agora - mtime < 1800:
            recentes_mon.append((os.path.basename(f), f, mtime))

print(f'  NPCs gerados: {len(recentes_npc)}')
for nome, path, _ in sorted(recentes_npc)[:10]:
    size = os.path.getsize(path)
    with open(path, 'r') as f: content = f.read()
    is_npc = 'npcType:register' in content or 'registerNpcType' in content
    is_mon = 'mType:register' in content or 'monsterType:register' in content
    has_name = re.search(r'internalNpcName\s*=\s*"([^"]+)"', content)
    name = has_name.group(1) if has_name else '?'
    print(f'    {nome:30s} {size:5d}b name={name:20s} npc={is_npc} mon={is_mon}')

contaminados_npc = sum(1 for nome, _, _ in recentes_npc if any(kw in nome.lower() for kw in ['dragao','demonio','orc','esqueleto','lobo','vampiro','ciclope','golem','markov','entidade','armor','shield','sword','sprite','como','oque','explique','qual','diferenca','funciona']))
normais_npc = len(recentes_npc) - contaminados_npc

print(f'  Monstros gerados: {len(recentes_mon)}')
for nome, path, _ in sorted(recentes_mon)[:10]:
    size = os.path.getsize(path)
    with open(path, 'r') as f: content = f.read()
    is_npc = 'npcType:register' in content
    is_mon = 'mType:register' in content
    has_name = re.search(r'internalNpcName\s*=\s*"([^"]+)"', content) or re.search(r'monster\.name\s*=\s*"([^"]+)"', content)
    name = has_name.group(1) if has_name else '?'
    print(f'    {nome:30s} {size:5d}b name={name:20s} npc={is_npc} mon={is_mon}')

contaminados_mon = sum(1 for nome, _, _ in recentes_mon if any(kw in nome.lower() for kw in ['markov','entidade','explique','qual','como','oque']))

# ─── Persistência ───────────────────────────────────────
print(f'\n{"-"*65}')
print('PERSISTENCIA')

mk_json = glob.glob('E:/MCR/mcr/kernel/markov_mcr_cognicao.json')
pal_json = glob.glob('E:/MCR/mcr/kernel/markov_mcr_palavra.json')

print(f'  mcr_cognicao.json: {"EXISTE" if mk_json else "NAO EXISTE"}')
if mk_json:
    size = os.path.getsize(mk_json[0])
    with open(mk_json[0]) as f:
        data = json.load(f)
    print(f'    {size} bytes, {len(data.get("transicoes",{}))} estados, {data.get("total",0)} total')

print(f'  mcr_palavra.json: {"EXISTE" if pal_json else "NAO EXISTE"}')
if pal_json:
    size = os.path.getsize(pal_json[0])
    with open(pal_json[0]) as f:
        data = json.load(f)
    print(f'    {size} bytes, {len(data.get("transicoes",{}))} estados, {data.get("total",0)} total')

# ─── Métricas finais ────────────────────────────────────
mk_est = len(mcr.mk.transicoes)
mk_trans = sum(len(v) for v in mcr.mk.transicoes.values())
mk_pal_est = len(mcr.mk_palavra.transicoes)
mk_pal_trans = sum(len(v) for v in mcr.mk_palavra.transicoes.values())
obs_pares = len(mcr._observador._pares)
obs_treinado = mcr._observador._treinado

# Verificar quantos tipos diferentes de ação foram usados
acoes_npc = sum(1 for nome, _ in recentes_npc if any(kw in nome.lower() for kw in ['ferreiro','mago','guarda','vendedor','alquimista','cozinheiro','arqueiro','pescador','taberneiro']))
contaminados_por_npc = sum(1 for nome, _ in recentes_npc if not any(kw in nome.lower() for kw in ['ferreiro','mago','guarda','vendedor','alquimista','cozinheiro','arqueiro','pescador','taberneiro','entidade']))
contaminados_por_mon = sum(1 for nome, _, in recentes_mon if any(kw in nome.lower() for kw in ['markov','entidade','explique','qual','como','oque']))

# ─── RESULTADO ──────────────────────────────────────────
print(f'\n{"="*65}')
print('  RESULTADO ENDURANCE')
print(f'{"="*65}')
print(f'  Roteamento:        {acertos_rot}/{len(INPUTS)} ({acertos_rot/len(INPUTS)*100:.0f}%)')
print(f'  Execucoes OK:      {acertos_exec}/{len(INPUTS)}')
print(f'  Tempo total:       {t_total:.1f}s ({t_total/len(INPUTS):.1f}s/input)')
print(f'  Acoes distintas:   {len(acoes_vistas)} ({acoes_vistas})')
print(f'  MK decisao:        {mk_est} est, {mk_trans} trans')
print(f'  MK palavra:        {mk_pal_est} est, {mk_pal_trans} trans ({"PERSISTIDO" if pal_json else "NAO PERSISTIDO"})')
print(f'  Observer:          {obs_pares} pares, treinado={obs_treinado}')
print(f'  NPCs gerados:      {len(recentes_npc)} (normais: {normais_npc}, contaminados: {contaminados_npc})')
print(f'  Monstros gerados:  {len(recentes_mon)} (contaminados: {contaminados_mon})')
print(f'  Cognicao JSON:     {"SIM" if mk_json else "NAO"}')
print(f'  LLM usado:         NAO')
print(f'{"="*65}')

resultado = {
    'roteamento_pct': round(acertos_rot/len(INPUTS)*100),
    'execucoes_ok': acertos_exec,
    'acoes_distintas': len(acoes_vistas),
    'tempo_total': round(t_total, 1),
    'tempo_medio': round(t_total/len(INPUTS), 1),
    'mk_estados': mk_est, 'mk_transicoes': mk_trans,
    'mk_palavra_estados': mk_pal_est, 'mk_palavra_transicoes': mk_pal_trans,
    'observer_pares': obs_pares,
    'npcs_gerados': len(recentes_npc),
    'monstros_gerados': len(recentes_mon),
    'contaminados_npc': contaminados_npc,
    'contaminados_mon': contaminados_mon,
    'cognicao_json': bool(mk_json),
    'palavra_json': bool(pal_json),
}
with open(os.path.join(RESULTS_DIR, 'endurance_result.json'), 'w') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
print(f'\nSalvo em {RESULTS_DIR}/endurance_result.json')
