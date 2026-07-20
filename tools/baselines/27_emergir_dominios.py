"""27_emergir_dominios.py — Tiro cego entre dominios grandes.

O tiro cego funciona entre musica + emocao? Imagem + matematica?
Wikipedia + corpus matematico? Testar com corpus pesado (37K obs,
70 acoes, 5 idiomas).

Se o emergir_tudo descobre relacoes cross-dominio, o MCR pode
criar conexoes que nenhum humano fez — musica que e matematica,
emocao que e codigo, imagem que e linguagem.
"""
import sys, os, json, time, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr


def main():
    print("=" * 70)
    print("  TESTE 27 — Tiro cego entre dominios grandes")
    print("=" * 70)

    # === Motor com Wikipedia (corpus pesado) ===
    print("\n[1] Carregando motor com Wikipedia (37K obs, 70 acoes)...")
    c, info = carregar_mcr(leve=False)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # Verificar dominios presentes
    acoes = sorted(c._freq_acao.keys())
    print(f"  Acoes ({len(acoes)}): {acoes[:20]}...")
    print(f"  Amostra: {acoes[:30]}")

    sonhador = SonhoMarkoviano(c)

    # === Tiro cego em todos os niveis ===
    print("\n[2] 500 tiros cegos em todos os niveis...")
    t0 = time.time()
    tiros = sonhador.emergir_tudo(n_tiros=500)
    dt = time.time() - t0
    print(f"  Tempo: {dt:.1f}s")

    sobreviventes = [t for t in tiros if t["sobrevive"]]
    novos = [t for t in tiros if t["e_nova"]]
    cross_level = [t for t in tiros if t["cross_level"]]
    cross_novos = [t for t in tiros if t["cross_level"] and t["e_nova"]]

    print(f"  Total: {len(tiros)}")
    print(f"  Sobreviventes: {len(sobreviventes)} ({len(sobreviventes)/len(tiros)*100:.1f}%)")
    print(f"  Novos: {len(novos)} ({len(novos)/len(tiros)*100:.1f}%)")
    print(f"  Cross-level: {len(cross_level)}")
    print(f"  Cross-level novos: {len(cross_novos)}")

    # Por par de niveis
    print(f"\n  Tiros por par de niveis:")
    por_par = Counter((t["nivel_x"], t["nivel_y"]) for t in tiros)
    for (n1, n2), n in por_par.most_common():
        sob = sum(1 for t in tiros if t["nivel_x"] == n1 and t["nivel_y"] == n2 and t["sobrevive"])
        nov = sum(1 for t in tiros if t["nivel_x"] == n1 and t["nivel_y"] == n2 and t["e_nova"])
        print(f"    {n1} + {n2}: {n} tiros, {sob} sob, {nov} novos")

    # Por acao Z (descobertas por dominio)
    print(f"\n  Descobertas por acao Z (dominio):")
    por_z = Counter(t["z"] for t in novos)
    for z, n in por_z.most_common(15):
        print(f"    {z}: {n}")

    # Top descobertas
    print(f"\n  Top 20 descobertas novas:")
    for t in novos[:20]:
        cross = "CROSS" if t["cross_level"] else ""
        print(f"  NOVA {cross:5s} {t['nivel_x']:>8s}+{t['nivel_y']:<8s} "
              f"'{t['x'][:12]}'+'{t['y'][:12]}' -> {t['z'][:15]} "
              f"(conf={t['conf']}, sin={t['sinergia']:+.3f})")

    # Top cross-level
    print(f"\n  Top 10 cross-level novos:")
    for t in cross_novos[:10]:
        print(f"  {t['nivel_x']:>8s}+{t['nivel_y']:<8s} "
              f"'{t['x'][:12]}'+'{t['y'][:12]}' -> {t['z'][:15]} "
              f"(conf={t['conf']}, sin={t['sinergia']:+.3f})")

    # === Motor contaminado? ===
    print(f"\n[3] Motor contaminado?")
    print(f"  Obs: {c._total} (controle: {info['total_obs']})")
    contaminado = c._total > info['total_obs']
    print(f"  Contaminado? {'SIM' if contaminado else 'NAO'}")

    # === Salvar ===
    resultado = {
        "teste": "emergir_dominios",
        "corpus": "wikipedia_37k",
        "n_tiros": len(tiros),
        "n_sobreviventes": len(sobreviventes),
        "n_novos": len(novos),
        "n_cross_level": len(cross_level),
        "n_cross_novos": len(cross_novos),
        "taxa_sobrevivencia": len(sobreviventes) / len(tiros),
        "taxa_descoberta": len(novos) / len(tiros),
        "por_par_niveis": {f"{n1}+{n2}": {"tiros": n, "novos": nov} for (n1, n2), n in por_par.most_common()},
        "por_acao_z": dict(por_z.most_common(15)),
        "top_descobertas": novos[:20],
        "top_cross_level": cross_novos[:10],
        "motor_contaminado": contaminado,
        "tempo": dt,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "27_emergir_dominios.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
