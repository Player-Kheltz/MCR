"""01_sinonimia_mcr_vs_w2v.py — Sinonímia cross-idioma: MCR vs CBOW do zero.

Teste NOVO. Compara MCR (_nmi_semantico) vs CBOW implementado do zero
em numpy, treinado no MESMO corpus Wikipedia multi-idioma.

Sem gensim disponivel — implementacao propria de CBOW para comparacao justa
(mesmo corpus, mesmo algoritmo, sem modelos pre-treinados externos).
"""
import sys, os, json, time, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from setup import carregar_mcr, mcr_nmi

# Pares de sinonimia cross-idioma (rotulados manualmente)
# 20 sinonimos (positivos) + 20 nao-relacionados (negativos)
PARES_SINONIMOS = [
    ("amor", "love", 1), ("casa", "house", 1), ("agua", "water", 1),
    ("luz", "light", 1), ("fogo", "fire", 1), ("cachorro", "dog", 1),
    ("gato", "cat", 1), ("sol", "sun", 1), ("lua", "moon", 1),
    ("estrela", "star", 1), ("livro", "book", 1), ("pao", "bread", 1),
    ("cadeira", "chair", 1), ("mesa", "table", 1), ("porta", "door", 1),
    ("janela", "window", 1), ("arvore", "tree", 1), ("flor", "flower", 1),
    ("rio", "river", 1), ("montanha", "mountain", 1),
]

PARES_NAO_REL = [
    ("cachorro", "mesa", 0), ("fogo", "numero", 0), ("peixe", "musica", 0),
    ("amor", "calculo", 0), ("casa", "raiz", 0), ("agua", "ponte", 0),
    ("luz", "tempestade", 0), ("gato", "algoritmo", 0), ("sol", "intervalo", 0),
    ("lua", "metal", 0), ("estrela", "lagar", 0), ("livro", "serpente", 0),
    ("pao", "tese", 0), ("cadeira", "nuvem", 0), ("mesa", "sopro", 0),
    ("porta", "silogismo", 0), ("janela", "esfera", 0),
    ("arvore", "codigo", 0), ("flor", "ponto", 0), ("rio", "rotulo", 0),
]

TODOS_PARES = PARES_SINONIMOS + PARES_NAO_REL


def tokenizar(texto):
    """Tokeniza texto em palavras lowercase."""
    import re
    return re.findall(r'[a-zà-ÿ]{2,}', texto.lower())


def carregar_corpus_wiki(dir_wiki, max_arquivos=100):
    """Carrega corpus Wikipedia do cache."""
    arquivos = sorted(os.listdir(dir_wiki))[:max_arquivos]
    corpus = []
    for arq in arquivos:
        path = os.path.join(dir_wiki, arq)
        with open(path, "r", encoding="utf-8") as f:
            texto = f.read()
        corpus.append(texto)
    return corpus


