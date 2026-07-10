> **Documenta��o hist�rica.** Este documento descreve vers�es anteriores do MCR.
> Para o estado atual, veja [README.md](../README.md) e [MANIFESTO_MCR.md](../MANIFESTO_MCR.md).
# Limitações e Roadmap do MCR

## Limitações Conhecidas

### 1. Ordem 1 (último estado apenas)

O MCR Clássico vê apenas o último token para predizer o próximo. Não capta:
- Sintaxe aninhada (`"se X então Y"` precisa ver `"se"`)
- Dependências de longo alcance (um sujeito no início que rege o verbo no fim)
- Raciocínio multi-passo

**Mitigação:** A Geração por Assinatura avalia cada candidato contra a **sequência completa** usando byte + palavra + token, que compensa parcialmente a falta de ordem.

**Roadmap:** Markov de ordem 2-3 com chave composta (`chave = "a→b"`).

### 2. Sem estado latente (tokens puros)

"Gato" e "felino" são tokens distintos. O modelo não sabe que são conceitos similares.

**Mitigação:** O Jaccard entre contextos de transição "gato" e "felino" revela similaridade indiretamente (ambos transicionam para "mia", "dorme").

**Roadmap:** Agrupamento de tokens por similaridade de vetor de transições (Jaccard entre `transicoes[token]`).

### 3. Sem composicionalidade

Não entende hierarquia de subobjetivos. Uma ação complexa ("fazer café") não é decomposta em sub-ações ("moer grãos", "ferver água").

**Roadmap:** Hierarquia de níveis com realimentação (nível superior influencia predição do inferior).

### 4. Pontes falsas em conectores gramaticais

O byte `B:65` (letra 'e') aparece em quase todo texto em português. O MarkovCruzado pode encontrar pontes em conectores que não carregam significado.

**Mitigação:** O filtro `CONECTORES` + autoavaliação de PALAVRA penalizam sequências sem palavras de conteúdo.

**Roadmap:** Busca por ponte num filtro de palavras de conteúdo (4+ caracteres, não conector).

### 5. Arquivos com cabeçalho (WAV, PNG, etc.)

Formatos como WAV têm cabeçalhos de 44 bytes que não representam o conteúdo real. A entropia do arquivo inteiro é influenciada pelo cabeçalho.

**Mitigação:** Para análise de conteúdo, extrair payload após o cabeçalho.

**Roadmap:** Detecção automática de cabeçalho por entropia de bloco.

## Roadmap

### Curto prazo (próximas semanas)

- [ ] Markov de ordem 2 (`chave = "a→b"`)
- [ ] Agrupamento de tokens por similaridade de transições
- [ ] Detecção automática de cabeçalhos de formato

### Médio prazo (próximo mês)

- [ ] Normalização de frequência (probabilidade em vez de contagem)
- [ ] Módulo de importação/exportação de modelos treinados
- [ ] Interface de linha de comando (`mcr analyze`, `mcr connect`)

### Longo prazo

- [ ] Hierarquia de níveis com realimentação
- [ ] Atenção determinística (janela de contexto variável)
- [ ] Versão em C para microcontroladores

## O que MCR NÃO vai tentar

- Embeddings densos (numpy, torch) — perderia a vantagem de 0 dependências
- Backpropagation — perderia determinismo e interpretabilidade
- Transformer blocks — perderia "~438KB"
- Competir com LLM em tarefas gerais — MCR complementa, não substitui
