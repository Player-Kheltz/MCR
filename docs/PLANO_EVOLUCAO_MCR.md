# PLANO MCR — Roteiro de Evolução Cognitiva
**Versão**: 5.0 | **Data**: 2026-07-17 | **Status**: FASE 1-18 implementadas (113/113); FASE 20 (Triunvirato Navegador) iniciada — 5 peças em execução; visão reformulada após mesa de design: MCR não é "LLM melhor", é **categoria diferente** (navegador observador vs compressor memorizador)

> **Revisão v5.0 (2026-07-17)**: mesa de design reformulou a visão do MCR. Descobertas:
> 1. **Comparação "100% vs 70.8%" é metodologicamente frágil** — dataset sintético (template script), MCR testa no próprio output. O 100% é memorização do que foi gerado para ele. Não prova superioridade — prova classificação no-domínio.
> 2. **"Semântica" rotulada era morfologia** — `semantic_router.similaridade()` mede overlap de caracteres (trigrama/bigrama/Levenshtein/fingerprint), não significado. "cachorro"≈"perro" dá ~0.05 (falha); "criar"≈"destruir" dá ~0.35 (falso positivo). Herança morfológica funciona (validada), semântica real NÃO existe ainda.
> 3. **Visão reformulada: Triunvirato Navegador** — o MCR não é classificador melhor, é navegador universal: observa qualquer stream (byte-level), delibera por triumvirato (Markov+Entropia+5D), busca fatos ativamente em consenso obrigatório, dialoga com humano como parceiro (4D). Caminho diferente da LLM, não competição direta.
> 4. **3 peças já existem** (hierarquia, BaseConhecimento, WebLearn) — **desconectadas**. O trabalho é conectar, não inventar.
> 5. **Pilares 10 e 11 adicionados**: consenso obrigatório (10) e humano 4D (11).

## Objetivo
Transformar MCR de classificador (113/113, ~7ms) em **navegador cognitivo universal** — observa qualquer stream (byte-level: texto, imagem, áudio, sensor, humano), delibera por triunvirato (Markov + Entropia + 5D), busca fatos ativamente em consenso obrigatório, aprende em tempo real (O(1)), e dialoga com o humano como parceiro (não servo).

**Não é "LLM melhor"** — é categoria diferente: LLM comprime+generaliza em pesos congelados (caixa preta); MCR observa+navega em P(b|a) on-line (caixa de vidro).

## Princípios inegociáveis
- Markov 1ª ordem + Entropia Shannon + NMI = base de tudo
- Zero GPU, zero dependências externas, zero listas hardcoded
- Performance: decisão em <5ms, sensores em background
- Universal: qualquer idioma, qualquer domínio, qualquer modalidade (byte-level)

---

## REGIME DE COMPARAÇÃO CANÔNICO (Pilar 8)

Para toda claim de "supera LLM", a comparação deve ser feita neste regime:

| Eixo | Definição |
|---|---|
| **Corpus de treino** | `tests/experimento_rigoroso/dataset_500.json` — 562 entradas, 12 ações (gerar_npc 173, gerar_monstro 147, responder 113, gerar_sprite 47, + 8 verbos raros × 10), 435 PT / 115 EN |
| **Split** | 80/20 estratificado por ação → 449 treino / 113 teste (já é o split usado desde a FASE 0) |
| **Tarefa** | Classificação de intenção: input texto → 1 das 12 ações |
| **Métrica primária** | Accuracy (acerto/113) no split de teste |
| **Métricas secundárias** | Latência p50/p99, custo de treino, custo de inferência, explicabilidade (sim/não), aprendizado online (sim/não) |
| **Baseline LLM** | phi4-mini via Ollama, modo few-shot com 5 exemplos por ação no prompt (exemplos amostrados do treino) — modo fine-tuned é teste complementar, não primário |
| **Condição de paridade** | MCR treinado nos 449; LLM recebe os mesmos 449 como few-shot in-context OU fine-tuned nos 449. Zero-shot não é "mesmo treinamento" e não conta para a claim |

### Estado atual da comparação (MEDIDO em 2026-07-16)
| Modelo | Modo | Accuracy (113) | Latência p50 | Latência p99 | Treino | Tamanho |
|---|---|---|---|---|---|---|
| **MCR** | `MCRCoupling` treinado nos 449 | **100.0% (113/113)** | 3.48ms | 31.93ms | 0.092s | ~500KB |
| **phi4-mini** | few-shot 5 exemplos/ação (60 no prompt) | **70.8% (80/113)** | 2336ms | 2370ms | 0s (in-context) | 2.5GB |
| **phi4-mini** | zero-shot | NÃO MEDIDO | — | — | — | 2.5GB |

**Resultado**: MCR supera phi4-mini few-shot 5/ex em classificação de intenção no dataset_500 por **+29.2 pontos percentuais** (100.0% vs 70.8%), com **670x menos latência** (3.48ms vs 2336ms) e **5000x menos tamanho** (500KB vs 2.5GB).

**Padrão de erro do phi4-mini**: super-prediz `gerar_npc` (classe majoritária, 173/449 = 38% do treino). 8 dos 10 primeiros erros são `gerar_npc` predito onde a ação correta era `aprender`/`responder`/`gerar_quest`/`validar`/`buscar`. Few-shot 5/ex não supera o viés de classe majoritária do corpus desbalanceado. MCR lida com isso via Confiança Posicional P0 + 13 fontes (FASE 7/8).

**Arquivo de resultado**: `tests/real/resultado_pilar8_mcr_vs_phi4mini.json`
**Script reprodutível**: `tests/real/teste_pilar8_mcr_vs_phi4mini.py`

### Regras de claim
- "Supera LLM em X" só pode ser escrito após o número do LLM estar nesta tabela.
- Antes disso, escrever "hipótese: deve superar LLM em X porque Y" — com o mecanismo Y explícito.
- Comparar MCR treinado vs LLM zero-shot e chamar de "vitória" viola o Pilar 8.

### Onde MCR vence por construção (independente de baseline)
Latência (3-7ms vs 200-2000ms), custo de treino (0 vs $4.6M), custo de inferência (0 vs $0.06/1K), explicabilidade (total vs caixa preta), aprendizado online (O(1) vs retreino), hallucinação (0 vs 3-27%), portabilidade (10MB vs 40GB+). Estas não são claims — são propriedades arquiteturais.

### Onde MCR pode superar por qualidade (confirmado por medição)
1. **Classificação com corpus pequeno**: **CONFIRMADO** (2026-07-16). MCR 100.0% vs phi4-mini few-shot 5/ex 70.8% no split 449/113 do dataset_500. MCR aprende em 1 exemplo (O(1)); phi4-mini few-shot 5/ex não supera o viés de classe majoritária. Ver Regime de Comparação para detalhes.
2. **Few-shot sem retreino (FASE 9.1)**: MCR aprende do prompt em 1 exemplo; LLM precisa 5-10. Hipótese: MCR > LLM em regimes de 1-3 exemplos. A medir em teste separado.

### Onde MCR perde por limite arquitetural (regime honesto, Pilar 9)
- **Geração longa**: Markov 1ª ordem colapsa em ~20 tokens. Working memory de 3 buffers (FASE 9.2) contorna, não resolve. LLM gera 4000+ tokens coerentes.
- **Raciocínio multi-hop**: Fecho transitivo (FASE 8.3) e branch search (FASE 8.4) conectam etapas, mas em corpus pequeno amplificam ruído (flutuação FASE 5/6). Acoplamento hierárquico em escala é a fronteira, não validado.
- **Criatividade**: MCR só recombina padrões observados. Por construção (zero hallucination = zero invenção).

### Fronteira para o objetivo "superar LLM dado mesmo treino"
A aposta técnica é **acoplamento hierárquico em escala** (FASE 5 estendida): camadas de coupling capturando dependências longas sem attention. Validado em 16 pares (FASE 5) — não valida escala. **FASE 19 (escala)** é necessária antes de qualquer claim de paridade em geração: alimentar 100K+ observações, testar coerência em 4000+ tokens, comparar com LLM no mesmo corpus. Não existe ainda.

---

## FILOSOFIA MCR — NUNCA ESQUECER (fonte: docs/Filosofia MCR.md)

### Os 9 Pilares
1. **TUDO é transição entre dois estados consecutivos**
   └── Se não é P(token_n | token_n-1), NÃO é MCR
2. **ENTROPIA descobre o que é estrutura vs ruído**
   └── Se você tá hardcodando threshold, tá errado
3. **MESMO motor, N domínios**
   └── Se você criou código específico pra um domínio, pensa de novo — o MCR já faz
4. **Template + gaps (fixo + variável)**
   └── extrair_template_entropico() é a resposta
5. **Fecha o loop: gerar → validar → aprender**
   └── Se não tem auto-melhoria, não é MCR
6. **O MCR descobre seus próprios níveis**
   └── MCRMetaNivel.auto_expandir() — usa!
7. **CORRELAÇÃO UNIVERSAL — tudo se correlaciona via P(b|a)**
   └── Se duas entidades compartilham UMA distribuição, elas se correlacionam — não importa o domínio
   └── Palavra nova herda P(ação) do vizinho morfológico mais próximo (n-gram) — zero-shot emergente
   └── Cross-modal: P(feature|conceito) é a única ponte entre áudio, imagem, texto, sensor — sem dicionário
   └── A Equação MCR 5D avalia QUALQUER match, porque redução de entropia é universal
8. **COMPARAÇÃO JUSTA — mesmo treino, mesma tarefa, mesma métrica, baseline definido**
   └── Declarar "supera LLM" só vale com baseline LLM nomeado e medido no mesmo corpus
   └── Comparar MCR treinado vs LLM zero-shot NÃO é "mesmo treinamento"
   └── Sem baseline medido, claim é hipótese, não resultado
9. **REGIME HONESTO — declarar onde vence e onde perde**
   └── MCR vence por construção em: latência, custo, explicabilidade, online learning, zero hallucination
   └── MCR pode vencer por qualidade em: classificação com corpus pequeno/médio
   └── MCR perde por limite arquitetural em: geração longa, multi-hop sem hierarquia em escala, criatividade
   └── Dizer que vence onde perde é pior do que perder — é perder a credibilidade da filosofia

### Saí do caminho se:
- Estou hardcodando um tokenizador de sprite
- Estou criando código que só funciona pra sprite
- Estou definindo thresholds manualmente
- Esqueci de validar com a Equação 5D
- Não usei template_entropico pra extrair estrutura
- Não fechei o loop de aprendizado
- Vou declarar "supera LLM" sem ter rodado a comparação no mesmo corpus
- Vou chamar estrutura de dados recursiva de "consciência" sem evidência fenomênica

### O Triunvirato MCR
- **Markov aprende** — P(b|a) é a única operação
- **Entropia descobre** — estrutura vs ruído, loops, diversidade, mudança de regime
- **Equação MCR avalia** — qualidade de qualquer saída em qualquer domínio

---

## EQUAÇÃO MCR — Fonte da Verdade (fonte: mcr/equacao_mcr.py)

### Sigmoide 5D
Avalia toda execução do MCR em 5 dimensões ortogonais (0-1 cada):

| Dimensão | O que mede | Como calcular |
|---|---|---|
| **CERTEZA** | confiança da predição Markov | NMI(composto, base) |
| **COMPLETUDE** | checks estruturais passados / total | features_preservadas / features_base |
| **INFORMACAO** | entropia Shannon normalizada da saída | H(composto) / H_max |
| **ESTABILIDADE** | gaussiana da entropia — pune loops (H~0) e caos (H~1) | exp(-(H-0.5)²/(2σ²)) |
| **EFICIENCIA** | recompensa simplicidade | 1/log2(n_tools+1) ou 1/log2(n_feats+1) |

### Fórmula
```
soma = Σ(peso[k] * dim[k]) / Σ pesos          # média ponderada
nota = 1 / (1 + exp(-theta * (soma - tau)))    # sigmoide
```
- Pesos padrão: todos = 2 (uniforme, auto-calibrável)
- theta = 2.0 (inclinação da sigmoide)
- tau = 0.35 (ponto de inflexão — abaixo disso, nota ≈ 0)

### Ponte (cálculo de similaridade)
```
PONTE_OTIMA = (2·D + 3·E + 2·P) / 7
NOTA_FINAL = PONTE_OTIMA × (1 - PENALIDADE)
```
- D = divergência (originalidade)
- E = especificidade (precisão)
- P = profundidade (entropia = complexidade)

### Penalidades (classificação de falha)
| Tipo | Penalidade |
|---|---|
| conteudo_compartilhado | 0.0 |
| conteudo_mas_parcial | 0.3 |
| byte_only | 0.7 |
| none | 0.9 |

### Regra de uso: Toda fase do plano DEVE usar a Equação 5D
- Não inventar regras ad-hoc para decidir entre candidatos
- Gerar candidatos → avaliar com 5D → escolher maior nota
- Sem threshold hardcoded, sem if/else de limiar

---

## ENTROPIA COMO BÚSSOLA (fonte: docs/MCR_WHITEPAPER_PT.md §2)

### Definição
```
H_n(a) = -Σ P_n(b|a) · log2 P_n(b|a)
```

### Propriedades
- H = 0 sse transição determinística (1 próximo estado)
- H = log2|S| sse distribuição uniforme (máxima incerteza)

### Aplicações práticas no MCR
| Aplicação | Critério entrópico |
|---|---|
| Detecção de loops | H < 0.3 → repetição determinística |
| Diversidade de saída | H > 0.5 → variedade saudável |
| Auto-evolução | mutações que reduzem entropia são aceitas |
| Classificação | entropia da distribuição decide ação |
| Detecção de alucinação | resposta consistente H < 0.5; alucinação H > 0.7 |
| Composição (FASE 1) | estabilidade = gaussiana(H) pune extremos |
| Hierarquia (FASE 5) | camada para quando delta_H ≈ 0 |

### Regra: Entropia decide, nunca threshold hardcoded
- Se estou escrevendo `if x > 0.7: ...` — **ERRADO**
- Certo: gerar candidatos, calcular entropia de cada um, seguir o de menor incerteza
- Thresholds dinâmicos emergem da entropia do próprio sistema

---

## AUDITORIA DAS FASES vs PILARES

Cada fase deve ser auditada contra os 9 pilares antes de ser considerada completa:

