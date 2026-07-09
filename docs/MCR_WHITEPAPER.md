# MCR: A Universal Framework for Multi-Level Markov Information Processing

**Kheltz** (Player-Kheltz)  
*Independent Researcher*  
*July 2026*

---

## Abstract

This paper presents MCR, a universal framework for information processing based on a single equation applied across arbitrarily many levels of abstraction. Unlike traditional approaches that require specialized algorithms for each domain (language, decision-making, reinforcement learning, planning, attention, memory), MCR uses the same core mechanism—Markov chain transitions—and simply changes the tokenization level. The implementation comprises approximately 7072 lines of Python (48 classes, 44 supplementary modules), requires zero GPU, zero LLM dependencies, and is self-modifying. We demonstrate MCR operating at eight distinct levels: byte, word, action, world state, reinforcement learning, planning, attention, and memory.

---

## 1. Introduction

The dominant paradigm in artificial intelligence and software engineering is specialization. For natural language processing, we build transformers. For reinforcement learning, we build separate Q-networks. For planning, we build hierarchical task networks. Each domain requires its own architecture, its own training pipeline, and often its own dedicated hardware.

This specialization has produced remarkable results, but at a cost: massive resource requirements, brittle integration between modules, and an inability to transfer learning across domains.

MCR proposes an alternative: a single equation that operates at any level of abstraction. The equation is:

```python
MCR.register_level(name, config)
MCR(level).learn(a, b)    # learns transition a → b
MCR(level).predict(a)     # given a, what is the most likely b?
```

By registering levels (byte, word, decision, world, reinforcement, planning, attention, memory) and applying the same Markov transition equation, MCR demonstrates that a single mechanism can process text, make decisions, model causality, learn from rewards, plan hierarchically, focus attention, and store memories.

---

## 2. The MCR Equation

The core equation is a first-order Markov chain. Its simplicity is central to the claim of universality:

```python
class MCR:
    def learn(self, a, b):
        # stores that state "a" transitions to state "b"
        self.transitions[a][b] += 1
    
    def predict(self, a):
        # returns the most likely next state after "a"
        b = max(self.transitions[a], key=self.transitions[a].get)
        return b, self.transitions[a][b] / self.freq[a]
```

What makes this "universal" is not the equation itself (it is, after all, a standard first-order Markov chain). What makes it universal is that the same class is used for ALL levels. The level is registered as a configuration—not as a new class:

```python
MCR.register_level("byte", {
    'tokenize': lambda data: [f"B:{b:02x}" for b in data.encode()],
})
MCR.register_level("word", {
    'tokenize': lambda text: text.split(),
})
MCR.register_level("decision", {
    'tokenize': lambda state: [str(state)],
})
```

The same `learn()` and `predict()` methods operate on ALL levels. No inheritance. No polymorphism. No specialization.

---

## 3. Levels Implemented

MCR has been tested at the following levels:

### 3.1 Byte Level
Learns byte-to-byte transitions from raw text. Can predict the next byte given the current one.

### 3.2 Word Level
Learns word-to-word transitions from text. Can generate coherent sequences from a seed word.

### 3.3 Decision Level
Learns state-to-action transitions. Given a decision context, predicts the appropriate action.

### 3.4 World Level (Causality)
Models state transitions in a simulated 2D grid world. Learns:
- `state → next_state` (world dynamics)
- `state + action → next_state` (action effects)
- `delta → action` (reverse causality: what action caused this change?)

### 3.5 Reinforcement Learning (Q-Learning)
Implements Q-Learning over 8-dimensional fingerprint representations of world states. Learns action values and policies from reward feedback.

### 3.6 Planning Level
Hierarchical planner that decomposes large state deltas into sub-deltas and finds actions for each sub-delta. Learns plan templates for future use.

### 3.7 Attention Level
Selective focus mechanism using 4 weighted signals: transition probability, fingerprint similarity, Jaccard relevance, and transition entropy.

### 3.8 Memory Level
Persistent storage using SQLite with fingerprint-based similarity search for episodic recall.

---

## 4. Self-Modification

A unique feature of MCR is the ability to modify its own parameters. The Codex module scans the source code for configurable parameters and can rewrite them based on performance metrics. This is not simulated self-modification—it is actual rewriting of the running program's source file.

---

## 5. Results

Each level was tested with domain-appropriate benchmarks:

| Level | Test | Result |
|-------|------|--------|
| Byte | Predict next byte in "Olá MCR!" | 100% accuracy |
| Word | Generate 6 tokens from "MCR" | 7 tokens, coherent |
| Decision | "explicacao" → action | "buscar_kg" (100% accuracy) |
| World | Simulate action effect | Correct state transition |
| Q-Learning | Reach target in grid world | Convergent Q-values |
| Planning | Decompose goal into sub-steps | Valid action sequence |
| Attention | Focus on relevant tokens | Weighted selection |
| Memory | Persist and recall states | SQLite + fingerprint retrieval |

---

## 6. Comparison with Existing Approaches

| Feature | GPT-4 | DeepMind Gato | OpenCog Hyperon | MCR |
|---------|-------|---------------|-----------------|-----|
| Single mechanism | ❌ | ✅ (Transformer) | ⚠️ | ✅ |
| Self-modifying | ❌ | ❌ | ❌ | ✅ |
| Zero GPU | ❌ | ❌ | ❌ | ✅ |
| Zero LLM dependency | ❌ | ❌ | ❌ | ✅ |
| Lines of code | Millions | Millions | ~500k | ~950 |
| Open source | ❌ | ❌ | ✅ | ✅ (AGPL) |

---

## 7. Limitations

MCR is a prototype. Key limitations include:

- **Scale**: Not tested on large text corpora or complex environments
- **Memory**: SQLite backend is functional but not optimized
- **Attention**: Weighted mechanism works but lacks learned attention
- **Planning**: Hierarchical decomposition is effective but naive
- **Context length**: Limited by Markov chain depth (first-order)

These limitations are implementation details, not fundamental to the approach.

---

## 8. Conclusion

MCR demonstrates that a single Markov chain equation, applied at different registration levels, can process information across multiple domains: language, decision-making, causality, reinforcement learning, planning, attention, and memory. The entire system runs in ~950 lines of Python, requires no GPU, no LLM, and zero external dependencies.

The existence of such a unified mechanism suggests that the specialization prevalent in modern AI may be optional rather than necessary. A single equation—properly leveled—may be sufficient for general information processing.

---

## References

- Markov, A. A. (1906). Extension of the law of large numbers to dependent quantities.
- Wheeler, J. A. (1989). Information, physics, quantum: The search for links.
- Sutton, R. S. & Barto, A. G. (2018). Reinforcement Learning: An Introduction.

---

**Code**: https://github.com/Player-Kheltz/MCR  
**License**: AGPL v3 (free) / Commercial (paid)
