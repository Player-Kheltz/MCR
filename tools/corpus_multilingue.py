"""tools/corpus_multilingue.py — Gerador de corpus multi-idioma multi-dominio.

Gera ~5000 observacoes cobrindo 10 dominios x 3 idiomas (PT, EN, ES)
com sinonimos跨-idioma em cada conceito.

MCR puro: tudo e observacao ingerida via coupling.alimentar(texto, acao).
Nenhuma lista hardcoded no motor — o corpus eDados, nao codigo.

Uso:
    from tools.corpus_multilingue import gerar_corpus
    corpus = gerar_corpus()  # List[Tuple[str, str]] (texto, acao)
    for texto, acao in corpus:
        coupling.alimentar(texto, acao)
"""
import random

# Seed para reprodutibilidade
random.seed(42)


# === CONCEITOS跨-idioma ===
# Cada conceito tem: PT, EN, ES + propriedades compartilhadas
# Sinonimos跨-idioma: cachorro (PT) = dog (EN) = perro (ES)

CONCEITOS = {
    "animais": {
        "cachorro": {"pt": "cachorro", "en": "dog", "es": "perro",
                     "acoes": ["late", "corre", "brinca", "come", "tem"],
                     "props": ["quatro patas", "pelo macio", "animal domestico"]},
        "gato": {"pt": "gato", "en": "cat", "es": "gato",
                 "acoes": ["mia", "sobe", "dorme", "come", "tem"],
                 "props": ["quatro patas", "pelo macio", "animal domestico"]},
        "passaro": {"pt": "passaro", "en": "bird", "es": "pajaro",
                    "acoes": ["voa", "canta", "bota", "tem"],
                    "props": ["penas", "asa", "animal voador"]},
        "peixe": {"pt": "peixe", "en": "fish", "es": "pez",
                  "acoes": ["nada", "respira", "tem"],
                  "props": ["escamas", "guelras", "vive na agua"]},
        "cavalo": {"pt": "cavalo", "en": "horse", "es": "caballo",
                   "acoes": ["corre", "galopa", "come", "tem"],
                   "props": ["quatro patas", "crina", "animal forte"]},
    },
    "tempo": {
        "dia": {"pt": "dia", "en": "day", "es": "dia",
                "acoes": ["tem", "passa", "comeca"],
                "props": ["vinte quatro horas", "manha tarde noite", "luz solar"]},
        "hora": {"pt": "hora", "en": "hour", "es": "hora",
                 "acoes": ["tem", "passa", "marca"],
                 "props": ["sessenta minutos", "unidade tempo", "relogio marca"]},
        "semana": {"pt": "semana", "en": "week", "es": "semana",
                   "acoes": ["tem", "passa"],
                   "props": ["sete dias", "trabalho descanso", "periodo tempo"]},
        "mes": {"pt": "mes", "en": "month", "es": "mes",
                "acoes": ["tem", "passa"],
                "props": ["trinta dias", "calendario", "periodo tempo"]},
        "ano": {"pt": "ano", "en": "year", "es": "ano",
                "acoes": ["tem", "passa"],
                "props": ["trezentos sessenta cinco dias", "doze meses", "calendario"]},
    },
    "objetos": {
        "cadeira": {"pt": "cadeira", "en": "chair", "es": "silla",
                    "acoes": ["tem", "serve", "feita"],
                    "props": ["quatro pernas", "madeira", "sentar"]},
        "mesa": {"pt": "mesa", "en": "table", "es": "mesa",
                 "acoes": ["tem", "serve"],
                 "props": ["tampo liso", "apoiar objetos", "madeira"]},
        "porta": {"pt": "porta", "en": "door", "es": "puerta",
                  "acoes": ["abre", "fecha", "tem"],
                  "props": ["madeira", "entrada", "passar"]},
        "janela": {"pt": "janela", "en": "window", "es": "ventana",
                   "acoes": ["deixa", "tem", "abre"],
                   "props": ["vidro", "luz entra", "ventilar"]},
        "livro": {"pt": "livro", "en": "book", "es": "libro",
                  "acoes": ["tem", "conta", "le"],
                  "props": ["paginas", "historias", "conhecimento"]},
    },
    "cores": {
        "vermelho": {"pt": "vermelho", "en": "red", "es": "rojo",
                     "acoes": ["e", "parece", "cor"],
                     "props": ["cor forte", "sangue fogo", "paixao"]},
        "azul": {"pt": "azul", "en": "blue", "es": "azul",
                 "acoes": ["e", "parece", "cor"],
                 "props": ["cor ceu", "cor mar", "calma"]},
        "verde": {"pt": "verde", "en": "green", "es": "verde",
                  "acoes": ["e", "parece", "cor"],
                  "props": ["cor planta", "cor folha", "natureza"]},
        "amarelo": {"pt": "amarelo", "en": "yellow", "es": "amarillo",
                    "acoes": ["e", "parece", "cor"],
                    "props": ["cor sol", "cor ouro", "alegre"]},
        "branco": {"pt": "branco", "en": "white", "es": "blanco",
                   "acoes": ["e", "parece", "cor"],
                   "props": ["cor neve", "cor luz", "pureza"]},
    },
    "emocoes": {
        "alegria": {"pt": "alegria", "en": "joy", "es": "alegria",
                    "acoes": ["e", "sente", "traz"],
                    "props": ["sentimento bom", "felicidade", "sorrir"]},
        "tristeza": {"pt": "tristeza", "en": "sadness", "es": "tristeza",
                     "acoes": ["e", "sente", "traz"],
                     "props": ["sentimento ruim", "chorar", "dor"]},
        "raiva": {"pt": "raiva", "en": "anger", "es": "ira",
                  "acoes": ["e", "sente", "traz"],
                  "props": ["sentimento forte", "irritacao", "violencia"]},
        "medo": {"pt": "medo", "en": "fear", "es": "miedo",
                 "acoes": ["e", "sente", "traz"],
                 "props": ["sentimento perigo", "fugir", "ansiedade"]},
        "amor": {"pt": "amor", "en": "love", "es": "amor",
                 "acoes": ["e", "sente", "traz"],
                 "props": ["sentimento forte", "carinho", "afeto"]},
    },
    "acoes_fisicas": {
        "correr": {"pt": "correr", "en": "run", "es": "correr",
                   "acoes": ["e", "rapido", "pernas"],
                   "props": ["movimento rapido", "exercicio", "esforco"]},
        "pular": {"pt": "pular", "en": "jump", "es": "saltar",
                  "acoes": ["e", "alto", "pernas"],
                  "props": ["movimento alto", "impulso", "altura"]},
        "nadar": {"pt": "nadar", "en": "swim", "es": "nadar",
                  "acoes": ["e", "agua", "braços"],
                  "props": ["movimento agua", "flutuar", "mergulhar"]},
        "voar": {"pt": "voar", "en": "fly", "es": "volar",
                 "acoes": ["e", "alto", "asa"],
                 "props": ["movimento alto", "ar", "liberdade"]},
        "escalar": {"pt": "escalar", "en": "climb", "es": "escalar",
                    "acoes": ["e", "alto", "maos"],
                    "props": ["subir", "montanha", "esforco"]},
    },
    "numeros": {
        "um": {"pt": "um", "en": "one", "es": "uno",
               "acoes": ["e", "conta", "numero"],
               "props": ["primeiro", "unidade", "singular"]},
        "dois": {"pt": "dois", "en": "two", "es": "dos",
                 "acoes": ["e", "conta", "numero"],
                 "props": ["par", "dupla", "segundo"]},
        "tres": {"pt": "tres", "en": "three", "es": "tres",
                 "acoes": ["e", "conta", "numero"],
                 "props": ["trio", "terceiro", "multiplo"]},
        "dez": {"pt": "dez", "en": "ten", "es": "diez",
                "acoes": ["e", "conta", "numero"],
                "props": ["dezena", "base dez", "multiplo"]},
        "cem": {"pt": "cem", "en": "hundred", "es": "cien",
                "acoes": ["e", "conta", "numero"],
                "props": ["centena", "base cem", "grande"]},
    },
    "ciencia": {
        "agua": {"pt": "agua", "en": "water", "es": "agua",
                 "acoes": ["e", "bebe", "liquido"],
                 "props": ["liquido", "essencial vida", "molhado"]},
        "fogo": {"pt": "fogo", "en": "fire", "es": "fuego",
                 "acoes": ["e", "queima", "quente"],
                 "props": ["calor", "luz", "combustao"]},
        "ar": {"pt": "ar", "en": "air", "es": "aire",
               "acoes": ["e", "respira", "gas"],
               "props": ["gas", "respirar", "invisivel"]},
        "terra": {"pt": "terra", "en": "earth", "es": "tierra",
                  "acoes": ["e", "solida", "planeta"],
                  "props": ["solo", "planeta", "solido"]},
        "luz": {"pt": "luz", "en": "light", "es": "luz",
                "acoes": ["e", "ilumina", "rapida"],
                "props": ["energia", "visivel", "rapida"]},
    },
    "corpo": {
        "mao": {"pt": "mao", "en": "hand", "es": "mano",
                "acoes": ["tem", "segura", "toca"],
                "props": ["cinco dedos", "pegar", "sentir"]},
        "pe": {"pt": "pe", "en": "foot", "es": "pie",
               "acoes": ["tem", "anda", "apoia"],
               "props": ["cinco dedos", "caminhar", "equilibrio"]},
        "olho": {"pt": "olho", "en": "eye", "es": "ojo",
                 "acoes": ["tem", "ve", "olha"],
                 "props": ["ver", "visao", "cor"]},
        "boca": {"pt": "boca", "en": "mouth", "es": "boca",
                 "acoes": ["tem", "fala", "come"],
                 "props": ["falar", "comer", "lábios"]},
        "coracao": {"pt": "coracao", "en": "heart", "es": "corazon",
                    "acoes": ["bate", "bomba", "tem"],
                    "props": ["sangue", "vida", "peito"]},
    },
    "conceitos": {
        "nome": {"pt": "nome", "en": "name", "es": "nombre",
                 "acoes": ["identifica", "e", "tem"],
                 "props": ["palavra", "pessoa", "identificar"]},
        "pessoa": {"pt": "pessoa", "en": "person", "es": "persona",
                   "acoes": ["e", "tem", "pensa"],
                   "props": ["humano", "nome", "idade"]},
        "conhecimento": {"pt": "conhecimento", "en": "knowledge", "es": "conocimiento",
                         "acoes": ["e", "aprende", "adquire"],
                         "props": ["aprendido", "observacao", "informacao"]},
        "aprender": {"pt": "aprender", "en": "learn", "es": "aprender",
                     "acoes": ["e", "adquire", "estuda"],
                     "props": ["conhecimento", "observacao", "estudo"]},
        "entender": {"pt": "entender", "en": "understand", "es": "entender",
                     "acoes": ["e", "compreende", "significado"],
                     "props": ["compreender", "significado", "clareza"]},
    },
    "tecnologia": {
        "computador": {"pt": "computador", "en": "computer", "es": "computadora",
                       "acoes": ["processa", "executa", "tem"],
                       "props": ["dados", "programas", "memoria rapida"]},
        "internet": {"pt": "internet", "en": "internet", "es": "internet",
                     "acoes": ["conecta", "transmite", "tem"],
                     "props": ["rede global", "informacao", "comunicacao"]},
        "programa": {"pt": "programa", "en": "program", "es": "programa",
                     "acoes": ["executa", "roda", "tem"],
                     "props": ["codigo", "instrucoes", "software"]},
        "dados": {"pt": "dados", "en": "data", "es": "datos",
                  "acoes": ["sao", "tem", "armazena"],
                  "props": ["informacao", "numeros", "estruturado"]},
        "codigo": {"pt": "codigo", "en": "code", "es": "codigo",
                   "acoes": ["e", "define", "tem"],
                   "props": ["instrucoes", "logica", "programar"]},
    },
    "comida": {
        "arroz": {"pt": "arroz", "en": "rice", "es": "arroz",
                  "acoes": ["e", "come", "cozinha"],
                  "props": ["grao branco", "alimento base", "nutritivo"]},
        "feijao": {"pt": "feijao", "en": "beans", "es": "frijoles",
                   "acoes": ["e", "come", "cozinha"],
                   "props": ["grao marrom", "proteina", "alimento"]},
        "pao": {"pt": "pao", "en": "bread", "es": "pan",
                "acoes": ["e", "come", "tem"],
                "props": ["farinha", "trigo", "alimento"]},
        "carne": {"pt": "carne", "en": "meat", "es": "carne",
                  "acoes": ["e", "come", "tem"],
                  "props": ["proteina animal", "vermelho", "nutritivo"]},
        "fruta": {"pt": "fruta", "en": "fruit", "es": "fruta",
                  "acoes": ["e", "come", "tem"],
                  "props": ["doce", "vitamina", "natural"]},
    },
    "lugares": {
        "casa": {"pt": "casa", "en": "house", "es": "casa",
                 "acoes": ["e", "tem", "abriga"],
                 "props": ["moradia", "abrigo", "construcao"]},
        "escola": {"pt": "escola", "en": "school", "es": "escuela",
                   "acoes": ["e", "tem", "ensina"],
                   "props": ["educacao", "aprender", "edificio"]},
        "cidade": {"pt": "cidade", "en": "city", "es": "ciudad",
                   "acoes": ["e", "tem", "abriga"],
                   "props": ["urbano", "pessoas", "construcoes"]},
        "floresta": {"pt": "floresta", "en": "forest", "es": "bosque",
                     "acoes": ["e", "tem", "abriga"],
                     "props": ["arvores", "natureza", "animais"]},
        "rio": {"pt": "rio", "en": "river", "es": "rio",
                "acoes": ["corre", "tem", "leva"],
                "props": ["agua", "corrente", "natureza"]},
    },
    "plantas": {
        "arvore": {"pt": "arvore", "en": "tree", "es": "arbol",
                   "acoes": ["cresce", "tem", "da"],
                   "props": ["tronco", "folhas", "madeira"]},
        "flor": {"pt": "flor", "en": "flower", "es": "flor",
                 "acoes": ["e", "tem", "exala"],
                 "props": ["petalas coloridas", "perfume", "planta bonita"]},
        "grama": {"pt": "grama", "en": "grass", "es": "hierba",
                  "acoes": ["cresce", "e", "cobrir"],
                  "props": ["verde", "planta rasteira", "jardim"]},
        "folha": {"pt": "folha", "en": "leaf", "es": "hoja",
                  "acoes": ["e", "cai", "faz"],
                  "props": ["verde", "fotossintese", "planta"]},
        "raiz": {"pt": "raiz", "en": "root", "es": "raiz",
                 "acoes": ["e", "absorve", "fixa"],
                 "props": ["subterranea", "agua", "nutriente"]},
    },
}


