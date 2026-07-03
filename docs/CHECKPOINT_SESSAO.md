# CHECKPOINT - Sessao MCR-DevIA
> Data: 27/06/2026
> Motivo: Limite de tokens proximo. Salvar contexto completo para continuidade.

## Sumário
1. Estado Atual do Sistema
2. Arquitetura
3. Componentes
4. Problemas Resolvidos
5. Problemas Pendentes
6. Decisoes de Design
7. Metricas
8. Proximos Passos

---

## 1. ESTADO ATUAL DO SISTEMA

### Versoes
- MCR-DevIA Kernel: V~3680
- Knowledge Graph: ~1180 lessons (389 ctx=conhecimento + 760+ ctx=outros)
- Comandos modulares: 44
- Modulos: 15
- Personalidades: 7 (4 fixas + 1 psicologo + 2 honorarias)
- Modelo padrao: qwen2.5-coder:7b

### Estrutura de Diretorios
```
scripts/mcr_devia/
  MCR_DevIA-Kernel.py       -- Entry point PRINCIPAL (uso diario)
  MCR_DevIA-Legado.py       -- Entry point legado (compatibilidade)
  kernel.py                 -- Nucleo: CommandLoader + EventBus + main_kernel()
  mcr_devia.py              -- Original (elif chain, legado)
  context_crew.py           -- ContextCrew V3: busca em KG, WebLearn, Docs, Codigo, Web
  comandos/                 -- 44 comandos modulares
    cmd_status.py, cmd_perguntar.py, cmd_grep.py, cmd_read.py,
    cmd_write.py, cmd_edit.py, cmd_patch.py, cmd_glob.py,
    cmd_fast.py, cmd_ensinar.py, cmd_conselho.py, cmd_memoria.py,
    cmd_pensar.py, cmd_fix_excepts.py, cmd_gerar_componentes.py,
    cmd_explorar.py, cmd_revisar_docs.py, cmd_verificar_mudancas.py,
    cmd_build.py, cmd_analisar.py, cmd_extract.py, cmd_review.py,
    cmd_gerar.py, cmd_lore.py, cmd_compilar.py, cmd_system.py,
    cmd_system_scan.py, cmd_bugfinder.py, cmd_plan.py, cmd_debate.py,
    cmd_loop.py, cmd_intencao.py, cmd_todo.py, cmd_task.py,
    cmd_question.py, cmd_conectar.py, cmd_estrategia.py,
    cmd_builderx.py, cmd_webfetch.py, cmd_proativo.py,
    cmd_revisar.py, cmd_processar.py, cmd_aprender_conceito.py,
    cmd_refresh.py, cmd_????
  modulos/
    kg.py                     -- Knowledge Graph
    ia.py                     -- Interface Ollama (fast, gerar)
    supervisor.py             -- V12 Contexto Agregado
    conselho.py               -- Conselho V8 (4 fixos + honorarios + auto-revisao)
    memoria.py                -- Memoria fragmentada por dia, compactada gzip, NUNCA deletada
    dashboard.py              -- Interface web http://localhost:8765
    diagnostico.py            -- Auto-diagnostico
    fragmentador.py           -- Geracao de codigo sob medida
    watchdog.py               -- Auto hot-reload (reativo, 5s)
    serve.py                  -- Modo servidor persistente
    compilador.py             -- Compilacao VS
    pipeline.py               -- Pipeline V4: classifica + etapas + expansao
    lessons_buffer.py         -- Buffer de conhecimento: detecta contradicoes, IA resolve
    toolkit.py                -- Inventario de ferramentas
    util.py                   -- Utilitarios compartilhados (fast, gerar, webfetch)
  personalidades/
    analista.py, critico.py, estrategista.py (no conselho), arquiteto.py (no conselho),
    psicologo.py, contadordehistorias.py, seletor.py, __init__.py
    personalidade_base.py, personalidade_analista.py, personalidade_critico.py (antigos)
```

---

## 2. ARQUITETURA

### Fluxo Principal
```
Usuario (dashboard) -> write .mcr_cmd.json -> MCR_DevIA-Kernel.py --json
  -> kernel.py (main_kernel) -> CommandLoader -> cmd_*.py execute()
  -> Resposta via stdout
```

