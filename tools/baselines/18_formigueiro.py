"""18_formigueiro.py — Testar pertencimento multiplo (formigueiro).

Validar:
1. Acoes pertencem a MULTIPLOS clusters (nao exclusivo)
2. Fragmentos tocam clusters sem ser completos (Collatz parcial)
3. Decisao combinada > decisao isolada
4. O numero 3 emerge?
"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.formigueiro import Formigueiro
from setup import carregar_mcr, mcr_decidir

DIR_GUTENBERG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "cache", "corpus_expa", "gutenberg")


def tokenizar(texto):
    return re.findall(r'[a-zà-ÿ]{2,}', texto.lower())


def frases_gutenberg(n_max=3000):
    frases = []
    for arq in sorted(os.listdir(DIR_GUTENBERG))[:8]:
        if not arq.endswith(".txt"):
            continue
        path = os.path.join(DIR_GUTENBERG, arq)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            texto = f.read()
        partes = texto.split("***")
        if len(partes) >= 3:
            texto = partes[1]
        raw = re.split(r'[.!?]+\s+|\n+', texto)
        for fr in raw:
            palavras = tokenizar(fr)
            if len(palavras) >= 4:
                frases.append(" ".join(palavras[:60]))
            if len(frases) >= n_max:
                return frases
    return frases


def main():
    print("=" * 70)
    print("  TESTE 18 — Formigueiro: pertencimento multiplo e sobreposto")
    print("=" * 70)

    # Carrega MCR
    print("\n[1] Carregando MCR com corpus...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # Adiciona Gutenberg
    print("\n[2] Adicionando Gutenberg (3000 frases)...")
    frases = frases_gutenberg(3000)
    for fr in frases:
        c.alimentar(fr, "gutenberg")
    print(f"  +{len(frases)} frases. Total: {c._total} obs, {len(c._freq_acao)} acoes")

    # === Construir formigueiro ===
    print("\n[3] Construindo formigueiro...")
    f = Formigueiro(c)
    t0 = time.time()
    resultado_constr = f.construir()
    dt = time.time() - t0
    print(f"  Tempo: {dt:.2f}s")
    print(f"  Clusters: {resultado_constr['n_clusters']}")
    print(f"  Threshold: {resultado_constr['threshold']}")
    print(f"  Pertencimento medio: {resultado_constr['pertencimento_medio']}")

    # === Estatisticas ===
    print("\n[4] Estatisticas do formigueiro:")
    stats = f.estatisticas()
    print(f"  N clusters: {stats['n_clusters']}")
    print(f"  N acoes: {stats['n_acoes']}")
    print(f"  Pertencimento medio: {stats['pertencimento_medio']}")
    print(f"  Distribuicao pertencimento: {stats['distribuicao_pertencimento']}")
    print(f"  Acoes por cluster:")
    for nome, n in stats['acoes_por_cluster'].items():
        print(f"    {nome}: {n} acoes -> {sorted(f._clusters[nome])}")

    print(f"\n  Clusters por acao:")
    for acao, n in sorted(stats['clusters_por_acao'].items()):
        clusters_dessa = [nome for nome, acoes in f._clusters.items() if acao in acoes]
        print(f"    {acao}: {n} clusters -> {clusters_dessa}")

    # === O numero 3 emerge? ===
    print("\n[5] O numero 3 emerge?")
    dist = stats['distribuicao_pertencimento']
    print(f"  Distribuicao: {dist}")
    if 3 in dist:
        print(f"  SIM — 3 clusters por acao aparece {dist[3]} vez(es)")
    # Moda
    if dist:
        moda = max(dist.items(), key=lambda x: x[1])
        print(f"  Moda: {moda[0]} clusters/acao ({moda[1]} acoes)")

    # === Teste de decisao: global vs formigueiro vs modular ===
    print("\n[6] Teste de decisao: global vs formigueiro vs modular...")
    testes = [
        ("sequencia dois quatro seis oito", "PA"),
        ("padrao tres cinco oito treze", "FIB"),
        ("encadear cinco dezesseis oito quatro", "COLL"),
        ("numeros quatro oito dezesseis", "PG"),
        ("ordem dois tres cinco sete", "PRIMO"),
        ("criar npc ferreiro", "gerar_npc"),
        ("o que e markov", "responder"),
        ("ele disse que nao voltaria", "gutenberg"),
        ("a lua prateada dancava", "gutenberg"),
        # Fragmentos parciais (Collatz parcial)
        ("dezesseis oito quatro dois", "COLL"),  # fragmento de Collatz
        ("oito quatro dois um", "COLL"),  # fragmento final de Collatz
        ("um dois tres", "PA"),  # fragmento PA
        ("um um dois tres", "FIB"),  # fragmento Fibonacci
    ]

    print(f"  {'Teste':<40s} {'Esp':<12s} {'Global':<15s} {'Sub-MCR':<15s} {'Modular':<15s}")
    print("  " + "-" * 110)

    ac_global = 0
    ac_formiga = 0
    ac_modular = 0

    for texto, esp in testes:
        # Global
        acao_g, conf_g = mcr_decidir(c, texto)

        # Formigueiro (sub-MCRs)
        r_sub = f.decidir(texto)
        acao_sub = r_sub['acao']

        # Formigueiro modular (MCR global modulado)
        r_mod = f.decidir_modular(texto)
        acao_mod = r_mod['acao']

        st_g = "OK" if acao_g == esp else "ERR"
        st_s = "OK" if acao_sub == esp else "ERR"
        st_m = "OK" if acao_mod == esp else "ERR"
        if acao_g == esp:
            ac_global += 1
        if acao_sub == esp:
            ac_formiga += 1
        if acao_mod == esp:
            ac_modular += 1

        print(f"  {texto[:38]:<40s} {esp:<12s} {st_g} {acao_g[:10]:<10s} {st_s} {acao_sub[:10]:<10s} {st_m} {acao_mod[:10]:<10s}")

    print(f"\n  Global:     {ac_global}/{len(testes)} = {ac_global/len(testes)*100:.1f}%")
    print(f"  Sub-MCR:    {ac_formiga}/{len(testes)} = {ac_formiga/len(testes)*100:.1f}%")
    print(f"  Modular:    {ac_modular}/{len(testes)} = {ac_modular/len(testes)*100:.1f}%")

    # === Salvar ===
    resultado = {
        "teste": "formigueiro",
        "mcr": {"obs": c._total, "vocab": len(c._palavra_acao), "acoes": len(c._freq_acao)},
        "estatisticas": stats,
        "n_clusters": resultado_constr['n_clusters'],
        "threshold": resultado_constr['threshold'],
        "pertencimento_medio": resultado_constr['pertencimento_medio'],
        "distribuicao_pertencimento": dist,
        "numero_3_emerge": 3 in dist,
        "acuracia_global": ac_global / len(testes),
        "acuracia_formigueiro": ac_formiga / len(testes),
        "acuracia_modular": ac_modular / len(testes),
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "18_formigueiro.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