# === TEMPLATES de frases por idioma ===
# Cada template gera uma frase contextual sobre o conceito

TEMPLATES = {
    "pt": [
        "{suj} {acao} {prop}",
        "{suj} tem {prop}",
        "{suj} e {prop}",
        "o {suj} {acao}",
        "{suj} {acao} {prop} no contexto",
        "conceito {suj} significa {prop}",
        "{suj} caracteristica {prop}",
        "{suj} exemplo {prop}",
        "{suj} associado {prop}",
        "{suj} relacionado {prop}",
    ],
    "en": [
        "{suj} {acao} {prop}",
        "{suj} has {prop}",
        "{suj} is {prop}",
        "the {suj} {acao}",
        "{suj} {acao} {prop} in context",
        "concept {suj} means {prop}",
        "{suj} characteristic {prop}",
        "{suj} example {prop}",
        "{suj} associated {prop}",
        "{suj} related {prop}",
    ],
    "es": [
        "{suj} {acao} {prop}",
        "{suj} tiene {prop}",
        "{suj} es {prop}",
        "el {suj} {acao}",
        "{suj} {acao} {prop} en contexto",
        "concepto {suj} significa {prop}",
        "{suj} caracteristica {prop}",
        "{suj} ejemplo {prop}",
        "{suj} asociado {prop}",
        "{suj} relacionado {prop}",
    ],
}


