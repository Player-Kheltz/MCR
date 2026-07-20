"""15_hiperfoco_gutenberg.py — Testar se Gutenberg balanceado preserva discriminacao.

Hipotese (Kheltz): Gutenberg desbalanceado (3:1) dilui por hiperfoco.
Balanceado (1:1), a entropia (Pilar 2) descobre as fronteiras naturais.

Setup:
- Motor A (controle): corpus atual 134K (sem Gutenberg)
- Motor B (experimental): Motor A + 116K Gutenberg (balanceado ~1:1)

Testes: sinonimia (01), zero-shot (14), estilo (03)
Critério: Motor B >= Motor A em >=2/3 testes = Gutenberg balanceado ajuda.
"""
import sys, os, json, time, re, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from setup import mcr_decidir, mcr_nmi, carregar_mcr

# Reutiliza datasets dos testes 01, 03, 14
from importlib import import_module

DIR_GUTENBERG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "corpus_expa", "gutenberg")

# Pares de sinonimia (do teste 01)
PARES_SINONIMOS = [
    ("amor", "love", 1), ("casa", "house", 1), ("agua", "water", 1),
    ("luz", "light", 1), ("fogo", "fire", 1), ("cachorro", "dog", 1),
    ("gato", "cat", 1), ("sol", "sun", 1), ("lua", "moon", 1),
    ("estrela", "star", 1), ("livro", "book", 1), ("pao", "bread", 1),
    ("cadeira", "chair", 1), ("mesa", "table", 1), ("porta", "door", 1),
    ("janela", "window", 1), ("arvore", "tree", 1), ("flor", "flower", 1),
    ("rio", "river", 1), ("montanha", "mountain", 1),
]
PARES_NAO_REL = [
    ("cachorro", "mesa", 0), ("fogo", "numero", 0), ("peixe", "musica", 0),
    ("amor", "calculo", 0), ("casa", "raiz", 0), ("agua", "ponte", 0),
    ("luz", "tempestade", 0), ("gato", "algoritmo", 0), ("sol", "intervalo", 0),
    ("lua", "metal", 0), ("estrela", "lagar", 0), ("livro", "serpente", 0),
    ("pao", "tese", 0), ("cadeira", "nuvem", 0), ("mesa", "sopro", 0),
    ("porta", "silogismo", 0), ("janela", "esfera", 0),
    ("arvore", "codigo", 0), ("flor", "ponto", 0), ("rio", "rotulo", 0),
]
TODOS_PARES = PARES_SINONIMOS + PARES_NAO_REL

# Zero-shot (do teste 14)
TESTE_ZERO_SHOT = [
    ("criar alquimista pocoes", "gerar_npc"), ("fazer arqueiro floresta", "gerar_npc"),
    ("gerar sage conselheiro", "gerar_npc"), ("construir nobre palacio", "gerar_npc"),
    ("criar hidra venenosa", "gerar_monstro"), ("fazer golem pedra", "gerar_monstro"),
    ("gerar fenix fogo", "gerar_monstro"), ("construir quimera mutante", "gerar_monstro"),
    ("qual diferenca markov", "responder"), ("porque entropia importa", "responder"),
    ("quando usar acoplamento", "responder"), ("onde aplicar cognicao", "responder"),
    ("criar textura agua", "gerar_sprite"), ("fazer icone magia", "gerar_sprite"),
    ("gerar padrao escudo", "gerar_sprite"), ("construir imagem mapa", "gerar_sprite"),
    ("criar missao resgate", "gerar_quest"), ("fazer tarefa exploracao", "gerar_quest"),
    ("gerar desafio puzzle", "gerar_quest"), ("construir jornada heroi", "gerar_quest"),
    ("examinar codigo python", "analisar"), ("estudar estrutura dados", "analisar"),
    ("avaliar performance sistema", "analisar"), ("inspecionar log erro", "analisar"),
    ("encontrar arquivos config", "buscar"), ("localizar funcao main", "buscar"),
    ("procurar definicao classe", "buscar"), ("descobrir pasta assets", "buscar"),
    ("confirmar sintaxe lua", "validar"), ("verificar tipos dados", "validar"),
    ("checar regras estilo", "validar"), ("testar validacao schema", "validar"),
    ("ligar modulo npc", "conectar"), ("unir sistema combate", "conectar"),
    ("integrar api externa", "conectar"), ("relacionar entidades jogo", "conectar"),
    ("absorver nova informacao", "aprender"), ("memorizar padrao codigo", "aprender"),
    ("registrar licao aprendida", "aprender"), ("estudar exemplo concreto", "aprender"),
]

