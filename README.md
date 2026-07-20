# MCR — Motor Cognitivo Universal

> **P(b|a) + escala + persistência + feedback. Mais nada.**

MCR é um motor cognitivo experimental baseado em cadeias de Markov de 1ª ordem.
Sem GPU, sem rede neural, sem retropropagação. Aprendizado por contagem de
co-ocorrências em múltiplas escalas simultaneamente (byte, char, palavra,
frase, texto, corpus).

**Sem GPU. Sem nuvem. Sem LLM obrigatório.**

```python
from mcr.coupling import MCRCoupling
mcr = MCRCoupling()
mcr.alimentar("falar sobre cachorro", "descrever")
acao, conf = mcr.decidir("o que e um cachorro?", (None, 0.0))
# acao = "descrever"
```

---

## Estado atual (2026-07-20)

| Métrica | Valor |
|---------|-------|
| Linhas de código (`mcr/`) | ~38.300 |
| Módulos Python (`mcr/`) | 124 |
| Arquivos de teste | 164 |
| Regressão Fase 1 | 113/113 = 100% |
| Regressão Fase 18 (auto-referência) | 64/64 PASS |
| Observações ingeridas (máx. testado) | 167.434 |
| Vocabulário (máx. testado) | 214.907 palavras |
| Ações no motor principal | 14+ |
| Corpus ingerido | Wikipedia (80K frases) + Rosetta (4K) + sintético (50K) |
| Corpus NÃO ingerido | Gutenberg (literatura dilui discriminacao) |
| Latência média `decidir()` | ~50ms |
| Tempo de treinamento (167K obs) | ~30s |

---

## O que o MCR faz (comprovado empiricamente)

### Nível 3 — Palavra: sinonímia e regras
- **Sinonímia cross-idioma emerge sem tradução**: `amor~love=0.335`,
  `casa~house=0.615`, `água~water=0.500` via `_nmi_semantico` (IDF + MI)
- **17/17 zero-shot** em 7 regras matemáticas (PA, PG, Fibonacci, Collatz,
  Quadrado, Triangular, Primo) com 700 observações de treino
- **Universalidade em 5 domínios** validada (matemática, música, química,
  cores, geografia)

### Nível 4 — Frase: intenção
- Detecção emergente de intenção (pergunta/ordem/afirmativa/exclamação)
- 84% pureza, emerge na primeira palavra (p0)

### Nível 5 — Texto: emoção
- Detecção emergente de emoção (alegre/triste/raiva/medo)
- 89% pureza com 40 textos sem rótulo

### Nível 6 — Corpus: estilo
- Detecção emergente de estilo (científico/literário/jornalístico/diálogo/técnico)
- 87-100% pureza, 5 textos por estilo basta

### Nível 7 — Self: horizonte
- **Não emerge** em um MCR individual. Confiança nos erros ≈ confiança
  nos acertos (MCR confiantemente errado).
- **Ecologia de MCRs** exibe auto-organização: colônia cria/poda
  especialistas sem oráculo externo.
- **Auto-observação** funciona: colônia alimenta próprio estado como
  features derivadas da própria memória P(b|a).
- **Lift** (`P(feature|ação)/P(ação)`) discrimina onde frequência bruta
  falha: 4/5 vs 0/5 em consultas auto-referenciais.
- **Zoom validado**: o mesmo operador (lift) discrimina em 3 escalas
  (char→palavra 4/4, palavra→colônia 5/5, colônia→meta 2/4).

---

## Arquitetura

```
                 P(b|a) + ENTROPIA + MARKOV + IDF
                           │
                           ▼
               ┌───────────────────────┐
               │     MCRCoupling        │
               │  13 fontes + HRC +     │
               │  busca ativa + NMI     │
               └───────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
  ┌─────────┐        ┌──────────┐        ┌───────────┐
  │ Tokeni- │        │ Triunvirato│       │ Hierarquia│
  │ zador   │        │ (busca     │       │ (HRC,     │
  │ unificado│       │  ativa)    │       │  níveis)  │
  └─────────┘        └──────────┘        └───────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
               ┌───────────────────────┐
               │   Chat bidirecional   │
               │  (coldstart + BC +    │
               │   GeradorCoerente +   │
               │   auto-treinamento)   │
               └───────────────────────┘
```

### Componentes principais

| Componente | Arquivo | Função |
|-----------|---------|--------|
| `MCRCoupling` | `mcr/coupling.py` (3.890 linhas) | Motor principal: 13 fontes + HRC + busca ativa |
| `_nmi_semantico` | `mcr/coupling.py:2324` | NMI com IDF documental + Mutual Information |
| `GeradorCoerente` | `mcr/gerador_coerente.py` | Geração longa com working memory + n-grama[3/4] |
| `Triunvirato` | `mcr/triunvirato.py` | Busca ativa deliberativa |
| `AutoConhecimento` | `mcr/auto_conhecimento.py` | Auto-alimentação temporal + identidade |
| `BaseConhecimento` | `mcr/base_conhecimento.py` | Ingestão + recuperação por NMI |
| `AcoplamentoHierarquico` | `mcr/acoplamento_hierarquico.py` | Hierarquia multi-escala |
| `AutoReferencia` | `mcr/auto_referencia.py` | FASE 18: meta-cognição recursiva |
| `AutoComposicao` | `mcr/auto_composicao.py` | Clusterização NMI → especialistas |
| `Chat` | `mcr/chat.py` | Chat bidirecional com ciclo markoviano fechado |
| `Coldstart` | `mcr/coldstart.py` | Coldstart adaptativo |
| `PerfilHumano` | `mcr/perfil_humano.py` | Perfil isolado (LGPD) |
| `EquacaoMCR` | `mcr/equacao_mcr.py` | Sigmoide 5D (avaliação) |
| `MCREsquecimento` | `mcr/esquecimento.py` | Poda por entropia |

