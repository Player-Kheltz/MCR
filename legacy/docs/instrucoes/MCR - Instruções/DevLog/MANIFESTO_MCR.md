# MANIFESTO DE CAPACIDADES — MCR-DevIA

**Data:** 07/07/2026 (Atualizado — Sessão MasterAgent + Indexador + Validator)
**Escopo:** `E:\MCR\` (72 .py) + `E:\Projeto MCR\historia\Scripts\mcr_devia\` (148 .py)
**Total:** ~220 módulos Python analisados
**Autor:** DeepSeek V4 + GLM 5.2 (Z.ia) — Engenharia reversa do ecossistema MCR-DevIA

---

## PARTE 1: E:\MCR\ (Workspace Ativo)

Arquivos construídos e integrados no PipelineExecutor.

| Arquivo | Classes/Funções | Descrição Funcional | Integrado? | Potencial Não Explorado |
|---------|----------------|---------------------|-----------|------------------------|
| **MCR.py** | `MCR`, `MCRConexao`, `MCRDecisorUniversal`, `MCRAutoEvolution`, `MCRCuriosidade`, `MCRGenesis`, `MCRKnowledgeGraph`, `MCRContextCrew`, `MCRConversa`, `MCRFileObserver`, etc. (~60 classes) | Motor Markov multi-nível completo: aprende, prediz, gera, auto-evolui. 243 testes passando | **Parcial** (MCR, MCRByteUtils, MCRConexao, MCRDecisorUniversal usados) | `MCRGenesis` — detecta gaps de conhecimento automaticamente. `MCRCuriosidade` — explora o projeto sem supervisão. `MCRAutoEvolution` — calibra thresholds sozinho (precisa adaptar target do Attention → DevIA). `MCRFileObserver` — monitora arquivos sem polling (Windows API). |
| **mcr_devia.py** | `processar()`, `main()` | Entry point: conecta MCR.py + MarkovDecider + 52 comandos + LLM (Ollama). 12.000+ seeds | **Sim** | — |
| **mcr_devia_v2.py** | `MarkovDecider`, `EntropyValidator`, `LLM`, `MCRDevIAV2`, `NoLLMQA` | Markov decide em 0.01ms, LLM gera em ~5s | **Sim** | `NoLLMQA` — QA sem LLM. Não usado no pipeline (substituído pelo MarkovDecider). |
| **PipelineExecutor.py** | `PipelineExecutor`, `CommandCapture`, `_dedup_resposta` | Orquestra pipeline de comandos com captura, parse e contexto compartilhado | **Sim** | — |
| **MarkovRouter.py** | `MarkovRouter` | Roteia estado → pipeline de ações em 10µs. 26 rotas bootstrap | **Sim** | `MCRDecisorUniversal` poderia gerar rotas automaticamente por entropia, removendo seeds manuais. |
| **Radar.py** | `Radar` | Detecta loops de ação (4x mesma ação → força alternativa) | **Sim** | — |
| **TemplateExtractor.py** | `extrair_template()`, `extrair_template_multi()` | Extrai esqueleto estrutural de código | **Sim** | `extrair_template_multi()` (múltiplos arquivos) não usado. |
| **DeterministicFiller.py** | `preencher_template()`, `preencher_gap()` | Preenche gaps por mapeamento (domínio→cor, tipo→categoria) | **Sim** | Mapeamentos limitados a SPA. Não cobre NPCs ou quests. |
| **code_analyzer.py** | `analisar_arquivo()`, `analisar_diretorio()` | 16 padrões de bug via regex em 0ms | **Sim** | Só detecta padrões conhecidos. Não faz análise semântica. |
| **code_parser.py** | `CodeParser` | Parse .lua/.cpp/.cs via tree-sitter (AST: funções, classes, chamadas) | **Sim** | AST extraído mas não usado pelo code_analyzer nem TemplateExtractor. |
| **LuaSyntaxValidator.py** | `verificar_sintaxe()`, `validar_com_loop()` | Valida sintaxe Lua com loop auto-corretivo (até 3x, LLM corrige) | **Sim** | Só classes `criar_*`. Não cobre escrita direta via cmd_write. |
| **rag_mcr.py** | `MCRRAG` | RAG via ChromaDB + nomic-embed-text (Ollama). Busca híbrida: keywords + embedding | **Sim** | Busca híbrida funciona mas RAG não indexa código-fonte (só docs .md). |
| **conexao_bridge.py** | `CerebroKG` | Adapta KG do DevIA → MCRConexao (0ms, 0 LLM) | **Sim** | Só `--emergir`. Não alimenta EmergirEngine original do DevIA. |
| **FeedbackFilter.py** | `FeedbackFilter` | Filtra respostas inválidas antes de alimentar KG | **Sim** | — |
| **SeedLoader.py** | `carregar_tudo()` | Converte PERSONALIDADE.md → 174 seeds análise + 80 seeds critérios | **Sim** | Só PERSONALIDADE.md. Docs do Canary não carregados. |
| **AutorevisaoTracker.py** | `AutorevisaoTracker` | Gera autorevisão conforme PERSONALIDADE.md linha 502 | **Sim** | — |
| **EncodingDetector.py** | `detectar_encoding()` | Detecta encoding por extensão (.lua→latin1, .cpp→utf8) | **Sim** | — |
| **self_calibrate.py** | `calibrar()` | Ajusta thresholds a cada 50 interações (taxa de aceite) | **Sim** | Muito simples. Não usa MCRAutoEvolution. |
| **watchdog_mcr.py** | `WatchdogMCR` | Monitora mudanças no projeto (watchdog) | **Sim** | Callback não conectado ao pipeline. |
| **log_watcher.py** | `LogWatcher` | Monitora logs do Canary, detecta erros, invoca DevIA para diagnosticar | **Sim** | Verifica a cada 30s. Separado do watchdog. |
| **ingest_canary.py** | `indexar_diretorio_lua()` | Indexa scripts Canary no ChromaDB, chunking por função Lua | **Parcial** | Lento (~2s/chunk). Não indexa todos os diretórios. |
| **MCRCuriosidade** (MCR.py:4875) | `MCRCuriosidade` | Exploração autônoma: descobre drives, arquivos, padrões por entropia | **Não** | Exploraria código do projeto automaticamente em background. |
| **MCRGenesis** (MCR.py:2670) | `MCRGenesis` | Detecta gaps de conhecimento, gera esqueletos de código | **Não** | Quando router não encontra seed, Genesis poderia gerar rota automaticamente. |
| **MCRPlanner** (MCR.py:2299) | `MCRPlanner` | Decompõe tarefas complexas em sub-passos (grid 5x5) | **Não** | Poderia decompor "crie uma quest" em NPC → Action → Diálogo. |
| **MCRCoupling** (MCR.py:1384) | `MCRCoupling` | Pesos entre fontes de informação (KG ↔ Memória ↔ ContextCrew) | **Não** | Cross-source prediction quando KG falha. |
| **MCREsfera** (MCR.py:1433) | `MCREsfera` | Predição cruzada: consulta todas as fontes, retorna melhor predição | **Não** | Fallback universal quando nenhuma fonte individual tem resposta. |
| **HDC/SDM** (6 arquivos) | `HDVector`, `SDM`, `SDM_MDL`, `PercepcaoNPC`, `MCRNPCv2`, `RedeNPCs` | Hyper-dimensional Computing, Sparse Distributed Memory, NPC com personalidade e memória | **Não** | `SDM_MDL` — memória esparsa com detecção de novidade. `MCRNPCv2` — NPC com alma e personalidade. |
| **nichos/tibia/** (12 arquivos) | `SQLiteMarkov`, `MCRPipeline`, `gerador_*.py`, `extract_*.py` | Geração NPC/Monstro com distribuições reais do Canary (1656 monstros, 1034 NPCs) | **Não** | `SQLiteMarkov` — Markov com persistência SQLite. `gerador_hibrido.py` — combina dados reais + Markov criativo. `extract_npc/monster.py` — já extraíram 1656 monstros e 1034 NPCs em JSON. |

---

## PARTE 2: historia\Scripts\mcr_devia\ (DevIA Original — 148 módulos)

Módulos que existem mas NÃO estão integrados no PipelineExecutor.

### Knowledge & Memory

| Arquivo | Classe | O que faz | Potencial não explorado |
|---------|--------|-----------|------------------------|
| `knowledge/kg.py` | `KnowledgeGraph` | KG multi-arquivo com lazy loading. 788 lessons ativas | Import quebra (`stop_words`). Precisa de wrapper leve. |
| `knowledge/episodic_memory.py` | `EpisodicMemory` | Memória de episódios com busca híbrida (embedding + keyword) | **Prioridade #1.** Registra request+result+lesson. Cache L3 persistente. |
| `knowledge/blank_filler.py` | `BlankFiller` | Gera esqueletos @BLANK_N, preenche via IA | Nosso TemplateExtractor + Filler > este. Mantido como fallback. |
| `knowledge/canary_indexer.py` | `CanaryIndexer` | Indexa 1034 NPCs do Canary, extrai keywords, tipos, itens | **Nunca usado.** Indexaria NPCs reais para referência. |
| `knowledge/item_database.py` | `ItemDatabase` | Busca em items.xml por nome/ID/categoria (LRU cache) | **Nunca usado.** Valida IDs de itens contra items.xml real. |
| `knowledge/lessons_buffer.py` | `LessonsBuffer` | Buffer que acumula e faz flush em lote (100 items) | Mais eficiente que FeedbackFilter individual. |
| `knowledge/tool_registry.py` | `ToolRegistry` | Catálogo vivo de 30+ ferramentas com metadados | **Nunca usado.** Poderia substituir seeds estáticas do Router. |
| `knowledge/memoria_compactada.py` | `Memoria` | Memória com compressão gzip de entradas antigas | Complementaria `_CACHE_L1` que é volátil. |

### Context

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `context_crew.py` | 5 fontes paralelas: KG, WebLearn, Docs, Código, Web | Call `context_crew` no pipeline é no-op. Deveria carregar contexto real. |
| `context_infinity.py` | Orquestrador de contexto: fragmentos prioritários | Fragmentos com prioridade dinâmica. Não usado. |
| `context_enricher.py` | Cria conteúdo NOVO: lore, dados, curiosidades | Enriqueceria respostas com lore do servidor. |
| `context_reinforcer.py` | Valida relevância + weblearn fallback | Não usado. |

### Analysis

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `pattern_engine.py` | Tokenizador universal + fingerprint + eixo Nirvana-Caos | Tokenizador útil para pré-processamento. |
| `diagnostic_engine.py` | Auto-diagnóstico: compilação, except vazio, backups | **Não usado.** Diagnosticaria problemas nos módulos do DevIA. |
| `tree_of_thought.py` | 5 perspectivas paralelas + síntese | Substituído por prompt LLM. Mas útil para problemas complexos. |
| `validation.py` | Validação V1-V9: padrões, fatos, código, alucinações, completude | **Não usado.** 9 checkers > nosso EntropyValidator simples. |
| `decider.py` | Classificador universal + cache LRU + fallback determinístico | Substituído por MarkovDecider (0.01ms vs 3-8s). |
| `auto_revisor.py` | Revisor pós-geração: detecta classes alucinadas, corrige | Substituído por EntropyValidator. Detecção de classes alucinadas é útil. |
| `self_study.py` | Auto-estudo: escaneia código fonte, extrai métricas, gera insights | **Nunca usado.** Aprenderia sobre o próprio DevIA. |
| `truncation_fixer.py` | Remove `[:N]` de respostas | Já roda no kernel init. |

### Reasoning

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `conselho.py` | Conselho infinito 9 arquétipos | Substituído (5 LLM → 0 Markov). Mas útil para decisões complexas. |
| `intention_engine.py` | 3 camadas: Pattern → keyword → FAST | Substituído por MarkovDecider + keyword. |
| `pi_engine.py` | Predição zero-IA via Markov do KG | **Não usado.** Predição de padrões sem LLM. |
| `mente.py` | Sistema 1 (rápido) com cache LRU 5min | Não usado. |
| `memoria_conselho.py` | Memória individual por arquétipo (score 0-100) | Não usado. |

### Pipeline & Generation

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `task_planner.py` | Decompõe requests complexos em subtarefas | **Prioridade #4.** Decompor "crie quest" em NPC → Action → Diálogo. |
| `orquestrador.py` | Templates de alta qualidade + contexto injetado | Substituído por nosso pipeline. Templates são ricos. |
| `npc_generator.py` | NPC Lua com 6 tipos, templates reais + LLM | **Não usado.** Mais maduro que nosso TemplateExtractor para NPCs. |
| `emergir.py` | Motor "E se...?" com autoavaliação e expansão | Substituído por MCRConexao + conexao_bridge. Mas Emergir original tem autoavaliação. |
| `master_agent.py` | Ciclo PERCEBER→PLANEJAR→EXECUTAR→INTEGRAR→APRENDER | **Prioridade #10.** Substituiria o processo linear por ciclo completo. |

### Validation

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `lua_validator.py` (original) | Verifica sintaxe, SQL injection, NpcHandler, FocusModule, estrutura Canary | **Prioridade #2.** MUITO mais completo que nosso LuaSyntaxValidator. |
| `validation_pipeline.py` | 9 estágios V1-V9 | **Prioridade #3.** Substituiria EntropyValidator simples. |
| `pos_processamento.py` | Extrai blocos ```lua de respostas LLM | **Prioridade #6.** Extração automática de código. |
| `auto_repair.py` | Reparo single-attempt via FAST | Não usado. |

