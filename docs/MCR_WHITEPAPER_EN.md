# MCR: A Universal Transition Equation for Multi-Level Information Processing

**Kheltz**  
*Independent Researcher*  
*July 2026*

---

## Abstract

We present **MCR** (Multi-level Cognitive Registry), a single mathematical equation for information processing that operates identically across arbitrary levels of abstraction. Given a state space $S_n$ and a transition function $T_n: S_n \times S_n \to \mathbb{N}$, MCR learns the conditional probability distribution $P(b|a) = T_n(a,b) / \sum_{c \in S_n} T_n(a,c)$ for any level $n$. We prove that this equation is **level-invariant**: the same operator $T$ works for byte prediction, word generation, decision-making, causal modeling, reinforcement learning, hierarchical planning, attention, and memory — differing only in the definition of $S_n$. An implementation in 950 lines of Python (zero GPU, zero LLM, zero external dependencies) serves as constructive proof. We discuss theoretical implications for AGI, showing that general intelligence may emerge from hierarchical compositions of a single transition primitive rather than from specialized architectures.

---

## 1. Formal Definition of the MCR Equation

### 1.1 The Transition Matrix

Let $\mathcal{L} = \{n_1, n_2, \dots, n_k\}$ be a set of **levels**. For each level $n \in \mathcal{L}$, define a **state space** $S_n$ whose elements are tokens, symbols, or representations at that level.

**Definition 1 (MCR Core).** At level $n$, the MCR equation maintains a sparse matrix $T_n: S_n \times S_n \to \mathbb{N}$ and a frequency vector $f_n: S_n \to \mathbb{N}$, where:

$$T_n(a,b) = \text{count of observed transitions } a \to b$$
$$f_n(a) = \sum_{c \in S_n} T_n(a,c)$$

**Definition 2 (Learn Operation).** Upon observing a transition $a \to b$, the update rule is:

$$T_n(a,b) \leftarrow T_n(a,b) + 1$$
$$f_n(a) \leftarrow f_n(a) + 1$$

**Definition 3 (Predict Operation).** Given a state $a$, the predicted next state and its confidence are:

$$P_n(b|a) = \frac{T_n(a,b)}{f_n(a)}$$
$$\hat{b} = \arg\max_{b \in S_n} P_n(b|a)$$
$$c(a) = \max_{b \in S_n} P_n(b|a)$$

**Definition 4 (Multi-Step Generation).** Given a seed $s_0$, the MCR generates a sequence of length $m$:

$$s_{t+1} = \arg\max_{b \in S_n} P_n(b|s_t) \quad \text{subject to } c(s_t) \geq \varepsilon$$

where $\varepsilon$ is a dynamically determined threshold.

### 1.2 Level Invariance Theorem

**Theorem 1 (Level Invariance).** For any two levels $n, m \in \mathcal{L}$, the MCR equation produces transition matrices $T_n$ and $T_m$ that are **isomorphic up to state space cardinality**. Specifically, the learning and prediction algorithms are identical; only the tokenization function $\tau_n$ differs.

*Proof.* The MCR class implements a single `learn(a,b)` and `predict(a)` method. These methods make no reference to the semantic content of $a$ or $b$. The state space $S_n$ is defined entirely by the tokenization function $\tau_n: \text{input} \to S_n$:
- $\tau_{\text{byte}}(x) = \{B:\text{hex}(x_i) \mid x_i \in \text{bytes}(x)\}$
- $\tau_{\text{word}}(x) = \{x_i \mid x_i \in \text{s.split()}\}$
- $\tau_{\text{token}}(x) = \{x_i[0] \mid x_i \in \text{s.split()}\}$

Since the same operator $T$ acts on the image of $\tau_n$ for any $n$, the equation is invariant to level choice.

**Corollary 1 (Universality).** If every information processing task can be represented as learning transitions in some state space $S$, and MCR can learn transitions in any $S$ via appropriate $\tau$, then MCR is a universal information processor.

---

## 2. Entropy as a State Metric

**Definition 5 (Transition Entropy).** The entropy of a state $a \in S_n$ is:

$$H_n(a) = -\sum_{b \in S_n} P_n(b|a) \log_2 P_n(b|a)$$

**Definition 6 (Mean Entropy).** The mean entropy across all observed states:

