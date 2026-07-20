"""19_trinidade_sonho.py — O numero 3 e estavel no sonho?

Hipotese do Kheltz: 3/10 unicos nao e limitacao, e estrutura.
O 3 aparece em 4 lugares independentes. Se for structural,
3 sonhos unicos devem ser estaveis em qualquer numero de ciclos.

Testes:
1. Rodar 30 ciclos — 3 unicos se mantem?
2. Rodar 50 ciclos — 3 unicos se mantem?
3. Analisar os 3 sonhos unicos: sao tese/antitese/sintese?
4. Gerar EXATAMENTE 3 sonhos (parar apos 3 unicos) — qualidade?
"""
import sys, os, json, time, re
from collections import Counter
from math import log2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr


def entropia_tokens(toks):
    if not toks:
        return 0.0
    cont = Counter(toks)
    n = len(toks)
    h = 0.0
    for c in cont.values():
        p = c / n
        if p > 0:
            h -= p * log2(p)
    return h


def rodar_ciclos(c, n_ciclos, modo="entropia"):
    """Roda n_ciclos de sonho e retorna os unicos em ordem."""
    sonhador = SonhoMarkoviano(c)
    sonhos_unicos = []
    hashes_vistos = set()
    detalhes = []

    semente_atual = None
    for i in range(n_ciclos):
        if semente_atual is None:
            semente = sonhador._serializar_estado()
        else:
            semente = semente_atual

        sonho = sonhador.sonhar(n_passos=30, semente=semente, modo=modo)
        tokens = sonhador._RE_TOKENS.findall(sonho.lower())
        h = entropia_tokens(tokens)

        hash_sonho = sonho[:100]
        is_novo = hash_sonho not in hashes_vistos
        hashes_vistos.add(hash_sonho)

        if is_novo:
            sonhos_unicos.append({
                "ciclo": i + 1,
                "n_tokens": len(tokens),
                "entropia": round(h, 3),
                "preview": sonho[:150],
                "tokens": tokens[:30],
            })

        detalhes.append({
            "ciclo": i + 1,
            "is_novo": is_novo,
            "entropia": round(h, 3),
        })

        # Proxima semente
        if tokens:
            estado = sonhador._serializar_estado(max_tokens=50)
            final = " ".join(tokens[-15:])
            semente_atual = final + " " + estado

        # Alimentar de volta
        c.alimentar(sonho, "sonhar")

    return sonhos_unicos, detalhes


def main():
    print("=" * 70)
    print("  TESTE 19 — O numero 3 e estavel no sonho? (Trindade)")
    print("=" * 70)

    # === Teste 1: 30 ciclos ===
    print("\n[1] 30 ciclos de sonho (entropia)...")
    c1, _ = carregar_mcr(leve=True)
    unicos_30, det_30 = rodar_ciclos(c1, n_ciclos=30, modo="entropia")
    print(f"  Sonhos unicos em 30 ciclos: {len(unicos_30)}")
    for i, s in enumerate(unicos_30):
        print(f"    Unico #{i+1} (ciclo {s['ciclo']}): H={s['entropia']}, "
              f"tokens={s['n_tokens']}")
        print(f"      '{s['preview'][:80]}'")

    # === Teste 2: 50 ciclos ===
    print("\n[2] 50 ciclos de sonho (entropia)...")
    c2, _ = carregar_mcr(leve=True)
    unicos_50, det_50 = rodar_ciclos(c2, n_ciclos=50, modo="entropia")
    print(f"  Sonhos unicos em 50 ciclos: {len(unicos_50)}")
    for i, s in enumerate(unicos_50):
        print(f"    Unico #{i+1} (ciclo {s['ciclo']}): H={s['entropia']}")

    # === Teste 3: 50 ciclos greedy (comparar) ===
    print("\n[3] 50 ciclos de sonho (greedy)...")
    c3, _ = carregar_mcr(leve=True)
    unicos_greedy, det_greedy = rodar_ciclos(c3, n_ciclos=50, modo="greedy")
    print(f"  Sonhos unicos em 50 ciclos (greedy): {len(unicos_greedy)}")

    # === Teste 4: 3 e estavel? ===
    print("\n[4] O numero 3 e estavel?")
    print(f"  10 ciclos entropia:  3 unicos (teste anterior)")
    print(f"  30 ciclos entropia:  {len(unicos_30)} unicos")
    print(f"  50 ciclos entropia:  {len(unicos_50)} unicos")
    print(f"  50 ciclos greedy:    {len(unicos_greedy)} unicos")

    # === Teste 5: Analisar os 3 sonhos unicos ===
    print("\n[5] Analisar os 3 sonhos unicos (30 ciclos)...")
    if len(unicos_30) >= 3:
        for i, s in enumerate(unicos_30[:3]):
            tokens = s["tokens"]
            print(f"\n  Sonho #{i+1} (ciclo {s['ciclo']}, H={s['entropia']}):")
            print(f"    Tokens: {tokens[:20]}")

            # Que acoes este sonho toca?
            acoes_tocadas = Counter()
            for t in tokens:
                dist = c1._palavra_acao.get(t, {})
                for a in dist:
                    acoes_tocadas[a] += 1
            top_acoes = acoes_tocadas.most_common(5)
            print(f"    Acoes tocadas: {top_acoes}")

            # Pertencimento: quantos clusters?
            # (simplificado: quantas acoes distintas)
            print(f"    Acoes distintas: {len(acoes_tocadas)}")

        # Tese/Antitese/Sintese?
        print("\n  Analise tese/antitese/sintese:")
        if len(unicos_30) >= 3:
            s1, s2, s3 = unicos_30[0], unicos_30[1], unicos_30[2]
            # Overlap entre sonhos
            t1, t2, t3 = set(s1["tokens"]), set(s2["tokens"]), set(s3["tokens"])
            overlap_12 = len(t1 & t2) / max(1, len(t1 | t2))
            overlap_13 = len(t1 & t3) / max(1, len(t1 | t3))
            overlap_23 = len(t2 & t3) / max(1, len(t2 | t3))
            print(f"    Overlap 1-2: {overlap_12:.3f}")
            print(f"    Overlap 1-3: {overlap_13:.3f}")
            print(f"    Overlap 2-3: {overlap_23:.3f}")
            print(f"    Tokens so no 1: {len(t1 - t2 - t3)}")
            print(f"    Tokens so no 2: {len(t2 - t1 - t3)}")
            print(f"    Tokens so no 3: {len(t3 - t1 - t2)}")
            print(f"    Tokens em todos: {len(t1 & t2 & t3)}")

    # === Salvar ===
    resultado = {
        "teste": "trindade_sonho",
        "ciclos_30_entropia": {"n_unicos": len(unicos_30), "unicos": unicos_30},
        "ciclos_50_entropia": {"n_unicos": len(unicos_50), "unicos": unicos_50},
        "ciclos_50_greedy": {"n_unicos": len(unicos_greedy)},
        "numero_3_estavel": len(unicos_30) == 3 and len(unicos_50) == 3,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "19_trindade_sonho.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")

    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO — O numero 3 e estavel?")
    print("=" * 70)
    print(f"  10 ciclos:  3 unicos")
    print(f"  30 ciclos:  {len(unicos_30)} unicos")
    print(f"  50 ciclos:  {len(unicos_50)} unicos")
    print(f"  Greedy 50:  {len(unicos_greedy)} unicos")
    estavel = len(unicos_30) == 3 and len(unicos_50) == 3
    print(f"\n  3 e estavel? {'SIM' if estavel else 'NAO'}")


if __name__ == "__main__":
    main()
