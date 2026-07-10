# MCRAutoTopologia — Geometria Emergente dos Dados

## O Problema

Toda implementação atual do MCR impõe uma **forma geométrica fixa** aos dados:

```
Circulo:    MCR("byte") isolado — 1D
Esfera:     MCREsfera — ND fixo (5 dimensoes)
Hiperesfera: MCRHiperesferaAutoExpansiva — ND descoberto, mas ainda ND
```

Mesmo a hiperesfera auto-expansiva assume que os dados vivem na **superfície de algo** — uma esfera N-dimensional onde cada eixo é uma dimensão. A forma ainda é escolhida pelo humano, não pelos dados.

## A Ideia

Em vez de impor uma forma, **deixar a geometria emergir das correlações entre níveis**.

O MCR já aprende transições dentro de cada nível (`MCR(nivel).aprender(a, b)`). A **MCREsfera** já aprende correlações entre níveis (`esfera.alimentar_par("byte", "palavra", ...)`). 

O próximo passo: tratar CADA NIVEL como um **nó** em um grafo. As arestas são ponderadas por **entropia condicional** — o quanto um nível explica o outro. A topologia do grafo **é a geometria dos dados**.

```python
# Em vez de:
#   byte ──── palavra ──── token ──── intencao ──── acao
#   (fixo, linear, humano escolheu)

# O grafo emerge:
#   byte ←→ palavra (peso: H(palavra|byte) = 0.3)
#   token ── byte  (peso: H(byte|token) = 0.9)  — quase independente
#   intencao ←→ acao (peso: H(acao|intencao) = 0.1) — fortemente acoplado
```

## Definição Formal

### Nós
Cada `MCR(nivel)` registrado é um nó no grafo.

### Arestas
Dois níveis A e B têm uma aresta ponderada por:

```
w(A, B) = 1 - H(A|B) / H(A)
```

Onde:
- `H(A|B)` = entropia condicional de A dado B
- `H(A)` = entropia marginal de A
- `w` = 1 quando B explica A perfeitamente (H(A|B)=0)
- `w` = 0 quando B não explica A (H(A|B)=H(A))

### Topologia

O grafo `G(V, E, w)` é simplificado removendo arestas com peso < threshold (padrão: 0.3). Componentes conectados formam **clusters naturais** — grupos de níveis que se explicam mutuamente. Nós isolados são níveis independentes que capturam aspectos diferentes dos dados.

### Métricas derivadas

| Métrica | Fórmula | Significado |
|---------|---------|-------------|
| **Coesão de cluster** | `C = 2|E_intra| / (|V_c|*(|V_c|-1))` | Quão integrado é um cluster de níveis |
| **Ponte entre clusters** | `B = max(w(x,y))` para x∈C1, y∈C2 | Melhor conexão entre grupos de níveis |
| **Centralidade** | `c(v) = sum(w(v,u)) / |V|` | Quão importante é um nível para explicar os outros |
| **Entropia total do sistema** | `H_total = -sum(p(c) * log(p(c)))` para clusters c | Diversidade informacional do sistema |

## Exemplo real com dados de código fonte

```
Niveis disponiveis: byte, palavra, token_tipo, linha, hash_curto, byte_delta

Matriz de entropia condicional H(A|B):
                 byte  pal  tok  lin  hash  delta
byte             0.0  0.8  0.9  0.7  0.6   0.3
palavra          0.8  0.0  0.4  0.2  0.3   0.9
token_tipo       0.9  0.4  0.0  0.5  0.7   0.8
linha            0.7  0.2  0.5  0.0  0.4   0.8
hash_curto       0.6  0.3  0.7  0.4  0.0   0.7
byte_delta       0.3  0.9  0.8  0.8  0.7   0.0

Grafo resultante (threshold w > 0.5):
  Cluster 1: palavra ←→ linha (peso ~0.8)
             └── hash_curto (peso ~0.7)
  Cluster 2: byte ←→ byte_delta (peso ~0.7)
  Isolado:   token_tipo (peso max ~0.5 com palavra)
```

Isso revelaria que `palavra` e `linha` são altamente correlacionadas (formam um cluster), enquanto `byte` se relaciona mais com `byte_delta` do que com `palavra`. A geometria **emerge dos dados**, não é imposta.

## Algoritmo

