"""28_score_relevancia.py — Score de Relevância Estrutural mata falsos positivos?

Testar se decidir_relevante() (P*IDF*Lift) elimina os falsos positivos
do decidir() bruto (P(b|a) puro).

Falsos positivos conhecidos:
- 'PG' + 'b:105' -> gerar_npc (conf=1.0) — IMPOSSIVEL
- '7' + 'e' -> gato (conf=0.86) — espurio
- '"1"' + '56' -> cavalo (conf=0.97) — espurio

Se decidir_relevante() rebaixa esses para ~0, a formula funciona.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from corpus_matematico import validar_corpus_matematico


def main():
    print("=" * 70)
    print("  TESTE 28 — Score de Relevancia Estrutural vs P(b|a) bruto")
    print("=" * 70)

    # === Motor leve (teste 26) ===
    print("\n[1] Motor leve (matematico + dataset_500)...")
    c_leve, _ = carregar_mcr(leve=True)
    print(f"  {c_leve._total} obs, {len(c_leve._palavra_acao)} pal")

    # Falsos positivos do teste 26
    print("\n[2] Falsos positivos do teste 26 (motor leve):")
    falsos_26 = [
        ("PG b:105", "gerar_npc"),  # conf=1.0, sin=+1.0 — IMPOSSIVEL
        ("b:101 PG", "gerar_npc"),  # conf=1.0, sin=+1.0
        ("w r", "gerar_monstro"),   # conf=1.0, sin=+1.0
        ("f u", "responder"),       # conf=0.99
        ("f i", "gerar_npc"),       # conf=0.98
    ]

    print(f"  {'Input':<20s} {'Esperado(falso)':<18s} {'decidir()':<25s} {'decidir_relevante()':<25s}")
    print("  " + "-" * 90)

    for texto, esp_falso in falsos_26:
        a_raw, conf_raw = c_leve.decidir(texto, (None, 0.0))
        a_rel, conf_rel = c_leve.decidir_relevante(texto, (None, 0.0))
        print(f"  {texto:<20s} {esp_falso:<18s} {a_raw[:12]} ({conf_raw:.3f}){'':>5s} "
              f"{a_rel[:12]} ({conf_rel:.3f})")

    # === Motor pesado (teste 27) ===
    print(f"\n[3] Motor pesado (Wikipedia 37K)...")
    c_pes, _ = carregar_mcr(leve=False)
    print(f"  {c_pes._total} obs, {len(c_pes._palavra_acao)} pal")

    # Falsos positivos do teste 27
    print(f"\n[4] Falsos positivos do teste 27 (Wikipedia):")
    falsos_27 = [
        ('"1" 56', "cavalo"),      # conf=0.97 — espurio
        ("7 e", "gato"),           # conf=0.86 — espurio
        ('" )', "feijao"),         # conf=0.50
        ("c:d pao", "hora"),       # conf=0.91, cross-level
    ]

    print(f"  {'Input':<20s} {'Esperado(falso)':<18s} {'decidir()':<25s} {'decidir_relevante()':<25s}")
    print("  " + "-" * 90)

    for texto, esp_falso in falsos_27:
        a_raw, conf_raw = c_pes.decidir(texto, (None, 0.0))
        a_rel, conf_rel = c_pes.decidir_relevante(texto, (None, 0.0))
        print(f"  {texto:<20s} {esp_falso:<18s} {a_raw[:12]} ({conf_raw:.3f}){'':>5s} "
              f"{a_rel[:12]} ({conf_rel:.3f})")

    # === Regressao: decidir_relevante nao quebra classificacao real? ===
    print(f"\n[5] Regressao: decidir_relevante mantem acertos reais?")
    testes_reais = [
        ("sequencia dois quatro seis oito", "PA"),
        ("padrao tres cinco oito treze", "FIB"),
        ("encadear cinco dezesseis oito quatro", "COLL"),
        ("numeros quatro oito dezesseis", "PG"),
        ("ordem dois tres cinco sete", "PRIMO"),
        ("criar npc ferreiro", "gerar_npc"),
        ("o que e markov", "responder"),
    ]

    print(f"  {'Teste':<40s} {'Esp':<12s} {'decidir()':<20s} {'relevante()':<20s}")
    print("  " + "-" * 95)

    ac_raw = 0
    ac_rel = 0
    for texto, esp in testes_reais:
        a_raw, conf_raw = c_leve.decidir(texto, (None, 0.0))
        a_rel, conf_rel = c_leve.decidir_relevante(texto, (None, 0.0))
        ok_raw = a_raw == esp
        ok_rel = a_rel == esp
        if ok_raw:
            ac_raw += 1
        if ok_rel:
            ac_rel += 1
        st_r = "OK" if ok_raw else "ERR"
        st_l = "OK" if ok_rel else "ERR"
        print(f"  {texto[:38]:<40s} {esp:<12s} {st_r} {a_raw[:10]:<10s} ({conf_raw:.2f})  "
              f"{st_l} {a_rel[:10]:<10s} ({conf_rel:.2f})")

    print(f"\n  decidir():         {ac_raw}/{len(testes_reais)} = {ac_raw/len(testes_reais)*100:.1f}%")
    print(f"  decidir_relevante(): {ac_rel}/{len(testes_reais)} = {ac_rel/len(testes_reais)*100:.1f}%")

    # === Emergir com decidir_relevante ===
    print(f"\n[6] Emergir com decidir_relevante (200 tiros, motor leve)...")
    # Preciso modificar emergir_tudo para usar decidir_relevante
    # Por ora, testar manualmente os top falsos positivos
    print(f"  (verificado acima — falsos positivos rebaixados?)")

    # === Salvar ===
    resultado = {
        "teste": "score_relevancia",
        "falsos_26": [{"input": t, "esperado_falso": e,
                       "decidir": {"acao": c_leve.decidir(t, (None,0.0))[0],
                                   "conf": c_leve.decidir(t, (None,0.0))[1]},
                       "relevante": {"acao": c_leve.decidir_relevante(t, (None,0.0))[0],
                                     "conf": c_leve.decidir_relevante(t, (None,0.0))[1]}}
                      for t, e in falsos_26],
        "falsos_27": [{"input": t, "esperado_falso": e,
                       "decidir": {"acao": c_pes.decidir(t, (None,0.0))[0],
                                   "conf": c_pes.decidir(t, (None,0.0))[1]},
                       "relevante": {"acao": c_pes.decidir_relevante(t, (None,0.0))[0],
                                     "conf": c_pes.decidir_relevante(t, (None,0.0))[1]}}
                      for t, e in falsos_27],
        "regressao": {"decidir": ac_raw, "relevante": ac_rel, "total": len(testes_reais)},
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "28_score_relevancia.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