class CBOWSimples:
    """CBOW com Negative Sampling implementado do zero em numpy.

    Mais rapido que softmax completo: O(K) por par em vez de O(V).
    """

    def __init__(self, dim=100, janela=5, min_freq=3, lr=0.01, epochs=3, k_neg=5):
        self.dim = dim
        self.janela = janela
        self.min_freq = min_freq
        self.lr = lr
        self.epochs = epochs
        self.k_neg = k_neg
        self.vocab = {}
        self.idx2word = []
        self.freqs = []
        self.W_in = None
        self.W_out = None
        self._neg_table = None

    def _construir_vocab(self, corpus_tokens):
        from collections import Counter
        cont = Counter()
        for tokens in corpus_tokens:
            cont.update(tokens)
        self.vocab = {}
        self.idx2word = []
        self.freqs = []
        for w, c in cont.items():
            if c >= self.min_freq:
                self.vocab[w] = len(self.idx2word)
                self.idx2word.append(w)
                self.freqs.append(c)

    def _construir_neg_table(self):
        """Tabela de amostragem negativa proporcional a freq^0.75."""
        freqs = np.array(self.freqs, dtype=np.float64) ** 0.75
        probs = freqs / freqs.sum()
        table_size = 100000
        self._neg_table = np.zeros(table_size, dtype=np.int32)
        cum = 0.0
        idx = 0
        for i, p in enumerate(probs):
            cum_end = cum + p
            while idx < table_size and idx / table_size < cum_end:
                self._neg_table[idx] = i
                idx += 1
            cum = cum_end

    def treinar(self, corpus_tokens):
        self._construir_vocab(corpus_tokens)
        V = len(self.idx2word)
        D = self.dim
        if V == 0:
            return

        self._construir_neg_table()

        # Inicializa matrizes
        rng = np.random.default_rng(42)
        self.W_in = (rng.standard_normal((V, D)) * 0.01).astype(np.float32)
        self.W_out = (rng.standard_normal((V, D)) * 0.01).astype(np.float32)

        # Gera pares (contexto, central)
        pares = []
        for tokens in corpus_tokens:
            ids = [self.vocab[t] for t in tokens if t in self.vocab]
            for i in range(self.janela, len(ids) - self.janela):
                ctx = ids[i - self.janela:i] + ids[i + 1:i + self.janela + 1]
                central = ids[i]
                pares.append((ctx, central))

        print(f"  CBOW: {V} palavras, {len(pares)} pares, neg sampling k={self.k_neg}")

        # Gradient descent com negative sampling
        for ep in range(self.epochs):
            total_loss = 0
            rng.shuffle(pares)
            for ctx, central in pares:
                # Contexto: media dos embeddings
                h = self.W_in[ctx].mean(axis=0)  # (D,)
                # Amostras negativas
                negs = self._neg_table[rng.integers(0, len(self._neg_table), self.k_neg)]
                # Positivo
                v_pos = self.W_out[central]  # (D,)
                score_pos = 1.0 / (1.0 + np.exp(-np.clip(np.dot(h, v_pos), -30, 30)))
                total_loss -= np.log(score_pos + 1e-10)
                # Gradiente positivo
                grad_pos = (score_pos - 1.0)
                # Negativos
                grad_negs = np.zeros(self.k_neg)
                for j, neg in enumerate(negs):
                    if neg == central:
                        continue
                    v_neg = self.W_out[neg]
                    score_neg = 1.0 / (1.0 + np.exp(np.clip(np.dot(h, v_neg), -30, 30)))
                    total_loss -= np.log(1 - score_neg + 1e-10)
                    grad_negs[j] = score_neg
                # Update W_out
                self.W_out[central] -= self.lr * np.clip(grad_pos * h, -1, 1)
                for j, neg in enumerate(negs):
                    if neg != central:
                        self.W_out[neg] -= self.lr * np.clip(grad_negs[j] * h, -1, 1)
                # Update W_in (gradiente volta para todas as palavras de contexto)
                dh = grad_pos * v_pos
                for j, neg in enumerate(negs):
                    if neg != central:
                        dh += grad_negs[j] * self.W_out[neg]
                dh = np.clip(dh, -1, 1)
                for idx in ctx:
                    self.W_in[idx] -= self.lr * dh / len(ctx)
            print(f"  Epoch {ep+1}/{self.epochs}: loss={total_loss/len(pares):.4f}")

    def similaridade(self, word_a, word_b):
        """Cosine similarity entre duas palavras."""
        if word_a not in self.vocab or word_b not in self.vocab:
            return 0.0
        va = self.W_in[self.vocab[word_a]]
        vb = self.W_in[self.vocab[word_b]]
        norm = np.linalg.norm(va) * np.linalg.norm(vb)
        if norm == 0:
            return 0.0
        return float(np.dot(va, vb) / norm)


def calcular_roc_auc(scores, labels):
    """Calcula ROC AUC simples."""
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    # Pares ordenados por score
    ordenado = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    fp = 0
    auc = 0.0
    for s, l in ordenado:
        if l == 1:
            tp += 1
        else:
            fp += 1
            auc += tp  # cada FP contribui com TP acima dele
    auc = auc / (n_pos * n_neg)
    return auc


def calcular_f1(scores, labels, threshold):
    """Calcula F1 para um threshold."""
    tp = sum(1 for s, l in zip(scores, labels) if s >= threshold and l == 1)
    fp = sum(1 for s, l in zip(scores, labels) if s >= threshold and l == 0)
    fn = sum(1 for s, l in zip(scores, labels) if s < threshold and l == 1)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return f1, prec, rec


