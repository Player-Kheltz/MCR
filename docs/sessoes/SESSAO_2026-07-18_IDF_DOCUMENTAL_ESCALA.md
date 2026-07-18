# SESSAO 2026-07-18 — IDF DOCUMENTAL + LOOP AUTO-TREINAMENTO + ESCALA 69K + JSD

## Objetivos da sessao
1. Fix loop de auto-treinamento (estava quebrado)
2. Fase B2b: escalar corpus multi-idioma para 50K+ obs
3. Validar discriminacao semantica跨-idioma em escala
4. Fix extrair_relacoes (retornava datas/perguntas como sinonimos)
5. Fix latencia outlier 5000ms na primeira chamada

## Problema 1: Loop de auto-treinamento quebrado

### Sintoma
"o que e python" → "nao sei" → "python e uma linguagem..." → nao aprendia (respondia "pergunta: qual contexto?")

### Diagnostico
1. NMI morfologico (`_nmi`) entre "o que e python" e "python e uma linguagem de programacao" = 0.9351
2. Threshold do historico = 0.9789 (inflado por entradas curtas do coldstart: "sim", "Kheltz" geram NMI~1.0 entre si)
3. Logica invertida: NMI alto = "mesma coisa = explicacao" — mas NMI alto significa MESMA ESTRUTURA ("o que e X"), nao mesma semantica

### Solucao: IDF + palavra-chave + palavras novas
Criterio MCR-puro para detectar explicacao vs nova pergunta:
1. **Palavra-chave** = palavra de maior IDF na pergunta (palavra mais rara = mais informativa)
2. **Palavra-chave presente** na entrada (a entrada e relacionada a pergunta)
3. **Mais palavras novas que compartilhadas** (a entrada traz mais informacao nova do que repete)

### Resultado
- python/javascript/rust: todos aprendidos em runtime ✅
- "nao sei" → humano explica → "obrigado! aprendi algo novo." → proxima pergunta respondida

## Problema 2: Discriminacao semantica falha em escala

### Sintoma
Corpus B2a (4K obs, 50 conceitos): delta = 0.20 PASS
Corpus B2b (57K obs, 70 conceitos): delta = -0.03 FAIL (INVERTIDO!)

### Diagnostico
- Sinonimos跨-idioma (cachorro-dog = 0.84) tinham NMI MAIS BAIXO que nao-relacionados mesmo-dominio (cachorro-gato = 0.93)
- Motivo: cachorro-gato compartilham mais planos ctx: (mesmas props em PT + templates PT) que cachorro-dog (props em PT mas templates em EN)
- IDF por frequencia (`log(total/freq_palavra)`) melhorou de -0.03 para +0.03 mas ainda FAIL

### Solucao: IDF documental + IDF²
1. **IDF documental**: `df(token) = |{w : token in ctx(w)}|` — quantas palavras tem o token como contexto
   - IDF = `log(N_palavras / df)`
   - "late" (6 palavras tem como ctx) → IDF=4.3 (alto, discriminativo)
   - "tem" (271 palavras) → IDF=0.49 (baixo, nao discrimina)
   - "associado" (214 palavras, template PT) → IDF=0.73 (baixo, nao discrimina)
2. **IDF²**: amplifica a diferenca entre palavras raras e comuns
   - IDF²("late") = 18.5; IDF²("tem") = 0.24 — ratio 77x
   - IDF("late") = 4.3; IDF("tem") = 0.49 — ratio 8.8x
3. Cache do IDF documental (`_cache_idf_doc`) invalidado a cada `alimentar()`

### Resultado
| Corpus | IDF | Sinonimos | Nao-relacionados | Delta | Veredito |
|--------|-----|-----------|-----------------|-------|----------|
| B2a (4K, 50 conc) | nenhum | 0.853 | 0.649 | 0.203 | PASS |
| B2b (57K, 70 conc) | nenhum | 0.865 | 0.894 | -0.030 | **FAIL (invertido!)** |
| B2b (57K, 70 conc) | freq | 0.884 | 0.854 | 0.030 | FAIL |
| B2b (57K, 70 conc) | IDF doc | 0.906 | 0.795 | 0.111 | FAIL (quase) |
| **B2b (57K, 70 conc)** | **IDF² doc** | **0.935** | **0.678** | **0.257** | **PASS** |

Motor principal (68960 obs): delta geral = 0.165 PASS; delta sin-mesmo = 0.128, delta sin-cross = 0.183

## Problema 3: Fluxo chat quebrado em scala

### Sintoma
Apos ingerir corpus B2b (50000 obs), CLI voltou a falhar:
- "o que e python" → "descrever" (acao em vez de resposta)
- "python e uma linguagem..." → "pergunta: qual contexto?" (nao aprendia)

### Diagnostico
- Corpus B2b treina acao "descrever" para todas as observacoes
- `decidir("o que e python")` → acao="descrever" (nao "responder")
- Fluxo antigo so admitia ignorancia se `acao == 'responder'`
- Logo: nunca chegava a `_ultima_ignorancia`, loop de auto-treinamento nao ativava

### Solucao: BC sempre primeiro + ignorancia para acoes de chat
1. BC tentado PRIMEIRO, independente da acao predita (Pilar 5)
2. Se BC nao encontra, admite ignorancia para acoes de chat (`responder`, `descrever`, `explicar`, etc.)
3. Acoes de jogo (`gerar_monstro`, etc.) seguem fluxo normal

