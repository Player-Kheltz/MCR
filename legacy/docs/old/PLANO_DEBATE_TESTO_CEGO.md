# Plano: Debate + Teste Cego — Cloud vs MCR-DevIA
# Salvo para uso futuro. Mesmo conceito, qualquer tema.

## Estrutura
"""
FASE 1: AQUECIMENTO (3 rounds de debate)
  → Cloud e MCR discutem um tema técnico
  → Sem teste cego ainda — apenas para aquecer

FASE 2: PROPOSTA DE TESTE CEGO (Cloud propõe)
  → "MCR, que tal testarmos quem responde melhor?"
  → Plano criado JUNTOS

FASE 3: EXECUÇÃO DO TESTE CEGO (3 perguntas)
  → MCR responde primeiro (sem ler resposta do Cloud)
  → Cloud responde (sem ler resposta do MCR)
  → Só então compara

FASE 4: JULGAMENTO E RESULTADO
  → Você julga qual resposta é melhor em cada rodada
  → Relatório final
"""

## Arquivos de suporte
"""
sandbox/.mcr_debate_progress.json  → Status de cada etapa
sandbox/.mcr_debate_perguntas.json → 3 perguntas do teste cego
respostas_mcr/p1.txt               → Resposta do MCR pergunta 1
respostas_cloud/p1.txt             → Resposta do Cloud pergunta 1
"""

## Anti-timeout
"""
Cada etapa = comando independente < 60s
Feedback via leitura de .mcr_debate_progress.json
User acompanha em tempo real
"""

## Critérios de julgamento
"""
Precisão (40%): A resposta está correta tecnicamente?
Clareza (30%): É clara, organizada, fácil de entender?
Completude (30%): Cobre todos os aspectos importantes?
"""