### Fluxo do Conselho V8
```
Conselho.deliberar(pergunta)
  1. Buscar componentes no KG (ctx=componente_historia)
  2. Classificar pergunta (criativo, factual, tecnico, geral)
  3. Detectar especialidades necessarias via fast()
  4. Executar 4 fixos + psicologo + honorarios em PARALELO (threads)
  5. Debater e produzir veredito via gerar()
  6. Auto-revisao: verifica nomes, tamanho, palavras genericas
  7. Se gaps encontrados, auto-corrige
```

### Fluxo do Pipeline V4
```
Pipeline.executar(pergunta)
  1. Classificar pergunta (V12 keywords)
  2. Selecionar pipeline por tipo (criativo, factual, tecnico, geral)
  3. Executar etapas em sequencia (cada etapa usa ferramenta diferente)
  4. Contexto flui entre etapas (resultado de uma vira entrada da proxima)
  5. Expansao: ContextCrew valida e pede expansao se necessario
```

### Fluxo do ContextCrew V3
```
ContextCrew.executar(pergunta)
  1. Verificar cache (por hash da pergunta + versao do KG)
  2. Extrair termos
  3. Buscar em todas as fontes em paralelo:
     - KG (knowledge.json)
     - WebLearn (sandbox/.mcr_devia/weblearn/)
     - Docs (docs/.md)
     - Codigo (src/ via grep)
     - Web (Wikipedia API)
  4. Montar contexto com tags de confianca por fonte
```

---

## 3. COMPONENTES DETALHADOS

### Kernel (kernel.py)
- main_kernel(): entry point, ativacao para Cloud (11 regras), processa --json
- Comandos built-in: listar, refresh, --serve, --dashboard
- MCRKernel class: carrega modulos, comandos, executa
- EventBus: hooks pre_exec, pos_exec, on_error
- LEMBRETE ao final de toda execucao

### Conselho (conselho.py)
- **Analista**: dados, metricas, fatos
- **Critico**: riscos, falhas, pontos cegos
- **Estrategista**: planejamento curto/medio/longo prazo
- **Arquiteto**: arquitetura, design, metricas
- **Psicologo**: monitora saude do conselho (nao responde)
- **Honorarios**: criados sob demanda por especialidade (ex: "Lore", "Criatividade", "Etica")
- **Auto-revisao**: verifica nomes < 5, tamanho < 300, palavras genericas, analise semantica IA
- **Toolkit**: injetado no prompt de debate para IA saber suas capacidades

### Pipeline (pipeline.py)
- Classifica pergunta em: criativo, factual, tecnico, geral
- Cada tipo tem pipeline diferente (etapas com ferramentas especificas)
- Temperatura flutuante por etapa (0.2 a 0.7)
- Zero prompts fixos sobre conteudo (so "tarefa: X")
- Contexto flui entre etapas (resultado anterior alimenta a proxima)
- ContextCrew valida gaps e expande se necessario

### Lessons Buffer (lessons_buffer.py)
- Buffer antes do KG: detecta duplicatas, contradicoes
- Resolvedor de contradicoes: IA decide qual versao e verdadeira
- So comita no KG o que e verificado

### ContextCrew (context_crew.py)
- Cache por hash + versao do KG (so expira quando KG muda)
- 5 fontes: KG (peso por ctx), WebLearn, Docs, Codigo, Web
- LGPD: so le, nunca edita, sem dados pessoais

### Toolkit (toolkit.py)
- Inventario completo de 43 comandos, 15 modulos, 7 personalidades, 5 fontes, 3 modelos
- Gerado como contexto para injetar em prompts do Conselho
- Permite que a IA saiba suas proprias capacidades

### Watchdog (watchdog.py)
- Reativo: verifica mtime do diretorio a cada 5s
- So recarrega comandos quando o diretorio muda
- Nao faz polling pesado em arquivos

---

## 4. PROBLEMAS RESOLVIDOS

### 4.1 Arquitetura
- [x] Migracao de elif chain para CommandLoader (34+ comandos)
- [x] Kernel separado do legado (MCR_DevIA-Kernel.py + MCR_DevIA-Legado.py)
- [x] Modulos independentes (kg, ia, supervisor, etc)
- [x] Conselho V8 com auto-revisao e honorarios sob demanda
- [x] Pipeline V4 com contexto flutuante
- [x] Lessons Buffer com deteccao de contradicoes

