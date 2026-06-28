#!/usr/bin/env python3
"""Benchmark: explorar atual vs explorar com IA + buffer."""
import sys, os, time, json
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.util import fast

BASE = r'E:\Projeto MCR'
KG_PATH = os.path.join(BASE, 'sandbox', '.mcr_devia', 'knowledge.json')

with open(KG_PATH, 'r', encoding='utf-8') as f:
    kg = json.load(f)

# 1. AMOSTRA ATUAL
atuais = [l for l in kg.get('licoes', []) if l.get('ctx') == 'conhecimento']
print(f'Lessons atuais (ctx=conhecimento): {len(atuais)}')

# Qualidade: quantas tem descricao util (nao so nome)?
uteis = sum(1 for l in atuais if len(l.get('solucao','')) > 60)
print(f'Com descricao util (>60 chars): {uteis} ({uteis/max(len(atuais),1)*100:.0f}%)')

# Duplicatas
erros = [l.get('erro','') for l in atuais]
dups = len(erros) - len(set(erros))
print(f'Duplicatas (mesmo erro): {dups}')

# 2. TESTE COM IA: pega 10 amostras e melhora com IA
print(f'\n--- Teste de melhoria com IA (10 amostras) ---')
t0 = time.time()
melhoradas = 0
for l in atuais[:10]:
    nome = l.get('erro','').replace('Code: ','').replace('Doc: ','')
    arquivo = l.get('causa','')
    tempo_inicial = time.time()
    
    # IA interpreta o que esse codigo faz
    interpretacao = fast(
        f'O que faz a classe/funcao "{nome}" em um servidor Tibia/OTServer? '
        f'Responda em 1 frase curta e objetiva:',
        0.2, 'leve'
    ) or ''
    
    if interpretacao and len(interpretacao) > 20:
        melhoradas += 1
        print(f'  {nome:30s} -> {interpretacao[:80]} ({time.time()-tempo_inicial:.1f}s)')

t_total = time.time() - t0
print(f'\n10 amostras: {melhoradas} melhoradas em {t_total:.1f}s')
print(f'Media: {t_total/10:.1f}s por lesson')
print(f'Projecao para 389 lessons: {t_total/10*389:.0f}s = {t_total/10*389/60:.1f}min')

# Projecao
print(f'\n--- Projecao ---')
print(f'Custo atual: 0s (so greppou nomes)')
print(f'Custo com IA: ~{(t_total/10*389):.0f}s para 389 lessons')
print(f'Qualidade atual: {uteis}/{len(atuais)} ({uteis/max(len(atuais),1)*100:.0f}% uteis)')
print(f'Qualidade com IA: potencial 90%+')
