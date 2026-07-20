"""22_sonho_alimenta_motor.py — O sonho melhora o motor?

Integrar criatividade (sonho) com logica (motor). O sonho alimenta
o motor de volta (FASE 21). O motor fica melhor — ou contamina?

Setup:
- Motor A (controle): corpus base (1262 obs)
- Motor B (experimental): corpus base + 10 sonhos alimentados de volta

Testes:
1. Classificacao: B > A? (zerar_shot + regras + formigueiro)
2. Criatividade: B > A? (sonho de B mais diverso que sonho de A?)
3. Vocabulario: B > A? (B tem mais vocab?)
"""
import sys, os, json, time, re
from collections import Counter
from math import log2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr, mcr_decidir, mcr_nmi

# Importa corpus matematico
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from corpus_matematico import alimentar_corpus_matematico, validar_corpus_matematico


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


def alimentar_sonhos(c, n_sonhos=10, n_passos=50):
    """Alimenta n_sonhos sonhos no coupling e retorna os sonhos."""
    sonhador = SonhoMarkoviano(c)
    sonhos = []
    hashes = set()
    semente_atual = None

    for i in range(100):
        s = sonhador._serializar_estado() if semente_atual is None else semente_atual
        sonho = sonhador.sonhar(n_passos=n_passos, semente=s, modo="greedy")
        h = sonho[:100]
        if h not in hashes:
            hashes.add(h)
            sonhos.append(sonho)
            if len(sonhos) >= n_sonhos:
                break
        tokens = sonhador._RE_TOKENS.findall(sonho.lower())
        if tokens:
            semente_atual = " ".join(tokens[-15:]) + " " + sonhador._serializar_estado(max_tokens=50)
        c.alimentar(sonho, "sonhar")

    return sonhos


def testar_classificacao(c):
    """Testa classificacao em regras + zero-shot."""
    # Regras matematicas (17 zero-shot)
    ac_regras, tot_regras, _ = validar_corpus_matematico(c)

    # Zero-shot (subconjunto do teste 14)
    testes_zs = [
        ("criar alquimista pocoes", "gerar_npc"),
        ("fazer golem pedra", "gerar_monstro"),
        ("qual diferenca markov", "responder"),
        ("criar textura agua", "gerar_sprite"),
        ("criar missao resgate", "gerar_quest"),
        ("encontrar arquivos config", "buscar"),
        ("examinar codigo python", "analisar"),
        ("confirmar sintaxe lua", "validar"),
        ("ligar modulo npc", "conectar"),
        ("absorver nova informacao", "aprender"),
    ]
    ac_zs = 0
    for texto, esp in testes_zs:
        acao, _ = mcr_decidir(c, texto)
        if acao == esp:
            ac_zs += 1

    return {
        "regras": {"acertos": ac_regras, "total": tot_regras,
                   "taxa": ac_regras / tot_regras if tot_regras else 0},
        "zero_shot": {"acertos": ac_zs, "total": len(testes_zs),
                      "taxa": ac_zs / len(testes_zs)},
    }


def testar_criatividade(c):
    """Testa criatividade: sonho do motor apos alimentacao."""
    sonhador = SonhoMarkoviano(c)
    sonho = sonhador.sonhar(n_passos=50, modo="greedy")
    tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
    h = entropia_tokens(tokens)
    n_uniq = len(set(tokens))
    return {
        "n_tokens": len(tokens),
        "n_uniq": n_uniq,
        "entropia": round(h, 3),
        "preview": sonho[:200],
    }


def testar_sinonimia(c):
    """Testa sinonimia cross-idioma (subconjunto)."""
    pares = [
        ("amor", "love", 1), ("casa", "house", 1), ("agua", "water", 1),
        ("cachorro", "mesa", 0), ("fogo", "numero", 0), ("peixe", "musica", 0),
    ]
    scores = []
    labels = []
    for a, b, label in pares:
        s = mcr_nmi(c, a, b)
        scores.append(s)
        labels.append(label)
    # AUC
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return {"auc": 0.5}
    ordenado = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    auc = 0.0
    for s, l in ordenado:
        if l == 1:
            tp += 1
        else:
            auc += tp
    return {"auc": round(auc / (n_pos * n_neg), 4)}


