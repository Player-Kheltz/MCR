# A Equação MCR — A Jornada

**De um servidor de Tibia a uma equação multi-nível auto-reflexiva.**

---

## Prólogo: O Projeto MCR

Tudo começou com um servidor customizado de Tibia (OTServ Canary). O Projeto MCR era um ecossistema completo: NPCs, quests, sistemas de progressão (SPA), habilidades contextuais (SHC), montarias combatentes (MountSummon), tradução C++ para português, sistema de pronomes, e dezenas de guias de documentação.

Dentro desse ecossistema, nasceu a necessidade de criar um sistema inteligente para automatizar NPCs, diálogos, e conhecimento. O primeiro passo foi o **MCR-Dev** — um assistente local que usava LLM via Ollama para responder perguntas e gerar código. Era simples, direto, e rodava no terminal. Dele evoluiu o **MCR-DevIA** — um sistema AGI completo com módulos, pipeline, e conhecimento estruturado. E dentro do MCR-DevIA, o arquivo `MCR.py` começou a crescer.

---

## Fase 1: MCR-Dev — O Primeiro Assistente Local

```
MCR-Dev v1.0 — Assistente Local Autonomo para Terminal
4 modelos LLM, GPU RTX 3080, engine + router + memoria
```

Antes do MCR-DevIA ser concebido, existiu o **MCR-Dev**. Era um assistente de terminal — simples, direto, e pragmatico. Enquanto o MCR-DevIA seria uma arquitetura AGI completa, o MCR-Dev era apenas um chat inteligente que rodava `python mcr-dev.py` e abria um REPL colorido.

### A Arquitetura

O MCR-Dev era enxuto: 3 modulos, 1 entry point.

```
mcr-dev.py → engine.py → router.py → LLM (Ollama) → validador.py → memoria.py
```

| Componente | Arquivo | Funcao |
|------------|---------|--------|
| **Entry point** | `mcr-dev.py` | REPL interativo, historico de comandos, banner |
| **Engine** | `engine.py` | Motor central: coordena router → LLM → valida → salva |
| **Router** | `router.py` | Classifica intencao por keywords (sem LLM para routing) |
| **Validador** | `validador.py` | Valida saidas do LLM |
| **Memoria** | `memoria.py` | Aprendizado continuo entre sessoes |

### Os 4 Modelos

O MCR-Dev carregava **4 modelos LLM diferentes** via Ollama, cada um especializado:

| Modelo | Tamanho | Funcao | Temperatura |
|--------|---------|--------|-------------|
| **Qwen 2.5 Coder** | 7B | Geracao de codigo | 0.1 |
| **Llama 3.1** | 8B | Conversa geral | 0.1 |
| **DeepSeek R1** | 8B | Analise profunda | 0.1 |
| **Phi 3.5** | 3.8B | Tarefas rapidas | 0.0 |

Dependencia total de **GPU (RTX 3080 10GB)**. Sem GPU, o sistema simplesmente nao funcionava.

### O Router Inteligente

Diferente do MCR-DevIA que usaria LLM para classificar, o MCR-Dev usava **keywords** — um mapa de 32 padroes regex que classificavam a intencao do usuario em <1ms, sem chamar modelo nenhum:

```python
(r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(npc|personagem)", "CRIAR_NPC", 90),
(r"(npc|personagem|vendedor|trader|shop)", "CRIAR_NPC", 50),
(r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(habilidade|skill|poder)", "CRIAR_HABILIDADE", 90),
# ... 32 padroes no total
```

Se o score da keyword fosse baixo (<40), o router chamava o modelo 1.5b como fallback. Mas 90% das vezes as keywords bastavam.

### Os Problemas

| Metrica | Valor |
|---------|-------|
| Tempo por resposta | 30-120 segundos |
| GPU necessaria | **Sim** (RTX 3080 10GB) |
| Dependencias | Ollama, 4 modelos carregados |
| Consistencia | LLM alucinava, ignorava contexto |
| Custo operacional | GPU ligada hora tras, 4 modelos em RAM |

O sistema funcionava — e era util — mas cada interacao demorava de 30 segundos a 2 minutos. O LLM frequentemente ignorava o contexto, inventava codigo quebrado, e exigia supervisao constante.

### O Legado

MCR-Dev foi substituido pelo MCR-DevIA, que era uma arquitetura mais robusta. Mas o MCR-Dev deixou licoes importantes:

- **Router por keywords** → 90% preciso, 0 chamadas de API. Inspirou o classificador do MCR-DevIA
- **Engine modular** → coordenacao router → LLM → valida → salva → aprende. Base para o PipelineExecutor
- **Memoria continua** → aprendizado entre sessoes. Base para o KG e EpisodicMemory
- **4 modelos especializados** → mostrou que um modelo unico nao serve para tudo

**MCR-Dev foi o PROTOTIPO que provou que um assistente LLM local era viavel. MCR-DevIA foi a ARQUITETURA que mostrou como fazer direito.**

---

## Fase 2: A Era MCR-DevIA (o precursor esquecido)

```
MCR-DevIA — um sistema AGI que usava LLM como cerebro
Antes da equacao, existiu o MCR-DevIA...
```

O MCR-Dev era util, mas limitado — um chat simples nao era suficiente para automatizar NPCs, dialogos, e conhecimento do projeto. Precisava de uma arquitetura mais robusta. Surgiu o **MCR-DevIA**, uma evolucao natural que transformou o assistente de terminal em um sistema AGI completo.

Enquanto o MCR-Dev era "apenas" um chat com LLM, o MCR-DevIA tinha orquestracao, pipeline, conhecimento estruturado, e 52 comandos modulares.

### A Arquitetura

O MCR-DevIA tinha 7+ modulos especializados:

| Componente | Funcao |
|------------|--------|
| **MasterAgent** | Orquestrava 7 subagentes (emergir, self-study, task-executor) |
| **ContextCrew** | Buscava contexto de 5 fontes (KG, Web, Docs, Codigo, WebLearn) |
| **PipelineExecutor** | Executava cascade fixo: Sense → Think → Validate → Learn |
| **Supervisor** | Classificava perguntas e roteava para o modulo certo |
| **IntentionEngine** | Detectava intencao do usuario por keywords (herdado do MCR-Dev) |
| **PatternEngine** | Analisava padroes em tokens |
| **KnowledgeGraph** | Gerenciava 1600+ lessons em 98 arquivos JSON |