# Estilo (do teste 03)
TEXTOS_ESTILO = [
    ("O experimento demonstrou que a reacao quimica ocorre em condicoes controladas.", "cientifico"),
    ("Os resultados indicam uma correlacao positiva entre as variaveis estudadas.", "cientifico"),
    ("A analise estatistica revelou diferencas significativas entre os grupos.", "cientifico"),
    ("Conclui-se que a hipotese nula pode ser rejeitada com nivel de 95 por cento.", "cientifico"),
    ("Os dados coletados sugerem que o fenomeno observado segue uma distribuicao normal.", "cientifico"),
    ("A lua prateada dancava sobre as aguas tranquilas do rio enquanto a brisa sussurrava.", "literario"),
    ("Ela caminhava lentamente pela floresta sentindo cada folha sob seus pes descalcos.", "literario"),
    ("O sol se punha no horizonte pintando o ceu com tons de laranja e purpura.", "literario"),
    ("No silencio da noite as estrelas contavam historias de amores perdidos.", "literario"),
    ("O vento carregava consigo o perfume das flores silvestres trazendo memorias.", "literario"),
    ("A reuniao ocorreu ontem no palacio do governo com autoridades locais.", "jornalistico"),
    ("Segundo fontes oficiais o projeto de lei sera votado na proxima sessao.", "jornalistico"),
    ("O balanco economico do trimestre aponta crescimento de tres por cento.", "jornalistico"),
    ("Pesquisa realizada pelo instituto mostra que a maioria apoia a nova politica.", "jornalistico"),
    ("O acordo firmado entre os paises prevê investimentos conjuntos em tecnologia.", "jornalistico"),
    ("Voce veio perguntou ele surpreso nao esperava que aparecesse tao cedo.", "dialogo"),
    ("Nao sei o que dizer respondeu ela olhando para o chao tudo mudou.", "dialogo"),
    ("Que tal sairmos para jantar sugeriu ele conheco um lugar excelente.", "dialogo"),
    ("Voce esta brincando exclamou o amigo isso e impossivel de acreditar.", "dialogo"),
    ("Obrigada pela ajuda disse ela sorrindo nao teria conseguido sem voce.", "dialogo"),
    ("Para instalar o pacote execute o comando pip install seguido do nome do modulo.", "tecnico"),
    ("A funcao recebe dois parametros inteiros como entrada e retorna um valor booleano.", "tecnico"),
    ("Configure o arquivo JSON com as chaves nome versao e dependencias antes de executar.", "tecnico"),
    ("O algoritmo percorre a lista verificando cada elemento e adiciona os validos.", "tecnico"),
    ("Importe a biblioteca numpy no inicio do arquivo para usar algebra linear.", "tecnico"),
]


def tokenizar(texto):
    return re.findall(r'[a-zà-ÿ]{2,}', texto.lower())


def frases_de_gutenberg(dir_gut, max_frases=130000):
    """Extrai frases dos arquivos Gutenberg. Limpa cabecalhos/rodapes."""
    frases = []
    for arq in sorted(os.listdir(dir_gut)):
        if not arq.endswith(".txt"):
            continue
        path = os.path.join(dir_gut, arq)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            texto = f.read()
        # Remove cabecalhos/rodapes Project Gutenberg
        partes = texto.split("***")
        if len(partes) >= 3:
            texto = partes[1] if len(partes) > 1 else texto
        # Divide por pontuacao E quebras de linha (paragrafos)
        raw = re.split(r'[.!?]+\s+|\n+', texto)
        for f in raw:
            f = f.strip().lower()
            palavras = tokenizar(f)
            if len(palavras) >= 4:
                frases.append(" ".join(palavras[:60]))
            if len(frases) >= max_frases:
                return frases
    return frases


