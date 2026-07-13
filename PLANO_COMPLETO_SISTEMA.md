# PLANO COMPLETO DO SISTEMA MCR-DevIA (Estado Atual)

## VISÃO GERAL

```
E:\MCR\ (raiz)
├── mcr/           (89 files, ~22,000 linhas) — Implementações do sistema
├── devia/         (177 files, ~38,400 linhas) — Lógica de negócio + kernel
├── prototypes/    (4 dirs) — mcr-universal (backend Markov)
├── server/        (Canary OTServ) — Dados de jogo
├── tests/         (33 files) — Testes ad-hoc
├── scripts/       (17 files) — Scripts auxiliares
├── cache/         (~137 entries) — Dados em cache
├── legacy/        (2 dirs) — Código legado
├── sandbox/       (2 files) — Dados temporários
└── 43 .py files soltos na raiz — Scripts de teste/debug
```

**Total: 399 arquivos Python, ~74,000 linhas de código**

---

## ARQUITETURA: 3 PIPELINES, 5 ENTRY POINTS

### Entry Points

| Entry Point | Porta | Pipeline | Uso |
|-------------|-------|----------|-----|
| `sse_server.py` | :8765 | PipelineCompleto | Web dashboard + REST API |
| `npc_server.py` | :7777 | MCRSystem + DialogueTrainer | Diálogo NPC em tempo real |
| `mcr_conversa.py` | — | mcr_devia.processar() | Conversa interativa |
| `MCR.py` (root) | — | Re-exporta MCR_legacy | Shim de compatibilidade |
| `adaptadores.py` | — | PipelineConectado + MCRMentePura | Pipeline principal |

### Pipeline 1: PipelineCompleto (`mcr/pipeline_completo.py`)

```
Entrada → MarkovDecider.classificar() → HybridRouter.decidir_rota()
  ├─ MCR: CacheHierarquico → _verificar_existente() → _injetar_contexto() → GeradorMultinivel
  └─ LLM: Ensemble7B / Ollama
→ ChainOfVerification.verificar() → MCRGuardrail.validar()
  └─ Se rejeitado: MCRSelfHeal.curar() → retry
→ _canonizar() (salva em world_state + chronicle)
→ Background: MCRAutoLoop + MCRRadar + MCRPesoNota + FeedbackFilter
```

**Dependências mcr_universal:** MCRAutoLoop, MCRRadar, MCRPesoNota, MCRSelfHeal, MCRGuardrail
**Dependências devia:** MarkovDecider, raw_token_set, FeedbackFilter
**Funciona sem LLM?** PARCIALMENTE — rota MCR gera sem LLM, mas fallback usa Ollama

### Pipeline 2: PipelineConectado (`mcr/adaptadores.py`)

```
Entrada → MCRMentePura.pensar() (5 MCRs independentes):
  1. percepcao:  P(tipo | fingerprint) — via MCRSignatureExpansiva
  2. decompor:   P(proxima_tarefa | tipo)
  3. executar:   P(ferramenta | tarefa) → executor_map
  4. avaliar:    P(nota | resultado)
  5. aprender:   cada step alimenta seu próprio MCR
→ InternalMonologue (texto cognitivo)
→ MCRAutoMelhoria (aprendizado)
→ Fallback: MCRDevIARevived (LLM, só se nota < 0.3)
```

**Dependências mcr_universal:** MCRSignatureExpansiva, MCRMotor
**Dependências devia:** 20+ módulos de kernel (MCR engine, evolution, memory, signature, decisor, meta, system, hdc_core, sdm_core, intention_engine)
**Funciona sem LLM?** SIM — totalmente Markov

### Pipeline 3: NPC Server (`mcr/npc_server.py`)

```
Entrada (TCP JSON) → DialogueTrainer.gerar_resposta()
  → MCRSystem.mk_palavra.predizer() (Markov palavra-a-palavra)
  → MCRSystem.kg.buscar() (episodic memory)
  → EpisodicMemory.registrar()
  → npc_sanity_filter()
→ Resposta JSON
```

**Funciona sem LLM?** SIM — totalmente Markov + diálogos treinados

### Pipeline 4: MCRUnificado (`mcr/mcr_unificado.py`)

```
Entrada → regex classificar() → roteador:
  saudacao → conversa
  criar_npc → NPCCriativo
  criar_codigo → GeradorCodigo
  criar_ideia → EmergirUnificado
  raciocinio → Raciocinador
  analise → análise
```

**Funciona sem LLM?** SIM — todos sub-módulos são Markov

---

## O QUE FUNCIONA (sem LLM)

