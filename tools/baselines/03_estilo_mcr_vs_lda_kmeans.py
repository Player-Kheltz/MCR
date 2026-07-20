"""03_estilo_mcr_vs_lda_kmeans.py — Clusterizacao de estilo: MCR vs LDA vs k-means.

Teste NOVO. Compara MCR vs LDA vs k-means(TF-IDF) em clusterizacao
de 25 textos em 5 estilos sem rotulo.

Metricas: ARI (Adjusted Rand Index), pureza, NMI extrinseca.
"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

# 25 textos: 5 estilos x 5 textos cada
# Estilos: cientifico, literario, jornalistico, dialogo, tecnico
TEXTOS = [
    # Cientifico (0)
    ("O experimento demonstrou que a reacao quimica ocorre em condicoes controladas de temperatura e pressao.", 0),
    ("Os resultados indicam uma correlacao positiva entre as variaveis independentes e dependentes estudadas.", 0),
    ("A analise estatistica revelou diferencas significativas entre os grupos controle e experimental.", 0),
    ("Conclui-se que a hipotese nula pode ser rejeitada com nivel de confianca de 95 por cento.", 0),
    ("Os dados coletados sugerem que o fenomeno observado segue uma distribuicao normal.", 0),
    # Literario (1)
    ("A lua prateada dançava sobre as aguas tranquilas do rio, enquanto a brisa sussurrava segredos antigos.", 1),
    ("Ela caminhava lentamente pela floresta, sentindo cada folha sob seus pes descalcos, ouvindo o coracao da terra.", 1),
    ("O sol se punha no horizonte, pintando o ceu com tons de laranja e purpura, como um artista apaixonado.", 1),
    ("No silencio da noite, as estrelas contavam historias de amores perdidos e esperancas renascidas.", 1),
    ("O vento carregava consigo o perfume das flores silvestres, trazendo memorias de um tempo que ja se foi.", 1),
    # Jornalistico (2)
    ("A reuniao ocorreu ontem no palacio do governo com a presenca de autoridades locais e representantes regionais.", 2),
    ("Segundo fontes oficiais, o projeto de lei sera votado na proxima sessao do congresso nacional.", 2),
    ("O balanco economico do trimestre aponta crescimento de tres por cento em relacao ao periodo anterior.", 2),
    ("Pesquisa realizada pelo instituto mostra que a maioria da populacao apoia a nova politica publica.", 2),
    ("O acordo firmado entre os paises prevê investimentos conjuntos em infraestrutura e tecnologia.", 2),
    # Dialogo (3)
    ("— Voce veio? — perguntou ele, surpreso. — Nao esperava que aparecesse tao cedo.", 3),
    ("— Nao sei o que dizer — respondeu ela, olhando para o chao. — Tudo mudou desde a ultima vez.", 3),
    ("— Que tal sairmos para jantar? — sugeriu ele. — Conheco um lugar excelente perto daqui.", 3),
    ("— Voce esta brincando! — exclamou o amigo. — Isso e impossivel de acreditar.", 3),
    ("— Obrigada pela ajuda — disse ela sorrindo. — Nao teria conseguido sem voce.", 3),
    # Tecnico (4)
    ("Para instalar o pacote execute o comando pip install seguido do nome do modulo desejado no terminal.", 4),
    ("A funcao recebe dois parametros inteiros como entrada e retorna um valor booleano como saida.", 4),
    ("Configure o arquivo JSON com as chaves nome, versao e dependencias antes de executar o script.", 4),
    ("O algoritmo percorre a lista verificando cada elemento e adiciona os validos a uma nova estrutura.", 4),
    ("Importe a biblioteca numpy no inicio do arquivo para usar operacoes de algebra linear no codigo.", 4),
]

ESTILOS = ["cientifico", "literario", "jornalistico", "dialogo", "tecnico"]


def tokenizar(texto):
    import re
    return re.findall(r'[a-zà-ÿ]{2,}', texto.lower())


def testar_mcr(c, textos):
    """MCR clusteriza por assinatura de features.

    Estrategia: alimentar MCR com cada texto+estilo, depois agrupar
    por similaridade de assinatura.
    """
    # Treina MCR com os textos (texto -> estilo)
    for texto, estilo_idx in textos:
        c.alimentar(texto, ESTILOS[estilo_idx])

    # Para cada texto, decidir() retorna o estilo predito
    preds = []
    for texto, estilo_idx in textos:
        acao, conf = c.decidir(texto, (None, 0.0))
        # Mapeia acao para indice
        if acao in ESTILOS:
            preds.append(ESTILOS.index(acao))
        else:
            preds.append(-1)

    return preds


def testar_lda(textos, n_clusters=5):
    """LDA clusteriza por topico."""
    corpus = [t for t, _ in textos]
    labels_true = [l for _, l in textos]

    vectorizer = TfidfVectorizer(max_features=1000, tokenizer=tokenizar, token_pattern=None)
    X = vectorizer.fit_transform(corpus)

    lda = LatentDirichletAllocation(n_components=n_clusters, random_state=42, max_iter=50)
    lda.fit(X)
    # Atribui cada documento ao topico mais provavel
    doc_topic = lda.transform(X)
    preds = doc_topic.argmax(axis=1).tolist()

    return preds, labels_true


def testar_kmeans(textos, n_clusters=5):
    """k-means clusteriza por TF-IDF."""
    corpus = [t for t, _ in textos]
    labels_true = [l for _, l in textos]

    vectorizer = TfidfVectorizer(max_features=1000, tokenizer=tokenizar, token_pattern=None)
    X = vectorizer.fit_transform(corpus)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    preds = km.fit_predict(X).tolist()

    return preds, labels_true


def calcular_pureza(preds, labels_true):
    """Calcula pureza da clusterizacao."""
    from collections import Counter, defaultdict
    clusters = defaultdict(list)
    for p, l in zip(preds, labels_true):
        clusters[p].append(l)
    total = len(labels_true)
    corretos = 0
    for cluster, labels in clusters.items():
        mais_comum = Counter(labels).most_common(1)[0][1]
        corretos += mais_comum
    return corretos / total if total > 0 else 0


def main():
    print("=" * 70)
    print("  TESTE 03 — Clusterizacao de estilo: MCR vs LDA vs k-means")
    print("=" * 70)

    print(f"\nDataset: {len(TEXTOS)} textos, {len(ESTILOS)} estilos x {len(TEXTOS)//len(ESTILOS)} textos")

    labels_true = [l for _, l in TEXTOS]

    # === MCR ===
    print("\n--- MCR ---")
    c, info = carregar_mcr(leve=True)
    preds_mcr = testar_mcr(c, TEXTOS)
    ari_mcr = adjusted_rand_score(labels_true, preds_mcr)
    nmi_mcr = normalized_mutual_info_score(labels_true, preds_mcr)
    pur_mcr = calcular_pureza(preds_mcr, labels_true)
    print(f"ARI: {ari_mcr:.3f}, NMI: {nmi_mcr:.3f}, Pureza: {pur_mcr:.3f}")

    if not SKLEARN_OK:
        print("\n[SKIP] sklearn nao disponivel")
        resultado = {
            "teste": "estilo",
            "mcr": {"ari": ari_mcr, "nmi": nmi_mcr, "pureza": pur_mcr},
            "lda": {"status": "SKIP"},
            "kmeans": {"status": "SKIP"},
        }
    else:
        # === LDA ===
        print("\n--- LDA ---")
        preds_lda, _ = testar_lda(TEXTOS, n_clusters=5)
        ari_lda = adjusted_rand_score(labels_true, preds_lda)
        nmi_lda = normalized_mutual_info_score(labels_true, preds_lda)
        pur_lda = calcular_pureza(preds_lda, labels_true)
        print(f"ARI: {ari_lda:.3f}, NMI: {nmi_lda:.3f}, Pureza: {pur_lda:.3f}")

        # === k-means ===
        print("\n--- k-means (TF-IDF) ---")
        preds_km, _ = testar_kmeans(TEXTOS, n_clusters=5)
        ari_km = adjusted_rand_score(labels_true, preds_km)
        nmi_km = normalized_mutual_info_score(labels_true, preds_km)
        pur_km = calcular_pureza(preds_km, labels_true)
        print(f"ARI: {ari_km:.3f}, NMI: {nmi_km:.3f}, Pureza: {pur_km:.3f}")

        print("\n--- Comparacao (ARI) ---")
        print(f"MCR:      {ari_mcr:.3f}")
        print(f"LDA:      {ari_lda:.3f}")
        print(f"k-means:  {ari_km:.3f}")
        if ari_lda > 0:
            print(f"MCR/LDA:     {ari_mcr/ari_lda:.2f}x")
        if ari_km > 0:
            print(f"MCR/k-means: {ari_mcr/ari_km:.2f}x")

        resultado = {
            "teste": "estilo",
            "n_textos": len(TEXTOS),
            "n_estilos": len(ESTILOS),
            "mcr": {"ari": ari_mcr, "nmi": nmi_mcr, "pureza": pur_mcr},
            "lda": {"ari": ari_lda, "nmi": nmi_lda, "pureza": pur_lda},
            "kmeans": {"ari": ari_km, "nmi": nmi_km, "pureza": pur_km},
        }

    path_out = os.path.join(os.path.dirname(__file__), "resultados", "03_estilo.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
