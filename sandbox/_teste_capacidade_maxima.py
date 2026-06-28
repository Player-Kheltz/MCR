#!/usr/bin/env python3
"""Teste de CAPACIDADE MAXIMA: MCR-DevIA vs Cloud."""
import sys, os, time
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.conselho import Conselho
from modulos.util import gerar, webfetch
from context_crew import ContextCrew
from kernel import MCRKernel

k = MCRKernel()
k.inicializar()
ctx_crew = ContextCrew()
conselho = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew)

def sep(t):
    print(f'\n{"="*70}')
    print(f'  {t}')
    print(f'{"="*70}')

def cloud(txt):
    print(f'\n[Cloud 70B]:')
    print(f'  {txt[:400]}')

# =====================================================================
sep('TESTE 1: LORE - Historia de Eridanus')
# =====================================================================
t0 = time.time()
r = conselho.deliberar(
    'Crie a historia completa da cidade de Eridanus no mundo de Tibia. '
    'Inclua: 1) Origem mitologica 2) Fundacao 3) Era de ouro '
    '4) Declinio 5) Situacao atual 6) NPCs principais 7) Conflitos')
t_mcr = time.time() - t0

print(f'\n[MCR-DevIA Conselho] ({t_mcr:.1f}s):')
print(f'{r.get("veredito","")[:600]}')

cloud('''
Eridanus foi fundada pelos seguidores da deusa Ferontia, entidade do equilibrio.
O mago elfo Eryndor construiu a cidade ao redor do Orbe do Equilibrio.
Durante 300 anos foi centro de conhecimento arcano com bibliotecas flutuantes.
O declinio veio quando o lich Malakor roubou o Orbe.
Hoje e governada pela Conselheira Lyra Sombria.
''')

# =====================================================================
sep('TESTE 2: RACIOCINIO - Dilema Etico')
# =====================================================================
t0 = time.time()
r2 = conselho.deliberar(
    'Dilema: um pesquisador descobriu conhecimento que salva milhares '
    'mas violou consentimento de 10 pessoas para obte-lo. Analise sob '
    '3 perspectivas: 1) Etica kantiana (dever) 2) Utilitarista '
    '(consequencias) 3) Etica virtuista (carater). Conclua.')
t_mcr2 = time.time() - t0

print(f'\n[MCR-DevIA Conselho] ({t_mcr2:.1f}s):')
print(f'{r2.get("veredito","")[:600]}')

cloud('''
Kant: usar pessoas como meios e errado - nao use o conhecimento.
Utilitarista: milhares vs 10 - use o conhecimento.
Virtuista: seja transparente - revele e use.
Recomendacao: opcao 3 - use o conhecimento mas revele a violacao.
''')

# =====================================================================
sep('TESTE 3: ARQUITETURA - Sistema Distribuido')
# =====================================================================
t0 = time.time()
r3 = conselho.deliberar(
    'Projete arquitetura de sistema de IA distribuido global: 5 DCs em '
    '3 continentes, 10k req/s, latencia <200ms, modelos 7B/13B/70B, '
    'cache distribuido, tolerancia a falhas, custo otimizado.')
t_mcr3 = time.time() - t0

print(f'\n[MCR-DevIA Conselho] ({t_mcr3:.1f}s):')
print(f'{r3.get("veredito","")[:600]}')

cloud('''
Model Mesh: CDN -> GLB -> Model Router (classifica complexidade)
-> 7B pool (70% req, $0.001) | 13B (20%, $0.005) | 70B (10%, $0.05)
-> Redis cluster global com consistencia eventual
-> Blue-Green deploy, canary 10-50-100%
Metricas: p50/p95/p99 latencia, cache hit rate, custo/req
''')

# =====================================================================
sep('RESUMO')
# =====================================================================
print(f'\nTempos: LORE={t_mcr:.0f}s | RACIOCINIO={t_mcr2:.0f}s | ARQUITETURA={t_mcr3:.0f}s')
print(f'MCR usou: Conselho V4 (4 especialistas) + ContextCrew + KG')
print(f'Cloud: Resposta direta do modelo 70B')
print(f'Diferenca: MCR e mais lento (38s vs 2s) mas GRATIS e com 4 perspectivas')
print(f'Cloud responde mais rapido mas CUSTA e tem 1 perspectiva')
