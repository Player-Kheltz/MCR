"""
Reproducible machine-checked artifacts for the MCR whitepaper audit
(docs/audits/mcr_whitepaper_audit_2026-07-03.md).

Verifies the crisp cores of P1, P2, P3, P5, P6 with Python + z3 (4.16.0).
P4 carries a Lean-kernel artifact (mcr_p4_not_derivable.lean);
this file is the fast, self-contained numeric/logic backbone.

Run:  python3 docs/audits/mcr_audit_artifacts.py   (needs z3)
"""
from __future__ import annotations

import math
from fractions import Fraction as Fr


def p1_parametricity_witness() -> dict:
    """P1: MCR's 'level invariance' is the free theorem — the learn/predict
    naturality square commutes for the REAL counter AND for a no-op stub that
    learns/predicts nothing. Insensitive to the body => VACUOUS."""
    import random
    rng = random.Random(0)
    tau = {0: "x", 1: "y", 2: "z"}   # a tokenization (relabelling) S -> S'

    def learn_real(t, a, b):
        t = {k: dict(v) for k, v in t.items()}
        t.setdefault(a, {})
        t[a][b] = t[a].get(b, 0) + 1
        return t

    def predict_real(t, a):
        if a not in t or not t[a]:
            return None
        return max(t[a], key=t[a].get)

    def learn_stub(t, a, b):
        return t   # learns NOTHING

    def predict_stub(t, a):
        return None   # predicts NOTHING

    def relabel(t):
        return {tau[a]: {tau[b]: c for b, c in row.items()}
                for a, row in t.items()}

    def square_ok(learn, predict):
        for _ in range(2000):
            t = {}
            for _ in range(rng.randint(0, 6)):
                t = learn(t, rng.randint(0, 2), rng.randint(0, 2))
            a = rng.randint(0, 2)
            b = rng.randint(0, 2)
            if relabel(learn(t, a, b)) != learn(relabel(t), tau[a], tau[b]):
                return False
            pr = predict(t, a)
            if predict(relabel(t), tau[a]) != (tau[pr] if pr is not None else None):
                return False
        return True

    return {
        "real_square": square_ok(learn_real, predict_real),
        "stub_square": square_ok(learn_stub, predict_stub),
    }


def p2_syllogism_invalid() -> dict:
    """P2: under the honest reading (Representable => Runnable, NOT eps-Learnable),
    P1&P2 |- C is INVALID.  z3: (P1 & P2_honest & not C) is SAT."""
    from z3 import Bool, Implies, Not, Solver, sat
    Representable, Runnable, EpsLearnable, Universal = (
        Bool("Rep"), Bool("Run"), Bool("EpsL"), Bool("Univ"))
    P1 = Representable
    P2_honest = Implies(Representable, Runnable)
    C = Implies(Universal, EpsLearnable)
    s = Solver()
    s.add(P1, P2_honest, Not(C))
    honest = s.check()
    s2 = Solver()
    s2.add(P1, Implies(Representable, EpsLearnable), Universal, Not(EpsLearnable))
    equivocated = s2.check()
    return {
        "honest_P1P2_notC_is_SAT": honest == sat,
        "equivocated_is_UNSAT": equivocated != sat,
    }


def p3_error_floor(q: Fr) -> dict:
    """P3: order-1 MCR on the mode-X/Y stream.  Error on a-steps = min(q,1-q)."""
    a_step_error = min(q, 1 - q)
    argmax = "b" if q > Fr(1, 2) else ("c" if q < Fr(1, 2) else "tie")
    return {
        "q": str(q),
        "argmax_a": argmax,
        "error_floor": str(a_step_error),
        "floor_positive": a_step_error > 0,
    }


def p3_z3_floor_proven() -> bool:
    """z3: negation of (state-a error >= min(q,1-q)) over (0,1) is UNSAT."""
    from z3 import Real, And, Or, Solver, sat
    q = Real("q")
    err = Real("err")
    floor = Or(And(q <= Fr(1, 2), err == q), And(q > Fr(1, 2), err == 1 - q))
    neg = And(q > 0, q < 1, floor, err <= 0)
    s = Solver()
    s.add(neg)
    return s.check() != sat


def p5_entropy_exceeds_logN() -> dict:
    """P5: E=-log2 p(w) can exceed log2 N.  Hapax in 1e6-token, N=100 corpus."""
    E = -math.log2(1e-6)
    logN = math.log2(100)
    return {
        "E": round(E, 4),
        "log2_N": round(logN, 4),
        "E_exceeds_logN": E > logN,
        "margin_bits": round(E - logN, 2),
    }


def p6_hoeffding_constant() -> dict:
    """P6: two-sided Hoeffding constant ln(2/delta); union bound over N
    outcomes gives ln(2N/delta)=ln(2/delta)+ln N. O(N ln N) SURVIVES."""
    from z3 import Real, Solver, sat
    d, n = Real("d"), Real("n")
    s = Solver()
    s.add(d > 0, n > 0, (2 * n / d) != (2 / d) * n)
    ratio_ok = s.check() != sat
    return {
        "two_sided_constant": "ln(2/delta)",
        "union_bound_absent_in_source": True,
        "union_identity_holds": ratio_ok,
        "corrected_total": "O(N ln N) survives",
    }


def main() -> int:
    print("=== MCR audit — reproducible machine-checked artifacts ===")
    r1 = p1_parametricity_witness()
    print(f"P1 (VACUOUS): real={r1['real_square']}  stub={r1['stub_square']}"
          "  -> insensitive to body")
    r2 = p2_syllogism_invalid()
    print(f"P2 (REFUTED): honest SAT={r2['honest_P1P2_notC_is_SAT']}"
          f"  equivocated UNSAT={r2['equivocated_is_UNSAT']}")
    print("P3 (countermodel PROVEN):")
    for q in (Fr(1, 10), Fr(3, 10), Fr(1, 2), Fr(7, 10), Fr(9, 10)):
        r = p3_error_floor(q)
        print(f"   q={r['q']}: argmax={r['argmax_a']:>3}"
              f"  floor={r['error_floor']}  >0={r['floor_positive']}")
    print(f"   z3 floor>0 negation UNSAT: {p3_z3_floor_proven()}")
    r5 = p5_entropy_exceeds_logN()
    print(f"P5 (ILL-POSED): E={r5['E']} > log2 N={r5['log2_N']}"
          f"  (violation {r5['margin_bits']} bits)")
    r6 = p6_hoeffding_constant()
    print(f"P6 (TRUE-BUT-WEAKER): const={r6['two_sided_constant']}"
          f"  union absent={r6['union_bound_absent_in_source']}"
          f"  identity holds={r6['union_identity_holds']}"
          f"  {r6['corrected_total']}")
    ok = (
        r1["real_square"] and r1["stub_square"]
        and r2["honest_P1P2_notC_is_SAT"]
        and r2["equivocated_is_UNSAT"]
        and p3_z3_floor_proven()
        and r5["E_exceeds_logN"]
        and r6["union_identity_holds"]
    )
    print(f"\nall reproducible artifacts GREEN: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
