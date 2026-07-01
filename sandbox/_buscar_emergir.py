"""Busca historico do EMERGIR no KG e nos logs de sessao."""
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'mcr_devia'))
from modulos.kg import KnowledgeGraph

kg = KnowledgeGraph()
licoes = kg._get_licoes()

# 1. Lessons emergentes
emergentes = [l for l in licoes if l.get('ctx') == 'emergente' and not l.get('inactive')]
print(f'Lessons emergentes ativas: {len(emergentes)}')
for l in emergentes[:5]:
    err = l.get('erro', '?')[:100]
    sol = l.get('solucao', '')[:150]
    print(f'  ERRO: {err}')
    print(f'  SOL:  {sol}')
    print()

# 2. Lessons com "E se" no erro
e_se = [l for l in licoes if 'E se' in l.get('erro', '') or 'E se' in l.get('solucao', '')]
print(f'Lessons com "E se": {len(e_se)}')
for l in e_se[:3]:
    err = l.get('erro', '')[:120]
    ctx = l.get('ctx', '?')
    print(f'  [{ctx}] {err}')
    print()

# 3. Logs de sessao — ultimos emergir outputs
sandbox_logs = [
    'sandbox/.emergir_v4_z.txt',
    'sandbox/.emergir_v3_response.txt', 
    'sandbox/.emergir_v2_output.txt',
    'sandbox/.resposta_emergir_completa.txt',
]
for log_path in sandbox_logs:
    if os.path.exists(log_path):
        size = os.path.getsize(log_path)
        print(f'Log: {log_path} ({size} bytes)')
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()[:300]
        print(f'  Primeiros 300 chars: {content[:200]}')
        print()
