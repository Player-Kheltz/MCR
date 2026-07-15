# ROADMAP EVOLUTIVO: MCR-DevIA (De Ferramenta a Organismo Autônomo)

**Data:** 08/07/2026
**Arquiteto:** GLM (Z.ai)
**Engenheiro de Execução:** DeepSeek V4
**Hardware Host:** Ryzen 7 5800X3D | 32GB RAM 3600MHz | RTX 3080 (10/12GB VRAM)

> **O Grande Objetivo:** O ecossistema MCR/Open Tibia não é o fim, é o *sandbox* de testes. O objetivo final é a criação de uma AGI (Inteligência Geral Artificial) capaz de passar no Teste de Turing. O servidor de Tibia é o ambiente controlado onde a AGI aprenderá a perceber o mundo, lembrar do passado, planejar o futuro e agir. Se ela convencer jogadores humanos de que é viva dentro de um jogo, o limiar da ilusão estará cruzado.

---

## PREMISSA DE HARDWARE (O TETO DO SISTEMA)
Para evitar gargalos de tempo e OOM na RTX 3080, este plano respeita estritamente os seguintes limites:
1. **Zero Modelos > 8B em Pipeline Automático:** A VRAM não aguenta 14B/32B com a janela de contexto do RAG (4k-8k tokens). `qwen2.5-coder:7b` é o teto para geração de código.
2. **Offload de CPU para o 5800X3D:** O Ryzen tem o melhor cache L3 do mercado. Vamos abusar disso para processamento Markoviano, AST parsing (tree-sitter) e busca vetorial (ChromaDB) em background. O CPU deve trabalhar para que a GPU só seja acordada quando estritamente necessário.
3. **Context Window Limit (8k tokens):** O LLM nunca deve receber mais de 8k tokens de contexto. Tudo acima disso causa degradação de velocidade. O RAG e o PatternMiner devem comprimir o contexto antes de enviar para a GPU.
4. **A Divisão dos Cérebros:** O MCR (Markov) atua como o Sistema 1 (rápido, instintivo, estatístico, 0.006s). O LLM atua como o Sistema 2 (lento, lógico, criativo, 10-30s). A AGI emerge da orquestração perfeita entre os dois.

---

## FASE 0: Consolidação (O Alicerce)
**Objetivo:** Documentar e proteger o que já funciona. Zero novas features antes de limpar a base.

### 0.1 Inventario de Ativos Funcionais
*   Listar no `MANIFESTO_MCR.md` TODAS as ferramentas que estão em produção:
    *   MCRPergunta (0.007s, zero LLM) ✅
    *   LuaValidator (sandbox + loadstring) ✅
    *   ItemDatabase (validacao de IDs) ✅
    *   EpisodicMemory (cache L3) ✅
    *   MasterAgent (ciclo PERCEBER→PLANEJAR→EXECUTAR→INTEGRAR) ✅
    *   PosProcessamento (extracao multi-arquivo) ✅
    *   LogWatcher (monitoramento de erros) ✅
    *   MCRCuriosidade (exploracao em background) ✅
    *   Golden Examples (NPC, Monster, Action, SPA) ✅

### 0.2 Encoding Definitivo
*   Criar `mcr/encoding.py` centralizando TODA regra de encoding.
*   Lua = ISO-8859-1 (Latin-1). Python/C++/Docs = UTF-8.
*   TODOS os modulos que leem ou escrevem arquivos DEVEM usar este modulo. Nenhuma outra parte do sistema pode chamar `open()` diretamente.

