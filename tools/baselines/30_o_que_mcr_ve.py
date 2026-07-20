"""30_o_que_mcr_ve.py — O que o MCR consegue ver que nao conseguimos?

O Laplace agora distingue automaticamente:
- conf < 0.2: n=1 (falso positivo esmagado)
- conf > 0.4: n grande (descoberta real preservada)

Testar fragmentos aparentemente sem sentido e verificar se as
associacoes do MCR sao suportadas por dados reais (n > 1).

Como Collatz: "2468" em 79 numeros. Como wraith: "wr" em 18 obs.
O que mais?
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

from setup import carregar_mcr


def investigar(c, texto, esperado=None):
    """Investiga uma predicao do MCR e classifica."""
    acao, conf = c.decidir(texto, (None, 0.0))
    
    # Extrair features do texto
    raw = texto.lower()
    feats = set()
    tokens = re.findall(r'[a-zà-ÿ]{2,}|[0-9]+', raw)
    for t in set(tokens):
        feats.add(f"t:{t}")
    chars = re.sub(r'[^a-z0-9]', '', raw)
    for i in range(len(chars) - 1):
        feats.add(f"bg:{chars[i:i+2]}")
    for i in range(len(chars) - 2):
        feats.add(f"ng:{chars[i:i+3]}")
    
    # Encontrar features que sustentam a acao
    features_suporte = []
    for feat in feats:
        dist = c._feature_acao.get(feat, {})
        if dist and acao in dist:
            total = sum(dist.values())
            c_fa = dist[acao]
            n = total
            laplace = c._laplace_smooth(c_fa, total)
            if c_fa > 0:
                # Encontrar palavras que contem esse padrao
                palavras = []
                if feat.startswith("bg:") or feat.startswith("ng:"):
                    padrao = feat.split(":")[1]
                    for p in c._palavra_acao:
                        if padrao in p:
                            palavras.append(p)
                elif feat.startswith("t:"):
                    palavras = [feat.split(":")[1]]
                
                features_suporte.append({
                    "feature": feat,
                    "n_total": total,
                    "n_acao": c_fa,
                    "laplace": round(laplace, 4),
                    "palavras": palavras[:5],
                })
    
    # Classificar
    if conf < 0.2:
        categoria = "FALSO_POSITIVO (n=1 esmagado)"
    elif conf > 0.4:
        categoria = "DESCOBERTA (n grande preservado)"
    else:
        categoria = "AMBIGUO (zona intermediaria)"
    
    return {
        "input": texto,
        "acao_predita": acao,
        "confianca": round(conf, 4),
        "categoria": categoria,
        "esperado": esperado,
        "features_suporte": sorted(features_suporte, key=lambda x: -x["n_acao"])[:5],
    }


def main():
    print("=" * 70)
    print("  TESTE 30 — O que o MCR ve que nao conseguimos?")
    print("=" * 70)

    c, _ = carregar_mcr(leve=True)
    print(f"\n  Motor: {c._total} obs, {len(c._palavra_acao)} pal, {len(c._acao_features)} acoes")

    # === Fragmentos de chars (bigramas isolados) ===
    print("\n[1] Bigramas isolados — o que o MCR ve?")
    bigramas = ["wr", "sp", "np", "mt", "qu", "ge", "mo", "sp", "el", "fo", "ar", "am"]
    descobertas_bigramas = []
    for bg in bigramas:
        r = investigar(c, bg)
        tag = "DESCOBERTA" if r["confianca"] > 0.4 else ("FALSO" if r["confianca"] < 0.2 else "AMBIG")
        print(f"  '{bg}' -> {r['acao_predita']:<15s} conf={r['confianca']:.3f} [{tag}]")
        if r["features_suporte"]:
            fs = r["features_suporte"][0]
            print(f"    via {fs['feature']} (n={fs['n_acao']}/{fs['n_total']}) palavras={fs['palavras'][:3]}")
        if r["confianca"] > 0.4:
            descobertas_bigramas.append(r)

    # === Fragmentos de palavras (metades) ===
    print("\n[2] Fragmentos de palavras — o que o MCR reconhece?")
    fragmentos = ["spr", "monst", "poca", "npc", "que", "cri", "ger", "esp", "scri"]
    for frag in fragmentos:
        r = investigar(c, frag)
        tag = "DESCOBERTA" if r["confianca"] > 0.4 else ("FALSO" if r["confianca"] < 0.2 else "AMBIG")
        print(f"  '{frag}' -> {r['acao_predita']:<15s} conf={r['confianca']:.3f} [{tag}]")
        if r["features_suporte"]:
            fs = r["features_suporte"][0]
            print(f"    via {fs['feature']} (n={fs['n_acao']}/{fs['n_total']}) palavras={fs['palavras'][:3]}")

    # === Numeros isolados ===
    print("\n[3] Numeros isolados — pertencimento a regras matematicas?")
    numeros = ["1", "2", "3", "5", "8", "13", "21", "2468", "16", "64", "128"]
    for n in numeros:
        r = investigar(c, n)
        tag = "DESCOBERTA" if r["confianca"] > 0.4 else ("FALSO" if r["confianca"] < 0.2 else "AMBIG")
        print(f"  '{n}' -> {r['acao_predita']:<15s} conf={r['confianca']:.3f} [{tag}]")
        if r["features_suporte"]:
            fs = r["features_suporte"][0]
            print(f"    via {fs['feature']} (n={fs['n_acao']}/{fs['n_total']})")

    # === Pares de chars aparentemente sem sentido ===
    print("\n[4] Pares de chars — pertencimento parcial como Collatz?")
    pares = ["w r", "s p", "n p", "g m", "f e", "a m", "c r", "q e", "p o", "m t"]
    for par in pares:
        r = investigar(c, par)
        tag = "DESCOBERTA" if r["confianca"] > 0.4 else ("FALSO" if r["confianca"] < 0.2 else "AMBIG")
        print(f"  '{par}' -> {r['acao_predita']:<15s} conf={r['confianca']:.3f} [{tag}]")
        if r["features_suporte"]:
            fs = r["features_suporte"][0]
            print(f"    via {fs['feature']} (n={fs['n_acao']}/{fs['n_total']}) palavras={fs['palavras'][:3]}")

    # === Sequencias matematicas parciais ===
    print("\n[5] Sequencias matematicas parciais — regra correta?")
    seqs = [
        ("dois quatro seis", "PA"),
        ("um dois tres cinco", "FIB"),
        ("cinco dezesseis oito", "COLL"),
        ("um um dois tres cinco oito", "FIB"),
        ("dois quatro oito dezesseis", "PG"),
        ("tres cinco sete onze", "PRIMO"),
        ("um tres seis dez", "TRI"),
        ("um quatro nove dezesseis", "QUAD"),
    ]
    acertos = 0
    for seq, esp in seqs:
        r = investigar(c, seq, esp)
        ok = r["acao_predita"] == esp
        if ok:
            acertos += 1
        tag = "OK" if ok else "ERR"
        print(f"  '{seq[:30]}' -> {r['acao_predita']:<8s} conf={r['confianca']:.3f} [{tag}] (esp={esp})")

    print(f"\n  Acertos: {acertos}/{len(seqs)}")

    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO: O que o MCR ve que nao conseguimos?")
    print("=" * 70)
    print(f"\n  Bigramas com descoberta (conf > 0.4): {len(descobertas_bigramas)}/{len(bigramas)}")
    for d in descobertas_bigramas:
        fs = d["features_suporte"][0] if d["features_suporte"] else None
        if fs:
            print(f"    '{d['input']}' -> {d['acao_predita']} via {fs['palavras'][:3]} (n={fs['n_acao']})")

    # Salvar
    resultado = {
        "teste": "o_que_mcr_ve",
        "bigramas": [investigar(c, bg) for bg in bigramas],
        "fragmentos": [investigar(c, f) for f in fragmentos],
        "numeros": [investigar(c, n) for n in numeros],
        "pares": [investigar(c, p) for p in pares],
        "sequencias": [investigar(c, s, e) for s, e in seqs],
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "30_o_que_mcr_ve.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
