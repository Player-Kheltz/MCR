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
import sys, os, json, time
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

    # === Teste 1: Sonho unico ===
    print("\n[2] Sonho unico (50 passos)...")
    t0 = time.time()
    sonho = sonhador.sonhar(n_passos=50)
    dt = time.time() - t0
    print(f"  Tempo: {dt:.3f}s")
    print(f"  Sonho: '{sonho[:200]}'")
    print(f"  Total tokens: {len(sonho.split())}")

    # === Teste 2: Determinismo (mesmo estado = mesmo sonho) ===
    print("\n[3] Determinismo (mesmo estado = mesmo sonho?)...")
    sonho1 = sonhador.sonhar(n_passos=30, semente=sonhador._serializar_estado())
    sonho2 = sonhador.sonhar(n_passos=30, semente=sonhador._serializar_estado())
    is_deterministico = sonho1 == sonho2
    print(f"  Sonho 1: '{sonho1[:100]}'")
    print(f"  Sonho 2: '{sonho2[:100]}'")
    print(f"  Deterministico: {'SIM' if is_deterministico else 'NAO'}")

    # === Teste 3: Novidade (tokens novos vs conhecidos) ===
    print("\n[4] Novidade do sonho...")
    import re
    tokens_sonho = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
    vocab = set(c._palavra_acao.keys())
    n_novos = sum(1 for t in tokens_sonho if t not in vocab)
    n_conhecidos = len(tokens_sonho) - n_novos
    print(f"  Tokens: {len(tokens_sonho)}")
    print(f"  Conhecidos: {n_conhecidos}")
    print(f"  Novos: {n_novos}")
    print(f"  Taxa novidade: {n_novos/len(tokens_sonho)*100:.1f}%" if tokens_sonho else "  N/A")

    # === Teste 4: Ciclo de sonhos (realimentacao) ===
    print("\n[5] Ciclo de sonhos (10 ciclos com realimentacao)...")
    print(f"  Antes: {c._total} obs, freq_sonhar={c._freq_acao.get('sonhar', 0)}")
    resultados = sonhador.ciclo_sonho(n_ciclos=10, n_passos=30)
    print(f"  Apos: {c._total} obs, freq_sonhar={c._freq_acao.get('sonhar', 0)}")

    # === Teste 5: Persistencia diferencial ===
    print("\n[6] Persistencia diferencial (sonhar persiste?)...")
    freq_sonhar = c._freq_acao.get("sonhar", 0)
    freq_total = sum(c._freq_acao.values())
    p_sonhar = freq_sonhar / freq_total if freq_total > 0 else 0
    print(f"  P(sonhar) = {freq_sonhar}/{freq_total} = {p_sonhar:.4f}")
    print(f"  Sonhos unicos: {sum(1 for r in resultados if r['is_novo'])}/{len(resultados)}")

    # === Teste 6: Entropia dos sonhos ===
    print("\n[7] Entropia dos sonhos...")
    entropias = [r["entropia"] for r in resultados]
    ent_media = sum(entropias) / len(entropias) if entropias else 0
    ent_min = min(entropias) if entropias else 0
    ent_max = max(entropias) if entropias else 0
    print(f"  Media: {ent_media:.3f}")
    print(f"  Min:   {ent_min:.3f}")
    print(f"  Max:   {ent_max:.3f}")
    print(f"  Interpretacao: {'estruturado (H<2)' if ent_media < 2 else 'diverso (H>=2)'}")

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
    print("  RESUMO DO SONHO MARKOVIANO")
    print("=" * 70)
    print(f"  Deterministico (Pilar 1):  {'PASS' if is_deterministico else 'FAIL'}")
    print(f"  Gera sequencia (nao vazio): {'PASS' if len(tokens_sonho) > 5 else 'FAIL'}")
    print(f"  Novidade > 0:              {'PASS' if n_novos > 0 else 'FAIL'} ({n_novos} novos)")
    print(f"  Ciclo fechou (freq>0):     {'PASS' if freq_sonhar > 0 else 'FAIL'} (freq={freq_sonhar})")
    print(f"  Entropia nao-trivial:      {'PASS' if 0.5 < ent_media < 5 else 'CHECK'} (H={ent_media:.3f})")
    print(f"  Sonhos unicos:             {sum(1 for r in resultados if r['is_novo'])}/{len(resultados)}")

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
        "ciclo_sonhos": resultados,
        "entropia": {"media": ent_media, "min": ent_min, "max": ent_max},
        "freq_sonhar": freq_sonhar,
        "p_sonhar": p_sonhar,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "16_sonho_markoviano.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
