"""20_trindade_delibera.py — Os 3 sonhos sao as 3 perspectivas do triunvirato?

Hipotese: os 3 sonhos unicos (greedy, Pilar 1 puro) sao as 3 perspectivas
do triunvirato (Pilar 10). Se cada sonho e uma perspectiva, eles devem:

1. DISCORDAR em alguns casos (perspectivas diferentes)
2. CONCORDAR em outros (consenso)
3. A combinacao dos 3 deve ser melhor que qualquer um isolado

Teste:
1. Extrair os 3 sonhos unicos
2. Alimentar cada sonho como "perspectiva" num sub-MCR
3. Para cada input de teste, cada perspectiva classifica
4. Se 2+ concordam = consenso (Pilar 10)
5. Comparar: consenso dos 3 vs global vs cada um isolado

Tambem: corpus-independencia — 3 emerge com Wikipedia?
"""
import sys, os, json, time, re
from collections import Counter, defaultdict
from math import log2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr, mcr_decidir


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


def extrair_3_sonhos(c, n_passos=30):
    """Extrai exatamente os 3 sonhos unicos do Pilar 1 puro (greedy)."""
    sonhador = SonhoMarkoviano(c)
    sonhos = []
    hashes = set()
    semente_atual = None

    for i in range(100):  # max 100 ciclos, para apos 3 unicos
        if semente_atual is None:
            semente = sonhador._serializar_estado()
        else:
            semente = semente_atual

        sonho = sonhador.sonhar(n_passos=n_passos, semente=semente, modo="greedy")
        h = sonho[:100]

        if h not in hashes:
            hashes.add(h)
            sonhos.append(sonho)
            if len(sonhos) >= 3:
                break

        tokens = sonhador._RE_TOKENS.findall(sonho.lower())
        if tokens:
            semente_atual = " ".join(tokens[-15:]) + " " + sonhador._serializar_estado(max_tokens=50)

        c.alimentar(sonho, "sonhar")

    return sonhos


def criar_perspectiva(sonho, coupling_base):
    """Cria um sub-MCR 'perspectiva' a partir de um sonho.

    A perspectiva e um MCR treinado com o sonho como corpus.
    Cada perspectiva tem uma visao diferente do mundo.
    """
    sub = MCRCoupling()
    tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())

    # Treinar com transicoes do sonho
    for i in range(len(tokens) - 1):
        sub.alimentar(tokens[i], tokens[i+1])

    # Tambem alimentar pares (palavra, acao) do sonho
    # Cada palavra do sonho vota nas acoes que conhece do coupling base
    for token in set(tokens):
        dist = coupling_base._palavra_acao.get(token, {})
        for acao, count in dist.items():
            for _ in range(min(count, 3)):
                sub.alimentar(token, acao)

    return sub


def testar_trindade(c, sonhos, testes):
    """Testa se os 3 sonhos funcionam como triunvirato.

    Cada sonho vira uma perspectiva. Para cada input:
    1. Cada perspectiva classifica (decidir)
    2. Se 2+ concordam = consenso
    3. Se 3 discordam = empate (usar global)

    Retorna acuracia de cada perspectiva isolada e do consenso.
    """
    # Criar 3 perspectivas
    perspectivas = []
    for i, sonho in enumerate(sonhos):
        sub = criar_perspectiva(sonho, c)
        perspectivas.append(sub)
        print(f"  Perspectiva #{i+1}: {len(sub._palavra_acao)} pal, "
              f"{len(sub._freq_acao)} acoes")

    # Testar
    resultados = []
    acertos_pers = [0, 0, 0]
    acertos_consenso = 0
    acertos_global = 0
    n_discordancas = 0
    n_consensos = 0

    for texto, esperado in testes:
        # Cada perspectiva classifica
        preds = []
        for sub in perspectivas:
            if len(sub._freq_acao) > 0:
                acao, conf = sub.decidir(texto, (None, 0.0))
            else:
                acao, conf = "NONE", 0.0
            preds.append(acao)

        # Global
        acao_g, conf_g = mcr_decidir(c, texto)

        # Consenso: 2+ concordam
        contagem = Counter(preds)
        top2 = contagem.most_common(2)
        if top2[0][1] >= 2:
            consenso = top2[0][0]
            n_consensos += 1
        else:
            # 3 discordam — usar global
            consenso = acao_g
            n_discordancas += 1

        # Verificar acertos
        for i, pred in enumerate(preds):
            if pred == esperado:
                acertos_pers[i] += 1
        if consenso == esperado:
            acertos_consenso += 1
        if acao_g == esperado:
            acertos_global += 1

        resultados.append({
            "texto": texto[:40],
            "esperado": esperado,
            "p1": preds[0],
            "p2": preds[1],
            "p3": preds[2],
            "consenso": consenso,
            "global": acao_g,
            "discordam": top2[0][1] < 2,
        })

    return {
        "acertos_perspectivas": acertos_pers,
        "acertos_consenso": acertos_consenso,
        "acertos_global": acertos_global,
        "n_testes": len(testes),
        "n_discordancas": n_discordancas,
        "n_consensos": n_consensos,
        "detalhes": resultados,
    }