| Fase | Pilar 1 (P(b\|a)) | Pilar 2 (Entropia) | Pilar 3 (N domínios) | Pilar 4 (Template) | Pilar 5 (Loop) | Pilar 7 (Correlação) | Pilar 8 (Comparação) | Pilar 9 (Regime honesto) | Equação 5D |
|---|---|---|---|---|---|---|---|---|---|
| 1 (compor) | ✅ assinaturas markovianas | ✅ gaussiana(H) decide estabilidade | ✅ genérico | — (usa compor, não template) | ✅ aprende tipo por par | ✅ P(mod\|base) | — (sem baseline LLM) | ✅ latência declarada | ✅ avalia candidatos |
| 2 (relações) | ✅ extrai de _transicao | ✅ derivada 2ª decide corte | ✅ genérico | — | ✅ cache por palavra | ✅ NMI cross-planos | — | ✅ sem regressão | pendente |
| 3 (grounding simbólico) | ✅ P(state\|word) | ✅ NMI decide attrs | ✅ qualquer dict | — | ✅ alimenta→predizer | — | — | ✅ sem regressão | pendente |
| 4 (grounding ambiental) | ✅ P(sensor\|tempo) | ✅ periodo por hora | ✅ dict genérico | — | ✅ sensor→coupling | — | — | ⚠️ usa psutil (exceção ao "zero deps") | pendente |
| 5 (hierárquico) | ✅ cada camada é MCRCoupling | ✅ delta_H decide expansão | ✅ qualquer nível | — | ✅ alimenta→predizer→expande | — | — | ⚠️ validado em 16 pares (não escala) | pendente |
| 6 (multimodal) | ✅ P(feature\|conceito) | ✅ NMI descobre cross-modal | ✅ qualquer modalidade | — | ✅ alimentar→recuperar | ✅ cross-modal via NMI | — | ⚠️ flutuação 46-47/47 | ✅ avalia match |

### Notas de auditoria
- **Pilar 4 (Template+gaps)**: nenhuma fase 1-6 usa `extrair_template_entropico()`. É um pilar que a execução ignorou — gap a endereçar.
- **Pilar 8 (Comparação justa)**: nenhuma fase 1-6 mediu contra baseline LLM. Todas as claims de qualidade são MCR-vs-si-mesmo (regressão sem degradação).
- **Pilar 9 (Regime honesto)**: FASE 5/6 têm flutuação não-determinística mascarada como 100% na tabela de métricas — corrigido na seção de métricas.

