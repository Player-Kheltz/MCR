# Diagnostico Comparativo — MCR vs. Baselines Reais

> 16/19 testes passam. 3 falham com causas conhecidas.
> Dados reais, não teoria. Gerado em 2026-07-03.

---

## Sumario

1. [O Teste](#1-o-teste)
2. [Resultado Geral](#2-resultado-geral)
3. [O Que Funciona (16/19)](#3-o-que-funciona-1619)
4. [O Que Falha (3/19) — Causas e Correcoes](#4-o-que-falha-319--causas-e-correcoes)
5. [Comparacao com Sistemas Estabelecidos](#5-comparacao-com-sistemas-estabelecidos)
6. [Plano de Correcao](#6-plano-de-correcao)

---

## 1. O Teste

Arquivo: `E:/MCR/test_mcr_comparativo.py`

11 testes comparando MCR contra baselines simples e deterministicos:

| Teste | MCR testado | Baseline | O que mede |
|-------|-----------|----------|-----------|
| 1 | Markov | Moda (mais frequente) | Predicao de sequencia |
| 2 | Entropia | Confianca de predicao | Deteccao de anomalia |
| 3 | MCRNLP | Aleatorio (1/N) | Classificacao NLP |
| 4 | MCRWorld | — | Predicao de estado |
| 5 | MCRMemory | — | Memoria por similaridade |
| 6 | MCRPlanner | Random walk | Planejamento |
| 7 | Fingerprint | 8D fixo | Separacao de padroes |
| 8 | MCRQLearn | 50x random | Convergencia RL |
| 9 | MCREntropia | — | Deteccao de mudanca |
| 10 | MCRAutoEvolution | — | Impacto real de mutacao |
| 11 | MCRHDCOperation | — | Analogia |

---

## 2. Resultado Geral

```
Total:  16/19 = 84%
Tempo:  0.27s
```

---

## 3. O Que Funciona (16/19)

### 3.1 Predicao de sequencia — 100%

```
Sequencia ABCDEFGHIJ ×3
MCR Markov:     29/29 = 100%
Baseline moda:  29/29 = 100%
```

**Conclusao:** Markov e moda empatam em sequencias deterministicas. Ambos acertam tudo.
MCR nao e pior que o baseline — mas tambem nao e melhor. Para sequencias com memoria
de longo prazo (ex: ABABAB...), Markov falharia onde HTM TM acertaria.

### 3.2 Deteccao de anomalia — Funciona

```
Entropia de estados normais:  0.0000
Entropia de estado anomalo X: 1.0000
Confianca de estados normais: 1.0000
Confianca de X:               0.0000
```

**Conclusao:** A entropia detecta perfeitamente estados nunca vistos.
Equivalente funcional ao anomaly score do HTM.

### 3.3 Classificacao NLP — 70% (4x melhor que aleatorio)

```
MCR NLP:        21/30 = 70%
Baseline aleat: 1/6  = 17%
Frases fora do vocabulario: 3/5 corretamente ignoradas
```

**Conclusao:** MCRNLP classifica 4x melhor que aleatorio. Mas 70% e baixo para
padroes da industria (word2vec: ~95%). A limitacao e Jaccard byte-level —
nao captura sinonimos ou parafrase.

### 3.4 Predicao de estado — Funciona

```
Heroi: x=0 → x=1 (movimento andar_dir)
Acao predita: "andar_dir" (correta)
```

### 3.5 Memoria — Funciona

```
10 estados salvos → 3 similares encontrados por fingerprint
```

### 3.6 Dimensionalidade ideal MELHOR que 8D fixo

```
Par                             8D         dim_ideal   Melhoria
"quero" vs "nao quero"          19%        70% (64D)   3.7x
"cachorro morde homem" vs inv   6.2%       72% (128D)  11.6x
"gato" vs "cachorro"            56%        65% (64D)   1.1x
"sim" vs "nao"                  67%        100% (64D)  1.5x
```

**Conclusao:** `MCRSignatureExpansiva.dimensionalidade_ideal()` sempre encontra
dimensao melhor que 8D fixo. A melhoria media e 4.5x na separacao.

### 3.7 Deteccao de mudanca por entropia — Funciona

```
Entropia antes:   0.0000  (padrao AA, AA, AA...)
Entropia durante: 0.7219  (introduz AB, confusao)
Entropia depois:  0.5033  (volta AA, mas memoria do B permanece)
```

**Conclusao:** A entropia SOBE quando o padrao muda e DESCE quando estabiliza.
Funciona como detector de mudanca de regime (change point detection).

### 3.8 Analogia HDC — Acertou "mulher"

```
analogia("rei", "homem", "rainha", ["mulher", "rainha", "princesa", "dama", "menina"])
→ "mulher" (conf=0.583)
```

**Conclusao:** A algebra HDC do MCR acertou a analogia "rei - homem + rainha ≈ mulher"
com confianca 0.583. Isso e SURPREENDENTE para fingerprint 8D — a similaridade
de bytes entre "homem" e "mulher" (compartilham 'm', 'e', 'm') deve ter contribuido.

---

## 4. O Que Falha (3/19) — Causas e Correcoes

### FALHA 1: MCRPlanner — Plano vazio

**Dados:**
```
Grid 5x5, heroi (0,0) → objetivo (4,4)
Distancia Manhattan: 8
Plano MCR: 0 acoes  ← FALHOU
```

**Causa raiz:** `MCRPlanner.plano()` usa `MCRWorld.distancia()` que compara
fingerprint 8D dos estados completo. Fingerprint de EstadoMundo com heroi
em (0,0) vs (4,4) tem cosseno ≈ 0.9. Em 8D, a diferenca de 8 posicoes no grid
e irrelevante no fingerprint. O planner conclui que ja esta no objetivo.

**Correcao:** Substituir `fingerprint()` por `distancia_manhattan()` para
medir distancia entre estados:
```python
def distancia_manhattan(self, a, b):
    ha = a.get("heroi")
    hb = b.get("heroi")
    if not ha or not hb: return 99
    return abs(ha.props.get("x",0)-hb.props.get("x",0)) + \
           abs(ha.props.get("y",0)-hb.props.get("y",0))
```

### FALHA 2: MCRQLearn — Pior que random walk

**Dados:**
```
Acoes aprendidas: → → → ← → ← (heroi oscila no eixo x, nunca desce)
Distancia final QL:  6
Melhor random (50x): 2
```

**Causa raiz:** `MCRReward.avaliar()` usa `similaridade_cosseno(fingerprint(estado_atual),
fingerprint(estado_objetivo))`. Em 8D, fingerprint de heroi em (3,0) e heroi
em (4,4) tem similaridade ≈ 0.85 — a recompensa nao distingue progresso no eixo Y.
O agente converge para "andar direita" (unica direcao que claramente melhora o fingerprint)
e oscila porque nao ha incentivo para descer.

**Correcao:** Adicionar recompensa explıcita por coordenada:
```python
def avaliar(self, est_atual, est_ant, est_obj=None, acao_ok=True):
    r = super().avaliar(est_atual, est_ant, est_obj, acao_ok)
    # Bonus por aproximacao Manhattan ao objetivo
    if est_obj:
        h_atual = est_atual.get("heroi")
        h_obj = est_obj.get("heroi")
        if h_atual and h_obj:
            dist_antes = sum(abs(h_atual.props.get(k,0)-h_obj.props.get(k,0))
                           for k in ["x","y"])
            h_ant = est_ant.get("heroi")
            if h_ant:
                dist_depois = sum(abs(h_ant.props.get(k,0)-h_obj.props.get(k,0))
                                for k in ["x","y"])
                r += (dist_depois - dist_antes) * 2  # bonus por aproximacao
    return max(-10.0, min(10.0, r))
```

### FALHA 3: MCRAutoEvolution — 0% aceitacao

**Dados:**
```
entropia_global() antes:  0.3594
  → muta threshold (thr.obs + [novo_valor])
  → entropia_global() depois: 0.3594 (IGUAL)
  → melhoria = 0.0000
  → 20/20 ciclos rejeitados
```

**Causa raiz:** `entropia_global()` mede:
- `mk_byte.entropia_media()` (0.3503)
- `mk_palavra.entropia_media()` (0.0000)
- `world.mk_estado` (N/A)
- coupling matrix (N/A)
- topic variance (N/A)

Nenhum destes e alterado por `thr.obs += [valor]`. A mutacao e a metrica
estao desacopladas. A docstring na linha 553 diz "A mutacao afeta DIRETAMENTE
as metricas de entropia_global()" — isso e falso.

**Correcao:** Adicionar variacao dos MCRThreshold a entropia_global():
```python
# entropia_global(), apos as metricas existentes:
thr_vals = []
for nome in ['thr', 'thr_entropia', 'thr_tamanho', 'thr_palavras',
             'thr_visitas', 'thr_amostras', 'thr_por_pasta']:
    if hasattr(c, nome):
        thr = getattr(c, nome)
        if isinstance(thr, MCRThreshold) and len(thr.obs) >= 3:
            thr_vals.append(thr.calcular())
if thr_vals:
    media = sum(thr_vals) / len(thr_vals)
    var = sum((v-media)**2 for v in thr_vals) / len(thr_vals)
    entropias.append(min(var, 1.0))
```

---

## 5. Comparacao com Sistemas Estabelecidos

| Sistema | Capaz | MCR faz igual? | Evidencia |
|---------|-------|---------------|-----------|
| **HTM TM** | Sequencias com contexto temporal | Parcial | Markov: 100% em seq curtas. Falha em longas (sem memoria de contexto). |
| **HTM Anomaly** | Score por erro de predicao | Sim | H=0.0→1.0 para anomalos. Equivalente funcional. |
| **HTM SP** | SDR esparsa com sobreposicao | Nao | Fingerprint 8D e denso, nao esparso. Sem generalizacao por overlap. |
| **Word2vec** | Embeddings semanticos (300D) | Nao | NLP 70% vs ~95%. Jaccard byte-level nao captura semantica. |
| **Kanerva HDC** | Algebra vetorial 10kD | Parcial | Algebra existe (bundle/bind/permute) mas em 8D, nao 10kD. Analogia acertou por byte-similaridade. |
| **MCTS** | Busca com expansao seletiva | Parcial | MCREntropicSearch existe mas thresholds nunca treinados. |
| **Godel Machine** | Auto-modificacao com prova | Nao | AE mede entropia desacoplada. 0% aceitacao. |
| **SQLite/busca** | Memoria persistente | Sim | Funciona — salva, busca por similaridade. |
| **Q-Learning** | RL com convergencia | Parcial | Implementacao correta, mas reward fingerprint 8D e insuficiente para guiar. |

---

## 6. Plano de Correcao

### Prioridade 1: Consertar AE

| O que | Onde | Linhas | Efeito |
|-------|------|--------|--------|
| Incluir thresholds em `entropia_global()` | `MCRAutoEvolution.entropia_global()` | ~20 | AE passa a detectar melhoria real |
| Ajustar docstring | `MCRAutoEvolution.ciclo()` | ~5 | Documentacao honesta |

### Prioridade 2: Consertar MCRPlanner

| O que | Onde | Linhas | Efeito |
|-------|------|--------|--------|
| Adicionar `distancia_manhattan()` | `MCRWorld` | ~10 | Planejamento funciona para grid |
| Usar Manhattan no `plano()` | `MCRPlanner.plano()` | ~3 | Plano nao fica mais vazio |

### Prioridade 3: Consertar Q-Learning

| O que | Onde | Linhas | Efeito |
|-------|------|--------|--------|
| Adicionar bonus Manhattan ao reward | `MCRReward.avaliar()` | ~10 | QL converge para objetivo |

### Prioridade 4: Testar novamente

```bash
python test_mcr_comparativo.py
# Resultado esperado: 19/19
```
