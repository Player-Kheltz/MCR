# MCR — Universal Computation Framework

> 1 equation. N levels. 0 GPU. 0 LLM. Self-modifying.

```python
MCR(nivel).aprender(a, b)  # → transicao aprendida
MCR(nivel).predizer(a)      # → proximo estado mais provavel
```

## What It Can Do

| Module | What it learns | Level |
|--------|---------------|-------|
| **Core** | Byte→byte, word→word, token→type | byte, palavra, token |
| **World** | State→state, state+action→state, delta→action | causalidade |
| **Actions** | Action→result, registered (zero if/elif) | acao |
| **NLP** | Intent by Jaccard similarity (zero keywords) | linguagem |
| **RL** | Q-Learning over 8-dim fingerprints | reforco |
| **Planning** | Hierarchical sub-goal decomposition | planejamento |
| **Memory** | SQLite persistent storage | memoria |
| **Attention** | Selective focus with 4 signals | atencao |
| **Self-Modify** | Rewrites its own parameters | auto |
| **Genesis** | Detects gaps, generates new modules | expansao |

## Quick Start

```bash
python MCR_AGI.py                            # chat mode
python MCR_AGI.py "explique SPA"              # direct question
python MCR_AGI.py --daemon                    # server mode
```

## Architecture

```
MCR(nivel).aprender(a, b)
├── byte       → proximo byte
├── palavra   → proxima palavra (texto)
├── decisao   → proxima acao
├── threshold → valor ideal
└── qualquer  → o que voce registrar
```

## Why This Matters

Current AI requires:
- Billions in GPUs
- Millions in training
- Thousands of lines per module

MCR requires:
- **Zero** GPUs
- **Zero** training data
- **950** lines total
- **Same equation** for everything

## License

AGPL v3 — Use, modify, share. Commercial use requires agreement.

## Author

**Kheltz** — Independent researcher.
Started with a question: *"What if one equation was enough?"*
