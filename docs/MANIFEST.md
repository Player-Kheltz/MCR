# 📋 Manifesto MCR-DevIA — Catálogo Vivo do Ecossistema

> **LEIA SEMPRE** antes de planejar ou executar qualquer tarefa.
> **ATUALIZE** ao descobrir algo novo (módulo, ferramenta, conceito).
> Versão: 1.0 | Data: 2026-06-30

---

## Sumário

1. [Módulos (52)](#-modulos-52)
2. [Ferramentas ToolOrchestrator (30)](#-ferramentas-temporchestrator-30)
3. [Comandos (54)](#-comandos-54)
4. [Conceitos Validados](#-conceitos-validados)
5. [Planos de Arquitetura (10+)](#-planos-de-arquitetura-10)
6. [Documentação Técnica do Projeto](#-documentacao-tecnica-do-projeto)
7. [Regras Operacionais (7)](#-regras-operacionais-7)
8. [Scripts Legados com Potencial](#-scripts-legados-com-potencial)
9. [Arquivos de Configuração](#-arquivos-de-configuracao)
10. [Duplicatas / Legado](#-duplicatas--legado)
11. [Itens da Raiz do Projeto](#-itens-da-raiz-do-projeto)
12. [Background Processes](#-background-processes)
13. [Prioridades de Integração](#-prioridades-de-integracao)

---

## 📦 Módulos (52)

Legenda: ✅ Ciclo | ❌ Fora | ⏸️ Pausado | 🔥 Prioridade

| Módulo | Status | Onde é usado | O que faz | Prioridade |
|--------|--------|-------------|-----------|------------|
| `kernel.py` | ✅ Ciclo | Entry point | Carregador de comandos, bus de eventos | Core |
| `pipeline_executor.py` | ✅ Ciclo | Supervisor | Pipeline ReAct + VALIDATE + LEARN | Core |
| `kg.py` | ✅ Ciclo | pipeline_executor | Knowledge Graph (buscar, aprender) | Core |
| `ia.py` | ✅ Ciclo | pipeline_executor | Interface Ollama + Router de modelos | Core |
| `tool_orchestrator.py` | ✅ Ciclo | pipeline_executor | 30 ferramentas executáveis | Core |
| `decider.py` | ✅ Ciclo | THINK | Classificador universal via FAST | Core |
| `mente.py` | ✅ Ciclo | THINK | Reflexão 1.5b batch (sem KG) | Core |
| `context_crew.py` | ✅ Ciclo | SENSE | 5 fontes de contexto (KG, WebLearn, Docs, Código, Web) | Core |
| `episodic_memory.py` | ✅ Ciclo | SENSE + LEARN | Memória episódica (busca + registra) | Core |
| `context_infinity.py` | ✅ Ciclo | SENSE + LEARN | Histórico de sessão via fragmentos | Core |
| `security.py` | ✅ Ciclo | SENSE | Filtra input malicioso | Core |
| `validation_pipeline.py` | ✅ Ciclo | VALIDATE | V1-V9: padrão, fatos, alucinação, semântica | Core |
| `auto_revisor.py` | ✅ Ciclo | VALIDATE | Detecta alucinações heurísticas pós-LLM | Core |
| `tradutor.py` | ✅ Ciclo | VALIDATE | Garante PT-BR na resposta | Core |
| `progress_tracker.py` | ✅ Ciclo | pipeline_executor | Barra de progresso em tempo real | Core |
| `kg_cleaner.py` | ✅ Startup | kernel.py | Marca lessons poluentes como inactive | Core |
| `truncation_fixer.py` | ✅ Startup | kernel.py | Remove truncamentos residuais do código | Core |
| `self_study.py` | ✅ Background | kernel.py | Escaneia código, métricas, sugestões (10min) | Core |
| `emergir.py` | ✅ Background | pipeline_executor | Padrões emergentes a cada 5 execuções | Core |
| `util.py` | ✅ Utilitário | Todos | Funções compartilhadas (fast, gerar, extrair) | Core |
| `pattern_engine.py` | ✅ Utilitário | reconstructor, pi_engine | Tokenização, fingerprint, Markov | Core |
| `context_enricher.py` | ✅ Ciclo | Enricher no pipeline | Gera contexto novo (lore, dados técnicos) | Core |
| `session_cache.py` | ✅ Supervisor | Supervisor | Cache de sessão para resume | Core |
| `conselho.py` | ❌ Fora | - | Conselho V10: personalidades com router de modelo | 🔥 Integrar |
| `orquestrador.py` | ❌ Fora | - | Motor de templates + fragmentação + cache LRU | 🔥 Integrar |
| `reconstructor.py` | ❌ Fora | - | KG Weaver: fingerprint + prioridade de ctx | 🔥 Integrar |
| `blank_filler.py` | ❌ Fora (tool) | ToolOrchestrator | Esqueleto + @BLANKs preenchidos individualmente | 🔥 Integrar |
| `context_reinforcer.py` | ❌ Fora | - | Expande pergunta antes de processar | 📗 Opcional |
| `tree_of_thought.py` | ❌ Fora | - | 3 perspectivas paralelas + síntese | 📗 Opcional |
| `supervisor.py` | ♻️ Reaproveitar | pipeline_executor | Keyword classifier (0 IA, 0s) + V12 contexto | 🔥 Extrair classificar() |
| `pi_engine.py` | ♻️ Reaproveitar | pipeline_executor | avaliar_entropia() + continuar_padrao() | 🔥 Integrar entropia no fluxo |
| `conceptual_planner.py` | ❌ Fora | - | Planejamento conceitual | 📗 Opcional |
| `agent_loop.py` | ❌ Fora | NPCs | Think-Act-Observe-Learn | NPC Domain |
| `npc_generator.py` | ❌ Fora (tool) | ToolOrchestrator | Geração de NPCs Lua | NPC Domain |
| `canary_indexer.py` | ❌ Fora | NPCs | Indexador do ecossistema Canary | NPC Domain |
| `lua_validator.py` | ❌ Fora (tool) | ToolOrchestrator | Validador de scripts Lua | NPC Domain |
| `master_agent.py` | ❌ Fora | cmd_master | Agente universal (comando separado) | 📗 Opcional |
| `task_executor.py` | ❌ Fora | master_agent | Execução de subtarefas | Master Domain |
| `task_planner.py` | ❌ Fora | master_agent | Decompõe requests complexos | Master Domain |
| `memoria_conselho.py` | ❌ Interno | conselho, mente | Memória individual por membro | Interno |
| `auto_repair.py` | ❌ Fora | - | Repara código com erro via FAST (1.5b) | 🔥 Integrar |
| `diagnostic_engine.py` | ❌ Fora (tool) | ToolOrchestrator | Auto-diagnóstico do sistema | 📗 Opcional |
| `sandbox_executor.py` | ❌ Fora (tool) | ToolOrchestrator | Executa código em ambiente isolado | 📗 Opcional |
| `watchdog.py` | ❌ Background | - | Monitora conversas + índice para ContextCrew | 📗 Iniciar |
| `sse_server.py` | ❌ Background | - | Dashboard tempo real | 📗 Opcional |
| `lessons_buffer.py` | ❌ Fora | - | Buffer de conhecimento antes do KG | 📗 Opcional |
| `crew_pipeline.py` (agents/) | ❌ Fora | - | Pipeline Universal: Analisar→Pesquisar→Filtrar→Compactar | 📗 Duplicata conceitual |
| `memoria_compactada.py` (knowledge/) | ❌ Fora | - | Memória fragmentada por data + compressão | 📗 Poderia otimizar LEARN |
| `fragmenter.py` (analysis/) | ❌ Fora | - | Super Fragmentador multi-modelo | 🔥 Poderia integrar ao Orquestrador |
| `MCR_DevIA-Kernel.py` | ✅ Entry point | CLI alternativa | Entry point alternativo ao kernel.py. Usado por cmd_perguntar diretamente | Core |
| `item_database.py` (knowledge/) | ❌ Fora | - | Wrapper sobre items.xml do Canary (buscar_item_canary) | 🔗 Usado via ferramenta |
| `tool_registry.py` (knowledge/) | ❌ Fora | - | Catálogo de metadados de 24 ferramentas do sistema | 🔗 Apenas metadados |
| `planner.py` (agents/) | ❌ Fora | - | Duplicata de task_planner.py | 📗 Duplicata |
| `_extract/` | 📦 Utilitário | - | Extração de funções de `validador_genero.py` — corretor de gênero de itens do items.xml | 📗 Cache/artefato de build |

---

## 🧰 Ferramentas ToolOrchestrator (30)

| # | Ferramenta | No ReAct? | Descrição | Observação |
|---|-----------|-----------|-----------|------------|
| 1 | `executar_comando` | ❌ | Executa comando no terminal | Segurança (não expor) |
| 2 | `ler_arquivo` | ✅ | Lê conteúdo de arquivo | - |
| 3 | `escrever_arquivo` | ✅ | Cria/modifica arquivo | Usar com cautela |
| 4 | `listar_diretorio` | ❌ | Lista arquivos de diretório | Útil para exploração |
| 5 | `criar_diretorio` | ❌ | Cria estrutura de diretórios | Raramente necessário |
| 6 | `buscar_codigo` | ✅ | Grep genérico em todo projeto | Universal |
| 7 | `buscar_inteligente` | ❌ | Busca com variações automáticas | **FALTA no ReAct** |
| 8 | `buscar_estrategico` | ✅ | Descobre diretórios + arquivos + funções | Core |
| 9 | `buscar_kg` | ✅ | Busca definições no Knowledge Graph | Core |
| 10 | `aprender_kg` | ❌ | Registra aprendizado no KG | **FALTA no ReAct** |
| 11 | `buscar_web` | ❌ | Pesquisa na web | **FALTA no ReAct** |
| 12 | `buscar_memoria` | ❌ | Busca na memória episódica | **FALTA no ReAct** |
| 13 | `gerar_npc` | ✅ | Gera script Lua de NPC | NPC Domain |
| 14 | `gerar_codigo` | ✅ | Gera código via IA | - |
| 15 | `gerar_esqueleto` | ✅ | Gera esqueleto com @BLANK_N | BlankFiller |
| 16 | `preencher_blank` | ✅ | Preenche um blank específico | BlankFiller |
| 17 | `diagnosticar` | ✅ | Roda diagnóstico do sistema | - |
| 18 | `pattern_analyze` | ✅ | Analisa padrões em texto/código | Universal |
| 19 | `escrever_artefato` | ✅ | Salva código criado em arquivo | - |
| 20 | `validar_lua` | ✅ | Valida script Lua | Específico |
| 21 | `validar_python` | ❌ | Valida código Python (compile) | **FALTA no ReAct** |
| 22 | `executar_python` | ✅ | Executa código Python no sandbox | - |
| 23 | `validar_codigo` | ❌ | Valida código em QUALQUER linguagem | 🔥 **FALTA no ReAct** |
| 24 | `perguntar_ia` | ❌ | Pergunta diretamente ao modelo IA | **FALTA no ReAct** |
| 25 | `analisar_codigo` | ✅ | Analisa código fonte com IA | - |
| 26 | `extrair_codigo` | ❌ | Extrai código de resposta markdown | 🔥 **FALTA no ReAct** |
| 27 | `gerar_requirements` | ❌ | Gera requirements.txt | Raramente necessário |
| 28 | `criar_atalho` | ❌ | Cria atalho para comando | Raramente necessário |
| 29 | `instalar_dependencias` | ❌ | Instala dependências Python | Segurança |
| 30 | `buscar_item_canary` | ❌ | Busca item no banco Canary | **FALTA no ReAct** |

**Ferramentas que FALTAM no ReAct (7):**
- `buscar_inteligente` — busca com variações
- `aprender_kg` — registra aprendizado
- `buscar_web` — pesquisa na web
- `buscar_memoria` — busca experiências
- `validar_python` — valida Python
- **`validar_codigo`** 🔥 — valida QUALQUER linguagem (universal!)
- **`extrair_codigo`** 🔥 — extrai código de markdown (universal!)
- `perguntar_ia` — pergunta direta ao modelo
- `buscar_item_canary` — busca itens do jogo

---

## 🎮 Comandos (54)

| Comando | Categoria | O que faz | Arquivo |
|---------|-----------|-----------|---------|
| `perguntar` | IA | Responde usando pipeline completo | cmd_perguntar.py |
| `ensinar` | Conhecimento | Registra lição no KG | cmd_ensinar.py |
| `aprender_conceito` | Conhecimento | Aprende conceito do código + docs | cmd_aprender_conceito.py |
| `explorar` | Conhecimento | Escaneia e aprende com IA mínima | cmd_explorar.py |
| `weblearn` | Conhecimento | Aprendizado web (busca, fragmenta, salva) | cmd_weblearn.py |
| `webfetch` | Conhecimento | Busca conteúdo de uma URL | cmd_webfetch.py |
| `analisar` | Análise | Analisa arquivo com Orquestrador | cmd_analisar.py |
| `revisar` | Análise | Revisor por pares | cmd_revisar.py |
| `review` | Análise | Revisa dados extraídos | cmd_review.py |
| `bugfinder` | Análise | Escaneia logs e registra erros no KG | cmd_bugfinder.py |
| `grep` | Busca | Busca texto em arquivos | cmd_grep.py |
| `glob` | Busca | Busca arquivos por nome | cmd_glob.py |
| `read` | Leitura | Lê arquivos com offset/limit | cmd_read.py |
| `write` | Escrita | Escreve conteúdo em arquivo | cmd_write.py |
| `edit` | Edição | Edita por LINHA (precisão cirúrgica) | cmd_edit.py |
| `patch` | Edição | Edição V12: Python estrutura, IA preenche | cmd_patch.py |
| `extract` | Edição | Extrai partes de arquivo, modifica, reaplica | cmd_extract.py |
| `gerar` | Geração | Geração genérica | cmd_gerar.py |
| `gerar_npc` | Geração | Gera NPCs Lua para Canary | cmd_gerar_npc.py |
| `gerar_componentes` | Geração | Pré-gera componentes | cmd_gerar_componentes.py |
| `build` | Geração | Pipeline Dinâmica: gera código sob medida | cmd_build.py |
| `fix_excepts` | Geração | Substitui `except:` por `except Exception` | cmd_fix_excepts.py |
| `lore` | Lore | Gera lore PT-BR | cmd_lore.py |
| `master` | AGI | Executa o MasterAgent | cmd_master.py |
| `task` | AGI | Delega para script do MCR-DevIA | cmd_task.py |
| `plan` | AGI | Planeja antes de executar | cmd_plan.py |
| `loop` | AGI | Loop autônomo OODA | cmd_loop.py |
| `conselho` | Conselho | Conselho V7 para respostas | cmd_conselho.py |
| `debate` | Debate | 2 sub-agentes discutem | cmd_debate.py |
| `conectar` | Thinker | Conexões entre domínios no KG | cmd_conectar.py |
| `pensar` | Reflexão | Documenta raciocínio no .mcr_conversa | cmd_pensar.py |
| `memoria` | Memória | Consulta histórico fragmentado | cmd_memoria.py |
| `status` | Sistema | Métricas do Knowledge Graph | cmd_status.py |
| `toolkit` | Sistema | Inventário de capacidades | cmd_toolkit.py |
| `system` | Sistema | Lê o computador inteiro (read-only) | cmd_system.py |
| `system_scan` | Sistema | Escaneia sistema | cmd_system_scan.py |
| `autoteste` | Teste | Auto-Teste Definitivo | cmd_autoteste.py |
| `super_test` | Teste | Pipeline de Validação Universal | cmd_super_test.py |
| `refresh` | Sistema | Hot-reload de comandos | cmd_refresh.py |
| `resume` | Sistema | Retoma sessão interrompida | cmd_resume.py |
| `proativo` | Sistema | Varre e sugere ações sem pedir | cmd_proativo.py |
| `compilar` | Build | Compilação | cmd_compilar.py |
| `builderx` | Build | Builder avançado | cmd_builderx.py |
| `turbo` | Offline | Modo Offline Turbinado | cmd_turbo.py |
| `verificar_mudancas` | Sistema | Detecta alterações nos arquivos | cmd_verificar_mudancas.py |
| `intencao` | ALIAS | ALIAS para perguntar | cmd_intencao.py |
| `orquestrar` | ALIAS | ALIAS para perguntar | cmd_orquestrar.py |
| `processar` | ALIAS | ALIAS para perguntar | cmd_processar.py |
| `question` | Pergunta | Pergunta ao usuário e aguarda resposta | cmd_question.py |
| `fast` | Classificação | Classificação rápida via IA | cmd_fast.py |
| `estrategia` | Estratégia | Estratégia | cmd_estrategia.py |
| `todo` | Tarefa | Gerenciador de tarefas | cmd_todo.py |
| `cmd_compilar` | Build | Compilação | cmd_compilar.py |
| `cmd_builderx` | Build | Builder avançado | cmd_builderx.py |

---

## 🧠 Conceitos Validados

Conceitos que você (Kheltz) criou e validou, mas estão fora do ciclo atualmente.

| Conceito | Módulo | Status | Prioridade | Observação |
|----------|--------|--------|-----------|------------|
| **Conselho V10** | `conselho.py` | ❌ Fora | 🔥 Alta | Personalidades com router de modelo. Mente substitui mas é 1.5b batch. Conselho usa 7b/14b por arquétipo |
| **Orquestrador** | `orquestrador.py` | ❌ Fora | 🔥 Alta | Motor de templates com fragmentação, cache LRU, 4 tiers de fallback. ReAct substitui mas Orquestrador tem templates validados |
| **Reconstructor** | `reconstructor.py` | ❌ Fora | 🔥 Alta | KG Weaver: fingerprint + prioridade de ctx + weaver contextual. Seed do KG substitui mas é mais raso |
| **BlankFiller** | `blank_filler.py` | ⚠️ Tool | 🔥 Alta | Esqueleto + blanks. Já é ferramenta no ReAct mas LLM não sabe usar. Precisa de melhor prompt |
| **V12 Contexto** | `supervisor.py` | ♻️ Reaproveitar | 🔥 Média | Roteador V12 + keyword classifier (0 IA). Extrair para pipeline |
| **TreeOfThought** | `tree_of_thought.py` | ❌ Fora | 📗 Baixa | 3 perspectivas. Só para perguntas muito complexas |
| **Supervisor (V12)** | `supervisor.py` | ♻️ Reaproveitar | 🔥 Média | Keyword classifier (0 IA, 0s). Extrair para pipeline |
| **PiEngine (Entropia)** | `pi_engine.py` | ♻️ Reaproveitar | 🔥 Média | avaliar_entropia() decide fluxo. continuar_padrao() para código |
| **AutoRepair** | `auto_repair.py` | ❌ Fora | 🔥 Média | Repara código com erro. Deveria estar no fluxo de criação |
| **ContextReinforcer** | `context_reinforcer.py` | ❌ Fora | 📗 Baixa | Expande pergunta. SENSE já faz papel similar |
| **AutoConsciencia** | `agents/autoconsciencia.py` | ❌ Fora | 📗 Baixa | Monitora padrões de erro. Background |
| **LessonsBuffer** | `lessons_buffer.py` | ❌ Fora | 📗 Baixa | Buffer de KG. Otimização |

---

## 📄 Planos de Arquitetura (10+)

Planos criados e validados. Muitos contêm conceitos não integrados.

| Plano | Tamanho | Conceitos-Chave | Status |
|-------|---------|-----------------|--------|
| `PLANO_MASTER_AGENT.md` | 4378 lin | TaskAnalyzer, Decider/FAST Universal, ContextInfinity, Cloud fallback | ⏳ Não lido pelo sistema |
| `PLANO_FINAL_MCR_DevIA.md` | 576 lin | 28 tarefas em 7 fases (17 pendentes) | ⏳ 11 feitas, 17 pendentes |
| `CHECKPOINT_SESSAO.md` | 355 lin | Estado do sistema 27/06, métricas, decisões de design | 📗 Histórico |
| `EMERGIR_V5.md` | 325 lin | Dashboard + Fragmentador 4 seções + Z expandido + Direcionado | ⏳ V4 implementado, V5 planejado |
| `AUTO_TESTE.md` | 202 lin | Teste oficial de capacidades gerais com auto-crítica | ⏳ Não executado |
| `EMERGIR.md` | 78 lin | Emergir original: amostrar + combinar fingerprint + validar | ✅ Implementado em modulos/emergir.py |
| `TROUBLESHOOTING.md` | 85 lin | Problemas comuns de compilação, LOS, visão | 📗 Referência técnica |
| `PLANO_DEBATE_TESTO_CEGO.md` | 44 lin | Debate Cloud vs MCR em 4 fases com 3 perguntas cegas | ⏳ Não executado |
| `PATTERN_ENGINE.md` | 46 lin | Tokenização multi-domínio, fingerprint 256d, eixo Nirvana-Caos | ✅ Implementado em pattern_engine.py |
| `PATTERN_GATEKEEPER.md` | 36 lin | `reparar_com_validacao()` em util.py — valida reparos | ✅ Implementado em util.py |
| `auto_avaliacao_mcr.md` | 27 lin | Ciclo de auto-aperfeiçoamento: Registrar→Implementar→Testar→Integrar | 📗 Filosofia do sistema |
| `AGI_ARCHITECTURE.md` | ~466 lin | Plano completo da arquitetura AGI 5 camadas | ⏳ Parcialmente implementado |

---

## 📚 Documentação Técnica do Projeto

Guias e documentações do Projeto MCR (servidor Tibia). Referenciados pelo CATALOG.md.

| Guia | O que cobre |
|------|-------------|
| `[0] MCR - INDICE GERAL.txt` | Pilares do projeto, roadmap, estado da implementação |
| `[1] MCR - Guia de Compilação (Servidor).txt` | Compilação do servidor Canary com SPA |
| `[2] MCR - Guia de Compilação (Cliente).txt` | Compilação do OTClient com opcodes |
| `[3] MCR - Guia de Configuração (Servidor e Rede).txt` | Portas, storages, opcodes, OTCFeatures |
| `[4] MCR - Guia do Login Server.txt` | API REST, autenticação, guest accounts |
| `[5] MCR - Guia de Interface (OTUI e Lua Cliente).txt` | Sintaxe OTUI, fontes, codificação |
| `[6] MCR - Guia de Narrativa e Diálogos.txt` | Imersão narrativa, personalidade NPCs, cores |
| `[7] MCR - Guia de Quests (Sistema Híbrido SQH).txt` | Missões com HUD, toasts, integração SPA |
| `[8] MCR - Guia de Criação de Conta e Personagem.txt` | Criação, Oráculo |
| `[9] MCR - Guia de Banco de Dados (MySQL).txt` | Schema MySQL |
| `[10] MCR - Guia de Tradução e Localização (PT-BR).txt` | Codificação por tipo de arquivo, pipeline de tradução |
| `[11] MCR - Guia de Experiência do Jogador.txt` | Jornada completa do Alma ao herói |
| `[12] MCR - Guia de Conteúdo Inicial e Tutorial.txt` | Tutorial de Eridanus, NPCs, missões iniciais |
| `[13] MCR - Guia de Criação de Habilidades.txt` | Filosofia de design, estrutura por hierarquia, pacotes temáticos |
| `DevLog/Pendências.md` | Estado atual do projeto, tarefas pendentes |
| `DevLog/Sistema Multi-Piso.md` | Decisões do sistema multi-piso: LOS, BattleList, pathfinding |
| `DevLog/Sistema de Codificação.md` | Decisões sobre encoding UTF-8 |
| `DevLog/Sistema de Montarias.md` | Decisões do sistema MountSummon |
| `DevLog/.session_checkpoint.json` | Checkpoint de sessão — estado interno do sistema (5.9KB) |

**Arquivos adicionais em:** `docs/MCR - Instruções/`

| Arquivo | O que cobre |
|---------|-------------|
| `[Aquivo Complementar] Lista de Items Uteis.txt` | Lista de itens do jogo com IDs, atributos e categorias |
| `[Documentação] MCR - Documentação Técnica do Motor SPA.txt` | Documentação técnica COMPLETA do motor SPA |
| `[Documentação] MCR - Filosofia do SPA - Sistema de Progressão do Aventureiro.txt` | Filosofia de design e conceitos do SPA |
| `[Documentação] MCR - Sistema de Montaria como Summon (MountSummon).txt` | Documentação do sistema MountSummon |
| `[Documentação] MCR - Sistema de Perseguição Multi-Piso.txt` | Documentação do sistema de pathfinding multi-piso |
| `[Gabarito] Habilidade Gabarito.txt` | Template/gabarito para criação de habilidades |
| `[Personalidade] MCR - Personalidade e Identidade de Dominios.txt` | Identidade narrativa e personalidade dos domínios |

**Sistema de Habilidades Contextuais (SHC) — diretório completo em:** `docs/MCR - Instruções/Sistema de Habilidades Contextuais/`

| Arquivo | O que cobre |
|---------|-------------|
| `00 - INDICE.txt` | Índice completo do Sistema de Habilidades Contextuais |
| `01 - ARQUITETURA DO SISTEMA.txt` | Arquitetura do SHC — camadas, postura, nível, sinergia, estado, condição |
| `02 - CATALOGO DE DOMINIOS/` | **5 arquivos**, um por domínio elemental: |
| ├ `23 - FOGO.txt` | Habilidades, atributos e mecânicas do domínio FOGO |
| ├ `24 - AGUA_GELO.txt` | Habilidades, atributos e mecânicas do domínio GELO |
| ├ `25 - TERRA_VENENO.txt` | Habilidades, atributos e mecânicas do domínio TERRA |
| ├ `26 - ENERGIA.txt` | Habilidades, atributos e mecânicas do domínio ENERGIA |
| └ `200 - SAGRADO_MORTE.txt` | Habilidades, atributos e mecânicas do domínio SAGRADO/MORTE |
| `03 - CATALOGO DE HABILIDADES/` | Diretório para catálogo de habilidades (atualmente vazio — criar conteúdo) |
| `04 - MATRIZ DE SINERGIAS.txt` | Tabela de sinergias entre domínios e habilidades |
| `05 - GUIAS DE CRIACAO.txt` | Guias e templates para criação de novas habilidades |

---

## ⚙️ Regras Operacionais (7)

Regras que definem como o MCR-DevIA opera.

| Regra | O que define | Arquivo |
|-------|-------------|---------|
| `autonomia` | Quando o sistema pode agir sem aprovação humana | `rules/autonomia.md` |
| `checkpoint` | Como salvar/restaurar estado da sessão | `rules/checkpoint.md` |
| `compilação` | Procedimento de build do servidor/cliente | `rules/compilacao.md` |
| `encoding` | Padronização UTF-8 em todo o projeto | `rules/encoding.md` |
| `intercâmbio` | Troca de informações entre módulos do sistema | `rules/intercambio.md` |
| `lições` | Como registrar aprendizado no Knowledge Graph | `rules/licoes.md` |
| `workflow` | Fluxo de trabalho padrão para tarefas | `rules/workflow.md` |

---

## 📦 Scripts Legados com Potencial

Scripts identificados em `PENDENCIA_REVAMP_SCRIPTS_LEGADOS.md` que contêm conceitos aproveitáveis.

| Script | Localização | O que faz | Potencial de Integração |
|--------|-------------|-----------|------------------------|
| `crew_deepseek.py` | scripts/ | Validador com fallback deepseek-r1 + qwen7b | 🔥 Virar ferramenta de validação universal |
| `super_fragmentador.py` | scripts/ | Fragmentação de texto multi-modelo | 🔥 Integrar ao Orquestrador |
| `mcr_knowledge.py` | scripts/ | Gerenciamento de conhecimento via IA | 🔥 Integrar ao KG |
| `mcr_auto_improve.py` | scripts/ | Auto melhoria contínua do sistema | 🔥 Integrar ao SelfStudy |
| `mcr_learning_scan.py` | scripts/ | Scan de aprendizado do código | 📗 Revisar se ainda útil |
| `mcr_observatory_v2.py` | scripts/ | Observatório do sistema | 📗 Revisar se ainda útil |

---

## 🗂️ Arquivos de Configuração

Arquivos de configuração e utilitários do sistema (não são módulos executáveis).

| Arquivo | O que faz | Onde |
|---------|-----------|------|
| `MCR_IDENTITY.md` | Identidade do projeto (injetada em templates) | `docs/` |
| `AGENTS.md` | Regras absolutas do assistente MCR | Raiz |
| `LEMBRETE.md` | Checklist de abertura de sessão | Raiz |
| `CATALOG.md` | Catálogo de toda documentação do projeto | `docs/` |
| `stop_words.py` | Stop words centralizadas (STOP_V12, STOP_BUSCA) | `scripts/mcr_devia/` |
| `mcr_devia.py` | Legado 2854 linhas — entry point antigo | `scripts/mcr_devia/` |
| `session.json` | Dados de sessão atual | `docs/` |
| `.mcr_*.json` | Arquivos de cache/estado do sistema (sandbox/) | `sandbox/` |
| `thought_dashboard.html` | Dashboard HTML para SSE Server | `sandbox/` |

---

## 🗂️ Duplicatas / Legado

| Original | Cópia | Risco |
|----------|-------|-------|
| `modulos/conselho.py` | `agents/conselho.py` | Divergência |
| `modulos/supervisor.py` | `agents/supervisor.py` | Divergência |
| `modulos/decider.py` | `analysis/decider.py` | Divergência |
| `modulos/pattern_engine.py` | `analysis/pattern_engine.py` | Divergência |
| `modulos/self_study.py` | `analysis/self_study.py` | Divergência |
| `modulos/validation_pipeline.py` | `analysis/validation.py` | Divergência |
| `modulos/tool_orchestrator.py` | `tools/orchestrator.py` | AINDA COM FINDSTR (legado) |
| `modulos/reconstructor.py` | `pipeline/reconstructor.py` | Versão alternativa |
| `modulos/pipeline_executor.py` | `pipeline/executor.py` | Versão alternativa |
| `modulos/session_cache.py` | `pipeline/session_cache.py` | Versão alternativa |
| `modulos/ia.py` | `core/ia.py` | Cópia |
| `modulos/util.py` | `core/util.py` | Cópia |
| `modulos/security.py` | `core/security.py` | Cópia |
| `modulos/progress_tracker.py` | `core/progress_tracker.py` | Cópia |
| `modulos/auto_revisor.py` | `analysis/auto_revisor.py` | Cópia |
| `modulos/truncation_fixer.py` | `analysis/truncation_fixer.py` | Cópia |
| `modulos/pi_engine.py` | (sem pipeline copy) | - |
| `modulos/diagnostic_engine.py` | `analysis/diagnostic_engine.py` | Cópia |
| `modulos/diagnostic_engine.py` | `analysis/diagnostico.py` | Cópia com nome diferente |
| `modulos/emergir.py` | `agents/emergir.py` | Cópia |
| `modulos/master_agent.py` | `agents/master_agent.py` | Cópia |
| `modulos/mente.py` | `agents/mente.py` | Cópia |
| `modulos/task_executor.py` | `agents/task_executor.py` | Cópia |
| `modulos/tree_of_thought.py` | `agents/tree_of_thought.py` | Cópia |
| `modulos/sandbox_executor.py` | `tools/sandbox.py` | Cópia com diferenças |
| `stop_words.py` (raiz) | (usado por context_crew, crew_pattern) | Utilitário central |
| `modulos/task_planner.py` | `agents/planner.py` | Nome diferente, mesma função |
| `MCR_DevIA-Kernel.py` | (núcleo do kernel) | Entry point crítico — verificar sincronia com kernel.py |
| `tools/toolkit.py` | (sem cópia em modulos) | Ferramenta de listagem de capacidades — adicionar ao MANIFEST |

---

## 📂 Itens da Raiz do Projeto

Arquivos e diretórios na raiz de `E:\Projeto MCR\` que não são módulos nem comandos, mas fazem parte do ecossistema.

### 📄 Documentos Críticos

| Arquivo | O que faz | Prioridade |
|---------|-----------|-----------|
| `Pendencias.md` | **"Leia no início de toda conversa"**. Estado do projeto em 27/06. 13 concluídas + 17 pendentes. **DIFERENTE** de DevLog/Pendências.md | 🔥 **CRÍTICO — não lido pelo sistema** |
| `README.md` | README do projeto | 📗 Baixa |
| `LEMBRETE.md` | Checklist de abertura de sessão | ✅ Já incluso em Arquivos de Configuração |
| `AGENTS.md` | Regras absolutas do assistente | ✅ Já incluso |

### 🔧 Scripts e Entry Points Alternativos

| Arquivo | O que faz | Usa |
|---------|-----------|-----|
| `mcr-dev.py` | Assistente standalone "MCR-Dev v1.0" — terminal interativo. Usa `from mcr_dev import engine, memoria` | `scripts/mcr_dev/engine` |
| `mcr-dev.bat` | Inicia mcr-dev.py | `mcr-dev.py` |
| `mcr.bat` | **Comando unificado**: chat, vivo, status, lore, ensinar, scan | `mcr_devia.py` (legado) |
| `mcr_devia.bat` | Inicia MCR_DevIA-Kernel.py | `MCR_DevIA-Kernel.py` |
| `mcr_chat.bat` | Terminal interativo | `mcr_chat.py` |
| `mcr_dashboard.bat` | Dashboard SSE | `kernel.py --dashboard` |
| `mcr_vivo.bat` | Modo autônomo + observatório | Combina scripts |
| `mcr_observatory.bat` | Narrador ao vivo | `kernel.py --observatory` |
| `mcr_painel_vivo.bat` | Painel V12 | V12 panel |
| `mcr-ollama.bat` | Inicia Ollama + MCR | Ollama + kernel |
| `opencode-safe.bat` | OpenCode safe mode (Ollama desligado) | OpenCode |

### 🔧 Módulos Legado (raiz `modulos/`)

Versões ANTERIORES de módulos que divergiram das atuais em `scripts/mcr_devia/modulos/`. **TODOS os 6 arquivos têm tamanhos diferentes.**

| Arquivo | Tamanho | vs Atual | Conceito Único | Reaproveitável? |
|---------|---------|----------|----------------|-----------------|
| `pipeline_executor.py` | 14KB | vs 64KB | **ContextReinforcer integrado** — expande pergunta antes de processar | 🔥 Sim — conceito PERDIDO |
| `conselho.py` | 22KB | vs 27KB | Router de modelos diferente (deepseek como analisar/revisor) | 📗 Arquivo histórico |
| `orquestrador.py` | 38KB | vs 38KB | Quase idêntico ao atual | ❌ Não |
| `supervisor.py` | 36KB | vs 36KB | `classificar_keyword()` (0 IA) — o que queremos extrair | 🔥 Sim |
| `mente.py` | 9KB | vs 8KB | `learn()` separado do `think()` | 📗 Diferença menor |
| `auto_revisor.py` | 10KB | vs 15KB | Versão mais antiga | ❌ Não |

### 🔧 Dependências Externas

| Item | O que é | Local |
|------|---------|-------|
| `LoginServer/` | Servidor de autenticação Go do OpenTibiaBR (terceiro) | `E:\Projeto MCR\LoginServer\` |
| `MapEditor/` | Editor de mapas para Tibia | `E:\Projeto MCR\MapEditor\` |
| `src/` | Scripts JS (index.js, crypto_test.js) | `E:\Projeto MCR\src\` |
| `node_modules/` | Dependências Node.js | `E:\Projeto MCR\node_modules\` |
| `package.json` | Dependências Node.js do projeto | Raiz |
| `opencode.json` | **Config da ferramenta de edição (OpenCode)** | Raiz |
| `opencode.local.json` | Config local do OpenCode | Raiz |

### 📊 Resultados de Teste Cego

| Item | Conteúdo |
|------|----------|
| `respostas_cloud/p1..p3.txt` | 3 respostas do Cloud em teste cego |
| `respostas_mcr/p1..p3.txt` + logs | 3 respostas do MCR + logs de execução |

### 📦 Outros

| Item | O que é |
|------|---------|
| `Backup/` | Zips de backup de componentes (LoginServer, MapEditor, etc.) |
| `replacements.txt` | Padrões de substituição para scripts |
| `.local_todo.json` | Tarefas locais |
| `tests/` | Testes Python (test_verdade, test_complexo, test_criacao, test_react) |

---

## ⚙️ Background Processes

| Processo | Onde | Frequência | Status |
|----------|------|-----------|--------|
| KGCleaner | kernel.py inicializar() | Única (startup) | ✅ |
| TruncationFixer | kernel.py inicializar() | Única (startup) | ✅ |
| SelfStudy | kernel.py thread | A cada 10min | ✅ |
| Emergir | pipeline_executor | A cada 5 execuções | ✅ |
| Watchdog | Precisa iniciar manualmente | Contínuo | ❌ Parado |
| SSEServer | Precisa iniciar manualmente | Contínuo | ❌ Parado |
| Autoconsciencia | Não implementado | A cada execução | ❌ Pendente |

---

## 🎯 Prioridades de Integração

**33 etapas organizadas em 5 fases.** Ver `docs/IMPLEMENTACAO_MANIFEST.md` para detalhes completos.

### 🔥 FASE A1 — Núcleo Híbrido (WEAVER + CONSELHO + ORQUESTRADOR)
1. Reconstructor como WEAVER
2. Conselho V10 como processador multi-perspectiva
3. Orquestrador como gerador principal
4. ReAct vira fallback
5. Fragmenter integrado ao Orquestrador
6. Keyword classifier do supervisor (0 IA)
7. PiEngine.avaliar_entropia

### 🔥 FASE A2 — Qualidade + Ferramentas
8. validar_codigo + extrair_codigo no ReAct
9. auto_repair no fluxo de criação
10. Router Híbrido (local + cloud)

### 🔥 FASE B — Limpeza
11. Remover fallbacks mortos do supervisor
12. Remover fallbacks mortos do cmd_perguntar
13. Revisar scripts legados úteis

### 📗 FASE C — Background + PLANO_FINAL
14-27. Watchdog, ferramentas, memoria_compactada + 11 tarefas do PLANO_FINAL

### 📗 FASE D — Conceitos Reavivados
28-33. Decider/FAST Universal, V12 Contexto, reparar_com_validacao, cmd_criar, AGI doc, AutoConsciencia

---

## 📊 Resumo de Status

```
✅ No ciclo AGI:      22 módulos
❌ Fora do ciclo:     22 módulos
♻️ Reaproveitáveis:    3 módulos (supervisor, pi_engine, V12)
🔥 Prioridade alta:  10 integrações
📗 Prioridade baixa:  8 integrações

✅ Ferramentas no ReAct:  18 de 30
❌ Ferramentas faltando:  7

✅ Background ativos:  3 (SelfStudy, Emergir, KGCleaner)
❌ Background parados: 2 (Watchdog, SSEServer)

📄 Planos de arquitetura: 12
📚 Documentação técnica:  25 guias + devlogs + SHC (12 arquivos, 1 dir vazio)
⚙️  Regras operacionais:   7
📦 Scripts legados uteis:  6 a revisar
📂 Modulos legado (raiz): 6 (com ContextReinforcer perdido)
📂 Itens raiz: Pendencias.md, mcr-dev.py, LoginServer, 9 .bat, opencode.json
📂 Teste cego: 3 respostas Cloud + 3 MCR
```

---

> **Regra**: Leia este manifesto COMPLETO antes de planejar ou executar.
> **Regra**: Atualize ao descobrir algo novo.
> **Próxima ação**: Iniciar FASE A — Integrar Reconstructor, Conselho, Orquestrador.
