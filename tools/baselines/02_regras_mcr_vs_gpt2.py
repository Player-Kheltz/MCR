"""02_regras_mcr_vs_gpt2.py — Classificacao de regras: MCR vs GPT-2.

Teste NOVO. Compara MCR vs GPT-2 124M em classificacao de sequencias
matematicas em 7 regras (PA, PG, FIB, COLL, QUAD, TRI, PRIMO).

MCR: decidir() com corpus matematico treinado (700 obs).
GPT-2: few-shot prompting (5 exemplos por regra).
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr, mcr_decidir

try:
    from transformers import pipeline
    TRANSFORMERS_OK = True
except ImportError:
    TRANSFORMERS_OK = False

# 17 sequencias zero-shot (mesmas do corpus_matematico.validar)
TESTES = [
    ("sequencia trinta trintaeum trintaedois", "PA"),
    ("progressao quarenta quarentaeum quarentaedois", "PA"),
    ("numeros vinteecinco trintaeseis quarentaenove", "QUAD"),
    ("padrao vinteeum vinteeoito trintaeseis", "TRI"),
    ("serie cinco seis dez quize", "TRI"),
    ("ordem treze dezessete dezenove", "PRIMO"),
    ("numeros quatro oito dezesseis", "PG"),
    ("padrao tres cinco oito treze", "FIB"),
    ("encadear cinco dezesseis oito quatro", "COLL"),
    ("sequencia doze seis tres dez", "COLL"),
    ("progressao seis doze vinteequatro", "PG"),
    ("padrao oito treze vinteeum", "FIB"),
    ("numeros nove dezesseis vinteecinco", "QUAD"),
    ("serie vinteeoito trintaeseis quarentaecinco", "TRI"),
    ("ordem onze treze dezessete", "PRIMO"),
    ("sequencia vinteequatro vinteecinco vinteeseis", "PA"),
    ("encadear dezenove cinquentaedois vinteseis", "COLL"),
]

REGRAS = ["PA", "PG", "FIB", "COLL", "QUAD", "TRI", "PRIMO"]

# Exemplos few-shot para GPT-2 (5 por regra)
EXEMPLOS_FEWSHOT = {
    "PA": ["dois quatro seis oito", "tres seis nove doze", "cinco dez quize vinte"],
    "PG": ["um dois quatro oito", "dois quatro oito dezesseis", "tres seis doze vinteequatro"],
    "FIB": ["um um dois tres cinco", "um dois tres cinco oito", "dois tres cinco oito treze"],
    "COLL": ["seis tres dezesseis oito quatro", "cinco dezesseis oito quatro dois", "doze seis tres dez cinco"],
    "QUAD": ["um quatro nove dezesseis", "dois quatro nove vinteecinco", "tres nove vinteseis quarentaeum"],
    "TRI": ["um tres seis dez", "dois tres seis dez", "tres seis dez quize"],
    "PRIMO": ["dois tres cinco sete", "tres cinco sete onze", "cinco sete onze treze"],
}


def construir_prompt_gpt2(sequencia_teste):
    """Constroi prompt few-shot para GPT-2."""
    prompt = "Classifique a sequencia numerica em uma regra: PA, PG, FIB, COLL, QUAD, TRI, PRIMO.\n\n"
    for regra in REGRAS:
        exemplos = EXEMPLOS_FEWSHOT.get(regra, [])
        for ex in exemplos[:2]:  # 2 exemplos por regra = 14 total
            prompt += f"{ex} -> {regra}\n"
    prompt += f"\n{sequencia_teste} ->"
    return prompt


def testar_mcr(c):
    """Testa MCR nas 17 sequencias."""
    acertos = 0
    detalhes = []
    for seq, esp in TESTES:
        acao, conf = mcr_decidir(c, seq)
        ac = acao == esp
        if ac:
            acertos += 1
        detalhes.append((seq, esp, acao, conf, ac))
    return acertos, len(TESTES), detalhes


def testar_gpt2():
    """Testa GPT-2 124M nas 17 sequencias com few-shot prompting."""
    print("  Carregando GPT-2 124M...")
    t0 = time.time()
    gerador = pipeline("text-generation", model="gpt2", max_new_tokens=10,
                       do_sample=False, device="cpu")
    dt_load = time.time() - t0
    print(f"  GPT-2 carregado em {dt_load:.1f}s")

    acertos = 0
    detalhes = []
    for seq, esp in TESTES:
        prompt = construir_prompt_gpt2(seq)
        try:
            saida = gerador(prompt, return_full_text=False)[0]["generated_text"].strip()
            # Extrai a regra da saida
            for r in REGRAS:
                if r in saida:
                    pred = r
                    break
            else:
                pred = saida[:10] if saida else "NONE"
        except Exception as e:
            pred = f"ERR:{e}"
            saida = ""

        ac = pred == esp
        if ac:
            acertos += 1
        detalhes.append((seq, esp, pred, saida[:30], ac))
    return acertos, len(TESTES), detalhes, dt_load


def main():
    print("=" * 70)
    print("  TESTE 02 — Regras matematicas: MCR vs GPT-2 (do zero)")
    print("=" * 70)

    print(f"\nDataset: {len(TESTES)} sequencias zero-shot, {len(REGRAS)} regras")

    # === MCR ===
    print("\n--- MCR ---")
    c, info = carregar_mcr(leve=True)
    ac_mcr, tot_mcr, det_mcr = testar_mcr(c)
    print(f"MCR: {ac_mcr}/{tot_mcr} = {ac_mcr/tot_mcr*100:.1f}%")
    for seq, esp, pred, conf, ac in det_mcr:
        st = "OK" if ac else "ERR"
        print(f"  {st} '{seq[:40]}' esp={esp} pred={pred} ({conf:.2f})")

    # === GPT-2 ===
    if not TRANSFORMERS_OK:
        print("\n[SKIP] transformers nao disponivel")
        resultado = {
            "teste": "regras_matematicas",
            "mcr": {"acertos": ac_mcr, "total": tot_mcr, "taxa": ac_mcr/tot_mcr},
            "gpt2": {"status": "SKIP", "motivo": "transformers indisponivel"},
        }
    else:
        print("\n--- GPT-2 124M (few-shot) ---")
        try:
            ac_gpt, tot_gpt, det_gpt, dt_load = testar_gpt2()
            print(f"GPT-2: {ac_gpt}/{tot_gpt} = {ac_gpt/tot_gpt*100:.1f}%")
            for seq, esp, pred, raw, ac in det_gpt:
                st = "OK" if ac else "ERR"
                print(f"  {st} '{seq[:40]}' esp={esp} pred={pred} (raw='{raw}')")
            resultado = {
                "teste": "regras_matematicas",
                "n_teste": len(TESTES),
                "mcr": {"acertos": ac_mcr, "total": tot_mcr, "taxa": ac_mcr/tot_mcr},
                "gpt2": {"acertos": ac_gpt, "total": tot_gpt, "taxa": ac_gpt/tot_gpt,
                         "tempo_load": dt_load},
            }
        except Exception as e:
            print(f"  ERRO: {e}")
            resultado = {
                "teste": "regras_matematicas",
                "mcr": {"acertos": ac_mcr, "total": tot_mcr, "taxa": ac_mcr/tot_mcr},
                "gpt2": {"status": "ERRO", "motivo": str(e)},
            }

    print("\n--- Comparacao ---")
    if "acertos" in resultado.get("gpt2", {}):
        tx_mcr = ac_mcr / tot_mcr
        tx_gpt = resultado["gpt2"]["acertos"] / resultado["gpt2"]["total"]
        print(f"MCR:   {tx_mcr*100:.1f}%")
        print(f"GPT-2: {tx_gpt*100:.1f}%")
        if tx_gpt > 0:
            print(f"MCR/GPT-2: {tx_mcr/tx_gpt:.2f}x")

    path_out = os.path.join(os.path.dirname(__file__), "resultados", "02_regras.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