def testar_corpus_independencia():
    """Testa se o 3 emerge com corpus diferente (Wikipedia)."""
    print("\n  Carregando Wikipedia...")
    c, info = carregar_mcr(leve=False)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    sonhador = SonhoMarkoviano(c)
    hashes = set()
    unicos = []
    semente_atual = None

    for i in range(50):
        if semente_atual is None:
            semente = sonhador._serializar_estado()
        else:
            semente = semente_atual

        sonho = sonhador.sonhar(n_passos=30, semente=semente, modo="greedy")
        h = sonho[:100]
        if h not in hashes:
            hashes.add(h)
            unicos.append(i + 1)

        tokens = sonhador._RE_TOKENS.findall(sonho.lower())
        if tokens:
            semente_atual = " ".join(tokens[-15:]) + " " + sonhador._serializar_estado(max_tokens=50)
        c.alimentar(sonho, "sonhar")

    return len(unicos), unicos


def main():
    print("=" * 70)
    print("  TESTE 20 — A Trindade Delibera: 3 sonhos = 3 perspectivas?")
    print("=" * 70)

    # === Extrair 3 sonhos ===
    print("\n[1] Extraindo 3 sonhos unicos (greedy, Pilar 1 puro)...")
    c, info = carregar_mcr(leve=True)
    sonhos = extrair_3_sonhos(c, n_passos=30)
    print(f"  {len(sonhos)} sonhos extraidos")
    for i, s in enumerate(sonhos):
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', s.lower())
        h = entropia_tokens(tokens)
        print(f"  Sonho #{i+1}: {len(tokens)} tokens, H={h:.3f}")
        print(f"    '{s[:100]}'")

    # === Testar triunvirato ===
    print("\n[2] Testando trindade como triunvirato...")
    testes = [
        ("sequencia dois quatro seis oito", "PA"),
        ("padrao tres cinco oito treze", "FIB"),
        ("encadear cinco dezesseis oito quatro", "COLL"),
        ("numeros quatro oito dezesseis", "PG"),
        ("ordem dois tres cinco sete", "PRIMO"),
        ("criar npc ferreiro", "gerar_npc"),
        ("o que e markov", "responder"),
        ("dezesseis oito quatro dois", "COLL"),
        ("oito quatro dois um", "COLL"),
        ("um um dois tres", "FIB"),
    ]

    # Recarregar motor limpo para o teste
    c2, _ = carregar_mcr(leve=True)
    resultado = testar_trindade(c2, sonhos, testes)

    # === Resultados ===
    print("\n[3] Resultados:")
    n = resultado["n_testes"]
    for i, ac in enumerate(resultado["acertos_perspectivas"]):
        print(f"  Perspectiva #{i+1}: {ac}/{n} = {ac/n*100:.1f}%")
    print(f"  Consenso (2+):    {resultado['acertos_consenso']}/{n} = "
          f"{resultado['acertos_consenso']/n*100:.1f}%")
    print(f"  Global:           {resultado['acertos_global']}/{n} = "
          f"{resultado['acertos_global']/n*100:.1f}%")
    print(f"  Consensos: {resultado['n_consensos']}, Discordancias: {resultado['n_discordancas']}")

    print("\n[4] Detalhes:")
    print(f"  {'Teste':<40s} {'Esp':<8s} {'P1':<10s} {'P2':<10s} {'P3':<10s} {'Cons':<10s} {'Glob':<10s}")
    for r in resultado["detalhes"]:
        dis = "*" if r["discordam"] else " "
        print(f"  {r['texto'][:38]:<40s} {r['esperado']:<8s} "
              f"{r['p1'][:8]:<10s} {r['p2'][:8]:<10s} {r['p3'][:8]:<10s} "
              f"{r['consenso'][:8]:<10s} {r['global'][:8]:<10s} {dis}")

    # === Corpus independencia ===
    print("\n[5] Corpus-independencia (3 emerge com Wikipedia?)...")
    n_wiki, unicos_wiki = testar_corpus_independencia()
    print(f"  Wikipedia: {n_wiki} unicos em {unicos_wiki}")

    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO — A Trindade Delibera?")
    print("=" * 70)
    ac_consenso = resultado["acertos_consenso"] / n
    ac_global = resultado["acertos_global"] / n
    ac_pers = [a / n for a in resultado["acertos_perspectivas"]]
    melhor_pers = max(ac_pers)
    print(f"  Melhor perspectiva isolada: {melhor_pers*100:.1f}%")
    print(f"  Consenso (2+ concordam):    {ac_consenso*100:.1f}%")
    print(f"  Global (MCR completo):       {ac_global*100:.1f}%")
    print(f"  Consenso > Global? {'SIM' if ac_consenso > ac_global else 'NAO'}")
    print(f"  Consenso > Melhor pers? {'SIM' if ac_consenso > melhor_pers else 'NAO'}")
    print(f"\n  3 emerge com Wikipedia? {'SIM' if n_wiki == 3 else 'NAO'} ({n_wiki})")

    # Salvar
    resultado_final = {
        "teste": "trindade_delibera",
        "n_sonhos": len(sonhos),
        "sonhos": [s[:200] for s in sonhos],
        "resultado_trindade": {
            "acertos_perspectivas": resultado["acertos_perspectivas"],
            "acertos_consenso": resultado["acertos_consenso"],
            "acertos_global": resultado["acertos_global"],
            "n_testes": n,
            "n_discordancas": resultado["n_discordancas"],
            "n_consensos": resultado["n_consensos"],
        },
        "consenso_supera_global": ac_consenso > ac_global,
        "consenso_supera_melhor_pers": ac_consenso > melhor_pers,
        "corpus_independencia": {"n_unicos_wiki": n_wiki, "unicos": unicos_wiki},
        "numero_3_corpus_independente": n_wiki == 3,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "20_trindade_delibera.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
