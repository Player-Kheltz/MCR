"""05_auto_conhec_mcr_vs_tfidf.py — Auto-conhecimento: MCR vs TF-IDF.

Teste NOVO. Compara MCR decidir() vs TF-IDF+cosine em auto-consulta
discriminativa (MCR se observa: "o que sei sobre X?").

Replica o experimento do lift: MCR aprende acoes e consulta a si mesmo.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr, mcr_decidir

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

import numpy as np

# Acoes do MCR (do dataset_500 + matematico)
ACOES = [
    ("criar npc ferreiro forjador armas", "gerar_npc"),
    ("gerar monstro dragao criatura hostil", "gerar_monstro"),
    ("gerar sprite imagem visual grafico", "gerar_sprite"),
    ("criar quest missao tarefa aventura", "gerar_quest"),
    ("o que e markov cadeia probabilistica", "responder"),
    ("explicar entropia incerteza medida", "responder"),
    ("definir acoplamento conexao niveis", "responder"),
    ("buscar arquivo procurar localizar", "buscar"),
    ("analisar codigo estudar examinar", "analisar"),
    ("validar sintaxe checar confirmar", "validar"),
    ("conectar ligar unir integrar", "conectar"),
    ("aprender memorizar absorver registrar", "aprender"),
    ("planejar estrategia planejamento plano", "planejar"),
    ("editar modificar alterar mudar", "editar"),
    ("sequencia dois quatro seis oito", "PA"),
    ("progressao um dois quatro oito", "PG"),
    ("padrao um um dois tres cinco", "FIB"),
    ("encadear cinco dezesseis oito quatro", "COLL"),
    ("numeros um quatro nove dezesseis", "QUAD"),
    ("serie um tres seis dez", "TRI"),
    ("ordem dois tres cinco sete", "PRIMO"),
]

# 10 consultas abstratas (o que o MCR "sabe" sobre X?)
CONSULTAS = [
    ("criar personagem", "gerar_npc"),
    ("fazer inimigo", "gerar_monstro"),
    ("desenhar visual", "gerar_sprite"),
    ("criar aventura", "gerar_quest"),
    ("explicar conceito", "responder"),
    ("encontrar arquivo", "buscar"),
    ("estudar codigo", "analisar"),
    ("verificar correto", "validar"),
    ("ligar modulos", "conectar"),
    ("sequencia numerica crescente", "PA"),
    ("serie dobra cada passo", "PG"),
    ("padrao fibonacci soma", "FIB"),
    ("sequencia Collatz impar", "COLL"),
    ("numeros quadrados perfeitos", "QUAD"),
    ("serie triangular somando", "TRI"),
    ("numeros primos sequencia", "PRIMO"),
]


def testar_mcr(c):
    """MCR: decidir() para cada consulta."""
    acertos = 0
    detalhes = []
    for consulta, esperado in CONSULTAS:
        acao, conf = mcr_decidir(c, consulta)
        ac = acao == esperado
        if ac:
            acertos += 1
        detalhes.append((consulta, esperado, acao, conf, ac))
    return acertos, len(CONSULTAS), detalhes


def testar_tfidf(c):
    """TF-IDF: cosine similarity entre consulta e descricoes de acoes."""
    if not SKLEARN_OK:
        return None, None, None

    # Corpus: descricoes das acoes
    corpus = [desc for desc, _ in ACOES]
    labels = [acao for _, acao in ACOES]

    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vec.fit_transform(corpus)

    # Para cada consulta, encontra a acao mais similar
    acertos = 0
    detalhes = []
    for consulta, esperado in CONSULTAS:
        q_vec = vec.transform([consulta])
        sims = cosine_similarity(q_vec, X)[0]
        best_idx = sims.argmax()
        pred = labels[best_idx]
        ac = pred == esperado
        if ac:
            acertos += 1
        detalhes.append((consulta, esperado, pred, sims[best_idx], ac))
    return acertos, len(CONSULTAS), detalhes


def testar_mcr_lift(c):
    """MCR com lift: P(feature|acao)/P(acao) em vez de freq bruta."""
    acertos = 0
    detalhes = []
    for consulta, esperado in CONSULTAS:
        # Calcular lift para cada acao
        dist = c._dist_features(consulta)
        if not dist:
            acao = "NONE"
            conf = 0.0
        else:
            # Lift = P(feature|acao) / P(acao) — normaliza por freq global
            freq_total = sum(c._freq_acao.values()) or 1
            lift_scores = {}
            for a, score in dist.items():
                p_acao = c._freq_acao.get(a, 0) / freq_total
                lift_scores[a] = score / (p_acao + 1e-10) if p_acao > 0 else 0
            acao = max(lift_scores.items(), key=lambda x: x[1])[0]
            conf = lift_scores[acao]

        ac = acao == esperado
        if ac:
            acertos += 1
        detalhes.append((consulta, esperado, acao, conf, ac))
    return acertos, len(CONSULTAS), detalhes


def main():
    print("=" * 70)
    print("  TESTE 05 — Auto-conhecimento: MCR vs TF-IDF (do zero)")
    print("=" * 70)

    print(f"\nAcoes: {len(ACOES)} descricoes")
    print(f"Consultas: {len(CONSULTAS)} auto-consultas")

    c, info = carregar_mcr(leve=True)
    # Alimenta acoes extras
    for desc, acao in ACOES:
        c.alimentar(desc, acao)

    print(f"\nMCR: {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # === MCR raw decidir() ===
    print("\n--- MCR (raw decidir) ---")
    ac_mcr, tot_mcr, det_mcr = testar_mcr(c)
    print(f"MCR raw: {ac_mcr}/{tot_mcr} = {ac_mcr/tot_mcr*100:.1f}%")
    for consulta, esp, pred, conf, ac in det_mcr:
        st = "OK" if ac else "ERR"
        print(f"  {st} '{consulta}' esp={esp} pred={pred} ({conf:.2f})")

    # === MCR com lift ===
    print("\n--- MCR (lift) ---")
    ac_lift, tot_lift, det_lift = testar_mcr_lift(c)
    print(f"MCR lift: {ac_lift}/{tot_lift} = {ac_lift/tot_lift*100:.1f}%")
    for consulta, esp, pred, conf, ac in det_lift:
        st = "OK" if ac else "ERR"
        print(f"  {st} '{consulta}' esp={esp} pred={pred} ({conf:.2f})")

    # === TF-IDF ===
    print("\n--- TF-IDF + cosine ---")
    if SKLEARN_OK:
        ac_tf, tot_tf, det_tf = testar_tfidf(c)
        print(f"TF-IDF: {ac_tf}/{tot_tf} = {ac_tf/tot_tf*100:.1f}%")
        for consulta, esp, pred, sim, ac in det_tf:
            st = "OK" if ac else "ERR"
            print(f"  {st} '{consulta}' esp={esp} pred={pred} ({sim:.3f})")
    else:
        ac_tf = None
        print("[SKIP] sklearn indisponivel")

    # === Comparacao ===
    print("\n--- Comparacao ---")
    tx_mcr = ac_mcr / tot_mcr if tot_mcr else 0
    tx_lift = ac_lift / tot_lift if tot_lift else 0
    print(f"MCR raw:  {tx_mcr*100:.1f}%")
    print(f"MCR lift: {tx_lift*100:.1f}%")
    if ac_tf is not None:
        tx_tf = ac_tf / tot_tf
        print(f"TF-IDF:   {tx_tf*100:.1f}%")
        if tx_tf > 0:
            print(f"lift/TF-IDF: {tx_lift/tx_tf:.2f}x")
            print(f"raw/TF-IDF:  {tx_mcr/tx_tf:.2f}x")

    resultado = {
        "teste": "auto_conhecimento",
        "n_acoes": len(ACOES),
        "n_consultas": len(CONSULTAS),
        "mcr_raw": {"acertos": ac_mcr, "total": tot_mcr, "taxa": tx_mcr},
        "mcr_lift": {"acertos": ac_lift, "total": tot_lift, "taxa": tx_lift},
    }
    if ac_tf is not None:
        resultado["tfidf"] = {"acertos": ac_tf, "total": tot_tf, "taxa": ac_tf/tot_tf}

    path_out = os.path.join(os.path.dirname(__file__), "resultados", "05_auto_conhecimento.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
