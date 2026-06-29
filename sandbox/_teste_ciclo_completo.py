"""Teste completo do ciclo: Self-Study + Checkpoint + Auto-Repair + Deep Analysis."""
import sys, json, time, os
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
from modulos.kg import KnowledgeGraph
from modulos.progress_tracker import ler

print('=' * 65)
print('   CICLO DE AUTO-MELHORIA — TESTE COMPLETO')
print('=' * 65)
print()

# 1. Verifica crash pendente
estado = ler()
if estado.get('crashed_at'):
    print('⚠ CRASH DETECTADO do ciclo anterior!')
    print(f'   Fase: {estado.get("checkpoint",{}).get("phase")}')
    print(f'   Erro: {estado.get("error_info",{}).get("msg")}')
    print()
elif estado.get('status') == 'running':
    print('⚠ Pipeline ainda rodando...')

# 2. Executa Self-Study
t0 = time.time()
ma = MasterAgent()
ma.self_study.executar()
t_total = round(time.time() - t0, 1)

# 3. Le resultados
kg = KnowledgeGraph()
licoes = kg._get_licoes()
sk = [l for l in licoes if l.get('ctx') == 'self_knowledge']
sugs = [l for l in licoes if l.get('ctx') == 'sugestao_melhoria']
repair = [l for l in licoes if l.get('ctx') == 'auto_repair']

print()
print('=' * 65)
print('   RESULTADOS DO CICLO')
print('=' * 65)
print()

# Scan atual
if sk:
    s = sk[-1]
    m = json.loads(s.get('solucao', '{}')) if isinstance(s.get('solucao'), str) else s.get('solucao', {})
    print(f'⏱ Tempo total: {t_total}s')
    print(f'📊 Scan: {m.get("total_arquivos")} arquivos, {m.get("total_linhas")} linhas')
    print(f'   Classes: {m.get("total_classes")} | Funções: {m.get("total_funcoes")}')
    print()
    print('   Top 5 maiores:')
    for a in m.get('top5_maiores', []):
        print(f'     {a["nome"]}: {a["linhas"]} linhas')
    print()

# Auto-repair
print(f'🔧 Auto-Repair: {len(repair)} lessons registradas')
if repair:
    por_arquivo = {}
    for r in repair:
        fname = r.get('erro', '').split(':')[1].strip() if ':' in r.get('erro', '') else '?'
        por_arquivo.setdefault(fname, []).append(r)
    for fname, rs in sorted(por_arquivo.items()):
        print(f'   {fname}: {len(rs)} correcoes')
    print()

# Health
correcoes_count = len(repair)
if correcoes_count > 0:
    print(f'📈 Saude do codigo: +{correcoes_count * 10}pts (rough estimate)')
    print()

# Sugestao final
if sugs:
    s = sugs[-1]
    print('💡 SUGESTAO FINAL:')
    print(f'   {s.get("erro", "")[:120]}')
    print(f'   Causa: {s.get("causa", "")[:150]}')
    print()
    print(s.get("solucao", "")[:1200])

print()
print('=' * 65)
print('   CICLO CONCLUIDO')
print('=' * 65)