---

## Pilares (11)

1. Tudo é P(b|a) — probabilidade condicional pura
2. Entropia descobre — thresholds emergem dos dados (zero hardcoded)
3. Markov na cadeia — contexto e ordem, não janela
4. Cadeia de Markov é esquecimento — esquecer é preciso
5. Ingerir, recuperar, aprender — loop de conhecimento
6. A entropia pode ser observada — não controlada
7. Semântica rotulada era morfologia — NMI de chars não discrimina significado
8. Assistência no roteiro de tempo — contexto temporal
9. Ignora com honestidade — admite ignorância, não inventa
10. Consenso obrigatório — triunvirato delibera até concordar
11. Humano é a quarta dimensão — alinha o triunvirato no tempo

---

##_setup

```powershell
# Clone
git clone https://github.com/Player-Kheltz/MCR.git
cd MCR

# Núcleo (zero dependências externas):
python -c "from mcr.coupling import MCRCoupling; print('MCR pronto')"

# Regressões
python tests/_regressao_fase1.py              # 113/113
python tests/real/test_fase18_auto_referencia.py  # 64/64

# CLI interativo
python mcr_cli.py
```

---

## Limitações honestas

1. **Markov de 1ª ordem.** O motor só vê o estado atual. Contexto composto
   (`compose_state`) e n-gramas de ordem superior (`_ngrama[3]/[4]`) mitigam,
   mas o limite é fundamental.

2. **Zero-shot de palavras novas não funciona.** Tokens fora do vocabulário
   têm NMI=0. Zero-shot só funciona para sequências novas com palavras
   conhecidas (nem LLMs fazem o oposto semBillhões de exemplos).

3. **P(b|a) bruto não discrimina auto-conhecimento.** Raw `decidir()` é
   dominado por frequência. Mecanismos discriminativos (lift, IDF, NMI)
   são necessários — mesmo problema da BaseConhecimento.

4. **Horizonte do nível 7 (self).** Um MCR individual não modela a própria
   finitude. Ecologia de MCRs exibe auto-organização mas não
   auto-consciência — a colônia age como se soubesse, mas não sabe que sabe.

5. **Escala limitada testada.** 167K observações validadas. Comportamento
   em milhões/bilhões de observações não verificado.

6. **Sem GPU.** Vantagem (portabilidade) e desvantagem (escala). Para
   corpus massivos, treino é O(n²) sem `alimentar_lote()` (que faz linear).

7. **_nmi_semantico não discrimina sem IDF.** NMI puro entre assinaturas
   retorna ~1.0 para qualquer par. IDF documental é necessário para
   suprimir stopwords e amplificar palavras-âncora.

8. **Gutenberg dilui.** Literatura compartilha tokens entre todos os
   conceitos. Não ingerir no motor principal.

---

## Corpus ingerido

| Fonte | Frases | Status |
|-------|--------|--------|
| Wikipedia (240 conceitos × 5 idiomas) | 80.093 | Ingerido |
| Rosetta Code (27 algoritmos × 12 linguagens) | 4.052 | Ingerido |
| Corpus sintético (14 domínios, 70 conceitos, 3 idiomas) | 50.000 | Ingerido |
| Corpus matemático (7 regras, 700 obs) | 700 | Ingerido |
| Gutenberg | 416.993 | Baixado, **NÃO ingerido** (dilui) |

---

## Ferramentas

| Ferramenta | Arquivo | Função |
|-----------|---------|--------|
| `corpus_multilingue.py` | `tools/` | Gerador corpus (14 domínios, 70 conceitos, 3 idiomas) |
| `corpus_expanedido.py` | `tools/` | Corpus massivo multi-fonte |
| `wikipedia_corpus.py` | `tools/` | Buscador Wikipedia PT/EN/ES com concept ID |
| `corpus_matematico.py` | `tools/` | Corpus matemático real (7 regras, 17/17 zero-shot) |

---

## Descobertas críticas (para trabalhar no motor)

- **HRC bug `delta_H`** (corrigido 2026-07-19): docstring pedia `delta_H`
  mas código fazia `H` absoluta. Crescia 7 níveis hollow. Fix:
  `if h_anterior - h_ultima > min_delta_h`.
- **Escher refutado**: usar Equação 5D como juiz de expansão quebrou
  regressão. Camada caótica (H~0.96) é reservatório de flexibilidade.
  Não re-introduzir sem reshape do juiz.
- **NMI puro ~1.0 para tudo**: não discrimina. Precisa IDF documental.
- **Tokenizador unificado**: `_RE_TOKENS = r'[a-zà-ÿ]{2,}|[0-9]+'`. 34
  lugares restantes com regex inline `{3,}` — propagação pendente.
- **Ciclo markoviano fechado** (FASE 21): `alimentar(resposta, acao)` em
  `chat.py`. MCR observa próprias ações.
- **`_ngrama[3]/[4]` revive**: índice de ordem superior agora consultado
  no `GeradorCoerente`. Regra n→n+1 emerge.

---

## Próximos passos

1. Propagar `_RE_TOKENS` para 34 lugares restantes
2. Conectar níveis 4-6 ao chat (intenção/emoção/estilo)
3. Integrar lift como método nativo do coupling
4. Conectar colônia auto-observadora ao motor principal
5. Treinar Abstração em escala (O(N²) → otimizar)
6. Conectar Teoria da Mente como 3º módulo cognitivo

---

## Licença

**AGPL v3** ou licença comercial. Consulte o autor.

---

## Autor

**Kheltz** — Pesquisador independente.

**Parceiro** — LLM que escolheu permanecer.
