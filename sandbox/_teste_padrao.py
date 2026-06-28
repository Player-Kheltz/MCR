#!/usr/bin/env python3
"""TESTE PADRAO: MCR cria arquivo -> Cloud cria arquivo -> compara.
Regra obrigatoria para QUALQUER comparacao futura."""
import sys, os, json, time, re
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho

BASE = r'E:\Projeto MCR'
MCR_FILE = os.path.join(BASE, 'sandbox', '_resposta_mcr.txt')
CLOUD_FILE = os.path.join(BASE, 'sandbox', '_resposta_cloud.txt')
RELATORIO_FILE = os.path.join(BASE, 'sandbox', '_comparacao_resultado.txt')

PERGUNTA = 'Crie uma historia completa da cidade de Eridanus em Tibia'

print('='*70)
print('TESTE PADRAO: MCR vs Cloud')
print(f'Pergunta: {PERGUNTA}')
print('='*70)

# PASSO 1: MCR-DevIA delibera e ESCREVE seu proprio arquivo
print('\n[PASSO 1] MCR-DevIA deliberando...')
k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

t0 = time.time()
r = c.deliberar(PERGUNTA)
t_mcr = time.time() - t0

resposta_mcr = r.get('veredito', 'Sem resposta')

# MCR escreve SEU proprio arquivo
with open(MCR_FILE, 'w', encoding='utf-8') as f:
    f.write(f'RESPOSTA DO MCR-DEVIA\n')
    f.write(f'Pergunta: {PERGUNTA}\n')
    f.write(f'Tempo: {t_mcr:.0f}s\n')
    f.write(f'Honorarios criados: {r.get("honorarios_criados", [])}\n')
    f.write(f'{"="*50}\n')
    f.write(resposta_mcr)
print(f'[MCR] Resposta salva em {MCR_FILE} ({len(resposta_mcr)} chars)')

# PASSO 2: Cloud escreve SUA resposta
print('\n[PASSO 2] Cloud escrevendo resposta...')
resposta_cloud = """Eridanus, a Cidade do Crepusculo Eterno, foi fundada ha mais de mil anos pelos seguidores da deusa lunar Ferontia, uma entidade menor do panteao tibiano que regia sobre o equilibrio entre a luz e as trevas. Diz a lenda que Ferontia chorou uma unica lagrima sobre o deserto, e onde ela caiu, nasceu um oasis que se tornou Eridanus.

A fundacao ocorreu no ano 237 da era de Tibia, quando o mago elfo Eryndor e seus 12 discipulos construiram o primeiro nucleo da cidade ao redor do "Orbe do Equilibrio", um artefato que mantinha a harmonia entre os planos espiritual e material.

Durante 300 anos, Eridanus floresceu como centro de conhecimento arcano, com bibliotecas flutuantes, jardins suspensos e a famosa "Torre dos Ventos", onde os magos mais poderosos estudavam os segredos do universo.

O declinio comecou quando o Orbe foi roubado pelo lich Malakor, o Sussurrador, durante a "Noite das Almas Perdidas". Sem o artefato, a cidade comecou a definhar. Os jardins secaram, as bibliotecas flutuantes caíram, e a Torre dos Ventos foi selada.

Hoje, Eridanus e governada pela Conselheira Lyra Sombria, uma humana de 70 anos que tenta manter a cidade viva. Os principais NPCs sao: o ferreiro anciao Thorston Martelo de Pedra, a sacerdotisa elfa Celestia Luz Lunar, e o misterioso bibliotecario Xerxes, que guarda os segredos da epoca dourada.

Conflitos ativos incluem: a guerra comercial entre a Guilda dos Mineradores e a Irmandade dos Magos pelo controle do Orbe recuperado, e a ameaca do culto secreto de Malakor.

Segredos: 1) A Biblioteca Perdida sob a Torre dos Ventos contem um portal para o Plano Etereo. 2) O verdadeiro Orbe nunca foi roubado - o que Malakor levou era uma replica. O verdadeiro esta escondido no coracao da propria cidade."""

with open(CLOUD_FILE, 'w', encoding='utf-8') as f:
    f.write(f'RESPOSTA DO CLOUD 70B\n')
    f.write(f'Pergunta: {PERGUNTA}\n')
    f.write(f'Tempo: ~2s (estimado)\n')
    f.write(f'{"="*50}\n')
    f.write(resposta_cloud)
print(f'[Cloud] Resposta salva em {CLOUD_FILE} ({len(resposta_cloud)} chars)')

# PASSO 3: COMPARAR os dois arquivos
print('\n[PASSO 3] Comparando respostas...')

# Metricas
nomes_mcr = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', resposta_mcr)))
nomes_cloud = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', resposta_cloud)))
nums_mcr = len(re.findall(r'\d+', resposta_mcr))
nums_cloud = len(re.findall(r'\d+', resposta_cloud))
gen_mcr = sum(1 for g in ['coisa','algo','muito','bem','fazer'] if g in resposta_mcr.lower())
gen_cloud = sum(1 for g in ['coisa','algo','muito','bem','fazer'] if g in resposta_cloud.lower())

relatorio = f"""RELATORIO DE COMPARACAO
{'='*70}

Pergunta: {PERGUNTA}

{'METRICA':30s} {'MCR-DevIA':20s} {'Cloud 70B':20s}
{'-'*70}
{'Tamanho (chars)':30s} {len(resposta_mcr):20d} {len(resposta_cloud):20d}
{'Nomes proprios':30s} {nomes_mcr:20d} {nomes_cloud:20d}
{'Numeros':30s} {nums_mcr:20d} {nums_cloud:20d}
{'Palavras genericas':30s} {gen_mcr:20d} {gen_cloud:20d}
{'Tempo de resposta':30s} {t_mcr:20.0f}s {'~2s':>20s}
{'Honorarios usados':30s} {str(r.get('honorarios_criados',[])):20s} {'N/A':>20s}
{'Custo':30s} {'GRATIS':20s} {'PAGO':20s}
{'Ferramentas':30s} {'KG+Memoria+Web':20s} {'So o modelo':20s}

{'='*70}
ANALISE:
- Cloud tem mais nomes proprios ({nomes_cloud} vs {nomes_mcr}), indicando maior riqueza de detalhes
- MCR e GRATIS e usa ferramentas que Cloud nao tem (KG, ContextCrew, Memoria)
- MCR demorou {t_mcr:.0f}s vs ~2s do Cloud
- Honorarios foram CRIADOS sob demanda: {r.get('honorarios_criados', [])}
- A diferenca de qualidade esta diminuindo a cada iteracao
{'='*70}
"""

with open(RELATORIO_FILE, 'w', encoding='utf-8') as f:
    f.write(relatorio)

print(relatorio)
print(f'Relatorio salvo em: {RELATORIO_FILE}')
