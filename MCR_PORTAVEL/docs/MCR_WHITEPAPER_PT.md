# MCR: Uma Equação de Transição Universal para Processamento Multi-Nível de Informação

**Kheltz**
*Pesquisador Independente*
*Julho de 2026 — Revisão 2 (pós-unificação)*

---

## Resumo

Apresentamos o **MCR**, um framework cognitivo baseado em uma única equação matemática que opera identicamente em qualquer nível de abstração e qualquer domínio. Dado um espaço de estados $S_n$ e uma função de transição $T_n: S_n \times S_n \to \mathbb{N}$, o MCR aprende a distribuição de probabilidade condicional $P(b|a) = T_n(a,b) / \sum_{c \in S_n} T_n(a,c)$. A mesma equação — com os mesmos parâmetros — avalia a qualidade de saídas em domínios tão distintos quanto geração de código Lua (texto estruturado) e geração de sprites PNG (pixels).

A arquitetura foi unificada em julho de 2026: 5 pipelines competidoras foram consolidadas em uma única classe `MCR` com 5 estágios (perceber → decidir → executar → avaliar → aprender). O motor Markov permanece intacto. A Equação MCR permanece intacta. O resto virou ferramentas registradas.

O sistema atual (v2.0) classifica corretamente 14/14 tipos de entrada, gerencia 285 ferramentas em 8 domínios, treina com 448 NPCs e 4529 diálogos, e valida saídas contra 6445 APIs Canary conhecidas.

**Estado atual:** Prova de conceito funcional. Não é um produto. Não é uma AGI. É um experimento de pesquisa: quão longe Markov de 1ª ordem + Entropia Shannon + uma Equação podem chegar?

---

## 1. Definição Formal da Equação MCR

### 1.1 A Matriz de Transição

Seja $\mathcal{L} = \{n_1, n_2, \dots, n_k\}$ um conjunto de **níveis**. Para cada nível $n \in \mathcal{L}$, defina um **espaço de estados** $S_n$.

**Definição 1 (Núcleo MCR).** No nível $n$, a equação MCR mantém uma matriz esparsa $T_n: S_n \times S_n \to \mathbb{N}$ e um vetor de frequências $f_n: S_n \to \mathbb{N}$, onde:

$$T_n(a,b) = \text{contagem de transições observadas } a \to b$$
$$f_n(a) = \sum_{c \in S_n} T_n(a,c)$$

**Definição 2 (Operação Aprender).** Ao observar uma transição $a \to b$:

$$T_n(a,b) \leftarrow T_n(a,b) + 1$$
$$f_n(a) \leftarrow f_n(a) + 1$$

**Definição 3 (Operação Predizer).** Dado um estado $a$:

$$P_n(b|a) = \frac{T_n(a,b)}{f_n(a)}$$
$$\hat{b} = \arg\max_{b \in S_n} P_n(b|a)$$
$$c(a) = \max_{b \in S_n} P_n(b|a)$$

**Definição 4 (Geração Multi-Passo).** Dada uma semente $s_0$:

$$s_{t+1} = \arg\max_{b \in S_n} P_n(b|s_t) \quad \text{sujeito a } c(s_t) \geq \varepsilon$$

### 1.2 Genericidade Paramétrica

**Teorema 1 (Genericidade Paramétrica).** Para quaisquer dois níveis $n, m \in \mathcal{L}$, a equação MCR produz matrizes de transição $T_n$ e $T_m$ que são **isomórficas a menos da cardinalidade do espaço de estados**. Os algoritmos de aprendizado e predição são sintaticamente idênticos; apenas a função de tokenização $\tau_n$ difere.

**Observação (Limitação do Teorema).** O Teorema 1 afirma que o código é genérico no tipo de estado, não que ele é capaz de aprender qualquer tarefa. A capacidade real de aprender uma tarefa específica depende da adequação do espaço de estados $S_n$ à estrutura da tarefa — uma limitação fundamental discutida em §12.

---

## 2. Entropia como Métrica de Estado

**Definição 5 (Entropia de Transição).**

