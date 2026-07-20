# Catálogo MCR — Módulos por Função

> **Versão: 3.0** | Data: 2026-07-20
> 133 módulos, 46.286 linhas
> Motor: P(b|a) + escalas + persistência + feedback

---

## Índice

1. [Núcleo do Motor](#1-nucleo-do-motor)
2. [Chat e Interação](#2-chat-e-interacao)
3. [Auto-Conhecimento e Meta-Cognição](#3-auto-conhecimento-e-meta-cognicao)
4. [Abstração e Raciocínio](#4-abstracao-e-raciocinio)
5. [Hierarquia e Magnitudes](#5-hierarquia-e-magnitudes)
6. [Features e Tokenização](#6-features-e-tokenizacao)
7. [Base de Conhecimento e Memória](#7-base-de-conhecimento-e-memoria)
8. [Equação e Esquecimento](#8-equacao-e-esquecimento)
9. [Agentes e Decisão](#9-agentes-e-decisao)
10. [Emergência e Geração](#10-emergencia-e-geracao)
11. [Padrões e Análise](#11-padroes-e-analise)
12. [Comunicação e Infra](#12-comunicacao-e-infra)
13. [Ferramentas Cognitivas](#13-ferramentas-cognitivas)
14. [Legado](#14-legado)
15. [Métricas do Ecossistema](#15-metricas-do-ecossistema)

---

## 1. Núcleo do Motor

O coração do MCR. Tudo converge para estas classes.

### `MCRCoupling` — Motor principal (13 fontes + HRC)

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/coupling.py` |
| **Linhas** | 4381 |
| **Classes** | `MCRCoupling` (única) |
| **Métodos principais** | `alimentar()`, `alimentar_lote()`, `decidir()`, `extrair_relacoes()` |
| **Depende de** | `math`, `collections`, `random`, `re` |
| **13 fontes** | `_dist_char`, `_dist_byte`, `_dist_palavra`, `_dist_esfera`, `_dist_features`, `_dist_trigramas`, `_dist_padrao`, `_transicao_palavra`, `_compor_n_grama`, `_avaliar_entropia`, `_nmi_semantico`, `_busca_ativa`, `_cobertura_features` |
| **HRC** | Hierarchical Regressive Compression: `_hrc_expandir()`, `_hrc_analisar()` |
| **Planos N-dim** | 10: t, c, b, bg, ng, p{i}, ca, cd, sl, ngp |
| **Caches** | `_cache_idf_doc`, `_transicao_rev_full`, `_posicao_acao_inv`, `_p0_chaves`, `_CACHE_H_JANELA` |
| **Notas** | `_nmi_semantico` usa MI puro (não JSD). NMI por plano (ctx, acao, posacao). IDF^4 documental. `_RE_TOKENS` unificado linha 35. `_ngrama[3]/[4]` alimentado nas linhas 357-362. |

### `_nmi_semantico` — NMI Semântico

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/coupling.py` (linha ~2006) |
| **Fórmula** | `NMI = 2 * I(a;b) / (H(a) + H(b))` |
| **IDF** | `freq_inv = log(N / max(1, df))`, elevado a 4 |
| **Planos** | ctx, acao, posacao — cada um contribui igualmente |
| **Filtragem** | `_corte_dinamico` remove tokens de baixo IDF no contexto |
| **Notas** | Essencial para discriminação semântica. NMI puro retorna ~1.0 para qualquer par. Sem IDF, não discrimina. |

### `_assinatura_palavra` — Plano de features por palavra

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/coupling.py` (linha ~1845) |
| **Cache** | `_cache_assinatura` + `_assinatura_para_action` |
| **Planos** | 10 dimensões de features |

---

## 2. Chat e Interação

### `Chat` — Chat bidirecional com ciclo fechado

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/chat.py` |
| **Linhas** | 611 |
| **Classe** | `Chat` (ou equivalente) |
| **Métodos** | `interagir()`, `_tentar_base_conhecimento()`, `_analisar_cognitivo()` |
| **Fluxo** | coldstart → BC → decidir() → GeradorCoerente → auto-treinamento |
| **FASE 21** | `alimentar(resposta, acao)` após cada interação — ciclo Markoviano fechado |
| **FASEs 13/19** | `_analisar_cognitivo()` invoca Abstração + Causalidade via try/except lazy |
| **Auto-treinamento** | IDF + palavra-chave + palavras novas da resposta |

### `Triunvirato` — Busca ativa deliberativa

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/triunvirato.py` |
| **Linhas** | 239 |
| **Classe** | `Triunvirato` |
| **Métodos** | `decidir()` com 3 membros + consenso obrigatório (Pilar 10) |
| **Notas** | 3 perspectivas independentes deliberam até concordar |

### `GeradorCoerente` — Geração longa

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/gerador_coerente.py` |
| **Linhas** | 368 |
| **Classe** | `GeradorCoerente` |
| **Método principal** | `_gerar_candidatos()` |
| **Corte de ordem** | `_ngrama[3]` primário → `recentes` → `_transicao_palavra` (fallback) |
| **Working memory** | Mantém contexto de geração para evitar loops |

---

## 3. Auto-Conhecimento e Meta-Cognição

### `AutoConhecimento` — Alimentação temporal + identidade

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/auto_conhecimento.py` |
| **Linhas** | 118 |
| **Funções** | `alimentar_contexto_temporal()`, `alimentar_identidade()`, `alimentar_vocabulario()` |
| **Notas** | Alimenta o MCR com metadados sobre si mesmo |

### `AutoReferencia` — FASE 18: recursão meta-cognitiva

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/auto_referencia.py` |
| **Linhas** | 509 |
| **Classe** | `AutoReferencia` |
| **5 capacidades** | auto-observação, auto-diagnóstico, auto-limpeza, verificação, regressão |
| **Testes** | 64/64 PASS |
| **Notas** | Testa se o MCR reconhece próprio estado como dados |

### `AutoComposicao` — Clusterização NMI → especialistas

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/auto_composicao.py` |
| **Linhas** | 391 |
| **Funções** | `auto_compor()`, `_clusterizar_nmi()` |
| **Notas** | Cria especialistas (sub-MCRs) por similaridade semântica |

### `AutoExpansao` — Expansão automática

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/auto_expansao.py` |
| **Linhas** | 458 |
| **Funções** | `expandir_auto()`, `_gerar_variacoes()` |

### `MetaCognitivo` — Meta-cognição

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/meta_cognitivo.py` |
| **Linhas** | 455 |
| **Classe** | `MetaCognitivo` |

### `Metacognicao` — Meta-cognição (alternativa)

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/metacognicao.py` |
| **Linhas** | 311 |

### `Observador` — Observação externa

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/observador.py` |
| **Linhas** | 305 |
| **Classe** | `Observador` |
| **Notas** | Pipe de observação de estado externo |

### `Feedback` — Ciclo de feedback

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/feedback.py` |
| **Linhas** | 440 |
| **Funções** | `receber_feedback()`, `_ajustar_thresholds()` |

---

## 4. Abstração e Raciocínio

Módulos que conectam FASEs 13/19 e vão além do P(b|a) puro.

### `Abstracao` — FASE 13: padrões abstratos

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/abstracao.py` |
| **Linhas** | 574 |
| **Classe** | `Abstracao` |
| **Notas** | Conectada ao chat via `_analisar_cognitivo()` |

### `Causalidade` — FASE 19: relações causais

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/causalidade.py` |
| **Linhas** | 331 |
| **Classe** | `Causalidade` |

### `Superposicao` — Superposição de estados

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/superposicao.py` |
| **Linhas** | 184 |
| **Classe** | `Superposicao` |

### `Contrafactual` — Raciocínio contrafactual

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/contrafactual.py` |
| **Linhas** | 433 |
| **Classe** | `Contrafactual` |

### `TeoriaDaMente` — Modelagem do outro

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/teoria_da_mente.py` |
| **Linhas** | 399 |
| **Classe** | `TeoriaDaMente` |

### `GroundingAmbiental` — Grounding no ambiente

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/grounding_ambiental.py` |
| **Linhas** | 329 |

### `Raciocinador` — Raciocínio geral

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/raciocinador.py` |
| **Linhas** | 392 |
| **Classe** | `Raciocinador` |

### `RaciocinadorMK` — Raciocínio Markov

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/raciocinador_mk.py` |
| **Linhas** | 177 |
| **Classe** | `RaciocinadorMK` |

### `Planejador` — Planejamento

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/planejador.py` |
| **Linhas** | 387 |

### `TaskPlannerDAG` — Planejador DAG

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/task_planner_dag.py` |
| **Linhas** | 584 |

---

## 5. Hierarquia e Magnitudes

### `AcoplamentoHierarquico` — Hierarquia multi-escala

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/acoplamento_hierarquico.py` |
| **Linhas** | 326 |
| **Classe** | `AcoplamentoHierarquico` |
| **Notas** | Níveis 3-7 validados: palavra (sinonímia), frase (intenção 84%), texto (emoção 89%), corpus (estilo 87-100%) |

### `Coldstart` — Inicialização adaptativa

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/coldstart.py` |
| **Linhas** | 221 |
| **Classe** | `Coldstart` |
| **Notas** | Adapta comportamento inicial baseado em entropia do ambiente |

### `PerfilHumano` — Perfil isolado (LGPD)

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/perfil_humano.py` |
| **Linhas** | 241 |
| **Classe** | `PerfilHumano` |

### `CacheHierarquico` — Cache multi-nível

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/cache_hierarquico.py` |
| **Linhas** | 179 |

---

## 6. Features e Tokenização

### `TokenizadorUniversal` — Tokenizador unificado

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/tokenizador_universal.py` |
| **Linhas** | 116 |
| **Classe** | `TokenizadorUniversal` |
| **`_RE_TOKENS`** | `r'[a-zà-ÿ]{2,}|[0-9]+'` |
| **Notas** | Aplicado em `alimentar()`, `_dist_features`, `_dist_esfera`. 34 lugares restantes com regex `{3,}` — propagação pendente. |

### `ExtratorFeatures` — Features N-dim

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/extrator_features.py` |
| **Linhas** | 281 |
| **10 planos** | t (token), c (char), b (byte), bg (bigrama), ng (ngrama), p{i} (posição), ca (categoria), cd (cardeal), sl (sílaba), ngp (ngrama de palavras) |

### `Esfera` — Representação esférica

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/esfera.py` |
| **Linhas** | 109 |

### `Hiperesfera` — Representação hiperesférica

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/hiperesfera.py` |
| **Linhas** | 88 |

---

## 7. Base de Conhecimento e Memória

### `BaseConhecimento` — BC com NMI semântico

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/base_conhecimento.py` |
| **Linhas** | 190 |
| **Classe** | `BaseConhecimento` |
| **Ingestão** | `ingerir(texto, acao)` |
| **Recuperação** | `recuperar(consulta)` via `_nmi_semantico` |
| **Notas** | ~80 fatos. Pilar 5: BC sempre primeiro. |

### `Memory` — Memória geral

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/memory.py` |
| **Linhas** | 792 |
| **Classe** | `Memory` |

### `Knowledge Graph` — KG persistente

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/knowledge/kg.py` |
| **Linhas** | 500 |
| **Classe** | `KnowledgeGraph` |

### `EpisodicMemory` — Memória episódica

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/knowledge/episodic_memory.py` |
| **Linhas** | 356 |

### `EpisodicGateway` — Gateway episódico

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/episodic_gateway.py` |
| **Linhas** | 55 |

---

## 8. Equação e Esquecimento

### `EquacaoMCR` — Avaliação 5D

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/equacao_mcr.py` |
| **Linhas** | 120 |
| **Classe** | `EquacaoMCR` |
| **Fórmula** | Sigmoide 5D: divergência × especificidade × profundidade |
| **Notas** | Juiz de qualidade. Usada para avaliar composições. |

### `MCREsquecimento` — Poda por entropia

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/esquecimento.py` |
| **Linhas** | 78 |
| **Classe** | `MCREsquecimento` |
| **Notas** | Pilar 4: cadeia de Markov é esquecimento. Remove transições com entropia máxima. |

### `Signature` — Assinatura de bytes

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/signature.py` |
| **Linhas** | 258 |
| **Classe** | `MCRSignature` |

### `TemplateEntropico` — Template por entropia

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/template_entropico.py` |
| **Linhas** | 136 |

### `MCRMetaEquacao` — Meta da equação

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/meta_equacao.py` |
| **Linhas** | 264 |

---

## 9. Agentes e Decisão

### `Agente` — Agente MCR

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/agente.py` |
| **Linhas** | 387 |

### `AgenteMCRIntegrado` — Agente integrado

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/agente_mcr_integrado.py` |
| **Linhas** | 196 |

### `MasterAgent` — Agente mestre

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/master_agent.py` |
| **Linhas** | 1104 |

### `ConselhoMulti` — Conselho multi-arquétipo

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/conselho_multi.py` |
| **Linhas** | 744 |
| **Notas** | 7+ arquétipos deliberam em paralelo |

### `Ensemble7B` — Ensemble de modelos

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/ensemble_7b.py` |
| **Linhas** | 176 |

### `Decisor` — Decisor de ações (legado)

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/decisor.py` |
| **Linhas** | 300 |
| **Notas** | Substituído pelo `decidir()` do coupling. Manter para compatibilidade. |

### `MarkovRouter` — Roteador Markov

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/markov_router.py` |
| **Linhas** | 151 |

### `SemanticRouter` — Roteador semântico

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/semantic_router.py` |
| **Linhas** | 178 |

---

## 10. Emergência e Geração

### `Emergir` — Emergência de padrões

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/emergir.py` |
| **Linhas** | 365 |

### `EmergirCrossModal` — Emergência cross-modal

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/emergir_crossmodal.py` |
| **Linhas** | 264 |

### `EmergirUnificado` — Emergência unificada

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/emergir_unificado.py` |
| **Linhas** | 600 |

### `Genesis` — Gênese

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/genesis.py` |
| **Linhas** | 93 |

### `GeradorUniversal` — Gerador universal

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/gerador_universal.py` |
| **Linhas** | 162 |

### `GeradorCodigo` — Geração de código

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/gerador_codigo.py` |
| **Linhas** | 312 |

### `VariadorUniversal` — Variação de conteúdo

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/variador_universal.py` |
| **Linhas** | 130 |

### `GeneratorMultinivel` — Geração multi-nível

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/generator_multinivel.py` |
| **Linhas** | 71 |

---

## 11. Padrões e Análise

### `PatternEngineTexto` — Motor de padrões

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/pattern_engine_texto.py` |
| **Linhas** | 902 |
| **Classe** | `PatternEngine` |

### `PatternMiner` — Mineração de padrões

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/pattern_miner.py` |
| **Linhas** | 409 |

### `CodeAnalyzer` — Análise de código

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/code_analyzer.py` |
| **Linhas** | 203 |

### `CodeParser` — Parser de código

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/code_parser.py` |
| **Linhas** | 139 |

### `BranchSearch` — Busca em ramos

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/branch_search.py` |
| **Linhas** | 117 |

### `ChainOfVerification` — Cadeia de verificação

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/chain_of_verification.py` |
| **Linhas** | 259 |

### `CognitiveDecomposer` — Decomposição cognitiva

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/cognitive_decomposer.py` |
| **Linhas** | 84 |

### `Descobridor` — Descoberta automática

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/descobridor.py` |
| **Linhas** | 241 |

### `AutoCuriosidade` — Curiosidade artificial

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/auto_curiosidade.py` |
| **Linhas** | 123 |

---

## 12. Comunicação e Infra

### `Bridge` — Ponte de comunicação

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/bridge.py` |
| **Linhas** | 88 |

### `BridgeAPI` — API da ponte

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/bridge_api.py` |
| **Linhas** | 332 |

### `SSEServer` — Server SSE

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/sse_server.py` |
| **Linhas** | 477 |

### `Daemon` — Daemon MCR

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/daemon.py` |
| **Linhas** | 306 |

### `Bootstrap` — Inicialização do sistema

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/bootstrap.py` |
| **Linhas** | 269 |

### `Registry` — Registro de módulos

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/registry.py` |
| **Linhas** | 224 |

### `Paths` — Gerenciamento de caminhos

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/paths.py` |
| **Linhas** | 85 |

### `Persistence` — Persistência

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/persistence.py` |
| **Linhas** | 337 |

### `State` — Gerenciamento de estado

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/state.py` |
| **Linhas** | 166 |

### `Encoding` — Codificação

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/encoding.py` |
| **Linhas** | 142 |

### `SilentLog` — Log silencioso

| Campo | Valor |
|-------|-------|
| **Path** | `mcr/silent_log.py` |
| **Linhas** | 46 |

---

## 13. Ferramentas Cognitivas

Módulos de suporte a operações cognitivas específicas.

| Módulo | Linhas | Função |
|--------|--------|--------|
| `dialogue_miner.py` | 124 | Mineração de diálogos |
| `dialogue_trainer.py` | 185 | Treino de diálogos |
| `mcr_radar.py` | 289 | Busca por similaridade em 4 ondas |
| `mcr_signature_cluster.py` | 388 | Clusterização por assinatura |
| `mcr_sqlite.py` | 306 | Markov com SQLite |
| `sqlite_markov.py` | 231 | Versão importável do SQLite Markov |
| `mcr_auto_evolution.py` | 176 | Evolução automática de thresholds |
| `mcr_auto_loop.py` | 330 | Loop de auto-treinamento |
| `mcr_meta.py` | 223 | Meta-operações |
| `meta.py` | 482 | Meta-cognição base |
| `mcr_autobiography.py` | 101 | Autobiografia do sistema |
| `mcr_conversa.py` | 133 | Registro de conversas |
| `mcr_inner_voice.py` | 152 | Voz interior |
| `mcr_self.py` | 85 | Self do MCR |
| `mcr_world_system.py` | 840 | Sistema de mundo |
| `internal_monologue.py` | 99 | Monólogo interno |
| `context_buffer.py` | 45 | Buffer de contexto |
| `multimodal.py` | 562 | Integração multimodal |
| `mundo.py` | 74 | Mundo MCR |
| `conexao.py` | 79 | Conexão entre módulos |
| `hdc_core.py` | 159 | Código HD (Hyperdimensional) |
| `hdc_kg_memory.py` | 105 | Memória HD+KG |
| `sdm_core.py` | 207 | SDM (Sparse Distributed Memory) |
| `rag_mcr.py` | 286 | RAG (Retrieval Augmented Generation) |
| `few_shot.py` | 81 | Few-shot learning |
| `config_llm.py` | 13 | Configuração LLM |
| `prompts_criativos.py` | 202 | Prompts criativos |
| `pos_processamento.py` | 261 | Pós-processamento |
| `anti_pattern.py` | 169 | Anti-padrões |
| `truncation_fixer.py` | 160 | Correção de truncamento |
| `shadow_canary.py` | 441 | Mock de ambiente Canary |
| `fragmenter.py` | 360 | Fragmentação de texto |

---

## 14. Legado

Módulos que existem no diretório `mcr/` mas não fazem mais parte do pipeline ativo do motor. Mantidos para referência histórica ou compatibilidade.

| Módulo | Linhas | Substituído por | Status |
|--------|--------|----------------|--------|
| `mcr.py` (3422) | 3422 | `coupling.py` | Mantido para referência |
| `mcr_unificado.py` | 517 | `coupling.py` | Substituído |
| `pipeline_completo.py` | 770 | `chat.py` + coupling | Substituído |
| `system.py` | 910 | Modular | Legado |
| `evolution.py` | 454 | `auto_composicao.py` | Legado |
| `engine.py` | 463 | `coupling.py` | Legado |
| `decisor.py` | 300 | `coupling.decidir()` | Legado |
| `adaptadores.py` | 630 | modular | Legado |
| `mcr_world_system.py` | 840 | módulos específicos | Parcial |
| `sanity_validator.py` | 343 | — | Domínio Tibia |
| `sanity_validator_cpp.py` | 290 | — | Domínio Tibia |
| `sanity_validator_cs.py` | 543 | — | Domínio Tibia |
| `sanity_validator_sql.py` | 309 | — | Domínio Tibia |
| `lua_validator.py` | 194 | — | Domínio Tibia |
| `monster_database.py` | 139 | — | Domínio Tibia |
| `rede_npcs.py` | 173 | — | Domínio Tibia |

---

## 15. Métricas do Ecossistema

### Visão geral

| Métrica | Valor |
|---------|-------|
| **Módulos Python** | 133 (46.286 linhas) |
| **Arquivos de teste** | 164 |
| **Regressão Fase 1** | 113/113 = 100% |
| **Regressão Fase 18** | 64/64 PASS |
| **Observações ingeridas** | 167.434 (máx. testado) |
| **Vocabulário** | 214.907 palavras (máx. testado) |
| **Ações no motor** | 14+ |
| **Fontes no coupling** | 13 |
| **Planos N-dim** | 10 (t, c, b, bg, ng, p{i}, ca, cd, sl, ngp) |
| **Latência decidir()** | ~50ms |
| **Tempo treino (167K obs)** | ~30s |
| **Caches de performance** | 7 índices invertidos |

### Corpus ingerido

| Fonte | Frases | Status |
|-------|--------|--------|
| Wikipedia (240 conceitos × 5 idiomas) | 80.093 | Ingerido |
| Rosetta Code (27 algoritmos × 12 linguagens) | 4.052 | Ingerido |
| Corpus sintético (14 domínios, 70 conceitos, 3 idiomas) | 50.000 | Ingerido |
| Corpus matemático (7 regras, 700 obs) | 700 | Ingerido |
| Gutenberg | 416.993 | **NÃO ingerido** (dilui) |

### Descobertas validadas

| Descoberta | Valor | Tipo |
|-----------|-------|------|
| Sinônimos cross-idioma | amor~love=0.335 | Emergente |
| Regras matemáticas | 17/17 zero-shot | Emergente |
| Universalidade | 5 domínios | Emergente |
| Intenção (nível 4) | 84% pureza | Emergente |
| Emoção (nível 5) | 89% pureza | Emergente |
| Estilo (nível 6) | 87-100% pureza | Emergente |
| Lift vs raw decidir() | 80% vs 0% | Discriminativo |
| Zoom lift (3 escalas) | 4/4 + 5/5 + 2/4 | Invariante |
| MCR observador (sem rótulos) | 66.7% | Agrupamento natural |
| Seleção natural Markoviana | 26× mais frequente | Emergente |

### Limitações documentadas

1. Markov de 1ª ordem — dependências longas não modeladas
2. Zero-shot de palavras novas não funciona
3. P(b|a) bruto não discrimina auto-conhecimento — precisa lift/IDF/NMI
4. Self (nível 7) não emerge em MCR individual
5. Gutenberg não ingerido (dilui discriminação)
6. 167K obs testado — escalas maiores não verificadas
