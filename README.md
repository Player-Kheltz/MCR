# MCR — Multi-level Markov Experiment

> 1 equation. N levels. 0 GPU. 0 LLM. Self-parameter-adjusting.

```python
MCR(nivel).aprender(a, b)  # → transicao aprendida
MCR(nivel).predizer(a)      # → proximo estado mais provavel
```

An experiment in **computational minimalism**: what can you do with a single Markov chain primitive applied at every level — byte, word, token, action — with zero dependencies, zero GPU, and ~2000 lines?

**134/134 tests pass in 0.2s. No GPU. No LLM. No numpy. Python stdlib only.**

## What It Does

| Module | What it learns | How it works |
|--------|---------------|--------------|
| **Core** | Byte→byte, word→word, token→type | Markov chain (transition count table) |
| **World** | State→state, state+action→state | Causal transitions in a 5x5 toy grid |
| **Actions** | Action→result | Dispatch via dictionary registry (zero if/elif) |
| **NLP** | Intent by byte-level Jaccard similarity | Bigram overlap between byte fingerprints |
| **RL** | Q-Learning over 8-dim fingerprints | Bellman update, epsilon-greedy |
| **Planning** | Sub-goal decomposition | Linear split of delta in toy grid |
| **Memory** | SQLite persistence | Save/load transition tables |
| **Attention** | Weighted heuristic focus | 4 signals: probability + fingerprint + jaccard + entropy |
| **Self-Modify** | Self-parameter adjustment | Scans own source, replaces hardcoded values |
| **Genesis** | Detects knowledge gaps | Auto-diagnoses weakest topic via signature |
| **Curiosity** | Autonomous file exploration | Discovers drives/files by entropy, learns patterns |

## Quick Start

```bash
python MCR_AGI.py                            # chat mode
python MCR_AGI.py "explique SPA"              # direct question
python MCR_AGI.py --daemon                    # server mode
```

## Verified Results

| Experiment | Result | Note |
|-----------|--------|------|
| 12 file formats (binary, audio, image, text) | Entropy scale 0.0-7.6 | Single equation, zero calibration |
| Collatz next-term prediction | 10x better than random | Problem open since 1937 |
| Prime gap prediction (±2) | 44x better than baseline | No closed-form formula exists |
| Code quality (good vs bad) | 5/5 entropy, 4/5 dimension | Zero training examples |
| Novel name generation | 9/10 phonetically valid | Zero templates |
| Self-diagnosis | Detects weakest topic | Signature-based gap analysis |

## Limitations (honest)

This is an **experiment in minimalism**, not a production AGI system.

- **"NLP" is byte-pattern matching** — Jaccard similarity on byte bigrams. It does not understand language; it finds similar byte sequences. A sentence with 70% different words will be treated as "unknown".
- **"Planning" is a toy** — works on a 5x5 grid with linear delta decomposition. Not generalizable to real-world problems.
- **"Attention" is weighted heuristics** — 4 fixed signals combined with weights. Not attention in the Transformer sense.
- **"Self-modifying" is regex** — scans source for hardcoded numbers and suggests replacements. No proof-checking.
- **No reasoning, no generalization** — Markov chains return only what was learned. There is no inference beyond statistical frequency.

### Comparison with established frameworks

| System | Type | Maturity | 
|--------|------|----------|
| **MCR** | Markov + heuristics | Prototype (1 dev) |
| **Numenta HTM** | Neocortical model | Product (Numenta) |
| **OpenCog Hyperon** | Metagraph + PLN | Active research |
| **Reservoir Computing** | Untrained RNN | Mature field |

MCR is not competing with these. It asks a different question: *how far can a single Markov primitive go?*

## Architecture

```
MCR(nivel).aprender(a, b)
├── byte       → proximo byte
├── palavra   → proxima palavra
├── decisao   → proxima acao
├── threshold → valor ideal
└── qualquer  → nivel registrado
```

## Test Suite

```bash
python test_mcr_veracidade.py                # 134 tests, ~0.2s
python test_mcr_veracidade.py --verbose       # detailed output
```

## Why This Matters

Current AI requires GPUs, cloud APIs, and massive dependencies. MCR fits in 17KB and runs on any machine with Python — no internet, no GPU, no LLM, no numpy.

## License

**MCR** is dual-licensed:

| License | When to use | Cost |
|---------|-------------|------|
| **AGPL v3** | Research, personal use, open-source projects | **Free** |
| **Commercial License** | Proprietary systems, closed-source products, enterprise servers | **Paid** |

Under AGPL v3, if you modify MCR and use it on a network server, you **must** disclose the source code. If you cannot or don't want to, you need a **commercial license** — contact for pricing.

See [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md) for details.

## Author

**Kheltz** — Independent researcher.
Started with a question: *"How far can one Markov chain go?"*
