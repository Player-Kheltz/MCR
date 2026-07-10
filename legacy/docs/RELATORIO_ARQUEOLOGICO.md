# RELATORIO DE INVENTARIO ARQUEOLOGICO
Data: 2026-07-07 20:51

## 1. ARTEFATOS CHAVE

| MCRAutoEvolution | mcr/mcr_auto_evolution.py:14 | Ativo | Ciclo de auto-evolucao: muta thresholds, mede entropia, aceita/rejeita. O nucleo da auto-evolucao. |
| MCRMeta.auto_melhoria() | mcr/mcr_meta.py:110 | Ativo | Diagnostica KG e executa ciclos de auto-melhoria. A equacao que se aplica sobre si mesma. |
| MCRPesoNota | temp_pesonota.py:1 + mcr/mcr_meta.py:14 | Ativo | Descobre pesos otimos da Equacao MCR testando combinacoes (byte, palavra, token). |
| MCRSelfHeal | devia/modules/self_study.py:265 | Ativo | Auto-reparo usando anti-patterns. Detecta e corrige proprios erros. |
| MCRRadar | devia/kernel/Radar.py | Ativo | Radar de deteccao de inteligencia/gaps. 0 ondas fixas, 0 thresholds fixos. |
| MCRMetaGap | mcr/meta_gap.py:55 | Ativo | Detecta gaps de conhecimento entre KG e codigo fonte do Canary. |
| AutoCuriosidade | mcr/auto_curiosidade.py:17 | Ativo | Mente inquieta: usa MCRMeta para detectar gaps no KG e estuda-los automaticamente. |
| InnerVoice | mcr/mcr_inner_voice.py:22 | Ativo | Voz interna: pensa quando ninguem fala. Loga em background. |
| Autobiography | mcr/mcr_autobiography.py:13 | Ativo | Memoria narrativa de longo prazo (memorias, nao dados crus). |
| MCRSelf | mcr/mcr_self.py:12 | Ativo | Identidade/ego dinamico para MCR-DevIA. Gerencia personalidade aprendida. |
| Emergir | mcr/emergir.py:19 + devia/modules/emergir.py | Ativo | Motor de criatividade: gera ideia -> escreve codigo -> valida -> promove. |
| MCRBridge | devia/kernel/conexao_bridge.py + devia/kernel/mcr_devia.py:13 | Ativo | Ponte entre MCR.py e o ecossistema DevIA. |
| MCRAutonomo (DELETADO) | git:06ab771f mcr_autonomo.py (321 linhas) | DELETADO | Ciclo perpetuo autonomo: explora -> pensa -> web -> evolui. Chamava MCRAutoEvolution.ciclo(). |
| Iniciar MCR Autonomo.bat | E:/MCR/Iniciar MCR Autonomo.bat (20 linhas) | Ativo | Bat que abria CMD: "title MCR Autonomo" e rodava python MCR.py --autonomo. |
| mcr_autonomo.py (ATUAL) | E:/MCR/mcr_autonomo.py | Ativo | Versao atual do autonomo. Diferente da deletada do git. |
| MCRPeso (innen class) | devia/kernel/MCR.py:2354 + MCR_ORIGINAL.py:2345 | Ativo | Gerenciamento de pesos para decisoes. Pesos mais comuns sao retornados. |
| MCRSystem | historia/scripts/mcr_devia/modulos/MCR.py:536 | Ativo | Sistema MCR completo para DevIA. Integra todos os componentes. |
| MCRKGAuto | historia/scripts/mcr_devia/modulos/MCR.py:2927 | Ativo | Automacao do Knowledge Graph: auto-popula, auto-organiza, auto-expande. |
| MCRExpansao | historia/scripts/mcr_devia/modulos/MCR.py:3119 | Ativo | Expansao automatica de conhecimento. Descobre novos topicos. |
| MCRMeta (DevIA) | historia/scripts/mcr_devia/modulos/MCR.py:3236 | Ativo | Meta-processamento para DevIA. Auto-organizacao e auto-melhoria. |
| MCRTarefa | historia/scripts/mcr_devia/modulos/MCR.py:3337 | Ativo | Gerenciamento de tarefas. Subtarefas, dependencias, conclusao. |
| MCRWorker | historia/scripts/mcr_devia/modulos/MCR.py:3374 | Ativo | Threads de trabalho para processamento paralelo. |
| MCRSpawner | historia/scripts/mcr_devia/modulos/MCR.py:3412 | Ativo | Criacao de processos filhos para tarefas isoladas. |
| MCRMestre | historia/scripts/mcr_devia/modulos/MCR.py:3525 | Ativo | Controlador mestre. Coordena Workers e Spawners. |
| MCRConversa | mcr/mcr_conversa.py:24 | Ativo | Oradores de dialogo: MCR fala, LLM so ensina. |
| MCRPipeline (nico Tibia) | nichos/tibia/mcr_pipeline.py:21 | Ativo | Pipeline de geracao contextual sem LLM: parse -> cache -> bridge -> fragment -> geracao -> aprendizado. |
| SQLiteMarkov | nichos/tibia/mcr_adapt.py:20 | Ativo | Markov chain com SQLite. Suporte a identidade. Predicao adaptativa por entropia. |
| MCRNPC | nichos/tibia/npc_mcr.py:47 | Ativo | NPC com alma: usa MCR para conversar, aprender e evoluir. Chamava auto_evolution.ciclo(). |
| MCRMin (embedded) | nichos/embedded/mcr_min.py:20 | Ativo | MCR minimalista (~160 linhas) para microcontroladores/embedded. |
| MCRHidridClassifier | prototypes/mcr-universal/mcr/hybrid/classifier.py:29 | Ativo | Classifica se pergunta precisa de LLM ou MCR so. Decide por entropia. |
| MCRHidridPipeline | prototypes/mcr-universal/mcr/hybrid/pipeline.py:28 | Ativo | Pipeline completo MCR+LLM com classifier, guardrail, metricas de custo. |
| MCRGuardrail | prototypes/mcr-universal/mcr/hybrid/guardrail.py:16 | Ativo | Validacao de resposta LLM usando Equacao MCR. |
| MCRSelfIndex | devia/kernel/MCR.py:6005 + MCR_ORIGINAL.py:5979 | Ativo | Auto-indexacao do proprio codigo fonte. Indexa MCR.py, modulos, comandos. |