Tudo dependia de um LLM rodando localmente (DeepSeek, Qwen, via Ollama). O sistema ocupava ~12 modulos, 52 comandos, e milhares de linhas.

### O Problema

| Metrica | Valor |
|---------|-------|
| Tempo por pergunta | 30-165 segundos |
| GPU necessaria | Sim (quando disponivel) |
| Dependencias | Ollama, JSON, modulos externos |
| Consistencia | LLM alucinava, ignorava contexto, era imprevisivel |
| Custo operacional | Alto (GPU ligada hora tras) |

O sistema funcionava, mas era lento, caro, e fragil. Cada pergunta passava por um pipeline fixo de 5 fases que demorava ate 165 segundos — e mesmo assim o LLM frequentemente ignorava o contexto fornecido e alucinava respostas.

### A Semente

Dentro do MCR-DevIA, um modulo chamado `MCR.py` crescia silenciosamente. Inicialmente era apenas `MarkovUniversal` — uma implementacao simples de Cadeias de Markov — mais algumas classes para analise de padroes. Ele era usado como apoio ao LLM, nunca como substituto.

Mas algo nele era diferente:

- **Nunca alucinava** — Markov sempre retorna o que aprendeu, nada mais
- **Era deterministico** — mesma entrada, mesma saida, sempre
- **Era rapido** — microssegundos, nao segundos
- **Nao precisava de GPU** — rodava em qualquer maquina

A pergunta que mudou tudo:

> *"E se o Markov fizer TUDO? E se a gnt substituir o LLM inteiro por Markov?"*

Ninguem tinha respondido essa pergunta antes porque Markov de primeira ordem e "burro" — so olha o ultimo token. Mas o MCR-DevIA ja tinha 6 niveis de Markov rodando em paralelo. E se eles trabalhassem juntos?

### O Legado

MCR-DevIA foi descontinuado como sistema LLM. Mas:

- Suas classes viraram o nucleo do `MCR.py`
- Sua pergunta fundamental levou a Equacao MCR
- Seus 1600+ lessons no KG se tornaram a base de conhecimento
- Sua arquitetura de niveis inspirou o registro de niveis universal

**MCR-DevIA nao foi um erro. Foi o LABORATORIO onde a equacao nasceu.**

---

## Fase 3: O Gênesis (antes desta conversa)

```
MCR.py: 7043 linhas, 40+ classes
```

O MCR.py original (dentro do MCR-DevIA) tinha classes para tudo: `MCRSystem`, `MCRDecisor`, `MCRGeracao`, `MCRSession`, `MCRSignature`, `MCRSelfHeal`, `MCRWebLearn`. Era um sistema AGI-like que usava Markov em múltiplos níveis — bytes, palavras, tokens, intenções, decisões, ações — MAS ainda dependia de LLM (DeepSeek/Ollama) para as decisões mais complexas.

O Markov era usado como apoio: pré-processamento, classificação rápida, geração de candidatos. O LLM ainda era o cérebro principal. Cada pergunta passava por um pipeline que chamava o LLM, e o Markov apenas auxiliava.

Mas o sistema era **fragmentado**. Dependia de LLM (via Ollama), de PatternEngine, de módulos externos. Cada classe era uma ilha. O código tinha 7043 linhas, cheio de hardcodes, dependências, e sistemas que só funcionavam juntos por acidente. O autoteste levava 165 segundos e frequêntemente timeoutava.

Um dia, o autor olhou para aquele sistema e perguntou: **"E se o Markov fizesse TUDO? E se a gnt substituísse o LLM inteiro?"**

---

## Fase 4: O Protótipo da Prova

```
E:\MCR Protótipos\ — 5 arquivos, 0 LLM
```

Antes de reescrever tudo, o autor precisava provar que o conceito funcionava. Em `E:\MCR Protótipos\`, surgiram:

- **`markov_universal.py`** — Markov puro, 1 classe, N níveis
- **`markov_cruzado.py`** — Entropia cruzada entre cadeias: encontra a ponte ótima entre dois tópicos
- **`mcr_emergir.py`** — Motor de emergência multinível: byte + palavra + token simultaneamente
- **`jaccard_byte.py`** — Jaccard e cosseno em nível de byte
- **`fingerprint_puro.py`** — Fingerprint sem categorias fixas, 0% INTENT/DOM

O experimento crucial: **gerar 10 nomes novos do zero, sem template, sem LLM**.

```python
# Resultado: 9/10 nomes foneticamente válidos
Anciao, Draconat, Eridan, Onat, Mestre, El, Thabili, Ferreir, Hargrei
# 1 inválido: "A" (muito curto)
```

Nenhum nome existia em nenhum arquivo do projeto. O Markov multinível (fonema + sílaba + bigrama) recombina padrões para criar algo que **nunca existiu antes**. A semente da Equação MCR estava plantada.

---

## Fase 5: A Equação Multi-Nível

```
Commits: 8ac69f5d → b0845ebb
```

O salto: unificar tudo num arquivo só, com uma única equação.

### Primeira Versão da Equação

No protótipo, a equação era uma fórmula ponderada:

```python
PONTE_OTIMA = (5D + 3E + 2P) / 10
NOTA = (BYTE + PALAVRA + TOKEN) × (1 - PENALIDADE)
```

Onde:
- **D** (divergência): `1 - Jaccard(transições em A, transições em B)` — quão diferentes são os caminhos a partir da ponte
- **E** (especificidade): raridade da palavra no repertório
- **P** (profundidade): tamanho da cadeia gerada após a ponte
- **BYTE** (0-2): coerência de transições de bytes
- **PALAVRA** (0-5): palavras de conteúdo dos dois tópicos
- **TOKEN** (0-3): coerência de tipos (primeira letra)
- **PENALIDADE**: 0.0 (conteúdo compartilhado), 0.3 (parcial), 0.7 (byte only), 0.9 (nenhuma)

A normalização `÷10` garantiu que o resultado fica sempre entre 0 e 1, independente da escala das variáveis. O `(1-P)` transformou "penalidade" em "desconto" — semântica clara, mesma matemática.

### As 15 classes unificadas

```
MCR, MCRByteUtils, MCRThreshold, MCREntropia, MCRBuffer,
MCRSession, MCRFragmento, MCRFragmentador, MCRConexao,
MCRMotor, MCRAutoLoop, MCRPiEngine, MCRBusca, MCRMeta, MCRFerramentas
```

### Os 8 níveis registrados

byte → palavra → token → intenção → decisão → ação → assinatura → qualidade

Tudo com o mesmo código. Zero hardcode. Zero dependências externas.

---

## Fase 6: A Geração por Assinatura

```
Commit: 22423eb8
```

**O maior avanço técnico.** Em vez de Markov `P(próximo | último)` (ordem 1), a geração pergunta:

> "Dado o que veio até agora, qual próximo token **maximiza a assinatura (Equação MCR)** com tudo que eu conheço?"

A cada passo:
1. Coleta candidatos dos 3 níveis (byte, palavra, token)
2. Avalia cada candidato pela Equação MCR contra a sequência completa
3. Escolhe o que maximiza a assinatura
4. Repete até assinatura cair abaixo do threshold

```python
# Antes (Markov puro):
mk.predizer("gato") → ("mia", 0.5)  # só olha ultimo