def alimentar_corpus_base(c):
    """Alimenta o corpus base (matematico + dataset_500)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
    from corpus_matematico import alimentar_corpus_matematico
    alimentar_corpus_matematico(c)
    caminho_ds = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "tests", "experimento_rigoroso", "dataset_500.json")
    if os.path.exists(caminho_ds):
        with open(caminho_ds, "r", encoding="utf-8") as f:
            ds = json.load(f)
        pares = [(d["input"], d["expected_action"]) for d in ds]
        c.alimentar_lote(pares)


def alimentar_wikipedia(c, max_obs=50000):
    """Alimenta Wikipedia do JSON pre-treinado se disponivel, senao do cache."""
    wiki_json = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                             "cache", "coupling_wiki_teste.json")
    if os.path.exists(wiki_json):
        # Salva estado atual, carrega wiki, depois restaura
        # Nao pode — load substitui tudo. Em vez disso, carrega wiki primeiro
        # e depois alimenta corpus base por cima
        ok = c.load(wiki_json)
        if ok:
            return c._total
    return 0


def testar_sinonimia(c):
    """Teste 01: sinonimia cross-idioma. Retorna AUC."""
    scores = []
    labels = []
    for a, b, label in TODOS_PARES:
        s = mcr_nmi(c, a, b)
        scores.append(s)
        labels.append(label)
    return calcular_roc_auc(scores, labels)


def calcular_roc_auc(scores, labels):
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ordenado = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    auc = 0.0
    for s, l in ordenado:
        if l == 1:
            tp += 1
        else:
            auc += tp
    return auc / (n_pos * n_neg)


def testar_zero_shot(c):
    """Teste 14: zero-shot externo. Retorna acuracia."""
    acertos = 0
    for texto, esp in TESTE_ZERO_SHOT:
        acao, conf = mcr_decidir(c, texto)
        if acao == esp:
            acertos += 1
    return acertos, len(TESTE_ZERO_SHOT)


def testar_estilo(c):
    """Teste 03: clusterizacao de estilo. Retorna ARI."""
    from sklearn.metrics import adjusted_rand_score
    # Treina
    for texto, estilo in TEXTOS_ESTILO:
        c.alimentar(texto, estilo)
    # Testa (mesmos textos — split real seria melhor mas mantemos comparavel)
    labels_true = [estilo for _, estilo in TEXTOS_ESTILO]
    preds = []
    for texto, estilo in TEXTOS_ESTILO:
        acao, conf = mcr_decidir(c, texto)
        preds.append(acao)
    return adjusted_rand_score(labels_true, preds)


def main():
    print("=" * 70)
    print("  TESTE 15 — Hiperfoco Gutenberg: Balanceado vs Sem Gutenberg")
    print("=" * 70)

    # Carrega frases Gutenberg — limita a ~38K para proporcao 1:1 com corpus base
    print("\n[1] Carregando frases Gutenberg...")
    t0 = time.time()
    todas_gut = frases_de_gutenberg(DIR_GUTENBERG, max_frases=130000)
    # Limita a ~38K para proporcao 1:1 com Wikipedia+corpus base (38646)
    random.seed(42)
    random.shuffle(todas_gut)
    frases_gut = todas_gut[:38000]
    dt = time.time() - t0
    print(f"  {len(todas_gut)} frases extraidas, {len(frases_gut)} selecionadas (1:1) em {dt:.1f}s")

    # === Motor A (controle) ===
    print("\n[2] Motor A (controle: Wikipedia + corpus base, sem Gutenberg)...")
    cA = MCRCoupling()
    t0 = time.time()
    # Wikipedia primeiro (via JSON pre-treinado)
    n_wiki = alimentar_wikipedia(cA)
    # Corpus base por cima
    alimentar_corpus_base(cA)
    dt_A = time.time() - t0
    print(f"  {cA._total} obs, {len(cA._palavra_acao)} pal, {len(cA._freq_acao)} acoes em {dt_A:.1f}s")
    print(f"  Wikipedia: {n_wiki} obs")

    print("\n  Testando Motor A...")
    t0 = time.time()
    auc_A = testar_sinonimia(cA)
    ac_zs_A, tot_zs_A = testar_zero_shot(cA)
    ari_A = testar_estilo(cA)
    dt_test_A = time.time() - t0
    print(f"  Sinonimia AUC: {auc_A:.3f}")
    print(f"  Zero-shot: {ac_zs_A}/{tot_zs_A} = {ac_zs_A/tot_zs_A*100:.1f}%")
    print(f"  Estilo ARI: {ari_A:.3f}")

    # === Motor B (experimental: + Gutenberg balanceado) ===
    print("\n[3] Motor B (experimental: Wikipedia + corpus base + Gutenberg balanceado)...")
    cB = MCRCoupling()
    t0 = time.time()
    # Wikipedia primeiro (mesmo JSON)
    n_wiki_B = alimentar_wikipedia(cB)
    # Corpus base por cima
    alimentar_corpus_base(cB)
    # Gutenberg balanceado
    pares_gut = [(fr, "gutenberg") for fr in frases_gut]
    cB.alimentar_lote(pares_gut)
    dt_B = time.time() - t0
    print(f"  {cB._total} obs, {len(cB._palavra_acao)} pal, {len(cB._freq_acao)} acoes em {dt_B:.1f}s")
    print(f"  Wikipedia: {n_wiki_B} obs, Gutenberg: {len(frases_gut)} frases")

    print("\n  Testando Motor B...")
    t0 = time.time()
    auc_B = testar_sinonimia(cB)
    ac_zs_B, tot_zs_B = testar_zero_shot(cB)
    ari_B = testar_estilo(cB)
    dt_test_B = time.time() - t0
    print(f"  Sinonimia AUC: {auc_B:.3f}")
    print(f"  Zero-shot: {ac_zs_B}/{tot_zs_B} = {ac_zs_B/tot_zs_B*100:.1f}%")
    print(f"  Estilo ARI: {ari_B:.3f}")

    # === Comparacao ===
    print("\n" + "=" * 70)
    print("  COMPARACAO: Motor A (sem Gutenberg) vs Motor B (com Gutenberg balanceado)")
    print("=" * 70)
    print(f"{'Teste':<25s} {'Motor A':>10s} {'Motor B':>10s} {'Delta':>10s} {'Vencedor':>12s}")
    print("-" * 70)

    vencedores = []
    # Sinonimia
    d_auc = auc_B - auc_A
    v = "B" if d_auc > 0 else ("A" if d_auc < 0 else "empate")
    vencedores.append(v == "B")
    print(f"{'Sinonimia AUC':<25s} {auc_A:>10.3f} {auc_B:>10.3f} {d_auc:>+10.3f} {v:>12s}")

    # Zero-shot
    tx_A = ac_zs_A / tot_zs_A
    tx_B = ac_zs_B / tot_zs_B
    d_zs = tx_B - tx_A
    v = "B" if d_zs > 0 else ("A" if d_zs < 0 else "empate")
    vencedores.append(v == "B")
    print(f"{'Zero-shot %':<25s} {tx_A*100:>9.1f}% {tx_B*100:>9.1f}% {d_zs*100:>+9.1f}% {v:>12s}")

    # Estilo
    d_ari = ari_B - ari_A
    v = "B" if d_ari > 0 else ("A" if d_ari < 0 else "empate")
    vencedores.append(v == "B")
    print(f"{'Estilo ARI':<25s} {ari_A:>10.3f} {ari_B:>10.3f} {d_ari:>+10.3f} {v:>12s}")

    print("-" * 70)
    n_B = sum(vencedores)
    print(f"\nVencedores B: {n_B}/3")
    if n_B >= 2:
        print("VEREDITO: Gutenberg balanceado AJUDA (hiperfoco confirmado)")
    else:
        print("VEREDITO: Gutenberg balanceado NAO ajuda (ou hiperfoco nao e a causa)")

    # Salva resultado
    resultado = {
        "teste": "hiperfoco_gutenberg",
        "hipotese": "Gutenberg balanceado 1:1 preserva discriminacao",
        "motor_A": {
            "descricao": "controle sem Gutenberg",
            "obs": cA._total, "vocab": len(cA._palavra_acao), "acoes": len(cA._freq_acao),
            "sinonimia_auc": auc_A, "zero_shot": ac_zs_A/tot_zs_A, "estilo_ari": ari_A,
        },
        "motor_B": {
            "descricao": "experimental com Gutenberg balanceado",
            "obs": cB._total, "vocab": len(cB._palavra_acao), "acoes": len(cB._freq_acao),
            "gutenberg_frases": len(frases_gut),
            "sinonimia_auc": auc_B, "zero_shot": ac_zs_B/tot_zs_B, "estilo_ari": ari_B,
        },
        "delta": {"auc": d_auc, "zero_shot": d_zs, "ari": d_ari},
        "vencedores_B": n_B,
        "veredito": "ajuda" if n_B >= 2 else "nao_ajuda",
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "15_hiperfoco_gutenberg.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