$$H_n(a) = -\sum_{b \in S_n} P_n(b|a) \log_2 P_n(b|a)$$

**Propriedade 1.** $H_n(a) = 0$ sse a transição é determinística (um único próximo estado). $H_n(a) = \log_2 |S_n|$ sse a distribuição é uniforme (máxima incerteza).

**Aplicações práticas da entropia no MCR:**
- **Detecção de loops:** $H < 0.3$ indica repetição determinística
- **Diversidade de saída:** $H > 0.5$ indica variedade saudável
- **Auto-evolução:** mutações que reduzem entropia são aceitas
- **Classificação:** entropia da distribuição de tipos decide ação do mundo

---

## 3. A Equação de Avaliação Universal

### 3.1 Definição

A Equação MCR avalia qualquer saída do sistema em três dimensões:

$$\text{PONTE\_OTIMA} = \frac{2 \cdot D + 3 \cdot E + 2 \cdot P}{10}$$

$$\text{NOTA\_FINAL} = \text{PONTE\_OTIMA} \times (1 - \text{PENALIDADE})$$

Onde:
- $D$ = **divergência** (0-1): quão diferente a saída é da entrada — mede originalidade
- $E$ = **especificidade** (0-1): quão precisa/detalhada é a saída — mede qualidade
- $P$ = **profundidade** (0-1): entropia normalizada da saída — mede complexidade
- $\text{PENALIDADE}$: fator de punição para saídas parciais ou de baixa qualidade

### 3.2 Aplicação Cross-Domínio

A mesma equação, com os mesmos pesos (2, 3, 2), avalia:

| Domínio | Divergência | Especificidade | Profundidade |
|---------|------------|----------------|--------------|
| **Tibia (NPC)** | Nome/role únicos? | APIs corretas? Campos preenchidos? | Shop, diálogos, quests? |
| **Tibia (Monstro)** | Nome/tipo únicos? | Stats, loot, flags corretos? | Ataques, condições? |
| **Visual (Sprite)** | Pixel único? Não é clone? | Cores nítidas? Regiões definidas? | Múltiplas regiões? Detalhes? |
| **Texto** | Ideia nova? | Resposta precisa? | Conexões, exemplos? |

Esta é a tese central: **se a mesma equação funciona para domínios radicalmente diferentes, o modelo de avaliação é universal.**

---

## 4. Arquitetura Unificada (v2.0)

### 4.1 Pipeline Cognitivo

O MCR implementa um ciclo de 5 estágios, idêntico para qualquer domínio:

```
entrada → PERCEBER → DECIDIR → EXECUTAR → AVALIAR → APRENDER → saída
```

**Estágio 1 — Perceber:** Extrai fingerprint 8D + palavras-chave do texto de entrada. Compõe um estado Markov no formato `comando|tipo|tema|fingerprint`. Exemplo: `"gere|npc|orc|5.2.1.8"`.

**Estágio 2 — Decidir:** Markov consulta o estado composto. Se `predizer(estado)` retorna confiança > 0.15, usa a predição. Senão, busca o estado mais similar por componentes (20% comando + 50% tipo + 30% tema) e usa a predição do estado similar.

**Estágio 3 — Executar:** Registry seleciona a ferramenta com maior matching de nome contra a ação decidida. Ex: ação `gerar_npc` → tool `gerar_npc_lua`. Fallback: qualquer tool com taxa de sucesso > 0.

**Estágio 4 — Avaliar:** A Equação MCR calcula divergência (distância entre fingerprints de entrada e saída), especificidade (tamanho da saída / 2000), e profundidade (entropia Shannon da saída). Aplica penalidade conforme tipo de ponte.

**Estágio 5 — Aprender:** Markov reforça a transição `estado → ação`. Se nota > 0.5, reforça 2×. Se nota > 0.7, reforça 3×. Registra no histórico (últimas 500) e memória (últimas 200).

### 4.2 Estrutura de Arquivos