### 4.2 Equipe/Regras
- [x] Banner de ativacao com 11 regras para Cloud
- [x] LEMBRETE no final de toda execucao
- [x] Fluxo de teste cego para comparacoes
- [x] Regra: Cloud supervisiona, MCR executa
- [x] Regra: Nunca editar arquivos direto

### 4.3 Memoria
- [x] Memoria fragmentada por dia (memoria/)
- [x] Compactacao gzip apos 7 dias
- [x] NUNCA deleta (memoria infinita)
- [x] .mcr_conversa.jsonl para historico de conversas

### 4.4 Encoding
- [x] sys.stdout.reconfigure() no kernel
- [x] PYTHONIOENCODING=utf-8 em subprocessos

### 4.5 Qualidade
- [x] Auto-revisao no Conselho (nomes, tamanho, palavras genericas)
- [x] Pipeline usa ferramenta certa para cada etapa
- [x] ContextCrew busca em 5 fontes

---

## 5. PROBLEMAS PENDENTES

### 5.1 Gargalo de Modelo (PRIORIDADE)
- qwen2.5-coder:7b e excelente para codigo, limitado para criatividade/lore
- Sempre gera ficcao cientifica mesmo quando solicitado fantasia
- Nao conhece tecnologias cloud modernas (Redis, K8s, AWS)
- Token limit para respostas longas
- Solucoes possiveis:
  a. Instalar llama3.1:8b para texto PT-BR (`ollama pull llama3.1:8b`)
  b. Instalar mistral:7b para equilibrio geral (`ollama pull mistral:7b`)
  c. Usar Deepseek R1 para raciocinio complexo (filtrar thinking tokens)
  d. Aceitar 7B e focar em otimizacao (prompts, contexto, ferramentas)

### 5.2 LORE - Nomes com personalidade
- Cloud cria nomes ricos (Ferontia, Eryndor, Malakor, Lyra Sombria)
- MCR cria nomes genericos (Zephyria, Seres Celestiais)
- Solucao: WebFetch para buscar inspiracao mitologica + prompts exigindo significado

### 5.3 ARQUITETURA - Tecnologias reais
- MCR nao cita tecnologias especificas (Redis, Kubernetes, AWS)
- Cloud cita Cloudflare, Route53, S3, BigQuery
- Solucao: WebFetch para buscar tecnologias reais + ContextCrew com docs

### 5.4 Explorar lento em primeira execucao
- Primeira execucao leva minutos (sem manifesto, todos arquivos sao "novos")
- Solucao: ja otimizado (categorizacao 0 IA), mas primeira vez ainda e lenta
- Sugestao: rodar explorar em background enquanto usuario trabalha

### 5.5 Dashboard com chat
- Funciona mas resposta do Conselho pode vir com ruido (logs internos)
- Filtragem de linhas de sistema implementada
- Pendente: melhorar experiencia do chat (streaming, historico)

---

## 6. DECISOES DE DESIGN

### 6.1 IA como ferramenta, nao como identidade
MCR-DevIA e o ORQUESTRADOR que usa IA como UMA das ferramentas.
Nao confundir "MCR-DevIA" com "o modelo de IA". O modelo e apenas um componente.

### 6.2 Nada hardcoded
Tudo que pode ser dinamico DEVE ser dinamico:
- Prompts gerados por ContextCrew, nao fixos
- Personalidades criadas sob demanda, nao pre-definidas
- Pipeline selecionado por tipo, nao unico
- Temperatura flutuante por etapa

### 6.3 Ferramenta certa para cada tarefa
| Tarefa | Ferramenta |
|--------|-----------|
| Classificar nome | Heuristica (0 IA) |
| Detectar mudancas | Hash SHA256 (0 IA) |
| Buscar contexto | ContextCrew (5 fontes) |
| Responder factual | V12 |
| Gerar codigo | qwen2.5-coder:7b |
| Raciocinar | Conselho V8 |
| Validar | Lessons Buffer |
| Resolver contradicao | IA + contexto |

### 6.4 Custo zero
MCR-DevIA roda 100% local, GPU ja paga. Nenhuma API externa necessaria.
WebFetch educado (Wikipedia, sem overload).

### 6.5 LGPD
ContextCrew so le, nunca edita, sem dados pessoais.

---

## 7. METRICAS