### Resultado
CLI completo funcional mesmo com 69K obs:
- python/javascript/rust: aprendidos em runtime ✅
- cachorro/agua/amor/dia/nome: BC responde ✅
- Latencia: 10-6000ms (outliers em primeira pergunta e apos aprendizado)

## Alteracoes nos arquivos

### `mcr/coupling.py`
- `_nmi_semantico` (`:1726`): IDF² documental em planos ctx:
  - Cache `_cache_idf_doc`: df(token) = |{w : token in ctx de w}|
  - `pesos[k] = max(idf, 0.01)² ²` para planos ctx:
  - Planos nao-ctx mantem peso 1
- `alimentar` (`:209`): invalida `_cache_idf_doc = None` no final
- Guard `max(0.0, ha)` no sqrt para evitar ValueError de entropia negativa

### `mcr/chat.py`
- `_nmi_semantico` nao usado mais no loop auto-treinamento (NMI morfologico nao discrimina explicacao)
- Loop auto-treinamento (`:177`): IDF + palavra-chave + palavras novas
  - IDF da palavra-chave = `log(total / max(freq, 1))` (do coupling)
  - Criterio: `palavra_chave in pal_entr AND len(pal_novas) > len(pal_compart)`
- Fluxo chat (`:237`): BC sempre primeiro + ignorancia para acoes de chat

### `tools/corpus_multilingue.py`
- 4 novos dominios: tecnologia, comida, lugares, plantas (25 novos conceitos, total 70)
- `gerar_corpus` agora usa todos os 10 templates (antes 3) e reps=3 (antes 1)
- Geracao: 57240 obs (50K limitadas)

## Problema 4: extrair_relacoes retornava lixo

### Sintoma
```
cachorro → sinonimos: [('17/07/2026', 0.475)]  ← DATA como sinonimo
casa     → sinonimos: [('estamos?', 0.745)]    ← pergunta de coldstart
cachorro → meronimos:  [('has', 1.0), ('tiene', 1.0)]  ← verbos de ligacao
```

### Diagnostico
1. `score_sin = nmi_full * 1/(1+log(freq))` — ponderacao por freq REDUNDANTE e INVERTIDA
   - dog (freq=900) → fator 0.128 → score BAIXO
   - 17/07/2026 (freq=1) → fator 1.0 → score ALTO
   - Mas _nmi_semantico com IDF² ja discrimina — ponderar de novo inverte a ordem
2. Bug mi > denom: `mi = ha + hb - hab` onde hab = entropia da soma das distribuicoes
   - Quando distribuicoes sao disjuntas (0 chaves compartilhadas), mi > 0 (INCORRETO)
   - mi deveria ser 0 para disjuntas, mas hab < ha + hb quando uma distribuição domina
   - NMI = mi/denom > 1.0 → clampado para 1.0 → tudo parece sinonimo

### Solucao: JSD + score_sin direto
1. **score_sin = nmi_full** (sem ponderacao por freq — IDF² ja discrimina)
2. **NMI baseado em Jensen-Shannon divergence**:
   - JSD = H(M) - (H(P) + H(Q))/2, onde M = (P+Q)/2
   - NMI = 1 - JSD/sqrt(H(P)*H(Q))
   - Quando P=Q: JSD=0, NMI=1
   - Quando disjuntas: JSD alto, NMI baixo (nunca > 1)
3. Meronimos: filtrar por IDF documental mediano (remove verbos de ligacao)

### Resultado
```
cachorro → sinonimos: perro (0.96), dog (0.94), cavalo (0.86)
amor     → sinonimos: love (0.92), alegria (0.92), tristeza (0.93)
casa     → sinonimos: house (0.90), ciudad (0.85), bosque (0.85)
arvore   → sinonimos: arbol (0.93), tree (0.90), grama (0.84)
```

## Problema 5: Latencia outlier 5000ms na primeira chamada

### Sintoma
"o que e python" = 5002ms na primeira chamada (depois 26ms medio)

### Diagnostico
_cache_idf_doc era construido lazy (na primeira chamada do _nmi_semantico).
Como extrair_relacoes chama _nmi_semantico para cada uma das 949 palavras,
a primeira chamada paga o custo de iterar sobre todas as _transicao_palavra.

### Solucao: Pre-construir _cache_idf_doc no load()
```python
# No final do load():
self._cache_idf_doc = {}
self._cache_idf_total = len(self._palavra_acao) or 1
for w in self._transicao_palavra:
    for ctx_token in self._transicao_palavra[w]:
        self._cache_idf_doc[ctx_token] = self._cache_idf_doc.get(ctx_token, 0) + 1
```

### Resultado
"o que e python" = 212ms na primeira chamada (antes 5002ms) — 23x mais rapido

## Regressoes
- FASE 1: 113/113 = 100% (latencia 25-27ms)
- FASE 18: 64/64 = 100%
- Sem regressao em todas as mudancas

## Estado final
- Motor principal: 68960 obs, 810 palavras, 14 acoes
- Discriminacao semantica跨-idioma: delta=0.164 PASS em escala 69K
- extrair_relacoes: cachorro→perro/dog, amor→love, casa→house, arvore→arbol/tree
- Loop de auto-treinamento funcional: python, javascript, rust aprendidos em runtime
- BC responde: cachorro, agua, cadeira, amor, vermelho, dia, nome, MCR (8+ conceitos)
- Backup pre-B2b: `cache/coupling_MCRCoupling_backup_preB2b.json` (18960 obs)
