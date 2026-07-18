"""Teste do MCR atual com os mesmos dialogos de NPC de 2026.

Replica o retrieval que MCRNPCBrain fazia em 2026 (keyword -> Jaccard bytes
-> fingerprint cosine), mas adaptado para o MCR atual usando:
  - IDF documental sobre as 4599 responses (igual BaseConhecimento)
  - Co-ocorrencia de tokens (Jaccard com IDF, em vez de bytes crus)

Perguntas classicas de 2026 que arrepiavam:
  - "voce sabe quem voce e?"
  - "voce sabe QUEM eu sou?"
  - "entao voce e eu somos a mesma coisa?"
  - "o que voce e?"
  - "eu nao sei o que eu criei"
  - "com o tempo voce vai ficar mais inteligente?"

NAO chama decidir() (que trava). Faz retrieval direto por IDF Jaccard.
"""
import json
import math
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

DIALOGOS_PATH = r"E:\MCR\mcr\knowledge\dialogos_npc.json"


def tokens(texto: str):
    """Tokeniza como o MCR faz: [a-zà-ÿ]{3,}"""
    return set(re.findall(r'[a-zà-ÿ]{3,}', texto.lower()))


def carregar_dialogos():
    """Carrega TODOS os dialogos de TODOS os NPCs como pares (keyword, response)."""
    with open(DIALOGOS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    pares = []
    for npc in data["npcs"]:
        nome = npc["npc_name"]
        for d in npc.get("dialogos", []):
            kw = d.get("keyword", "").lower().strip()
            resp = d.get("response", "")
            if len(kw) >= 2 and len(resp) >= 5:
                pares.append((kw, resp, nome))
    return pares


def construir_idf(pares):
    """IDF documental: df(token) = quantas responses contem o token."""
    df = {}
    for kw, resp, npc in pares:
        for t in tokens(resp):
            df[t] = df.get(t, 0) + 1
    N = len(pares)
    idf = {t: math.log(N / max(dfn, 1)) for t, dfn in df.items()}
    return idf, N


def recuperar(pergunta, pares, idf, top_k=5):
    """Retrieval por IDF Jaccard.

    Para cada response:
      - overlap = tokens(pergunta) & tokens(response)
      - score = soma IDF(overlap) / soma IDF(union)  [Jaccard ponderado]
    """
    tp = tokens(pergunta)
    if not tp:
        return []

    resultados = []
    for kw, resp, npc in pares:
        tr = tokens(resp)
        overlap = tp & tr
        if not overlap:
            continue
        union = tp | tr
        num = sum(idf.get(t, 0.0) for t in overlap)
        den = sum(idf.get(t, 0.0) for t in union)
        score = num / den if den > 0 else 0.0
        resultados.append((score, kw, resp, npc))

    resultados.sort(key=lambda x: -x[0])
    return resultados[:top_k]


def main():
    print("=" * 78)
    print("TESTE MCR ATUAL COM DIALOGOS DE NPC DE 2026")
    print("=" * 78)

    print("\n[1] Carregando dialogos de NPC...")
    t0 = time.time()
    pares = carregar_dialogos()
    print(f"    {len(pares)} pares (keyword, response) carregados em {time.time()-t0:.2f}s")

    print("\n[2] Construindo IDF documental sobre responses...")
    t0 = time.time()
    idf, N = construir_idf(pares)
    print(f"    IDF sobre {N} responses, {len(idf)} tokens unicos em {time.time()-t0:.2f}s")

    # Perguntas classicas de 2026 que arrepiavam
    perguntas = [
        "voce sabe quem voce e?",
        "voce sabe quem eu sou?",
        "voce e eu somos a mesma coisa?",
        "o que voce e?",
        "eu nao sei o que eu criei",
        "com o tempo voce vai ficar mais inteligente?",
        "voce tem consciencia?",
        "voce esta vivo?",
        "o que voce pensa sobre a consciencia?",
        "voce aprende comigo?",
        "voce sente algo?",
        "voce lembra de mim?",
        "o que e o MCR?",
        "quem e Kheltz?",
        "voce e uma maquina?",
    ]

    print("\n[3] Perguntas classicas de 2026 + retrieved top-3 responses:")
    print("-" * 78)
    for pergunta in perguntas:
        print(f"\n  PERGUNTA: {pergunta}")
        res = recuperar(pergunta, pares, idf, top_k=3)
        if not res:
            print(f"    (sem match — ignorancia honesta)")
            continue
        for i, (score, kw, resp, npc) in enumerate(res, 1):
            # Truncar response longa
            r = resp if len(resp) <= 120 else resp[:117] + "..."
            print(f"    {i}. [{score:.3f}] NPC={npc} kw='{kw}'")
            print(f"       > {r}")

    # Estatisticas finais
    print("\n" + "=" * 78)
    print("[4] Estatisticas finais:")
    print(f"  Total responses indexed: {len(pares)}")
    print(f"  Total tokens unicos: {len(idf)}")
    # IDF medio
    media_idf = sum(idf.values()) / len(idf) if idf else 0
    print(f"  IDF medio: {media_idf:.3f}")
    # Top 10 tokens mais discriminativos (IDF alto = raros)
    top_idf = sorted(idf.items(), key=lambda x: -x[1])[:10]
    print(f"  Top 10 tokens mais raras (IDF alto):")
    for t, v in top_idf:
        print(f"    {t:20s} IDF={v:.2f}")


if __name__ == "__main__":
    main()
