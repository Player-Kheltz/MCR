#!/usr/bin/env python3
"""Analise completa do estado atual para o plano de integracao."""
import sys, os, json
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()

# 1. CATEGORIAS NATURAIS DO KG
ctxs = Counter(l.get('ctx','?') for l in licoes)

# Agrupa por prefixo
cats = {}
for ctx, count in ctxs.most_common():
    prefixo = ctx.split('_')[0] if '_' in ctx else ctx
    if prefixo not in cats: cats[prefixo] = {'ctxs': [], 'total': 0, 'count': 0}
    cats[prefixo]['ctxs'].append(ctx)
    cats[prefixo]['total'] += count
    cats[prefixo]['count'] += 1

print('=== CATEGORIAS NATURAIS DO KG ===')
print(f'{len(ctxs)} ctxs, {len(licoes)} lessons\n')

for prefixo, dados in sorted(cats.items(), key=lambda x: -x[1]['total']):
    print(f'  {prefixo:25s}: {dados["total"]:4d} lessons ({dados["count"]} ctxs)')
print()

# 2. LESSONS UTEIS VS LIXO
uteis = [l for l in licoes 
         if l.get('solucao','') and len(l.get('solucao','')) > 50
         and not l.get('solucao','').strip().startswith('{')
         and not l.get('inactive')]
lixo = [l for l in licoes if l not in uteis]
print(f'Lessons uteis: {len(uteis)} de {len(licoes)} ({len(uteis)/len(licoes)*100:.0f}%)')
print(f'Lessons lixo: {len(lixo)}')

# 3. MODULOS DISPONIVEIS
mod_dir = os.path.join('scripts', 'mcr_devia', 'modulos')
modulos = [f.replace('.py','') for f in os.listdir(mod_dir) if f.endswith('.py') and not f.startswith('__')]
print(f'\nModulos disponiveis: {len(modulos)}')

# 4. COMANDOS
cmd_dir = os.path.join('scripts', 'mcr_devia', 'comandos')
cmds = [f.replace('cmd_','').replace('.py','') for f in os.listdir(cmd_dir) 
        if f.startswith('cmd_') and f.endswith('.py')]
print(f'Comandos: {len(cmds)}')

# 5. FERRAMENTAS
try:
    import importlib
    # Lista ferramentas do MANIFEST
    ferramentas = [
        'executar_comando', 'ler_arquivo', 'escrever_arquivo', 'listar_diretorio',
        'criar_diretorio', 'buscar_codigo', 'buscar_inteligente', 'buscar_estrategico',
        'buscar_kg', 'aprender_kg', 'buscar_web', 'buscar_memoria',
        'gerar_npc', 'gerar_codigo', 'gerar_esqueleto', 'preencher_blank',
        'diagnosticar', 'pattern_analyze', 'escrever_artefato', 'validar_lua',
        'validar_python', 'executar_python', 'validar_codigo', 'perguntar_ia',
        'analisar_codigo', 'extrair_codigo', 'gerar_requirements', 'criar_atalho',
        'instalar_dependencias', 'buscar_item_canary'
    ]
    print(f'Ferramentas ToolOrchestrator: {len(ferramentas)}')
except:
    print('Ferramentas: N/A')

# 6. O QUE O MCR CONECTOR USA AGORA
print(f'\n=== ESTADO ATUAL DO MCR ===')
print(f'MCR.py linhas: ~2100')
print(f'Classes principais: MarkovUniversal, MCR, MCRConector, MCRCadeia, MCRPergunta')
print(f'Componentes MCRzificados: MCRPeso, MCREntropia, MCRRuido, MCRDecisor, MCRDiagnostico, MCRFerramenta')

# 7. RESUMO
print(f'\n=== RESUMO PARA INTEGRACAO ===')
print(f'Para o MCR ser autossuficiente, precisa INTEGRAR:')
print(f'  1. KG: {len(uteis)} lessons uteis de {len(licoes)} ({len(uteis)/len(licoes)*100:.0f}%)')
print(f'  2. Modulos: {len(modulos)}')
print(f'  3. Comandos: {len(cmds)}')
print(f'  4. Ferramentas: {len(ferramentas)}')
print(f'  5. Componentes MCRzificados: 6')
print(f'  Total: ~{len(uteis)//10 + len(modulos) + len(cmds) + len(ferramentas) + 6} integracoes')