def main():
    print("=" * 70)
    print("  TESTE 01 — Sinonímia cross-idioma: MCR vs CBOW (do zero)")
    print("=" * 70)

    print(f"\nDataset: {len(PARES_SINONIMOS)} sinonimos + {len(PARES_NAO_REL)} nao-rel = {len(TODOS_PARES)} pares")

    # Carrega corpus Wikipedia
    dir_wiki = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "wiki")
    print(f"\nCarregando corpus Wikipedia de {dir_wiki}...")
    corpus = carregar_corpus_wiki(dir_wiki, max_arquivos=50)
    corpus_tokens = [tokenizar(texto) for texto in corpus]
    n_tokens = sum(len(t) for t in corpus_tokens)
    print(f"Corpus: {len(corpus)} arquivos, {n_tokens} tokens")

    # === MCR ===
    print("\n--- MCR (com Wikipedia) ---")
    c, info = carregar_mcr(leve=False)
    scores_mcr = []
    for a, b, label in TODOS_PARES:
        s = mcr_nmi(c, a, b)
        scores_mcr.append(s)
        st = "SIN" if label else "NREL"
        print(f"  {st} {a}~{b} = {s:.3f}")

    # === CBOW ===
    print("\n--- CBOW (do zero, mesmo corpus) ---")
    cbow = CBOWSimples(dim=100, janela=5, min_freq=3, lr=0.025, epochs=2)
    t0 = time.time()
    cbow.treinar(corpus_tokens)
    dt_cbow = time.time() - t0
    print(f"  Treino: {dt_cbow:.1f}s")

    scores_cbow = []
    for a, b, label in TODOS_PARES:
        s = cbow.similaridade(a, b)
        scores_cbow.append(s)
        st = "SIN" if label else "NREL"
        print(f"  {st} {a}~{b} = {s:.3f}")

    # === Metricas ===
    labels = [l for _, _, l in TODOS_PARES]

    auc_mcr = calcular_roc_auc(scores_mcr, labels)
    auc_cbow = calcular_roc_auc(scores_cbow, labels)

    # F1 com threshold otimo (maximiza F1)
    best_f1_mcr = 0
    best_th_mcr = 0
    for th in [s for s in sorted(scores_mcr)]:
        f1, _, _ = calcular_f1(scores_mcr, labels, th)
        if f1 > best_f1_mcr:
            best_f1_mcr = f1
            best_th_mcr = th

    best_f1_cbow = 0
    best_th_cbow = 0
    for th in [s for s in sorted(scores_cbow)]:
        f1, _, _ = calcular_f1(scores_cbow, labels, th)
        if f1 > best_f1_cbow:
            best_f1_cbow = f1
            best_th_cbow = th

    print("\n--- Resultados ---")
    print(f"MCR:  ROC AUC = {auc_mcr:.3f}, F1 = {best_f1_mcr:.3f} (th={best_th_mcr:.3f})")
    print(f"CBOW: ROC AUC = {auc_cbow:.3f}, F1 = {best_f1_cbow:.3f} (th={best_th_cbow:.3f})")

    print("\n--- Comparacao ---")
    if auc_cbow > 0:
        ratio_auc = auc_mcr / auc_cbow
    else:
        ratio_auc = float('inf')
    print(f"MCR/CBOW AUC: {ratio_auc:.2f}x")

    resultado = {
        "teste": "sinonimia_cross_idioma",
        "n_pares": len(TODOS_PARES),
        "n_sinonimos": len(PARES_SINONIMOS),
        "n_nao_rel": len(PARES_NAO_REL),
        "corpus_tokens": n_tokens,
        "mcr": {"roc_auc": auc_mcr, "f1": best_f1_mcr, "threshold": best_th_mcr,
                "scores": scores_mcr},
        "cbow": {"roc_auc": auc_cbow, "f1": best_f1_cbow, "threshold": best_th_cbow,
                 "scores": scores_cbow, "dim": 100, "janela": 5, "epochs": 3,
                 "tempo_treino": dt_cbow},
        "vantagem_mcr_cbow_auc": ratio_auc,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "01_sinonimia.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
