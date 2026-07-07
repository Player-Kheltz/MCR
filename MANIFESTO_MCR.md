# MANIFESTO MCR-DevIA
**Status do Ecossistema:** 7 FASES CONCLUIDAS — Organismo Operacional
**Hardware:** Ryzen 7 5800X3D | 32GB RAM | RTX 3080
**Inicializacao:** `python start_mcr_organism.py`

## 1. Ativos em Producao (14 Modulos mcr/)

### Nucleo
- `mcr/paths.py` — 27 constantes de caminho centralizadas
- `mcr/encoding.py` — Leitura/escrita com encoding por extensao (.lua=Latin-1, resto=UTF-8)

### FASE 1 — PatternMiner (AST -> KG)
- `mcr/pattern_miner.py` — Mineracao de AST tree-sitter C++/Lua
- 2690 padroes no KG (1034 NPC + 1656 Monster)

### FASE 2 — Metacognicao (Gateway de Incerteza)
- `mcr/metacognicao.py` — Threshold 0.70: <70% bloqueia LLM
- Testado: NPC=0.87 APROVA, PvP=0.20 BLOQUEIA, Monster=0.71 APROVA

### FASE 3 — Auto-Curiosidade (Mente Inquieta)
- `mcr/meta_gap.py` — Detector de lacunas (8 detectadas: raid, house, imbuement, etc.)
- `mcr/auto_curiosidade.py` — Thread background de estudo autonomo

### FASE 4 — Validacao Empirica (Anti-Patterns)
- `mcr/anti_pattern.py` — Classifica erros + registra no KG
- `mcr/logwatcher_bridge.py` — Ponte LogWatcher -> Anti-Patterns
- `mcr/anti_pattern_injector.py` — Injeta anti-patterns no prompt LLM

### FASE 5 — Shadow Canary (Mock Lua)
- `mcr/shadow_canary.py` — Ambiente mock de execucao Lua sem servidor

### FASE 6 — Motor de Criatividade ("E se...?")
- `mcr/emergir.py` — Ciclo: gerar ideia -> LLM -> validar -> promover
- `mcr/sanity_validator.py` — 512 APIs base + KG

### FASE 7 — Caminho Druida (NPC Server)
- `mcr/npc_sanity_filter.py` — Filtro de respostas (200 chars, sem codigo)
- `mcr/npc_server.py` — Servidor TCP :7777 para dialogos NPC
- `mcr/dialogue_miner.py` — Extracao de falas de NPCs .lua
- `mcr/dialogue_trainer.py` — Treinamento MCR com dialogos reais
- `mcr_npc_bridge.lua` — Bridge Canary -> Python Server

## 2. Hardcodes Mapeados para Eliminacao
- `_seeds_gerais` no `mcr_devia.py` -> Sera substituido por Auto-seeding
- `MODELO_POR_CLASSE` -> Sera substituido por dinamicismo
- `golden_examples/` -> Sera substituido por PatternMiner Dinamico
- Caminhos `E:\Projeto MCR\` -> **RESOLVIDO** via `mcr/paths.py`
- Encoding manual -> **RESOLVIDO** via `mcr/encoding.py`

## 3. Como Iniciar o Organismo

```bash
# Terminal unico: sobe tudo
python start_mcr_organism.py

# Terminal 2 (opcional): Pipeline de geracao de codigo
python devia/kernel/mcr_devia.py "Crie um NPC Guarda Real"

# Teste rapido do NPC Server
python -c "from mcr.npc_server import processar_dialogo; print(processar_dialogo({'npc_id':'Druida','player_id':'Kheltz','message':'Onde acho ervas?'}))"
```

O `start_mcr_organism.py` faz:
1. Carrega MCRSystem + KG
2. Treina 448 NPCs com 4529 dialogos
3. Inicia Auto-Curiosidade em background (ciclo 120s)
4. Sobe servidor socket TCP :7777
5. `Ctrl+C` desliga gracefulmente

## 4. Arquitetura do Sistema

```
+-------------------+       +------------------+       +------------------+
|   Markov Puro     | ----> |   KG (Memoria)   | ----> |   LLM (Geracao)  |
| (MCRPergunta)     |       | (KnowledgeGraph) |       | (qwen2.5-coder)  |
| 0.007s, zero GPU  |       | Lessons + Padroes |       | ~30s, RTX 3080   |
+-------------------+       +------------------+       +------------------+
         |                          |                          |
         v                          v                          v
+---------------------------------------------------------------+
|                    MasterAgent (Orquestrador)                  |
|  PERCEBER -> PLANEJAR -> EXECUTAR -> INTEGRAR -> APRENDER    |
+---------------------------------------------------------------+
         |                          |                          |
         v                          v                          v
+-------------------+       +------------------+       +------------------+
|   LuaValidator    |       |  Shadow Canary   |       |  NPC Server      |
| (Sintaxe + API)   |       | (Mock Lua)       |       | (TCP :7777)      |
+-------------------+       +------------------+       +------------------+
```

## 5. Metricas de Performance

| Operacao | Tempo | GPU | Descricao |
|----------|-------|-----|-----------|
| Pergunta conceitual (KG) | 0.007s | 0% | Markov puro, sem LLM |
| Dialogo NPC | <0.001s | 0% | MCR treinado com 4529 falas |
| Geracao de NPC | ~25s | 100% | LLM + Golden Example |
| Geracao de sistema | ~33s | 100% | MasterAgent + LLM |
| Validacao Lua | <0.1s | 0% | Sandbox + loadstring |
| Mineracao 1027 NPCs | 2.0s | 0% | Tree-sitter AST (5800X3D) |
| 100 req NPC Server | 100ms | 0% | <1ms cada, 0% GPU |
| Resposta NPC (rede) | <1ms | 0% | Socket local + MCR puro |