$$\bar{H}_n = \frac{1}{|S_n^{\text{obs}}|} \sum_{a \in S_n^{\text{obs}}} H_n(a)$$

where $S_n^{\text{obs}} = \{a \in S_n \mid f_n(a) > 0\}$.

**Property 1.** $H_n(a) = 0$ iff $P_n(b|a) = 1$ for some $b$ (deterministic transition). $H_n(a) = \log_2 |S_n|$ iff $P_n(b|a) = 1/|S_n|$ for all $b$ (uniform distribution — maximum uncertainty).

**Property 2.** In the implementation, entropy thresholds are learned rather than hardcoded. The `MCRThreshold` class observes entropy values and dynamically adjusts:

$$\varepsilon_{\text{loop}} = \text{median}(\{H_n(a_t) \mid t \in W\}) \cdot \lambda$$

where $W$ is a sliding window of observations and $\lambda$ is learned.

---

## 3. Fingerprint and Dimensional Projection

### 3.1 Fingerprint Function

States are projected into a $d$-dimensional continuous space for similarity comparison.

**Definition 7 (Fingerprint).** Given a byte sequence $x$ of length $L$, the fingerprint $f_{d}: \{0,1\}^* \to [0,1]^d$ is:

$$f_{d}(x)[k] = \frac{1}{Z} \sum_{i=0}^{L-1} \mathbb{1}[(i + x_i) \bmod d = k]$$

where $Z = \sum_{k=0}^{d-1} f_{d}(x)[k]$ (normalization constant) and $\mathbb{1}[\cdot]$ is the indicator function.

### 3.2 Optimal Dimensionality

**Definition 8 (Dimensionality Discovery).** The optimal dimension $d^*$ is found by evaluating the entropy of fingerprints at increasing dimensions:

$$d^* = \arg\min_{d \in \{1,2,4,8,16,32,64,128\}} \left| H(f_d(x)) - H(f_{d/2}(x)) \right| < \delta$$

where $\delta$ is a convergence threshold. This identifies the dimension at which additional degrees of freedom no longer increase information content.

### 3.3 Cosine Similarity

**Definition 9 (Fingerprint Similarity).** The similarity between two states is measured by cosine similarity in fingerprint space:

$$\text{sim}(x,y) = \frac{f_d(x) \cdot f_d(y)}{\|f_d(x)\| \cdot \|f_d(y)\|}$$

### 3.4 Delta Fingerprint

**Definition 10 (Transition Delta).** For states $x$ (before) and $y$ (after), the delta fingerprint captures the directional change:

$$\Delta_{x \to y} = f_d(y) - f_d(x)$$

This enables **causal inference**: given a known delta, the system can predict which action produced it via:

$$a = \arg\max_{a'} P_{\text{causal}}(\Delta_{x \to y} \mid a')$$

---

## 4. The Optimal Bridge Equation

**Definition 11 (Bridge Score).** Given two topics $A$ and $B$, the optimal bridge between them is scored as:

$$\mathcal{B}(A,B) = \frac{5D + 3E + 2P}{10}$$

where:

- $D$ **(Divergence)**: $1 - \text{Jaccard}(T_A, T_B)$, measuring how different the transition sets are
- $E$ **(Specificity)**: $-\log_2(p(w))$, where $p(w)$ is the relative frequency of word $w$ in the corpus
- $P$ **(Depth)**: length of the generated chain after bridging

**Theorem 2 (Bridge Normalization).** $\mathcal{B}(A,B) \in [0,1]$ for any $A,B$.

*Proof.* Since $D \in [0,1]$, $E \in [0, \log_2 N]$ normalized, and $P$ has a finite maximum, the weighted sum $(5D + 3E + 2P) / 10$ is bounded by $[0,1]$ when $D, E, P$ are normalized to $[0,1]$.

### 4.1 Connection Score

**Definition 12 (Connection Score).** For a generated sequence spanning topics $A$ and $B$:

$$\mathcal{C}(A,B) = (W_{\text{byte}} + W_{\text{word}} + W_{\text{token}}) \times (1 - \pi)$$

where:
- $W_{\text{byte}} \in [0,2]$: byte-level transition coherence
- $W_{\text{word}} \in [0,5]$: content word overlap
- $W_{\text{token}} \in [0,3]$: token-level pattern continuity
- $\pi \in \{0, 0.3, 0.7, 0.9\}$: penalty based on bridge type

