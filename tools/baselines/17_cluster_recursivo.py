"""17_cluster_recursivo.py — Testar clusterizacao recursiva.

Validar:
1. A arvore emerge com multiplos niveis
2. Cada cluster isola dominios (tokens nao transbordam)
3. O numero 3 emerge naturalmente (filhos por no)?
4. Decidir isolado vs decidir global (com/sem Gutenberg)
5. Regressoes intactas
"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.cluster_recursivo import ClusterRecursivo, NoCluster
from setup import carregar_mcr, mcr_decidir

# Corpus Gutenberg para teste de isolamento
DIR_GUTENBERG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "cache", "corpus_expa", "gutenberg")


def tokenizar(texto):
    return re.findall(r'[a-zà-ÿ]{2,}', texto.lower())


def frases_gutenberg(n_max=5000):
    """Carrega algumas frases Gutenberg para teste de isolamento."""
    frases = []
    for arq in sorted(os.listdir(DIR_GUTENBERG))[:10]:
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
    print("  TESTE 17 — Cluster Recursivo: cluster de cluster de clusters")
    print("=" * 70)

    # Carrega MCR (leve para velocidade — sem Wikipedia 94K pal)
    print("\n[1] Carregando MCR com corpus leve...")
    c, info = carregar_mcr(leve=True)  # leve: matematico + dataset_500
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # Adiciona Gutenberg
    print("\n[2] Adicionando Gutenberg (3000 frases)...")
    frases = frases_gutenberg(3000)
    for fr in frases:
        c.alimentar(fr, "gutenberg")
    print(f"  +{len(frases)} frases Gutenberg. Total: {c._total} obs, {len(c._freq_acao)} acoes")

    # === Cluster recursivo ===
    print("\n[3] Clusterizando recursivamente...")
    cr = ClusterRecursivo(c, min_delta_h=0.02, max_niveis=7, min_acoes=2)
    t0 = time.time()
    arvore = cr.clusterizar_recursivo()
    dt = time.time() - t0
    print(f"  Tempo: {dt:.2f}s")

    # === Imprimir arvore ===
    print("\n[4] Arvore de clusters:")
    def imprimir(no, prefix=""):
        print(f"  {prefix}{no}")
        for f in no.filhos:
            imprimir(f, prefix + "  ")
    imprimir(arvore)

    # === Estatisticas ===
    print("\n[5] Estatisticas:")
    stats = cr.estatisticas()
    print(f"  Folhas: {stats['n_folhas']}")
    print(f"  Nos: {stats['n_nos']}")
    print(f"  Max niveis: {stats['max_niveis']}")
    print(f"  Filhos por no: {stats['filhos_por_no']}")
    print(f"  Media filhos: {stats['media_filhos']:.2f}")
    print(f"  Lista filhos: {stats['filhos_por_no_lista']}")

    # === O numero 3 emerge? ===
    print("\n[6] O numero 3 emerge?")
    dist = stats['filhos_por_no']
    if 3 in dist:
        print(f"  SIM — 3 filhos aparece {dist[3]} vez(es)")
    else:
        print(f"  NAO — distribuicao: {dist}")
    # Verificar se 3 e a moda
    if dist:
        moda = max(dist.items(), key=lambda x: x[1])
        print(f"  Moda: {moda[0]} filhos ({moda[1]} nos)")

    # === Teste de isolamento ===
    print("\n[7] Teste de isolamento (Gutenberg vs matematica)...")
    testes_isolamento = [
        ("sequencia dois quatro seis oito", "PA"),
        ("padrao tres cinco oito treze", "FIB"),
        ("criar npc ferreiro", "gerar_npc"),
        ("o que e markov", "responder"),
        ("ele disse que nao voltaria", "gutenberg"),  # frase literaria
        ("a lua prateada dancava sobre as aguas", "gutenberg"),
    ]

    print(f"  {'Teste':<40s} {'Esperado':<12s} {'Global':<15s} {'Isolado':<15s} {'No':<15s}")
    print("  " + "-" * 100)

    for texto, esp in testes_isolamento:
        # Decidir global (sem isolamento)
        acao_g, conf_g = mcr_decidir(c, texto)

        # Decidir isolado (roteado para no folha)
        try:
            no, (acao_i, conf_i) = cr.rotear(texto)
            no_nome = no.nome
        except Exception as e:
            acao_i, conf_i, no_nome = "ERR", 0.0, str(e)[:10]

        st_g = "OK" if acao_g == esp else "ERR"
        st_i = "OK" if acao_i == esp else "ERR"
        print(f"  {texto[:38]:<40s} {esp:<12s} {st_g} {acao_g[:10]:<10s} {st_i} {acao_i[:10]:<10s} {no_nome[:13]:<15s}")

    # === Arvore serializada ===
    print("\n[8] Arvore serializada (JSON):")
    arvore_dict = arvore.to_dict()
    print(json.dumps(arvore_dict, indent=2, ensure_ascii=False)[:2000])

    # === Salvar resultado ===
    resultado = {
        "teste": "cluster_recursivo",
        "mcr": {"obs": c._total, "vocab": len(c._palavra_acao), "acoes": len(c._freq_acao)},
        "gutenberg_frases": len(frases),
        "tempo_clusterizacao": dt,
        "estatisticas": stats,
        "arvore": arvore_dict,
        "numero_3_emerge": 3 in dist,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "17_cluster_recursivo.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