def main():
    print("=" * 70)
    print("  TESTE 22 — O Sonho Alimenta o Motor?")
    print("=" * 70)

    # === Motor A (controle) ===
    print("\n[1] Motor A (controle: corpus base)...")
    cA, _ = carregar_mcr(leve=True)
    stats_A = {
        "obs": cA._total,
        "vocab": len(cA._palavra_acao),
        "acoes": len(cA._freq_acao),
    }
    print(f"  {stats_A['obs']} obs, {stats_A['vocab']} pal, {stats_A['acoes']} acoes")

    # === Motor B (experimental: controle + 10 sonhos) ===
    print("\n[2] Motor B (experimental: controle + 10 sonhos)...")
    cB, _ = carregar_mcr(leve=True)
    sonhos = alimentar_sonhos(cB, n_sonhos=10, n_passos=50)
    stats_B = {
        "obs": cB._total,
        "vocab": len(cB._palavra_acao),
        "acoes": len(cB._freq_acao),
        "n_sonhos": len(sonhos),
    }
    print(f"  {stats_B['obs']} obs, {stats_B['vocab']} pal, {stats_B['acoes']} acoes")
    print(f"  +{len(sonhos)} sonhos alimentados")
    print(f"  Vocab novo: {stats_B['vocab'] - stats_A['vocab']} palavras")

    # === Teste 1: Classificacao ===
    print("\n[3] Teste de classificacao...")
    print("  Motor A:")
    class_A = testar_classificacao(cA)
    print(f"    Regras: {class_A['regras']['acertos']}/{class_A['regras']['total']} "
          f"= {class_A['regras']['taxa']*100:.1f}%")
    print(f"    Zero-shot: {class_A['zero_shot']['acertos']}/{class_A['zero_shot']['total']} "
          f"= {class_A['zero_shot']['taxa']*100:.1f}%")

    print("  Motor B:")
    class_B = testar_classificacao(cB)
    print(f"    Regras: {class_B['regras']['acertos']}/{class_B['regras']['total']} "
          f"= {class_B['regras']['taxa']*100:.1f}%")
    print(f"    Zero-shot: {class_B['zero_shot']['acertos']}/{class_B['zero_shot']['total']} "
          f"= {class_B['zero_shot']['taxa']*100:.1f}%")

    # === Teste 2: Criatividade ===
    print("\n[4] Teste de criatividade (sonho do motor)...")
    print("  Motor A (sonha):")
    criat_A = testar_criatividade(cA)
    print(f"    H={criat_A['entropia']}, unicos={criat_A['n_uniq']}, "
          f"tokens={criat_A['n_tokens']}")
    print(f"    '{criat_A['preview'][:100]}'")

    print("  Motor B (sonha apos ser alimentado por sonhos):")
    criat_B = testar_criatividade(cB)
    print(f"    H={criat_B['entropia']}, unicos={criat_B['n_uniq']}, "
          f"tokens={criat_B['n_tokens']}")
    print(f"    '{criat_B['preview'][:100]}'")

    # === Teste 3: Sinonimia ===
    print("\n[5] Teste de sinonimia...")
    sin_A = testar_sinonimia(cA)
    sin_B = testar_sinonimia(cB)
    print(f"  Motor A: AUC={sin_A['auc']}")
    print(f"  Motor B: AUC={sin_B['auc']}")

    # === Comparacao ===
    print("\n" + "=" * 70)
    print("  COMPARACAO: Motor A (controle) vs Motor B (controle + sonhos)")
    print("=" * 70)

    d_regras = class_B['regras']['taxa'] - class_A['regras']['taxa']
    d_zs = class_B['zero_shot']['taxa'] - class_A['zero_shot']['taxa']
    d_h = criat_B['entropia'] - criat_A['entropia']
    d_uniq = criat_B['n_uniq'] - criat_A['n_uniq']
    d_auc = sin_B['auc'] - sin_A['auc']
    d_vocab = stats_B['vocab'] - stats_A['vocab']

    print(f"  {'Metrica':<25s} {'Motor A':>10s} {'Motor B':>10s} {'Delta':>10s} {'Vencedor':>10s}")
    print(f"  {'-'*65}")
    print(f"  {'Regras':<25s} {class_A['regras']['taxa']*100:>9.1f}% {class_B['regras']['taxa']*100:>9.1f}% "
          f"{d_regras*100:>+9.1f}% {'B' if d_regras > 0 else ('A' if d_regras < 0 else '='):>10s}")
    print(f"  {'Zero-shot':<25s} {class_A['zero_shot']['taxa']*100:>9.1f}% {class_B['zero_shot']['taxa']*100:>9.1f}% "
          f"{d_zs*100:>+9.1f}% {'B' if d_zs > 0 else ('A' if d_zs < 0 else '='):>10s}")
    print(f"  {'Sonho H':<25s} {criat_A['entropia']:>10.3f} {criat_B['entropia']:>10.3f} "
          f"{d_h:>+10.3f} {'B' if d_h > 0 else ('A' if d_h < 0 else '='):>10s}")
    print(f"  {'Sonho unicos':<25s} {criat_A['n_uniq']:>10d} {criat_B['n_uniq']:>10d} "
          f"{d_uniq:>+10d} {'B' if d_uniq > 0 else ('A' if d_uniq < 0 else '='):>10s}")
    print(f"  {'Sinonimia AUC':<25s} {sin_A['auc']:>10.3f} {sin_B['auc']:>10.3f} "
          f"{d_auc:>+10.3f} {'B' if d_auc > 0 else ('A' if d_auc < 0 else '='):>10s}")
    print(f"  {'Vocab':<25s} {stats_A['vocab']:>10d} {stats_B['vocab']:>10d} "
          f"{d_vocab:>+10d} {'B' if d_vocab > 0 else ('A' if d_vocab < 0 else '='):>10s}")

    # Veredito
    vencedores_B = sum([d_regras > 0, d_zs > 0, d_h > 0, d_uniq > 0, d_auc > 0, d_vocab > 0])
    vencedores_A = sum([d_regras < 0, d_zs < 0, d_h < 0, d_uniq < 0, d_auc < 0, d_vocab < 0])
    print(f"\n  Vencedores B: {vencedores_B}/6")
    print(f"  Vencedores A: {vencedores_A}/6")

    if vencedores_B > vencedores_A:
        veredito = "SONHO MELHORA O MOTOR"
    elif vencedores_A > vencedores_B:
        veredito = "SONHO CONTAMINA O MOTOR"
    else:
        veredito = "SONHO E NEUTRO"
    print(f"  Veredito: {veredito}")

    # Salvar
    resultado = {
        "teste": "sonho_alimenta_motor",
        "motor_A": {**stats_A, **class_A, "criatividade": criat_A, "sinonimia": sin_A},
        "motor_B": {**stats_B, **class_B, "criatividade": criat_B, "sinonimia": sin_B},
        "delta": {
            "regras": d_regras, "zero_shot": d_zs,
            "sonho_h": d_h, "sonho_uniq": d_uniq,
            "sinonimia_auc": d_auc, "vocab": d_vocab,
        },
        "veredito": veredito,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "22_sonho_alimenta_motor.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
