# PLANO MCR — Roteiro de Evolução Cognitiva
**Versão**: 2.1 | **Data**: 2026-07-16 | **Status**: FASE 1 implementada e validada

## Objetivo
Transformar MCR de classificador (94.7% zero-shot, 3ms) em cognição completa:
composicional, hierárquica, fundamentada no mundo, multimodal.

## Princípios inegociáveis
- Markov 1ª ordem + Entropia Shannon + NMI = base de tudo
- Zero GPU, zero dependências externas, zero listas hardcoded
- Performance: decisão em <5ms, sensores em background
- Universal: qualquer idioma, qualquer domínio, qualquer modalidade

---

## FASE 1 — Composição (Gateway)
**Status**: IMPLEMENTADA e VALIDADA (2026-07-16)
**Esforço**: médio | **Impacto**: muito alto

### Resultados reais
| Métrica | Meta | Obtido | Status |
|---|---|---|---|
| "cachorro verde" closer de "cachorro" | >70% | 95.08% | supera |
| "correr rápido" closer de "correr" | >70% | 92.02% | supera |
| "não bom" closer de "ruim" (negação) | >70% | 50% (empate) | limitação FASE 2 |
| Accuracy zero-shot (regressão) | 94.7% | 94.7% (107/113) | idêntico |
| Latência (regressão) | <5ms | 3.65ms | ok |

### 1.1 Operador `compor(sig_a, sig_b)` — IMPLEMENTADO
Decisão automática por NMI entre assinaturas:
- NMI >= 0.1 → modificação (A é base, B restringe)
- NMI < 0.1 → complemento (uniao, conceitos independentes)

Regra original (entropia marginal) foi refutada: confundia polissemia
com generalidade. "rápido" tinha H maior que "correr" por ser mais
polissêmico, não por ser mais geral — levava a "complemento" errado.

### 1.2 `_assinatura_frase()` — IMPLEMENTADO
Quebra frase em palavras, compõe recursivamente via `compor()`.

### 1.3 `similaridade()` — ATUALIZADO
Detecta frases multi-palavra (regex 3+ chars) e usa `_assinatura_frase`
ao invés de `_assinatura_palavra`. Palavras únicas: comportamento idêntico.

### Limitação conhecida: negação
"não bom" não se aproxima de "ruim" porque `alimentar()` pega "bom"
como palavra isolada em "não bom inimigo" e associa bom+inimigo,
poluindo a assinatura. Solução: FASE 2 precisa de dados onde
"não X" é rotulado como oposto de X, OU alimentar() precisa usar
_assinatura_frase durante o treino (mudança maior).

---

## FASE 2 — Extrator de Relações
**Status**: pronto para implementar
**Esforço**: médio | **Impacto**: alto

### 2.1 Extrair relações da matriz existente
Tudo já está em `_transicao_palavra` e `_palavra_acao`. Só precisa de operadores de extração:

```python
def extrair_relacoes(self, palavra):
    sig = self._assinatura_palavra(palavra)
    return {
        "sinonimos": [p for p in self._palavra_acao 
                      if p != palavra and self._nmi(sig, self._assinatura_palavra(p)) > 0.7],
        "antonimos": [p for p in self._palavra_acao 
                      if p != palavra and self._nmi(sig, self._assinatura_palavra(p)) < 0.1
                      and self._mesma_categoria(palavra, p)],  # mesmo cluster mas NMI baixo
        "hiperonimos": [p for p, dist in self._transicao_palavra.get(palavra, {}).items()
                        if sum(dist.values()) > threshold],  # "cachorro"→"animal"
        "hiponimos": [p for p, dist in self._transicao_palavra.items()
                        if palavra in dist and sum(dist.values()) > threshold],
        "meronimos": [p for p in self._transicao_palavra.get(palavra, {})
                        if self._nmi(sig, self._assinatura_palavra(p)) > 0.3
                        and len(p) < len(palavra)],  # parte-de: menor
    }
```

### 2.2 Detecção de antônimos (insight)
Antônimos = mesmo cluster (mesma categoria semântica) MAS NMI baixo.
"bom" e "ruim" ambos aparecem com "qualidade", "avaliação", "julgamento" — mesmo cluster.
Mas NMI entre eles é 0.00 — distribuições opostas.
**Critério: mesmo cluster + NMI < 0.1 = antônimos.**

### 2.3 Lista universal de relações a descobrir
| Relação | Como MCR descobre | Dados necessários |
|---|---|---|
| Sinônimos | NMI > 0.7 | co-ocorrência |
| Antônimos | mesmo cluster + NMI < 0.1 | co-ocorrência |
| Hiperônimos | A→B frequente em _transicao | co-ocorrência |
| Hipônimos | B→A frequente (inverso) | co-ocorrência |
| Merônimos | NMI médio + A maior que B | co-ocorrência |
| Holônimos | inverso de merônimo | co-ocorrência |
| Causa | A→B onde B é estado/resultado | pares (ação,resultado) |
| Polissemia | H alta em _palavra_acao[palavra] | co-ocorrência |
| Negação | "não A" inverte distribuição de A | pares (texto,ação) |
| Metáfora | NMI médio entre domínios distantes | cross-domain |

**Todas descobertas por entropia. Zero rótulos.**

---

## FASE 3 — Grounding Simbólico
**Status**: pronto para implementar
**Esforço**: baixo | **Impacto**: médio

### 3.1 Alimentar com pares (texto, estado_do_mundo)
```python
coupling.alimentar("fogo", '{"temp":200,"dano":5,"cor":"vermelho"}')
coupling.alimentar("gelo", '{"temp":-5,"dano":0,"cor":"branco"}')
```

### 3.2 Raciocínio sobre estados
```python
# MCR aprende: fogo + gelo → temperatura média
# Via NMI: sig("fogo") ∩ sig("gelo") → conceito compartilhado = "temperatura"
# P(temp_media | fogo, gelo) aprendido das observações
```

### 3.3 Grounding via Tibia (ambiente simulado real)
Tibia já tem estado do mundo mensurável:
- NPCs: posição, vocação, level, itens
- Monstros: HP, dano, elemento, loot
- Mapa: coordenadas, tipo de terreno
- Combate: dano causado, elemento, resistência

```python
coupling.alimentar(
    "o mago atacou com fogo",
    '{"ator":"mago","acao":"atacar","elemento":"fogo","dano":150,"mana":-30}'
)
```

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
2. **FASE 2** (relações) — dados já estão, só extrair
3. **FASE 3** (grounding simbólico) — código existe, só dados
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
| 2 | Relações extraídas corretas | >80% | — | pendente |
| 3 | Raciocínio sobre estados | validar | — | pendente |
| 4 | Contexto ambiental melhora accuracy | >96% | — | pendente |
| 5 | Geração de 50+ tokens coerentes | validar | — | pendente |
| 6 | Cross-modal: áudio↔texto matching | >60% | — | pendente |
