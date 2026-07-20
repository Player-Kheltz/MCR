"""16_sonho_markoviano.py — Testar o sonho markoviano do MCR.

O MCR "sonha": le seu proprio estado interno, gera markovianamente
a partir dele (sem random), e alimenta o resultado de volta.

Validar:
1. O sonho gera sequencias ineditas (novidade > 0)
2. O sonho e deterministico (mesmo estado, mesmo sonho)
3. Apos N ciclos, a acao "sonhar" tem frequencia (ciclo fechou)
4. A entropia dos sonhos e nao-trivial (ha estrutura, nao e ruido)
5. Regressoes 113/113 + 64/64 permanecem intactas
"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr

# Importa corpus matematico
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from corpus_matematico import alimentar_corpus_matematico


def main():
    print("=" * 70)
    print("  TESTE 16 — Sonho Markoviano: O MCR sonha a partir de si mesmo")
    print("=" * 70)

    # Carrega MCR com corpus
    print("\n[1] Carregando MCR com corpus...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # Cria o sonhador
    sonhador = SonhoMarkoviano(c)

    # === Teste 1: Sonho unico (greedy) ===
    print("\n[2a] Sonho unico — modo GREEDY (50 passos)...")
    t0 = time.time()
    sonho_greedy = sonhador.sonhar(n_passos=50, modo="greedy")
    dt = time.time() - t0
    tokens_g = sonho_greedy.split()
    print(f"  Tempo: {dt:.3f}s, Tokens: {len(tokens_g)}")
    print(f"  Sonho: '{sonho_greedy[:150]}'")

    # === Teste 1b: Sonho unico (entropia) ===
    print("\n[2b] Sonho unico — modo ENTROPIA (50 passos)...")
    t0 = time.time()
    sonho_ent = sonhador.sonhar(n_passos=50, modo="entropia")
    dt = time.time() - t0
    tokens_e = sonho_ent.split()
    print(f"  Tempo: {dt:.3f}s, Tokens: {len(tokens_e)}")
    print(f"  Sonho: '{sonho_ent[:150]}'")

    # Comparar diversidade
    from collections import Counter
    from math import log2
    def entropia_tokens(toks):
        if not toks:
            return 0.0
        cont = Counter(toks)
        n = len(toks)
        h = 0.0
        for c in cont.values():
            p = c / n
            if p > 0:
                h -= p * log2(p)
        return h

    h_greedy = entropia_tokens(tokens_g)
    h_ent = entropia_tokens(tokens_e)
    uniq_g = len(set(tokens_g))
    uniq_e = len(set(tokens_e))
    print(f"\n  Comparacao greedy vs entropia:")
    print(f"    Greedy:   H={h_greedy:.3f}, unicos={uniq_g}/{len(tokens_g)}")
    print(f"    Entropia: H={h_ent:.3f}, unicos={uniq_e}/{len(tokens_e)}")
    print(f"    Delta H:  {h_ent - h_greedy:+.3f}")
    print(f"    Delta uniq: {uniq_e - uniq_g:+d}")

    # === Teste 2: Determinismo (mesmo estado = mesmo sonho) ===
    print("\n[3] Determinismo (mesmo estado = mesmo sonho?)...")
    s1 = sonhador.sonhar(n_passos=30, semente=sonhador._serializar_estado(), modo="entropia")
    s2 = sonhador.sonhar(n_passos=30, semente=sonhador._serializar_estado(), modo="entropia")
    is_deterministico = s1 == s2
    print(f"  Sonho 1: '{s1[:100]}'")
    print(f"  Sonho 2: '{s2[:100]}'")
    print(f"  Deterministico: {'SIM' if is_deterministico else 'NAO'}")

    # === Teste 3: Novidade (tokens novos vs conhecidos) ===
    print("\n[4] Novidade do sonho (entropia)...")
    sonho = sonho_ent  # usar o sonho por entropia
    tokens_sonho = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
    vocab = set(c._palavra_acao.keys())
    n_novos = sum(1 for t in tokens_sonho if t not in vocab)
    n_conhecidos = len(tokens_sonho) - n_novos
    print(f"  Tokens: {len(tokens_sonho)}")
    print(f"  Conhecidos: {n_conhecidos}")
    print(f"  Novos: {n_novos}")
    print(f"  Taxa novidade: {n_novos/len(tokens_sonho)*100:.1f}%" if tokens_sonho else "  N/A")

    # === Teste 4: Ciclo de sonhos (realimentacao) — entropia ===
    print("\n[5] Ciclo de sonhos ENTROPIA (10 ciclos com realimentacao)...")
    print(f"  Antes: {c._total} obs, freq_sonhar={c._freq_acao.get('sonhar', 0)}")
    resultados_ent = sonhador.ciclo_sonho(n_ciclos=10, n_passos=30, modo="entropia")
    unicos_ent = sum(1 for r in resultados_ent if r['is_novo'])
    print(f"  Apos: {c._total} obs, freq_sonhar={c._freq_acao.get('sonhar', 0)}")
    print(f"  Sonhos unicos (entropia): {unicos_ent}/10")

    # === Teste 4b: Ciclo greedy para comparar ===
    print("\n[5b] Ciclo de sonhos GREEDY (10 ciclos, motor separado)...")
    c2, info2 = carregar_mcr(leve=True)
    sonhador2 = SonhoMarkoviano(c2)
    resultados_greedy = sonhador2.ciclo_sonho(n_ciclos=10, n_passos=30, modo="greedy")
    unicos_greedy = sum(1 for r in resultados_greedy if r['is_novo'])
    print(f"  Sonhos unicos (greedy): {unicos_greedy}/10")

    # === Teste 5: Persistencia diferencial ===
    print("\n[6] Persistencia diferencial (sonhar persiste?)...")
    freq_sonhar = c._freq_acao.get("sonhar", 0)
    freq_total = sum(c._freq_acao.values())
    p_sonhar = freq_sonhar / freq_total if freq_total > 0 else 0
    print(f"  P(sonhar) = {freq_sonhar}/{freq_total} = {p_sonhar:.4f}")
    print(f"  Sonhos unicos entropia: {unicos_ent}/10")
    print(f"  Sonhos unicos greedy:   {unicos_greedy}/10")

    # === Teste 6: Entropia dos sonhos ===
    print("\n[7] Entropia dos sonhos...")
    entropias = [r["entropia"] for r in resultados_ent]
    ent_media = sum(entropias) / len(entropias) if entropias else 0
    ent_min = min(entropias) if entropias else 0
    ent_max = max(entropias) if entropias else 0
    print(f"  Entropia (media/min/max): {ent_media:.3f} / {ent_min:.3f} / {ent_max:.3f}")

    entropias_g = [r["entropia"] for r in resultados_greedy]
    ent_media_g = sum(entropias_g) / len(entropias_g) if entropias_g else 0
    print(f"  Greedy (media): {ent_media_g:.3f}")
    print(f"  Delta H: {ent_media - ent_media_g:+.3f}")

    # === Estatisticas finais ===
    print("\n[8] Estatisticas finais...")
    stats = sonhador.estatisticas()
    print(f"  Total obs: {stats['total_obs']}")
    print(f"  Vocab: {stats['vocab']}")
    print(f"  Acoes: {stats['n_acoes']}")
    print(f"  Freq sonhar: {stats['freq_sonhar']}")
    print(f"  Top acoes: {sorted(stats['acoes'].items(), key=lambda x: -x[1])[:5]}")

    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO DO SONHO MARKOVIANO — GREEDY vs ENTROPIA")
    print("=" * 70)
    print(f"  Deterministico (Pilar 1):  {'PASS' if is_deterministico else 'FAIL'}")
    print(f"  Gera sequencia (nao vazio): {'PASS' if len(tokens_sonho) > 5 else 'FAIL'}")
    print(f"  Novidade > 0:              {'PASS' if n_novos > 0 else 'FAIL'} ({n_novos} novos)")
    print(f"  Ciclo fechou (freq>0):     {'PASS' if freq_sonhar > 0 else 'FAIL'} (freq={freq_sonhar})")
    print(f"  Entropia nao-trivial:      {'PASS' if 0.5 < ent_media < 7 else 'CHECK'} (H={ent_media:.3f})")
    print()
    print(f"  GREEDY:   unicos={unicos_greedy}/10, H_media={ent_media_g:.3f}")
    print(f"  ENTROPIA: unicos={unicos_ent}/10, H_media={ent_media:.3f}")
    print(f"  Melhoria entropia: unicos +{unicos_ent - unicos_greedy}, H +{ent_media - ent_media_g:.3f}")

    # Salva resultado
    resultado = {
        "teste": "sonho_markoviano",
        "mcr_antes": {"obs": info["total_obs"], "vocab": info["vocab"], "acoes": info["n_acoes"]},
        "mcr_depois": stats,
        "sonho_unico": {
            "n_tokens": len(tokens_sonho),
            "n_conhecidos": n_conhecidos,
            "n_novos": n_novos,
            "taxa_novidade": n_novos / len(tokens_sonho) if tokens_sonho else 0,
            "preview": sonho[:200],
        },
        "deterministico": is_deterministico,
        "ciclo_sonhos_entropia": resultados_ent,
        "ciclo_sonhos_greedy": resultados_greedy,
        "entropia": {"media": ent_media, "min": ent_min, "max": ent_max,
                     "greedy_media": ent_media_g},
        "unicos_entropia": unicos_ent,
        "unicos_greedy": unicos_greedy,
        "freq_sonhar": freq_sonhar,
        "p_sonhar": p_sonhar,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "16_sonho_markoviano.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
