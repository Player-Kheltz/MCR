# MCR — Multi-level Cognitive Registry

> 1 equation. N levels. 0 GPU. 0 LLM. 0 dependencies.
> ~4650 lines of Python stdlib. **449/449 tests pass.**

```python
MCR(nivel).aprender(a, b)  # learns that "a" leads to "b"
MCR(nivel).predizer(a)      # most probable "b" given "a"
```

**A single Markov equation** applied at byte, word, token, subject, relation, object, decision, action, and any auto-discovered level — simultaneously, coupled via N-dimensional entropy.

The system **observes passively** (Windows hooks + file monitoring), **learns in real time**, and **generates novel output** through the collision of independent chains (superposition). No backprop. No attention heads. No GPUs. Just counters, entropy, and emergence.

---

## What It Actually Does

### Core (Stdlib Only)

| Capability | How |
|-----------|-----|
| **Multi-level Markov** | Byte, palavra, tven, sujeito, relação, objeto, decisão, ação + auto-descobertos |
| **N-Dimensional Coupling** | `MCRCoupling` + `MCREsfera` — cross-level correlation matrix |
| **Superposition** | `MCRSuperposicao.colidir()` — two chains collide → novel token neither predicted alone |
| **Auto-Validation** | `MCRAutoValidacaoContinua` — recursive self-validation by entropy |
| **Criticality** | `MCRAutoEvolution` — self-modification at the edge of chaos (entropy 0.2–0.7) |
| **Fingerprinting** | 8–128D projection with auto-dimensionality discovery |
| **HDC** | Bundle, bind, permute, analogy: `rei − homem + mulher → rainha` |
| **Semantic Parsing** | `MCRParserMinimo` — extracts (subject, relation, object) triples from Portuguese text |
| **Relational State Space** | `MCRRedeSemantica` — subject→relation→object chains + transitive BFS |

### Observation (Passive, Event-Driven)

| Source | Mechanism | Platform |
|--------|-----------|----------|
| **Keyboard** | Low-level hook (`WH_KEYBOARD_LL`) | Windows |
| **Mouse** | Low-level hook (`WH_MOUSE_LL`) | Windows |
| **Clipboard** | Polling window handle | Windows |
| **Foreground Window** | `EVENT_SYSTEM_FOREGROUND` | Windows |
| **Filesystem** | `FindFirstChangeNotificationW` + signature diff | Windows |

All feed into a **single unified byte chain** (`sys_byte`). The MCR discovers correlations between ALL sources via multi-level entropy.

### Emergence

| Mechanism | What Emerges |
|-----------|-------------|
| **Superposition** | Tokens that NO single chain predicts — the collision of two Markov routes generates novelty |
| **Hiperesfera Auto-Expansiva** | New tokenization dimensions from high-entropy data (bigrama, trigrama, byte_delta, hash, etc.) |
| **Auto-Topology** | Correlation graph between levels — geometry emerges from data |
| **Cross-Level Prediction** | The esfera predicts a word from a byte, a byte from an intention |

### Interaction

```bash
python MCR_AGI.py                          # chat — learns from conversation
python MCR_AGI.py "explique o MCR"         # direct question
python MCR_AGI.py --daemon                 # server — observes system in background
python MCR_AGI.py --aprender               # feeds NPC dialogue files
```

---

## Test Results (449/449 — 100%)

| Suite | Tests | Result | What It Validates |
|-------|-------|--------|-------------------|
| `test_mcr_veracidade.py` | 194 | 10.0/10 | Every promise MCR makes |
| `test_mcr_desafios.py` | 13 | 13/13 | Multi-level entropy, curiosity, coupling, superposition |
| `test_mcr_comparativo.py` | 22 | 22/22 | vs simple baselines |
| `test_mcr_comparativo_avancado.py` | 32 | 32/32 | vs known systems (Q-Learning, HDC, planning) |
| `test_bateria_real.py` | 12 | Pass | Real-world behavioral validation |
| `test_mcr_stress.py` | 100 | 100/100 | 10 rounds: 50K mass, 10 sources, 1000 auto-evolution cycles |
| `test_mcr_promessas.py` | 100 | 100/100 | 10 promises validated |
| `test_silogismo.py` | 60 | 60/60 | Semantic parser + transitive inference |
| **Total** | **449** | **449/449** | **100% — zero hardcoded results** |

---

## Architecture

