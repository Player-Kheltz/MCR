# MCR — Multi-level Markov Engine

> 1 equation. N levels. 0 GPU. 0 LLM. 0 dependencies.
> ~3600 lines of Python stdlib.

```python
MCR(nivel).aprender(a, b)  # → transition learned
MCR(nivel).predizer(a)      # → most probable next state
```

An experiment in **computational minimalism**: a single Markov chain primitive applied at every level — byte, word, token, action, decision, fingerprint — with zero external dependencies.

**194/194 tests pass in <1s. No GPU. No LLM. No numpy. Python stdlib only.**

## What It Actually Does

| Module | Capability | Mechanism |
|--------|-----------|-----------|
| **Core** | Byte→byte, word→word, token→type | Markov chain dict-of-dicts |
| **Fingerprint** | 8-128D projection with auto-dimensionality discovery | `MCRSignatureExpansiva.dimensionalidade_ideal()` |
| **HDC** | Bundle, bind, permute, bundle_inv, analogy | `MCRHDCOperation` — vector algebra on fingerprints |
| **World** | Causal state model + counterfactuals | Grid world with pathfinding (8x8, obstacles) |
| **Actions** | Zero-if/elif action dispatch | Dictionary registry, 7 built-in actions |
| **NLP** | Intent classification via Jaccard + cosine at optimal dim | `dimensionalidade_ideal()` + `MCRThreshold` limiar |
| **RL** | Q-Learning with fingerprinted state (12-32D) | Bellman update, Manhattan bonus, Radar loop detector |
| **Planning** | Hierarchical + Entropic Tree Search | `MCREntropicSearch` — rollout with trajectory entropy |
| **Memory** | SQLite persistent fingerprint search | Cosine similarity over 8-128D |
| **Attention** | 4-signal weighted ranking (learnable via MCRThreshold) | prob + fp + jac + ent |
| **Self-Modify** | MCTRreshold mutation with entropy validation | In-memory threshold tweaking, entropy-gated accept/reject |
| **Genesis** | Gap detection + skeleton module generation | Entropy-based diagnosis |
| **Curiosity** | Autonomous filesystem exploration | MCRThreshold-guided walking and sampling |
| **Identity** | Writer fingerprint recognition via vocabulary+entropy | Multi-signature author identification |
| **Auto-Validation** | Continuous cross-dimensional stability monitoring | Detects which dimensions are unstable vs stable |
| **Topology** | Correlation graph between levels | `MCRAutoTopologia` — emergent clustering |
| **Orchestrator** | Markov-decided action flow | State → action via learned transitions, zero if/elif |

## Quick Start

```bash
python MCR_AGI.py                            # chat mode
python MCR_AGI.py "explique SPA"              # direct question
python MCR_AGI.py --daemon                    # server mode
python MCR_AGI.py --status                    # show execution count
```

## What It CAN Do (tested & measured)

| Test | Result | vs Baseline |
|------|--------|-------------|
| Sequence prediction (deterministic) | 29/29 = 100% | Moda = 100% (tie) |
| Anomaly detection | H normal=0.0 → H anomalo=1.0 | CUSUM equivalent |
| Intent classification (6 classes) | 21/30 = 70% | Aleatorio = 17% (4x) |
| Dimensionality discovery | 8D → 128D: 19% → 70% separation | Fingerprint 8D fixo: 3.7x pior |
| Analogia HDC | "rei - homem + rainha" → **"mulher"** (conf=0.583) | — |
| Loop detection (alternating) | **Detecta** ababab... | Contagem simples: **não detecta** |
| Context disambiguation | Geração continua após palavra ambígua | Roteamento cross-dimensional |
| Planning with obstacles (8x8) | 7 ações, dist 14→7, 0 colisões | Random: 50% mais distancia |
| Q-Learning (dim_ideal) | **3 direções**, dist=1, 40 replay | 8D: 1 direção |
| Memory (SQLite) | 500 inserts in 0.05s, search in 0.2ms | — |
| Auto-evolution | 2/20 mutations accepted | Entropy delta detected |
| Performance | 2.5M predictions/s, 170k fingerprints/s | — |