def gerar_corpus(reps_por_frase: int = 3, max_obs: int = 50000) -> list:
    """Gera corpus multi-idioma multi-dominio.

    Props sao compartilhadas entre idiomas — cria bridges跨-idioma.
    "dog has quatro patas" e gramaticalmente errado mas estatisticamente
    cria co-ocorrencia: dog~quatro~patas = cachorro~quatro~patas = perro~quatro~patas.
    MCR puro: P(b|a) nao depende de gramatica, depende de co-ocorrencia.

    Returns: List[Tuple[str, str]] — (texto, acao) para coupling.alimentar()
    """
    corpus = []
    for dominio, conceitos in CONCEITOS.items():
        for conceito_id, dados in conceitos.items():
            for idioma in ["pt", "en", "es"]:
                suj = dados[idioma]
                for acao in dados["acoes"]:
                    for prop in dados["props"]:
                        for template in TEMPLATES[idioma]:  # todos os 10 templates
                            frase = template.format(suj=suj, acao=acao, prop=prop)
                            for _ in range(reps_por_frase):
                                corpus.append((frase, "descrever"))
    random.shuffle(corpus)
    if max_obs and len(corpus) > max_obs:
        corpus = corpus[:max_obs]
    return corpus


def sinonimos_teste() -> list:
    """Retorna lista de pares跨-idioma para validacao _nmi_semantico.

    Returns: List[Tuple[str, str, str, str]] — (a, b, idioma_a, idioma_b)
    """
    pares = []
    for dominio, conceitos in CONCEITOS.items():
        conceito_ids = list(conceitos.keys())
        for i, cid in enumerate(conceito_ids):
            dados = conceitos[cid]
            # Sinonimos跨-idioma: PT vs EN vs ES do mesmo conceito
            pares.append((dados["pt"], dados["en"], "sinonimo PT-EN"))
            pares.append((dados["pt"], dados["es"], "sinonimo PT-ES"))
            pares.append((dados["en"], dados["es"], "sinonimo EN-ES"))
            # Nao-relacionados: conceitos diferentes do mesmo dominio
            for j in range(i + 1, len(conceito_ids)):
                outros = conceitos[conceito_ids[j]]
                pares.append((dados["pt"], outros["pt"], "nao-relacionado mesmo dominio"))
    # Nao-relacionados跨-dominio
    todos_conceitos = []
    for dominio, conceitos in CONCEITOS.items():
        for cid, dados in conceitos.items():
            todos_conceitos.append((dominio, cid, dados))
    for i in range(len(todos_conceitos)):
        for j in range(i + 1, len(todos_conceitos)):
            d1, c1, dados1 = todos_conceitos[i]
            d2, c2, dados2 = todos_conceitos[j]
            if d1 != d2:
                pares.append((dados1["pt"], dados2["pt"], "nao-relacionado跨-dominio"))
    return pares


if __name__ == "__main__":
    corpus = gerar_corpus()
    print(f"Corpus gerado: {len(corpus)} observacoes")
    print(f"Dominios: {len(CONCEITOS)}")
    print(f"Conceitos: {sum(len(c) for c in CONCEITOS.values())}")
    print(f"Idiomas: 3 (PT, EN, ES)")
    pares = sinonimos_teste()
    print(f"Pares de teste: {len(pares)}")
    sin = [p for p in pares if "sinonimo" in p[2]]
    nao = [p for p in pares if "nao-relacionado" in p[2]]
    print(f"  Sinonimos跨-idioma: {len(sin)}")
    print(f"  Nao-relacionados: {len(nao)}")