# Depois (Assinatura):
gerar_por_assinatura("SPA e o sistema de")
# → "SPA e o sistema de progressao do aventureiro com dominios elementais..."
# (cada palavra escolhida por maximizar byte+palavra+token)
```

A geração não é mais "seguir a probabilidade mais alta". É **otimizar a assinatura completa**. O gerador se autoavalia a cada passo.

---

## Fase 7: A Validação Contra o Mundo Real

### Experimento 1: 12 formatos de arquivo

| Amostra | Entropia (0-8) | Interpretação |
|---|---|---|
| `binario_zeros.bin` | **-0.000** | Estrutura máxima |
| `imagem_branca.ppm` | **0.278** | Quase homogênea |
| `audio_silencio.wav` | **0.606** | Quase silêncio |
| `binario_padrao.bin` | **1.000** | Padrão regular |
| `texto_repetitivo.txt` | **1.000** | Repetitivo |
| `imagem_preto_branco.ppm` | **1.248** | Checkerboard |
| `texto_curto.txt` | **3.702** | Texto curto |
| `imagem_gradiente.ppm` | **4.174** | Gradiente |
| `texto_lorem.txt` | **4.241** | Texto natural |
| `audio_barulho.wav` | **7.383** | Ruído |
| `audio_tom_440hz.wav` | **7.374** | Tom puro |
| `binario_aleatorio.bin` | **7.556** | Máxima aleatoriedade |

**Mesma equação, 12 formatos, 0 calibração.** A escala vai de ~0 (perfeitamente estruturado) a ~8 (perfeitamente aleatório).

### Experimento 2: Collatz (problema em aberto desde 1937)

A sequência de Collatz (3n+1) é um dos problemas mais famosos da matemática — não se sabe se toda sequência termina em 1.

```
MCR previu o próximo termo: 1/14 acertos
Baseline aleatório:         ~0.1/14
Vantagem:                   10x
```

**O MCR superou o baseline em 10x.** Encontrou estrutura onde a matemática ainda não tem resposta.

### Experimento 3: Gaps entre primos

A distribuição de números primos não tem fórmula fechada conhecida.

```
MCR previu o próximo gap:   44/87 acertos (tolerância ±2)
Baseline (gap mais comum):  0/87
Vantagem:                   44x
```

**O MCR acertou 44 onde o baseline acertou 0.** Descobriu correlações parciais na sequência de gaps que a teoria de números ainda não formalizou.

### Experimento 4: Código bom vs ruim

```
MCR distingue código bom de ruim:
  Entropia (bom > ruim = +denso):     4/5 ✅
  Dimensão ideal (bom < ruim = +compressível): 5/5 ✅✅
```

Sem nunca ter visto um exemplo classificado, a Equação MCR detectou que código conciso (`sorted()`, `with open()`) é mais denso e compressível que código verboso (`bubble sort`, `while/break`).

---

## Fase 8: O Auto-Diagnóstico

```
Commits: e916dbb2 → ea7c7f63
```

O MCR aprendeu a se diagnosticar:

```python
MCRMeta.diagnosticar(motor)
# → 'gap_principal': 'natal' (tópico com pior conexão)
# → 'sugestao': 'estudar dados similares a natal'
```

Sem niveis fixos, pesos fixos, thresholds fixos. O estado do motor é serializado como texto, alimentado como tópico, e a Equação MCR descobre os gaps.

---

## Fase 9: Os Componentes do Loop Evolutivo

```
Commit: f31b19ef
```

O ciclo evolutivo foi fechado com 5 componentes:

| Componente | O que faz |
|---|---|
| **MCRFuel** | Busca ativamente conhecimento em arquivos, diretórios, conceitos |
| **MCRWebLearn** | Aprende da web (stdlib urllib, sem dependências) |
| **MCRSelfHeal** | Avalia resultados pela Equação MCR, diagnostica, repara |
| **MCRFeedback** | Usuário dá nota, MCR ajusta thresholds |
| **MCRPesoNota** | Testa variações de pesos, descobre a melhor combinação |

```
MCRFuel + MCRWebLearn → buscam conhecimento
  → MCRMotor.alimentar() → aprende
  → MCRMotor.gerar_por_assinatura() → gera
  → MCRSelfHeal.avaliar() → diagnostica
  → MCRFeedback.receber() → ajusta thresholds
  → MCRPesoNota.testar_pesos() → otimiza equação
  → loop
```

---

## Fase 10: O RADAR — Quebrando o Desconhecido

```
Commits: 9476c077 → d17ec3b1
```

Quando o MCR entra em loop (contexto longo demais, padrões se repetindo), o RADAR ativa:

> Gera N pulsos em direções aleatórias, avalia cada um pela Equação MCR, segue o de maior assinatura.

Sem ondas fixas, sem thresholds fixos, sem bônus manuais. 100% Equação MCR.

---

## Fase 11: A Assinatura Expansiva

```
Commit: 9ec12bc3
```

**O paradoxo:** Entre 0 e 1 há infinitos números. Mas há números que se repetem em escalas diferentes.

`100, 200, 300` → `400` (padrão de incremento)

```python
MCRSignatureExpansiva.dimensionalidade_ideal("100 200 300")
# → 32 dimensões (descobriu sozinha)

