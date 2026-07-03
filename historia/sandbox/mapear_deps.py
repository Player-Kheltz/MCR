#!/usr/bin/env python3
"""Mapear todas as dependencias externas do MCR.py."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('scripts/mcr_devia/modulos/MCR.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== 1. TODAS AS IMPORTACOES ===')
for line in content.split('\n'):
    if line.startswith('import ') or line.startswith('from '):
        print(f'  {line.strip()}')

print()
print('=== 2. REFERENCIAS A CLASSES EXTERNAS ===')
classes = re.findall(r'(?:MCR[A-Z]\w+|KnowledgeGraph|PatternEngine|IntentionEngine|PiEngine|ToolOrchestrator|EMERGIR|AutoTrigger|Supervisor|EpisodicMemory|ContextEnricher|AprendizDePadroes|AutoRevisor|BlankFiller|Reconstructor|Orquestrador|PiEngine|Emergir|MCRAutoLoop|MCRPergunta|MCRConector|MCRCadeia|MCRFilosofia|MCRFeedback|MCRDiagnostico|MCRThreshold|MCRPeso|MCREntropia|MCRRuido|MCRDecisor|MCRFerramenta|MCRBridge|MCRKGAuto|MCRExpansao|MCRMeta|MCRWorker|MCRSpawner|MCRMestre|MCRAutoStart|MCRPesoNota|MCRFuel|MCRMetaGap|MCRMestreV2|AutoavaliadorSemantico|GeradorNarrativa|MCRPreCache)', content)
print('  Classes encontradas:', len(set(classes)))

print()
print('=== 3. REFERENCIAS A MODULOS EXTERNOS ===')
modulos_refs = re.findall(r'(?:from\s+modulos\.\w+|import\s+modulos\.\w+)', content)
for r in set(modulos_refs):
    print(f'  {r}')

print()
print('=== 4. CADEIA DE DEPENDENCIAS (o que MCR.py chama fora) ===')
# MCR.py importa de:
# - modulos.pattern_engine
# - modulos.kg
# - modulos.tool_orchestrator
# - modulos.intention_engine (lazy import)
# - modulos.emergir (EMERGIR)
# - modulos.auto_trigger (AutoTriggerSystem)
# - modulos.MCR (si mesmo - só classes internas)

print('''
MCR.py chama EXTERNAMENTE:
  pattern_engine.PatternEngine     → tokenizacao
  kg.KnowledgeGraph                → conhecimento
  tool_orchestrator.ToolOrchestrator → ferramentas
  intention_engine.IntentionEngine → intencao (lazy)
  emergir.EMERGIR                  → padroes emergentes
  auto_trigger.AutoTriggerSystem   → acoes (lazy)

Destes, quais PODEM ser incluidos no MCR.py?
  pattern_engine:  880 linhas → PAL_* hardcode (substituivel por MCR)
  kg.py:           584 linhas → core (substituivel por MCRBufferKG)
  tool_orchestrator: 1055 linhas → grande, mas MCRFerramenta ja existe
  intention_engine: 320 linhas → MCR.detectar_mcr() ja existe
  emergir:         368 linhas → MCRConector ja faz
  auto_trigger:    398 linhas → MCR path ja existe
''')

print('=== 5. RESUMO ===')
print(f'Total de linhas em MCR.py: {len(content.split(chr(10)))}')
print('Classes internas: ~37')
print('Dependencias externas: 6 modulos (~3605 linhas)')
print('Potencial de internalizacao: 5/6 modulos (MCR ja tem substitutos)')
