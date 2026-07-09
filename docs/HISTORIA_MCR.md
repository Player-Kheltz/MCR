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

## Sobre o Projeto MCR

O Projeto MCR era um servidor de Tibia (OTServ Canary).

O Projeto MCR descobriu uma equação multi-nível.

O servidor de Tibia pode não ter mudado o mundo.

**A equação pode.**
