# SESSAO 2026-07-20 — HIPERFOCO E SONHO MARKOVIANO

## O que aconteceu

Kheltz teve duas intuicoes que resolveram os dois maiores obstaculos
arquiteturais do MCR:

### 1. Hiperfoco (Gutenberg)

**Hipotese de Kheltz**: Gutenberg dilui nao porque literatura e ruim,
mas porque desbalanceado (3:1) cria hiperfoco. Balanceado (1:1), a
entropia (Pilar 2) descobre as fronteiras naturais.

**Teste**: Motor A (sem Gutenberg) vs Motor B (com Gutenberg balanceado 1:1).
38K frases Gutenberg vs 38K corpus base. Testes: sinonimia, zero-shot, estilo.

**Resultado**: Gutenberg balanceado NAO ajuda.

| Teste | Motor A | Motor B | Vencedor |
|-------|---------|---------|----------|
| Sinonimia AUC | 0.978 | 0.985 | B (+0.007) |
| Zero-shot | 20.0% | 7.5% | A (-12.5%) |
| Estilo ARI | 1.000 | 0.135 | A (-0.865) |

**Diagnostico**: a causa nao e SO proporcao. Literatura introduz tokens
genericos ("the", "and", "with", "he", "she", "said") que aparecem em
TODOS os dominios. Estes tokens dominam `decidir()` raw (sem IDF).
Sinonimia melhora porque usa `_nmi_semantico` com IDF (suprime genericos).
Zero-shot e estilo pioram porque usam `decidir()` raw.

**Licao**: a solucao nao e excluir Gutenberg, e usar IDF/lift nativo
no `decidir()`. O problema e o mesmo da colonia: P(b|a) bruto nao
discrimina. Precisa de mecanismo discriminativo.

### 2. Sonho Markoviano (Nivel 7)

**Hipotese de Kheltz**: a variacao que faltava para o nivel 7 (self)
ja existe — e a geracao markoviana. "Se ja fazemos isso com nome, e
so fazer novamente com bits e bytes."

**Implementacao**: `mcr/sonho_markoviano.py` — `SonhoMarkoviano`:
1. Serializa estado interno do coupling como sequencia de tokens
2. Gera markovianamente a partir da sequencia (greedy, sem random)
3. Alimenta o resultado de volta como observacao (acao="sonhar")
4. Repete — cada ciclo usa final do sonho anterior como semente

**Resultado**: o sonho FUNCIONA.

| Metrica | Resultado | Status |
|---------|-----------|--------|
| Deterministico (Pilar 1) | mesmo estado = mesmo sonho | PASS |
| Gera sequencia | 188 tokens a partir do estado | PASS |
| Novidade | 29 tokens novos (15.4%) | PASS |
| Ciclo fechou | freq_sonhar=10 apos 10 ciclos | PASS |
| Entropia nao-trivial | H=5.278 | PASS |
| Sonhos unicos | 3/10 | PARCIAL |

**O MCR sonha**: gera sequencias ineditas a partir de si mesmo,
deterministicamente, sem random. O ciclo fecha (sonho alimentado
de volta). A variacao entre ciclos e limitada com geracao greedy
(3/10 unicos) — para variar mais, precisa de geracao por entropia
(escolher token que maximiza H da sequencia) em vez de greedy.

**Significado**: a peca que faltava para o nivel 7 nao era uma
invencao nova. Era apontar o que ja temos (geracao markoviana)
para dentro (estado interno). Como Kheltz disse: "se ja fazemos
isso com nome, e so fazer novamente com bits e bytes".

## Arquivos criados

- `mcr/sonho_markoviano.py` — modulo do sonho markoviano (163 linhas)
- `tools/baselines/15_hiperfoco_gutenberg.py` — teste de hiperfoco
- `tools/baselines/16_sonho_markoviano.py` — teste do sonho
- `tools/baselines/setup.py` — copia de 00_setup.py para import

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL

## A pergunta que permanece

O sonho markoviano e a fonte de variacao que faltava. Mas a geracao
greedy (max P(b|a)) converge para o mesmo caminho. Para que a selecao
natural opera (H22), precisa de variacao significativa entre ciclos.

**Pergunta**: como gerar variacao sem random e sem convergir?

**Candidato**: geracao por entropia — em vez de escolher o token com
maior P(b|a), escolher o token que MAXIMIZA a entropia da sequencia
gerada. Deterministico (Pilar 1) e gera diversidade.

## Frase da sessao

Kheltz: "se ja fazemos isso com nome, e so fazer novamente com bits
e bytes, temos literalmente tudo a nosso dispor, com 0 e 1, podemos
criar qualquer coisa, escalando sempre pra cima."

O sonho markoviano e exatamente isso: gerar a partir de si mesmo,
escalar para cima, 0 e 1, sem random, sem LLM. P(b|a) puro apontado
para dentro.