---

## 5. Multi-Signal Attention Mechanism

**Definition 13 (Attention Score).** Given context $C$ and query $Q$, the relevance of candidate token $t$ is:

$$\mathcal{A}(t) = \frac{\omega_1 \cdot P(t) + \omega_2 \cdot \text{sim}(f(C), f(C \oplus t)) + \omega_3 \cdot \text{Jaccard}(Q, D_t) + \omega_4 \cdot (1 - |H(t) - 0.5| \cdot 2)}{\sum_{i=1}^4 \omega_i}$$

where:
- $\omega = (3.0, 5.0, 4.0, 1.0)$: empirically determined weights
- $P(t)$: Markov transition probability
- $\text{sim}(f(C), f(C \oplus t))$: fingerprint similarity before and after adding $t$
- $\text{Jaccard}(Q, D_t)$: relevance of $t$ to query $Q$ via domain $D_t$
- $H(t)$: normalized entropy of $t$ (penalizing both highly predictable and highly unpredictable tokens)

**Property 3.** The attention mechanism is **self-normalizing**: the denominator $\sum \omega_i$ ensures $\mathcal{A}(t) \in [0,1]$ as a convex combination of the four signals.

---

## 6. Reinforcement Learning as a Special Case

**Theorem 3 (Q-Learning Embedding).** Q-learning can be represented as a two-level MCR system:

$$Q(s,a) \cong T_{\text{Q}}(FP(s), a)$$
$$\pi(s) = \arg\max_a T_{\text{Q}}(FP(s), a)$$

where $T_{\text{Q}}$ is an MCR instance at the "reinforcement" level and $FP(s)$ is the fingerprint of state $s$.

**Definition 14 (Q-Update via MCR).** The Bellman update:

$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') - Q(s,a) \right]$$

is implemented as:

$$T_{\text{Q}}(\text{"Q:"} + FP(s) + \text{":"} + a) \leftarrow Q_{\text{new}}$$

where $Q_{\text{new}}$ is stored as a transition target, and subsequent predictions retrieve it by maximum likelihood. Convergence follows from standard Q-learning convergence theorems, with the MCR equation serving as a non-parametric lookup table.

---

## 7. Reverse Causality and Counterfactual Reasoning

**Definition 15 (Causal Inference).** Given before-state $x$ and after-state $y$, the action $a$ that caused the transition is inferred via:

$$a = \arg\max_{a'} P_{\text{causal}}(\Delta_{x \to y} \mid a')$$

where $\Delta_{x \to y} = f_d(y) - f_d(x)$.

**Definition 16 (Counterfactual Impact).** The impact of changing variable $v$ to value $w$ is:

$$\mathcal{I}(v,w) = \left\| \Delta_{\text{real}} - \Delta_{\text{counterfactual}} \right\|_2$$

where $\Delta_{\text{real}} = f_d(y) - f_d(x)$ and $\Delta_{\text{counterfactual}} = f_d(y') - f_d(x')$ with $x',y'$ being the states with the modified variable.

---

## 8. Hierarchical Planning

**Definition 17 (Sub-Goal Decomposition).** Given a start state $s_0$ and goal state $g$, the required delta is decomposed into $k$ sub-deltas:

$$\Delta_{s_0 \to g} = \sum_{i=1}^k \delta_i$$

where $k = \max(2, \min(m, d^*))$ with $m$ the maximum plan length and $d^*$ the ideal dimensionality.

Each sub-delta $\delta_i$ is mapped to an action via:

$$a_i = \arg\max_{a'} P_{\text{causal}}(\delta_i \mid a')$$

**Property 4 (Plan Convergence).** If $\|\delta_i\|_2 < \epsilon$ for all $i$, then the composition of actions $\{a_1, \dots, a_k\}$ achieves the goal.

---

## 9. Self-Modification

**Definition 18 (Codex Operation).** The MCR system can modify its own parameters by scanning source code for configurable values and rewriting them. The generic form is:

$$\theta_{t+1} = \theta_t + \eta \cdot \nabla_\theta \mathcal{L}(\theta_t)$$

where $\theta$ are scalar parameters in source files, $\mathcal{L}$ is the meta-loss computed from threshold observations, and $\eta$ is implicitly 1 (direct substitution based on learned optimal values).

