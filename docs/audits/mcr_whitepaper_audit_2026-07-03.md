# MCR Whitepaper — Auditoria Formal

**Data:** 2026-07-03
**Auditores:** Chimera (engineering review, reprodução independente) + Leibniz (verificação formal)
**Tooling:** Z3 4.16.0, Lean 4.31 + Mathlib
**Alvo:** `docs/MCR_WHITEPAPER_PT.md` e `docs/MCR_WHITEPAPER_EN.md`

---

## Resumo

8 achados categorizados como PROVEN / REFUTED / ILL-POSED / TRUE-BUT-WEAKER / NOT-PROVEN / VACUOUS.
Cada finding tem artifact reproduzível em `docs/audits/`.

---

## Findings

### P1 — Theorem 1 é trivial (VACUOUS)

**Categoria:** VACUOUS  
**Artifact:** `mcr_audit_artifacts.py` (`p1_parametricity_witness`)

O Teorema 1 ("Level Invariance") é o *free theorem* de parametricidade (Reynolds 1983):
o quadrado natural comuta para QUALQUER implementação genérica, inclusive um stub
que não aprende nada. O whitepaper trata como se provasse capacidade real.

**Ação:** Teorema 1 renomeado para "Genericidade Paramétrica" + Observação 1
explicitando que genericidade não implica capacidade.

---

### P2 — Corollary 1 usa "aprender" equivocadamente (REFUTED)

**Categoria:** REFUTED  
**Artifact:** `mcr_audit_artifacts.py` (`p2_syllogism_invalid`)

Z3: `P1 ∧ P2_honest ∧ ¬C` é SAT (entailment inválido). O silogismo no Corolário 1
equivoca "representável como transições" com "aprendível com erro baixo".

**Ação:** Corolário 1 removido do whitepaper.

---

### P3 — Contraexemplo explícito {a,b,c} (REFUTED)

**Categoria:** REFUTED  
**Artifact:** `mcr_audit_artifacts.py` (`p3_error_floor`, `p3_z3_floor_proven`)

Análise estacionária do bigrama em Σ={a,b,c} com modo oculto X/Y:
- De a, sucessor é b (modo X, prob q) ou c (modo Y, prob 1−q)
- argmax escolhe b se q>1/2, c se q<1/2
- Erro nos passos de a: min(q, 1−q) > 0

Z3 prova que a negação (floor ≤ 0) é UNSAT para todo q∈(0,1).

**Ação:** Contraexemplo adicionado em §12.5 (PT) / §15.6 (EN).

---

### P4 — Theorem 3 (Q-learning) incompatível com Defs 1-2 (REFUTED)

**Categoria:** REFUTED  
**Artifact:** `mcr_p4_not_derivable.lean`

Def 2 (contagem): strictly increasing sobre ℕ.
Def 14 (Q-update): constant overwrite sobre ℝ.
Lean proof: se uma função u:V→V é estritamente crescente E constante,
então ∀a b:V, a=b. Sobre ℤ: 0=1 → False.
As duas primitivas são incompatíveis em tipo.

**Ação:** §6 reescrito como analogia conceitual, não incorporação formal.
Teorema 3 removido.

---

### P5 — Theorem 2 (Bridge Normalization) com normalização indefinida (ILL-POSED)

**Categoria:** ILL-POSED  
**Artifact:** `mcr_audit_artifacts.py` (`p5_entropy_exceeds_logN`)

E = −log₂(p(w)) é ilimitado. Hapax em corpus 10⁶ tokens com N=100:
E ≈ 19.93 bits > log₂(100) ≈ 6.64 bits. Prova do Teorema 2 assumia E∈[0,log₂N]
sem definir normalização.

**Ação:** Def 11a adicionada: E'(w) = clamp(−log₂p(w) / log₂N_max, 0, 1).

---

### P6 — Theorem 4 com union bound ausente (TRUE-BUT-WEAKER)

**Categoria:** TRUE-BUT-WEAKER  
**Artifact:** `mcr_audit_artifacts.py` (`p6_hoeffding_constant`)

Desigualdade per-estado está correta. Falta union bound para garantir
simultaneidade sobre N estados: δ → δ/N. ln(2N/δ) = ln(2/δ) + ln N = Θ(ln N).
O(N ln N) sobrevive.

**Ação:** Union bound adicionado na demonstração do Corolário do Teorema 4.

---

### P7 — §13 → AGI não se sustenta (NOT-PROVEN)

**Categoria:** NOT-PROVEN  
**Artifact:** N/A (análise lógica)

Três premissas não declaradas:
1. Toda tarefa reduz-se a contagem de transições (refutada por P3)
2. MCR aprende genuinamente cada uma (refutada por P3)
3. Reusabilidade sintática ⇒ competência semântica (não justificada)

A conclusão AGI é um não-sequitur.

**Ação:** §13 reescrito completamente. AGI substituído pelo Teorema 5
(Universalidade Condicional). Seções adicionadas: 13.1-13.5.

---

### P8 — Teorema verdadeiro (PROVEN)

**Categoria:** PROVEN  
**Artifact:** N/A (derivação matemática)

Para qualquer processo Markov estacionário de ordem k sobre Σ,
defina S̃ = Σᵏ. Então o processo é Markov de 1ª ordem sobre S̃,
e MCR converge para P(σ_{t+1}|s̃) com complexidade O(|Σ|ᵏ ln|Σ|ᵏ).

**Ação:** Adicionado como Teorema 5 em §13.2 (PT e EN).

---

## Artefatos

| Arquivo | Conteúdo |
|---------|----------|
| `mcr_audit_artifacts.py` | Python + Z3: P1, P2, P3, P5, P6 |
| `mcr_p4_not_derivable.lean` | Lean 4: P4 (kernel-checked, 0 sorries) |

## Verificação

- Z3 4.16.0: todos os modelos SAT/UNSAT confirmados
- Lean 4.31 + Mathlib: `#check` 0 errors, 0 warnings, 0 sorries
- Python 3.12+: script auto-verificado (`assert` no `main`)
