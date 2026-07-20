"""24_emergir.py — O sonho como EMERGIR: 'E se X + Y = Z?'

Como Kheltz faz 'decida, explore, valide' com o LLM, o MCR faz
consigo mesmo. O sonho pergunta 'E se?', o motor valida.

1. DECIDA: sonho escolhe conceitos do vocabulario
2. EXPLORE: recombina markovianamente
3. VALIDE: motor verifica se a recombinação tem estrutura
4. Se valido: nova relacao descoberta. Se nao: descarta.

Testes:
1. emergir(): recombina conceitos que coocorrem (sinergia conhecida)
2. emergir_livre(): recombina conceitos que NUNCA coocorrem (novidade)
3. Quantas hipoteses sao confirmadas? Quantas sao novas?
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr


def main():
    print("=" * 70)
    print("  TESTE 24 — Emergir: o MCR pergunta 'E se X + Y = Z?'")
    print("=" * 70)

    # Carregar motor
    print("\n[1] Carregando motor...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    sonhador = SonhoMarkoviano(c)

    # === Emergir (sinergia conhecida) ===
    print("\n[2] Emergir: 'E se X + Y?' (conceitos que coocorrem)...")
    hipoteses = sonhador.emergir(n_hipoteses=30)

    confirmadas = [h for h in hipoteses if h["confirmada"]]
    print(f"  {len(hipoteses)} hipoteses, {len(confirmadas)} confirmadas")

    print(f"\n  Top 10 por sinergia:")
    for h in hipoteses[:10]:
        status = "OK" if h["confirmada"] else "REF"
        print(f"  {status} '{h['x']}' + '{h['y']}' -> {h['acao']} "
              f"(conf={h['conf']}, sinergia={h['sinergia']:+.3f})")
        print(f"       X isolado: {h['acao_x']} ({h['conf_x']})")
        print(f"       Y isolado: {h['acao_y']} ({h['conf_y']})")

    # === Emergir livre (novidade) ===
    print(f"\n[3] Emergir livre: 'E se X + Y?' (conceitos que NUNCA coocorrem)...")
    hipoteses_livres = sonhador.emergir_livre(n_hipoteses=50)

    novas = [h for h in hipoteses_livres if h["e_nova"]]
    confirmadas_livres = [h for h in hipoteses_livres if h["confirmada"]]
    print(f"  {len(hipoteses_livres)} hipoteses livres")
    print(f"  {len(confirmadas_livres)} confirmadas (sinergia > 0.05)")
    print(f"  {len(novas)} NOVAS (nunca coocorrem + confirmadas)")

    print(f"\n  Top 10 livres por sinergia:")
    for h in hipoteses_livres[:10]:
        status = "NOVA" if h["e_nova"] else ("OK" if h["confirmada"] else "REF")
        cooc = "sim" if h["coocorre_no_corpus"] else "NAO"
        print(f"  {status:4s} '{h['x'][:15]}' + '{h['y'][:15]}' -> {h['acao'][:12]} "
              f"(conf={h['conf']}, sinergia={h['sinergia']:+.3f}, cooc={cooc})")

    # === Analise ===
    print(f"\n[4] Analise:")
    print(f"  Emergir (conhecido):")
    print(f"    Hipoteses: {len(hipoteses)}")
    print(f"    Confirmadas: {len(confirmadas)} ({len(confirmadas)/max(1,len(hipoteses))*100:.1f}%)")
    if confirmadas:
        sinergias = [h["sinergia"] for h in confirmadas]
        print(f"    Sinergia media: {sum(sinergias)/len(sinergias):.3f}")
        print(f"    Sinergia max: {max(sinergias):.3f}")

    print(f"  Emergir livre (novidade):")
    print(f"    Hipoteses: {len(hipoteses_livres)}")
    print(f"    Confirmadas: {len(confirmadas_livres)} ({len(confirmadas_livres)/max(1,len(hipoteses_livres))*100:.1f}%)")
    print(f"    Novas (nao coocorrem + confirmadas): {len(novas)}")
    if novas:
        print(f"\n  Descobertas novas:")
        for h in novas[:10]:
            print(f"    '{h['x']}' + '{h['y']}' -> {h['acao']} "
                  f"(conf={h['conf']}, sinergia={h['sinergia']:+.3f})")

    # === Motor contaminado? ===
    print(f"\n[5] Motor contaminado?")
    print(f"  Obs: {c._total} (controle: {info['total_obs']})")
    print(f"  Vocab: {len(c._palavra_acao)} (controle: {info['vocab']})")
    print(f"  freq_sonhar: {c._freq_acao.get('sonhar', 0)}")
    contaminado = c._total > info['total_obs']
    print(f"  Contaminado? {'SIM' if contaminado else 'NAO'}")

    # === Salvar ===
    resultado = {
        "teste": "emergir",
        "emergir_conhecido": {
            "n_hipoteses": len(hipoteses),
            "n_confirmadas": len(confirmadas),
            "taxa_confirmacao": len(confirmadas) / max(1, len(hipoteses)),
            "top": hipoteses[:10],
        },
        "emergir_livre": {
            "n_hipoteses": len(hipoteses_livres),
            "n_confirmadas": len(confirmadas_livres),
            "n_novas": len(novas),
            "taxa_confirmacao": len(confirmadas_livres) / max(1, len(hipoteses_livres)),
            "top": hipoteses_livres[:10],
        },
        "motor_contaminado": contaminado,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "24_emergir.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
