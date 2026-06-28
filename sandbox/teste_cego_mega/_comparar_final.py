#!/usr/bin/env python3
"""Compara as respostas do Teste Cego Final."""
import re, os

def metricas(texto, nome):
    """Extrai metricas de qualidade de uma resposta."""
    m = {}
    m['chars'] = len(texto)
    m['linhas'] = len(texto.split('\n'))
    
    # Blocos de codigo
    blocos = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    m['blocos_codigo'] = len(blocos)
    m['linhas_codigo'] = sum(len(b.split('\n')) for b in blocos)
    
    # Erros de sintaxe
    erros = 0
    for b in blocos:
        try:
            compile(b.strip(), '<test>', 'exec')
        except:
            erros += 1
    m['erros_sintaxe'] = erros
    
    # Palavras-chave de qualidade
    keywords = {
        'async': r'\basync\b', 'await': r'\bawait\b', 'aiohttp': r'\baiohttp\b',
        'asyncio': r'\basyncio\b', 'gather': r'\bgather\b', 'retry': r'\bretry\b',
        'backoff': r'\bbackoff\b', 'timeout': r'\btimeout\b', 'logging': r'\blogging\b',
        'type_hints': r'\bdef\s+\w+\(.*?:', 'dataclass': r'\bdataclass\b',
        'solid': r'\bSOLID\b', 'srp': r'\bSRP\b|\bSingle Responsibility\b',
    }
    for k, p in keywords.items():
        m[k] = len(re.findall(p, texto))
    
    # Total de boas praticas
    m['boas_praticas'] = sum(m[k] for k in keywords.keys())
    
    return m

base = r"E:\Projeto MCR\sandbox\teste_cego_mega"
mcr_txt = open(os.path.join(base, "respostas_mcr", "cego_final.txt"), "r", encoding="utf-8-sig", errors="replace").read()
cloud_txt = open(os.path.join(base, "respostas_cloud", "cego_final.txt"), "r", encoding="utf-8-sig", errors="replace").read()

m = metricas(mcr_txt, "MCR")
c = metricas(cloud_txt, "Cloud")

print("=" * 75)
print("  TESTE CEGO FINAL - Async Refactoring")
print("=" * 75)

print(f"\n{'Metrica':<35} {'MCR':<15} {'Cloud':<15} {'Vencedor':<10}")
print("-" * 75)

# Metricas onde maior e melhor
maior_melhor = ['chars', 'linhas', 'blocos_codigo', 'linhas_codigo', 'boas_praticas',
                'async', 'await', 'aiohttp', 'asyncio', 'gather', 'retry', 'backoff',
                'timeout', 'logging', 'type_hints', 'dataclass', 'solid', 'srp']
# Metricas onde menor e melhor
menor_melhor = ['erros_sintaxe']

for k in maior_melhor:
    mv = m.get(k, 0)
    cv = c.get(k, 0)
    if mv > cv:
        win = "MCR +"
    elif cv > mv:
        win = "Cloud +"
    else:
        win = "="
    nome = k.replace('_', ' ').title()
    print(f"  {nome:<35} {mv:<15} {cv:<15} {win:<10}")

for k in menor_melhor:
    mv = m.get(k, 0)
    cv = c.get(k, 0)
    if mv < cv:
        win = "MCR +"
    elif cv < mv:
        win = "Cloud +"
    else:
        win = "="
    nome = k.replace('_', ' ').title()
    print(f"  {nome:<35} {mv:<15} {cv:<15} {win:<10}")

# Score composto
score_mcr = sum(m[k] for k in maior_melhor) - sum(m[k] for k in menor_melhor)
score_cloud = sum(c[k] for k in maior_melhor) - sum(c[k] for k in menor_melhor)

print(f"\n  {'SCORE TOTAL':<35} {score_mcr:<15} {score_cloud:<15}")
if score_mcr > score_cloud:
    print(f"\n  >>> VENCEDOR: MCR-DevIA ({score_mcr} vs {score_cloud})")
elif score_cloud > score_mcr:
    print(f"\n  >>> VENCEDOR: Cloud ({score_cloud} vs {score_mcr})")
else:
    print(f"\n  >>> EMPATE TECNICO")
print("=" * 75)
