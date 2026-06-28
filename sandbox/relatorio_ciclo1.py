"""Relatorio final do Auto-Teste Ciclo 1."""
import json

path = r'E:/Projeto MCR/sandbox/autoteste_historico.json'
with open(path, 'r', encoding='utf-8') as f:
    h = json.load(f)

testes = h['ciclos'][0]['testes']

print('=' * 60)
print('  RELATORIO FINAL - AUTO-TESTE CICLO 1')
print('  Data: 28/06/2026')
print('=' * 60)
print()
print('--- PLACAR: Cloud vs MCR-DevIA ---')
print()

total_cloud = 0
total_mcr = 0
for i, t in enumerate(testes):
    cloud_n = t['cloud_nota']
    mcr_n = t['auto_critica']['nota']
    gap = t['gap']
    vencedor = 'Cloud' if cloud_n > mcr_n else ('MCR' if mcr_n > cloud_n else 'Empate')
    if cloud_n > mcr_n:
        total_cloud += 1
    elif mcr_n > cloud_n:
        total_mcr += 1
    
    alerta = ' [PONTO CEGO]' if gap > 2 else ''
    print(f'  {t["categoria"]:15s}  Cloud:{cloud_n}  MCR:{mcr_n}  Gap:{gap}{alerta}')
    print(f'    Cloud: {cloud_n}/10 | MCR: {mcr_n}/10 | Vencedor: {vencedor}')
    print()

print(f'  VITORIAS: Cloud {total_cloud} x MCR {total_mcr}')
print()

print('--- GAPS (auto-nota MCR vs Cloud-nota) ---')
gaps = [t['gap'] for t in testes]
print(f'  Gap medio: {sum(gaps)/len(gaps):.1f}')
print(f'  Pontos cegos (gap > 2): {len([g for g in gaps if g > 2])} de {len(gaps)}')
print()

print('--- PRINCIPAL DESCOBERTA ---')
print('''
  O pipeline do MCR-DevIA forcou contexto MCR em TODAS as perguntas,
  mesmo quando a pergunta era de CONHECIMENTO GERAL (relatividade,
  mudancas climaticas, vocabulario cientifico).
  
  Causa raiz: CR + Enricher + ContextCrew assumem que TODA pergunta
  e sobre o MCR. Nao ha um "modo geral" ou deteccao de escopo.
  
  Impacto: Respostas 4 e 5 foram completamente off-topic (nota 0).
  Respostas 1-3 estavam corretas no conteudo mas com framing MCR
  inadequado, reduzindo a nota.
''')

print('--- RECOMENDACOES ---')
print('''
  1. [ALTA] Adicionar deteccao de escopo no CR: se pergunta nao
     contiver termos MCR, NAO injetar contexto MCR.
  2. [ALTA] Criar modo "conhecimento geral" no pipeline que busca
     weblearn em vez de ContextCrew quando o assunto nao for MCR.
  3. [MEDIA] Auto-Revisor deve detectar quando resposta forcou
     contexto MCR em pergunta geral e marcar como alucinacao.
  4. [BAIXA] Pergunta 4 (data/hora) sugere bug no pipeline -
     investigar porque respondeu com timestamp.
''')

print('=' * 60)