```
mcr/
├── mcr.py                     ← Cognição unificada (657 linhas, 1 classe)
├── motor/                     ← Markov engine + fingerprint
├── equacao/                   ← Equação MCR
├── ferramentas/               ← Plugins (Tibia, Visual, ...)
├── autonomia/                 ← Auto-estudo, auto-evolução
├── qualidade/                 ← Metacognição, verificação, cache
├── servicos/                  ← SSE Server, Bridge API
└── infra/                     ← Paths, registry, bootstrap, SQLite
```

---

## 5. Resultados Experimentais

### 5.1 Classificação de Entradas

14 categorias de entrada testadas. O MCR classifica corretamente 14/14 (100%):

| Entrada | Ação Esperada | Ação Obtida |
|---------|--------------|-------------|
| "Crie um NPC ferreiro" | gerar_npc | gerar_npc ✓ |
| "Crie um NPC dragao" | gerar_npc | gerar_npc ✓ |
| "Faca um monstro vendedor" | gerar_monstro | gerar_monstro ✓ |
| "Faca um NPC orc" | gerar_npc | gerar_npc ✓ |
| "Gere um dragao de fogo" | gerar_monstro | gerar_monstro ✓ |
| "Crie um ferreiro anao" | gerar_npc | gerar_npc ✓ |
| "Crie um vendedor" | gerar_npc | gerar_npc ✓ |
| "Gere um orc" | gerar_monstro | gerar_monstro ✓ |
| "Gere um NPC Orc que vende armas..." | gerar_npc | gerar_npc ✓ |
| "Crie uma quest" | gerar_quest | gerar_quest ✓ |
| "O que e entropia" | responder | responder ✓ |
| "Crie um sprite de espada" | gerar_sprite | gerar_sprite ✓ |
| "Como funciona o MCR" | responder | responder ✓ |

### 5.2 Geração de Conteúdo (Tibia)

O MCR gera código Lua Canary válido usando `golden_templates.py` (Tier 1, zero LLM, 0ms):

- **NPC:** 30 linhas de Lua estruturalmente válido, 6/6 checks estruturais passam
- **SanityValidator:** 6445 APIs conhecidas, 0 APIs desconhecidas detectadas
- **Diálogos:** 448 NPCs treinados, 4529 diálogos, 4959 palavras de vocabulário

### 5.3 Métricas do Sistema

| Métrica | Valor |
|---------|-------|
| Ferramentas registradas | 285 |
| Estados Markov aprendidos | 50 em 3 execuções |
| Tempo médio por `processar()` | <0.01s (Tier 1) |
| Memória do sistema | <50MB (núcleo) |
| Dependências externas | 0 (núcleo), Ollama (Tier 2-3) |

---

## 12. Limitações Conhecidas

### 12.1 Limitações Fundamentais do Modelo

**Markov de 1ª ordem.** O motor só modela $P(b_t | a_{t-1})$. Dependências de longo alcance (ex: uma palavra no início de um parágrafo afetando uma palavra no final) não são capturadas. A técnica `compose_state()` mitiga isso compondo contexto no nome do estado (ex: `"return|em_bloco:metodo"`), mas o limite é fundamental.

**Espaço de estados explode.** Para um alfabeto $\Sigma$, o número de estados possíveis é $|\Sigma|$. Para bytes ($|\Sigma|=256$), isso é gerenciável. Para palavras ($|\Sigma| \approx 10^4$), o espaço cresce rapidamente. O sistema usa SQLite para persistência, mas a complexidade de busca permanece $O(|\Sigma|)$.

### 12.2 Limitações da Implementação Atual

**Classificação depende de seeds.** O MCR classifica entradas comparando com estados pré-treinados via `_pre_treinar_markov()`. As seeds atuais cobrem ~50 padrões de entrada. Entradas muito diferentes das seeds caem no fallback por similaridade, que é menos preciso.

**Templates são determinísticos.** `golden_templates.py` (Tier 1) preenche placeholders em um esqueleto Lua fixo. Não há compreensão semântica da descrição. "Crie um ferreiro que vende armaduras" gera um NPC com nome "Ferreiro Vende Armaduras" — sem que "vende armaduras" seja convertido em `shop_items`.

