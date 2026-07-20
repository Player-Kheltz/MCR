"""26_emergir_tudo.py — Tiro cego em TODOS os niveis.

X + Y = Z nao e so sobre palavras. E sobre TUDO.
Byte + byte. Char + char. Token + token. Feature + feature.
Cluster + cluster. Cross-level: byte + token, feature + cluster.

Como mutacao biologica: pode acontecer em qualquer nivel.
O motor e a selecao natural que valida.
"""
import sys, os, json, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr


def main():
    print("=" * 70)
    print("  TESTE 26 — Tiro cego em TODOS os niveis (mutacao multi-escala)")
    print("=" * 70)

    print("\n[1] Carregando motor...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    sonhador = SonhoMarkoviano(c)

    # === Tiro cego em todos os niveis ===
    print("\n[2] 200 tiros cegos em todos os niveis...")
    t0 = time.time()
    tiros = sonhador.emergir_tudo(n_tiros=200)
    dt = time.time() - t0
    print(f"  Tempo: {dt:.1f}s")

    sobreviventes = [t for t in tiros if t["sobrevive"]]
    novos = [t for t in tiros if t["e_nova"]]
    cross_level = [t for t in tiros if t["cross_level"]]
    cross_novos = [t for t in tiros if t["cross_level"] and t["e_nova"]]

    print(f"  Total: {len(tiros)}")
    print(f"  Sobreviventes (sinergia > 0.05): {len(sobreviventes)} ({len(sobreviventes)/len(tiros)*100:.1f}%)")
    print(f"  Novos (nao coocorrem + sobrevivem): {len(novos)} ({len(novos)/len(tiros)*100:.1f}%)")
    print(f"  Cross-level: {len(cross_level)}")
    print(f"  Cross-level novos: {len(cross_novos)}")

    # Por nivel
    print(f"\n  Tiros por par de niveis:")
    por_par = Counter((t["nivel_x"], t["nivel_y"]) for t in tiros)
    for (n1, n2), n in por_par.most_common():
        sob = sum(1 for t in tiros if t["nivel_x"] == n1 and t["nivel_y"] == n2 and t["sobrevive"])
        print(f"    {n1} + {n2}: {n} tiros, {sob} sobreviventes")

    # Por acao Z
    print(f"\n  Descobertas por acao Z:")
    por_z = Counter(t["z"] for t in novos)
    for z, n in por_z.most_common():
        print(f"    {z}: {n}")

    # Top descobertas
    print(f"\n  Top 15 descobertas (todas):")
    for t in sobreviventes[:15]:
        cross = "CROSS" if t["cross_level"] else ""
        novo = "NOVA" if t["e_nova"] else ""
        print(f"  {novo:4s} {cross:5s} {t['nivel_x']:>8s}+{t['nivel_y']:<8s} "
              f"'{t['x'][:10]}'+'{t['y'][:10]}' -> {t['z'][:12]} "
              f"(conf={t['conf']}, sin={t['sinergia']:+.3f})")

    # Top cross-level
    print(f"\n  Top 10 cross-level:")
    for t in cross_novos[:10]:
        print(f"  {t['nivel_x']:>8s}+{t['nivel_y']:<8s} "
              f"'{t['x'][:10]}'+'{t['y'][:10]}' -> {t['z'][:12]} "
              f"(conf={t['conf']}, sin={t['sinergia']:+.3f})")

    # === Motor contaminado? ===
    print(f"\n[3] Motor contaminado?")
    print(f"  Obs: {c._total} (controle: {info['total_obs']})")
    contaminado = c._total > info['total_obs']
    print(f"  Contaminado? {'SIM' if contaminado else 'NAO'}")

    # === Salvar ===
    resultado = {
        "teste": "emergir_tudo",
        "n_tiros": len(tiros),
        "n_sobreviventes": len(sobreviventes),
        "n_novos": len(novos),
        "n_cross_level": len(cross_level),
        "n_cross_novos": len(cross_novos),
        "taxa_sobrevivencia": len(sobreviventes) / len(tiros),
        "taxa_descoberta": len(novos) / len(tiros),
        "por_par_niveis": {f"{n1}+{n2}": n for (n1, n2), n in por_par.most_common()},
        "por_acao_z": dict(por_z),
        "top_descobertas": sobreviventes[:15],
        "top_cross_level": cross_novos[:10],
        "motor_contaminado": contaminado,
        "tempo": dt,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "26_emergir_tudo.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