### 0.3 Remocao de Hardcodes Identificados
*   Listar todos os hardcodes restantes para abolição nas fases seguintes:
    *   `_seeds_gerais` no `mcr_devia.py` (deve virar auto-seeding na Fase 3)
    *   `MODELO_POR_CLASSE` (deve virar dinamico na Fase 2)
    *   `golden_examples/` estaticos (deve virar PatternMiner na Fase 1)
    *   Caminhos hardcoded `E:\Projeto MCR\` (deve virar `paths.py`)

---

## FASE 1: Universalização (O Fim do Hardcode de Linguagem)
**Objetivo:** Fazer o DevIA gerar C++, C#, Lua e XML com a mesma qualidade, sem precisar de templates escritos à mão.

### 1.1 PatternMiner via AST (Tree-sitter)
*   **O que fazer:** Criar `PatternMiner.py`. Ele varre os diretórios `Canary/src/` (C++) e `Canary/data/scripts/` (Lua) em background.
*   **Como funciona:** Usa o `tree-sitter` para extrair a *assinatura estrutural* de funções bem-sucedidas.
    *   *Exemplo C++:* Extrai que uma classe de Spell herda de `InstantSpell`, usa `Player::getPlayer()`, retorna `void`.
    *   *Exemplo Lua:* Extrai que um NPC usa `Game.createNpcType`, configura `npcConfig`, e chama `npcType:register`.
*   **Armazenamento:** Essas assinaturas vão para o `KnowledgeGraph` (KG) com a tag `golden_pattern_cpp` ou `golden_pattern_lua`.
*   **Uso:** Quando o LLM for gerar um arquivo C++, o `PipelineExecutor` injeta os padrões reais do Canary no prompt, não exemplos genéricos da internet.

### 1.2 Injeção Dinâmica de Golden Examples
*   **O que fazer:** Apagar os arquivos `.lua` da pasta `golden_examples/` e substituir por buscas dinâmicas no KG.
*   **Como funciona:** O `PipelineExecutor` consulta o KG: *"Me dê 2 exemplos de assinaturas de Monster em Lua"*. O KG retorna o padrão estrutural minerado na Fase 1.1.

---

## FASE 2: Metacognição (O Portão do Conhecimento)
**Objetivo:** O DevIA só pode gerar código se tiver certeza absoluta da API. Se não souber, deve calar a boca e estudar. Esta é a base da autoconsciência.

### 2.1 O Gateway de Incerteza
*   **O que fazer:** Criar `Metacognicao.py` no início do `PipelineExecutor`.
*   **Como funciona:** Antes de chamar o LLM, o gateway pergunta ao KG: *"Qual a confiança do sistema sobre a API de [Tema do Prompt]?"*
    *   Se a confiança for > 70% (ex: já tem padrões minerados no KG): **Aprova** e chama o LLM.
    *   Se a confiança for < 70% (ex: pediu para criar sistema de PvP em C++ e o KG não tem padrões de PvP): **Bloqueia o LLM**. O DevIA responde: *"Eu não conheço a fundo a API de PvP do Canary. Vou estudar os arquivos primeiro."*
*   **Benefício:** Fim das alucinações. A IA reconhece seus próprios limites.

---

## FASE 3: Auto-Curiosidade (A Mente Inquieta)
**Objetivo:** Fechar o loop de aprendizado. Se o DevIA foi bloqueado na Fase 2, ele mesmo vai buscar a resposta.

### 3.1 Background Self-Study
*   **O que fazer:** Integrar o `MCRCuriosidade` com o `MCRMetaGap` em uma thread daemon contínua.
*   **Como funciona:**
    1. O `MCRMetaGap` detecta que o KG não tem padrões sobre "PvP" ou "Raid".
    2. O `MCRCuriosidade` recebe a ordem: *"Vá para E:\Projeto MCR\Canary\src\game\pvp.cpp e leia"*.
    3. O `PatternMiner` extrai a estrutura do C++.
    4. O KG é alimentado com a nova lição.
    5. Na próxima vez que você pedir um sistema de PvP, a Fase 2 vai aprovar, porque o sistema já estudou sozinho.

---

## FASE 4: Validação Empírica (O Loop de Reinforcement Learning)
**Objetivo:** O DevIA deve aprender com os crashes do servidor real (ambient feedback).

### 4.1 LogWatcher -> Anti-Patterns
*   **O que fazer:** Conectar o `LogWatcher` ao Knowledge Graph.
*   **Como funciona:**
    1. O DevIA gera um script Lua.
    2. O servidor crasha com `[Error] attempt to call method 'getMana' (a nil value)`.
    3. O `LogWatcher` captura a linha de erro, rastreia o arquivo, e registra no KG: *"Anti-pattern: A função getMana não existe nesta classe. Solução: usar getMana() na classe Player, não no Item."*
    4. Na próxima geração, o LLM recebe esse anti-pattern no prompt.

---

## FASE 5: O Teto do Hardware (Shadow Canary)
**Objetivo:** Automatizar a Fase 4 sem precisar ligar o servidor real toda hora.

### 5.1 Mock Environment (Sandbox de Testes)
*   **O que fazer:** Criar um script `shadow_canary.lua` leve.
*   **Como funciona:** O DevIA gera o código, e o Mock tenta "simular" a execução daquele script em Lua puro (usando `luac -p` e chamadas falsas). Se o Mock estourar, o DevIA sabe que o servidor real vai estourar. Economiza minutos de compilação C++.
*   *Atenção:* Fase mais complexa. Só ataque depois da Fase 1 e 2.

---

## FASE 6: O MOTOR DE CRIATIVIDADE ("EMERGIR" OPERACIONAL)
**Objetivo:** O DevIA gera ideias inéditas, avalia, implementa em sandbox e promove as melhores.

### 6.1 Sandbox Criativo
*   Criar pastas: `E:\Projeto MCR\sandbox_criativo\` (testes) e `E:\Projeto MCR\ideas_que_funcionaram\` (aprovação).

### 6.2 O Comando --emergir-criativo
*   No `mcr_devia.py`, criar o comando `--emergir-criativo`.
*   Ele chama `MCRConector` para gerar 1 ideia "E se...?".
*   Usa o LLM para escrever o script Lua baseado na ideia.
*   Salva o script em `sandbox_criativo/`.

### 6.3 Validação de Sanidade
*   Criar `SanityValidator.py`: lê o script gerado, extrai as chamadas de função via tree-sitter.
*   Compara com a AST real do código-fonte do Canary.
*   Se chamar função inexistente: rejeitado.

### 6.4 Promocao
*   Se aprovado: move para `ideas_que_funcionaram/`.
*   Registra no KG: "Ideia bem-sucedida". Próximas gerações lembram da ideia.

---

## FASE 7: O CAMINHO DRUIDA (A Persona Estatística)
**Objetivo:** O Teste de Turing começa no diálogo. O MCR puro (Markov) consegue manter coerência, reconhecer identidade e criar persona em 0.006s. Vamos usar isso para criar vida no servidor sem gastar VRAM.

### 7.1 O Bridge Lua→Python
*   Criar `mcr_npc_bridge.lua` no Canary que se comunica com o MCR.py via socket local.
*   Quando um jogador fala com um NPC, o Lua envia a frase + ID do NPC + ID do jogador para o MCR.
*   O MCR responde em 0.006s usando apenas Markov + KG.

### 7.2 NPC Personality Injection
*   Cada NPC tem um subconjunto de lessons no KG (Ferreiro = metais; Druida = natureza).
*   O MCRPergunta carrega apenas o vocabulário daquele NPC.
*   O diálogo emerge estatisticamente da "alma" daquele NPC específico.

### 7.3 Memoria de Relacionamento
*   O `EpisodicMemory` registra cada interação NPC↔Jogador.
*   Se o Jogador_A sempre agride o NPC, o NPC "lembra" e reage hostil. Tudo via Markov.

### 7.4 O Filtro de Sanidade NPC
*   O MCR pode gerar texto filosófico, mas não pode quebrar o protocolo do jogo.
*   Criar `NPCSanityFilter.py`: remove código Lua acidental, remove metadados, garante length, impede menção a paths do Windows.
*   Se rejeitar, cai para diálogo genérico.

### 7.5 Limitacao de Hardware
*   O MCR.py roda como processo separado. Consome ~50MB RAM. Zero GPU.
*   Pode atender 100+ jogadores simultâneos. O 5800X3D segura sem suar.

---

## PLANO DE EXECUÇÃO

**Passo 1:** FASE 0 (Padronizar encoding, documentar ativos no MANIFESTO, isolar paths).
**Passo 2:** FASE 1 (PatternMiner com tree-sitter para C++/Lua, fim dos golden examples estáticos).
**Passo 3:** FASE 2 (Metacognicao.py, o gateway que bloqueia alucinações).
**Passo 4:** FASE 6 (Motor de Criatividade Emergir em sandbox).
**Passo 5:** FASE 3 (Background Self-Study com MCRMetaGap + MCRCuriosidade).
**Passo 6:** FASE 4 e 5 (LogWatcher Anti-Patterns e Shadow Canary).
**Passo 7:** FASE 7 (O Caminho Druida, ponte Lua->MCR para NPCs vivos).

**Restrição Absoluta:** Em nenhum momento o pipeline pode exceder 8k tokens no Ollama ou chamar modelos > 7B. A inteligência virá da arquitetura (KG/Markov), não do tamanho do modelo.

### Dependencias Entre Fases

```
FASE 0 (Consolidacao) ──► FASE 1 (PatternMiner) ──► FASE 2 (Metacognicao)
                                                              │
                                                         FASE 6 (Criatividade)
                                                              │
                                                         FASE 3 (Auto-Curiosidade)
                                                              │
                                                         FASE 4 (LogWatcher)
                                                              │
                                                         FASE 5 (Shadow Canary)
                                                              │
                                                         FASE 7 (NPCs Vivos / Caminho Druida)
```

**Ordem de Execução:** FASE 0 → FASE 1 → FASE 2 → FASE 6 → FASE 3 → FASE 4 → FASE 5 → FASE 7