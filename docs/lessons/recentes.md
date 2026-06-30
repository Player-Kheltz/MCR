# Licoes Recentes

## 2026-06-30 — Sessao AGI completa: ReAct + Busca Estrategica + BlankFiller + 5 camadas

### Resumo
Sessao mais produtiva ate agora. Implementamos a arquitetura AGI completa em 5 camadas, substituimos o pipeline cascade fixo por ReAct loop dinamico, criamos busca estrategica para descoberta de codigo real, e integramos BlankFiller para criacao segura.

### O que foi feito

1. **FASE 1 — SENSE** (completa):
   - Security: filtra input malicioso
   - ContextCrew: 5 fontes de contexto (KG, WebLearn, Docs, Codigo, Web)
   - EpisodicMemory: busca experiencias passadas similares
   - ContextInfinity: historico de sessao
   - KG.aprender(): toda resposta vira lesson

2. **FASE 2 — THINK** (completa):
   - Decider.classificar(): classifica tipo de pergunta
   - Mente.think(kg=None): reflexao 1.5b, ~3s, cache 5min
   - Sem KG pesado (evita 120s de delay)

3. **FASE 3 — VALIDATE** (completa):
   - V1-V9 ValidationPipeline
   - AutoRevisor: detecta alucinacoes heuristicas
   - Tradutor: garante PT-BR

4. **FASE 4 — LEARN** (completa):
   - KG.aprender() em todas as respostas
   - EpisodicMemory.registrar() guarda experiencias
   - Emergir a cada 5 execucoes
   - SelfStudy thread background a cada 10min

5. **ReAct Loop** (substituiu cascade fixo):
   - LLM pede ferramentas via [FER: ...]
   - Sistema executa e retorna resultado
   - Ciclo se repete ate LLM finalizar
   - Seed automatico com buscar_estrategico no primeiro ciclo

6. **Busca Estrategica** (tool_orchestrator.py):
   - `buscar_estrategico(termo)`: descobre diretorios, explora arquivos .lua, encontra funcoes reais
   - Profundidade maxima 6, exclui dependencias (vcpkg, node_modules, etc.)
   - Match por palavra (nao substring) para evitar falsos positivos
   - Retorna em 0.1-2s (vs os.walk que timeout em 15s)

7. **BlankFiller** (ja existia, agora integrado):
   - `gerar_esqueleto(contexto, tipo)`: gera estrutura com @BLANK_N
   - `preencher_blank(esqueleto, blank_id, contexto)`: preenche um blank

8. **TruncationFixer corrigido**: adicionado `str(...)[:N]` como excecao

### Problemas Identificados e Solucoes

- **TruncationFixer removia `[:1500]` do codigo**: Regex `(?<!sys\.path)\[\s*\:[\s\w\d]+\]` capturava `str(x)[:1500]`. Solucao: adicionar `str\(.*?\)\[:\d+\]` como excecao.
- **Enricher gerava 156K chars**: Contexto estourava 4096 tokens do modelo 14b. Solucao: limitar cada secao a <2000 chars.
- **Keyword boost em TODAS as lessons**: Todas as lessons seed mencionavam "MCR". Solucao: boost apenas no `erro`, nao na `solucao`.
- **Mente.think() com KG pesado**: 376K chars de KG, 120s por pergunta. Solucao: passar `kg=None` para Mente.
- **ReAct LLM ignorava ferramentas**: LLM respondia direto sem explorar. Solucao: seed automatico com `buscar_estrategico` no primeiro ciclo.

### Resultados dos Testes

| Teste | Nota | Tempo |
|-------|------|-------|
| Teste de Verdade (7 perguntas) | 7/7 PASS (10/10) | 344.8s |
| Teste Complexo (SPA + SHC + Lua + Lore) | 8.0/10 | 89.0s |
| Teste Criacao (3 combos SPA) | 8.6/10 | 71.8s |
| Teste ReAct (tool calling) | 8.5/10 | 36.0s |

### Arquivos Modificados/Criados

- `modulos/pipeline_executor.py`: ReAct loop, seed, ferramentas completas (MAJOR rewrite do cascade)
- `modulos/tool_orchestrator.py`: +buscar_estrategico, +buscar_inteligente, filtros de cache
- `modulos/reconstructor.py`: Keyword boost no erro, filtro resposta_*, +termos_pergunta
- `modulos/truncation_fixer.py`: Excecao `str(...)[:N]`
- `modulos/validation_pipeline.py`: Fix V4 (coerente/negacao)
- `kernel.py`: SelfStudy thread background
- `tests/test_verdade.py`: Normalizacao de acentos
- `tests/test_complexo.py` (novo): Teste AGI completo
- `tests/test_react.py` (novo): Teste ReAct tool calling
- `tests/test_criacao.py` (novo): Teste de criacao de codigo
- `docs/plano/AGI_ARCHITECTURE.md`: Plano completo atualizado

### Pendentes

1. **Testar com `--fast` para verificar performance com modelo 7b**
2. **KGCleaner automatico**: marcar lessons poluentes como inactive no startup
3. **DataCanary NPC System**: aplicar o novo pipeline ReAct para geracao de NPCs
4. **Dashboard SSE**: conectar o ReAct Loop ao SSE Server para visualizacao em tempo real
5. **ContextCrew + WebLearn automatico**: quando ReAct nao encontrar dados, disparar weblearn
6. **Validar se o SelfStudy esta rodando corretamente em background**

### Licoes Aprendidas

> **O pipeline fixo morreu. Viva o ReAct.** O cascade de niveis (tool → kg → enricher → llm) era rigido e limitava o raciocinio do LLM. O ReAct Loop permite que o LLM DECIDA o que investigar, em que ordem, e quando parar.
>
> **Seed beats instruction.** O LLM IGNORA instrucoes ("use as ferramentas") mas USA os dados se estiverem no prompt. Semear o ReAct com `buscar_estrategico` no primeiro ciclo garante que o LLM veja dados reais.
>
> **Busca por palavra, nao substring.** "SPA" em "spatial" e falso positivo. Dividir o nome do diretorio em partes (`SPA`, `core`, `postura`) e comparar cada parte evita matches espurios.
>
> **Contexto limitado a <7000 chars.** Modelo 14b tem 4096 tokens (~16K chars). Com identidade + ferramentas + contexto, o prompt total deve ficar abaixo de 7K chars para garantir que o modelo veja tudo.
>
> **TruncationFixer e um faca de dois gumes.** Remove `[:N]` que sao uteis (limites de contexto). A excecao `str(...)[:N]` foi essencial.