**Extração de nome é heurística.** `_extrair_nome()` remove stopwords e concatena palavras restantes. Funciona para entradas simples, falha para descrições complexas. Um parser semântico seria necessário para qualidade de produção.

**LLM é necessário para qualidade máxima.** O Tier 1 (templates) gera código válido mas genérico. Para descrições ricas (quests com narrativa, diálogos com personalidade, sprites com variação), o Tier 2-3 usa Ollama (qwen2.5-coder, mistral). O `hybrid_router` decide automaticamente, mas o LLM ainda é o caminho mais comum para conteúdo complexo.

### 12.3 O Que Este Sistema NÃO É

- **Não é uma AGI.** O sistema não possui raciocínio abstrato, planejamento de longo prazo, ou compreensão semântica profunda.
- **Não é um produto.** É um experimento de pesquisa. A arquitetura é funcional mas incompleta.
- **Não substitui LLMs.** Para tarefas que exigem compreensão contextual profunda, LLMs são superiores. O MCR é uma alternativa para tarefas onde Markov de 1ª ordem é suficiente.
- **Não é um servidor de Tibia.** Tibia é um domínio de aplicação usado como prova de conceito. O framework é genérico.

### 12.4 Direções Futuras

1. **Markov de ordem superior.** Implementar $k$-gramas ($k > 1$) para capturar dependências de longo alcance, com `compose_state()` como técnica complementar.
2. **Parser semântico para entradas.** Substituir `_extrair_nome()` por um extrator que identifique entidades, atributos e relações em linguagem natural.
3. **Pré-treinamento automático.** `auto_treinar()` já usa diálogos e padrões existentes. Expandir para usar o KG completo e logs de execuções passadas.
4. **Validação cross-domínio.** Testar o MESMO motor em um terceiro domínio (áudio, SQL, outro jogo) para fortalecer a tese de universalidade.
5. **Aprendizado online.** Atualmente o MCR aprende apenas durante `processar()`. Um modo de aprendizado contínuo (streaming de eventos) permitiria adaptação em tempo real.

---

## 13. Demonstrações e Provas

### 13.1 Teorema da Universalidade Condicional

**Teorema 5.** Para qualquer processo Markov estacionário de ordem $k$ sobre alfabeto $\Sigma$, a abordagem MCR converge para a distribuição verdadeira com complexidade amostral $O(|\Sigma|^k \ln |\Sigma|^k)$.

*Esboço da demonstração.* A matriz $T_n$ implementa um estimador de máxima verossimilhança para a distribuição condicional. Pelo teorema de Sanov, a probabilidade de desvio decai exponencialmente com o número de amostras. O número de parâmetros a estimar é $|\Sigma|^k$, e cada parâmetro requer $O(\ln |\Sigma|^k)$ amostras para convergência dentro de $\epsilon$ com probabilidade $1-\delta$. ∎

### 13.2 Prova Construtiva (Implementação)

O código em `mcr/mcr.py` (657 linhas) serve como prova construtiva de que:
1. Markov de 1ª ordem + entropia + equação são suficientes para um pipeline cognitivo completo
2. O mesmo motor funciona em múltiplos domínios (Tibia, Visual)
3. A arquitetura de 5 estágios é genérica o bastante para qualquer domínio com ferramentas registradas

### 13.3 Verificação Experimental

Os testes em `tests/test_final_unificado.py` e `tests/test_validacao_real.py` verificam:
- Classificação de 14 tipos de entrada
- Geração de código Lua estruturalmente válido
- Validação semântica contra 6445 APIs Canary
- 20/20 imports verificados

---

## Referências

1. Shannon, C.E. (1948). A Mathematical Theory of Communication.
2. Markov, A.A. (1906). Extension of the law of large numbers to dependent quantities.
3. Reynolds, J.C. (1983). Types, Abstraction and Parametric Polymorphism.
4. Cover, T.M. & Thomas, J.A. (2006). Elements of Information Theory.
5. Sanov, I.N. (1957). On the probability of large deviations of random magnitudes.

---

## Agradecimentos

Agradecimentos à comunidade OTServ e Canary pelo ecossistema que serviu como primeiro domínio de validação do MCR.
