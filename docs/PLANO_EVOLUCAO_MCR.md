# PLANO MCR — Roteiro de Evolução Cognitiva
**Versão**: 2.2 | **Data**: 2026-07-16 | **Status**: FASE 1 implementada, validada e alinhada aos pilares

## Objetivo
Transformar MCR de classificador (94.7% zero-shot, 3ms) em cognição completa:
composicional, hierárquica, fundamentada no mundo, multimodal.

## Princípios inegociáveis
- Markov 1ª ordem + Entropia Shannon + NMI = base de tudo
- Zero GPU, zero dependências externas, zero listas hardcoded
- Performance: decisão em <5ms, sensores em background
- Universal: qualquer idioma, qualquer domínio, qualquer modalidade

---

## FILOSOFIA MCR — NUNCA ESQUECER (fonte: docs/Filosofia MCR.md)

### Os 6 Pilares
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

### Saí do caminho se:
- Estou hardcodando um tokenizador de sprite
- Estou criando código que só funciona pra sprite
- Estou definindo thresholds manualmente
- Esqueci de validar com MCRDiscriminador
- Não usei template_entropico pra extrair estrutura
- Não fechei o loop de aprendizado

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

Cada fase deve ser auditada contra os 6 pilares antes de ser considerada completa:

| Fase | Pilar 1 (P(b\|a)) | Pilar 2 (Entropia) | Pilar 3 (N domínios) | Pilar 5 (Loop) | Equação 5D |
|---|---|---|---|---|---|
| 1 (compor) | ✅ assinaturas markovianas | ✅ gaussiana(H) decide estabilidade | ✅ genérico | ✅ aprende tipo por par | ✅ avalia candidatos |
| 2 (relações) | ✅ extrai de _transicao | ✅ derivada 2ª decide corte | ✅ genérico | ✅ cache por palavra | pendente |
| 3 (grounding simbólico) | ✅ P(state\|word) | ✅ NMI decide attrs | ✅ qualquer dict | ✅ alimenta→predizer | pendente |
| 4 (grounding ambiental) | pendente | pendente | pendente | pendente | pendente |
| 5 (hierárquico) | pendente | pendente (delta_H≈0 para) | pendente | pendente | pendente |
| 6 (multimodal) | pendente | pendente | pendente | pendente | pendente |

