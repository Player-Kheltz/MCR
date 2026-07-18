"""Teste do MCR ATUAL (167K obs Wikipedia+Rosetta) alimentado com dialogos NPC.

Diferente do teste anterior (que so fazia retrieval direto via IDF Jaccard),
este teste:
  1. Carrega o motor atual do cache (167K obs, 204K palavras)
  2. Alimenta os 3493 dialogos NPC como novas observacoes
     (acao=keyword, texto=response)
  3. Usa extrair_relacoes() em palavras-chave das perguntas classicas de 2026
  4. Ve o que o MCR DESCOBRE sobre essas palavras no corpus de NPC
"""
import json
import os
import sys
import time

sys.path.insert(0, r"E:\MCR")
sys.stdout.reconfigure(encoding='utf-8')

from mcr.coupling import MCRCoupling

DIALOGOS_PATH = r"E:\MCR\mcr\knowledge\dialogos_npc.json"
MOTOR_PATH = r"E:\MCR\cache\coupling_MCRCoupling_backup_preB2c.json"


def carregar_dialogos():
    with open(DIALOGOS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    pares = []
    for npc in data["npcs"]:
        for d in npc.get("dialogos", []):
            kw = (d.get("keyword", "") or "").lower().strip()
            resp = d.get("response", "") or ""
            if len(kw) >= 2 and len(resp) >= 5:
                pares.append((kw, resp, npc["npc_name"]))
    return pares


def main():
    print("=" * 78)
    print("TESTE MCR ATUAL (167K) + DIALOGOS NPC INGERIDOS")
    print("=" * 78)

    print("\n[1] Carregando motor atual (167K obs)...")
    t0 = time.time()
    motor = MCRCoupling()
    ok = motor.load(MOTOR_PATH)
    print(f"    load()={ok} em {time.time()-t0:.1f}s")
    print(f"    Total obs: {motor._total}")
    print(f"    Vocabulario: {len(motor._transicao_palavra)}")
    print(f"    Acoes: {len(motor._freq_acao)}")

    print("\n[2] Carregando dialogos NPC...")
    pares = carregar_dialogos()
    print(f"    {len(pares)} pares (keyword, response) carregados")

    print("\n[3] Alimentando motor com dialogos NPC...")
    t0 = time.time()
    n = 0
    for kw, resp, npc in pares:
        # acao = keyword (igual concept ID na Wikipedia), texto = response
        motor.alimentar(resp, kw)
        n += 1
        if n % 500 == 0:
            print(f"    {n}/{len(pares)}  ({time.time()-t0:.1f}s)")
    print(f"    Alimentado {n} dialogos em {time.time()-t0:.1f}s")

    # Perguntas classicas + palavras-chave para investigar
    perguntas_palavras = [
        ("voce sabe quem voce e?",         ["sabe", "quem", "voce"]),
        ("voce sabe quem eu sou?",         ["sabe", "quem"]),
        ("voce e eu somos a mesma coisa?", ["mesma", "coisa", "somos"]),
        ("o que voce e?",                  ["voce"]),
        ("voce tem consciencia?",          ["consciencia", "consciência"]),
        ("voce esta vivo?",                ["vivo"]),
        ("voce aprende comigo?",           ["aprende"]),
        ("voce lembra de mim?",            ["lembra", "mim"]),
        ("o que e o MCR?",                 ["mcr"]),
        ("quem e Kheltz?",                 ["kheltz"]),
        ("voce sente algo?",               ["sente"]),
        ("o que voce pensa?",              ["pensa"]),
    ]

    print("\n[4] extrair_relacoes() para palavras-chave das perguntas:")
    print("-" * 78)
    for pergunta, palavras in perguntas_palavras:
        print(f"\n  PERGUNTA: {pergunta}")
        for p in palavras:
            try:
                rels = motor.extrair_relacoes(p, top_n=5)
            except Exception as e:
                print(f"    erro em '{p}': {e}")
                continue
            sinonimos = rels.get("sinonimos", [])
            if not sinonimos:
                print(f"    [{p}] (sem sinonimos descobertos)")
                continue
            print(f"    [{p}] sinonimos descobertos:")
            for s, score in sinonimos[:5]:
                # Truncar nome
                print(f"      {s:25s}  NMI={score:.3f}")

    # Estatistica final
    print("\n" + "=" * 78)
    print("[5] Estatisticas do motor apos ingestao NPC:")
    print(f"  Total obs: {motor._total}")
    print(f"  Vocabulario: {len(motor._transicao_palavra)}")
    print(f"  Acoes: {len(motor._freq_acao)}")
    # Acoes mais frequentes
    top_acoes = sorted(motor._freq_acao.items(), key=lambda x: -x[1])[:15]
    print(f"  Top 15 acoes mais frequentes:")
    for a, f in top_acoes:
        print(f"    {a[:40]:40s}  freq={f}")


if __name__ == "__main__":
    main()
