"""04_intencao_mcr_vs_bert.py — Intencao: MCR vs BERT.

Teste NOVO. Compara MCR vs BERT-base em classificacao de intencao
(pergunta, ordem, afirmacao, exclamacao).

MCR: decidir() com treino nas 120 frases (80 treino, 40 teste).
BERT: embeddings + cosine similarity com prototipos (zero-shot, sem fine-tune).
"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr, mcr_decidir

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

try:
    import torch
    from transformers import BertTokenizer, BertModel
    BERT_OK = True
except ImportError:
    BERT_OK = False

INTENCOES = ["pergunta", "ordem", "afirmacao", "exclamacao"]

# 120 frases: 4 classes x 30
FRASES = [
    # Perguntas (0) - 30
    ("o que e markov", 0), ("como funciona entropia", 0), ("porque usar mcr", 0),
    ("qual a diferenca", 0), ("quando aplicar", 0), ("onde fica", 0),
    ("quem descobriu", 0), ("quantos sao", 0), ("o que significa", 0),
    ("como fazer", 0), ("porque importa", 0), ("qual melhor", 0),
    ("que e cadeia", 0), ("como calcular", 0), ("onde usar", 0),
    ("quando ocorre", 0), ("quem criou", 0), ("qual objetivo", 0),
    ("o que faz", 0), ("como funciona memoria", 0), ("porque falha", 0),
    ("qual resultado", 0), ("que e acoplamento", 0), ("como decidir", 0),
    ("onde procurar", 0), ("quando termina", 0), ("quem sabe", 0),
    ("qual a causa", 0), ("o que prova", 0), ("como aprender", 0),
    # Ordens (1) - 30
    ("crie um npc", 1), ("gerar monstro", 1), ("fazer sprite", 1),
    ("execute comando", 1), ("rode script", 1), ("validar codigo", 1),
    ("buscar arquivo", 1), ("analisar dados", 1), ("conectar modulos", 1),
    ("aprender conceito", 1), ("gerar quest", 1), ("criar dialogo", 1),
    ("gerar npc ferreiro", 1), ("fazer monstro dragao", 1), ("criar sprite espada", 1),
    ("rodar teste", 1), ("validar sintaxe", 1), ("buscar funcao", 1),
    ("analisar performance", 1), ("conectar sistema", 1), ("aprender padrao", 1),
    ("gere codigo", 1), ("crie classe", 1), ("fazer funcao", 1),
    ("execute pipeline", 1), ("rode regressao", 1), ("validar estrutura", 1),
    ("buscar documentacao", 1), ("analisar erro", 1), ("conectar api", 1),
    # Afirmacoes (2) - 30
    ("markov e probabilistico", 2), ("entropia mede incerteza", 2),
    ("mcr funciona sem gpu", 2), ("cadeia tem estados", 2),
    ("acoplamento conecta niveis", 2), ("sistema aprende", 2),
    ("motor classifica", 2), ("codigo roda", 2), ("teste passou", 2),
    ("resultado correto", 2), ("dados validos", 2), ("funcao retorna", 2),
    ("algoritmo converge", 2), ("parametro aceito", 2), ("config carregada", 2),
    ("modulo importado", 2), ("classe instanciada", 2), ("metodo executado", 2),
    ("variavel definida", 2), ("estrutura criada", 2), ("processo terminou", 2),
    ("operacao sucesso", 2), ("conexao estabelecida", 2), ("validacao ok", 2),
    ("treino completo", 2), ("modelo carregado", 2), ("cache atualizado", 2),
    ("estado salvo", 2), ("erro corrigido", 2), ("sistema pronto", 2),
    # Exclamacoes (3) - 30
    ("incrivel resultado", 3), ("fantastico mcr", 3), ("que amazingly", 3),
    ("uau funcionou", 3), ("maravilha isto", 3), ("excelente trabalho", 3),
    ("perfeito agora", 3), ("sensacional descoberta", 3), ("brilhante ideia", 3),
    ("genial solucao", 3), ("otimo progresso", 3), ("espetacular performance", 3),
    ("formidavel sistema", 3), ("impressionante velocidade", 3), ("extraordinario", 3),
    ("muito bom", 3), ("que beleza", 3), ("fantastico mesmo", 3),
    ("incrivel mesmo", 3), ("uau que coisa", 3), ("maravilha pura", 3),
    ("excelente mesmo", 3), ("perfeito tudo", 3), ("sensacional mesmo", 3),
    ("brilhante ideia", 3), ("genial mesmo", 3), ("otimo resultado", 3),
    ("espetacular isso", 3), ("formidavel mesmo", 3), ("impressionante isso", 3),
]


def testar_mcr(treino, teste):
    """MCR treina nas 80 frases e testa nas 40."""
    c, info = carregar_mcr(leve=True)
    for texto, idx in treino:
        c.alimentar(texto, INTENCOES[idx])

    acertos = 0
    detalhes = []
    for texto, esp_idx in teste:
        acao, conf = mcr_decidir(c, texto)
        pred_idx = INTENCOES.index(acao) if acao in INTENCOES else -1
        ac = pred_idx == esp_idx
        if ac:
            acertos += 1
        detalhes.append((texto, INTENCOES[esp_idx], acao, conf, ac))
    return acertos, len(teste), detalhes


def testar_bert_zero_shot(treino, teste):
    """BERT: embeddings + cosine com prototipos de classe (zero-shot)."""
    if not BERT_OK:
        return None, None, None

    print("  Carregando BERT-base...")
    t0 = time.time()
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    model = BertModel.from_pretrained("bert-base-uncased")
    model.eval()
    dt_load = time.time() - t0
    print(f"  BERT carregado em {dt_load:.1f}s")

    def embed(texto):
        inputs = tokenizer(texto, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
        # Mean pooling da ultima hidden state
        return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

    # Constroi prototipos de classe (media dos embeddings de treino)
    protos = {}
    for intencao in INTENCOES:
        embs = [embed(t) for t, i in treino if INTENCOES[i] == intencao]
        if embs:
            protos[intencao] = sum(embs) / len(embs)

    # Testa
    acertos = 0
    detalhes = []
    for texto, esp_idx in teste:
        emb = embed(texto)
        # Cosine similarity com cada prototipo
        best_sim = -1
        best_int = None
        for intencao, proto in protos.items():
            sim = cosine_similarity([emb], [proto])[0][0]
            if sim > best_sim:
                best_sim = sim
                best_int = intencao
        pred_idx = INTENCOES.index(best_int) if best_int else -1
        ac = pred_idx == esp_idx
        if ac:
            acertos += 1
        detalhes.append((texto, INTENCOES[esp_idx], best_int, best_sim, ac))
    return acertos, len(teste), detalhes


def testar_tfidf_cosine(treino, teste):
    """TF-IDF + cosine similarity com prototipos (baseline classico)."""
    if not SKLEARN_OK:
        return None, None, None

    corpus_treino = [t for t, _ in treino]
    corpus_teste = [t for t, _ in teste]

    vec = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    X_treino = vec.fit_transform(corpus_treino)
    X_teste = vec.transform(corpus_teste)

    # Prototipos: media TF-IDF por classe
    import numpy as np
    protos = {}
    for intencao in INTENCOES:
        mask = [i for _, i in treino if INTENCOES[i] == intencao]
        if mask:
            protos[intencao] = np.asarray(X_treino[mask].mean(axis=0))

    labels_treino = [INTENCOES[i] for _, i in treino]
    labels_teste = [INTENCOES[i] for _, i in teste]

    acertos = 0
    detalhes = []
    for j, (texto, esp_idx) in enumerate(teste):
        emb = X_teste[j].toarray()
        best_sim = -1
        best_int = None
        for intencao, proto in protos.items():
            sim = cosine_similarity(emb, proto)[0][0]
            if sim > best_sim:
                best_sim = sim
                best_int = intencao
        pred_idx = INTENCOES.index(best_int) if best_int else -1
        ac = pred_idx == esp_idx
        if ac:
            acertos += 1
        detalhes.append((texto, INTENCOES[esp_idx], best_int, best_sim, ac))
    return acertos, len(teste), detalhes


def main():
    print("=" * 70)
    print("  TESTE 04 — Intencao: MCR vs BERT vs TF-IDF (do zero)")
    print("=" * 70)

    print(f"\nDataset: {len(FRASES)} frases, {len(INTENCOES)} intencoes x {len(FRASES)//len(INTENCOES)} frases")

    # Split 80/20
    random.seed(42)
    random.shuffle(FRASES)
    n_treino = int(len(FRASES) * 0.67)
    treino = FRASES[:n_treino]
    teste = FRASES[n_treino:]
    print(f"Split: {len(treino)} treino, {len(teste)} teste")

    # === MCR ===
    print("\n--- MCR ---")
    ac_mcr, tot_mcr, det_mcr = testar_mcr(treino, teste)
    print(f"MCR: {ac_mcr}/{tot_mcr} = {ac_mcr/tot_mcr*100:.1f}%")

    # === TF-IDF + cosine ===
    print("\n--- TF-IDF + cosine ---")
    if SKLEARN_OK:
        ac_tf, tot_tf, det_tf = testar_tfidf_cosine(treino, teste)
        print(f"TF-IDF: {ac_tf}/{tot_tf} = {ac_tf/tot_tf*100:.1f}%")
    else:
        ac_tf = None
        print("[SKIP] sklearn indisponivel")

    # === BERT zero-shot ===
    print("\n--- BERT-base (zero-shot embeddings) ---")
    if BERT_OK:
        ac_bert, tot_bert, det_bert = testar_bert_zero_shot(treino, teste)
        if ac_bert is not None:
            print(f"BERT: {ac_bert}/{tot_bert} = {ac_bert/tot_bert*100:.1f}%")
        else:
            print("[ERRO] BERT falhou")
    else:
        ac_bert = None
        print("[SKIP] transformers indisponivel")

    # === Comparacao ===
    print("\n--- Comparacao ---")
    tx_mcr = ac_mcr / tot_mcr if tot_mcr else 0
    print(f"MCR:     {tx_mcr*100:.1f}%")
    if ac_tf is not None:
        tx_tf = ac_tf / tot_tf
        print(f"TF-IDF:  {tx_tf*100:.1f}%")
        if tx_tf > 0:
            print(f"MCR/TF-IDF: {tx_mcr/tx_tf:.2f}x")
    if ac_bert is not None:
        tx_bert = ac_bert / tot_bert
        print(f"BERT:    {tx_bert*100:.1f}%")
        if tx_bert > 0:
            print(f"MCR/BERT: {tx_mcr/tx_bert:.2f}x")

    # Exemplos
    print("\n--- Exemplos MCR (10) ---")
    for texto, esp, pred, conf, ac in det_mcr[:10]:
        st = "OK" if ac else "ERR"
        print(f"  {st} '{texto[:30]}' esp={esp} pred={pred} ({conf:.2f})")

    resultado = {
        "teste": "intencao",
        "n_treino": len(treino),
        "n_teste": len(teste),
        "mcr": {"acertos": ac_mcr, "total": tot_mcr, "taxa": tx_mcr},
    }
    if ac_tf is not None:
        resultado["tfidf"] = {"acertos": ac_tf, "total": tot_tf, "taxa": ac_tf/tot_tf}
    if ac_bert is not None:
        resultado["bert"] = {"acertos": ac_bert, "total": tot_bert, "taxa": ac_bert/tot_bert}

    path_out = os.path.join(os.path.dirname(__file__), "resultados", "04_intencao.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