```
Input (text, keys, mouse, clipboard, files, clock)
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Multi-Level Parallel Markov Chains                      │
│                                                          │
│  ┌──────┐  ┌────────┐  ┌──────┐  ┌────────┐  ┌──────┐  │
│  │ Byte │  │ Word   │  │ Tven │  │Subject │  │Relac │  │
│  │→byte │  │→word   │  │→type │  │→relac  │  │→obj  │  │
│  └──┬───┘  └───┬────┘  └──┬───┘  └───┬────┘  └──┬───┘  │
│     │          │          │          │          │       │
│  ┌──▼──────────▼──────────▼──────────▼──────────▼────┐  │
│  │       MCRCoupling + MCREsfera (N×N)              │  │
│  │  Cross-level correlation + N-dimensional esfera  │  │
│  │  + MCRSuperposicao (collision → emergence)       │  │
│  └──────────────────────────────────────────────────┘  │
│     │          │          │          │          │       │
│  ┌──▼──────────▼──────────▼──────────▼──────────▼────┐  │
│  │  MCRAutoValidacaoContinua + MCRAutoEvolution     │  │
│  │  (criticality: entropy 0.2–0.7, self-modify)     │  │
│  └──────────────────────────────────────────────────┘  │
│     │                                                  │
│  ┌──▼──────────────────────────────────────────────┐  │
│  │  MCRDecisorUniversal + mk_orq (Markov-decided)  │  │
│  │  Zero if/elif — all decisions via predizer()    │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
    │
    ▼
Prediction / Generation / Action / Emergence
```

All levels learn simultaneously from every input. The coupling matrix captures correlations. The esfera enables cross-level prediction. The superposition generates what no chain predicted alone.

---

## How Is This Different

| Aspect | Current AI | MCR |
|--------|-----------|-----|
| **Representation** | Dense vectors (embeddings) | Sparse discrete symbols |
| **Learning** | Backpropagation | Frequency counting |
| **Architecture** | Specialized (CNN, RNN, Transformer) | One equation, N levels |
| **Observation** | Training dataset | Real-time hooks + files |
| **Novelty** | Interpolation of training data | Collision of independent chains |
| **Cost** | Millions in GPU/datacenter | CPU, zero dependencies |
| **Transparency** | Black box | Full deterministic trace |

---

## Files

```
E:/MCR/
├── MCR_AGI.py                   # ~4650 lines, stdlib only (ENTIRE system)
├── test_mcr_veracidade.py       # 194 tests
├── test_mcr_desafios.py         # 13 multi-level tests
├── test_mcr_comparativo.py      # 22 vs baseline
├── test_mcr_comparativo_avancado.py  # 32 vs known systems
├── test_bateria_real.py         # 12 real-world tests
├── test_mcr_stress.py           # 100 pts stress test
├── test_mcr_promessas.py        # 100 pts promise validation
├── test_silogismo.py            # 60 pts transitive inference
├── docs/
│   ├── MANIFESTO_MCR.md         # The philosophy
│   ├── MCR_WHITEPAPER_EN.md     # Technical whitepaper
│   ├── MCR_WHITEPAPER_PT.md     # Whitepaper (Portuguese)
│   ├── REFLEXAO_MCR.md          # Reflection on the project
│   ├── CONVERSA_FILOSOFICA.md    # The philosophical conversation
│   ├── ESFERA_CONCEITO.md       # The esfera concept
│   ├── TOPOLOGIA_EMERGENTE.md   # Emergent topology
│   └── ...
└── cache/                       # Learned data (gitignored)
```

---

## Philosophy

> **Entropy is a coordinate, not a metric.**
> It measures where the system is in N-dimensional space — not how "good" or "bad" it is.

> **Criticality, not optimization.**
> The system seeks the edge of chaos (entropy 0.2–0.7), not zero entropy. Dead systems have zero entropy. Learning happens at the boundary.

> **Observation, not control.**
> The MCR is an observer in an open system. It cannot prevent entropy fluctuations. It learns from what it cannot control.

> **Emergence, not programming.**
> New dimensions auto-discover. Chains collide into novelty. The topology emerges from data. No human decides what the system should find.

---

## License

**MCR** is dual-licensed under AGPL v3 (free) or commercial license. See [LICENSE](LICENSE) and [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

---

## Author

**Kheltz** — Independent researcher.

*How far can one Markov chain go when applied at every level, coupled by entropy, and left to emerge?* — Apparently, very far.
