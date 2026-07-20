"""25_emergir_escala.py — Ate onde o emergir vai?

Testar em escala:
1. 500 hipoteses livres — quantas novas? Qual a taxa de descoberta?
2. Sequencias longas (100+ tokens) — coerencia interna se mantem?
3. Por dominio — descobertas em cada regra matematica?
4. Por plano — descobertas em byte, char, token, bigrama?
"""
import sys, os, json, time, re
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr, mcr_decidir

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from corpus_matematico import validar_corpus_matematico


def main():
    print("=" * 70)
    print("  TESTE 25 — Ate onde o emergir vai?")
    print("=" * 70)

    # Carregar motor
    print("\n[1] Carregando motor...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    sonhador = SonhoMarkoviano(c)

    # === Teste 1: 500 hipoteses livres ===
    print("\n[2] 500 hipoteses livres...")
    t0 = time.time()
    hipoteses = sonhador.emergir_livre(n_hipoteses=500)
    dt = time.time() - t0
    print(f"  Tempo: {dt:.1f}s")

    novas = [h for h in hipoteses if h["e_nova"]]
    confirmadas = [h for h in hipoteses if h["confirmada"]]
    print(f"  Total: {len(hipoteses)}")
    print(f"  Confirmadas (sinergia > 0.05): {len(confirmadas)} ({len(confirmadas)/len(hipoteses)*100:.1f}%)")
    print(f"  Novas (nao coocorrem + confirmadas): {len(novas)} ({len(novas)/len(hipoteses)*100:.1f}%)")

    # Por acao
    print(f"\n  Descobertas por acao:")
    por_acao = Counter(h["acao"] for h in novas)
    for acao, n in por_acao.most_common():
        print(f"    {acao}: {n}")

    # Top 15 descobertas
    print(f"\n  Top 15 descobertas novas:")
    for h in novas[:15]:
        print(f"    '{h['x'][:12]}' + '{h['y'][:12]}' -> {h['acao'][:12]} "
              f"(conf={h['conf']}, sin={h['sinergia']:+.3f})")

    # === Teste 2: Sequencias longas ===
    print(f"\n[3] Sequencias longas (100, 200, 500 tokens)...")
    for n_passos in [100, 200, 500]:
        sonho = sonhador.sonhar(n_passos=n_passos, modo="greedy")
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
        # Validar: classificar o sonho
        acao, conf = mcr_decidir(c, sonho)
        # Coerencia: quantas trincas do sonho sao transicoes conhecidas?
        trincas = [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
        conhecidas = sum(1 for a, b in trincas if b in c._transicao_palavra.get(a, {}))
        taxa_coh = conhecidas / max(1, len(trincas))
        print(f"  {n_passos} passos: {len(tokens)} tokens, acao={acao}, "
              f"conf={conf:.3f}, coerencia={taxa_coh*100:.1f}%")

    # === Teste 3: Emergir por dominio ===
    print(f"\n[4] Emergir por dominio (acao alvo)...")
    # Para cada acao matematica, quantas descobertas novas mapeiam para ela?
    acoes_mat = ["PA", "PG", "FIB", "COLL", "QUAD", "TRI", "PRIMO"]
    for acao_alvo in acoes_mat:
        descobertas_acao = [h for h in novas if h["acao"] == acao_alvo]
        print(f"  {acao_alvo}: {len(descobertas_acao)} descobertas")
        if descobertas_acao:
            top = descobertas_acao[0]
            print(f"    top: '{top['x'][:12]}' + '{top['y'][:12]}' "
                  f"(conf={top['conf']}, sin={top['sinergia']:+.3f})")

    # === Teste 4: Sonho como gerador de "frases" ===
    print(f"\n[5] Sonho como gerador — 5 'frases' de 50 tokens...")
    for i in range(5):
        # Variar semente deterministicamente
        estado = sonhador._serializar_estado(max_tokens=50)
        rot = " ".join(estado.split()[i*5:] + estado.split()[:i*5])
        sonho = sonhador.sonhar(n_passos=50, semente=rot, modo="greedy")
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
        acao, conf = mcr_decidir(c, sonho)
        # Novelty: tokens novos vs conhecidos
        vocab = set(c._palavra_acao.keys())
        n_novos = sum(1 for t in tokens if t not in vocab)
        print(f"  #{i+1}: {len(tokens)} tokens, acao={acao}, conf={conf:.3f}, "
              f"novos={n_novos}")
        print(f"    '{sonho[:120]}'")

    # === Motor contaminado? ===
    print(f"\n[6] Motor contaminado?")
    print(f"  Obs: {c._total} (controle: {info['total_obs']})")
    print(f"  Vocab: {len(c._palavra_acao)} (controle: {info['vocab']})")
    contaminado = c._total > info['total_obs']
    print(f"  Contaminado? {'SIM' if contaminado else 'NAO'}")

    # === Salvar ===
    resultado = {
        "teste": "emergir_escala",
        "n_hipoteses": len(hipoteses),
        "n_confirmadas": len(confirmadas),
        "n_novas": len(novas),
        "taxa_descoberta": len(novas) / len(hipoteses),
        "descobertas_por_acao": dict(por_acao),
        "top_descobertas": novas[:15],
        "motor_contaminado": contaminado,
        "tempo": dt,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "25_emergir_escala.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
