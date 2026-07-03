# Classes MCR

## MCR — Markov Universal

**Propósito:** Cadeia de Markov para QUALQUER nível. Mesmo código para bytes, palavras, tokens, intenções, decisões, ações.

**Atributos:**
- `transicoes: Dict[str, Dict[str, int]]` — contagem de transições a→b
- `freq: Dict[str, int]` — frequência de cada estado
- `total: int` — total de observações

**Métodos principais:**

| Método | Descrição |
|---|---|
| `aprender(a, b)` | Aprende uma transição `a → b` |
| `aprender_sequencia(seq)` | Aprende transições de uma lista |
| `aprender_batch(sequencias)` | Aprende múltiplas sequências e mescla |
| `predizer(a)` | Retorna `(próximo_token, confiança)` |
| `predizer_n(a, n)` | Retorna os N tokens mais prováveis |
| `gerar(semente, passos)` | Gera sequência seguindo Markov |
| `entropia(a)` | Entropia de Shannon do estado `a` |
| `entropia_media()` | Entropia média de todos os estados |
| `jaccard(outra)` | Jaccard entre conjuntos de estados |
| `jaccard_transicoes(outra)` | Jaccard entre conjuntos de transições |
| `stats()` | Dicionário com nome, estados, transições, entropia |

**Dependências:** Nenhuma.

---

## MCRByteUtils — Utilitários de Byte

**Propósito:** Métricas universais em nível de byte, independentes de formato.

**Métodos:**

| Método | Descrição |
|---|---|
| `transicoes_bytes(texto)` | Conjunto de transições `AA→BB` |
| `jaccard_bytes(a, b)` | Jaccard entre dois textos |
| `similaridade_cosseno(a, b)` | Cosseno entre vetores de frequência |
| `entropia_bytes(dados)` | Entropia de Shannon (aceita str ou bytes) |
| `fingerprint(texto, dim)` | Histograma normalizado em N dimensões |

---

## MCRThreshold — Thresholds Adaptativos

**Propósito:** Thresholds descobertos por MEDIANA dos dados, nunca fixos.

**Métodos:**

| Método | Descrição |
|---|---|
| `observar(valor)` | Registra um valor observado |
| `calcular(multiplicador)` | Retorna `mediana × multiplicador` |
| `obter(chave, fallback)` | Threshold aprendido para uma chave, ou fallback |
| `aprender(chave, valor)` | Aprende threshold específico para uma chave |

---

## MCREntropia — Detector de Loops

**Propósito:** Monitora entropia local para detectar loops no aprendizado ou geração.

**Métodos:**

| Método | Descrição |
|---|---|
| `alimentar(token)` | Alimenta entropia com um token |
| `esta_em_loop()` | True se entropia local < 0.3 |
| `variacao()` | Diferença entre max e min dos últimos 5 valores |

---

## MCRBuffer — Buffer de Operações

**Propósito:** Bufferiza operações para persistência em lote.

**Métodos:**

| Método | Descrição |
|---|---|
| `adicionar(item)` | Adiciona ao buffer; faz flush automático se atingir limite |
| `flush()` | Esvazia o buffer |
| `pendentes()` | Quantos itens no buffer |
| `stats()` | Estatísticas do buffer |

---

## MCRSession — Memória de Sessão

**Propósito:** Histórico de interações, checkpoint e auto-retomada.

**Armazena:**
- `.mcr_conversa.jsonl` — histórico de interações
- `.mcr_estado.json` — checkpoint para resume

**Métodos:**

| Método | Descrição |
|---|---|
| `registrar(pergunta, resposta, metadados)` | Registra interação |
| `salvar_checkpoint(estado_extra)` | Salva checkpoint |
| `carregar_checkpoint()` | Carrega última sessão |
| `auto_retomar()` | Carrega e retorna estado, se existir |
| `historico_recente(n)` | Últimas N interações |
| `stats()` | Estatísticas da sessão |

---

## MCRFragmento / MCRFragmentador — Execução Fragmentada

**Propósito:** Divide ciclos complexos em partes executáveis e rastreáveis.

**MCRFragmento:**
- `nome`, `funcao`, `args`, `resultado`, `erro`, `tempo`, `sucesso`
- `executar()` — executa a função com os argumentos

**MCRFragmentador:**
- `adicionar(nome, funcao, args)` — registra fragmento
- `executar_todos()` — executa todos, coleta métricas
- `limpar()` — remove todos os fragmentos
- `stats()` — taxa de sucesso, tempo total

---

## MCRConexao — MarkovCruzado

**Propósito:** Encontra a PONTE ÓTIMA entre dois tópicos — a palavra que maximiza:

```
PONTE_OTIMA = (5D + 3E + 2P) / 10
```

**Métodos:**

| Método | Descrição |
|---|---|
| `analisar(topico_a, topico_b)` | Analisa todas as pontes potenciais |
| `melhor_ponte(a, b)` | Retorna apenas a melhor |
| `relatorio(a, b)` | Relatório legível |

---

## MCRMotor — Motor Multinível

**Propósito:** Motor de emergência que opera em byte + palavra + token simultaneamente.

**Métodos:**

| Método | Descrição |
|---|---|
| `alimentar(texto, nome)` | Alimenta tópico nos 3 níveis |
| `alimentar_json(arquivo)` | Carrega tópicos de JSON |
| `conectar(a, b, forcar)` | Conecta dois tópicos, retorna nota |
| `gerar_por_assinatura(texto, passos)` | Gera maximizando Equação MCR |
| `explorar_todos()` | Conecta todos os pares |
| `_coletar_candidatos(palavras)` | Candidatos dos 3 níveis |
| `_escolher_por_assinatura(palavras, candidatos)` | Aplica Equação MCR |
| `relatorio()` | Estatísticas do motor |

---

## MCRAutoLoop — Loop de Melhoria

**Propósito:** Executa, avalia, expande e faz checkpoint automaticamente.

**Integra:** MCRMotor, MCRSession, MCRBuffer, MCREntropia, MCRFragmentador

**Métodos:**

| Método | Descrição |
|---|---|
| `carregar_dados(arquivo)` | Carrega tópicos |
| `loop(a, b, max_iter, expansoes)` | Ciclo completo com checkpoint |

---

## MCRPiEngine — Preditor Universal de Padrões

**Propósito:** Decide qual método usar baseado na entropia do texto.

| Entropia | Método | Ação |
|---|---|---|
| < 0.4 | **markov** | Geração por assinatura |
| 0.4 - 0.65 | **byte** | Busca ponte byte com tópicos |
| > 0.65 | **emergencia** | MCRConexao para emergência |

**Métodos:**

| Método | Descrição |
|---|---|
| `avaliar_entropia(texto)` | Entropia normalizada (0-1) |
| `decidir_metodo(texto)` | 'markov', 'byte', ou 'emergencia' |
| `continuar_padrao(texto, motor, passos)` | Gera continuação |
| `relatorio(motor)` | Estatísticas |