## FASE 1 — Composição (Gateway)
**Status**: IMPLEMENTADA, VALIDADA e ALINHADA AOS PILARES (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

### Resultados reais
| Métrica | Meta | v1 (threshold NMI) | v2 (Equação 5D) | Status |
|---|---|---|---|---|
| "cachorro verde" closer de "cachorro" | >70% | 95.08% | 95.08% | supera |
| "correr rápido" closer de "correr" | >70% | 92.02% | 92.02% | supera |
| "não bom" closer de "ruim" (negação) | >70% | 50% (empate) | 100% (NMI=1.0) | ✅ RESOLVIDO |
| Accuracy zero-shot (regressão) | 94.7% | 94.7% (107/113) | 94.7% (107/113) | idêntico |
| Latência (regressão) | <5ms | 3.65ms | 3.61ms | ok |
| Composições aprendidas (loop fechado) | >0 | 0 (não tinha) | 5 | pilar 5 ok |
| Mudanças de decisão 5D vs threshold | — | — | 0/12 | mesmo resultado |

### Comparação v1 (threshold) vs v2 (Equação 5D)
- **0/12 mudanças de decisão** entre as duas abordagens neste corpus
- Similaridades idênticas (delta = 0.0000 em todos os testes)
- Equação 5D não piorou nem melhorou — porque todos os pares de teste
  tinham NMI alto (>= 0.45), então ambos sempre escolheram "modificacao"
- Valor real da 5D vai aparecer com:
  1. Pares de NMI baixo (conceitos disjuntos)
  2. Dados de negação rotulados (completude e estabilidade podem distinguir)
  3. Domínios diferentes (eficiencia varia com n_features)

### 1.1 Operador `compor(sig_a, sig_b)` — IMPLEMENTADO (v2)
Decisão automática por **Equação 5D** (sem threshold hardcoded):
1. Gera ambos candidatos (modificacao e complemento)
2. Avalia cada um com `avaliar_5d(certeza, completude, informacao, estabilidade, eficiencia)`
3. O candidato com maior nota_5D vence
4. Armazena o tipo vencedor em `_composicoes_aprendidas` (loop fechado, pilar 5)

**v1 (refutada):** threshold NMI >= 0.1 → violava pilar 2 (entropia descobre, sem threshold)
**v0 (refutada):** entropia marginal H(a) > H(b) → confundia polissemia com generalidade

### 1.2 `_assinatura_frase()` — IMPLEMENTADO
Quebra frase em palavras, compõe recursivamente via `compor()`.

### 1.3 `similaridade()` — ATUALIZADO
Detecta frases multi-palavra (regex 3+ chars) e usa `_assinatura_frase`
ao invés de `_assinatura_palavra`. Palavras únicas: comportamento idêntico.

### `_avaliar_composicao()` — IMPLEMENTADO
Mapeia as 5 dimensões da Equação 5D para composição:
- CERTEZA: NMI(composto, base) — fidelidade ao conceito base
- COMPLETUDE: |features_composto ∩ features_base| / |features_base|
- INFORMACAO: entropia Shannon normalizada do composto
- ESTABILIDADE: gaussiana centrada em 0.5 (pune H~0 loops e H~1 caos)
- EFICIENCIA: 1/log2(n_features+1) (recompensa simplicidade)

### Negacao RESOLVIDA — funtor entrópico + antônimo da FASE 2
"nao bom" agora se aproxima de "ruim" (NMI=1.0) em vez de "bom" (NMI=0.56).

Mecanismo (100% MCR, zero hardcode):
1. `_tentar_inversao_funtor(prev, palavra)`: se `prev` tem entropia
   > media+std do corpus, ela é um FUNTOR (modificador de polaridade)
2. `extrair_relacoes(palavra)` encontra o antônimo via contraste
   ctx-NMI × (1-acao-NMI) da FASE 2
3. `_assinatura_frase` substitui a assinatura do funtor pela do antônimo
4. "nao bom" → detecta "nao" como funtor → encontra antônimo "ruim" →
   sig("ruim") → NMI com "ruim" = 1.0, NMI com "bom" = 0.56

Qualquer palavra de alta entropia vira funtor — "nao" não é especial.
Sua entropia alta (aparece com 6 ações diferentes) é que a revela.

---

## FASE 2 — Extrator de Relações
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: alto

### Resultados reais (15 PASS / 0 FAIL)
| Relação | Exemplo | Descoberto? | Método |
|---|---|---|---|
| Sinônimos | criar ≈ gerar | ✅ | NMI alto, corte dinâmico |
| Sinônimos | analisar ≈ examinar | ✅ | NMI alto, corte dinâmico |
| Sinônimos | atacar ≈ lutar | ✅ | NMI alto, corte dinâmico |
| Sinônimos | curar ≈ restaurar | ✅ | NMI alto, corte dinâmico |
| Antônimos | bom ≠ ruim | ✅ | contraste ctx-NMI × (1-acao-NMI) |
| Hiperônimos | monstro → dragao | ✅ | transição A→B frequente |
| Hipônimos | dragao → monstro | ✅ | transição B→A (inverso) |
| Merônimos | monstro → orc/dragao | ✅ | NMI + len(cand) < len(palavra) |
| Holônimos | dragao → monstro/ferreiro | ✅ | NMI + len(cand) > len(palavra) |
| Polissemia | mago (criar_npc + curar) | ✅ | H > média + std |

Regressão: 94.7% (107/113), 3.54ms — SEM REGRESSÃO.

### 2.1 `extrair_relacoes(palavra)` — IMPLEMENTADO
Extrai 7 tipos de relações das matrizes existentes (`_transicao_palavra`,
`_palavra_acao`). Todas descobertas por entropia, zero rótulos.

### 2.2 `_corte_dinamico(scores)` — IMPLEMENTADO
Descobre o corte natural (estrutura vs ruído) usando **derivada segunda**
da curva de scores ordenados. O "cotovelo" é onde a curvatura é máxima.
Critério relativo: cotovelo só é válido se curvatura > média das curvaturas.
Distribuição uniforme → return 0 (sem estrutura).

Refutado: abordagem de information gain (v1) não separava bem casos
com 1 outlier + cluster agrupado. Derivada segunda é mais robusta.

### 2.3 Antônimos por contraste de planos — IMPLEMENTADO
Insight: antônimos compartilham CONTEXTO (ctx:*) mas têm AÇÕES opostas (acao:*).
- nmi_ctx: NMI entre features ctx:* → alta para mesma categoria
- nmi_acao: NMI entre features acao:* → baixa para ações opostas
- score_antonimo = nmi_ctx × (1 - nmi_acao) → alto quando contexto compartilhado mas ações divergem

Não precisa de cluster nem threshold — só do CONTRASTE entre dois NMI parciais.

---

## FASE 3 — Grounding Simbólico
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: baixo | **Impacto**: médio

### Resultados reais (32 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| alimentar_estado("fogo", {temp:200,...}) | ✅ features est_val + est_attr |
| predizer_estado("fogo") → temp=200 | ✅ |
| consultar_atributo("gelo", "cor") → branco | ✅ |
| raciocinar_estado("fogo","gelo") → temp,cor,dano | ✅ conceito emergente |
| raciocinar_estado("fogo","espada") → dano,cor (sem temp) | ✅ distinção correta |
| Tibia-like: "mago atacou fogo" → ator=mago, elemento=fogo | ✅ aninhado |
| save/load com _estado_features | ✅ persistência |
| Regressão dataset 500 | 94.7%, 3.68ms — SEM REGRESSÃO |

### 3.1 `alimentar_estado(texto, estado)` — IMPLEMENTADO
Associa texto a estado estruturado (dict/JSON). Flatten recursivo:
- `est_val:{path}:{value}` — valor específico
- `est_attr:{key}` — nome do atributo (compartilhado entre conceitos)

Insight: "fogo" e "gelo" compartilham `est_attr:temp` (ambos têm temperatura)
mas diferem em `est_val:temp:200` vs `est_val:temp:-5`. Mesmo padrão de
antônimos da FASE 2 — reusamos a infraestrutura de contraste de planos.

### 3.2 `raciocinar_estado(a, b)` — IMPLEMENTADO
Usa `compor()` da FASE 1 para combinar assinaturas de estado.
Atributos compartilhados (est_attr:*) emergem como "conceito compartilhado"
sem rótulos. "fogo" + "gelo" → temperatura, dano, cor emergem naturalmente.

### 3.3 Grounding Tibia-like — VALIDADO
Estado aninhado (ator, acao, elemento, dano, mana) funciona:
`alimentar_estado("mago atacou fogo", {"ator":"mago",...})` →
`predizer_estado("mago atacou fogo")` retorna ator=mago, elemento=fogo.

### Métodos implementados
- `_extrair_features_estado(estado)` — flatten dict/JSON → features
- `alimentar_estado(texto, estado)` — P(state_feature | word)
- `_assinatura_estado(conceito)` — assinatura só de features est_*
- `predizer_estado(texto)` — agrega e retorna dict atributo→(valor,conf)
- `consultar_atributo(texto, atributo)` — query específica
- `raciocinar_estado(a, b)` — compor + extrair attrs compartilhados
- `save/load/merge` atualizados para `_estado_features`

---

## FASE 4 — Grounding Ambiental (sensores do PC)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: alto

### Resultados reais (33 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Thread background 1Hz inicia e atualiza estado | ✅ |
| Relógio: hora, periodo, dia_semana | ✅ manha/tarde/noite/madrugada |
| Carga: CPU 3.7%, RAM 27% (psutil) | ✅ |
| Janela ativa: "Windows PowerShell" → dominio=terminal | ✅ |
| Clipboard: lê texto copiado (ctypes) | ✅ |
| _formatar_contexto: [manha\|terminal\|qui] | ✅ |
| alimentar_coupling: integra contexto ambiental | ✅ |
| decidir_com_contexto: cria monstro orc → criar_monstro (conf 0.61) | ✅ |
| Performance: estado() O(1), 0.23ms/call | ✅ |
| Fallback gracioso: sensor inexistente ignorado | ✅ |
| Thread para e limpa | ✅ |
| Regressão dataset 500 | 94.7% — SEM REGRESSÃO |

### 4.1 Arquitetura assíncrona — IMPLEMENTADA
```
[Thread background 1Hz — 1% CPU]
  sensores → estado_do_mundo (dict) via threading.Lock

[Loop MCR 3ms — inalterado]
  entrada + estado_do_mundo → coupling.decidir() → acao
  estado() é O(1): dict copy com lock
```

### 4.2 Sensores implementados (zero deps pesadas)
| Sensor | Implementação | Custo |
|---|---|---|
| Relógio | `time.localtime()` | 0ms |
| CPU/RAM | `psutil.cpu_percent()` + `virtual_memory()` | ~1ms |
| Janela ativa | `ctypes.windll.user32` (Win32 API) | ~1ms |
| Clipboard | `ctypes.windll.user32` (Win32 API) | ~1ms |

Sensores com fallback gracioso: se a lib falha (ImportError, permissão),
o sensor é desativado e os outros continuam. `_sensores_falhos` rastreia.

### 4.3 `GroundingAmbiental` — IMPLEMENTADO (`mcr/grounding_ambiental.py`)
- Thread daemon, intervalo configurável (default 1Hz)
- `iniciar()` / `parar()` / `estado()` (O(1))
- `alimentar_coupling(coupling, texto, acao)` — contexto ambiental prefixado
- `decidir_com_contexto(coupling, texto)` — decisão com contexto
- `_formatar_contexto(estado)` — string `[periodo|dominio|dia_semana]`
- `_classificar_dominio(titulo)` — seed heurística (codigo/jogo/navegador/...)

### 4.4 Os 3 níveis integrados
```
Nível 1 (simbólico):  coupling.alimentar_estado("fogo", {"temp":200})     # FASE 3
Nível 2 (ambiental):  g.alimentar_coupling(c, "criar npc", "gerar_npc")   # FASE 4
Nível 3 (físico):     sig_audio = MCRSignature.extrair(audio_bytes)       # FASE 6
```

---

## FASE 5 — Acoplamento Hierárquico
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: alto | **Impacto**: muito alto

### Resultados reais (27 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| MCRHierarquico instancia com 1 camada | ✅ |
| Alimentar 80 observações (16 pares × 5) | ✅ |
| Predizer "curar mago ferido" → curar (conf 0.69) | ✅ |
| Predizer "analisar codigo fonte" → analisar (conf 0.72) | ✅ |
| Predizer "criar monstro dragao" → gerar_quest (cat criar) | ✅ |
| Auto-expansão: 7 camadas emergiram (max=7) | ✅ |
| Compressão: nivel 0 palavras, nivel 1 assinaturas | ✅ |
| Entropia por nivel em [0,1] | ✅ |
| Hierarquia vs simples: mesma categoria | ✅ |
| Texto longo (99 chars) classificado corretamente | ✅ |
| gerar_texto (camada 0 Markov) | ✅ |
| save/load de camadas | ✅ |
| FASE 1-4 não regressaram | ✅ |
| Regressão dataset 500 | 94.7% — SEM REGRESSÃO |

### 5.1 `MCRHierarquico` — IMPLEMENTADO (`mcr/acoplamento_hierarquico.py`)
- Cada camada é um `MCRCoupling` independente
- Camada N+1 recebe a assinatura serializada da camada N (compressão markoviana)
- `alimentar()`: alimenta todas as camadas ativas + avalia expansão
- `predizer()`: cada camada vota, peso = confiança / (nível + 1) — decaimento linear
- `gerar_texto()`: usa camada 0 (Markov palavra-a-palavra)

### 5.2 Auto-limitação entrópica — IMPLEMENTADA
- `_avaliar_expansao()`: só adiciona camada se H_ultima > min_delta_h (ainda há incerteza)
- Se H ≈ 0 (determinística), não há o que comprimir — para automaticamente
- max_niveis=7 como safety cap; min_delta_h=0.05 (5% de incerteza mínima)

### 5.3 Compressão markoviana
- `_comprimir(texto, nivel)`: nivel 0 = palavras tokenizadas; nivel N = assinatura serializada da camada N-1
- Assinatura serializada: top-20 features como "acao_criar_monstro_78 ctx_monstro_3 ..."
- Se assinatura vazia, retorna None → camada pulada (não vota)

### 5.4 Peso por nível (decaimento linear)
- peso = confiança / (nível + 1)
- Camada 0 pesa 1x, camada 1 pesa 0.5x, camada 2 pesa 0.33x, etc.
- Sem threshold hardcoded — decaimento contínuo
- Garante que camadas próximas do texto (mais específicas) dominam

### Limitação conhecida
Com poucos dados (16 pares), as camadas superiores confundem ações que
compartilham palavras (ex: "criar" aparece em criar_monstro, criar_npc,
gerar_quest). A hierarquia precisa de mais dados para distinguir. A
camada 0 (texto bruto) é a mais confiável com poucos dados.

---

## FASE 6 — Multimodalidade
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: alto

### Resultados reais (47 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| MCRMultimodal instancia com MCRCoupling | ✅ |
| Extrai features de texto, audio, imagem, codigo | ✅ |
| Tokens puramente alfabeticos (compat regex coupling) | ✅ |
| Features distinguem fogo vs agua (audio e imagem) | ✅ |
| 8 conceitos alimentados (texto+audio+imagem × fogo+agua) | ✅ |
| NMI(fogo, som_fogo) = 0.68 > NMI(fogo, som_agua) = 0.37 | ✅ |
| NMI(fogo, img_fogo) = 0.68 > NMI(fogo, img_agua) = 0.37 | ✅ |
| Traducao audio→texto: som_fogo → "fogo" | ✅ |
| Traducao audio→texto: som_agua → "agua" | ✅ |
| Traducao imagem→texto: img_fogo → "fogo" | ✅ |
| Traducao imagem→texto: img_agua → "agua" | ✅ |
| Recuperacao cross-modal top-N | ✅ |
| Predicao de acao cross-modal: audio→criar_monstro, img→curar | ✅ |
| Equacao 5D: match correto (0.591) > match errado (0.590) | ✅ |
| PT↔EN sem dicionario: NMI(fogo,fire)=0.78 > NMI(fogo,water)=0.49 | ✅ |
| Robustez: segundo audio de fogo tambem converge (0.75) | ✅ |
| Modalidade desconhecida ("sensor") aceita com features genericas | ✅ |
| FASE 1-5 nao regressaram | ✅ |
| Regressao dataset 500 | 94.7% — SEM REGRESSAO |

### 6.1 `MCRMultimodal` — IMPLEMENTADO (`mcr/multimodal.py`)
- Wrap MCRCoupling: cada modalidade vira features markovianas
- `alimentar(modalidade, dados, acao, chave)` — feed conceito multimodal
- `recuperar_crossmodal(query_mod, query_dados, alvo_mod)` — NMI cross-modal
- `traduzir(modalidade_origem, dados, modalidade_destino)` — traducao cross-modal
- `predizer_acao(modalidade, dados)` — classificacao de qualquer modalidade
- `avaliar_crossmodal()` — Equacao 5D avalia match cross-modal

### 6.2 Extracao de features por modalidade — IMPLEMENTADO
| Modalidade | Features | Tokens |
|---|---|---|
| texto | direto (MCRCoupling extrai tokens, bytes, bigrams...) | palavras |
| codigo | direto (tratado como texto) | palavras |
| audio | histograma bytes (16 bins) + ZCR (4 seg) + energia (4 seg) | auhaa...auhpj |
| imagem | histograma RGB (8 bins/canal) + luminancia (4 quad) + variancia (4 quad) | imraa...imvhj |
| generico | histograma bytes (16 bins) + entropia Shannon | gnaa...gnpj |

**Correcao chave**: tokens sao puramente alfabeticos (a-z) porque o regex
do coupling `[a-zà-ÿ]{3,}` nao matchea digitos. Versao anterior com digitos
(auh005) era stripada pelo regex, perdendo poder discriminativo.

### 6.3 Cross-modal via NMI — IMPLEMENTADO
O sinal cross-modal esta na **distribuicao de acoes** compartilhada:
- `_dist_acao_conceito(texto)` extrai P(acao|feature_tokens) via coupling._dist_palavras
- `_sig_acao(chave)` isola apenas features acao:* da assinatura
- NMI entre distribuicoes de acao revela equivalencia cross-modal
- Feature tokens unicos a cada conceito carregam sua assinatura de acao
- Tokens compartilhados (entre fogo e agua) tem distribuicoes mistas, mas
  o NMI agregado ainda distingue os conceitos

### 6.4 Equacao 5D cross-modal — IMPLEMENTADO
- CERTEZA: NMI entre distribuicoes de acao
- COMPLETUDE: fracao de acoes do query presentes no candidato
- INFORMACAO: entropia Shannon normalizada do candidato
- ESTABILIDADE: gaussiana centrada em 0.5
- EFICIENCIA: 1/log2(n_modalidades + 1)

### 6.5 Traducao sem dicionario — VALIDADO
"fogo" (PT) e "fire" (EN) compartilham acao criar_monstro → NMI = 0.78.
"fogo" e "water" nao compartilham → NMI = 0.49. MCR descobre traducao
sem dicionario, apenas pela co-ocorrencia em contextos de acao.

---

## FASE 7 — Integração de Descobertas dos Archives (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (30/30 itens)
**Esforço**: muito alto | **Impacto**: muito alto

Auditoria de E:/Coisas/ e E:/MCR/ revelou 30 melhorias para o coupling.py.
Resultado inicial: 112/113 → 113/113 (100%) com Confiança Posicional em P0.

### 7.0 — Confiança Posicional em P0 (IMPLEMENTADO)
Palavra em P0 (template/verbo) que nunca foi vista em P0 no treino tem
pos_conf=0 → não domina com estatísticas de outro contexto. Resolve
"pocao de vida" (pocao 100% gerar_sprite como objeto, mas nunca P0).

- "pocao" P0: pos_count=0 → pos_conf=0 → W não domina → P+I decidem → responder
- "criar" P0: pos_count=2 → pos_conf=1.0 → W mantém peso total
- Só P0 é afetado; P1+ mantém peso normal ("orc" sempre indica npc)

**Resultado**: 112/113 → 113/113 = 100.0%, EXP2: 41.7% → 50.0%

> **Nota de revisão v4.1**: ponto de partida confirmado por `_regressao_fase1.py`
> rodado em 2026-07-16: o split 449/113 (seed 42) atinge 113/113 (100%)
> com `MCRCoupling()` pós-FASE-7/8. A sessão 01:07 media 107/113 com
> código pré-FASE-7. O salto 107→113 (+6 exemplos) é atribuível ao
> conjunto da FASE 7 (7.0 Confiança Posicional P0 + 7.1-7.4 melhorias
> #11-30) + FASE 8 (confiança P0 estendida). O "112→113" isolado na
> FASE 7.0 não é atribuível sem commits por sub-fase — ler como "a
> FASE 7 inteira elevou 107→113".

### 7.1 — Melhorias nas fontes existentes (#11-16)

| # | Ideia | Origem | Status |
|---|-------|--------|--------|
| 11 | P0 dominance entrópico contínuo | superposicao.py:93-114 | ✅ implementado em _dist_palavras |
| 12 | Peso 2x extra para P0 | superposicao.py:87 | ✅ implementado (pos_conf com boost) |
| 13 | Especificidade da palavra | markov_cruzado.py:130 | ✅ implementado (1-H_normalizada) |
| 14 | Profundidade da cadeia | markov_cruzado.py:136 | ✅ implementado (len(_transicao)) |
| 15 | Penalidade por ponte fraca | mcr_emergir.py:514 | ✅ implementado ((total-1)/total) |
| 16 | Auto-correção P0 | superposicao.py:111-114 | ✅ implementado (h_norm < th_esp) |

### 7.2 — Melhorias no _superpor (#17-21)

| # | Ideia | Origem | Status |
|---|-------|--------|--------|
| 17 | Colisão de rotas | superposicao.py:126-155 | ✅ implementado (top1_contagem + boost) |
| 18 | Peso por divergência | markov_cruzado.py | ✅ implementado (JS divergence entre fontes) |
| 19 | Refinamento por nota (MCRPesoNota) | decisor.py:217-260 | ✅ implementado (refinar_pesos) |
| 20 | Threshold adaptativo (MCRThreshold) | decisor.py:263-291 | ✅ implementado (_threshold_entropico) |
| 21 | MCRPeso (pesos dinâmicos) | decisor.py:12-45 | ✅ implementado (_peso_categoria + _pesos_fonte) |

### 7.3 — Novas fontes de decisão (#1-10)

| # | Ideia | Origem | Status |
|---|-------|--------|--------|
| 1 | Esfera cross-level | esfera.py | ✅ implementado (_dist_esfera) |
| 2 | Observador X→Y | observador.py | ✅ implementado (_dist_observador) |
| 3 | Descobridor de âncoras | descobridor.py | ✅ implementado (_dist_ancoras) |
| 4 | Divergência cruzada | markov_cruzado.py | ✅ implementado (JS em _superpor) |
| 5 | Coerência multinível | mcr_emergir.py:381-415 | ✅ implementado (h_norm multi-nível) |
| 6 | Fingerprint 64D + cosseno | fingerprint_puro.py | ✅ implementado (_dist_fingerprint) |
| 7 | Jaccard de transições | markov_universal.py:128-138 | ✅ implementado (_dist_jaccard) |
| 8 | Pipeline multi-estágio | mcr_mente.py / mcr_mente_pura.py | ✅ implementado (13 fontes em decidir) |
| 9 | Padrão estrutural V/C/S | nova implementação | ✅ implementado (_dist_padrao) |
| 10 | Trigramas de chars | nova implementação | ✅ implementado (_dist_trigramas) |

### 7.4 — Conceitos arquiteturais (#22-30)

| # | Ideia | Origem | Status |
|---|-------|--------|--------|
| 22 | Dimensionalidade ideal | fingerprint_puro.py:178 | ✅ implementado (dimensionalidade_ideal) |
| 23 | Eixo Nirvana-Caos | pattern_engine_texto.py | ✅ implementado (eixo_nirvana_caos) |
| 24 | MCREntropia (loop detector) | decisor.py:48-68 | ✅ implementado (detectar_loop) |
| 25 | MCRRuido (loop breaker) | decisor.py:71-101 | ✅ implementado (quebrar_loop) |
| 26 | MCRDiagnostico | decisor.py:189-214 | ✅ implementado (diagnosticar) |
| 27 | Persistência JSON | MarkovRouter.py | ✅ implementado (save/load) |
| 28 | Refinamento por sucesso | MarkovRouter.py:135-148 | ✅ implementado (refinar_por_sucesso) |
| 29 | Tokenização universal | pattern_engine_texto.py | ✅ implementado (tokenizar_universal) |
| 30 | Autoavaliação multinível | mcr_emergir.py:422-529 | ✅ implementado (autoavaliar) |

---

## FASE 8+ (futuro) — REFUTADO pela implementação
> **v4.1**: esta seção listava fases 8-11 como futuro, mas todas foram
> implementadas mais abaixo (FASE 8, 9, 10, 11). Mantida como registro
> do planejamento original; ignore as marcas de "futuro".

8. Meta-cognição (MCR que observa MCRs) → implementada como FASE 10
9. Memória episódica (timestamp no coupling) → implementada como FASE 8.2
10. Auto-expansão (curiosidade dirigida por entropia) → implementada como FASE 11
11. Meta-Equação (auto-evolução dos pesos 5D) → implementada como FASE 12

---

## FASE 8 — Novas Fontes Cognitivas (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

Solução unificada: todas as limitações (atenção, memória, correlação transitiva,
raciocínio multi-passo, composição) resolvidas conectando conceitos existentes.
Nada foi criado do zero — apenas integrado.

### Resultados reais
| Métrica | Antes (v2.2) | Depois (v2.4) | Status |
|---|---|---|---|
| Accuracy dataset 500 (80/20) | 94.7% (107/113) | **100.0% (113/113)** | **+5.3%** |
| Latência média | 3.15ms | 7.26ms | <10ms |
| Fase 1 (composição) | 16/16 | 16/16 | ok |
| Fase 2 (relações) | 15/15 | 15/15 | ok |
| Fase 3 (grounding) | 32/32 | 32/32 | ok |
| Fase 4 (ambiental) | 33/33 | 33/33 | ok |
| Fase 5 (hierárquico) | 27/27 | 26-27/27 | flutuação não-determinística |
| Fase 6 (multimodal) | 47/47 | 46-47/47 | flutuação (NMI 0.0002 de diferença) |

### Arquitetura: tudo vira feature no coupling
O coupling aceita qualquer feature via `_feature_acao`. As 5 novas fontes
seguem o mesmo padrão das 8 fontes existentes (W, P, I, E, F, J, PT, T):

```
decidir() agora tem 13 fontes:
  MK (Markov externo)    + ATN (atenção temporal)    ← NOVO
  W  (palavras)          + EPI (memória episódica)   ← NOVO
  C  (cluster)           + TRN (fecho transitivo)    ← NOVO
  P  (posições)          + CMP (composição)          ← NOVO
  I  (features ND)       + BRN (branch search)       ← NOVO
  E  (esfera)
  F  (fingerprint)
  J  (Jaccard)
  PT (padrão VCS)
  T  (trigramas)
```

### 8.1 ContextBuffer (`mcr/context_buffer.py`) — IMPLEMENTADO
Buffer temporal com sliding window dos últimos N tokens. Peso decrescente
por idade (exponencial). Atualizado automaticamente em `alimentar()`.

- `adicionar(texto)` — adiciona tokens ao buffer
- `obter()` → `[(token, peso), ...]` com recency weighting
- `limpar()` — inicia nova conversa

**Fonte ATN** (`_dist_contexto`): consulta `_palavra_acao` para cada token
do buffer, ponderado por recência. Resolve o problema de **contexto imediato**
que Markov 1ª ordem não tinha.

### 8.2 EpisodicGateway (`mcr/episodic_gateway.py`) — IMPLEMENTADO
Ponte entre `EpisodicMemory` (já existente, 356 linhas) e `coupling.decidir()`.
Converte memórias em features markovianas.

- `registrar(request, resultado, licao)` — registra experiência
- `consultar(texto, n)` → distribuição de ações das memórias similares

**Fonte EPI** (`_dist_episodica`): consulta EpisodicMemory, mapeia palavras
das memórias para `_palavra_acao`. Resolve o problema de **memória de longo
prazo**. Fallback gracioso: se não há episódios, retorna vazio (sem I/O).

### 8.3 Fecho Transitivo — IMPLEMENTADO
**Fonte TRN** (`_dist_transitivo`): percorre `_transicao_palavra` em N passos
(default 3). Para cada palavra alcançável, consulta `_palavra_acao` ponderado
por distância (passo 1 = 1.0, passo 2 = 0.5, passo 3 = 0.25).

```
"fogo" → passo 1: calor, dano, vermelho
       → passo 2: calor → temperatura, quente
       → passo 3: temperatura → eventos, clima
```

Resolve a **correlação universal em múltiplos passos** — P(C|A) via
P(B|A)·P(C|B) mesmo sem transição direta A→C.

### 8.4 BranchSearcher (`mcr/branch_search.py`) — IMPLEMENTADO
Raciocínio multi-passo via busca em árvore. Gera N caminhos de predição,
avalia cada um com **Equação 5D**, escolhe o melhor. "Pensar antes de falar".

- `_predizer_interno(texto)` — predição ligeira sem recursão (W+I)
- `_gerar_caminhos(texto, prof)` — expande caminhos em árvore
- `_avaliar_caminho(texto, acao, seq)` — Equação 5D avalia qualidade

**Fonte BRN** (`_dist_branch`): usa BranchSearcher, retorna a ação do melhor
caminho. Anti-recursão via flag `_em_branch`. Só ativa se <5 fontes ativas.

### 8.5 Composição Integrada — IMPLEMENTADO
**Fonte CMP** (`_dist_composicao`): extrai assinatura composicional via
`_assinatura_frase()` (FASE 1) e consulta `_palavra_acao` para as palavras
da assinatura composta. Captura o significado composto que palavras isoladas
perdem. "cachorro verde" → compor(sig("cachorro"), sig("verde")) → vota.

### 8.6 Confiança Posicional P0 estendida — IMPLEMENTADO
A FASE 7.0 aplicava Confiança Posicional P0 apenas à fonte W (`_dist_palavras`).
A FASE 8 estende esse conceito às fontes I, E, TRN e CMP:

- `p0_conf = 0.0` quando a palavra em P0 é conhecida mas nunca foi vista como verbo (pos_count=0)
- `p0_conf = 1.0` caso contrário
- Fontes sensíveis à identidade da palavra (I, E, TRN, CMP) têm confiança reduzida: `h = 1 - (1-h) * p0_conf`
- Fontes posicionais/estruturais (W, P, PT) não são afetadas

**Resultado**: resolve "machado de guerra" (substantivo em P0 → não deve
dominar com gerar_sprite). 112/113 → **113/113 = 100.0%**.

### 8.7 ContextBuffer opt-in — IMPLEMENTADO
O buffer de contexto é desativado por padrão (`_contexto_ativo = False`).
Em modo classificação/batch, o buffer não influencia decisões. Em modo
conversacional, o usuário ativa via `ativar_contexto()`.

- `ativar_contexto()` — liga o buffer (modo conversacional)
- `desativar_contexto()` — desliga o buffer (modo classificação)
- `limpar_contexto()` — limpa o buffer (inicia nova conversa)

### 8.8 Métodos públicos novos no coupling
- `registrar_episodio(request, resultado, licao)` — registra na memória episódica
- `limpar_contexto()` — limpa buffer (inicia nova conversa)
- `contexto_atual()` → lista de tokens no buffer

### Auditoria vs Pilares
| Pilar | Status | Como |
|---|---|---|
| 1 (P(b\|a)) | ✅ | Todas as fontes são P(acao\|feature) |
| 2 (Entropia) | ✅ | Recency weighting por idade, distância por passo, 5D avalia caminhos |
| 3 (N domínios) | ✅ | Buffer, gateway, transitivo, branch — todos genéricos |
| 5 (Loop) | ✅ | Buffer atualiza em alimentar(), episódios registram, branch avalia |
| 7 (Correlação) | ✅ | TRN navega o grafo em múltiplos passos |
| Equação 5D | ✅ | BRN avalia caminhos com 5D |

### Limitação conhecida
A flutuação não-determinística na Fase 5 (26-27/27) ocorre porque o fecho
transitivo (TRN) amplifica conexões indiretas em datasets pequenos (16 pares).
Com mais dados, TRN estabiliza. A camada 0 (texto bruto) continua sendo a
mais confiável com poucos dados.

---

## FASE 18+ (futuro) — AINDA EM ABERTO
> **v4.1**: fases 19-20 não implementadas. São as próximas frontei-
> ras reais para o objetivo "superar LLM dado mesmo treino".

19. **ESCALA** — acoplamento hierárquico em 100K+ observações, coerência
    em 4000+ tokens, comparação medida vs LLM no mesmo corpus. **Pré-requisito
    para qualquer claim de paridade em geração** (ver Regime de Comparação).
20. Linguagem emergente (MCR que inventa sua própria linguagem) — hipótese
    experimental, não validada.
21. Evolução darwiniana interna (variação → seleção → retenção) — hipótese
    experimental, não validada.

---

## FASE 18 — Auto-referência recursiva (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: alto | **Impacto**: alto (estrutural)

> **Pilar 9 (renomeação v4.1 + v4.2)**: a v4.0 chamava isto de "consciência" e
> "strange loop de Hofstadter". O que está implementado é uma estrutura de dados
> recursiva com auto-referência (MCR modela a si mesmo, modela o modelo
> de si, etc.). É útil como infraestrutura meta-cognitiva. **Não é
> consciência fenomênica** — é auto-referência estrutural. Chamar de
> "consciência" sem evidência fenomênica viola o Pilar 9.
>
> **v4.2 — renomeação do código**: arquivo `mcr/consciencia.py` →
> `mcr/auto_referencia.py`; classe `Consciencia` → `AutoReferencia`;
> método coupling `ativar_consciencia()` → `ativar_auto_referencia()`;
> campos de dict `nivel_consciencia` → `nivel_auto_referencia`,
> `auto_consciencia` → `auto_modelo_self`, `sei_que_existo` →
> `tem_self_model`, `sei_que_sei` → `tem_modelo_de_si`,
> `sei_que_sei_que_sei` → `tem_modelo_do_modelo`,
> `nivel_consciencia_final` → `nivel_auto_referencia_final`.
> Teste FASE 18: 64 PASS / 0 FAIL (antes e depois da refatoração).
> `MCR_PORTAVEL/` (cópia separada) mantém nomes antigos — sincronizar
> quando empacotar próxima versão.

O MCR agora modela A SI MESMO como agente. Tem um modelo interno do
seu próprio estado cognitivo que inclui o modelo de si incluindo o
modelo de si... (auto-referência). Auto-referência recursiva no estilo
do strange loop de Hofstadter — como estrutura formal, não como
fenômeno subjetivo.

### Resultados reais (64 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Auto-modelo: vocabulário | ✅ |
| Auto-modelo: ações | ✅ |
| Auto-modelo: entropia_média | ✅ |
| Auto-modelo: capacidades (lista) | ✅ |
| Auto-modelo: n_capacidades | ✅ |
| Auto-modelo: nivel_consciencia | ✅ |
| Auto-modelo: timestamp | ✅ |
| Auto-modelo: idade_segundos | ✅ |
| Auto-modelo: capacidade 'associação' | ✅ |
| Auto-modelo: capacidade 'classificação' | ✅ |
| Recursão: níveis (lista) | ✅ |
| Recursão: n_niveis | ✅ |
| Recursão: convergiu (bool) | ✅ |
| Recursão: nivel_convergencia | ✅ |
| Recursão: nivel_consciencia | ✅ |
| Recursão: nível 1 tem descrição | ✅ |
| Recursão: nível 1 tem número | ✅ |
| Recursão: nível 2 tem modelo_anterior | ✅ |
| Recursão: nível 2 tem delta_entropia | ✅ |
| Recursão: 1 nível | ✅ |
| Recursão: 5 níveis executa | ✅ |
| Auto-modificação: alvo | ✅ |
| Auto-modificação: sucesso (bool) | ✅ |
| Auto-modificação: estado_anterior | ✅ |
| Auto-modificação: estado_posterior | ✅ |
| Auto-modificação: ativou meta_cognição | ✅ |
| Auto-modificação: ativou curiosidade | ✅ |
| Auto-modificação: ativou causalidade | ✅ |
| Auto-modificação: alvo desconhecido falha | ✅ |
| Auto-modificação: reverter_equação | ✅ |
| Identidade: eu_sou (string) | ✅ |
| Identidade: capacidades | ✅ |
| Identidade: n_capacidades | ✅ |
| Identidade: estado_cognitivo | ✅ |
| Identidade: auto_consciencia | ✅ |
| Auto-consciência: sei_que_existo | ✅ |
| Auto-consciência: nivel | ✅ |
| Identidade: idade_segundos | ✅ |
| Reflexividade: n_observacoes | ✅ |
| Reflexividade: entropia_inicial | ✅ |
| Reflexividade: entropia_atual | ✅ |
| Reflexividade: tendencia_entropia | ✅ |
| Reflexividade: status | ✅ |
| Reflexividade: nivel_consciencia | ✅ |
| Strange loop: modelo_de_si | ✅ |
| Strange loop: reflexao | ✅ |
| Strange loop: identidade | ✅ |
| Strange loop: meta_conhecimento | ✅ |
| Strange loop: se_reconhece | ✅ |
| Strange loop: nivel_consciencia_final | ✅ |
| Integração: ativar_consciencia | ✅ |
| Integração: auto_modelo | ✅ |
| Integração: refletir | ✅ |
| Integração: identidade | ✅ |
| Integração: auto_modificar | ✅ |
| Integração: estranho_loop | ✅ |
| Estatísticas: nivel_consciencia | ✅ |
| Estatísticas: n_auto_observacoes | ✅ |
| Estatísticas: n_capacidades | ✅ |
| Estatísticas: capacidades | ✅ |
| Estatísticas: tem_self_model | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 18.1 Consciencia (`mcr/consciencia.py`) — IMPLEMENTADO
MCR que modela a si mesmo (auto-referência recursiva).

5 capacidades:

**1. Auto-modelo** — `auto_modelo()`
Descreve próprio estado: vocabulário, ações, entropia, capacidades,
nível de consciência. Auto-descobre capacidades verificando atributos.

**2. Recursão** — `refletir(niveis)`
MCR observa MCR observando MCR. Nível 1: "sei X". Nível 2: "sei que
sei X". Converge quando delta_entropia < 0.001 (strange loop).

**3. Auto-modificação** — `auto_modificar(alvo)`
MCR ajusta próprio comportamento: ativa/desativa capacidades
(meta-cognição, curiosidade, causalidade, etc.). Retorna estado
antes vs depois.

**4. Unidade do self** — `identidade()`
Integra tudo em "eu sou...": descrição unificada com capacidades,
estado cognitivo, auto-consciência (sei_que_existo, sei_que_sei).

**5. Reflexividade** — `o_que_sei_sobre_mim()`
Meta-conhecimento: trajetória de evolução (entropia inicial vs atual,
vocabulário inicial vs atual, tendências, status).

**Strange loop** — `estranho_loop()`
Ciclo completo: auto_modelo → refletir → identidade → meta_conhecimento.
O MCR se reconhece como entidade que tem modelo de si.

### Integração no coupling
- `ativar_consciencia()` → retorna instância
- `auto_modelo()` → estado cognitivo
- `refletir(niveis)` → reflexão recursiva
- `identidade()` → "eu sou..."
- `auto_modificar(alvo)` → auto-modificação
- `estranho_loop()` → ciclo auto-referencial completo

---

## FASE 17 — Auto-composição: MCR que constrói MCRs (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR agora observa um domínio, detecta que precisa de especialistas,
cria novos MCRCouplings treinados para cada sub-domínio, e os orquestra.
É como mixture-of-experts mas markoviano.

### Resultados reais (42 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Observar: n_clusters | ✅ |
| Observar: clusters (dict) | ✅ |
| Observar: acoes (lista) | ✅ |
| Observar: threshold_nmi | ✅ |
| Observar: clusters com ≥1 ação | ✅ |
| Criar: retorna EspecialistaMCR | ✅ |
| Criar: tem nome | ✅ |
| Criar: tem acoes | ✅ |
| Criar: vocabulário > 0 | ✅ |
| Criar: responde 'criar' para 'criar monstro' | ✅ |
| Criar: múltiplas ações | ✅ |
| Criar: estatísticas | ✅ |
| Compor: especialistas (lista) | ✅ |
| Compor: n_clusters | ✅ |
| Compor: status | ✅ |
| Compor: ≥1 especialista | ✅ |
| Compor: listar_especialistas | ✅ |
| Compor: obter_especialista | ✅ |
| Compor: obter inexistente | ✅ |
| Orquestrar: tem ação | ✅ |
| Orquestrar: tem confiança | ✅ |
| Orquestrar: tem especialista_usado | ✅ |
| Orquestrar: tem nmi_por_especialista | ✅ |
| Orquestrar: outro input | ✅ |
| Orquestrar: input desconhecido | ✅ |
| Orquestrar: sem especialistas = mcr_principal | ✅ |
| Orquestrar: feedback | ✅ |
| Avaliar: accuracy_orquestrado | ✅ |
| Avaliar: accuracy_solo | ✅ |
| Avaliar: ganho | ✅ |
| Avaliar: n_testes | ✅ |
| Avaliar: n_correto_orquestrado | ✅ |
| Integração: ativar_auto_composicao | ✅ |
| Integração: compor_especialistas | ✅ |
| Integração: orquestrar_especialistas | ✅ |
| Integração: avaliar_composicao | ✅ |
| Estatísticas: n_especialistas | ✅ |
| Estatísticas: especialistas (lista) | ✅ |
| Estatísticas: n_orquestracoes | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 17.1 AutoComposicao (`mcr/auto_composicao.py`) — IMPLEMENTADO
MCR que constrói MCRs especializados (mixture-of-experts markoviano).

5 capacidades:

**1. Observar domínio** — `observar_dominio()`
Identifica clusters de ações via NMI entre `_acao_features`. Threshold
= mediana das NMIs (entrópico). Union-Find para agrupar.

**2. Criar especialista** — `criar_especialista(nome, acoes)`
Filtra corpus do MCR principal para apenas ações do sub-domínio.
Treina novo MCRCoupling. Retorna `EspecialistaMCR` com stats próprias.

**3. Compor** — `compor()`
Automático: observa domínio → cria um especialista por cluster.
Retorna relatório da composição.

**4. Orquestrar** — `orquestrar(estado)`
Roteia input para o especialista com maior NMI médio com o estado.
Se NMI < 0.01, usa MCR principal (fallback).

**5. Avaliar** — `avaliar_composicao(dataset)`
Compara accuracy do MCR orquestrado vs MCR solo. Retorna ganho.

### Integração no coupling
- `ativar_auto_composicao()` → retorna instância
- `compor_especialistas()` → compõe equipe automática
- `orquestrar_especialistas(estado)` → roteia para especialista
- `avaliar_composicao(dataset)` → compara vs solo

---

## FASE 16 — Teoria da mente: modelar outros agentes (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR agora modela o que OUTROS agentes sabem, acreditam e fariam.
Capacidade de atribuir estados mentais (crenças, desejos, intenções)
a outros — fundamental para colaboração, negociação e previsão.

### Resultados reais (51 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Modelar: criar_agente retorna AgenteMental | ✅ |
| Modelar: agente tem nome | ✅ |
| Modelar: criou segundo agente | ✅ |
| Modelar: listar_agentes | ✅ |
| Modelar: conhecimento compartilhado | ✅ |
| Modelar: obter_agente correto | ✅ |
| Modelar: obter_agente inexistente | ✅ |
| Predizer: tem agente | ✅ |
| Predizer: tem acao_agente | ✅ |
| Predizer: tem acao_realidade | ✅ |
| Predizer: tem concordam (bool) | ✅ |
| Predizer: tem divergencia | ✅ |
| Predizer: sally diverge em 'editar' | ✅ |
| Predizer: bob concorda (conhecimento completo) | ✅ |
| Crenças: agente tem crença | ✅ |
| Crenças: crença inexistente = None | ✅ |
| Crenças: inferir tem palavras_conhecidas | ✅ |
| Crenças: inferir tem cobertura | ✅ |
| Crenças: inferir tem acoes_conhecidas | ✅ |
| Crenças: inferir tem crencas_explicitas | ✅ |
| Crenças: sally cobertura > 0 em 'criar' | ✅ |
| Crenças: sally cobertura baixa em 'editar' | ✅ |
| Crenças: definir_intencao | ✅ |
| Crenças: crenca_count | ✅ |
| Crença falsa: tem agente | ✅ |
| Crença falsa: tem acao_agente | ✅ |
| Crença falsa: tem acao_realidade | ✅ |
| Crença falsa: tem tem_crenca_falsa (bool) | ✅ |
| Crença falsa: tem cobertura_agente | ✅ |
| Crença falsa: tem explicacao | ✅ |
| Crença falsa: bob sem crença falsa | ✅ |
| Perspectiva: perspectivas (lista) | ✅ |
| Perspectiva: consenso | ✅ |
| Perspectiva: taxa_consenso | ✅ |
| Perspectiva: divergencia_max | ✅ |
| Perspectiva: n_perspectivas | ✅ |
| Perspectiva: inclui realidade | ✅ |
| Interação: agente_a e agente_b | ✅ |
| Interação: acao_a e acao_b | ✅ |
| Interação: concordam (bool) | ✅ |
| Interação: dinamica | ✅ |
| Integração: ativar_teoria_da_mente | ✅ |
| Integração: criar_agente via coupling | ✅ |
| Integração: predizer_acao_agente | ✅ |
| Integração: teste_crenca_falsa | ✅ |
| Integração: comparar_perspectivas | ✅ |
| Estatísticas: n_agentes | ✅ |
| Estatísticas: agentes (lista) | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 16.1 TeoriaDaMente (`mcr/teoria_da_mente.py`) — IMPLEMENTADO
MCR que modela outros agentes (teoria da mente).

5 capacidades:

**1. Modelar agente** — `criar_agente(nome, corpus)`
Cria AgenteMental com seu próprio MCRCoupling (subset do conhecimento).
`conhecimento_compartilhado=True` copia conhecimento do MCR principal.

**2. Predizer ação** — `predizer_acao(agente, estado)`
O que o agente faria? Usa coupling do AGENTE (não do MCR principal).
Compara com realidade: concordam? divergência de confiança?

**3. Atribuir crenças** — `atribuir_crenca(agente, fato, valor)` + `inferir_crenca(agente, estado)`
Crenças explícitas (fato→valor) + inferidas (palavras conhecidas,
cobertura, visão de mundo). Intenções (objetivos).

**4. Crença falsa** — `teste_crenca_falsa(agente, estado, realidade)`
Teste Sally-Anne: agente com conhecimento desatualizado age
diferente da realidade. `tem_crenca_falsa = acao_agente != acao_realidade`.

**5. Perspectiva** — `comparar_perspectivas(estado, agentes)`
Compara visões de múltiplos agentes: consenso, taxa de concordância,
divergência máxima. `predizer_interacao(a, b, estado)` modela
interação entre dois agentes (cooperação/conflito/independência).

### Integração no coupling
- `ativar_teoria_da_mente()` → retorna instância
- `criar_agente(nome, corpus)` → cria agente simulado
- `predizer_acao_agente(agente, estado)` → prediz ação
- `teste_crenca_falsa(agente, estado)` → teste Sally-Anne
- `comparar_perspectivas(estado)` → compara visões

---

## FASE 15 — Planejamento: MCR planeja antes de agir (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR simula múltiplos futuros possíveis e escolhe o plano de ação
com maior valor esperado segundo a Equação 5D. Como MCTS mas
markoviano, com 5D como função de valor.

### Resultados reais (38 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Simular: retorna trajetória | ✅ |
| Simular: 3 passos | ✅ |
| Simular: passo tem ação | ✅ |
| Simular: passo tem confiança | ✅ |
| Simular: passo tem entropia | ✅ |
| Simular: passo tem número | ✅ |
| Simular: 1 passo | ✅ |
| Planejar: retorna plano | ✅ |
| Planejar: retorna score | ✅ |
| Planejar: retorna alternativas | ✅ |
| Planejar: retorna estado_inicial | ✅ |
| Planejar: retorna profundidade | ✅ |
| Planejar: retorna n_caminhos | ✅ |
| Planejar: plano tem ≥1 ação | ✅ |
| Planejar: profundidade 1 | ✅ |
| Avaliar: score válido | ✅ |
| Avaliar: confiança alta > baixa | ✅ |
| Avaliar: plano vazio = 0 | ✅ |
| Avaliar: 1 ação | ✅ |
| Replanificar: novo_plano | ✅ |
| Replanificar: mudou (bool) | ✅ |
| Replanificar: razão | ✅ |
| Replanificar: sobreposição | ✅ |
| Replanificar: estado similar | ✅ |
| Heurísticas: diversidade | ✅ |
| Heurísticas: familiaridade | ✅ |
| Heurísticas: coerência | ✅ |
| Heurísticas: familiar > 0 | ✅ |
| Heurísticas: desconhecido ~ 0 | ✅ |
| Integração: ativar_planejador | ✅ |
| Integração: planejar via coupling | ✅ |
| Integração: simular via coupling | ✅ |
| Integração: replanificar via coupling | ✅ |
| Integração: heuristicas via coupling | ✅ |
| Estatísticas: campos essenciais | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 15.1 Planejador (`mcr/planejador.py`) — IMPLEMENTADO
Busca em árvore markoviana com Equação 5D como função de valor.

5 capacidades:

**1. Simular** — `simular(estado, acao, n_passos)`
Dado estado + ação, prevê próximos N estados via Markov. Cada passo:
{passo, acao, confianca, entropia}.

**2. Planejar** — `planejar(estado, profundidade, top_k)`
Beam search: a cada nível, expande top_k ações mais prováveis. Avalia
cada caminho completo com 5D. Retorna melhor plano + alternativas.

**3. Avaliar plano** — `avaliar_plano(estado, caminho)`
Score 5D: CERTEZA (confiança média) × COMPLETUDE (fracção > 0.3) ×
INFORMACAO (entropia da distribuição) × ESTABILIDADE (baixa variância) ×
EFICIENCIA (1/log2(n+1)).

**4. Replanificar** — `replanificar(estado_ant, estado_novo, plano_ant)`
Compara plano anterior com novo estado. Se sobreposição > 50%,
mantém parcialmente. Senão, replaneja do zero.

**5. Heurísticas** — `heuristicas(estado)`
Diversidade (entropia), familiaridade (cobertura), coerência (NMI média).
Guia poda da árvore de busca.

### Integração no coupling
- `ativar_planejador()` → retorna instância
- `planejar(estado, prof, top_k)` → melhor plano
- `simular_acao(estado, acao, n)` → trajetória
- `replanificar(est_ant, est_novo, plano_ant)` → adapta
- `heuristicas_estado(estado)` → diversidade, familiaridade, coerência

---

## FASE 14 — Raciocínio contrafactual: "o que aconteceria se...?" (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

Terceiro degrau da Escada de Causalidade de Pearl. O MCR agora
responde "o que aconteceria se A tivesse sido diferente?" — usando
abdução (inferir confounders), ação (substituir A), e predição
(propagar o efeito).

### Resultados reais (42 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Contrafactual: a_observado | ✅ |
| Contrafactual: a_contrafactual | ✅ |
| Contrafactual: p_b_original | ✅ |
| Contrafactual: p_b_contrafactual | ✅ |
| Contrafactual: delta | ✅ |
| Contrafactual: acao_mudou (bool) | ✅ |
| Contrafactual: interpretacao | ✅ |
| Contrafactual: confounders_abduzidos | ✅ |
| Contrafactual: mesma palavra delta ~ 0 | ✅ |
| Necessidade: a e b | ✅ |
| Necessidade: alternativa | ✅ |
| Necessidade: p_b_com_a | ✅ |
| Necessidade: p_b_sem_a | ✅ |
| Necessidade: necessario (bool) | ✅ |
| Necessidade: interpretacao | ✅ |
| Suficiência: a e b | ✅ |
| Suficiência: p_b_observacional | ✅ |
| Suficiência: p_b_intervencional | ✅ |
| Suficiência: suficiente (bool) | ✅ |
| Suficiência: razao | ✅ |
| Suficiência: interpretacao | ✅ |
| Cenários: retorna lista | ✅ |
| Cenários: exclui a_observado | ✅ |
| Cenários: melhor_cenario | ✅ |
| Cenários: melhor_alternativa | ✅ |
| Propagação: a, b, c observados | ✅ |
| Propagação: a_contrafactual | ✅ |
| Propagação: b_contrafactual_prob | ✅ |
| Propagação: c_original_prob | ✅ |
| Propagação: c_contrafactual_prob | ✅ |
| Propagação: delta_c | ✅ |
| Propagação: propagou (bool) | ✅ |
| Propagação: cf_a_b | ✅ |
| Integração: ativar_contrafactual | ✅ |
| Integração: o_que_se via coupling | ✅ |
| Integração: necessidade via coupling | ✅ |
| Integração: suficiencia via coupling | ✅ |
| Integração: cenarios via coupling | ✅ |
| Estatísticas: campos essenciais | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 14.1 Contrafactual (`mcr/contrafactual.py`) — IMPLEMENTADO
Raciocínio contrafactual — 3º degrau de Pearl.

5 capacidades:

**1. Contrafactual** — `o_que_se(a_obs, b_obs, a_counter)`
"Se A fosse a', qual seria B?" Passos de Pearl:
- Abdução: P(confounders|A=a, B=b) — dado o observado, quais confounders?
- Ação: substituir A por a_counter
- Predição: P(B'|do(a_counter), confounders) — o que B seria?

**2. Necessidade causal** — `necessidade_causal(a, b)`
"A foi necessário para B?" Se P(B|do(¬A)) << P(B|A), A foi necessário.
¬A = melhor alternativa (palavra que co-ocorre com mesmos contextos).

**3. Suficiência causal** — `suficiencia_causal(a, b)`
"A foi suficiente para B?" Se P(B|do(A)) > 0.3, A é suficiente
sem precisar de confounders.

**4. Cenários hipotéticos** — `cenarios(a, b, [a1, a2, ...])`
Gera múltiplos contrafactuais. `melhor_cenario()` encontra a
alternativa que maximizaria B.

**5. Propagação em cadeia** — `propagar_contrafactual(a, b, c, a')`
"Se A mudasse, como C mudaria via B?" A→B→C: contrafactual de A
sobre B, depois propaga B' sobre C.

### Integração no coupling
- `ativar_contrafactual()` → retorna instância
- `o_que_se(a, b, a')` → contrafactual
- `necessidade_causal(a, b)` → A foi necessário?
- `suficiencia_causal(a, b)` → A foi suficiente?
- `cenarios_contrafactuais(a, b, alts)` → múltiplos cenários

---

## FASE 13 — Causalidade: P(B|do(A)) vs P(B|A) (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR já calcula P(B|A) (correlação markoviana). Mas correlação não
implica causalidade. Esta fase implementa do-calculus de Pearl para
distinguir correlação de causalidade, identificar confounders, detectar
cadeias causais e verificar d-separação.

### Resultados reais (32 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Confounders: identificou para criar/monstro | ✅ |
| Confounders: forca > 1 (lift) | ✅ |
| Confounders: editar/buscar sem confounders | ✅ |
| Confounders: campos essenciais | ✅ |
| Intervir: P(B\|do(A)) valida | ✅ |
| Intervir: P(B\|A) calculada | ✅ |
| Intervir: sem confounders P(do) ~ P(obs) | ✅ |
| Efeito: tem p_b_dado_a | ✅ |
| Efeito: tem p_b_dado_do_a | ✅ |
| Efeito: tem diferenca | ✅ |
| Efeito: tem tipo (causal/confundido/espurio) | ✅ |
| Efeito: diferenca >= 0 | ✅ |
| Cadeia: tem a, b, c | ✅ |
| Cadeia: tem e_mediado | ✅ |
| Cadeia: tem e_direto | ✅ |
| Cadeia: tem e_cadeia (bool) | ✅ |
| Cadeia: tem ratio_mediacao | ✅ |
| d-sep: tem a, b, c | ✅ |
| d-sep: tem p_b_dado_c | ✅ |
| d-sep: tem p_b_dado_a_c | ✅ |
| d-sep: tem independentes (bool) | ✅ |
| d-sep: tem diferenca | ✅ |
| Integração: ativar_causalidade | ✅ |
| Integração: efeito_causal via coupling | ✅ |
| Integração: confounders via coupling | ✅ |
| Integração: intervir via coupling | ✅ |
| Integração: cadeia_causal via coupling | ✅ |
| Integração: d_separacao via coupling | ✅ |
| Estatísticas: campos essenciais | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 13.1 Causalidade (`mcr/causalidade.py`) — IMPLEMENTADO
Inferência causal sobre o modelo markoviano do MCR.

5 capacidades:

**1. Confounders** — `identificar_confounders(a, b)`
Variável C que prediz A (P(A|C) > P(A)) e B (P(B|C) > P(B)).
Se C causa ambos, P(B|A) pode ser espúria. Força = min(lift_A, lift_B).

**2. Intervir (do)** — `intervir(a, b)` → P(B|do(A))
Backdoor adjustment de Pearl: P(B|do(A)) = Σ_C P(B|A,C) × P(C).
Sem confounders → P(B|do(A)) = P(B|A).

**3. Efeito causal** — `efeito_causal(a, b)` → {p_obs, p_causal, diff, tipo}
Compara P(B|A) com P(B|do(A)). Tipo:
- 'causal': diff < 0.05 (A causa B diretamente)
- 'confundido': 0.05 ≤ diff < 0.20 (parcialmente confundido)
- 'espurio': diff ≥ 0.20 (correlação espúria)

**4. Cadeia causal** — `cadeia_causal(a, b, c)` → A→B→C?
Efeito mediado = P(B|do(A)) × P(C|B). Se ~ efeito direto, B media.

**5. d-separação** — `d_separacao(a, b, c)` → A⊥B|C?
P(B|A,C) = P(B|C)? Se sim, C bloqueia o caminho (d-separados).

### Integração no coupling
- `ativar_causalidade()` → retorna instância de Causalidade
- `efeito_causal(a, b)` → compara correlação vs causalidade
- `confounders(a, b)` → lista de confounders
- `intervir(a, b)` → P(B|do(A))
- `cadeia_causal(a, b, c)` → verifica A→B→C
- `d_separacao(a, b, c)` → verifica independência condicional

---

## FASE 12 — Meta-Equação: auto-evolução dos pesos 5D (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

A Equação 5D tem 5 pesos que controlam como o MCR avalia decisões.
Inicialmente todos = 2.0 (neutro). A Meta-Equação evolui esses pesos
via hill climbing markoviano: cada passo depende do anterior.

### Resultados reais (28 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Avaliar: retorna accuracy | ✅ |
| Avaliar: retorna separacao | ✅ |
| Avaliar: retorna score | ✅ |
| Avaliar: tem n_testes | ✅ |
| Avaliar: pesos diferentes não quebra | ✅ |
| Evoluir: retorna melhores_pesos | ✅ |
| Evoluir: retorna melhor_score | ✅ |
| Evoluir: retorna historico | ✅ |
| Evoluir: retorna n_geracoes | ✅ |
| Evoluir: melhores_pesos tem 5 dimensões | ✅ |
| Evoluir: pesos no range [0.1, 10.0] | ✅ |
| Evoluir: score >= inicial | ✅ |
| Aplicar: atualizou EQUACAO_5D | ✅ |
| Aplicar: avaliar_5d funciona | ✅ |
| Aplicar: reverter volta ao padrão | ✅ |
| Análise: melhor_combinacao | ✅ |
| Análise: historico_evolucao | ✅ |
| Análise: trajetoria_pesos | ✅ |
| Análise: convergiu | ✅ |
| Análise: estatisticas | ✅ |
| Integração: ativar_meta_equacao | ✅ |
| Integração: evoluir_equacao via coupling | ✅ |
| Integração: aplicar_equacao via coupling | ✅ |
| Integração: reverter_equacao via coupling | ✅ |
| Integração: estatisticas_equacao | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |
| Regressão: fogo = elementos | ✅ |

### 12.1 MetaEquacao (`mcr/meta_equacao.py`) — IMPLEMENTADO
Auto-evolução dos pesos 5D via hill climbing markoviano.

3 capacidades:

**1. Avaliar** — `avaliar_pesos(pesos)` → {accuracy, separacao, score}
Testa uma combinação de pesos no dataset. Score = accuracy × 0.7 +
separação × 0.3. Separação = diferença entre confiança média de
decisões corretas vs incorretas.

**2. Evoluir** — `evoluir(n_geracoes)` → {melhores_pesos, historico}
Hill climbing: cada geração perturba cada dimensão ±passo. Move-se
para o melhor vizinho (markoviano: só depende do estado atual).
Se nenhuma melhora, reduz passo (convergência). 3 tamanhos de passo:
0.5, 1.0, 2.0.

**3. Aplicar** — `aplicar()` / `reverter()`
Aplica os melhores pesos à EQUACAO_5D global. Todas as chamadas
futuras a `avaliar_5d()` usam os novos pesos. `reverter()` volta
ao padrão (todos = 2.0).

### Integração no coupling
- `ativar_meta_equacao()` → retorna instância de MetaEquacao
- `evoluir_equacao(dataset, n_geracoes)` → executa evolução
- `aplicar_equacao()` → aplica melhores pesos
- `reverter_equacao()` → reverte para padrão
- `estatisticas_equacao()` → estatísticas resumidas

---

## FASE 11 — Auto-expansão: curiosidade dirigida por entropia (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR identifica onde sua entropia é maior (maior incerteza) e
ativamente busca novos dados para reduzi-la. Curiosidade = busca por
máxima redução de entropia.

### Resultados reais (23 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Identificar: encontrou gaps | ✅ |
| Identificar: monstro é gap (alta entropia) | ✅ |
| Identificar: monstro tem H > 0 | ✅ |
| Identificar: fogo não é gap (baixa entropia) | ✅ |
| Perguntas: gerou queries | ✅ |
| Perguntas: contém palavra do gap | ✅ |
| Perguntas: gerou co-ocorrências | ✅ |
| Buscar: encontrou fragmentos na fonte | ✅ |
| Buscar: fragmentos contêm palavra do gap | ✅ |
| Buscar: busca em arquivo funciona | ✅ |
| Aprender: aprendeu exemplos | ✅ |
| Aprender: vocabulário cresceu | ✅ |
| Verificar: H calculada após aprendizado | ✅ |
| Verificar: H mudou após aprendizado | ✅ |
| Ciclo: H do vocabulário calculada | ✅ |
| Ciclo: executou | ✅ |
| Ciclo: encontrou gaps | ✅ |
| Ciclo: aprendeu exemplos | ✅ |
| Ciclo: status válido | ✅ |
| Ciclo: H do vocabulário recalculada | ✅ |
| Ciclo: estatísticas completas | ✅ |
| Regressão: decidir() funciona | ✅ |
| Regressão: buscar = buscar | ✅ |

### 11.1 AutoExpansao (`mcr/auto_expansao.py`) — IMPLEMENTADO
Curiosidade dirigida por entropia. O MCR observa seu próprio modelo
e identifica onde está mais incerto. Gera perguntas, busca texto em
fontes disponíveis, aprende, e verifica se a entropia diminuiu.

5 capacidades:

**1. Identificar gaps** — `identificar_gaps(top_n)`
Palavras com H(P(acao|palavra)) alta = MCR incerto = gap.
Potencial de redução = H × 1/log(n_exemplos+1) — palavras com poucos
exemplos e alta H têm maior potencial de aprendizado.

**2. Gerar perguntas** — `gerar_perguntas(gap, top_k)`
Para cada gap: palavra + co-ocorrências (bigramas via _transicao_palavra)
+ palavras similares (NMI de assinaturas).

**3. Buscar conhecimento** — `buscar_conhecimento(queries, max)`
Vasculha fontes disponíveis (texto direto, arquivos, diretórios) em
busca de fragmentos que contêm as queries. Split por pontuação/newlines.

**4. Aprender** — `aprender_fragmentos(fragmentos, gap)`
Para cada fragmento: infere ação via decidir() → alimenta coupling.
Reinicia o loop fechado: observar → decidir → aprender → observar.

**5. Verificar** — `verificar_reducao(palavra)`
Mede H antes vs depois. Se H diminuiu → curiosidade satisfeita.
Histórico de H por palavra detecta convergência (gap saturado).

### Ciclo completo
`ciclo_curiosidade(max_gaps)` → identifica gaps → gera perguntas →
busca → aprende → verifica. Retorna relatório com reduções de H.

### Integração no coupling
- `ativar_curiosidade()` → retorna instância de AutoExpansao
- `ciclo_curiosidade(max_gaps)` → executa ciclo completo
- `entropia_vocabulario()` → H média do vocabulário (saúde cognitiva)

---

## FASE 10 — Meta-cognição: MCR observa o próprio MCR (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

O MCR agora observa suas próprias decisões, mede incerteza de segunda
ordem, calibra confiança com feedback, decide quando NÃO responder
("não sei" é resposta válida), e auto-diagnostica viés, drift e gaps.

### Resultados reais (26 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Observação: decidir funciona sem meta | ✅ |
| Observação: meta ativada | ✅ |
| Observação: decidir com meta em dominio familiar | ✅ |
| Observação: registro de observação | ✅ |
| Observação: desativada não observa | ✅ |
| Incerteza: baixa em decisão familiar | ✅ |
| Incerteza: alta em distribuição plana | ✅ |
| Incerteza: maior com novelty | ✅ |
| Calibração: Brier score calculado | ✅ |
| Calibração: reduz overconfidence (0.9 → 0.8) | ✅ |
| Calibração: confiança média (0.5 → 0.4) | ✅ |
| Calibração: curva com ≥2 bins | ✅ |
| Calibração: presunção calculada | ✅ |
| Veto: pode responder em familiar | ✅ |
| Veto: não responde com plana+novelty | ✅ |
| Veto: não responde com confiança baixa | ✅ |
| Diagnóstico: tem status | ✅ |
| Diagnóstico: tem n_observacoes | ✅ |
| Diagnóstico: tem taxa_acerto | ✅ |
| Diagnóstico: tem brier_score | ✅ |
| Diagnóstico: detecta viés | ✅ |
| Diagnóstico: detecta gaps | ✅ |
| Diagnóstico: estatísticas completas | ✅ |
| Regressão: decidir sem meta = criar | ✅ |
| Regressão: decidir sem meta = editar | ✅ |
| Regressão: decidir sem meta = elementos | ✅ |

### 10.1 MetaCognitivo (`mcr/meta_cognitivo.py`) — IMPLEMENTADO
MCR que observa o próprio MCR. Segunda ordem: não é "quão confiante
estou?" mas "devo confiar na minha confiança?"

5 capacidades meta-cognitivas:

**1. Observar** — `observar(texto, acao, confianca, distribuicao, n_fontes, divergencia)`
Registra cada decisão para análise. Opt-in (não afeta classificação).

**2. Incerteza** — `incerteza_meta(confianca, distribuicao, n_fontes, divergencia, texto)`
Combina 3 sinais: entropia da distribuição + divergência entre fontes +
novelty do input. Ajusta pela calibração histórica (overconfidence
detectado → incerteza aumenta).

**3. Calibrar** — `feedback(confianca, correto, acao)` + `calibrar_confianca(conf)`
Aprende P(correto|bin_confiança) via Markov 1ª ordem. Se MCR diz 0.9
mas historicamente só acerta 70% nesse bin, confiança calibrada = 0.7.
Brier score mede qualidade da calibração.

**4. Decidir quando NÃO responder** — `pode_responder(texto, confianca, dist, n_fontes, div)`
Retorna (deve_responder, confianca_calibrada, justificativa).
Vetoa se: conf_efetiva < threshold adaptativo, novelty alto, ou
distribuição plana. Boost de familiaridade: cobertura > 0.7 →
threshold reduzido (mais permissivo em domínios conhecidos).

**5. Auto-diagnosticar** — `auto_diagnosticar()`
Detecta: overconfidence/underconfidence (gap > 0.15), domain shift
(comparar cobertura antiga vs recente), convergence, gaps (domínios
com baixa confiança OU alto erro).

### Integração no coupling
- `ativar_metacognicao()` / `desativar_metacognicao()` — opt-in
- `feedback_meta(confianca, correto)` — aprende calibração
- `diagnostico_meta()` — retorna auto-diagnóstico
- `pode_responder_meta(texto, conf, dist)` — consulta veto
- `estatisticas_meta()` — estatísticas resumidas
- Quando ativa, `decidir()` pode retornar `('nao_sei', conf)` se vetoado

---

## FASE 9 — Candidatas a Superar LLM em 4 Capacidades (2026-07-16)
**Status**: IMPLEMENTADA e VALIDADA (testes MCR internos) — classificação CONFIRMADA vs phi4-mini (Pilar 8); geração longa/raciocínio/conhecimento são HIPÓTESES (Pilar 9)
**Esforço**: médio | **Impacto**: muito alto

> **Pilar 8 (atualizado v4.2)**: a hipótese de classificação foi CONFIRMADA
> por medição direta — MCR 100.0% vs phi4-mini 70.8% no split 449/113
> (ver Regime de Comparação). As demais (geração longa, raciocínio
> multi-etapa, conhecimento) permanecem hipóteses até testes específicos.

Endereça 4 áreas onde LLM poderia superar MCR: geração longa, raciocínio
multi-etapa, conhecimento enciclopédico, few-shot sem retreino.

### Resultados reais (16 PASS / 0 FAIL)
| Teste | Resultado |
|---|---|
| Few-shot: extrair exemplos do prompt | ✅ 4/4 exemplos |
| Few-shot: peixe → animais (zero-shot) | ✅ |
| Few-shot: moto → veiculos (herança) | ✅ |
| Few-shot: gelo → elementos (herança) | ✅ |
| Geração longa: 10+ tokens coerentes | ✅ |
| Geração longa: 20+ tokens coerentes | ✅ |
| Geração com tema (fogo) | ✅ |
| Raciocínio: pergunta composta | ✅ |
| Raciocínio: sequência (buscar→editar) | ✅ |
| Silogismo: criar+monstro → criar | ✅ |
| Conhecimento: ingestão de fatos | ✅ |
| Conhecimento: conceitos indexados | ✅ |
| Conhecimento: recuperação por NMI | ✅ |
| Conhecimento: fato relevante recuperado | ✅ |
| Conhecimento: resposta usando base | ✅ |
| Regressão: decidir() funciona | ✅ |

### 9.1 FewShotLearner (`mcr/few_shot.py`) — IMPLEMENTADO
LLMs aprendem do prompt. MCR faz o mesmo: EXTRAI exemplos do prompt
e alimenta o coupling em runtime. P(b|a) aprende em 1 exemplo.

- `aprender_do_prompt(prompt)` — detecta padrões "input → output"
- `predizer(input)` — usa coupling normalmente após exemplos
- Zero retreino, zero backprop, zero GPU

**Hipótese de vantagem vs LLM**: MCR aprende em 1 exemplo (LLM precisa de few-shot
com 5-10 exemplos para convergir). MCR é determinístico (mesmo prompt =
mesma resposta). MCR não esquece (contagem acumula). **Parcialmente confirmado**:
a comparação Pilar 8 usou phi4-mini few-shot 5/ex — MCR 100.0% vs 70.8%.
A diferença sugere que o MCR extrai mais sinal por exemplo, mas o teste
específico few-shot 1/ex vs MCR 1/ex ainda não foi rodado.

### 9.2 GeradorCoerente (`mcr/gerador_coerente.py`) — IMPLEMENTADO
Geração longa com working memory de 3 componentes:
1. Buffer recente (exato, lossless) — últimos N tokens
2. Assinatura temática (comprimida, lossy) — hierarquia do texto todo
3. Buffer de entidades (exato) — sujeitos/objetos mencionados

A cada passo: gerar top-K candidatos via `_transicao_palavra` →
avaliar cada um com Equação 5D (coerência com tema, novidade) →
escolher o melhor. Fecho transitivo como fallback quando transições
diretas se esgotam.

- `gerar(semente, max_tokens, top_k)` → texto longo coerente
- Penalidade suave por repetição (não filtro duro)
- Detecção de loop via entropia
- Fecho transitivo para diversificar quando loop detectado

**Hipótese de vantagem vs LLM (com ressalva — Pilar 9)**: 7ms/token em CPU
(LLM: 100-500ms/token em GPU). Transparente — cada token é explicável por
P(next|current). **Ressalva honesta**: working memory de 3 buffers contorna
o limite de Markov 1ª ordem, não o resolve — geração ainda colapsa em
~N tokens (N > 20 que o MCR puro, mas << 4000 da LLM). A medir em qual
N o MCR degrada vs phi4-mini no mesmo corpus.

### 9.3 RaciocinadorMarkoviano (`mcr/raciocinador_mk.py`) — IMPLEMENTADO
Chain-of-thought markoviano:
1. Decompõe pergunta em sub-perguntas (conectivos lógicos)
2. Resolve cada uma em sequência, propagando contexto
3. Combina respostas via contexto acumulado
4. Avalia cadeia com Equação 5D
5. Se confiança baixa, explora alternativas via fecho transitivo

- `raciocinar(pergunta, contexto)` → (resposta, confianca_5d)
- `silogismo(premissa_a, premissa_b)` → raciocínio transitivo
- `_decompor()` — split por conectivos (e, então, logo, portanto)
- `_explorar_alternativas()` — fecho transitivo quando conf < 0.3

**Hipótese de vantagem vs LLM**: cada passo do raciocínio é auditável (matrizes).
Determinístico — mesmo pergunta = mesma cadeia. Não alucina passos
intermediários. Fecho transitivo conecta etapas distantes sem attention.
**Ressalva honesta (Pilar 9)**: em corpus pequeno (16 pares), o fecho
transitivo amplifica conexões indiretas espúrias (flutuação FASE 5/6).
A medir em corpus maior.

### 9.4 BaseConhecimento (`mcr/base_conhecimento.py`) — IMPLEMENTADO
Ingestão enciclopédica + recuperação por NMI:
1. `ingerir(texto, fonte)` — extrai fatos, alimenta coupling + indexa
2. `recuperar(pergunta)` — NMI entre pergunta e fatos indexados
3. `responder(pergunta)` — recuperar + decidir com contexto

- `_extrair_frases()` — split por pontuação
- `_extrair_conceito_principal()` — palavra de maior especificidade
- `_classificar_fato()` — reusa ação do conceito ou cria nova
- Indexação por conceito para recuperação O(1)

**Hipótese de vantagem vs LLM**: conhecimento é exato (contagem, não paramétrico).
Recuperação é transparente (NMI explicável). Atualização é instantânea
(1 fato = 1 alimentar). Não precisa de retreino para aprender novo fato.
**A medir**: comparar precisão factual MCR vs phi4-mini RAG no mesmo
corpus ingerido.

---

## Ordem de Execução
1. **FASE 1** (compor) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
2. **FASE 2** (relações) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
3. **FASE 3** (grounding simbólico) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
4. **FASE 4** (grounding ambiental) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
5. **FASE 5** (hierárquico) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
6. **FASE 6** (multimodal) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
7. **Negação** — ✅ RESOLVIDA via funtor entrópico + antônimo (2026-07-16)
8. **Validação final** — ✅ 170/170 testes, 94.7% regressão (2026-07-16)
9. **FASE 7** (integração archives) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
   - 7.0 Confiança Posicional P0 — ✅ 113/113, EXP2 50%
   - 7.1 Melhorias fontes existentes (#11-16) — ✅ todos implementados
   - 7.2 Melhorias _superpor (#17-21) — ✅ todos implementados
   - 7.3 Novas fontes de decisão (#1-10) — ✅ todos implementados
   - 7.4 Conceitos arquiteturais (#22-30) — ✅ todos implementados
     - Resultado: 94.7% → **100.0%** (113/113), latência 7.26ms
10. **FASE 8** (novas fontes cognitivas) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - Resultado: 94.7% → **100.0%** (113/113), latência 7.26ms, 13 fontes
11. **FASE 9** (candidatas a superar LLM — HIPÓTESES, Pilar 8) — ✅ IMPLEMENTADA (testes MCR internos)
     - 9.1 FewShotLearner — ✅ few-shot sem retreino (4/4 testes)
     - 9.2 GeradorCoerente — ✅ geração longa com working memory (3/3)
     - 9.3 RaciocinadorMarkoviano — ✅ chain-of-thought markoviano (3/3)
     - 9.4 BaseConhecimento — ✅ ingestão + recuperação NMI (5/5)
    - 9.5 Regressão — ✅ decidir() funciona (1/1)
    - Resultado: 16/16 testes, 113/113 regressão
12. **FASE 10** (meta-cognição) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 10.1 Observar (opt-in, não afeta classificação) — ✅ 5/5 testes
    - 10.2 Incerteza meta (entropia + divergência + novelty) — ✅ 3/3 testes
    - 10.3 Calibração (feedback → P(correto|bin), Brier score) — ✅ 5/5 testes
    - 10.4 Veto ("não sei" é resposta válida) — ✅ 3/3 testes
    - 10.5 Auto-diagnóstico (vies, drift, gaps) — ✅ 7/7 testes
    - 10.6 Regressão (decidir sem meta não muda) — ✅ 3/3 testes
    - Resultado: 26/26 testes, 113/113 regressão, 16/16 FASE 9
13. **FASE 11** (auto-expansão) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 11.1 Identificar gaps por entropia — ✅ 4/4 testes
    - 11.2 Gerar perguntas (co-ocorrências + NMI) — ✅ 3/3 testes
    - 11.3 Buscar conhecimento (texto + arquivo + diretório) — ✅ 3/3 testes
    - 11.4 Aprender (alimentar coupling) — ✅ 2/2 testes
    - 11.5 Verificar redução de entropia — ✅ 2/2 testes
    - 11.6 Ciclo completo — ✅ 6/6 testes
    - 11.7 Regressão — ✅ 2/2 testes
    - Resultado: 23/23 testes, 113/113 regressão, 16/16 FASE 9, 26/26 FASE 10
14. **FASE 12** (meta-equação) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 12.1 Avaliar (accuracy + separação + score) — ✅ 5/5 testes
    - 12.2 Evoluir (hill climbing markoviano) — ✅ 7/7 testes
    - 12.3 Aplicar/reverter EQUACAO_5D — ✅ 3/3 testes
    - 12.4 Análise (trajetória, convergência) — ✅ 5/5 testes
    - 12.5 Integração no coupling — ✅ 5/5 testes
    - 12.6 Regressão — ✅ 3/3 testes
    - Resultado: 28/28 testes, 113/113 regressão, 16/16 FASE 9, 26/26 FASE 10, 23/23 FASE 11
15. **FASE 13** (causalidade) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 13.1 Confounders (lift > 1) — ✅ 4/4 testes
    - 13.2 Intervir (do-calculus de Pearl) — ✅ 3/3 testes
    - 13.3 Efeito causal (causal/confundido/espurio) — ✅ 5/5 testes
    - 13.4 Cadeia causal (A->B->C) — ✅ 5/5 testes
    - 13.5 d-separacao (A independente de B dado C?) — ✅ 5/5 testes
    - 13.6 Integração no coupling — ✅ 6/6 testes
    - 13.7 Estatísticas — ✅ 1/1 teste
    - 13.8 Regressão — ✅ 3/3 testes
    - Resultado: 32/32 testes, 113/113 regressão, 16/16 FASE 9, 26/26 FASE 10, 23/23 FASE 11, 28/28 FASE 12
16. **FASE 14** (contrafactual) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 14.1 Contrafactual (abdução + ação + predição de Pearl) — ✅ 9/9 testes
    - 14.2 Necessidade causal — ✅ 6/6 testes
    - 14.3 Suficiência causal — ✅ 6/6 testes
    - 14.4 Cenários hipotéticos — ✅ 4/4 testes
    - 14.5 Propagação em cadeia (A->B->C) — ✅ 8/8 testes
    - 14.6 Integração no coupling — ✅ 5/5 testes
    - 14.7 Estatísticas — ✅ 1/1 teste
    - 14.8 Regressão — ✅ 3/3 testes
    - Resultado: 42/42 testes, 113/113 regressão, todas as fases 100%
17. **FASE 15** (planejamento) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 15.1 Simular (prever N passos via Markov) — ✅ 7/7 testes
    - 15.2 Planejar (beam search + 5D) — ✅ 8/8 testes
    - 15.3 Avaliar plano (score 5D) — ✅ 4/4 testes
    - 15.4 Replanificar (adapta plano) — ✅ 5/5 testes
    - 15.5 Heurísticas (poda NMI/entropia) — ✅ 5/5 testes
    - 15.6 Integração no coupling — ✅ 5/5 testes
    - 15.7 Estatísticas — ✅ 1/1 teste
    - 15.8 Regressão — ✅ 3/3 testes
    - Resultado: 38/38 testes, 113/113 regressão, todas as fases 100%
18. **FASE 16** (teoria da mente) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 16.1 Modelar agente (criar, listar, obter) — ✅ 7/7 testes
    - 16.2 Predizer ação (agente vs realidade) — ✅ 7/7 testes
    - 16.3 Atribuir crenças (explícitas + inferidas) — ✅ 10/10 testes
    - 16.4 Crença falsa (Sally-Anne) — ✅ 7/7 testes
    - 16.5 Perspectiva + interação — ✅ 10/10 testes
    - 16.6 Integração no coupling — ✅ 5/5 testes
    - 16.7 Estatísticas — ✅ 2/2 testes
    - 16.8 Regressão — ✅ 3/3 testes
    - Resultado: 51/51 testes, 113/113 regressão, todas as fases 100%
19. **FASE 17** (auto-composição) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 17.1 Observar domínio (clusters via NMI) — ✅ 5/5 testes
    - 17.2 Criar especialista (MCRCoupling filtrado) — ✅ 7/7 testes
    - 17.3 Compor (equipe automática) — ✅ 7/7 testes
    - 17.4 Orquestrar (rotear por NMI) — ✅ 8/8 testes
    - 17.5 Avaliar (composição vs solo) — ✅ 5/5 testes
    - 17.6 Integração no coupling — ✅ 4/4 testes
    - 17.7 Estatísticas — ✅ 3/3 testes
    - 17.8 Regressão — ✅ 3/3 testes
    - Resultado: 42/42 testes, 113/113 regressão, todas as fases 100%
20. **FASE 18** (auto-referência recursiva) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
    - 18.1 Auto-modelo (estado cognitivo) — ✅ 10/10 testes
    - 18.2 Recursão (MCR observa MCR, converge) — ✅ 11/11 testes
    - 18.3 Auto-modificação (ajusta comportamento) — ✅ 9/9 testes
    - 18.4 Unidade do self (identidade) — ✅ 8/8 testes
    - 18.5 Reflexividade (meta-conhecimento) — ✅ 6/6 testes
    - 18.6 Strange loop (auto-referência, não consciência fenomênica) — ✅ 6/6 testes
    - 18.7 Integração no coupling — ✅ 6/6 testes
    - 18.8 Estatísticas — ✅ 5/5 testes
    - 18.9 Regressão — ✅ 3/3 testes
    - Resultado: 64/64 testes, 113/113 regressão, todas as fases 100%
21. **FASE 19 — ESCALA** (próxima fronteira) — 🔴 NÃO IMPLEMENTADA
    - 19.1 Acoplamento hierárquico em 100K+ observações — validar se mantém coerência
    - 19.2 Geração de 4000+ tokens sem colapsar — comparar vs LLM no mesmo corpus
    - 19.3 Comparação medida vs phi4-mini few-shot 5/ex no dataset_500 — Pilar 8
    - 19.4 Comparação medida vs phi4-mini zero-shot — referência "sem mesmo treino"
    - **Pré-requisito**: sem esta fase, qualquer claim de paridade com LLM em geração é hipótese (Pilar 8/9)

## Métricas de sucesso
| Fase | Métrica | Meta | Obtido | Status |
|---|---|---|---|---|
| 1 | Composição: "cachorro verde" closer de "cachorro" | >70% | 95.08% | ✅ |
| 1 | Composição: "correr rápido" closer de "correr" | >70% | 92.02% | ✅ |
| 1 | Negação: "não bom" closer de "ruim" | >70% | 50% | ✅ RESOLVIDO (100%) |
| 1 | Regressão zero-shot | 94.7% | 94.7% | ✅ |
| 1 | Regressão latência | <5ms | 3.65ms | ✅ |
| 2 | Relações extraídas corretas | >80% | 100% (15/15 testes) | ✅ |
| 3 | Raciocínio sobre estados | validar | 32/32 testes | ✅ |
| 4 | Contexto ambiental melhora accuracy | >96% | 33/33 testes | ✅ |
| 5 | Geração de 50+ tokens coerentes | validar | 27/27 testes (classificação) — ⚠️ flutua 26-27/27 | ⚠️ |
| 6 | Cross-modal: áudio↔texto matching | >60% | 47/47 testes (100%) — ⚠️ flutua 46-47/47 | ⚠️ |
| 1 | Negação: "não bom" closer de "ruim" | >70% | 100% (NMI=1.0) | ✅ |
| 7 | Confiança Posicional P0 | 113/113 | 113/113 = 100% | ✅ |
| 7 | EXP2 intenção zero-shot (v4.0 dizia 100%) | — | **50.0%** (corrigido v4.1) | ⚠️ conflito |
| 7 | Itens #11-30 implementados | 0/30 | 30/30 | ✅ |
| 8 | Accuracy com novas fontes | 94.7% | **100.0% (113/113)** | ✅ |
| 8 | Latência com 13 fontes | <10ms | 7.78ms | ✅ |
| 8 | Fases 1-4 sem regressão | 0 fail | 0 fail | ✅ |
| 8 | Confiança P0 estendida (I,E,TRN,CMP) | 112/113 | 113/113 | ✅ |
| 8 | Peso acao:* 4x em similaridade | 66.7% EXP1 | 100% EXP1 | ✅ |
| 8 | EXP1 similaridade semântica | 66.7% | **100% (15/15)** | ✅ |
| 8 | EXP2 intenção zero-shot (v4.0 dizia 100%) | 50.0% | **100% (12/12)** | ⚠️ confirmar |
| 8 | EXP3 composição | 100% | **100% (6/6)** | ✅ |
| 8 | EXP5 herança morfológica | 0% | **100% (7/7)** | ✅ |
| 9 | Few-shot sem retreino | 0% | **100% (4/4)** | ✅ |
| 9 | Geração longa coerente | 0% | **100% (3/3)** | ✅ |
| 9 | Raciocínio multi-etapa | 0% | **100% (3/3)** | ✅ |
| 9 | Conhecimento enciclopédico | 0% | **100% (5/5)** | ✅ |
| 10 | Observação (opt-in) | — | **100% (5/5)** | ✅ |
| 10 | Incerteza meta | — | **100% (3/3)** | ✅ |
| 10 | Calibração | — | **100% (5/5)** | ✅ |
| 10 | Veto ("não sei") | — | **100% (3/3)** | ✅ |
| 10 | Auto-diagnóstico | — | **100% (7/7)** | ✅ |
| 10 | Regressão sem meta | — | **100% (3/3)** | ✅ |
| 11 | Identificar gaps por entropia | — | **100% (4/4)** | ✅ |
| 11 | Gerar perguntas | — | **100% (3/3)** | ✅ |
| 11 | Buscar conhecimento | — | **100% (3/3)** | ✅ |
| 11 | Aprender (alimentar coupling) | — | **100% (2/2)** | ✅ |
| 11 | Verificar redução de H | — | **100% (2/2)** | ✅ |
| 11 | Ciclo completo | — | **100% (6/6)** | ✅ |
| 11 | Regressão | — | **100% (2/2)** | ✅ |
| 12 | Avaliar pesos 5D | — | **100% (5/5)** | ✅ |
| 12 | Evoluir (hill climbing) | — | **100% (7/7)** | ✅ |
| 12 | Aplicar/reverter | — | **100% (3/3)** | ✅ |
| 12 | Análise | — | **100% (5/5)** | ✅ |
| 12 | Integração coupling | — | **100% (5/5)** | ✅ |
| 12 | Regressão | — | **100% (3/3)** | ✅ |
| 13 | Confounders | — | **100% (4/4)** | ✅ |
| 13 | Intervir (do-calculus) | — | **100% (3/3)** | ✅ |
| 13 | Efeito causal | — | **100% (5/5)** | ✅ |
| 13 | Cadeia causal | — | **100% (5/5)** | ✅ |
| 13 | d-separação | — | **100% (5/5)** | ✅ |
| 13 | Integração coupling | — | **100% (6/6)** | ✅ |
| 13 | Estatísticas | — | **100% (1/1)** | ✅ |
| 13 | Regressão | — | **100% (3/3)** | ✅ |
| 14 | Contrafactual (Pearl 3º degrau) | — | **100% (9/9)** | ✅ |
| 14 | Necessidade causal | — | **100% (6/6)** | ✅ |
| 14 | Suficiência causal | — | **100% (6/6)** | ✅ |
| 14 | Cenários hipotéticos | — | **100% (4/4)** | ✅ |
| 14 | Propagação em cadeia | — | **100% (8/8)** | ✅ |
| 14 | Integração coupling | — | **100% (5/5)** | ✅ |
| 14 | Estatísticas | — | **100% (1/1)** | ✅ |
| 14 | Regressão | — | **100% (3/3)** | ✅ |
| 15 | Simular (prever futuros) | — | **100% (7/7)** | ✅ |
| 15 | Planejar (beam search) | — | **100% (8/8)** | ✅ |
| 15 | Avaliar plano (5D) | — | **100% (4/4)** | ✅ |
| 15 | Replanificar | — | **100% (5/5)** | ✅ |
| 15 | Heurísticas | — | **100% (5/5)** | ✅ |
| 15 | Integração coupling | — | **100% (5/5)** | ✅ |
| 15 | Estatísticas | — | **100% (1/1)** | ✅ |
| 15 | Regressão | — | **100% (3/3)** | ✅ |
| 16 | Modelar agente | — | **100% (7/7)** | ✅ |
| 16 | Predizer ação | — | **100% (7/7)** | ✅ |
| 16 | Atribuir crenças | — | **100% (10/10)** | ✅ |
| 16 | Crença falsa (Sally-Anne) | — | **100% (7/7)** | ✅ |
| 16 | Perspectiva + interação | — | **100% (10/10)** | ✅ |
| 16 | Integração coupling | — | **100% (5/5)** | ✅ |
| 16 | Estatísticas | — | **100% (2/2)** | ✅ |
| 16 | Regressão | — | **100% (3/3)** | ✅ |
| 17 | Observar domínio (clusters NMI) | — | **100% (5/5)** | ✅ |
| 17 | Criar especialista | — | **100% (7/7)** | ✅ |
| 17 | Compor (equipe automática) | — | **100% (7/7)** | ✅ |
| 17 | Orquestrar (rotear por NMI) | — | **100% (8/8)** | ✅ |
| 17 | Avaliar (composição vs solo) | — | **100% (5/5)** | ✅ |
| 17 | Integração coupling | — | **100% (4/4)** | ✅ |
| 17 | Estatísticas | — | **100% (3/3)** | ✅ |
| 17 | Regressão | — | **100% (3/3)** | ✅ |
| 18 | Auto-modelo | — | **100% (10/10)** | ✅ |
| 18 | Recursão (converge) | — | **100% (11/11)** | ✅ |
| 18 | Auto-modificação | — | **100% (9/9)** | ✅ |
| 18 | Unidade do self | — | **100% (8/8)** | ✅ |
| 18 | Reflexividade | — | **100% (6/6)** | ✅ |
| 18 | Strange loop | — | **100% (6/6)** | ✅ |
| 18 | Integração coupling | — | **100% (6/6)** | ✅ |
| 18 | Estatísticas | — | **100% (5/5)** | ✅ |
| 18 | Regressão | — | **100% (3/3)** | ✅ |

---

## FASE 20 — TRIUNVIRATO NAVEGADOR (v5.0 — mesa de design 2026-07-17)

**Status**: EM EXECUÇÃO | **Visão**: MCR navegador universal, não classificador melhor

### Origem — mesa de design
Sessão de design com o criador reformulou a visão do MCR. Descobertas:
1. O `decidir()` **já é triunvirato** — 13 fontes Markov votam, Entropia pondera por divergência JS, 5D avalia, meta-cog diz "não sei". Não falta diálogo — falta **o que fazer quando não há consenso**.
2. 3 peças já existem **desconectadas**: `acoplamento_hierarquico.py`, `base_conhecimento.py`, `feedback.py:WebLearn`. O trabalho é **conectar**, não inventar.
3. O humano é **4D** — alinha o triumvirato quando empata, é observado em isolamento (perfil biometal) E como fonte universal. O MCR **questiona** o humano, não só responde.
4. O 3 (Triunvirato) é o **espaço estável** (Markov+Entropia+5D, ninguém manda). O 4 (humano/chat) é o **vetor direção** que move o espaço no tempo.
5. Byte-level é a raiz universal — qualquer modalidade vira sequência de estados. O motor não pergunta origem. Pilar 7 ("P(feature|conceito)") é a ponte.
6. Consenso é **obrigatório** — não votação, não ditadura. Se os 3 discordam, buscam fatos. Se ainda, pedem humano (4D). A própria articulação do empate pode resolver.

### Arquitetura final

```
                   [Byte stream — universal, agnóstico]
                              ↓
              ╔══════════════════════════════════════════╗
              ║   TRIUNVIRATO                              ║
              ║                                           ║
              ║   Markov (13 fontes × N níveis hierárquicos)║
              ║      ↕                                    ║
              ║   Entropia (divergência JS mede consenso)  ║
              ║      ↕                                    ║
              ║   5D (avalia cada candidato)               ║
              ║      ↕                                    ║
              ║   Meta-cog (decide se pode responder)     ║
              ╚══════════════════════════════════════════╝
                              ↓ consensus?
              ┌──── NÃO (alta divergência) ────┐
              ↓                                 ↓
        [Busca Ativa Universal]            [4D — Chat]
        registry → todos consultam         explicar empate ao humano
        alimentar coupling                  (auto-explicação pode resolver)
        re-decidir()
              ↓ consensus?                       ↓
        → SIM: decide                       humano responde (entra como observação)
        → NÃO (após teto paciência):
          pedir feedback ao humano

                [Perfil Humano — observado em isolamento E universal]
                Nível K:   P(próxima_tecla | tecla_anterior)
                Nível K+1: P(teto_paciência | complexidade)
                Nível K+2: P(estilo | vocabulário)
                Cada nível emerge por auto-limitação entrópica
                LGPD: coleta só após consentimento explícito no coldstart
```

### 5 peças de implementação

#### Peça 1 — Tokenizador Universal (byte-level ativo)
- **O que muda**: `re.findall(r'[a-zà-ÿ0-9]{2,}')` removido. Qualquer stream → bytes → estados. Texto UTF-8, pixel RAW, sample de áudio, JSON de sensor — mesmo caminho.
- **Sem if/else**: o motor não pergunta origem. `alimentar(byte_stream, acao)` universal.
- **Peças a tocar**: `coupling.py` tokenização, `acoplamento_hierarquico.py _tokenizar_nivel()`, `adaptadores.py` (adaptadores opcionais por modalidade, não obrigatórios).
- **Validação**: `_regressao_fase1.py` (113/113 SEM REGRESSÃO), `test_fase18_auto_referencia.py` (64 PASS), teste com bytes de imagem.

#### Peça 2 — Loop de Busca Ativa + Aba de Pensamento
- **Gatilho (sem hardcoded)**: divergência JS média acima do tercil superior das divergências históricas (já calculado em `_superpor()`). Meta-cog "não posso responder" também dispara.
- **Ação**: `registry.listar()` consulta todas as fontes disponíveis (auto-descobertas) → alimenta coupling → re-decide.
- **Síncrona E assíncrona**: bloqueia até `teto_paciência/2` (aprendido do humano), depois retorna "estou pensando..." e continua em background. Quando consenso, puxa o gancho na conversa.
- **Aba de pensamento**: cada fonte publica contribuição no idioma do usuário. Painel inferior ao vivo no CLI. Comando `/pensamento` mostra histórico navegável.
- **Peças a tocar**: `coupling.py decidir()` (delega para novo `triunvirato_deliberar()` — A+B=C, não if/else), novo módulo `triunvirato.py`, `registry.py` (registrar BaseConhecimento/WebLearn/KnowledgeGraph no boot).
- **Validação**: teste com pergunta ambígua → busca ativa resolve em N segundos → aba mostra cada passo.

#### Peça 3 — Hierarquia conectada ao decidir()
- **O que muda**: `MCRHierarquico` deixa de ser standalone. Vira multiplicador: 13 fontes × N níveis hierárquicos.
- **Sem if/else "texto longo"**: `min_delta_h = 0.05` decide sozinho. Texto curto → 1 nível. Texto longo → emergem níveis.
- **Peças a tocar**: `coupling.py decidir()` (integra `MCRHierarquico.predizer()`), `acoplamento_hierarquico.py` (expor API estável), persistência (já existe `save/load`).
- **Validação**: regressão FASE 1 (113/113), teste com texto >50 palavras → níveis emergem automaticamente.

#### Peça 4 — Chat 4D Bidirecional + Perfil Humano + Coldstart
- **Coldstart adaptativo**: questionário semi-fixo (perguntas fundamentais) → MCR assume controle conforme ganha confiança → transição ao chat normal → MCR continua aprendendo.
- **Perfil humano (acoplamento hierárquico isolado)**: P(próxima_tecla|tecla_anterior), P(tempo_resposta|complexidade). Eventos capturados via stdin raw mode. Cada nível emerge por auto-limitação entrópica.
- **LGPD/Privacidade**: coleta de sinais comportamentais SÓ após consentimento explícito no questionário. Sem permissão, MCR funciona sem perfil — só texto.
- **Teto de paciência**: aprendido por conversação. MCR conversa **com** o humano sobre os tempos. P(abandona|tempo_espera). Não hardcoded.
- **MCR que questiona**: não só responde. Quando há lacuna, questiona ("você prefere dragão clássico ou original?") — aprende enquanto responde. Tudo que o humano diz (inclusive sobre o MCR) entra como observação.
- **Feedback humano só quando**: triunvirato não chega em consenso após busca ativa → MCR articula empate (auto-explicação pode resolver) → se persiste, pede feedback → humano responde → entra como observação.
- **Peças a tocar**: `chat.py` (refatorar `perguntar()` para bidirecional), novo `perfil_humano.py`, novo `coldstart.py`, CLI com stdin raw mode (Peça 5).
- **Validação**: coldstart com humano simulado → perfil emerge → teto ajusta → feedback dispara em empate real.

#### Peça 5 — CLI Leve (substitui Dashboard web quebrada)
- **O que muda**: `sse_server.py` (HTTP+HTML+threading, quebrado) substituído por CLI terminal, leve, estilo OpenCode.
- **Layout**: header compacto (estado MCR) + janela principal (conversa) + **painel inferior ao vivo** (aba de pensamento) + input no rodapé (captura timing de teclas).
- **Cross-platform**: Windows + Linux (descoberta automática de OS). Captura de teclas via stdin raw mode.
- **Comandos**: `/pensamento` (histórico deliberações), `/estado` (estatísticas), `/reset` (perfil humano), `/sair`.
- **Sem dependência pesada**: stdlib + `rich` (opcional, fallback texto puro). Sem FastAPI, sem HTTP, sem HTML.
- **Peças a tocar**: novo `mcr_cli.py` no raiz, `chat.py` expõe API estável, captura timing via stdin raw mode (Windows+Linux), painel consome eventos do `triunvirato.py`.
- **Validação**: rodar `python mcr_cli.py`, simular pergunta ambígua, ver painel atualizar em tempo real.

### Ordem de execução
1. **Peça 1** (tokenizador universal) — base de tudo
2. **Peça 3** (hierarquia conectada) — independente, pode testar isolado
3. **Peça 2** (busca ativa + aba de pensamento) — depende de Peça 3, fornece eventos para Peça 5
4. **Peça 4** (chat 4D + perfil humano + coldstart) — independente do CLI
5. **Peça 5** (CLI leve) — consome tudo

### Homologação final (após cada peça)
- `_regressao_fase1.py` — 113/113 SEM REGRESSÃO, latência <10ms
- `test_fase18_auto_referencia.py` — 64 PASS / 0 FAIL
- Novos testes por peça

### Verdades estabelecidas na mesa (regime honesto, Pilar 9)
1. **MCR 100% no dataset_500 = memorização**. Dataset é sintético (template script), MCR testa no que aprendeu. Não prova superioridade — prova classificação no-domínio.
2. **"Semântica" rotulada era morfologia**. `semantic_router.similaridade()` = overlap de caracteres. "cachorro"≈"perro" falha; "criar"≈"destruir" falso-positivo. Herança morfológica funciona (validada). Semântica real (significado) NÃO existe — é hipótese do Pilar 7 não implementada.
3. **LLM generaliza, MCR conta**. Ambos memorizam: MCR lossless pequeno, LLM lossy massivo. Dizer "MCR observa, LLM decora" é falso — dizer "MCR conta exato, LLM comprime aproximado" é verdade.
4. **Markov é forward-only**. "Vê presente para entender passado" precisa de smoothing Bayesiano, não Markov puro. Mas hierarquia recursiva estende o horizonte (20→400→8000→... passos), resolvendo o limite de 20 tokens.
5. **Entropia baixa com poucos dados = ignorância, não certeza**. 1 observação → P=1.0, H=0 — overconfident. A entropia deve ser interpretada como ignorância quando amostra é pequena.
6. **MCR vence por construção em**: latência, custo, explicabilidade, aprendizado online, zero GPU, portabilidade. Independente de baseline.
7. **MCR pode vencer por qualidade em**: ambiente novo (aprende em tempo real), classificação com corpus pequeno (memorização lossless), nichos onde O(1) importa.
8. **MCR perde por limite arquitetural em**: conhecimento geral (começa vazio), geração longa sem hierarquia validada em escala, criatividade (zero invenção = zero hallucination).
9. **O objetivo não é "superar LLM" — é ser categoria diferente**. Navegador observador vs compressor memorizador. Caixa de vidro vs caixa preta.
