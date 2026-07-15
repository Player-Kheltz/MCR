# Módulos Órfãos — Varredura Curada

Módulos funcionais, não integrados ao pipeline `mcr/`, com potencial de preencher lacunas.

---

## Geração de NPC (substituir/expandir LLM)

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `npc_generator.py` | `devia/modules/` | Gera Lua de NPC Canary por template + LLM. 6 tipos (shop, quest, bank, gate, trainer, dialogue). Templates extraídos de NPCs reais. | **Funcional** |
| `comandos.py (prototype)` | `prototypes/mcr-universal/mcr/generate/` | Método `gerar_npc()` + `lore()` por assinatura Markov. Gera nomes e conteúdo descritivo. | **Funcional** |
| `generator.py (prototype)` | `prototypes/mcr-universal/mcr/generate/` | Gerador universal: `_gerar_codigo()`, `_gerar_nome()`. Usa Markov + Preencher + Validator. | **Funcional** |
| `preencher.py (prototype)` | `prototypes/mcr-universal/mcr/generate/` | Preenche `@BLANK_*` em templates via Markov (zero LLM). | **Funcional** |
| `builder.py (prototype)` | `prototypes/mcr-universal/mcr/generate/` | Extrai blocos de código, monta estrutura de arquivo por `@BLOCK`, salva em disco. | **Funcional** |
| `engine.py (mcr_dev)` | `historia/scripts/mcr_dev/` | Pipeline completo de geração: router → find example → generate (Qwen 7B) → validate → save → learn. 401 linhas. | **Funcional** |
| `create.py` | `historia/scripts/` | Gerador template-based: dominio, habilidade, monster, item, spell, NPC, quest. 552 linhas. | **Funcional** |

---

## Validação de Lua/Canary

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `lua_validator.py` | `devia/modules/` | Valida sintaxe Lua, SQL injection, boas práticas Canary (register, createNpcType), estrutura obrigatória. | **Funcional** |
| `validator.py (prototype)` | `prototypes/mcr-universal/mcr/generate/` | Validador universal por coerência byte/word/token contra padrões aprendidos. | **Funcional** |
| `guardrail.py (prototype)` | `prototypes/mcr-universal/mcr/hybrid/` | Guardrail de saída LLM: entropia + coerência + Jaccard. Rejeita sem chamar LLM de novo. | **Funcional** |
| `validador.py (mcr_dev)` | `historia/scripts/mcr_dev/` | Validadores por tipo: NPC, HABILIDADE, MONSTER, ITEM, SPELL, QUEST. | **Funcional** |
| `sandbox.py` | `historia/scripts/mcr_devia/tools/` | Executa código em isolamento: Python (exec), Lua (luac compile), Shell (timeout). | **Funcional** |
| `auto_revisor.py` | `devia/modules/` + `analysis/` | Pós-geração: detecta classes alucinadas, nomes inconsistentes, auto-corrige. | **Funcional** |

---

## Roteamento (MCR path + detecção de intenção)

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `classifier.py (prototype)` | `prototypes/mcr-universal/mcr/hybrid/` | Decide MCR vs LLM por entropia + cobertura + gap detection. Essência do roteador universal. | **Funcional** |
| `pipeline.py (prototype)` | `prototypes/mcr-universal/mcr/hybrid/` | Pipeline híbrido de 6 passos: Classifier → MCR/LLM → Guardrail → max 2 ciclos → custo. | **Funcional** |
| `MarkovRouter.py` | `devia/kernel/` | Estado → próxima ação via Markov puro. Aprendizado real com MCR + persistência JSON. | **Funcional** |
| `router.py (mcr_dev)` | `historia/scripts/mcr_dev/` | Classificador de intenção via Qwen 1.5B + regex. 90% acurácia. Roteia para NPC, skill, item. | **Funcional** |
| `decider.py` | `devia/analysis/` | Classificador universal: FAST model + fallback determinístico. Cache LRU com TTL. | **Funcional** |

---

## Aprendizado e Memória

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `episodic_memory.py` | `devia/modules/` + `knowledge/` | Armazena experiências (request + resultado + lesson) com embeddings + fallback keyword. | **Funcional** |
| `learn/fuel.py (prototype)` | `prototypes/mcr-universal/mcr/learn/` | Ingere `.py/.md/.txt/.lua/.json` para ensinar padrões ao motor Markov. Já inclui `.lua`. | **Funcional** |
| `learn/weblearn.py (prototype)` | `prototypes/mcr-universal/mcr/learn/` | Aprendizado da web: busca Wikipedia, HTML `<p>`, alimenta motor MCR. | **Funcional** |
| `memoria.py (mcr_dev)` | `historia/scripts/mcr_dev/` | Aprendizado contínuo: salva/carrega conhecimento aprendido em `.learn_db/mcr_dev.json`. | **Funcional** |
| `lessons_buffer.py` | `devia/knowledge/` | Buffer de conhecimento pré-KG: deduplicação, detecção de contradição, resolução via ContextCrew. | **Funcional** |
| `FeedbackFilter.py` | `devia/kernel/` | Previne contaminação do KG: filtra por entropia, tamanho, repetição, template. | **Funcional** |
| `feedback/self_heal.py (prototype)` | `prototypes/mcr-universal/mcr/feedback/` | Auto-cura: detecta resultado baixa qualidade, regenera com contexto extra do motor. | **Funcional** |