| Módulo | Arquivo | Status |
|--------|---------|--------|
| MCR Engine | `devia/kernel/mcr_kernel/engine.py` (430L) | ✅ |
| MCRSignatureExpansiva | `prototypes/mcr_universal/core/signature.py` | ✅ |
| MCRMotor | `prototypes/mcr_universal/emergence/motor.py` | ✅ |
| MCRHybridClassifier | `prototypes/mcr_universal/hybrid/classifier.py` | ✅ |
| MCRGuardrail | `prototypes/mcr_universal/hybrid/guardrail.py` | ✅ |
| MCRAutoLoop | `prototypes/mcr_universal/emergence/auto_loop.py` | ✅ |
| MCRRadar | `prototypes/mcr_universal/intelligence/radar.py` | ✅ |
| MCRPesoNota | `prototypes/mcr_universal/feedback/peso_nota.py` | ✅ |
| MCRSelfHeal | `prototypes/mcr_universal/feedback/self_heal.py` | ✅ |
| MCRThreshold | `prototypes/mcr_universal/core/threshold.py` | ✅ |
| MCRBuffer | `prototypes/mcr_universal/core/buffer.py` | ✅ |
| MCREntropia | `prototypes/mcr_universal/core/entropia.py` | ✅ |
| MCRSession | `prototypes/mcr_universal/core/session.py` | ✅ |
| MCRFragmentador | `prototypes/mcr_universal/core/fragmento.py` | ✅ |
| MCRByteUtils | `prototypes/mcr_universal/core/byte_utils.py` | ✅ |
| MCRMentePura | `mcr/mcr_mente_pura.py` (411L) | ✅ |
| MCRMente | `mcr/mcr_mente.py` (339L) | ✅ |
| HybridRouter | `mcr/hybrid_router.py` (69L) | ✅ |
| ChainOfVerification | `mcr/chain_of_verification.py` (218L) | ✅ |
| CacheHierarquico | `mcr/cache_hierarquico.py` (173L) | ✅ |
| MarkovDecider | `devia/kernel/mcr_devia_v2.py` (716L) | ✅ |
| MarkovRouter | `devia/kernel/MarkovRouter.py` (151L) | ✅ |
| IntentionEngine | `devia/modules/intention_engine.py` (354L) | ✅ |
| PatternEngine | `devia/modules/pattern_engine.py` (902L) | ✅ |
| KnowledgeGraph | `devia/knowledge/kg.py` (500L) | ✅ |
| CanaryIndexer | `devia/knowledge/canary_indexer.py` (540L) | ✅ |
| EpisodicMemory | `devia/knowledge/episodic_memory.py` (356L) | ✅ |
| ItemDatabase | `devia/knowledge/item_database.py` (446L) | ✅ |
| ToolRegistry | `devia/knowledge/tool_registry.py` (642L) | ✅ |
| PatternMiner | `mcr/pattern_miner.py` (312L) | ✅ |
| GoldenTemplates | `mcr/golden_templates.py` (172L) | ✅ |
| MCREntityFactory | `mcr/mcr_entity_factory.py` (265L) | ✅ |
| MCRWorldSystem | `mcr/mcr_world_system.py` (718L) | ✅ |
| MCRWorldBuilder | `mcr/mcr_world_builder.py` (1,371L) | ✅ |
| MCRWorldFoundation | `mcr/mcr_world_foundation.py` (439L) | ✅ |
| MCRSpriteMotor | `mcr/mcr_sprite_motor.py` (349L) | ✅ |
| MCRSpriteUniversal | `mcr/mcr_sprite_universal.py` (368L) | ✅ |
| SpriteCorpus | `mcr/sprite_corpus.py` (391L) | ✅ |
| DialogueTrainer | `mcr/dialogue_trainer.py` (155L) | ✅ |
| DialogueMiner | `mcr/dialogue_miner.py` (101L) | ✅ |
| AntiPattern | `mcr/anti_pattern.py` (147L) | ✅ |
| SanityValidator | `mcr/sanity_validator.py` (300L) | ✅ |
| SanityValidatorCS | `mcr/sanity_validator_cs.py` (497L) | ✅ |
| SanityValidatorCPP | `mcr/sanity_validator_cpp.py` (246L) | ✅ |
| SanityValidatorSQL | `mcr/sanity_validator_sql.py` (264L) | ✅ |
| ShadowCanary | `mcr/shadow_canary.py` (375L) | ✅ |
| AutoCuriosidade | `mcr/auto_curiosidade.py` (108L) | ✅ |
| AutoEvolution | `mcr/mcr_auto_evolution.py` (139L) | ✅ |
| Metacognicao | `mcr/metacognicao.py` (237L) | ✅ |
| ExecutorMap | `mcr/executor_map.py` (300L) | ✅ |
| Encoding | `mcr/encoding.py` (129L) | ✅ |
| Cielab | `mcr/cielab.py` (208L) | ✅ |
| Paths | `mcr/paths.py` (69L) | ✅ |
| SignatureCluster | `mcr/mcr_signature_cluster.py` (322L) | ✅ |
| TokenizadorHierarquico | `mcr/tokenizador_hierarquico.py` (460L) | ✅ |
| TemplateEntropico | `mcr/template_entropico.py` (126L) | ✅ |
| TemplateRegiao | `mcr/template_regiao.py` (622L) | ✅ |
| RegioesAnatomicas | `mcr/regioes_anatomicas.py` (547L) | ✅ |
| DiscriminadorAnatomia | `mcr/discriminador_anatomia.py` (180L) | ✅ |
| MeusOlhos | `mcr/meus_olhos.py` (97L) | ✅ |
| OlhosMCR | `mcr/olhos_mcr.py` (242L) | ✅ |
| VisualCoupling | `mcr/visual_coupling.py` (174L) | ✅ |
| WorldAnomalyDetector | `mcr/world_anomaly_detector.py` (247L) | ✅ |
| WorldObserver | `mcr/world_observer.py` (256L) | ✅ |
| MCRMeta | `mcr/mcr_meta.py` (188L) | ✅ |
| MCRSelf | `mcr/mcr_self.py` (75L) | ✅ |
| MCRAutobiography | `mcr/mcr_autobiography.py` (87L) | ✅ |
| MCRConversa | `mcr/mcr_conversa.py` (113L) | ✅ |
| MCRInnerVoice | `mcr/mcr_inner_voice.py` (132L) | ✅ |
| MCRSqlite | `mcr/mcr_sqlite.py` (263L) | ✅ |
| SQLiteMarkov | `mcr/sqlite_markov.py` (229L) | ✅ |
| EquacaoMCR | `mcr/equacao_mcr.py` (78L) | ✅ |
| CognitiveDecomposer | `mcr/cognitive_decomposer.py` (74L) | ✅ |
| DataInjector | `mcr/data_injector.py` (61L) | ✅ |
| GeneratorMultinivel | `mcr/generator_multinivel.py` (60L) | ✅ |
| GeradorCodigo | `mcr/gerador_codigo.py` (266L) | ✅ |
| PromptsCriativos | `mcr/prompts_criativos.py` (162L) | ✅ |
| BridgeAPI | `mcr/bridge_api.py` (288L) | ✅ |
| LogwatcherBridge | `mcr/logwatcher_bridge.py` (53L) | ✅ |
| SilentLog | `mcr/silent_log.py` (38L) | ✅ |
| Emergir | `mcr/emergir.py` (316L) | ✅ |
| EmergirCrossmodal | `mcr/emergir_crossmodal.py` (248L) | ✅ |
| EmergirUnificado | `mcr/emergir_unificado.py` (505L) | ✅ |
| NPCCriativo | `mcr/npc_criativo.py` (346L) | ✅ |
| NPCSanityFilter | `mcr/npc_sanity_filter.py` (89L) | ✅ |
| MCRideaToSpec | `mcr/mcr_idea_to_spec.py` (159L) | ✅ |
| Planejador | `mcr/planejador.py` (209L) | ✅ |
| Raciocinador | `mcr/raciocinador.py` (330L) | ✅ |
| Ensemble7B | `mcr/ensemble_7b.py` (154L) | ✅ |
| MCRWorldSeed | `mcr/mcr_world_seed.py` (90L) | ✅ |
| MCRWorldChronicle | `mcr/mcr_world_chronicle.py` (60L) | ✅ |
| MCRWorldState | `mcr/mcr_world_state.py` (75L) | ✅ |
| HDCKGMemory | `mcr/hdc_kg_memory.py` (93L) | ✅ |
| PipelineMCRSprite | `mcr/pipeline_mcr_sprite.py` (321L) | ✅ |
| PipelineUniversal | `mcr/pipeline_universal.py` (359L) | ✅ |
| MCRSpriteExtractor | `mcr/sprite_extractor.py` (173L) | ✅ |
| Dominios/* | `mcr/dominios/` (5 files, 177L) | ✅ |

**Total funcional sem LLM: 90+ módulos**

---

## O QUE PRECISA DE LLM (Ollama)

| Módulo | Arquivo | Modelo | Status |
|--------|---------|--------|--------|
| Ensemble7B | `mcr/ensemble_7b.py` | 3x 7B models | Votação multi-modelo |
| PipelineCompleto (rota LLM) | `mcr/pipeline_completo.py` | mistral:7b / qwen2.5-coder:7b | Fallback |
| sse_server `/api/chat` | `mcr/sse_server.py` | via PipelineCompleto | Streaming |
| sse_server `/api/chat-stream` | `mcr/sse_server.py` | Ollama streaming | Direct |
| ChainOfVerification.corrigir() | `mcr/chain_of_verification.py` | qwen2.5-coder:7b | Correção |
| MCRideaToSpec | `mcr/mcr_idea_to_spec.py` | — | Conversão |
| MCRWorldBuilder (lore) | `mcr/mcr_world_builder.py` | mistral:7b | Lore generation |
| MCRTarefa (LLM fallback) | `devia/kernel/mcr_kernel/evolution.py` | — | Fallback |
| MCRDevIARevived | `devia/kernel/fix_mcr_devia_v2.py` | — | Fallback PipelineConectado |
| Emergir.executar_ideia() | `devia/modules/emergir.py` | — | Ideia → código |
| InnerVoice (texto) | `mcr/mcr_inner_voice.py` | — | Texto de monólogo |
| mcr_conversa (diálogo) | `mcr/mcr_conversa.py` | mistral:7b | Respostas naturais |

**Total dependente de LLM: ~13 módulos** (todos com fallback Markov)

---

## O QUE ESTÁ DEIXADO DE FORA

### 1. devia/comandos/ — 52 COMANDOS CLI (4,752 linhas)

Sistema de comandos completo mas não integrado a nenhum pipeline.

### 2. devia/analysis/ — 5 MÓDULOS INDEPENDENTES (1,032 linhas)

| Módulo | Linhas | Status |
|--------|--------|--------|
| `fragmenter.py` | 360 | Self-contained, não conectado |
| `diagnostic_engine.py` | 249 | Self-contained, não conectado |
| `decider.py` | 181 | Self-contained, não conectado |
| `truncation_fixer.py` | 160 | Self-contained, não conectado |
| `diagnostico.py` | 78 | Self-contained, não conectado |

### 3. devia/kernel/ — 34 ARQUIVOS SOLtos (sem __init__.py)

~20 arquivos não conectados, ~8 conectados, sem `__init__.py`

### 4. 43 ARQUIVOS SOLtos NA RAIZ

Scripts de teste/debug que não são importados por ninguém.

### 5. DUPLICAÇÕES RESTANTES

| Classe | Localizações |
|--------|-------------|
| MCRSqlite + SQLiteMarkov | `mcr/mcr_sqlite.py` + `mcr/sqlite_markov.py` |
| MCRMente + MCRMentePura | `mcr/mcr_mente.py` + `mcr/mcr_mente_pura.py` |
| PromptCache | `devia/modules/orquestrador.py` + `devia/modules/conselho.py` |

### 6. INFRAESTRUTURA AUSENTE

- pytest/unittest framework
- CI/CD
- Logging estruturado
- Rate limiting
- Auth
- Type hints
- Docstrings

---

## CHECKLIST DE CORREÇÕES

### Fase 1: devia/kernel/ __init__.py
- [x] Criar `devia/kernel/__init__.py`

### Fase 2: Duplicatas restantes
- [x] Consolidar MCRSqlite + SQLiteMarkov (sqlite_markov.py agora wraps mcr_sqlite.py)
- [x] Consolidar PromptCache (conselho.py agora importa de orquestrador.py)

### Fase 3: Mover arquivos soltos da raiz
- [x] Mover 42 arquivos .py da raiz para tests/root_scripts/ (18), scripts/sprite_training/ (9), scripts/ (15)

### Fase 4: Limpar dead code em devia/kernel/
- [x] Deletar 15 arquivos UNUSED: CommandCapture, conexao_bridge, DeterministicFiller, encoding, EncodingDetector, fix_paths, ingest_canary, LuaSyntaxValidator, main_npc, MasterAgent, MCR.py (restaurado como wrapper), mundo_tibia, SeedLoader, self_calibrate, TemplateExtractor
- [x] Restaurar MCR.py como wrapper de compatibilidade (necessário para mcr_devia_v2.py)
- [x] 10 arquivos DYNAMIC_ONLY mantidos (referenciados por executor_map.py)

### Fase 5: Verificação final
- [x] Todos os 8 checks de import passam
- [x] mcr_universal: OK
- [x] mcr core: OK
- [x] devia.kernel.mcr_kernel: OK
- [x] devia.kernel modules: OK
- [x] consolidated duplicates: OK
- [x] devia.analysis re-exports: OK
- [x] pipeline modules: OK
- [x] devia.modulos wrapper: OK
