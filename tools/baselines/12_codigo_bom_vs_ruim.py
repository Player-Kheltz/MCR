"""12_codigo_bom_vs_ruim.py — Discriminação de qualidade de código do zero.

Teste NOVO. MCR distingue código "bom" (conciso, pythonico) de
"ruim" (verboso, redundante) sem nunca ter visto exemplos classificados.

Original (Fase 7): entropia 4/5, dimensão 5/5.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr

CODIGOS_BONS = [
    "sorted(xs)",
    "with open(f) as h: h.read()",
    "sum(x for x in xs)",
    "[x*2 for x in xs]",
    "dict(zip(ks, vs))",
    "any(x > 0 for x in xs)",
    "max(xs, key=len)",
    "collections.Counter(xs)",
    "map(str, xs)",
    "filter(None, xs)",
    "x if x else y",
    "lambda x: x + 1",
    "set.intersection(a, b)",
    "os.path.join(a, b)",
    "json.dumps(d)",
    "' '.join(words)",
    "xs[::-1]",
    "enumerate(xs)",
    "isinstance(x, int)",
    "print(f'{x}')",
]

CODIGOS_RUINS = [
    "result = []\nfor x in xs:\n    result.append(x * 2)\nreturn result",
    "if x == True:\n    return True\nelse:\n    return False",
    "try:\n    do_thing()\nexcept:\n    pass",
    "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]",
    "total = 0\nfor i in range(len(xs)):\n    total = total + xs[i]\nreturn total",
    "if x != None:\n    do_thing()",
    "while True:\n    if cond:\n        break\n    do_other()",
    "result = {}\nfor i in range(len(ks)):\n    result[ks[i]] = vs[i]\nreturn result",
    "if len(xs) > 0:\n    return xs[0]\nelse:\n    return None",
    "for i in range(len(arr)):\n    print(arr[i])",
    "if type(x) == int:\n    do_thing()",
    "result = ''\nfor w in words:\n    result = result + w + ' '\nreturn result",
    "if x == '':\n    x = None",
    "def func():\n    global x\n    x = x + 1\n    return x",
    "import os, sys, re, json, time, math\nimport os",
    "if not x in ys:\n    do_thing()",
    "return 0 if x == 0 else x",
    "names = []\nfor p in people:\n    names.append(p.name)",
    "if x > 0 and x > 0:\n    do_thing()",
    "d = dict()\nd['a'] = 1\nd['b'] = 2\nd['c'] = 3",
]


def entropia_shannon(tokens):
    """Entropia de Shannon de uma lista de tokens."""
    from collections import Counter
    from math import log2
    cont = Counter(tokens)
    n = len(tokens)
    if n == 0:
        return 0.0
    h = 0.0
    for c in cont.values():
        p = c / n
        if p > 0:
            h -= p * log2(p)
    return h


def tokenizar_codigo(codigo):
    """Tokeniza codigo em tokens simples."""
    import re
    return re.findall(r'[a-zA-Z_]\w*|\S', codigo)


def extrair_features(codigo):
    """Extrai features do codigo para MCR."""
    tokens = tokenizar_codigo(codigo)
    return {
        "n_tokens": len(tokens),
        "n_uniq": len(set(tokens)),
        "entropia": entropia_shannon(tokens),
        "n_linhas": codigo.count("\n") + 1,
        "densidade": len(tokens) / (codigo.count("\n") + 1),
    }


def testar_mcr_entropia(codigos_bons, codigos_ruins):
    """Testa MCR discriminando por entropia de tokens.

    Hipotese: codigo bom tem entropia MAIOR (mais diverso, menos repeticao).
    """
    hs_bons = [extrair_features(c)["entropia"] for c in codigos_bons]
    hs_ruins = [extrair_features(c)["entropia"] for c in codigos_ruins]

    med_bom = sum(hs_bons) / len(hs_bons)
    med_ruim = sum(hs_ruins) / len(hs_ruins)

    # Threshold = media das medias
    th = (med_bom + med_ruim) / 2

    # Classifica: H > th = bom, H <= th = ruim
    acertos = 0
    for h in hs_bons:
        if h > th:
            acertos += 1
    for h in hs_ruins:
        if h <= th:
            acertos += 1

    return acertos, len(hs_bons) + len(hs_ruins), med_bom, med_ruim, th


def testar_mcr_densidade(codigos_bons, codigos_ruins):
    """Testa MCR discriminando por densidade (tokens/linha).

    Hipotese: codigo bom tem densidade MAIOR (mais conciso por linha).
    """
    ds_bons = [extrair_features(c)["densidade"] for c in codigos_bons]
    ds_ruins = [extrair_features(c)["densidade"] for c in codigos_ruins]

    med_bom = sum(ds_bons) / len(ds_bons)
    med_ruim = sum(ds_ruins) / len(ds_ruins)
    th = (med_bom + med_ruim) / 2

    acertos = 0
    for d in ds_bons:
        if d > th:
            acertos += 1
    for d in ds_ruins:
        if d <= th:
            acertos += 1

    return acertos, len(ds_bons) + len(ds_ruins), med_bom, med_ruim, th


def testar_mcr_nuniq(codigos_bons, codigos_ruins):
    """Testa MCR discriminando por nº de tokens únicos."""
    us_bons = [extrair_features(c)["n_uniq"] for c in codigos_bons]
    us_ruins = [extrair_features(c)["n_uniq"] for c in codigos_ruins]

    med_bom = sum(us_bons) / len(us_bons)
    med_ruim = sum(us_ruins) / len(us_ruins)
    th = (med_bom + med_ruim) / 2

    acertos = 0
    for u in us_bons:
        if u > th:
            acertos += 1
    for u in us_ruins:
        if u <= th:
            acertos += 1

    return acertos, len(us_bons) + len(us_ruins), med_bom, med_ruim, th


def testar_baseline_aleatorio(n):
    """Baseline: 50% (chance)."""
    return n // 2


def main():
    print("=" * 70)
    print("  TESTE 12 — Código bom vs ruim: MCR vs Baseline (do zero)")
    print("=" * 70)

    n = len(CODIGOS_BONS) + len(CODIGOS_RUINS)
    print(f"\nDataset: {len(CODIGOS_BONS)} bons, {len(CODIGOS_RUINS)} ruins, {n} total")

    print("\n--- Features extraidas (medias) ---")
    feats_bons = [extrair_features(c) for c in CODIGOS_BONS]
    feats_ruins = [extrair_features(c) for c in CODIGOS_RUINS]
    for k in feats_bons[0]:
        mb = sum(f[k] for f in feats_bons) / len(feats_bons)
        mr = sum(f[k] for f in feats_ruins) / len(feats_ruins)
        delta = mb - mr
        direcao = "bom>ruim" if delta > 0 else "ruim>bom"
        print(f"  {k:>12s}: bom={mb:.2f} ruim={mr:.2f} delta={delta:+.2f} ({direcao})")

    print("\n--- MCR (entropia) ---")
    ac_e, tot_e, mb_e, mr_e, th_e = testar_mcr_entropia(CODIGOS_BONS, CODIGOS_RUINS)
    print(f"Acertos: {ac_e}/{tot_e} = {ac_e/tot_e*100:.1f}%")
    print(f"  H(bom)={mb_e:.2f}, H(ruim)={mr_e:.2f}, th={th_e:.2f}")

    print("\n--- MCR (densidade) ---")
    ac_d, tot_d, mb_d, mr_d, th_d = testar_mcr_densidade(CODIGOS_BONS, CODIGOS_RUINS)
    print(f"Acertos: {ac_d}/{tot_d} = {ac_d/tot_d*100:.1f}%")
    print(f"  D(bom)={mb_d:.2f}, D(ruim)={mr_d:.2f}, th={th_d:.2f}")

    print("\n--- MCR (n_uniq) ---")
    ac_u, tot_u, mb_u, mr_u, th_u = testar_mcr_nuniq(CODIGOS_BONS, CODIGOS_RUINS)
    print(f"Acertos: {ac_u}/{tot_u} = {ac_u/tot_u*100:.1f}%")
    print(f"  U(bom)={mb_u:.2f}, U(ruim)={mr_u:.2f}, th={th_u:.2f}")

    print("\n--- Baseline aleatorio ---")
    ac_rand = testar_baseline_aleatorio(n)
    print(f"Acertos: {ac_rand}/{n} = {ac_rand/n*100:.1f}%")

    print("\n--- Comparacao ---")
    tx_e = ac_e / tot_e
    tx_d = ac_d / tot_d
    tx_u = ac_u / tot_u
    tx_r = ac_rand / n
    print(f"Entropia:  {tx_e*100:.1f}% vs {tx_r*100:.1f}% ({tx_e/tx_r:.1f}x)")
    print(f"Densidade: {tx_d*100:.1f}% vs {tx_r*100:.1f}% ({tx_d/tx_r:.1f}x)")
    print(f"N_uniq:    {tx_u*100:.1f}% vs {tx_r*100:.1f}% ({tx_u/tx_r:.1f}x)")

    resultado = {
        "teste": "codigo_bom_vs_ruim",
        "n_bons": len(CODIGOS_BONS),
        "n_ruins": len(CODIGOS_RUINS),
        "mcr_entropia": {"acertos": ac_e, "total": tot_e, "taxa": tx_e,
                         "H_bom": mb_e, "H_ruim": mr_e, "threshold": th_e},
        "mcr_densidade": {"acertos": ac_d, "total": tot_d, "taxa": tx_d,
                          "D_bom": mb_d, "D_ruim": mr_d, "threshold": th_d},
        "mcr_nuniq": {"acertos": ac_u, "total": tot_u, "taxa": tx_u,
                      "U_bom": mb_u, "U_ruim": mr_u, "threshold": th_u},
        "baseline_aleatorio": {"acertos": ac_rand, "total": n, "taxa": tx_r},
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "12_codigo_bom_vs_ruim.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