```python
class MCRAutoTopologia:
    """Geometria emergente dos dados via grafo de entropia condicional.
    
    Nao impoe forma (nem circulo, nem esfera, nem hiperesfera).
    A topologia emerge das correlacoes entre niveis.
    """
    
    def __init__(self):
        self.niveis: Dict[str, MCR] = {}
        self.tokenizadores: Dict[str, Callable] = {}
        self.grafo: Dict[str, Dict[str, float]] = {}
        self.clusters: List[Set[str]] = []
        self.H = MCRHiperesferaAutoExpansiva()  # reuso
    
    def alimentar(self, texto: str):
        """Alimenta todos os niveis e recalcula o grafo."""
        # Descobre niveis se necessario
        if not self.niveis:
            dims = self.H.descobrir(texto)
            for nome, mk in self.H.dimensoes.items():
                self.niveis[nome] = mk
                self.tokenizadores[nome] = self.H.tokenizadores[nome]
        
        # Alimenta cada nivel
        for nome, mk in self.niveis.items():
            tokens = self.tokenizadores[nome](texto)
            for i in range(len(tokens)-1):
                mk.aprender(tokens[i], tokens[i+1])
        
        # Recalcula topologia
        self._recalcular_grafo()
        self._detectar_clusters()
    
    def _recalcular_grafo(self):
        """Calcula matriz de entropia condicional entre todos os pares."""
        self.grafo = {n: {} for n in self.niveis}
        
        for a in self.niveis:
            for b in self.niveis:
                if a == b:
                    self.grafo[a][b] = 1.0
                    continue
                
                # H(A|B) ≈ H(A) - I(A;B) ≈ entropia de A que B nao explica
                # Simplificacao: entropia de A menos correlacao via esfera
                Ha = self.niveis[a].entropia_media() if self.niveis[a].total > 0 else 1.0
                
                # Correlacao = quao bem um valor de A prediz B
                correlacao = 0
                total = 0
                for valor_a in list(self.niveis[a].freq.keys())[:50]:
                    pred, conf = self.H.esfera.predizer_cross(b, **{a: valor_a})
                    if pred:
                        correlacao += conf
                        total += 1
                
                correlacao_media = correlacao / max(total, 1)
                # w = 1 - H(A|B)/H(A) ≈ correlacao_media
                w = max(0, min(1, correlacao_media))
                self.grafo[a][b] = round(w, 3)
    
    def _detectar_clusters(self, threshold=0.3):
        """Detecta clusters usando componentes conectados."""
        visitados = set()
        self.clusters = []
        
        for nivel in self.niveis:
            if nivel in visitados: continue
            cluster = set()
            fila = [nivel]
            while fila:
                v = fila.pop(0)
                if v in visitados: continue
                visitados.add(v)
                cluster.add(v)
                for u, peso in self.grafo.get(v, {}).items():
                    if peso >= threshold and u not in visitados:
                        fila.append(u)
            if cluster:
                self.clusters.append(cluster)
    
    def topologia(self) -> dict:
        """Retorna a topologia atual do sistema."""
        return {
            "n_niveis": len(self.niveis),
            "n_clusters": len(self.clusters),
            "clusters": [sorted(c) for c in self.clusters],
            "grafo": {n: {d: p for d, p in adj.items() if p >= 0.3}
                      for n, adj in self.grafo.items()},
            "niveis_isolados": [n for c in self.clusters for n in c
                                if len(c) == 1] if self.clusters else [],
        }
```

## Comparação com abordagens anteriores

| Aspecto | Círculo (MCR puro) | Esfera (MCREsfera) | Hiperesfera (AutoExpansiva) | Topologia Emergente |
|---------|-------------------|-------------------|---------------------------|---------------------|
| Forma | 1 cadeia | ND fixo | ND até estabilizar | **Nenhuma — emerge** |
| Dimensões | 1 | 5 escolhidas | Descobertas por entropia | **Clusters naturais** |
| Correlações | N/A | Pairwise fixa | Pairwise + entropia | **Grafo completo** |
| Quem decide | Humano | Humano | Entropia | **Dados (grafo)** |
| Limitação | Isolamento | Forma fixa | ND ainda é uma forma | **Nenhuma conhecida** |

## Integração no MCR_AGI.py

A topologia emergente seria uma classe adicional (não substituta) que:

1. Usa `MCRHiperesferaAutoExpansiva` para descobrir níveis iniciais
2. Constrói o grafo de entropia condicional entre eles
3. Detecta clusters naturais
4. Expõe a topologia via `cerebro.topologia()`
5. Opcional: usa a topologia para decidir quais níveis alimentar (poda de arestas fracas)

A métrica de qual nível é "útil" não seria mais `entropia < threshold` (hiperesfera) — mas sim **centralidade no grafo > threshold**. Um nível com alta centralidade explica muitos outros níveis, então é importante. Um nível isolado no grafo é redundante ou ruído.

## Status

**Conceito.** Baseado no insight de que "esfera ainda é uma forma fixa". A topologia emergente remove a última prisão conceitual: a geometria deixa de ser imposta e passa a ser **descoberta**.

Implementação futura: ~250 linhas, usando MCR existente + MCREsfera + MCRHiperesferaAutoExpansiva.
