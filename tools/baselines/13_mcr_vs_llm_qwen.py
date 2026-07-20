"""13_mcr_vs_llm_qwen.py — MCR vs Qwen LLM (do zero).

Teste NOVO. Compara classificacao MCR vs LLM Qwen2.5-coder:7b via Ollama.

Pula se Ollama indisponivel (baseline nao disponivel).
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

try:
    import urllib.request
    req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    OLLAMA_OK = True
except Exception:
    OLLAMA_OK = False


def main():
    print("=" * 70)
    print("  TESTE 13 — MCR vs LLM Qwen (do zero)")
    print("=" * 70)

    if not OLLAMA_OK:
        print("\n[SKIP] Ollama indisponivel — baseline LLM nao pode ser testado.")
        print("Para rodar: instale Ollama e baixe qwen2.5-coder:7b")
        resultado = {
            "teste": "mcr_vs_llm_qwen",
            "status": "SKIP",
            "motivo": "Ollama indisponivel",
        }
        path_out = os.path.join(os.path.dirname(__file__), "resultados", "13_mcr_vs_llm_qwen.json")
        with open(path_out, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"Resultado salvo: {path_out}")
        return

    # Se Ollama disponivel, implementa teste completo
    from setup import carregar_mcr, mcr_decidir

    c, info = carregar_mcr(leve=True)

    # Dataset: 20 frases de teste (4 acoes x 5 frases)
    teste = [
        ("criar um npc ferreiro", "gerar_npc"),
        ("gerar personagem vendedor", "gerar_npc"),
        ("fazer npc comerciante", "gerar_npc"),
        ("criar guarda real", "gerar_npc"),
        ("gerar npc curandeiro", "gerar_npc"),
        ("criar um monstro dragao", "gerar_monstro"),
        ("gerar criatura hostil", "gerar_monstro"),
        ("fazer bestia selvagem", "gerar_monstro"),
        ("criar monstro chefe", "gerar_monstro"),
        ("gerar inimigo poderoso", "gerar_monstro"),
        ("o que e mcr", "responder"),
        ("explicar markov", "responder"),
        ("descrever cadeia markov", "responder"),
        ("como funciona entropia", "responder"),
        ("definir acoplamento", "responder"),
        ("criar sprite escudo", "gerar_sprite"),
        ("gerar imagem espada", "gerar_sprite"),
        ("fazer visual armadura", "gerar_sprite"),
        ("criar grafico personagem", "gerar_sprite"),
        ("gerar sprite montaria", "gerar_sprite"),
    ]

    # MCR
    print("\n--- MCR ---")
    ac_mcr = 0
    for texto, esp in teste:
        acao, conf = mcr_decidir(c, texto)
        ac = acao == esp
        if ac:
            ac_mcr += 1
        print(f"  {'OK' if ac else 'ERR'} '{texto}' esp={esp} pred={acao} ({conf:.2f})")

    # LLM Qwen
    print("\n--- LLM Qwen2.5-coder:7b ---")
    prompt_sistema = "Classifique a frase em uma acao: gerar_npc, gerar_monstro, responder, gerar_sprite. Responda SO a acao."

    ac_llm = 0
    for texto, esp in teste:
        try:
            data = json.dumps({
                "model": "qwen2.5-coder:7b",
                "prompt": f"{prompt_sistema}\nFrase: {texto}",
                "stream": False,
                "options": {"temperature": 0.0}
            }).encode()
            req = urllib.request.Request("http://localhost:11434/api/generate",
                                         data=data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=30)
            r = json.loads(resp.read())
            saida = r.get("response", "").strip().lower()
            # Extrai acao da saida
            acoes = ["gerar_npc", "gerar_monstro", "responder", "gerar_sprite"]
            acao = next((a for a in acoes if a in saida), saida.split()[0] if saida else "")
            ac = acao == esp
            if ac:
                ac_llm += 1
            print(f"  {'OK' if ac else 'ERR'} '{texto}' esp={esp} pred={acao} (raw='{saida[:30]}')")
        except Exception as e:
            print(f"  ERR '{texto}' erro={e}")

    print("\n--- Comparacao ---")
    print(f"MCR:  {ac_mcr}/{len(teste)} = {ac_mcr/len(teste)*100:.1f}%")
    print(f"LLM:  {ac_llm}/{len(teste)} = {ac_llm/len(teste)*100:.1f}%")

    resultado = {
        "teste": "mcr_vs_llm_qwen",
        "mcr": {"acertos": ac_mcr, "total": len(teste)},
        "llm_qwen": {"acertos": ac_llm, "total": len(teste)},
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "13_mcr_vs_llm_qwen.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