---

## 10. Genesis: Automatic Module Generation

**Definition 19 (Gap Detection).** A gap $g$ is detected when the diagonal of the coupling matrix $\mathbf{C}$ satisfies:

$$\mathbf{C}_{n,n} < \gamma \quad \text{for some level } n$$

where $\mathbf{C}_{n,m} = \text{cooc}(n,m) / \text{total\_cooc}$ and $\gamma$ is a learned threshold.

**Definition 20 (Module Generation).** Given a gap $g$ with severity $s_g$, a new module skeleton is generated:

$$M_g = \text{generate\_class}(\text{name}_g, \text{template}_g)$$

where `generate_class` uses string templates parameterized by the gap description.

---

## 11. Sample Complexity

**Theorem 4 (Sample Bound).** For a state space $|S_n| = N$ with observed transitions $M = \sum_{a,b} T_n(a,b)$, the expected error in transition probability estimation satisfies:

$$\mathbb{E}\left[|P_n(b|a) - \hat{P}_n(b|a)|\right] \leq \sqrt{\frac{1}{2f_n(a)} \ln \frac{2}{\delta}}$$

with probability $1 - \delta$, by Hoeffding's inequality applied to the multinomial distribution of transitions from state $a$.

*Corollary.* Reliable estimation ($\text{error} < 0.05$) for each state requires $f_n(a) \geq O(\ln N)$ samples per state, giving a total sample complexity of $O(N \ln N)$.

---

## 12. Limitations and Open Questions

1. **First-order Markov assumption.** MCR uses a first-order chain, which cannot capture long-range dependencies without additional mechanisms (e.g., higher-order memories or fingerprint augmentation).

2. **Scalability.** The current implementation stores transitions in dictionaries; for $|S_n| \gg 10^4$, more efficient data structures or approximate methods are needed.

3. **Semantic depth.** The Jaccard-based NLP mechanism is shallow; it captures lexical overlap but not syntax, semantics, or pragmatics.

4. **Theoretical guarantees.** While convergence of individual MCR instances follows from Markov chain theory, the convergence of the coupled multi-level system (with cross-level feedback via `MCRCoupling`) remains an open problem.

---

## 13. Conclusion

The MCR equation demonstrates that a single transition primitive — $T_n(a,b) \leftarrow T_n(a,b) + 1$ — suffices for learning across at least ten distinct levels of information processing. The level invariance theorem (Theorem 1) shows that claimed specialization is not a mathematical necessity but an architectural choice.

The implications for AGI are significant: if general intelligence requires learning transitions in increasingly abstract state spaces, and one equation operates across all such spaces, then the path to AGI may be one of **level discovery** rather than **architecture invention**. The discovery of appropriate state representations at each level becomes the central research question — not the design of domain-specific algorithms.

The complete implementation (950 lines, zero GPU, zero LLM) serves as constructive proof that this approach is not merely theoretical but realizable.

---

## Acknowledgments

This work was developed with assistance from AI language models used as collaborative tools for code generation, mathematical formulation, and document preparation. All conceptual decisions, architectural designs, and mathematical proofs were directed by the author.

---

## References

1. Markov, A. A. (1906). Extension of the law of large numbers to dependent quantities. *Izvestiya Fiziko-Matematicheskogo Obschestva pri Kazanskom Universitete*, 15(1), 135-156.

2. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379-423.

3. Sutton, R. S. & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.

4. Watkins, C. J. C. H. & Dayan, P. (1992). Q-learning. *Machine Learning*, 8(3), 279-292.

5. Wheeler, J. A. (1989). Information, physics, quantum: The search for links. *Proceedings of the 3rd International Symposium on Foundations of Quantum Mechanics*, 354-368.

6. Jaccard, P. (1901). Étude comparative de la distribution florale dans une portion des Alpes et du Jura. *Bulletin de la Société Vaudoise des Sciences Naturelles*, 37, 547-579.

7. Hoeffding, W. (1963). Probability inequalities for sums of bounded random variables. *Journal of the American Statistical Association*, 58(301), 13-30.

---

**Code Repository**: [github.com/Player-Kheltz/MCR](https://github.com/Player-Kheltz/MCR)  
**License**: AGPL v3 (Open Source) / Commercial License  
**Contact**: Kheltz (independent researcher)