## 2. ARQUIVOS .bat RELEVANTES

| Arquivo | Caminho | Proposito |
|---------|---------|-----------|
| Iniciar MCR Autonomo.bat | E:/MCR/ | Abre CMD e roda python MCR.py --autonomo |
| mcr.bat | E:/Projeto MCR/historia/Scripts/ | Comando unificado: chat, vivo, status, lore, ensinar, scan, treinar |
| mcr_devia.bat | E:/Projeto MCR/historia/Scripts/ | Inicia MCR-DevIA com parametros |
| mcr_vivo.bat | E:/Projeto MCR/historia/Scripts/ | Modo autonomo + observatorio |
| mcr_dashboard.bat | E:/Projeto MCR/historia/Scripts/ | Painel de controle em tempo real |
| mcr_painel_vivo.bat | E:/Projeto MCR/historia/Scripts/ | Painel vivo |
| mcr_observatory.bat | E:/Projeto MCR/historia/Scripts/ | Observatorio |
| evoluir_24h.bat | DELETADO (de7bcb1d) | Evolucao 24 horas |

## 3. ARQUIVOS PERDIDOS / DELETADOS (recuperaveis do git)

### 3.1 Deleted root files (de7bcb1d)
- MCR.py (completo, incluia _EQUACAO_ATUAL)
- MCR_Chat.py (orquestrador universal de ferramentas)
- MCR_AGI.py (versao anterior)
- evoluir_autonomo.py
- evoluir_24h.bat
- setup_git.py, check_git.py
- agi_prototipo/ (25 prototipos: genesis, codex, agi_completo)

### 3.2 Deleted validacao/ files
- bateria_testes.py, bateria_fim_a_fim.py
- meta_observer_v1.py, meta_observer_v2.py, meta_observer_v3.py
- teste_rag_completo.py
- validacao_aprendizado.py

### 3.3 Deleted genesis/ files
- mcr_gen_dados_ruidosos_*.py (4 files)
- test_gen_dados_ruidosos.py

### 3.4 Deleted commit ebe4e2e6 (76 files)
- aprendizado_autonomo.py
- benchmark_final.py, benchmark_stress.py, benchmark_v2.py
- teste_cego_completo/ (19 files)
- teste_cego_mega/ (22 files)
- teste_comandos/ (4 files)

