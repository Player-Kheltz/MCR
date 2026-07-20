"""10_collatz_mcr_zero.py — Collatz prediction do zero.

Teste NOVO do zero. MCR aprende sequencias Collatz (3n+1) e tenta
prever o proximo termo. Compara contra baseline aleatorio.

Collatz: se par, n/2. Se impar, 3n+1. Toda sequencia termina em 1
(conjectura nao provada desde 1937).
"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr

NUM50 = [
    "zero","um","dois","tres","quatro","cinco","seis","sete","oito","nove",
    "dez","onze","doze","treze","quatorze","quize","dezesseis","dezessete",
    "dezoito","dezenove",
    "vinte","vinteeum","vinteedois","vinteetres","vinteequatro","vinteecinco",
    "vinteeseis","vintesete","vinteeoito","vinteenove",
    "trinta","trintaeum","trintaedois","trintaetres","trintaequatro",
    "trintaecinco","trintaeseis","trintasete","trintaeoito","trintaenove",
    "quarenta","quarentaeum","quarentaedois","quarentaetres","quarentaequatro",
    "quarentaecinco","quarentaeseis","quarentasete","quarentaeoito",
    "quarentaenove","cinquenta",
]

NUM2VAL = {w: i for i, w in enumerate(NUM50)}
VAL2NUM = {i: w for i, w in enumerate(NUM50)}


def collatz_seq(n, max_steps=30):
    """Gera sequencia Collatz a partir de n. Retorna lista de valores."""
    seq = []
    while n > 1 and len(seq) < max_steps:
        seq.append(n)
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
    if n == 1:
        seq.append(1)
    return seq


def val2word(v):
    """Converte valor numerico para palavra (se possivel)."""
    if v in VAL2NUM:
        return VAL2NUM[v]
    # Para valores > 50, usa string do numero
    return str(v)


def word2val(w):
    """Converte palavra para valor numerico."""
    if w in NUM2VAL:
        return NUM2VAL[w]
    try:
        return int(w)
    except ValueError:
        return None


def gerar_dataset_collatz(n_seeds=40, max_val=50):
    """Gera dataset de sequencias Collatz.

    Returns:
        (treino, teste) — listas de (sequencia_palavras, proximo_termo_palavra)
    """
    random.seed(42)
    seqs = []
    for seed in range(2, max_val + 1):
        seq = collatz_seq(seed, max_steps=20)
        if len(seq) >= 4:
            seqs.append(seq)

    random.shuffle(seqs)
    n = len(seqs)
    n_treino = int(n * 0.7)

    treino = []
    teste = []

    for i, seq in enumerate(seqs):
        # Para cada par (contexto, proximo) na sequencia
        for j in range(len(seq) - 1):
            ctx = seq[:j + 1]
            prox = seq[j + 1]
            # Converte para palavras
            ctx_words = [val2word(v) for v in ctx]
            prox_word = val2word(prox)
            par = (" ".join(ctx_words[-5:]), prox_word)  # ultimas 5 palavras
            if i < n_treino:
                treino.append(par)
            else:
                teste.append(par)

    return treino, teste


def testar_mcr(c, treino, teste):
    """Treina MCR com sequencias Collatz e testa previsao."""
    # Alimenta MCR com transicoes
    for ctx, prox in treino:
        palavras = ctx.split()
        # Alimenta como transicao: ctx -> prox
        # Usar alimentar com acao=prox para criar associacao
        c.alimentar(ctx, prox)

    # Testa: para cada (ctx, prox_esperado), MCR prediz proximo
    acertos = 0
    detalhes = []
    for ctx, esperado in teste:
        # Usa _transicao_palavra para prever
        palavras = ctx.split()
        if not palavras:
            continue
        ultima = palavras[-1]
        trans = c._transicao_palavra.get(ultima, {})
        if not trans:
            # Fallback: usar _dist_features
            dist = c._dist_features(ctx)
            if dist:
                pred = max(dist.items(), key=lambda x: x[1])[0]
            else:
                pred = None
        else:
            pred = max(trans.items(), key=lambda x: x[1])[0]

        ac = pred == esperado
        if ac:
            acertos += 1
        detalhes.append((ctx, esperado, pred, ac))

    return acertos, len(teste), detalhes


def testar_baseline_aleatorio(teste, vocab_prox):
    """Baseline: escolhe proximo termo aleatoriamente do vocabulario."""
    random.seed(123)
    acertos = 0
    for ctx, esperado in teste:
        pred = random.choice(list(vocab_prox))
        if pred == esperado:
            acertos += 1
    return acertos, len(teste)


def testar_baseline_moda(teste):
    """Baseline: sempre escolhe o termo mais frequente (moda)."""
    from collections import Counter
    contagem = Counter(prox for _, prox in teste)
    moda = contagem.most_common(1)[0][0]
    acertos = sum(1 for _, esp in teste if moda == esp)
    return acertos, len(teste), moda


def main():
    print("=" * 70)
    print("  TESTE 10 — Collatz: MCR vs Baselines (do zero)")
    print("=" * 70)

    # Gera dataset
    treino, teste = gerar_dataset_collatz(n_seeds=50, max_val=50)
    print(f"\nDataset: {len(treino)} treino, {len(teste)} teste")

    # Vocabulario de proximos termos (para baseline aleatorio)
    vocab_prox = set(prox for _, prox in treino) | set(prox for _, prox in teste)
    print(f"Vocabulario de termos: {len(vocab_prox)}")

    # Carrega MCR leve
    c, info = carregar_mcr(leve=True)

    # Testa MCR
    print("\n--- MCR ---")
    t0 = time.time()
    ac_mcr, tot_mcr, det_mcr = testar_mcr(c, treino, teste)
    dt_mcr = time.time() - t0
    print(f"Acertos: {ac_mcr}/{tot_mcr} = {ac_mcr/tot_mcr*100:.1f}%")
    print(f"Tempo: {dt_mcr:.2f}s")

    # Testa baseline aleatorio
    print("\n--- Baseline aleatorio ---")
    ac_rand, tot_rand = testar_baseline_aleatorio(teste, vocab_prox)
    print(f"Acertos: {ac_rand}/{tot_rand} = {ac_rand/tot_rand*100:.1f}%")

    # Testa baseline moda
    print("\n--- Baseline moda ---")
    ac_moda, tot_moda, moda = testar_baseline_moda(teste)
    print(f"Acertos: {ac_moda}/{tot_moda} = {ac_moda/tot_moda*100:.1f}% (moda='{moda}')")

    # Comparacao
    print("\n--- Comparacao ---")
    taxa_mcr = ac_mcr / tot_mcr if tot_mcr else 0
    taxa_rand = ac_rand / tot_rand if tot_rand else 0
    taxa_moda = ac_moda / tot_moda if tot_moda else 0
    vantagem_rand = taxa_mcr / taxa_rand if taxa_rand > 0 else float('inf')
    vantagem_moda = taxa_mcr / taxa_moda if taxa_moda > 0 else float('inf')
    print(f"MCR vs aleatorio: {vantagem_rand:.1f}x")
    print(f"MCR vs moda:      {vantagem_moda:.1f}x")

    # Mostra alguns exemplos
    print("\n--- Exemplos (10 primeiros) ---")
    for ctx, esp, pred, ac in det_mcr[:10]:
        status = "OK" if ac else "ERR"
        print(f"  {status} ctx='{ctx[:30]}' esp={esp} pred={pred}")

    # Salva resultado
    resultado = {
        "teste": "collatz",
        "n_treino": len(treino),
        "n_teste": len(teste),
        "mcr": {"acertos": ac_mcr, "total": tot_mcr, "taxa": taxa_mcr, "tempo": dt_mcr},
        "baseline_aleatorio": {"acertos": ac_rand, "total": tot_rand, "taxa": taxa_rand},
        "baseline_moda": {"acertos": ac_moda, "total": tot_moda, "taxa": taxa_moda, "moda": moda},
        "vantagem_mcr_vs_aleatorio": vantagem_rand,
        "vantagem_mcr_vs_moda": vantagem_moda,
    }
    os.makedirs(os.path.join(os.path.dirname(__file__), "resultados"), exist_ok=True)
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "10_collatz.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
