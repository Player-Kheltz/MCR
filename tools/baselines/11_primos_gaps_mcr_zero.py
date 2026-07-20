"""11_primos_gaps_mcr_zero.py — Gaps entre primos do zero.

Teste NOVO. MCR aprende gaps entre numeros primos consecutivos
e tenta prever o proximo gap. Sem formula fechada conhecida.

Original (Fase 7): MCR 44/87 (tolerancia ±2), baseline 0/87, 44x.
"""
import sys, os, json, time, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr


def eh_primo(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def gerar_primos(n_max=500):
    return [n for n in range(2, n_max + 1) if eh_primo(n)]


def calcular_gaps(primos):
    return [primos[i+1] - primos[i] for i in range(len(primos) - 1)]


def gerar_dataset_gaps(primos, gaps, n_contexto=5):
    """Gera dataset: (contexto_gaps, proximo_gap).

    Returns:
        (treino, teste) — listas de (contexto_str, proximo_gap_str)
    """
    random.seed(42)
    pares = []
    for i in range(n_contexto, len(gaps)):
        ctx = gaps[i - n_contexto:i]
        prox = gaps[i]
        # Converte para palavras (numeros como strings)
        ctx_str = " ".join(str(g) for g in ctx)
        prox_str = str(prox)
        # Inclui informacao do primo atual para dar contexto
        primo_atual = primos[i]
        ctx_str = f"primo {primo_atual} gaps {ctx_str}"
        pares.append((ctx_str, prox_str))

    random.shuffle(pares)
    n = len(pares)
    n_treino = int(n * 0.7)
    return pares[:n_treino], pares[n_treino:]


def testar_mcr(c, treino, teste, tolerancia=2):
    """Treina MCR com gaps e testa previsao com tolerancia."""
    for ctx, prox in treino:
        c.alimentar(ctx, prox)

    acertos = 0
    acertos_tol = 0
    detalhes = []
    for ctx, esperado in teste:
        # Predicao via _transicao_palavra
        palavras = ctx.split()
        ultima = palavras[-1] if palavras else ""
        trans = c._transicao_palavra.get(ultima, {})
        if trans:
            pred_str = max(trans.items(), key=lambda x: x[1])[0]
        else:
            dist = c._dist_features(ctx)
            if dist:
                pred_str = max(dist.items(), key=lambda x: x[1])[0]
            else:
                pred_str = "0"

        try:
            pred_val = int(pred_str)
            esp_val = int(esperado)
        except ValueError:
            pred_val = None
            esp_val = None

        ac_exato = pred_str == esperado
        ac_tol = abs((pred_val or 0) - (esp_val or 0)) <= tolerancia if pred_val and esp_val else ac_exato

        if ac_exato:
            acertos += 1
        if ac_tol:
            acertos_tol += 1
        detalhes.append((ctx, esperado, pred_str, ac_exato, ac_tol))

    return acertos, acertos_tol, len(teste), detalhes


def testar_baseline_aleatorio(teste, vocab_gaps):
    """Baseline: gap aleatorio do vocabulario."""
    random.seed(123)
    ac = 0
    ac_tol = 0
    for ctx, esp in teste:
        pred = random.choice(list(vocab_gaps))
        if pred == esp:
            ac += 1
        try:
            if abs(int(pred) - int(esp)) <= 2:
                ac_tol += 1
        except ValueError:
            pass
    return ac, ac_tol, len(teste)


def testar_baseline_moda(teste):
    """Baseline: sempre o gap mais comum."""
    from collections import Counter
    cont = Counter(esp for _, esp in teste)
    moda = cont.most_common(1)[0][0]
    ac = sum(1 for _, esp in teste if moda == esp)
    ac_tol = 0
    for _, esp in teste:
        try:
            if abs(int(moda) - int(esp)) <= 2:
                ac_tol += 1
        except ValueError:
            pass
    return ac, ac_tol, len(teste), moda


def main():
    print("=" * 70)
    print("  TESTE 11 — Gaps entre primos: MCR vs Baselines (do zero)")
    print("=" * 70)

    primos = gerar_primos(n_max=500)
    gaps = calcular_gaps(primos)
    print(f"\nPrimos ate 500: {len(primos)}, gaps: {len(gaps)}")
    print(f"Gaps unicos: {sorted(set(gaps))[:10]}...")

    treino, teste = gerar_dataset_gaps(primos, gaps, n_contexto=5)
    print(f"Dataset: {len(treino)} treino, {len(teste)} teste")

    vocab_gaps = set(esp for _, esp in treino) | set(esp for _, esp in teste)
    print(f"Vocab gaps: {sorted(vocab_gaps, key=lambda x: int(x) if x.isdigit() else 0)}")

    c, info = carregar_mcr(leve=True)

    print("\n--- MCR ---")
    t0 = time.time()
    ac_exato, ac_tol, tot, det = testar_mcr(c, treino, teste, tolerancia=2)
    dt = time.time() - t0
    print(f"Exato:    {ac_exato}/{tot} = {ac_exato/tot*100:.1f}%")
    print(f"Toler±2:  {ac_tol}/{tot} = {ac_tol/tot*100:.1f}%")
    print(f"Tempo: {dt:.2f}s")

    print("\n--- Baseline aleatorio ---")
    ac_r, ac_r_tol, tot_r = testar_baseline_aleatorio(teste, vocab_gaps)
    print(f"Exato:    {ac_r}/{tot_r} = {ac_r/tot_r*100:.1f}%")
    print(f"Toler±2:  {ac_r_tol}/{tot_r} = {ac_r_tol/tot_r*100:.1f}%")

    print("\n--- Baseline moda ---")
    ac_m, ac_m_tol, tot_m, moda = testar_baseline_moda(teste)
    print(f"Exato:    {ac_m}/{tot_m} = {ac_m/tot_m*100:.1f}% (moda={moda})")
    print(f"Toler±2:  {ac_m_tol}/{tot_m} = {ac_m_tol/tot_m*100:.1f}%")

    print("\n--- Comparacao (tolerancia ±2) ---")
    tx_mcr = ac_tol / tot if tot else 0
    tx_rand = ac_r_tol / tot_r if tot_r else 0
    tx_moda = ac_m_tol / tot_m if tot_m else 0
    v_rand = tx_mcr / tx_rand if tx_rand > 0 else float('inf')
    v_moda = tx_mcr / tx_moda if tx_moda > 0 else float('inf')
    print(f"MCR vs aleatorio: {v_rand:.1f}x")
    print(f"MCR vs moda:      {v_moda:.1f}x")

    print("\n--- Exemplos (10) ---")
    for ctx, esp, pred, ae, at in det[:10]:
        st = "OK" if at else "ERR"
        print(f"  {st} esp={esp} pred={pred} | {ctx[:40]}")

    resultado = {
        "teste": "primos_gaps",
        "n_primos": len(primos),
        "n_treino": len(treino),
        "n_teste": len(teste),
        "mcr": {"exato": ac_exato, "tol2": ac_tol, "total": tot, "tempo": dt},
        "baseline_aleatorio": {"exato": ac_r, "tol2": ac_r_tol, "total": tot_r},
        "baseline_moda": {"exato": ac_m, "tol2": ac_m_tol, "total": tot_m, "moda": moda},
        "vantagem_tol2_mcr_vs_aleatorio": v_rand,
        "vantagem_tol2_mcr_vs_moda": v_moda,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "11_primos_gaps.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
