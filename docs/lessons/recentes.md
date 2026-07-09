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

## 2026-07-01 — MCR'zificacao: FiltroMCR nativo no kg + MCR.py unificado

### Resumo
Sessao de MCR'zificacao pratica. Integramos o FiltroMCR (Jaccard de bytes) NATIVAMENTE no `kg.buscar()`, atualizamos o `MCR.py` (que ja tinha autoavaliacao por Jaccard, Decisor, Loop), e MCR'zificamos o `auto_trigger.py` para usar MarkovDecisor.

### O que foi feito

1. **FiltroMCR nativo no kg.buscar()**:
   - `kg.buscar()` agora aceita `pergunta=` para ativar re-ranqueio por Jaccard de bytes
   - Nota MCR = 70% keyword score + 30% Jaccard * 50
   - SEM filtro: lesson irrelevante (#1) "5 metodos em master_agent.py"
   - COM filtro: lesson relevante (#1) "SPA = Sistema de Progressao do Aventureiro"
   - Jaccard SPA=0.224 vs master_agent=0.119 (diferenca 0.104)

2. **MCR.py atualizado**:
   - `_executar()` agora passa `pergunta=` para `kg.buscar()` — ativa FiltroMCR nativo
   - `_responder()` tbm usa `pergunta=` — resposta foi de 5.1 para 8.7/10
   - IE movido de lazy import para `__init__` (criado uma vez)
   - Adicionado `__main__` com teste rapido

3. **auto_trigger.py MCR'zificado**:
   - `_get_rota()` tenta MCR.MarkovDecisor primeiro
   - Fallback para ROTAS hardcoded quando MCR nao disponivel
   - Traducao de acoes MCR para ferramentas auto_trigger

4. **14 prototipos revisados**:
   - 3760+ linhas de prototipos analisados
   - Conceitos validados: MarkovUniversal, Jaccard de bytes, Fingerprint RAW (sem INTENT_*)
   - Autoavaliacao por tipos ERA FALSA — Jaccard de bytes e a metrica REAL

### Problemas Identificados e Solucoes

- **kg.buscar() sem FiltroMCR**: Lesson "5 metodos em master_agent" era #1 para pergunta "Explique SPA". Solucao: `buscar()` agora aceita `pergunta=` que re-ranqueia por Jaccard de bytes.
- **Autoavaliacao por tipos e FALSA**: Cobertura de tipos (ANTES) dava nota alta para resposta errada. Solucao: ja estava corrigida no MCR.py (usa Jaccard).
- **MCR.py nao passava pergunta= para kg.buscar()**: O FiltroMCR so existia no MCR, nao no KG. Solucao: `_executar()` e `_responder()` agora passam `pergunta=`.
- **auto_trigger.py com ROTAS fixas**: Decisao de ferramentas era hardcoded. Solucao: `_get_rota()` tenta MCR.MarkovDecisor primeiro.

### Resultados dos Testes

| Teste | Metricas | Status |
|-------|----------|--------|
| FiltroMCR no kg.buscar() | Irrelevante caiu de #1 para #3. Relevante foi de #2 para #1. | ✅ OK |
| Jaccard discrimina relevancia | SPA=0.224 vs master_agent=0.119 (diferenca 0.104) | ✅ OK |
| MCRAutoLoop com FiltroMCR | SPA: 5.1 -> 8.7/10. Canary: 8.3/10 com KG | ✅ Melhorou |
| MarkovUniversal standalone | Jaccard SPA/SPA=1.0, SPA/NPC=0.0 | ✅ OK |
| auto_trigger MCR path | MarkovDecisor acionado via _get_rota() | ✅ Integrado |

### Arquivos Modificados

- `modulos/kg.py`: `buscar()` ganhou parametro `pergunta=` + metodo `_jaccard_bytes()` + re-ranqueio MCR
- `modulos/MCR.py`: `_executar()` passa `pergunta=` p/ kg.buscar(); `_responder()` idem; IE movido p/ __init__; `__main__` adicionado
- `modulos/auto_trigger.py`: `__init__` carrega MCR opcional; `_get_rota()` tenta MCR.MarkovDecisor primeiro
- `docs/PLANO_MCRZIFICACAO.md`: Criado com plano completo de MCR'zificacao
- `sandbox/test_mcr_integracao.py`: Teste de integracao criado

### Licoes Aprendidas

> **O FiltroMCR por Jaccard de bytes funciona como metrica universal.** Substitui keyword scoring, cobertura de tipos, e similaridade de fingerprint. Um unico Jaccard entre pergunta e resposta avalia relevância, qualidade e similaridade.
>
> **MCR.py ja existia e ja estava correto.** A autoavaliacao por Jaccard, FiltroMCR, MarkovDecisor e AutoLoop ja estavam implementados. So faltava conectar ao kg.buscar() passando o parametro `pergunta=`.
>
> **MCR'zificar e conectar, nao reescrever.** O kg.buscar() nao precisou ser reescrito — so ganhou um parametro opcional `pergunta=` que ativa o re-ranqueio MCR. Compatibilidade total mantida.
>
> **14 prototipos validaram o conceito.** 3760+ linhas de prototipos provaram que MarkovUniversal funciona em QUALQUER nivel (byte, palavra, token, intencao, acao). O MCR.py final tem ~420 linhas.