---

## Worldbuilding e Lore

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `context_enricher.py` | `devia/modules/` | Gera conteúdo novo: nomes próprios para lore, dados técnicos, curiosidades. Lista anti-alucinação. | **Funcional** |
| `emergir.py` | `devia/modules/` | `EmergirEngine` — descobre conexões emergentes entre tópicos distantes do KG. Gera insights Z. | **Funcional** |
| `item_database.py` | `devia/knowledge/` | Wrapper completo sobre items.xml do Canary. Busca fuzzy por nome, ID, categoria. Cache LRU. | **Funcional** |
| `ingest_canary.py` | `devia/kernel/` | Indexa scripts Lua e XML do Canary no ChromaDB. Chunking por função Lua. | **Funcional** |
| `rag_mcr.py` | `devia/kernel/` | RAG via ChromaDB + nomic-embed-text. Indexa docs do projeto para recuperação contextual. | **Funcional** |
| `npc_vivo.py` | `devia/kernel/` | NPC vivo: emoções, personalidade, máquina de estados, diálogo. Usa HD + SDM. 9 tipos de personalidade. | **Funcional** |
| `percepcao.py` | `devia/kernel/` | Converte estado do mundo (posição, jogadores, itens) em HD vectors 10k-dim. | **Funcional** |
| `amplificador_lore.py` | `historia/sandbox/` | Geração de lore auto-crescente: cada domínio tem seu Markov. Ciclo: gera → KG → corpus cresce → gera mais. 531 linhas. | **Funcional** |

---

## Infraestrutura de Geração (engines de baixo nível)

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `blank_filler.py` | `devia/knowledge/` | Preenche blanks de template via IA: gera esqueleto → extrai blanks → preenche cada um → monta final. | **Funcional** |
| `DeterministicFiller.py` | `devia/kernel/` | Valores determinísticos para geração: domínio → cor, skill → cooldown, NPC → outfit/vida/comportamento. | **Funcional** |
| `TemplateExtractor.py` | `devia/kernel/` | Extrai esqueleto estrutural de arquivos similares. Identifica fixo vs variável → template com placeholders. | **Funcional** |
| `hdc_core.py` | `devia/kernel/` | Hiperdimensional Computing: vetores 10k-dim aleatórios, bundling, binding, similaridade cosseno. | **Funcional** |
| `sdm_core.py` | `devia/kernel/` | Sparse Distributed Memory: projeta 10k-dim → 200-dim, armazena/recupera por raio de ativação. | **Funcional** |
| `emergence/conexao.py (prototype)` | `prototypes/mcr-universal/mcr/emergence/` | Otimizador de pontes Markov: encontra conexão ótima entre duas cadeias. | **Funcional** |
| `intelligence/radar.py (prototype)` | `prototypes/mcr-universal/mcr/intelligence/` | Scanner de padrões: detecta loops, gaps de conhecimento, sugere próximo passo. | **Funcional** |
| `core/entropia.py (prototype)` | `prototypes/mcr-universal/mcr/core/` | Detector de loop por entropia: rastreia histórico, detecta repetição. | **Funcional** |
| `feedback/peso_nota.py (prototype)` | `prototypes/mcr-universal/mcr/feedback/` | Otimizador de pesos para equação MCR ideal. | **Funcional** |

---

## Pipeline AGI Completo (end-to-end, zero LLM)

| Módulo | Path | O que faz | Status |
|--------|------|-----------|--------|
| `prototipo_ciclo_completo.py` | `historia/sandbox/` | Ciclo completo MCR sem LLM. 8 fases: percepção, contexto, geração, criação, bug, correção, validação, aprendizado. | **Funcional** |
| `prototipo_inception.py` | `historia/sandbox/` | Conselho de Padrões: MCR convoca workers com diferentes temperaturas + validadores + seleção do melhor. | **Funcional** |
| `prototipo_omni.py` | `historia/sandbox/` | PatternEngine omnidirecional: ciclos até entropia < 0.3. | **Funcional** |
| `prototipo_mcr_conectado.py` | `historia/sandbox/` | MCR alimentado por dados reais. 5 níveis Markov. | **Funcional** |
| `auto_loop.py (prototype)` | `prototypes/mcr-universal/mcr/emergence/` | Loop contínuo de melhoria: executa → avalia → expande → checkpoint. | **Funcional** |
| `session_cache.py` | `devia/modules/` | Cache de sessão para retomar pipeline interrompido. | **Funcional** |

---

## Top 5 para Integração Imediata

| # | Módulo | Lacuna que preenche | Linhas |
|---|--------|---------------------|--------|
| 1 | `hybrid/pipeline.py (prototype)` | Roteamento MCR↔LLM com guardrail + custo | ~200 |
| 2 | `lua_validator.py (devia/modules/)` | Validação específica Canary além do ShadowCanary genérico | ~250 |
| 3 | `npc_generator.py (devia/modules/)` | Templates de NPC extraídos de NPCs reais | ~600 |
| 4 | `item_database.py (devia/knowledge/)` | Dados reais de items.xml para NPCs de loja | ~400 |
| 5 | `learn/fuel.py (prototype)` | Ingestão de `.lua` no motor Markov | ~120 |