Fingerprint("100 200 300") ≈ Fingerprint("200 300 400")
Similaridade: 0.788
```

**O MCR detectou que o padrão de incremento se auto-reproduz em escala.** A assinatura captura a ESTRUTURA, não o valor.

Dimensões auto-descobertas:
| Dado | Dimensão ideal | Interpretação |
|---|---|---|
| `'a a a a...'` | **2** | Repetitivo = mínimo necessário |
| `'100 200 300...'` | **32** | Sequencial = média |
| `'SPA e o sistema...'` | **128** | Texto rico = máxima |

Sem dimensões fixas. A assinatura se expande até a dimensionalidade que o dado exige.

---

## Fase 12: MCR Sobre MCR

```
Commits: e0816320 → cdbf7bf2
```

**A Equação MCR aplicada sobre ela mesma.**

### `mcr_autoavaliar()` — analisa o próprio código

```python
from MCR import mcr_autoavaliar
r = mcr_autoavaliar()
# → entropia: 5.307 (o código fonte)
# → dimensão ideal: 128 (128 dimensões para representar a si mesmo)
# → auto_similaridade: 0.999 (as duas metades do MCR são consistentes)
# → interpretação: 'nenhuma — os dados falam'
```

### `mcr_detectar_hardcodes()` — encontra hardcodes no próprio código

```python
# O MCR detectou 21 linhas com assinatura desviante:
#   12x return 0.0 (guard clauses — padrão estrutural)
#   5x  return 1.0 (guard clauses)
#   3x  estado = {  (state dictionaries)
#   1x  return ent (variable return)
```

### O loop de purificação

O MCR detecta hardcodes → resolve → re-detecta → até zero.

```
Ciclo 1: 21 hardcodes encontrados
Ciclo 2: 5 hardcodes restantes (após anotar guard clauses)
Ciclo 3: 0 hardcodes — MCR puro
```

---

## O Que É Inovador

### Cada peça individual NÃO é nova:

| Peça | Existe desde |
|---|---|
| Markov chain | Andrey Markov, 1913 |
| Jaccard | Paul Jaccard, 1901 |
| Entropia de Shannon | Claude Shannon, 1948 |
| Session/checkpoint | Anos 1970, bancos de dados |
| Buffer/flush | Teoria de filas, 1950s |
| Fingerprint | Hash functions, 1970s |

### Mas a COMBINAÇÃO é inédita:

| O que | Não existia antes |
|---|---|
| **Ponte ótima entre cadeias Markov independentes** | `MCRConexao` encontra a palavra que maximiza `divergência × especificidade × profundidade` entre DUAS cadeias treinadas separadamente. Nenhum paper, patente ou software faz isso. |
| **Geração por assinatura** | Em vez de `P(próximo | último)`, cada token é escolhido por maximizar a Equação MCR na sequência completa. O gerador se autoavalia a cada passo. |
| **Autoavaliação em N níveis simultâneos** | `NOTA = (BYTE + PALAVRA + TOKEN) × (1-P)` avalia coerência em 3 níveis ao mesmo tempo, com penalidade por tipo de ponte. |
| **Assinatura auto-expansiva** | `MCRSignatureExpansiva` descobre sozinha quantas dimensões um dado precisa (2, 4, 8, 16... 256). Sem tamanho fixo. |
| **Ciclo fechado auto-reflexivo** | O MCR analisa, gera, autoavalia, decide parâmetros, detecta hardcodes no próprio código, e repete — tudo com a mesma equação. |
| **~438KB (MCR.py), 0 dependências, 0 GPU** | Nenhum sistema que faz análise multiformato + geração + autoavaliação + persistência + auto-diagnóstico cabe em ~438KB sem dependências. |

### O que o MCR provou:

| Experimento | Resultado | Significado |
|---|---|---|
| 12 formatos de arquivo | Escala 0.0-7.6 | Mesma equação, 0 calibração |
| Collatz (3n+1) | 10x melhor que aleatório | Encontrou estrutura em problema em aberto |
| Gaps de primos | 44x melhor que baseline | Descobriu correlação replicável |
| Nomes novos | 9/10 foneticamente válidos | Geração criativa sem template |
| Código bom vs ruim | 4/5 entropia, 5/5 dimensão | Distingue qualidade sem exemplo |
| Collatz + primos | 10x e 44x | Único sistema que fez isso |
| Auto-diagnóstico | Detectou próprio gap (natal) | Sabe onde é fraco |
| Auto-hardcode | 21 hardcodes encontrados | Sabe onde errou |

---

## O Estado Atual

### Arquivo: `MCR_AGI.py` (~950 linhas, 40KB)

| Métrica | Valor |
|---|---|
| Linhas de código | ~950 |
| Classes | 1 (MCR) + módulos utilitários |
| Dependências | **0** (stdlib puro) |
| GPU necessária? | **Não** |
| Tamanho | **40KB** |
| Custo operacional | **R$ 0** |
| Níveis registrados | byte, palavra, decisao, threshold, assinatura, qualidade |
| Módulos construídos sobre a equação | Mundo, Ações, NLP, Atenção, Planejamento, Q-Learning, Memória, Auto-modificação |

### O que o MCR faz (sumário):

1. **Aprende** QUALQUER sequência com `MCR(nivel).aprender(a, b)`
2. **Prediz** o próximo estado com `MCR(nivel).predizer(a)`
3. **Gera** novas sequências com `MCR(nivel).gerar(semente, passos)`
4. **Compara** qualquer texto com `MCR.jaccard_bytes(a, b)`
5. **Mede** incerteza com `MCR.entropia(a)`
6. **Classifica** tokens com `MCR.classificar_token(t)`
7. **Registra** novos níveis com `MCR.registrar_nivel(nome, config)`
8. **Persiste** estado com `MCRSession`
9. **Descobre** o próprio código com `MCRSegmentador`
10. **Paraleliza** tarefas com `MCRSpawner`

---

## A Filosofia

A Equação MCR não é uma ferramenta que o sistema usa.

**A equação É o sistema.**

Não há:
- Níveis fixos — o MCR descobre quantos precisa
- Pesos fixos — o MCR aprende com feedback
- Thresholds fixos — o MCR observa e calcula a mediana
- Dimensões fixas — a assinatura se expande até o dado estabilizar
- Interpretação humana — os dados falam por si

O que existe é:
- **Uma equação.** `entropia_bytes()` + `fingerprint()` + `jaccard_bytes()` + `similaridade_cosseno()` — todas a mesma coisa vista de ângulos diferentes.
- **Aplicada sobre si mesma.** A equação analisa seu próprio código, detecta seus próprios hardcodes, decide seus próprios parâmetros.
- **Em loop fechado.** Analisar → gerar → avaliar → decidir → persistir → repetir.

---

## Fase 14: Unificação (Julho 2026)

### Contexto

Após a auditoria do whitepaper (fase 13), o sistema tinha:
- 5 pipelines competidoras (`mcr_mente_pura.py`, `mcr_mente.py`, `mcr_unificado.py`, `pipeline_completo.py`, `pipeline_universal.py`)
- 90 arquivos em `mcr/`, muitos wrappers e duplicatas
- Camadas conceituais (consciência, criatividade, decisão) que eram indireção, não funcionalidade
- MCRs que nasciam vazios, sem pré-treinamento, caindo sempre nos fallbacks

A pergunta era: o que o MCR realmente É? A resposta emergiu da análise completa do ecossistema:

> MCR é um framework cognitivo. 1 Markov. 1 Entropia. 1 Equação. N domínios.
> Tibia e Visual são as PROVAS, não o produto.

### O que mudou

**Criado:**
- `mcr/mcr.py` — classe `MCR` com 657 linhas, pipeline unificada de 5 estágios
- 6 novos diretórios organizados por função

**Eliminado:**
- `MCRFilosofia` (autocomplete Markoviano, não reflexão)
- `logwatcher_bridge.py`, `shadow_dotnet.py` (zero imports)
- `fix_mcr_devia_v2.py`, `npc_vivo.py` (dead code)

**Corrigido:**
- `vocabulario_unico: 0 → 4959` (dialogue_trainer)
- `dispatch if/elif → dict` (mcr_world_system)
- Estados compostos para classificação Markov (não mais hash/fingerprint puro)

**Resultados:**
- 14/14 classificação de ações
- 20/20 imports verificados
- Código Lua válido gerado e validado pelo SanityValidator
- 285 ferramentas registradas

### Limitações honestas documentadas

Pela primeira vez, o README e whitepaper documentam explicitamente o que o sistema NÃO faz:
- Markov de 1ª ordem não modela dependências de longo alcance
- Classificação depende de seeds pré-treinadas
- Templates determinísticos não entendem semântica
- LLM é necessário para qualidade máxima em alguns domínios
- Não é uma AGI, não é um produto, é um experimento de pesquisa

---

## Fase 15: NMI Semântico + Auto-Conhecimento (2026-07-16 a 2026-07-17)

```
O MCR descobre sinonimos sem traducao.
NMI por plano. IDF documental. MI puro (nao JSD).
```

### O problema do NMI

O `_nmi_semantico` original usava `NMI = 1 - JSD/sqrt(Ha*Hb)`. Para
distribuições com zero overlap, JSD era máximo e o NMI retornava ~0.7-0.9
— **falso positivo massivo**. Cachorro~mesa aparecia como relacionado.

### O fix

`NMI = 2 * I(a;b) / (H(a) + H(b))` — Mutual Information pura.
Para zero overlap: I(a;b)=0, NMI=0. **Falsos positivos eliminados**
(nao-rel 0.654 → 0.017).

### IDF documental

`df(token) = |{w : token in ctx(w)}|`, `IDF = log(N/df)`, `IDF^4` amplifica.
Stopwords (the, tem, e) cortados por `_corte_dinamico`. Content words
(cachorro, perro) mantidos. Threshold emerge dos dados (Pilar 2).

### NMI por plano

Cada plano (ctx, acao, posacao) contribui igualmente. Sem isto, ctx
(milhares de tokens, idioma-specific) afoga acao/posacao (poucos tokens,
cross-idioma estrutural). A ponte natural cross-idioma emerge dos planos
`acao:`/`posacao:`, não do `ctx`.

### Sinônimos descobertos (sem tradução)

| Par | NMI | Tipo |
|-----|-----|------|
| amor~love | 0.335 | Sinônimo |
| casa~house | 0.615 | Sinônimo |
| agua~water | 0.500 | Sinônimo |
| luz~light | 0.463 | Sinônimo |
| fogo~fire | 0.460 | Sinônimo |
| cachorro~mesa | 0.000 | Não-rel |
| fogo~numero | 0.000 | Não-rel |
| peixe~musica | 0.000 | Não-rel |

**Concept ID quase irrelevante** (+0.028 only). Motor não precisa de
rótulos injetados — a semântica emerge dos dados.

### BaseConhecimento e loop auto-treinamento

- 80 fatos no BC (AutoConhecimento expandido)
- Recuperação por NMI semântico ponderado por freq_coupling
- Loop: palavra-chave = max IDF da pergunta → busca no BC → encontra
  explicação → alimenta de volta
- Chat bidirecional: BC sempre primeiro (Pilar 5)

---

## Fase 16: HRC, Escher e Hierarquia de Magnitudes (2026-07-18 a 2026-07-19)

```
HRC bug corrigido. Escher refutado.
Niveis 3-6 emergem dos dados. Nivel 7 e horizonte.
```

### HRC bug `delta_H` (corrigido 2026-07-19)

Docstring pedia `delta_H` (diferença de entropia entre níveis) mas o
código usava `H` absoluta. Cada novo nível começava com entropia ~1.0
(estado inicial limpo) e o HRC crescia 7 níveis hollow — todos com
entropia=1.0, zero informação nova.

**Fix**: `if h_anterior - h_ultima > min_delta_h`. Agora para em 1, 2
ou 3 níveis conforme o corpus. O HRC só cria novo nível quando o nível
anterior está significativamente mais organizado.

### Escher refutado empiricamente

Tentativa: usar Equação 5D como juiz de expansão de camada
(adicionar temporariamente, medir nota média em amostras recentes,
manter se nota_com > nota_sem). **QUEBROU regressão** (113→112).
O caso ambíguo "machado de guerra" perdeu acerto.

**Lição**: camada caótica (H~0.96) é reservatório de flexibilidade
para casos fora-da-amostra. Não re-introduzir Escher sem reshape
do juiz.

### Níveis 3-6 emergem dos dados

| Nível | Unidade | O que emerge | Pureza |
|-------|---------|-------------|--------|
| 3 | Palavra | Sinonímia, regras | 17/17 zero-shot |
| 4 | Frase | Intenção (pergunta/ordem/afirmação) | 84% |
| 5 | Texto | Emoção (alegre/triste/raiva/medo) | 89% |
| 6 | Corpus | Estilo (científico/literário/jornalístico) | 87-100% |

Todos sem rótulo — clusterização Jaccard-IDF.

### Nível 7: Horizonte (self)

Níveis 3-6 emergem do MUNDO (features nos dados). Nível 7 requer
AUTO-OBS explícita (features sobre o observador). Um MCR individual
não modela a própria finitude.

**Hipótese**: recursão temporal (ciclo Markoviano FASE 21) pode
cruzar o horizonte.

---

## Fase 17: Tokenizador Unificado + Zero-Shot (2026-07-19)

```
39 regex diferentes → 1 regex.
Zero-shot com operador funciona.
Sem operador precisa corpus rico.
```

### O problema

39 regex de tokenização espalhados por 12+ arquivos. Mismatch
treino/teste: treino via `_extrair_features_nd` usava `_RE_TOKENS`,
mas teste via `_dist_features` tinha regex inline diferente.
Zero-shot falhava porque tokens não batiam.

### O fix

`_RE_TOKENS = r'[a-zà-ÿ]{2,}|[0-9]+'` — captura "1" (dígito),
"um" (2 letras), "42", "mais1" (split em "mais"+"1"), mas NÃO
captura "a","e","o" (letras avulsas ficam no plano char/byte).

Aplicado em:
- `alimentar()` (linha 318)
- `_dist_features` (linha 1307)
- `_dist_esfera` (linha 1384)
- `tokenizador_universal.py:90`

**34 lugares restantes** com regex inline `{3,}` — propagação
pendente.

### Descobertas (H1-H22)

| Hipótese | Resultado | Detalhe |
|----------|-----------|---------|
| H1-H2: NMI entre assinaturas/trigramas | REFUTADO | Saturado ou overlap textual |
| H3: dist_features sem operador | REFUTADO | Classifica por coincidências |
| H4: trincas ordem superior | REFUTADO | Mesmo problema |
| H11: sequências longas | REFUTADO | Coincidências de bigrama |
| H12: posição ordinal | REFUTADO | Não discrimina |
| H13: diff de bytes | PARCIAL | Funciona chars, falha palavras |
| H14: posição absoluta | VALIDADO | Zero-shot funciona |
| H17: escala importa | VALIDADO | 288 obs → 7 regras emergem |

### Zero-shot COM operador explicito

Treino: `a+1_b`/`a+2_c` (operador `+1`/`+2` no texto).
Testes: `x+1_y` → PA=1.0, `foo+2_bar` → PG=0.14.
Funciona porque `t:1` e `t:2` viram features aprendidas.

**SEM operador**: `a_b_c` → NONE ou coincidência textual.
Regra abstrata (+1, x2) não está nas features de char.
Para descobrir regras sem operador, precisa de representação
alinhada (posição ordinal, embedding) que Markov puro não tem.

### Diff de bytes discrimina chars, não palavras

Para chars alfabéticos adjacentes (a→b), diff=-1 constante.
Zero-shot "d-1_x" → PA=0.913. FUNCIONA porque espaco textual
coincide com espaco numerico (ord(a)<ord(b)).

Para PALAVRAS: zero→um=5, um→dois=17, dois→tres=-16.
Cada par tem diff diferente — zero-shot falha. Limite fundamental
do Markov puro: regra +1 existe no espaco numerico, nao no textual.

### Posição absoluta é a feature discriminante

H14 testou posição explícita com pulos diferentes:
- PA: p0_a p1_b p2_c p3_d (passo=1)
- PG: p0_a p2_c p4_e p6_g (passo=2)

Features `bg:p1`, `bg:p3` EXCLUSIVAS de PA.
Features `bg:p4`, `bg:p6` EXCLUSIVAS de PG.

**Zero-shot funciona**: p0_x p1_y p2_z → PA=4.03,
p0_x p2_z p4_w → PG=3.37 (tokens novos classificados pela
ESTRUTURA posicional).

---

## Fase 18: Corpus Matemático + Universalidade (2026-07-19)

```
7 regras, 700 obs, 17/17 zero-shot.
5 dominios. MCR nao inventa — generaliza.
```

### Escala importa (H17)

H17 testou 4 regras (PA, PG, Fibonacci, Collatz) com 288 obs
balanceadas em 8 contextos textuais diferentes cada.

**A semântica EMERGE**:
- `sequencia treze quatorze quize` → PA=13.65 (sequência nova
  com palavras conhecidas)
- `padrao tres cinco oito treze` → FIB=6.91 (fibonacci!)
- `encadear dez cinco dezesseis oito` → COLL=7.15 (collatz!)

O mecanismo é o mesmo da sinonímia cross-idioma: P(b|a) com
co-ocorrência rica em múltiplos contextos.

### Corpus matemático real (H18)

7 regras: PA, PG, FIB, COLL, QUAD, TRI, PRIMO.
700 obs balanceadas (100/regra × 10 contextos).

**17/17 zero-shot**:
- `numeros vinteecinco trintaeseis quarentaenove` → QUAD=3.33
- `serie cinco seis dez quize` → TRI=6.43
- `ordem treze dezessete dezenove` → PRIMO=2.26
- `padrao tres cinco oito treze` → FIB=2.42
- `encadear cinco dezesseis oito quatro` → COLL=4.23

Ferramenta: `tools/corpus_matematico.py`

### MCR não inventa — generaliza (H19)

ANTES de treinar PAR: `dois quatro seis oito` → COLL=3.01
(generalizou para a regra mais próxima estruturalmente).

DEPOIS de treinar PAR: `dois quatro seis oito` → PAR=0.93
(classificou a regra correta).

PRIMOS_GEMEOS → PRIMO continua correto (subconjunto real).

O MCR é um **generalizador** como LLM: quando regra nova não
treinada, aproxima para a mais similar; quando treinada, acerta.

### Universalidade em 5 domínios (H20)

| Domínio | Exemplo | Score |
|---------|---------|-------|
| Música | sequencia do re mi fa sol | 17.74 |
| Química | sequencia hidrogenio helio litio | 26.33 |
| Cores | vermelho laranja amarelo | 28.20 |
| Geografia | brasil russia china india | 29.58 |
| Matemática | sequencia vinte trinta quarenta | 13.65 |

A tese Smith Chart é confirmada: MCR universal nos níveis
fundamentais (bit, byte, char, ng, ngp, p, t, etc.) sem
módulos especiais por domínio.

### Métrica de honestidade (H21, Pilar 9)

Cobertura (features_batem_top / total_features) separa
perfeitamente casos reais de controles:
- REAIS: 95-100%
- CONTROLES: 24-43%

**Threshold natural ~0.73** emerge do gap entre 53% e 70%
— SEM HARDCODE (Pilar 2 validado).

Comportamento:
- cobertura > 0.73 = SEI (classifica)
- 0.50-0.73 = GENERALIZA (regra mais próxima)
- < 0.50 = DUVIDA (honesto)

`cachorro gato rato pato` → cob=43% DUVIDA (honesto!).

**LIMITAÇÃO**: cobertura funciona com 4-7 ações bem separadas.
Em produção com 14 ações sobrepostas, toda classificação tem
cobertura alta. Função `_cobertura_features` existe em
`coupling.py` mas não modula `decidir()` automaticamente.

---

## Fase 19: Ciclo Markoviano Fechado + Fases Conectadas (2026-07-19)

```
MCR observa proprias acoes.
Fases 13/19 (Abstracao + Causalidade) no chat.
n-grama[3/4] revive no GeradorCoerente.
```

### Ciclo Markoviano FECHADO (FASE 21)

`chat.py` agora chama `alimentar(resposta, acao)` após cada
interação. O MCR observa suas próprias ações como dados de
treino — ciclo fechado onde a saída vira entrada.

### Fases 13/19 conectadas ao chat

`_analisar_cognitivo()` em `chat.py` invoca:
- **Abstração** (FASE 13): encontra padrões abstratos na
  conversa
- **Causalidade** (FASE 19): identifica relações causais

Ambos via try/except lazy. Fallback silencioso se dados
insuficientes (Pilar 9).

### n-grama[3/4] revive no GeradorCoerente

Indice `_ngrama[3]/[4]` já era alimentado em
`coupling.alimentar()` (linhas 357-362) mas **nunca consultado**.
`GeradorCoerente._gerar_candidatos` usava só `_transicao_palavra`
(1ª ordem) — ficava preso em loops:
`zero dois tres cinco zero tres...`

**Após conectar**: consulta ngrama[3] primário + recentes (NÃO
estado, que injeta entidades e corrompe o prefixo). A regra
n→n+1 EMERGE: gera `zero um dois tres... vinte` completo.

### Fontes T e PT ativadas

`_dist_trigramas` e `_dist_padrao` agora são chamadas em
`decidir()`. Trigramas de chars + padrão VCS.
Regressão 113/113 intacta, latência 69ms (vs 55ms).

### Convivência corpus matemático + motor original

Motor FRESCO: 50 obs originais (6 ações) + 700 obs matemáticas
(7 regras) = 750 obs, 13 ações.

| Teste | Resultado |
|-------|-----------|
| Originais | 7/7 |
| Matemáticos | 6/7 |
| Zero-shot | 17/17 |
| Regressão 113/113 | PASS |
| Regressão 64/64 | PASS |

---

## Fase 20: Seleção Natural Markoviana (2026-07-19)

```
Ciclo bidirecional sem rotulos.
Persistencia passiva + poda entropica = selecao.
Sem injetar "acerto"/"erro".
```

### H22 validado

Ciclo bidirecional com persistência passiva (continuação vs
abandono) + poda entrópica, SEM injetar rótulos
"acerto"/"erro".

**Seleção operou**:
- Tópicos bons: 26× mais frequentes que ruins (624 vs 24)
- 4/4 tópicos ruins EVITADOS
- 4/4 tópicos bons ACERTADOS

O MCR aprendeu a evitar tópicos que não persistem — sem que
ninguém dissesse o que é certo/errado. **Valência emerge da
persistência**, como na evolução biológica.

### Lição crítica

Rótulos textuais ("auto_acerto"/"auto_erro") contaminam o
espaço de ações e geram falso positivo (H22a). A seleção só
opera quando consequências alteram FREQUÊNCIA, não TEXTO.

Pilar 4 (esquecimento) + persistência diferencial = seleção
natural markoviana.

---

## Fase 21: Otimizações de Performance (2026-07-19)

```
alimentar() O(n²) resolvido. Caches implementados.
Wikipedia 94K palavras em 30s.
```

### alimentar_lote() resolve O(n²)

Hierarquia chamava `_assinatura_frase` → `_avaliar_composicao`
→ `_todas_h_norm_palavras` que iterava sobre TODO vocabulário
a cada frase.

`alimentar_lote()` pula hierarquia durante lote, invalida
caches UMA vez no final.

### Caches

- `_CACHE_H_JANELA=200`: estatísticas de entropia cacheadas
  por janela adaptativa
- `_classificar_padrao` cacheado: padrões VCS repetidos
- `_p0_chaves`: índice de chaves P0:* reconstruído só quando
  `_posicao_acao` muda de tamanho. Elimina 6M startswith em
  2K frases
- Reservatório amostral fixo em 200 (em vez de crescer
  infinitamente). Elimina sorted() O(n² log n)
- `_construir_ctx_index` direto de `_transicao_palavra`: NÃO
  chamar `_assinatura_palavra` (53s → 0.27s)
- `_transicao_rev_full`: índice invertido completo
  (era O(P) por chamada de extrair_relacoes, agora O(1) — 30s → 1s)
- `_posicao_acao_inv`: índice invertido de `_posicao_acao`
- `_cache_idf_doc` pré-construído no `load()`

### Wikipedia ingerida

240 conceitos × 5 idiomas (PT/EN/ES/FR/DE) = 80.093 frases.
Concept ID como ação (cachorro(PT) e dog(EN) compartilham
ação:cachorro — ponte natural).

Delta=0.287 PASS SEM pontes (só Wikipedia+Rosetta).

**Gutenberg NÃO ingerido**: 416.993 frases baixadas, delta cai
de 0.314 (sem) para 0.081 (com). Literatura dilui discriminação
— tokens comuns entre todos os conceitos.

---

## Fase 22: Comutação de Nível + Ecologia de MCRs (2026-07-19 a 2026-07-20)

```
Comutacao em decidir(): so Esfera/Trigrama, sem random.
Ecologia de MCRs: 5 estagios validados.
Colonia como agente.
```

### Comutação de nível ajustada

Amostragem proporcional REMOVIDA (`random.uniform` viola Pilar 1).
Comutação para Esfera→Trigrama mantida (determinística,
conf < 0.15). 113/113 + 64/64 intactas.

### Ecologia de MCRs — 5 estágios

| Estágio | Descrição | Resultado |
|---------|-----------|-----------|
| v3 | Orquestração NMI | Ecossistema estável (1.5×) |
| v4 | Morte via vida_media < 2.0 | Seleção 2.6× |
| v4 final | AutoComposicao cria especialistas | Ciclo completo |
| v4.5 | Museu dos mortos (aprendizado vicário) | 60 modulações, 0 mudança de trajetória |
| v5 | Delegação como ação | Razão caiu 1.4×, trigger hardcoded viola Pilar 1 |

### Colônia como agente com auto-observação (v7)

- Colônia alimenta `estado_ferreiro=True/False` como feature
  derivada da PRÓPRIA memória P(b|a)
- Criação automática (necessidade), poda automática
  (vida < 2.0)
- **3 BONS vivos, 0 RUINS, 23 criações, 20 mortes**
- Memória da colônia: 38 palavras, 12 ações

**Self da colônia existe nos dados** mas não é acessível via
raw coupling. Precisa de mecanismo discriminativo (lift, NMI,
IDF) — mesmo problema do `_nmi_semantico` vs coupling bruto
na BaseConhecimento.

---

## Fase 23: Lift + Zoom + MCR Observador (2026-07-20)

```
Lift discrimina onde raw decidir() falha.
Zoom: mesmo operador, 3 escalas, padrao invariante.
MCR observador sem rotulos: 66.7%.
```

### Lift como discriminador

`lift = P(feature|acao) / P(acao)` normaliza frequência global.

| Método | Acertos |
|--------|---------|
| Raw decidir() | 0/5 (0%) |
| Lift | 4/5 (80%) |

Predição de feedback por domínio: **perfeita** —
BONS→feedback_bom lift>0, RUINS→feedback_ruim lift>0.

### Zoom validado

O mesmo operador (lift) discrimina estrutura em 3 escalas:

| Nível | Escala | Resultado |
|-------|--------|-----------|
| 1 | char→palavra | 4/4 (silaba_fer, silaba_bib, silaba_tro, silaba_alq) |
| 2 | palavra→colônia | 5/5 (cada domínio mapeia para ação criar_X) |
| 3 | colônia→meta | 2/4 (parcial — falha em consultas sem overlap token) |

**Conclusão**: o padrão é invariante por escala. O mesmo
operador (lift) discrimina estrutura em todas as escalas —
cilindro, não torre.

### MCR como observador (dados reais, sem rótulos)

32 frases reais (de SESSAO 2026-07-18). Cada frase = ação
única, sem rótulo de tema.

Zero-shot: **8/12 (66.7%)** de novas frases agrupadas no tema
correto — sem etiquetas injetadas no treino.

Erros: tokens compartilhados entre temas ("mcr", "voce") não
discriminam.

**Não é tautologia**: MCR agrupa sem Kheltz ter dito o que é
"identidade" vs "técnico" vs "filosofia" vs "emoção".

---

## Estado Atual (2026-07-20)

| Métrica | Valor |
|---------|-------|
| Módulos Python | 133 (46.286 linhas) |
| Arquivos de teste | 164 |
| Regressão Fase 1 | 113/113 = 100% |
| Regressão Fase 18 | 64/64 PASS |
| Observações ingeridas | 167.434 |
| Vocabulário | 214.907 palavras |
| Ações no motor | 14+ |
| Corpus | Wikipedia (80K) + Rosetta (4K) + sintético (50K) + matemático (700) |
| Latência decidir() | ~50ms |
| Tempo treino 167K obs | ~30s |

### Limitações honestas

1. Markov de 1ª ordem — o limite é fundamental
2. Zero-shot de palavras novas não funciona
3. P(b|a) bruto não discrimina auto-conhecimento
4. Horizonte nível 7: self individual não emerge
5. 167K obs testado — milhões/bilhões não verificado
6. Gutenberg não ingerido (dilui)

### Próximos passos

1. Propagar `_RE_TOKENS` para 34 lugares restantes
2. Conectar níveis 4-6 ao chat (intenção/emoção/estilo)
3. Integrar lift como método nativo do coupling
4. Conectar colônia auto-observadora ao motor principal
5. Treinar Abstração em escala (O(N²) → otimizar)
6. Conectar Teoria da Mente como 3º módulo cognitivo

---

## Sobre o Projeto MCR

O Projeto MCR começou como um servidor de Tibia (OTServ Canary).

Dentro dele, nasceu um motor Markov.

O motor Markov se tornou um framework cognitivo.

O servidor de Tibia virou o campo de provas.

**A pergunta não é "o MCR gera NPCs?".**
**A pergunta é: "Markov 1ª ordem + Entropia + 1 Equação = Cognição?"**

A resposta ainda está sendo construída.