## FASE 1 — Composição (Gateway)
**Status**: IMPLEMENTADA, VALIDADA e ALINHADA AOS PILARES (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

### Resultados reais
| Métrica | Meta | v1 (threshold NMI) | v2 (Equação 5D) | Status |
|---|---|---|---|---|
| "cachorro verde" closer de "cachorro" | >70% | 95.08% | 95.08% | supera |
| "correr rápido" closer de "correr" | >70% | 92.02% | 92.02% | supera |
| "não bom" closer de "ruim" (negação) | >70% | 50% (empate) | 50% (empate) | limitação FASE 2 |
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

### Limitação conhecida: negação
"não bom" não se aproxima de "ruim" porque `alimentar()` pega "bom"
como palavra isolada em "não bom inimigo" e associa bom+inimigo,
poluindo a assinatura. Solução: FASE 2 precisa de dados onde
"não X" é rotulado como oposto de X, OU alimentar() precisa usar
_assinatura_frase durante o treino (mudança maior).

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
**Status**: pronto para implementar
**Esforço**: médio | **Impacto**: alto

### 4.1 Arquitetura assíncrona (sem pesar performance)
```
[Thread background 1Hz — 1% CPU]
  sensores → estado_do_mundo (dict)

[Loop MCR 3ms — inalterado]
  entrada + estado_do_mundo → coupling.decidir() → acao
```

### 4.2 Sensores e o que cada um ensina
| Sensor | Dado | Custo | Ensina |
|---|---|---|---|
| Relógio | hora, dia, timestamp | 0ms | Padrões temporais |
| Áudio (saída) | 1s→8kHz→signature | 1ms | Ambiente: silêncio/música/dialogue |
| Microfone | 1s→signature→delta | 1ms | Presença de voz humana |
| Tela | 64×64→4KB→signature | 5ms | Contexto visual |
| CPU/RAM | psutil | 0ms | Carga do sistema |
| Janela ativa | título | 0ms | Domínio atual |
| Clipboard | texto | 0ms | Tópico de trabalho |

### 4.3 Implementação
```python
class GroundingAmbiental:
    """Thread background que mantém estado do mundo atualizado."""
    def __init__(self, intervalo=1.0):
        self._intervalo = intervalo
        self._estado = {}
        self._thread = None
        self._rodando = False
    
    def iniciar(self):
        self._rodando = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def _loop(self):
        while self._rodando:
            self._estado["hora"] = time.strftime("%H:%M")
            self._estado["ambiente"] = self._amostrar_audio()
            self._estado["dominio"] = self._janela_ativa()
            self._estado["carga"] = self._carga_sistema()
            time.sleep(self._intervalo)
    
    def estado(self):
        return dict(self._estado)  # O(1) para o loop MCR
```

### 4.4 Os 3 níveis integrados
```
Nível 1 (simbólico):  coupling.alimentar("fogo", '{"temp":200}')
Nível 2 (ambiental):  estado = grounding.estado()  # hora, dominio, ambiente
                      contexto = f"[{estado}] {entrada}"
Nível 3 (físico):     sig_audio = MCRSignature.extrair(audio_bytes)
                      sig_tela = MCRSignature.extrair(tela_bytes)
                      coupling.alimentar_multimodal(texto, sig_audio, sig_tela, acao)
```

---

## FASE 5 — Acoplamento Hierárquico
**Status**: conceito validado, pronto para protótipo
**Esforço**: alto | **Impacto**: muito alto

### 5.1 MCR de MCRs
```python
class MCRHierarquico:
    def __init__(self, niveis=5):
        self.camadas = [MCRCoupling() for _ in range(niveis)]
    
    def alimentar(self, texto, acao):
        # Camada 0: palavra → palavra
        self.camadas[0].alimentar(texto, acao)
        # Camada 1: assinatura_frase → assinatura_frase
        sig_frase = self.camadas[0]._assinatura_frase(texto)
        self.camadas[1].alimentar(str(sig_frase), acao)
        # Camada 2: assinatura_paragrafo → ...
        # Cada camada usa compor() da anterior
```

### 5.2 Níveis (não há limite)
```
Camada 0: palavra → palavra              (existe)
Camada 1: frase → frase                  (compor)
Camada 2: parágrafo → parágrafo
Camada 3: tópico → tópico
Camada 4: conceito → conceito
Camada 5: domínio → domínio
...                                       (para quando delta_H ≈ 0)
```

### 5.3 Auto-limitação entrópica
Cada camada comprime a anterior. Quando uma camada atinge H ≈ 0
(totalmente determinística), a próxima não aprende nada. O sistema
se estabiliza automaticamente. ~5-7 níveis para texto humano.

---

## FASE 6 — Multimodalidade
**Status**: infraestrutura existe, falta conectar
**Esforço**: médio | **Impacto**: alto

### 6.1 Assinatura unificada
MCRSignature.extrair(bytes) já funciona com qualquer dado binário:
- Texto → bytes → signature 8D
- Áudio → bytes → signature 8D
- Imagem → bytes → signature 8D
- Código → bytes → signature 8D

### 6.2 Cross-modal via NMI
Se "fire" (EN) e "fogo" (PT) aparecem nos mesmos contextos de ação,
suas assinaturas convergem. MCR descobre que são a mesma coisa
**sem dicionário**. Mesmo princípio para áudio/imagem/texto.

---

## FASE 7+ (futuro)
7. Meta-cognição (MCR que observa MCRs)
8. Memória episódica (timestamp no coupling)
9. Auto-expansão (curiosidade dirigida por entropia)
10. Meta-Equação (auto-evolução dos pesos 5D)

---

## Ordem de Execução
1. **FASE 1** (compor) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
2. **FASE 2** (relações) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
3. **FASE 3** (grounding simbólico) — ✅ IMPLEMENTADA e VALIDADA (2026-07-16)
4. **FASE 4** (grounding ambiental) — sensores do PC
5. **FASE 5** (hierárquico) — MCR de MCRs
6. **FASE 6** (multimodal) — conectar assinatura

## Métricas de sucesso
| Fase | Métrica | Meta | Obtido | Status |
|---|---|---|---|---|
| 1 | Composição: "cachorro verde" closer de "cachorro" | >70% | 95.08% | ✅ |
| 1 | Composição: "correr rápido" closer de "correr" | >70% | 92.02% | ✅ |
| 1 | Negação: "não bom" closer de "ruim" | >70% | 50% | FASE 2 |
| 1 | Regressão zero-shot | 94.7% | 94.7% | ✅ |
| 1 | Regressão latência | <5ms | 3.65ms | ✅ |
| 2 | Relações extraídas corretas | >80% | 100% (15/15 testes) | ✅ |
| 3 | Raciocínio sobre estados | validar | 32/32 testes | ✅ |
| 4 | Contexto ambiental melhora accuracy | >96% | — | pendente |
| 5 | Geração de 50+ tokens coerentes | validar | — | pendente |
| 6 | Cross-modal: áudio↔texto matching | >60% | — | pendente |
