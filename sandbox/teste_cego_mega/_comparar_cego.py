#!/usr/bin/env python3
"""Compara as respostas do Teste Cego do context_crew.py."""
import re

def analisar(texto, nome):
    metrics = {}
    metrics['chars'] = len(texto)
    metrics['linhas'] = len(texto.split('\n'))
    
    # Problemas de seguranca mencionados
    seg = ['eval', 'SSRF', 'URL', 'hardcoded', 'injection', 'path traversal', 'os.system',
           'subprocess', 'shell', 'seguranca', 'seguran', 'vazamento']
    metrics['problemas_seguranca'] = sum(1 for s in seg if s.lower() in texto.lower())
    
    # Problemas de performance mencionados
    perf = ['performance', 'conexao', 'thread', 'pool', 'cache', 'gargalo', 'lento',
            'varredura', 'recursivo', 'O(n)', 'complexidade']
    metrics['problemas_performance'] = sum(1 for p in perf if p.lower() in texto.lower())
    
    # Codigo gerado
    code_blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    metrics['blocos_codigo'] = len(code_blocks)
    metrics['linhas_codigo'] = sum(len(b.split('\n')) for b in code_blocks)
    
    # Erros de sintaxe
    erros = 0
    for b in code_blocks:
        try:
            compile(b.strip(), '<test>', 'exec')
        except:
            erros += 1
    metrics['erros_sintaxe'] = erros
    
    # Mencao de classes/metodos reais do context_crew
    reais = ['ContextCrew', '_buscar_kg', '_buscar_weblearn', '_buscar_docs', '_buscar_codigo',
             '_buscar_web', 'executar', '_extrair_termos', '_hash', '_cache', 'ThreadPoolExecutor']
    metrics['termos_reais'] = sum(1 for r in reais if r.lower() in texto.lower())
    
    return metrics

mcr = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/cego_1.txt", "r", encoding="utf-8-sig").read()
cloud = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_cloud/cego_1.txt", "r", encoding="utf-8-sig").read()

m = analisar(mcr, "MCR")
c = analisar(cloud, "Cloud")

print("=" * 65)
print("  COMPARATIVO TESTE CEGO - context_crew.py")
print("=" * 65)
print(f"\n{'Metrica':<35} {'MCR':<15} {'Cloud':<15}")
print("-" * 65)
for k in ['chars', 'linhas', 'problemas_seguranca', 'problemas_performance',
          'blocos_codigo', 'linhas_codigo', 'erros_sintaxe', 'termos_reais']:
    m_val = m[k]
    c_val = c[k]
    winner = "+" if m_val > c_val else ("+" if c_val > m_val else "=")
    if k in ('erros_sintaxe',):
        winner = "+" if m_val < c_val else ("+" if c_val < m_val else "=")
    print(f"  {k:<35} {m_val:<12} {c_val:<12}  {winner}")

print(f"\n  {'SCORE TOTAL':<35} {sum(m.values()):<12} {sum(c.values()):<12}")
if sum(m.values()) > sum(c.values()):
    print("  VENCEDOR: MCR-DevIA")
elif sum(c.values()) > sum(m.values()):
    print("  VENCEDOR: Cloud")
else:
    print("  EMPATE TECNICO")
print("=" * 65)