### 3.5 Deleted commit d049addc (4 files)
- cmd_intencao.py, cmd_orquestrar.py, cmd_processar.py
- conceptual_planner.py

## 4. PROTOTIPOS LEGADO (sandbox/)

| Prototipo | Arquivo | Conceito |
|-----------|---------|---------|
| prototipo_mcr_autoloop.py | E:/MCR/historia/sandbox/ | Auto-loop com autoavaliacao |
| prototipo_mcr_byte_unico.py | E:/MCR/historia/sandbox/ | Markov de byte unico |
| prototipo_mcr_zero.py | E:/MCR/historia/sandbox/ | MCR partindo do zero |
| prototipo_inception.py | E:/MCR/historia/sandbox/ | Arquitetura Inception (MCR dentro de MCR) |
| prototipo_regra_de_ouro.py | E:/MCR/historia/sandbox/ | Regra de Ouro: fingerprint dinamico, threshold adaptativo |
| prototipo_radar.py | E:/MCR/historia/sandbox/ | Radar: busca por ondas de similaridade |
| prototipo_reconstrucao.py | E:/MCR/historia/sandbox/ | Reconstroi resposta final de fragmentos |
| prototipo_context_vector.py | E:/MCR/historia/sandbox/ | Vetor de contexto com entropia |
| prototipo_mcr_memoria.py | E:/MCR/historia/sandbox/ | Memoria com entropia de Shannon |
| prototipo_mcr_aprende_codigo.py | E:/MCR/historia/sandbox/ | Aprende padroes de codigo |

## 5. TESTES DE DESCOBERTAS CIENTIFICAS

| Teste | Arquivo | O que descobriu |
|-------|---------|-----------------|
| experimentos_refutacao.py | E:/MCR/historia/sandbox/ | Testes de hipoteses do MCR |
| teste_final_mcr.py | E:/MCR/historia/validacao/ | Validacao final do MCR |
| testar_problemas_reais.py | E:/MCR/historia/validacao/ | Problemas reais (Collatz, primos) |
| testar_radar.py | E:/MCR/historia/validacao/ | Validacao do RADAR |
| teste_multinivel_puro.py | E:/MCR/historia/validacao/ | Processamento multi-nivel |
| validar_equacao.py | E:/MCR/historia/validacao/ | Validacao da Equacao MCR |

## 6. TESTES DE PERFORMANCE E UNIDADE

| Suite | Caminho | Cobertura |
|-------|---------|-----------|
| test_mcr_veracidade.py | E:/MCR/ | 194/194 (10.0/10) |
| test_mcr_comparativo.py | E:/MCR/ | 22 testes |
| test_mcr_comparativo_avancado.py | E:/MCR/ | 27 testes |
| prototypes/mcr-universal/tests/ | 19 arquivos de teste | Core, emergence, feedback, generate, hybrid, intelligence |

## 7. ARTE FATOS DELETADOS vs EXISTENTES (mapeamento)

| Conceito | Existe em | Deletado de | Status |
|----------|-----------|-------------|--------|
| MCRAutoEvolution | mcr/mcr_auto_evolution.py | — | ATIVO |
| MCRMeta.auto_melhoria | mcr/mcr_meta.py | — | ATIVO |
| MCRPesoNota | temp_pesonota.py | — | ATIVO |
| MCRSelfHeal | devia/modules/self_study.py | — | ATIVO |
| MCRRadar | devia/kernel/Radar.py | — | ATIVO |
| MCRAutonomo | mcr_autonomo.py | git:06ab771f | AMBOS |
| Iniciar MCR Autonomo.bat | E:/MCR/ | — | ATIVO |
| MCR_Chat.py | — | de7bcb1d | DELETADO |
| evoluir_autonomo.py | — | de7bcb1d | DELETADO |
| evoluir_24h.bat | — | de7bcb1d | DELETADO |
| conceptual_planner.py | — | d049addc | DELETADO |
| MCR_AGI.py (original) | E:/Projeto MCR/ | de7bcb1d | AMBOS |
| _EQUACAO_ATUAL | MCR.py (DELETADO) | de7bcb1d | PERDIDO? |