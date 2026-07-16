# PLANO DE INCLUSÃO REAL — MCR v7.0

## Princípio: descartar só o que REALMENTE não tem utilidade

### Descarta (zero utilidade):
- devia_archive/knowledge/* (8) — idênticos a mcr/knowledge/
- devia_archive/kernel/mcr_kernel/* (11) — já decompostos
- devia_archive/modulos/* (38) — shims quebrados
- devia_archive/comandos/* (53) — CLI wrappers (capacidades já registradas)
- MCR_legacy.py — já decomposto
- 63 testes pequenos do trash/ — ad-hoc
- sqlite_markov.py — duplica mcr_sqlite
- state.py — duplica decisor
- tool_orchestrator_legacy.py — duplica registry
- prompts_criativos.py — quebra agnosticismo

### Bloco 1: Copiar 10 de E:\Coisas (com correções)
1. hdc_core.py → mcr/ — HDC 10k-dim, remover numpy se possível
2. sdm_core.py → mcr/ — SDM, tornar params descobríveos
3. code_parser.py → mcr/ — tree-sitter, descobrir exts por frequência
4. rag_mcr.py → mcr/ — RAG, remover URL hardcoded, usar config_llm
5. master_agent.py → mcr/ — orquestrador, remover PLANOS_CONHECIDOS
6. conselho.py → mcr/ — multi-persona, remover nomes de modelos
7. rede_npcs.py → mcr/ — rede NPCs, lazy import hdc
8. monster_database.py → mcr/ — database monstros data-driven
9. pos_processamento.py → mcr/ — salvar artefatos, usar paths.py
10. mcr_auto_loop.py → mcr/ — auto-loop por nota, corrigir imports

### Bloco 2: Conectar 10 de E:\MCR ao pipeline
1. bootstrap.py → _bootstrap()
2. config_llm.py → topo mcr.py
3. pattern_engine_texto.py → _perceber()
4. task_planner_dag.py → wrapper _planejar
5. template_entropico.py → _gerar_universal()
6. gerador_codigo.py → tool no registry
7. mcr_radar.py → _decidir() fallback
8. mcr_signature_cluster.py → _aprender()
9. mcr_autobiography.py → _aprender()
10. mcr_meta.py → _avaliar()

### Bloco 3: Mover 28 nicho → nichos/tibia/
cielab, data_injector, discriminador_anatomia, golden_templates, meus_olhos,
olhos_mcr, regioes_anatomicas, sprite_corpus, sprite_extractor, mcr_sprite_motor,
mcr_sprite_universal, pipeline_mcr_sprite, template_regiao, tokenizador_hierarquico,
visual_coupling, npc_criativo, npc_sanity_filter, npc_server, mcr_entity_factory,
mcr_entity_validator, mcr_idea_to_spec, mcr_world_builder, mcr_world_chronicle,
mcr_world_foundation, mcr_world_seed, mcr_world_state, world_observer,
world_anomaly_detector

### Bloco 4: Arquivar 5 quebrados → E:\Coisas\mcr_archive_broken\
hybrid_router.py, mcr_mente_pura.py, mcr_mente.py, pipeline_universal.py

### Bloco 5: Corrigir 1 import
knowledge/lessons_buffer.py: from modulos.util → from mcr.encoding

### Bloco 6: Adaptar 11 testes trash/ → tests/experimento_rigoroso/
12_teste_veracidade, 13_comparativo_avancado, 14_desafios, 15_comparativo,
16_promessas, 17_bateria_real, 18_stress, 19_exp1_mudanca_stream,
20_exp2_gridworld_critical, 21_silogismo, 22_markov_vs_llm

### Bloco 7: Copiar 3 docs
Modulos_Orfaos.md → docs/, ANALISE_ARQUITETURAL → docs/audits/, ROADMAP → docs/

### Bloco 8: Incluir "TALVEZ" (20) com correções
auto_revisor, context_enricher, intention_engine, sandbox_executor, self_study,
validation_pipeline, diagnostico, diagnostic_engine, truncation_fixer,
MarkovRouter, percepcao, log_watcher, FeedbackFilter, code_analyzer,
npc_generator(→nicho), orquestrador, pipeline_executor, mcr_auto_loop(prototipo),
fragmenter(verificar), task_planner_dag(conectar)

### Bloco 9: Auditar 6 subpacotes
autonomia/, dominios/, equacao/, ferramentas/, qualidade/, servicos/

### LLM: NÃO nesta etapa. Próxima fase do projeto.
