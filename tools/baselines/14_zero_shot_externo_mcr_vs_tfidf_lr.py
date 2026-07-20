"""14_zero_shot_externo_mcr_vs_tfidf_lr.py — Zero-shot externo do zero.

Teste NOVO. Compara MCR vs TF-IDF + LogisticRegression em classificacao
de frases AFORA do dominio de treino.

Protocolo:
- Treino: dataset_500 (562 obs, 12 acoes)
- Teste: 40 frases NOVAS, AFORA do dataset, em dominios nao treinados
- MCR: decidir() sem ver as frases de teste
- TF-IDF+LR: fit() no treino, predict() no teste
"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr, mcr_decidir

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False


# 40 frases novas, fora do dataset_500, em dominios parcialmente novos
TESTE_ZERO_SHOT = [
    # gerar_npc — mas com vocabulario novo
    ("criar alquimista pocoes", "gerar_npc"),
    ("fazer arqueiro floresta", "gerar_npc"),
    ("gerar sage conselheiro", "gerar_npc"),
    ("construir nobre palacio", "gerar_npc"),
    # gerar_monstro — vocabulario novo
    ("criar hidra venenosa", "gerar_monstro"),
    ("fazer golem pedra", "gerar_monstro"),
    ("gerar fenix fogo", "gerar_monstro"),
    ("construir quimera mutante", "gerar_monstro"),
    # responder — perguntas novas
    ("qual diferenca markov", "responder"),
    ("porque entropia importa", "responder"),
    ("quando usar acoplamento", "responder"),
    ("onde aplicar cognicao", "responder"),
    # gerar_sprite — vocabulario novo
    ("criar textura agua", "gerar_sprite"),
    ("fazer icone magia", "gerar_sprite"),
    ("gerar padrao escudo", "gerar_sprite"),
    ("construir imagem mapa", "gerar_sprite"),
    # gerar_quest — dominio pouco treinado
    ("criar missao resgate", "gerar_quest"),
    ("fazer tarefa exploracao", "gerar_quest"),
    ("gerar desafio puzzle", "gerar_quest"),
    ("construir jornada heroi", "gerar_quest"),
    # analisar — dominio pouco treinado
    ("examinar codigo python", "analisar"),
    ("estudar estrutura dados", "analisar"),
    ("avaliar performance sistema", "analisar"),
    ("inspecionar log erro", "analisar"),
    # buscar — dominio pouco treinado
    ("encontrar arquivos config", "buscar"),
    ("localizar funcao main", "buscar"),
    ("procurar definicao classe", "buscar"),
    ("descobrir pasta assets", "buscar"),
    # validar — dominio pouco treinado
    ("confirmar sintaxe lua", "validar"),
    ("verificar tipos dados", "validar"),
    ("checar regras estilo", "validar"),
    ("testar validacao schema", "validar"),
    # conectar — dominio pouco treinado
    ("ligar modulo npc", "conectar"),
    ("unir sistema combate", "conectar"),
    ("integrar api externa", "conectar"),
    ("relacionar entidades jogo", "conectar"),
    # aprender — dominio pouco treinado
    ("absorver nova informacao", "aprender"),
    ("memorizar padrao codigo", "aprender"),
    ("registrar lição aprendida", "aprender"),
    ("estudar exemplo concreto", "aprender"),
]


def main():
    print("=" * 70)
    print("  TESTE 14 — Zero-shot externo: MCR vs TF-IDF+LR (do zero)")
    print("=" * 70)

    print(f"\nDataset teste: {len(TESTE_ZERO_SHOT)} frases novas (fora do treino)")

    # Carrega dataset_500 para treino
    caminho_ds = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "tests", "experimento_rigoroso", "dataset_500.json")
    with open(caminho_ds, "r", encoding="utf-8") as f:
        ds = json.load(f)
    treino = [(d["input"], d["expected_action"]) for d in ds]
    print(f"Dataset treino: {len(treino)} frases (dataset_500)")

    # === MCR ===
    print("\n--- MCR ---")
    c, info = carregar_mcr(leve=True)
    ac_mcr = 0
    for texto, esp in TESTE_ZERO_SHOT:
        acao, conf = mcr_decidir(c, texto)
        ac = acao == esp
        if ac:
            ac_mcr += 1
        st = "OK" if ac else "ERR"
        print(f"  {st} '{texto}' esp={esp} pred={acao} ({conf:.2f})")
    print(f"MCR: {ac_mcr}/{len(TESTE_ZERO_SHOT)} = {ac_mcr/len(TESTE_ZERO_SHOT)*100:.1f}%")

    # === TF-IDF + LogisticRegression ===
    if not SKLEARN_OK:
        print("\n[SKIP] sklearn nao disponivel")
        resultado = {
            "teste": "zero_shot_externo",
            "mcr": {"acertos": ac_mcr, "total": len(TESTE_ZERO_SHOT)},
            "tfidf_lr": {"status": "SKIP", "motivo": "sklearn indisponivel"},
        }
    else:
        print("\n--- TF-IDF + LogisticRegression ---")
        X_treino = [t for t, _ in treino]
        y_treino = [a for _, a in treino]
        X_teste = [t for t, _ in TESTE_ZERO_SHOT]
        y_teste = [a for _, a in TESTE_ZERO_SHOT]

        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ("lr", LogisticRegression(max_iter=1000, random_state=42)),
        ])
        pipe.fit(X_treino, y_treino)
        preds = pipe.predict(X_teste)

        ac_lr = 0
        for (texto, esp), pred in zip(TESTE_ZERO_SHOT, preds):
            ac = pred == esp
            if ac:
                ac_lr += 1
            st = "OK" if ac else "ERR"
            print(f"  {st} '{texto}' esp={esp} pred={pred}")
        print(f"TF-IDF+LR: {ac_lr}/{len(TESTE_ZERO_SHOT)} = {ac_lr/len(TESTE_ZERO_SHOT)*100:.1f}%")

        resultado = {
            "teste": "zero_shot_externo",
            "n_treino": len(treino),
            "n_teste": len(TESTE_ZERO_SHOT),
            "mcr": {"acertos": ac_mcr, "total": len(TESTE_ZERO_SHOT),
                    "taxa": ac_mcr / len(TESTE_ZERO_SHOT)},
            "tfidf_lr": {"acertos": ac_lr, "total": len(TESTE_ZERO_SHOT),
                         "taxa": ac_lr / len(TESTE_ZERO_SHOT)},
        }

    print("\n--- Comparacao ---")
    if "tfidf_lr" in resultado and "acertos" in resultado["tfidf_lr"]:
        tx_mcr = ac_mcr / len(TESTE_ZERO_SHOT)
        tx_lr = ac_lr / len(TESTE_ZERO_SHOT)
        if tx_lr > 0:
            ratio = tx_mcr / tx_lr
        else:
            ratio = float('inf')
        print(f"MCR:       {tx_mcr*100:.1f}%")
        print(f"TF-IDF+LR: {tx_lr*100:.1f}%")
        print(f"MCR/LR:    {ratio:.2f}x")

    path_out = os.path.join(os.path.dirname(__file__), "resultados", "14_zero_shot_externo.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