## What It CANNOT Do (honest limitations)

| Limitation | Why | Workaround |
|-----------|-----|-----------|
| **Direct string similarity** | Jaccard("carro","automovel") = 0 | Context Markov learns synonymy with 50+ examples each |
| **Optimal planning** | MCRPlanner finds a valid path, not the shortest | EntropicSearch minimizes trajectory entropy instead |
| **Q-Learning convergence** | Fingerprint approximation vs tabular exact | Generalizes to larger state spaces (tabular doesn't scale) |
| **External knowledge** | No pretrained models, no internet | All knowledge is experiential (fed by user or Curiosity) |

## Test Suites

```bash
python test_mcr_veracidade.py                # 194 tests, 10.0/10
python test_mcr_comparativo.py               # 22 tests, 91% (QL approximation)
python test_mcr_comparativo_avancado.py       # 27 tests, 100%
python test_mcr_comparativo_avancado.py --verbose  # detailed output
```

## Architecture

```
Entrada (bytes)
    │
    ▼
┌──────────────────────────────────────┐
│  Multi-dimensional Parallel Markov   │
│                                      │
│  ┌──────┐  ┌────────┐  ┌─────────┐  │
│  │ Byte │  │ Word   │  │ Token   │  │
│  │→byte │  │→word   │  │→type    │  │
│  └──┬───┘  └───┬────┘  └────┬────┘  │
│     │          │             │       │
│  ┌──▼──────────▼─────────────▼────┐  │
│  │      MCRCoupling (N×N)        │  │
│  │  + MCREsfera (N-dimensional)   │  │
│  └────────────────────────────────┘  │
│     │          │             │       │
│  ┌──▼──────────▼─────────────▼────┐  │
│  │  MCRAutoValidacaoContinua     │  │
│  │  (detects unstable dimensions) │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
    │
    ▼
Decisao (MLearn / EntropicSearch / Curiosity)
    │
    ▼
Resposta (MCRResposta / Geracao / Acao)
```

## How Is This Different

| System | Dependencies | GPU? | Lines | Unique to MCR |
|--------|-------------|------|-------|---------------|
| PyTorch | CUDA, numpy | Yes | 2M+ | Tensor computation |
| Transformers | torch, numpy | Yes | 500k+ | LLMs |
| Numenta HTM | numpy | Opt | 100k+ | Cortical model |
| OpenCog | 30+ deps | Opt | 500k+ | AGI framework |
| **MCR** | **stdlib** | **0** | **3606** | Markov-only multi-level, entropy as universal metric |

## Why This Matters

Current AI requires billions in GPUs and millions in training. MCR is:

- **Zero** external dependencies
- **Zero** GPU required
- **Zero** training data needed (knowledge via experience)
- **~3600 lines** total
- **~0.2s** full test suite

It doesn't compete with LLMs or deep learning. It explores a different question: *how far can a single Markov primitive go when applied at every level, with entropy as the only compass?*

## Files

```
E:/MCR/
├── MCR_AGI.py                        # ~3600 lines, single file
├── test_mcr_veracidade.py            # 194 tests (what MCR claims)
├── test_mcr_comparativo.py           # 22 tests (vs simple baselines)
├── test_mcr_comparativo_avancado.py  # 27 tests (vs known systems)
├── docs/
│   ├── ENTROPIA_CONDICIONAL.md       # Cross-dimensional entropy
│   ├── ESTABILIDADE_CROSS_DIM.md     # Stability across dimensions
│   ├── NLP_REALIDADE.md              # Real NLP pipeline analysis
│   ├── DIAGNOSTICO_COMPARATIVO.md    # Comparative diagnosis
│   └── ...
└── cache/                            # Learned data (gitignored)
```

## License

**MCR** is dual-licensed under AGPL v3 (free) or commercial license. See [LICENSE](LICENSE) and [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

## Author

**Kheltz** — Independent researcher.
Started with: *"How far can one Markov chain go?"*
