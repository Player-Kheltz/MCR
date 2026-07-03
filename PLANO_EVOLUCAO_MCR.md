# Plano de Evolucao — MCR Multi-Paradigma

> 1 equacao. N paradigmas. 0 hardcode.
> Data: Julho 2026
> Base: MCR_AGI.py (secao 01-23)
> Proposito: Incorporar conceitos de HDC, Reservoir Computing, MC-AIXI e
>   Godel Machine dentro da filosofia MCR — Markov + entropia + zero hardcode.

---

## Sumario

1. [Preambulo: O que MCR ja tem](#1-preambulo)
2. [F1 — HDC: Algebra de Fingerprints](#2-f1--hdc-algebra-de-fingerprints)
3. [F2 — Reservoir: Multiscale Fingerprint Vector](#3-f2--reservoir-multiscale-fingerprint-vector)
4. [F3 — MC-AIXI: Entropic Tree Search](#4-f3--mc-aixi-entropic-tree-search)
5. [F4 — Godel Machine: Auto-modificacao Entropica](#5-f4--godel-machine-auto-modificacao-entropica)
6. [F5 — Ciclo Completo: Explorar → Descobrir → Gerar → Validar](#6-f5--ciclo-completo)
7. [Metricas de Sucesso](#7-metricas-de-sucesso)
8. [Riscos e Limitacoes](#8-riscos-e-limitacoes)

---

## 1. Preambulo

### O que ja existe (fundacao)

| Componente | Uso atual | Uso no plano |
|-----------|-----------|--------------|
| `MCRSignatureExpansiva.dimensionalidade_ideal()` | Descobrir dim otima para fingerprint | Base para reservoir multiescala |
| `MCRByteUtils.fingerprint(dados, dim)` | Projecao fixa 8D | Deve virar dim variavel otimizada |
| `MCRCoupling` | Pesos entre byte/palavra/tven | Readout do reservoir; entropia decide |
| `MCRWorld.mk_estado` | Transicoes de fingerprint | Base para operacoes HDC |
| `MCRQLearn` | Q-learning grid 5x5 | Noyau do Entropic Tree Search |
| `MCRThreshold` | Limiares aprendidos | Decisao de aceitacao/rejeicao |
| `MCRGenesis` | Detecta gaps, gera classes | Ciclo de auto-modificacao |
| `MCRCodex.escanear/substituir` | Auto-modificacao trivial | Substituir por prova entropica |
| `MCREntropia` | Deteccao de loop | Metrica universal de otimalidade |
| `MCRDecisorUniversal` | Decisao de parametros | Orquestrador de rollout/exploracao |

### Princípios da implementacao

1. **Nada novo que a equacao ja nao faca** — toda funcionalidade nova deve ser expressavel como `MCR.aprender(a, b)` + entropia + threshold
2. **Zero numeros magicos** — dimensionamentos decididos por `MCRDecisorUniversal` e `MCRThreshold`
3. **Medida unica de qualidade** — entropia media do sistema decide se mudanca e boa
4. **Conhecimento via uso** — fingerprints, pesos, thresholds: tudo aprendido, nunca hardcoded

---

## 2. F1 — HDC: Algebra de Fingerprints

### Objetivo

Adicionar as 3 operacoes da Hyperdimensional Computing (bundle, bind, permute) como
operacoes aprendidas por Markov, permitindo raciocinio analogico tipo
"rei - homem + mulher ≈ rainha" sem modelo externo.

### O que muda

**Novas classes:**

```
MCRHDCOperation:
  - bundle(a, b):      soma ponderada de fingerprints
  - bind(a, b):        multiplicacao elemento a elemento
  - permute(a, rot):   rotacao circular do vetor
  - bundle_inv(a, b):  subtracao (para analogias)
```

Cada operacao tem seu proprio `MCR` que aprende quando aplica-la:

```python
# O MCR aprende: "se entrada X, aplicar bundle com Y, saida Z"
mk_bundle.aprender(f"{str(fp_a)}:{str(fp_b)}", str(fp_c))
```

**Novo fluxo:**

```
1. Alimentar texto A → fingerprint(A)
2. Alimentar texto B → fingerprint(B)
3. Para cada operacao (bundle, bind, permute):
   a. Aplicar → fp_resultado
   b. Perguntar ao MCR: "qual a chance de fp_resultado ser C?"
   c. Confianca = probabilidade Markov
4. Escolher operacao com maior confianca
5. Aprender: operacao escolhida + fingerprints = resultado
```

### Analogia "rei - homem + mulher ≈ rainha"

```
Passo 1: Alimentar pares
  fp("rei")     = bundle( fp("homem"), fp("real")     )  # aprendido
  fp("rainha")  = bundle( fp("mulher"), fp("real")    )  # aprendido

Passo 2: Inferencia
  fp_resultado = bundle_inv( fp("rei"), fp("homem") )  # ≈ fp("real")
  fp_resultado = bundle( fp_resultado, fp("mulher") )  # ≈ fp("rainha")

Passo 3: Buscar texto mais similar a fp_resultado
  MCRResposta._buscar por fingerprint → "rainha"
```

### Arquivos afetados

- `MCR_AGI.py` secao [01] — adicionar classe `MCRHDCOperation`
- `MCR_AGI.py` secao [04] — `MCRWorld` estendido para operacoes HDC
- `test_mcr_veracidade.py` — novos testes seccao 15

### Criterios de sucesso

- `bundle(fp(a), fp(b)) ≈ fp(a+b)` com similaridade cosseno > 0.7
- Analogia 3-termo: `solve("A:B::C:?")` com acerto > 60% em 10 trials
- Entropia de transicao HDC < entropia de transicao fingerprint simples

---

## 3. F2 — Reservoir: Multiscale Fingerprint Vector

### Objetivo

Substituir fingerprint 8D unico por um vetor multiescala (16, 32, 64, 128 dims)
que funciona como reservatorio de alta dimensao, permitindo separar padroes
nao-lineares que Markov linear nao consegue.

### O que muda

**Novo componente: `MCRReservoir`**

```python
class MCRReservoir:
    def __init__(self):
        self.dims = []                          # descoberto por entropia
        self.fingerprints = {}                  # cache: texto → fp_multiscale
        self.coupling = MCRCoupling()           # readout multi-nivel
        self.mk = MCR("reservoir")              # transicoes entre estados do reservoir

    def vetor(self, texto):
        # Descobre dimensionalidades ideais (16, 32, 64, ...)
        dim_otima = MCRSignatureExpansiva.dimensionalidade_ideal(
            texto.encode()[:2000], mx=128, thr=0.03
        )
        # Gera fingerprints em potencias de 2 ate dim_otima
        fps = []
        for d in [d for d in [1,2,4,8,16,32,64,128] if d <= dim_otima]:
            fps.extend(MCRByteUtils.fingerprint(texto, d))
        return fps  # vetor concatenado de N*?? dimensoes

    def readout(self, vetor):
        # Pesos aprendidos por coupling entre dimensoes
        # Reduz dimensionalidade para a representacao mais informativa
        pass
```

**Readout via entropia:**

O `MCRCoupling` existente ja faz isso entre niveis discretos. A extensao e:

```python
# Para cada par de dimensoes (d1, d2), aprender peso:
self.coupling.alimentar(f"fp_{d1}", f"fp_{d2}", fp_d1_str, fp_d2_str)
self.coupling.recalcular()

# O peso = confianca de que fp_d2 pode ser predito a partir de fp_d1
# Quanto maior o peso, mais redundancia → pode remover uma dimensao
```

O reservatorio entao **descobre sua propria estrutura otima**:
- Se dim 8 + dim 16 tem coupling 0.95 → dim 8 e redundante (pode remover)
- Se coupling dim 64 → dim 128 e baixo → ambas sao necessarias
- Dimensionalidade total do vetor = soma das dims com baixo coupling mutuo

### Fluxo

```
1. Entrada: texto
2. Gerar vetor multiescala via dimensionalidade_ideal()
3. Calcular coupling entre todas as dimensoes do vetor
4. Podar dimensoes redundantes (coupling > threshold aprendido)
5. Vetor resultante = "reservatorio" do MCR
6. MCR aprende transicoes entre estados do reservatorio
7. Predicao usa o vetor completo (nao apenas 8D)
```

### Arquivos afetados

- `MCR_AGI.py` secao [01] — nova classe `MCRReservoir`
- `MCR_AGI.py` secao [07] — `MCRCoupling` estendido para dims automaticas
- `MCR_AGI.py` secao [04] — `MCRWorld` pode usar `MCRReservoir` como representacao

### Criterios de sucesso

- Vetor reservatorio tem entropia informativa > vetor 8D fixo para o mesmo texto
- Coupling mutuo entre dimensoes identifica redundancia corretamente
- `MCRWorld.simular` com reservoir prediz estados mais precisamente que com fp 8D
- Tempo de execucao < 2x do fingerprint 8D

---

## 4. F3 — MC-AIXI: Entropic Tree Search

### Objetivo

Substituir `MCRPlanner.plano()` (split linear de delta) por Monte Carlo Tree Search
com metrica de incerteza baseada em entropia, aproximando o limite teorico do AIXI.

### O que muda

**Novo componente: `MCREntropicSearch`**

```python
class MCREntropicSearch:
    def __init__(self, world: MCRWorld, qlearn: MCRQLearn):
        self.world = world
        self.qlearn = qlearn
        self.mk_sim = MCR("es_similaridade")     # similaridade entre estados simulados
        self.mk_inc = MCR("es_incerteza")        # incerteza = entropia do rollout
        self.thr_rollouts = MCRThreshold("es_n_rollouts")
        self.thr_depth = MCRThreshold("es_depth")

    def rollout(self, estado, acao, passos=5):
        """Simula N passos a partir de estado + acao.
        Retorna: estados_visitados, recompensa_total, entropia_media"""
        est = estado.clone()
        hist = [est]
        for _ in range(passos):
            ac = self.qlearn.melhor_acao(est) or self.qlearn.escolher_acao(est, epsilon=0.1)
            prox = self.world.simular(est, ac)
            hist.append(prox)
            est = prox
        recomp = sum(MCRReward().avaliar(est, hist[i-1], hist[-1], True)
                     for i in range(1, len(hist)))
        ent_media = sum(MCRByteUtils.entropia_bytes(e.serializar()[:500])
                       for e in hist) / len(hist)
        return hist[-1], recomp, ent_media

    def planejar(self, estado, objetivo, n_rollouts=None):
        """Entropic Tree Search sobre espaco de acoes."""
        n_rollouts = n_rollouts or int(self.thr_rollouts.obter("rollouts", 20))
        depth = int(self.thr_depth.obter("depth", 5))

        melhor_acao = None
        melhor_score = -float('inf')

        for acao in MCRAcao.disponiveis():
            # Multiplos rollouts para cada acao
            recompensas = []
            entropias = []
            for _ in range(n_rollouts):
                prox, r, ent = self.rollout(estado, acao, depth)
                # Bonus por proximidade ao objetivo
                dist = self.world.distancia(prox, objetivo)
                r_final = r - dist
                recompensas.append(r_final)
                entropias.append(ent)

            # Score = media recompensa - incerteza (variancia entropia)
            media_r = sum(recompensas) / len(recompensas)
            var_ent = sum((e - sum(entropias)/len(entropias))**2 for e in entropias) / len(entropias)
            score = media_r - var_ent * self.qlearn.gamma

            if score > melhor_score:
                melhor_score = score
                melhor_acao = acao

            # Aprender: para este estado, esta acao tem score X
            self.mk_sim.aprender(
                f"ES:{str(estado.fingerprint(8)[:3])}:{acao}",
                f"{score:.4f}"
            )

        # Aprender quantos rollouts foram uteis
        self.thr_rollouts.observar(n_rollouts * (melhor_score / max(abs(melhor_score), 0.01)))

        return melhor_acao, melhor_score

    def plano_completo(self, estado, objetivo, max_acoes=10):
        """Gera sequencia de acoes via Entropic Search."""
        plano = []
        est = estado.clone()
        for _ in range(max_acoes):
            dist = self.world.distancia(est, objetivo)
            if dist < 0.5:
                break
            ac, _ = self.planejar(est, objetivo)
            if not ac:
                break
            plano.append(ac)
            est = self.world.simular(est, ac) or MCRAcao.executar(est, ac)
            # Aprender transicao real
            self.world.aprender(est, ac, est)
        return plano
```

### Diferenca do planejador atual

| Atual (`MCRPlanner`) | Novo (`MCREntropicSearch`) |
|---------------------|---------------------------|
| Split linear de delta fingerprint | Monte Carlo com incerteza |
| Sem exploracao | Epsilon-greedy por rollout |
| Sem metrica de confianca | Variancia da entropia como incerteza |
| Uma unica predicao | Multiplas simulacoes (rollouts) |
| Plano fixo | Acao a acao com replanejamento |
| Zero aprendizado do plano | `mk_sim` aprende scores por estado+acao |

### Integracao com `MCRDecisorUniversal`

```python
# Decidir parametros do Entropic Search por contexto
MCRDecisorUniversal.decidir_passos("entropic_search", {
    "n_topicos": len(cerebro.topicos),     # mais dados → mais rollouts
    "tamanho_bytes": entropia_contexto,     # alta entropia → mais profundidade
})
```

### Criterios de sucesso

- `plano_completo` chega ao objetivo em grid 10x10 (vs grid 5x5 atual)
- `plano_completo` funciona mesmo com obstaculos moveis (não deterministico)
- Numero de rollouts se ajusta automaticamente (`MCRThreshold`)
- Entropia media do rollout correlaciona com taxa de sucesso (>0.7)

---

## 5. F4 — Godel Machine: Auto-modificacao Entropica

### Objetivo

Transformar `MCRCodex.substituir()` (re.sub) em um ciclo real de
auto-modificacao com verificacao empirica: alterar → medir entropia →
aceitar se reduziu entropia → reverter se aumentou → aprender.

### O que muda

**Novo componente: `MCRAutoEvolution`**

```python
class MCRAutoEvolution:
    def __init__(self, cerebro):
        self.cerebro = cerebro
        self.mk_mutacoes = MCR("ae_mutacoes")     # historico de mutacoes
        self.mk_resultados = MCR("ae_resultados") # entropia antes/depois
        self.thr_aceitacao = MCRThreshold("ae_aceite")
        self.codex = MCRCodex()
        self.hist = []

    def entropia_global(self):
        """Entropia media do sistema completo como metrica de saude."""
        entropias = []
        if hasattr(self.cerebro, 'mk_byte'):
            entropias.append(self.cerebro.mk_byte.entropia_media())
        if hasattr(self.cerebro, 'mk_palavra'):
            entropias.append(self.cerebro.mk_palavra.entropia_media())
        if hasattr(self.cerebro, 'world') and hasattr(self.cerebro.world, 'mk_estado'):
            entropias.append(self.cerebro.world.mk_estado.entropia_media())
        if hasattr(self.cerebro, 'coupling'):
            cp = MCRByteUtils.entropia_bytes(
                json.dumps(self.cerebro.coupling.matriz).encode()
            )
            entropias.append(cp)
        # Entropia dos topicos (variedade de conteudo)
        if self.cerebro.topicos:
            textos = [t.get("texto","") for t in self.cerebro.topicos.values()]
            ent_texto = MCRByteUtils.entropia_bytes(" ".join(textos).encode()[:5000]) if textos else 1.0
            entropias.append(ent_texto)
        return sum(entropias) / max(len(entropias), 1) if entropias else 1.0

    def ciclo(self):
        """Um ciclo completo de auto-evolucao:

        1. Escanear parametros candidatos (MCRCodex.escanear)
        2. Medir entropia global ANTES
        3. Propor mutacao via MCRGenesis + parametros
        4. Aplicar mutacao em copia temporaria
        5. Executar N episodios de validacao
        6. Medir entropia global DEPOIS
        7. ACEITAR se entropia_depois < entropia_antes - δ
        8. REJEITAR se entropia_depois >= entropia_antes - δ
        9. Aprender: esta classe de mutacao foi boa/ruim
        """
        hcs = self.codex.escanear()
        if not hcs:
            return {"acao": "nada_para_mutar"}

        ent_antes = self.entropia_global()
        diag = None

        # Propor mutacao
        genesis = MCRGenesis(self.cerebro)
        gaps = genesis.diagnosticar()

        mutacao = None
        if gaps['total'] > 0:
            # Priorizar gap com maior severidade
            melhor_gap = max(gaps['gaps'], key=lambda g: g['severidade'])
            mutacao = {
                'tipo': 'novo_modulo',
                'gap': melhor_gap,
                'codigo': genesis.projetar(melhor_gap)
            }
        elif hcs:
            # Modificar parametro existente
            hc = _rand.choice(hcs)
            novo_valor = str(int(hc['valor']) + 1) if hc['valor'].isdigit() else "10"
            mutacao = {
                'tipo': 'parametro',
                'param': hc['param'],
                'linha': hc['linha'],
                'novo_valor': novo_valor
            }

        if mutacao is None:
            return {"acao": "sem_mutacao_valida"}

        # Aplicar mutacao em copia
        if mutacao['tipo'] == 'parametro':
            if not self.codex.substituir(__file__, mutacao['linha'], mutacao['param'], mutacao['novo_valor']):
                return {"acao": "mutacao_falhou"}
        elif mutacao['tipo'] == 'novo_modulo':
            # Salva novo modulo em arquivo separado
            mod_path = os.path.join(BASE_DIR, "modulos_gerados",
                                    f"{mutacao['gap']['nome']}.py")
            os.makedirs(os.path.dirname(mod_path), exist_ok=True)
            with open(mod_path, "w") as f:
                f.write(mutacao['codigo'])
            mutacao['arquivo'] = mod_path

        # Validar: executar episodios
        n_val = max(2, int(self.thr_aceitacao.obter("n_validacao", 3)))
        for _ in range(n_val):
            try:
                # Alimentar texto de teste
                self.cerebro.alimentar(
                    f"teste auto-evolucao {time.time()}",
                    f"ae_test_{hash(str(time.time()))%10000}"
                )
                # Executar Q-Learning episode
                est = EstadoMundo.criar_simples()
                self.cerebro.rl.executar_episodio(est, est, 5)
            except:
                pass

        ent_depois = self.entropia_global()
        melhoria = ent_antes - ent_depois

        # Decidir: aceitar ou reverter
        limiar = self.thr_aceitacao.obter("limiar_melhoria", 0.05)
        aceite = melhoria > limiar

        if aceite:
            # Manter alteracao
            self.mk_resultados.aprender(f"ACEITE:{mutacao['tipo']}", f"{melhoria:.4f}")
            resultado = "aceito"
        else:
            # Reverter: recarregar do git ou do backup
            if mutacao['tipo'] == 'parametro':
                # Reverter o `substituir` restaurando o original
                # (na pratica: git checkout ou copia de backup)
                pass
            elif mutacao['tipo'] == 'novo_modulo':
                if 'arquivo' in mutacao:
                    try:
                        os.unlink(mutacao['arquivo'])
                    except:
                        pass
            self.mk_resultados.aprender(f"REJEITE:{mutacao['tipo']}", f"{melhoria:.4f}")
            resultado = "rejeitado"

        registro = {
            "timestamp": time.time(),
            "mutacao": mutacao,
            "ent_antes": round(ent_antes, 4),
            "ent_depois": round(ent_depois, 4),
            "melhoria": round(melhoria, 4),
            "resultado": resultado,
        }
        self.hist.append(registro)
        self.thr_aceitacao.observar(abs(melhoria))
        self.mk_mutacoes.aprender(
            f"AE:{mutacao['tipo']}:{resultado}",
            f"{melhoria:.4f}"
        )

        return registro

    def relatorio(self):
        """Sumario do historico de evolucao."""
        aceites = sum(1 for h in self.hist if h['resultado'] == 'aceito')
        rejeicoes = sum(1 for h in self.hist if h['resultado'] == 'rejeitado')
        melhoria_media = (sum(h['melhoria'] for h in self.hist) /
                         max(len(self.hist), 1))
        return {
            "ciclos": len(self.hist),
            "aceites": aceites,
            "rejeicoes": rejeicoes,
            "taxa_aceite": round(aceites / max(len(self.hist), 1), 3),
            "melhoria_media": round(melhoria_media, 4),
            "entropia_atual": round(self.entropia_global(), 4),
        }
```

### Diferenca do atual

| Atual (`MCRCodex`) | Novo (`MCRAutoEvolution`) |
|-------------------|--------------------------|
| `substituir()` sempre aceita | Ciclo medir → mutar → validar → aceitar/rejeitar |
| Sem metrica de impacto | Entropia global como utility function |
| Sem memoria | `mk_resultados` aprende que mutacoes funcionam |
| Nao gera codigo novo | Pode gerar modulos via `MCRGenesis` |
| Sem rollback | Reverte automaticamente se entropia piorar |

### Equivalente a Godel Machine

- **Godel Machine:** prova formal que cada modificacao e otima via proof search
- **MCRAutoEvolution:** mede otimalidade via entropia empirica (proxy computavel)

A entropia global e o equivalente funcional da utility function — mas aprendida
pelo uso, nao programada. O threshold de aceitacao e aprendido por `MCRThreshold`,
não hardcoded.

---

## 6. F5 — Ciclo Completo

### Integracao de F1-F4 em um unico loop autonomo

```
while True:
    # FASE 1 — EXPLORAR (curiosidade)
    # MCR percorre drives/arquivos, alimenta cerebro
    # Usa MCRReservoir (F2) para representacao multiescala
    cur.ciclo()

    # FASE 2 — ANALOGIA (HDC)
    # MCR busca analogias entre topicos
    # Usa MCRHDCOperation (F1) para bundle/bind/permute
    analogias = buscar_analogias(cerebro)

    # FASE 3 — PLANEJAR (Entropic Search)
    # Se tem objetivos, planeja com incerteza
    # Usa MCREntropicSearch (F3)
    plano = search.plano_completo(estado, objetivo)

    # FASE 4 — EVOLUIR (Auto-modificacao)
    # Mede entropia, propoe mudancas, valida, aceita/rejeita
    # Usa MCRAutoEvolution (F4)
    evolucao = ae.ciclo()

    # FASE 5 — RELATAR
    # Auto-diagnostico completo
    print(ae.relatorio())
    print(cerebro.auto_diagnosticar())

    # MCR decide quando parar (entropia minima atingida)
    if ae.entropia_global() < 0.1:
        break
```

### Dependencias entre fases

```
F2 (Reservoir) ──→ F1 (HDC)       [reservoir fornece fingerprint multiescala para HDC]
F2 (Reservoir) ──→ F3 (Entropic)  [reservoir melhora predicao de estado no MCTS]
F1 (HDC)       ──→ F5 (Ciclo)     [analogias alimentam o auto-diagnostico]
F3 (Entropic)  ──→ F4 (Evolution) [resultados do planejamento viram metrica de entropia]
F4 (Evolution) ──→ F2 (Reservoir) [auto-modificacao pode alterar dimensionalidade]
```

Ordem de implementacao sugerida: **F2 → F1 → F3 → F4 → F5**

---

## 7. Metricas de Sucesso

### Objetivas (codigo)

| Metrica | Atual | Alvo F1 | Alvo F2 | Alvo F3 | Alvo F4 | Alvo F5 |
|---------|-------|---------|---------|---------|---------|---------|
| Testes passando | 134/134 | 140+ | 145+ | 150+ | 155+ | 160+ |
| Nota test_mcr_veracidade | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 |
| Grid size do planner | 5x5 | 5x5 | 5x5 | 10x10 | 10x10 | 20x20 |
| Tempo execucao testes | 0.2s | <0.5s | <1.0s | <2.0s | <3.0s | <5.0s |
| Linhas de codigo | ~2100 | ~2400 | ~2800 | ~3200 | ~3600 | ~4000 |

### Subjetivas (comportamento)

- MCR descobre analogias sem exemplos explícitos ("rei:homem::rainha:?")
- MCR planeja em grid com obstaculos que exigem desvio
- MCR rejeita auto-modificacao que piora entropia vs aceita que melhora
- MCR decide sozinho quando explorar vs. planejar vs. evoluir
- Entropia global diminui com o tempo (sistema fica "mais organizado")

---

## 8. Riscos e Limitacoes

| Risco | Probabilidade | Mitigacao |
|-------|--------------|-----------|
| **F1 HDC:** Fingerprint 8D e pequeno demais para algebra | Alta | `dimensionalidade_ideal()` descobre dim > 8; reservoir (F2) fornece vetor maior |
| **F2 Reservoir:** Vetor multiescala cresce exponencialmente | Media | `MCRCoupling` poda dims redundantes; threshold decidido por entropia |
| **F3 Entropic Search:** MCTS e computacionalmente caro | Alta | `MCRThreshold` aprende n_rollouts otimo; `MCRDecisorUniversal` limita profundidade |
| **F4 Evolution:** Mutacao quebra o sistema | Media | Rollback automatico; execucao em copia; `MCRGenesis` gera codigo compilavel |
| **F5 Ciclo:** Loop infinito sem convergencia | Baixa | `MCREntropia.esta_em_loop()` detecta; criterio de parada por entropia minima |
| **Geral:** Complexidade cresce, MCR deixa de ser minimalista | Media | Cada nova classe reusa `MCR` primitivo; adicoes sao modulares e removiveis |

---

## Apendice: Arquivos do Plano

```
E:/MCR/
├── test_mcr_veracidade.py       # Teste de veracidade (134 checks, 14 secoes)
├── PLANO_EVOLUCAO_MCR.md        # Este arquivo — plano completo de evolucao
├── modulos_gerados/              # Modulos gerados por MCRAutoEvolution (F4)
└── cache/
    └── test_veracidade_result.json  # Resultado do ultimo teste de veracidade
```