### Tools

| Arquivo | O que faz | Potencial |
|---------|-----------|-----------|
| `tool_orchestrator.py` | 30+ ferramentas executáveis | Nosso PipelineExecutor só lida com cmd_*. |
| `sandbox.py` | Execução isolada Python/Lua/Shell | Não usado. |
| `tradutor.py` | Tradução PT-BR via llama3.1:8b + cache | Nosso pipeline usa LLM genérico. |

### Commands (52)

Todos em `comandos/cmd_*.py`. Já corrigidos (encoding, BASE path). Carregados via `kernel.loader.scan()`.

55 comandos disponíveis: perguntar, gerar, lore, build, analisar, review, grep, read, write, edit, patch, conselho, master, task, plan, debate, penser, webfetch, weblearn, explorar, bugfinder, autoteste, etc.

---

## PARTE 3: TOP 10 Integrações Pendentes

Ordenado por impacto imediato no pipeline.

| # | Ferramenta | Localização | Status | Detalhes |
|---|-----------|-------------|--------|----------|
| **1** | `EpisodicMemory` | `knowledge/episodic_memory.py` | ✅ Em Produção | Cache L3 no `processar()`: busca semântica antes da pipeline, registra após sucesso. Persiste em `sandbox/.mcr_episodios.json`. |
| **2** | `lua_validator.py` (original) | `modulos/lua_validator.py` | ✅ Em Produção | Context-aware: detecta tipo (npc/action/spa/quest) automaticamente, valida estruturas específicas. Rejeita `action.uid = ` (deve ser `action:uid()`). Anti SQL injection. |
| **3** | `validation_pipeline.py` | `modulos/validation_pipeline.py` | ⚠️ Parcial | EntropyValidator ativo. Validation V1-V9 não integrado. |
| **4** | `task_planner.py` | `modulos/task_planner.py` | ✅ Em Produção | Integrado no `MasterAgent.executar()`: decompõe tarefas, executa pipeline com auto-correção (até 3 tentativas). |
| **5** | `canary_indexer.py` | `knowledge/canary_indexer.py` | ✅ Em Produção | 1028 NPCs indexados. 40 exemplos (5/tipo) no ChromaDB RAG. Script `alimentar_indexador.py` faz batch. |
| **6** | `pos_processamento.py` | `modulos/pos_processamento.py` | ✅ Em Produção | Extração multi-formato no `PipelineExecutor`: `--- ARQUIVO:` markers, ```lua blocks, `-- filename.lua` comments. Fallback para bloco único. Encoding Latin-1. |
| **7** | `tool_registry.py` | `knowledge/tool_registry.py` | ✅ Em Produção | Fallback no `MarkovRouter.decidir()`: quando nenhuma seed match, consulta `buscar_por_palavras_chave(classe)` e extrai pipeline. |
| **8** | `item_database.py` | `knowledge/item_database.py` | ✅ Em Produção | Validação de IDs `clientId`/`itemId` contra `items.xml` no pipeline de NPC/quest. Auto-correção via LLM se ID inválido. |
| **9** | `MCRCuriosidade` | MCR.py:4875 | ✅ Em Produção | Thread background a cada 60s. Limitado a `Canary/data-canary/scripts/` via override de `_descobrir_drives()`. Alimenta CerebroAGI. |
| **10** | `master_agent.py` | `E:\MCR\MasterAgent.py` (lightweight) | ✅ Em Produção | Ciclo PERCEBER→PLANEJAR→EXECUTAR→INTEGRAR→APRENDER. Ativado para `criar_quest`, `criar_npc`, `criar_habilidade_spa`, `criar_sistema`. Anti-reentrância com flag global. Usa MarkovRouter + PipelineExecutor padrão. |

---

## PARTE 4: Duplicatas Identificadas

| Arquivo A | Arquivo B | Ação Sugerida |
|-----------|-----------|---------------|
| `modulos/emergir.py` | `agents/emergir.py` | ✅ agents/ já removido |
| `modulos/conselho.py` | `agents/conselho.py` | Manter modulos/ (é o fonte ativo) |
| `modulos/lua_validator.py` | `tools/lua_validator.py` | Manter modulos/ (é o fonte ativo) |
| `modulos/tool_orchestrator.py` | `tools/orchestrator.py` | Manter modulos/ (versão mais completa, 1055 linhas) |
| `modulos/MCR.py` (437KB) | `E:\MCR\MCR.py` (311KB) | **Problema crônico.** Kernel precisa de MCRSession do modulos/. Nosso entry point usa E:\MCR\. Isolar MCRSession. |

---

## Resumo Estratégico

| Categoria | Arquivos | Integrados | % Integrado |
|-----------|----------|------------|-------------|
| **Core Engine** (MCR.py, v2, entry) | 4 | 4 | 100% |
| **Code Analysis** | 6 | 6 | 100% |
| **Knowledge/Memory/RAG** | 7 | 7 | 100% |
| **Monitoring** | 2 | 2 | 100% |
| **Calibration/Self-Healing** | 3 | 3 | 100% |
| **Template/Gap Filling** | 2 | 2 | 100% |
| **Pipeline** | 3 | 3 | 100% |
| **HDC/SDM/NPC Simulation** | 6 | 0 | 0% |
| **DevIA Knowledge** | 8 | 5 | 63% |
| **DevIA Analysis** | 9 | 1 | 11% |
| **DevIA Pipeline/Generation** | 6 | 4 | 67% |
| **DevIA Validation** | 5 | 3 | 60% |
| **DevIA Tools** | 5 | 3 | 60% |
| **Total** | **~200** | **43** | **~22%** |

---

## PARTE 5: Vulnerabilidades Corrigidas

Registro das correções estruturais aplicadas nesta sessão (07/07/2026, Sessão #5).

| # | Vulnerabilidade | Severidade | Correção | Arquivo |
|---|----------------|-----------|----------|---------|
| **1** | `lr.execute(codigo)` executava código LLM sem sandbox | **Crítica** | Substituído por `lr.eval('loadstring(...)')` que apenas COMPILA sem executar. `attribute_filter` remove `os`, `io`, `package`, `debug`, `loadfile`, `dofile`, `require` dos globals. | `LuaSyntaxValidator.py` |
| **2** | `MarkovRouter.mk` era None — aprendizado nunca funcionava | **Crítica** | `__init__` carrega `_carregar_mk()` que instancia `MCR("router_markov")` com persistência em `cache/router_markov.json`. `aprender()` alimenta MCR real: sucesso reforça 4x, falha registra como `FALHA__`. | `MarkovRouter.py` |
| **3** | Flag global `_EM_MASTER_AGENT` quebrava em múltiplas threads | **Alta** | Substituído por `threading.local()` — cada thread tem seu próprio estado. | `mcr_devia.py` |
| **4** | `MasterAgent._planejar()` usava `confianca=0.9` hardcoded ignorando a confiança real do `MarkovDecider` | **Alta** | Agora recebe `confianca` do `processar()` via `tarefas["confianca"]`. Retry adaptativo com `cmd_grep` + RAG profundo na 2ª tentativa. | `MasterAgent.py` |
| **5** | `rag_mcr.buscar_hibrido()` usava `collection.get(limit=total_docs)` — carregava TODOS os docs na RAM | **Alta** | Substituído por `collection.query(query_texts=..., n_results=k*3)` — busca nativa do ChromaDB, muito mais rápida. Keyword re-ranking leve sobre resultados. | `rag_mcr.py` |
| **6** | `pos_processamento` tinha 7 fallbacks aninhados que mascaravam erros de formato do LLM | **Alta** | Reduzido a 1 parser único: `r'---\s*ARQUIVO:\s*(\S+\.lua)\s*---\s*\n?```lua\n(.*?)```'`. Se não encontrar, `raise ValueError` imediato → loop de auto-correção do LLM. | `PipelineExecutor.py` |
| **7** | Nenhum `timeout` nos comandos `cmd_grep`/`cmd_read` — travavam o pipeline por minutos | **Alta** | `threading.Thread` com `join(timeout=15)` envolve toda chamada `kernel.executar()`. Se estourar, loga `[Pipeline] TIMEOUT` e segue para o próximo comando. | `PipelineExecutor.py` |
| **8** | Encoding inconsistente: `.lua` salvo como UTF-8 (regra do projeto: Latin-1) | **Média** | Criado `encoding.py` com `ler_lua()` (Latin-1), `ler_texto()` (UTF-8), `escrever_lua()` (Latin-1). Todos os saves de `.lua` no pipeline usam `encoding='latin-1'`. | `encoding.py`, `PipelineExecutor.py` |

### Resumo das Correções

| Métrica | Antes | Depois |
|---------|-------|--------|
| **Vulnerabilidades de segurança** | 1 (`lr.execute`) | 0 |
| **Aprendizado do Router** | Placeholder (nunca funcionava) | MCR real com persistência JSON |
| **Thread safety** | Flag global quebrada | `threading.local()` |
| **Fallbacks do PosProcess** | 7 aninhados | 1 parser único |
| **Timeout em comandos** | Nenhum (travava minutos) | 15s por comando |
| **Encoding de Lua** | UTF-8 (incorreto) | Latin-1 (ISO-8859-1) |
| **RAG query** | `get(limit=total)` (lento) | `query()` nativa (rápida) |
