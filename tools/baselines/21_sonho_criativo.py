"""21_sonho_criativo.py — O sonho como criatividade, nao classificacao.

O sonho nao e triunvirato. E CRIATIVIDADE. E lúdico. E vocabulario.
E onde o LLM ainda ganha — mas o MCR pode alcancar.

O sonho e o MCR gerando coisas novas a partir de si mesmo:
- Coerencia: o sonho faz sentido estrutural?
- Novidade: gera tokens/sequencias que nao existiam?
- Ludico: recombina de forma surpreendente?
- Vocabulario: expande o que o MCR conhece?

Comparar geracao MCR (sonho) vs GPT-2 em CRIATIVIDADE (nao classificacao).
"""
import sys, os, json, time, re
from collections import Counter
from math import log2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr

try:
    from transformers import pipeline
    TRANSFORMERS_OK = True
except ImportError:
    TRANSFORMERS_OK = False


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


def analisar_sonho(sonho, vocab_base):
    """Analisa um sonho sob 4 metricas de criatividade."""
    tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', sonho.lower())
    if not tokens:
        return None

    # 1. Coerencia: frases de 3+ tokens que fazem sentido
    # (aparecem no corpus base como sequencia conhecida)
    frases_3 = []
    for i in range(len(tokens) - 2):
        trinca = (tokens[i], tokens[i+1], tokens[i+2])
        frases_3.append(trinca)

    # 2. Novidade: tokens que NAO estao no vocabulario base
    tokens_novos = [t for t in tokens if t not in vocab_base]
    n_novos = len(tokens_novos)
    taxa_novidade = n_novos / len(tokens) if tokens else 0

    # 3. Ludico: diversidade de tokens unicos (H alta = lúdico)
    h = entropia_tokens(tokens)
    n_uniq = len(set(tokens))

    # 4. Vocabulario: tokens novos unicos (expansao de vocab)
    novos_uniq = set(tokens_novos)

    # 5. Recombinacao: trincas que sao ineditas (nao estao no n-grama)
    # (medir overlap com transicoes conhecidas)
    trans_conhecidas = 0
    trans_novas = 0
    for i in range(len(tokens) - 1):
        par = (tokens[i], tokens[i+1])
        # Verificar se esta transicao e conhecida
        # (simplificado: se ambos tokens estao no vocab)
        if tokens[i] in vocab_base and tokens[i+1] in vocab_base:
            trans_conhecidas += 1
        else:
            trans_novas += 1

    return {
        "n_tokens": len(tokens),
        "n_uniq": n_uniq,
        "entropia": round(h, 3),
        "n_novos": n_novos,
        "novos_uniq": sorted(novos_uniq)[:20],
        "taxa_novidade": round(taxa_novidade, 4),
        "trans_conhecidas": trans_conhecidas,
        "trans_novas": trans_novas,
        "taxa_recombinacao": round(trans_novas / max(1, trans_conhecidas + trans_novas), 4),
        "preview": sonho[:200],
    }


def gerar_gpt2(n_geracoes=5, max_tokens=50):
    """Gera texto com GPT-2 para comparar criatividade."""
    if not TRANSFORMERS_OK:
        return None

    print("  Carregando GPT-2...")
    gerador = pipeline("text-generation", model="gpt2",
                       max_new_tokens=max_tokens, do_sample=True,
                       temperature=0.8, top_k=50, device="cpu")

    geracoes = []
    prompts = [
        "The dream of numbers",
        "A sequence of thoughts",
        "In the mind of a machine",
        "Patterns in the void",
        "The echo of structure",
    ]

    for prompt in prompts[:n_geracoes]:
        saida = gerador(prompt, return_full_text=False, num_return_sequences=1)
        texto = saida[0]["generated_text"].strip()
        geracoes.append(texto)

    return geracoes