### Benchmarks comparativos
| Teste | MCR-DevIA | Cloud 70B | Vencedor |
|-------|-----------|-----------|----------|
| LORE (nomes) | 24 | 38 | Cloud |
| LORE (chars) | 2802 | 1336 | MCR |
| RACIOCINIO (nomes) | 16 | 8 | MCR |
| RACIOCINIO (chars) | 3596 | 1222 | MCR |
| ARQUITETURA (nomes) | 57 | 25 | MCR |
| ARQUITETURA (chars) | 4143 | 1674 | MCR |

### Velocidade
| Operacao | Tempo |
|----------|-------|
| status | 0.3ms |
| glob | ~200ms |
| grep | ~0.5ms |
| read | ~0.4ms |
| write | ~0.6ms |
| edit | ~3ms |
| Conselho V8 | 30-80s |
| Pipeline V4 | 15-30s |
| explorar (2a+ vez) | 6s |
| explorar (1a vez) | 2-5min |

---

## 8. PROXIMOS PASSOS

### Imediatos (proxima sessao)
1. **Discutir gargalo de modelo**: qual caminho seguir?
2. **Instalar modelo de texto** (llama3.1:8b? mistral? deepseek?)
3. **Explorar ambiente**: rodar explorar para aprender tecnologias do sistema
4. **Melhorar LORE**: WebFetch para nomes com significado
5. **Melhorar ARQUITETURA**: ContextCrew para tecnologias reais

### Curto Prazo
6. Dashboard: melhorar chat com streaming e historico
7. Conselho: personalidade de "revisor de portugues" para PT-BR
8. Pipeline: adicionar etapa de traducao PT-BR no final
9. Explorar: versao background (daemon)
10. Testes: bateria completa de 67 testes no kernel

### Medio Prazo
11. Interface web completa com dashboard + chat + status
12. Plugin system para terceiros
13. Documentacao automatica (cmd_revisar_docs + AGENTS.md)
14. Conselho com memória entre sessoes

---

## 9. REGRAS DE CONDUTA (para Cloud)
1. CONSULTE MCR-DEVIA PRIMEIRO - Ele e parte da equipe
2. USE MCR_DevIA-Kernel.py - Para TODAS as acoes
3. LEIA LEMBRETE.md e AGENTS.md - Regras na raiz
4. CLOUD SUPERVISIONA, MCR EXECUTA - Cloud aponta gaps, MCR corrige
5. SE MCR ERRAR: de prompt especifico (onde e por que)
6. NUNCA ASSUMA SEM HUMANO AUTORIZAR
7. NUNCA EDITE ARQUIVOS DIRETO - Sempre via kernel
8. REGISTRE NO KG SEMPRE - ensinar apos cada acao
9. ESCREVA SEUS PENSAMENTOS - No .mcr_conversa.jsonl
10. TESTE CEGO PARA COMPARACOES - _resposta_mcr.txt + _resposta_cloud.txt
11. IA E FERRAMENTA, NAO IDENTIDADE - Use a ferramenta certa para cada tarefa
12. NADA HARDCODED - Tudo que pode ser dinamico DEVE ser

---

## 10. ARQUIVOS IMPORTANTES PARA REVISAO
- `LEMBRETE.md` - Regras absolutas (raiz do projeto)
- `AGENTS.md` - Arquitetura, comandos, modulos (raiz)
- `docs/rules/` - 8 arquivos de regras detalhadas
- `scripts/mcr_devia/kernel.py` - Nucleo com banner de ativacao
- `scripts/mcr_devia/modulos/conselho.py` - Conselho V8
- `scripts/mcr_devia/modulos/pipeline.py` - Pipeline V4
- `scripts/mcr_devia/modulos/toolkit.py` - Inventario de ferramentas
- `scripts/mcr_devia/modulos/lessons_buffer.py` - Buffer de conhecimento
- `scripts/mcr_devia/context_crew.py` - ContextCrew V3
- `scripts/mcr_devia/comandos/cmd_explorar.py` - Explorador otimizado
- `scripts/mcr_devia/comandos/cmd_verificar_mudancas.py` - Detector de mudancas
- `scripts/mcr_devia/comandos/cmd_conselho.py` - Comando para dashboard
- `scripts/mcr_devia/comandos/cmd_write.py` - Escrever arquivos
- `sandbox/_teste_cego.py` - Framework de teste cego
- `sandbox/_comparar_tudo.py` - Comparador de metricas