def main():
    print("=" * 70)
    print("  TESTE 21 — O Sonho como Criatividade (nao classificacao)")
    print("=" * 70)

    # === Carregar MCR ===
    print("\n[1] Carregando MCR...")
    c, info = carregar_mcr(leve=True)
    vocab_base = set(c._palavra_acao.keys())
    print(f"  {c._total} obs, {len(vocab_base)} pal vocab base")

    # === Gerar 10 sonhos ===
    print("\n[2] Gerando 10 sonhos (greedy, Pilar 1 puro)...")
    sonhador = SonhoMarkoviano(c)
    sonhos = []
    hashes = set()
    semente_atual = None

    for i in range(100):
        s = sonhador._serializar_estado() if semente_atual is None else semente_atual
        sonho = sonhador.sonhar(n_passos=50, semente=s, modo="greedy")
        h = sonho[:100]
        if h not in hashes:
            hashes.add(h)
            sonhos.append(sonho)
            if len(sonhos) >= 10:
                break
        tokens = sonhador._RE_TOKENS.findall(sonho.lower())
        if tokens:
            semente_atual = " ".join(tokens[-15:]) + " " + sonhador._serializar_estado(max_tokens=50)
        c.alimentar(sonho, "sonhar")

    print(f"  {len(sonhos)} sonhos unicos gerados")

    # === Analisar cada sonho ===
    print("\n[3] Analisando sonhos (criatividade)...")
    analises = []
    for i, sonho in enumerate(sonhos):
        a = analisar_sonho(sonho, vocab_base)
        if a:
            analises.append(a)
            print(f"\n  Sonho #{i+1}:")
            print(f"    Tokens: {a['n_tokens']}, Unicos: {a['n_uniq']}, H: {a['entropia']}")
            print(f"    Novos: {a['n_novos']} ({a['taxa_novidade']*100:.1f}%), "
                  f"Novos unicos: {len(a['novos_uniq'])}")
            print(f"    Trans conhecidas: {a['trans_conhecidas']}, "
                  f"Trans novas: {a['trans_novas']} ({a['taxa_recombinacao']*100:.1f}%)")
            if a['novos_uniq']:
                print(f"    Vocabulario novo: {a['novos_uniq'][:10]}")
            prev = a["preview"][:120]
            print("    Preview: " + repr(prev))

    # === Metricas agregadas ===
    print("\n[4] Metricas agregadas (media dos 10 sonhos):")
    if analises:
        med_h = sum(a["entropia"] for a in analises) / len(analises)
        med_novos = sum(a["n_novos"] for a in analises) / len(analises)
        med_recomb = sum(a["taxa_recombinacao"] for a in analises) / len(analises)
        med_uniq = sum(a["n_uniq"] for a in analises) / len(analises)
        todos_novos = set()
        for a in analises:
            todos_novos.update(a["novos_uniq"])
        print(f"  Entropia media: {med_h:.3f}")
        print(f"  Tokens novos medios: {med_novos:.1f}")
        print(f"  Taxa recombinação media: {med_recomb*100:.1f}%")
        print(f"  Tokens unicos medios: {med_uniq:.1f}")
        print(f"  Vocabulario novo total: {len(todos_novos)} tokens")
        print(f"  Amostra vocab novo: {sorted(todos_novos)[:20]}")

    # === Comparar com GPT-2 ===
    print("\n[5] Comparando com GPT-2 (geracao criativa)...")
    geracoes_gpt = gerar_gpt2(n_geracoes=5, max_tokens=50)

    if geracoes_gpt:
        print("\n  Geracoes GPT-2:")
        # Vocabulario base para GPT-2 = ingles
        vocab_en = set()
        for a in analises:
            vocab_en.update(a["novos_uniq"])

        gpt_analises = []
        for i, texto in enumerate(geracoes_gpt):
            tokens = re.findall(r'[a-zA-Z]{2,}', texto.lower())
            if tokens:
                h = entropia_tokens(tokens)
                n_uniq = len(set(tokens))
                print(f"  GPT-2 #{i+1}: {len(tokens)} tokens, H={h:.3f}, "
                      f"unicos={n_uniq}")
                print(f"    '{texto[:120]}'")
                gpt_analises.append({
                    "n_tokens": len(tokens),
                    "n_uniq": n_uniq,
                    "entropia": h,
                    "preview": texto[:200],
                })

        if gpt_analises:
            med_h_gpt = sum(a["entropia"] for a in gpt_analises) / len(gpt_analises)
            med_uniq_gpt = sum(a["n_uniq"] for a in gpt_analises) / len(gpt_analises)
            print(f"\n  Comparacao MCR vs GPT-2 (geracao criativa):")
            print(f"    {'Metrica':<25s} {'MCR (sonho)':>15s} {'GPT-2':>15s}")
            print(f"    {'-'*55}")
            print(f"    {'Entropia media':<25s} {med_h:>15.3f} {med_h_gpt:>15.3f}")
            print(f"    {'Tokens unicos medios':<25s} {med_uniq:>15.1f} {med_uniq_gpt:>15.1f}")
            print(f"    {'Vocab novo gerado':<25s} {len(todos_novos):>15d} {'?':>15s}")
    else:
        print("  [SKIP] transformers indisponivel")

    # === Salvar ===
    resultado = {
        "teste": "sonho_criativo",
        "mcr": {"obs": c._total, "vocab_base": len(vocab_base)},
        "n_sonhos": len(sonhos),
        "analises": analises,
        "metricas_agregadas": {
            "entropia_media": med_h if analises else 0,
            "tokens_novos_medios": med_novos if analises else 0,
            "taxa_recombinacao_media": med_recomb if analises else 0,
            "vocab_novo_total": len(todos_novos) if analises else 0,
        },
        "gpt2": [{"preview": g[:200]} for g in geracoes_gpt] if geracoes_gpt else None,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "21_sonho_criativo.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
