"""tools/corpus_expanedido.py — Corpus massivo multi-fonte multi-idioma.

Busca de 4 fontes em paralelo:
  1. Wikipedia 5 idiomas (PT/EN/ES/FR/DE) — 300+ conceitos
  2. Rosetta Code — codigo跨-linguagem (same algorithms, different languages)
  3. Project Gutenberg — livros classicos em multiplos idiomas

MCR puro: tudo e observacao ingerida via coupling.alimentar().
Corpus e DADOS, nao codigo do motor.

Uso:
    from tools.corpus_expanedido import buscar_tudo
    corpus = buscar_tudo(cache_only=False)  # List[Tuple[str, str]]
    for texto, acao in corpus:
        coupling.alimentar(texto, acao)
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
import os
import sys
import hashlib
import html as html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'corpus_expa')
os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# PARTE 1: CONCEITOS EXPANDIDOS (16 dominios, 5 idiomas)
# ============================================================
# Formato: cid: (pt, en, es, fr, de, acoes, props)

CONCEITOS_NOVOS = {
    "matematica": {
        "numero": ("numero", "number", "numero", "nombre", "Zahl", ["conta", "mede", "representa"], ["abstrato", "quantidade", "simbolo"]),
        "soma": ("soma", "sum", "suma", "somme", "Summe", ["calcula", "une", "junta"], ["operacao", "adicao", "resultado"]),
        "subtracao": ("subtracao", "subtraction", "resta", "soustraction", "Subtraktion", ["tira", "diminui", "calcula"], ["operacao", "diferenca", "menos"]),
        "multiplicacao": ("multiplicacao", "multiplication", "multiplicacion", "multiplication", "Multiplikation", ["calcula", "multiplica", "aumenta"], ["operacao", "produto", "vezes"]),
        "divisao": ("divisao", "division", "division", "division", "Division", ["calcula", "divide", "separa"], ["operacao", "quociente", "razao"]),
        "geometria": ("geometria", "geometry", "geometria", "geometrie", "Geometrie", ["estuda", "mede", "calcula"], ["forma", "espaco", "angulo"]),
        "angulo": ("angulo", "angle", "angulo", "angle", "Winkel", ["mede", "forma", "tem"], ["graus", "giro", "vertices"]),
        "circulo": ("circulo", "circle", "circulo", "cercle", "Kreis", ["tem", "mede", "forma"], ["raio", "diametro", "pi"]),
        "triangulo": ("triangulo", "triangle", "triangulo", "triangle", "Dreieck", ["tem", "forma", "tem tres"], ["angulo", "lado", "base"]),
        "retangulo": ("retangulo", "rectangle", "rectangulo", "rectangle", "Rechteck", ["tem", "forma", "tem quatro"], ["lado", "angulo", "perimetro"]),
        "area": ("area", "area", "area", "superficie", "Flache", ["mede", "calcula", "tem"], ["superficie", "quadrado", "espaco"]),
        "perimetro": ("perimetro", "perimeter", "perimetro", "perimetre", "Umfang", ["mede", "calcula", "tem"], ["contorno", "soma lados", "extensao"]),
        "fracao": ("fracao", "fraction", "fraccion", "fraction", "Bruch", ["representa", "divide", "calcula"], ["parte", "numerador", "denominador"]),
        "decimal": ("decimal", "decimal", "decimal", "decimal", "Dezimal", ["representa", "usa", "calcula"], ["ponto", "casas", "precisao"]),
        "equacao": ("equacao", "equation", "ecuacion", "equation", "Gleichung", ["resolve", "iguala", "contem"], ["incognita", "termo", "solucao"]),
    },
    "fisica": {
        "gravidade": ("gravidade", "gravity", "gravedad", "gravite", "Schwerkraft", ["atrai", "puxa", "afeta"], ["forca", "massa", "aterrissagem"]),
        "energia": ("energia", "energy", "energia", "energie", "Energie", ["faz", "move", "transforma"], ["forca", "trabalho", "potencia"]),
        "forca": ("forca", "force", "fuerza", "force", "Kraft", ["empurra", "puxa", "move"], ["newton", "vetor", "intensidade"]),
        "velocidade": ("velocidade", "speed", "velocidad", "vitesse", "Geschwindigkeit", ["mede", "calcula", "tem"], ["rapidez", "distancia", "tempo"]),
        "aceleracao": ("aceleracao", "acceleration", "aceleracion", "acceleration", "Beschleunigung", ["aumenta", "mede", "muda"], ["velocidade", "forca", "massa"]),
        "inercia": ("inercia", "inertia", "inercia", "inertie", "Tragheit", ["resiste", "mantem", "obedece"], ["massa", "movimento", "repouso"]),
        "friccao": ("friccao", "friction", "frottement", "friccion", "Reibung", ["resiste", "atrasa", "aquece"], ["superficie", "forca", "deslizamento"]),
        "onda": ("onda", "wave", "onda", "onde", "Welle", ["propaga", "transporta", "oscila"], ["frequencia", "amplitude", "comprimento"]),
        "luz": ("luz", "light", "luz", "lumiere", "Licht", ["ilumina", "viaja", "reflete"], ["foton", "espectro", "velocidade"]),
        "calor": ("calor", "heat", "calor", "chaleur", "Warme", ["aquece", "transmite", "mede"], ["temperatura", "energia", "transferencia"]),
        "temperatura": ("temperatura", "temperature", "temperatura", "temperature", "Temperatur", ["mede", "indica", "afeta"], ["graus", "celsius", "fahrenheit"]),
        "eletricidade": ("eletricidade", "electricity", "electricidad", "electricite", "Elektrizitat", ["conduz", "gera", "alimenta"], ["corrente", "tensao", "resistencia"]),
        "magnetismo": ("magnetismo", "magnetism", "magnetismo", "magnetisme", "Magnetismus", ["atrai", "repole", "gera"], ["polo", "campo", "forca"]),
    },
    "biologia": {
        "celula": ("celula", "cell", "celula", "cellule", "Zelle", ["contem", "divide", "funciona"], ["membrana", "nucleo", "citoplasma"]),
        "dna": ("dna", "dna", "adn", "adn", "dns", ["contem", "codifica", "transmite"], ["gene", "helice", "heranca"]),
        "gene": ("gene", "gene", "gen", "gene", "Gen", ["codifica", "determina", "transmite"], ["dna", "heranca", "proteina"]),
        "especie": ("especie", "species", "especie", "espece", "Art", ["classifica", "descreve", "evolui"], ["biologia", "populacao", "classificacao"]),
        "evolucao": ("evolucao", "evolution", "evolucion", "evolution", "Evolution", ["transforma", "seleciona", "adapta"], ["especie", "mutacao", "adaptacao"]),
        "fotossintese": ("fotossintese", "photosynthesis", "fotosintesis", "photosynthese", "Photosynthese", ["converte", "produz", "usa"], ["luz", "clorofila", "oxigenio"]),
        "respiracao": ("respiracao", "respiration", "respiracion", "respiration", "Atmung", ["inspira", "expira", "troca"], ["oxigenio", "gas carbonico", "pulmao"]),
        "digestao": ("digestao", "digestion", "digestion", "digestion", "Verdauung", ["quebra", "absorve", "processa"], ["alimento", "enzima", "estomago"]),
        "circulacao": ("circulacao", "circulation", "circulacion", "circulation", "Kreislauf", ["bomba", "transporta", "leva"], ["sangue", "coracao", "vasos"]),
        "sistema_nervoso": ("sistema nervoso", "nervous system", "sistema nervioso", "systeme nerveux", "Nervensystem", ["controla", "transmite", "coordena"], ["neuronio", "cerebro", "sinal"]),
        "ecossistema": ("ecossistema", "ecosystem", "ecosistema", "ecosysteme", "Okosystem", ["contem", "interage", "equilibra"], ["organismo", "ambiente", "cadeia alimentar"]),
        "biodiversidade": ("biodiversidade", "biodiversity", "biodiversidad", "biodiversite", "Biodiversitat", ["mede", "protege", "varia"], ["especie", "habitat", "conservacao"]),
    },
    "quimica": {
        "atomo": ("atomo", "atom", "atomo", "atome", "Atom", ["composto", "contem", "combina"], ["proton", "neutron", "eletron"]),
        "molecula": ("molecula", "molecule", "molecula", "molecule", "Molekul", ["composta", "forma", "reage"], ["atomo", "liga", "estrutura"]),
        "elemento": ("elemento", "element", "elemento", "element", "Element", ["composto", "classificado", "tabela"], ["quimico", "simbolo", "numero atomico"]),
        "reacao_quimica": ("reacao quimica", "chemical reaction", "reaccion quimica", "reaction chimique", "Chemische Reaktion", ["transforma", "produz", "libera"], ["produtos", "reativos", "energia"]),
        "acido": ("acido", "acid", "acido", "acide", "Saure", ["corroi", "dissolve", "reage"], ["pH", "proton", "corrosivo"]),
        "base": ("base", "base", "base", "base", "Base", ["neutraliza", "corrosiva", "reage"], ["pH", "hidroxido", "sabao"]),
        "sal": ("sal", "salt", "sal", "sel", "Sal", ["dissolve", "cristaliza", "condutor"], ["cloreto sodio", "sabor", "cristal"]),
        "gas": ("gas", "gas", "gas", "gaz", "Gas", ["expande", "comprime", "flui"], ["molecula", "pressao", "temperatura"]),
        "solucao": ("solucao", "solution", "solucion", "solution", "Losung", ["mistura", "dissolve", "homogenea"], ["solute", "solvente", "concentracao"]),
        "metal": ("metal", "metal", "metal", "metal", "Metal", ["conduz", "dobra", "brilha"], ["conduzor", "liga", "corrosao"]),
    },
    "astronomia": {
        "planeta": ("planeta", "planet", "planeta", "planete", "Planet", ["orbita", "gira", "tem"], ["sol", "lua", "gravidade"]),
        "estrela": ("estrela", "star", "estrella", "etoile", "Stern", ["brilha", "nascem", "morrem"], ["luz", "fusao", "constelacao"]),
        "galaxia": ("galaxia", "galaxy", "galaxia", "galaxie", "Galaxie", ["contem", "gira", "tem"], ["estrelas", "buraco negro", "espaco"]),
        "sistema_solar": ("sistema solar", "solar system", "sistema solar", "systeme solaire", "Sonnensystem", ["contem", "orbita", "inclui"], ["sol", "planetas", "asteroides"]),
        "lua": ("lua", "moon", "luna", "lune", "Mond", ["orbita", "ilumina", "causa"], ["gravidade", "maré", "fases"]),
        "sol": ("sol", "sun", "sol", "soleil", "Sonne", ["ilumina", "aquece", "brilha"], ["estrela", "energia", "fusao"]),
        "constelacao": ("constelacao", "constellation", "constelacion", "constellation", "Sternbild", ["forma", "contem", "observa"], ["estrelas", "mito", "ceu"]),
        "meteoro": ("meteoro", "meteor", "meteoro", "meteore", "Meteor", ["entra", "brilha", "queima"], ["atmosfera", "asteroide", "chamas"]),
        "cometa": ("cometa", "comet", "cometa", "comete", "Komet", ["orbita", "tem", "aparece"], ["cauda", "gelo", "orbita"]),
        "buraco_negro": ("buraco negro", "black hole", "agujero negro", "trou noir", "Schwarzes Loch", ["atrai", "engole", "curva"], ["gravidade", "horizonte eventos", "singularidade"]),
    },
    "geologia": {
        "rocha": ("rocha", "rock", "roca", "roche", "Gestein", ["forma", "contem", "erode"], ["mineral", "solo", "ciclo"]),
        "mineral": ("mineral", "mineral", "mineral", "mineral", "Mineral", ["compoe", "cristaliza", "dura"], ["quartz", "feldspato", "cristal"]),
        "vulcao": ("vulcao", "volcano", "volcan", "volcan", "Vulkan", ["erupcao", "lanca", "aquece"], ["lava", "magma", "erupcao"]),
        "terremoto": ("terremoto", "earthquake", "terremoto", "seisme", "Erdbeben", ["sacaude", "libera", "causa"], ["placa", "vibracao", "destruicao"]),
        "erosao": ("erosao", "erosion", "erosion", "erosion", "Erosion", ["quebra", "transporta", "molha"], ["vento", "agua", "tempo"]),
        "sedimento": ("sedimento", "sediment", "sedimento", "sediment", "Sediment", ["deposita", "acumula", "formou"], ["camada", "areia", "lodo"]),
        "tectonica": ("tectonica", "tectonics", "tectonica", "tectonique", "Tektonik", ["move", "formou", "causa"], ["placa", "continente", "colisao"]),
        "fossil": ("fossil", "fossil", "fosil", "fossile", "Fossil", ["preserva", "revela", "formou"], ["especie", "rocha", "antigo"]),
        "solo": ("soil", "soil", "suelo", "sol", "Boden", ["contem", "nutre", "sustenta"], ["humus", "mineral", "organismo"]),
        "magma": ("magma", "magma", "magma", "magma", "Magma", ["derrete", "flui", "esfria"], ["rocha", "vulcao", "temperatura"]),
    },
    "historia": {
        "civilizacao": ("civilizacao", "civilization", "civilizacion", "civilisation", "Zivilisation", ["desenvolve", "constroi", "floresce"], ["cultura", "cidade", "governo"]),
        "guerra": ("guerra", "war", "guerra", "guerre", "Krieg", ["envolve", "causa", "destrói"], ["conflito", "exercito", "paz"]),
        "revolucao": ("revolucao", "revolution", "revolucion", "revolution", "Revolution", ["transforma", "muda", "causa"], ["mudanca", "poder", "povo"]),
        "imperio": ("imperio", "empire", "imperio", "empire", "Reich", ["domina", "expande", "contem"], ["territorio", "governo", "conquista"]),
        "comercio": ("comercio", "trade", "comercio", "commerce", "Handel", ["troca", "vende", "conecta"], ["mercado", "moeda", "rotas"]),
        "escrita": ("escrita", "writing", "escritura", "ecriture", "Schrift", ["registra", "comunica", "desenvolve"], ["letra", "texto", "historia"]),
        "religiao": ("religiao", "religion", "religion", "religion", "Religion", ["pratica", "ensina", "une"], ["fe", "culto", "ritual"]),
        "filosofia": ("filosofia", "philosophy", "filosofia", "philosophie", "Philosophie", ["estuda", "questiona", "reflete"], ["pensamento", "logica", "verdade"]),
        "tecnologia": ("tecnologia", "technology", "tecnologia", "technologie", "Technologie", ["desenvolve", "facilita", "transforma"], ["invencao", "maquina", "progresso"]),
        "migracao": ("migracao", "migration", "migracion", "migration", "Migration", ["move", "causa", "busca"], ["povo", "territorio", "esperanca"]),
    },
    "geografia": {
        "continente": ("continente", "continent", "continente", "continent", "Kontinent", ["contem", "forma", "dividem"], ["terra", "oceano", "regiao"]),
        "montanha": ("montanha", "mountain", "montana", "montagne", "Berg", ["sobe", "formou", "tem"], ["pico", "encosta", "rocha"]),
        "deserto": ("deserto", "desert", "desierto", "desert", "Wuste", ["seco", "quente", "areia"], ["cacto", "oasis", "temperatura"]),
        "oceano": ("oceano", "ocean", "oceano", "ocean", "Ozean", ["contem", "cobrem", "profundo"], ["agua", "salgada", "mar"]),
        "ilha": ("ilha", "island", "isla", "ile", "Insel", ["rodeada", "flutua", "tem"], ["praia", "costa", "océano"]),
        "costa": ("costa", "coast", "costa", "cote", "Kuste", ["borda", "beira", "tem"], ["praia", "mar", "rocha"]),
        "caverna": ("caverna", "cave", "cueva", "grotte", "Hohle", ["escuro", "formou", "contem"], ["estalactite", "morcego", "rocha"]),
        "cachoeira": ("cachoeira", "waterfall", "cascada", "chute d'eau", "Wasserfall", ["cai", "formou", "brilha"], ["agua", "altura", "rio"]),
        "lago": ("lago", "lake", "lago", "lac", "See", ["contem", "rodeado", "tem"], ["agua", "peixe", "margem"]),
        "planicie": ("planicie", "plain", "llanura", "plaine", "Ebene", ["largo", "plano", "tem"], ["terra", "agricultura", "extenso"]),
    },
    "filosofia": {
        "logica": ("logica", "logic", "logica", "logique", "Logik", ["estuda", "aplica", "segue"], ["raciocinio", "deducao", "argumento"]),
        "etica": ("etica", "ethics", "etica", "ethique", "Ethik", ["estuda", "guias", "questiona"], ["moral", "bom", "certo"]),
        "moral": ("moral", "morals", "moral", "moral", "Moral", ["guias", "ensina", "determina"], ["comportamento", "bem", "mal"]),
        "verdade": ("verdade", "truth", "verdad", "verite", "Wahrheit", ["busca", "descobre", "define"], ["realidade", "mentira", "conhecimento"]),
        "consciencia": ("consciencia", "consciousness", "conciencia", "conscience", "Bewusstsein", ["percebe", "sente", "reflete"], ["awareness", "mente", "experiencia"]),
        "existencialismo": ("existencialismo", "existentialism", "existencialismo", "existentialisme", "Existenzialismus", ["questiona", "explora", "afirma"], ["liberdade", "sentido", "angustia"]),
        "racionalismo": ("racionalismo", "rationalism", "racionalismo", "rationalisme", "Rationalismus", ["defende", "usa", "aposta"], ["razao", "logica", "verdade"]),
        "empirismo": ("empirismo", "empiricism", "empirismo", "empirisme", "Empirismus", ["defende", "observa", "testa"], ["experiencia", "sentidos", "ciencia"]),
        "dialética": ("dialética", "dialectics", "dialéctica", "dialectique", "Dialektik", ["usa", "opoe", "resolve"], ["tese", "antitese", "sintese"]),
        "estetica": ("estetica", "aesthetics", "estetica", "esthetique", "Asthetik", ["estuda", "aprecia", "avalia"], ["beleza", "arte", "gosto"]),
    },
    "economia": {
        "moeda": ("moeda", "currency", "moneda", "monnaie", "Wahrung", ["troca", "vale", "representa"], ["dinheiro", "valor", "comercio"]),
        "mercado": ("mercado", "market", "mercado", "marche", "Markt", ["compra", "vende", "negocia"], ["oferta", "demanda", "preco"]),
        "oferta": ("oferta", "supply", "oferta", "offre", "Angebot", ["disponibiliza", "produz", "vende"], ["produto", "quantidade", "preco"]),
        "demanda": ("demanda", "demand", "demanda", "demande", "Nachfrage", ["quer", "precisa", "busca"], ["consumidor", "desejo", "quantidade"]),
        "investimento": ("investimento", "investment", "inversion", "investissement", "Investition", ["coloca", "espera", "cresce"], ["capital", "risco", "retorno"]),
        "lucro": ("lucro", "profit", "ganancia", "profit", "Gewinn", ["gera", "calcula", "realiza"], ["receita", "custo", "margem"]),
        "trabalho": ("trabalho", "work", "trabajo", "travail", "Arbeit", ["faz", "produz", "gera"], ["emprego", "salario", "esforco"]),
        "capital": ("capital", "capital", "capital", "capital", "Kapital", ["investe", "acumula", "financia"], ["dinheiro", "recursos", "riqueza"]),
        "consumo": ("consumo", "consumption", "consumo", "consommation", "Konsum", ["usa", "compra", "gasta"], ["produto", "necessidade", "desejo"]),
        "desemprego": ("desemprego", "unemployment", "desempleo", "chomage", "Arbeitslosigkeit", ["afeta", "causa", "mede"], ["trabalho", "crise", "social"]),
    },
    "musica": {
        "instrumento": ("instrumento", "instrument", "instrumento", "instrument", "Instrument", ["toca", "produz", "tem"], ["som", "musica", "corda"]),
        "nota_musical": ("nota musical", "musical note", "nota musical", "note musicale", "Musiknote", ["representa", "produz", "tem"], ["altura", "duracao", "pentagrama"]),
        "ritmo": ("ritmo", "rhythm", "ritmo", "rythmus", "Rhythmus", ["marca", "guia", "tem"], ["batida", "tempo", "movimento"]),
        "melodia": ("melodia", "melody", "melodia", "melodie", "Melodie", ["canta", "compoem", "tem"], ["notas", "harmonia", "frase"]),
        "harmonia": ("harmonia", "harmony", "armonia", "harmonie", "Harmonie", ["combina", "acompanha", "enriquece"], ["acorde", "notas", "consonancia"]),
        "orquestra": ("orquestra", "orchestra", "orquesta", "orchestre", "Orchester", ["executa", "dirige", "contem"], ["musico", "instrumento", "concerto"]),
        "canto": ("canto", "singing", "canto", "chant", "Gesang", ["produz", "expressa", "tecnica"], ["voz", "nota", "letra"]),
        "compositor": ("compositor", "composer", "compositor", "compositeur", "Komponitor", ["cria", "escreve", "imagina"], ["musica", "partitura", "obra"]),
        "genero_musical": ("genero musical", "music genre", "genero musical", "genre musical", "Musikgenre", ["classifica", "agrupa", "identifica"], ["estilo", "cultura", "publico"]),
        "partitura": ("partitura", "musical score", "partitura", "partition", "Notenblatt", ["escreve", "registra", "le"], ["notas", "ritmo", "instrumento"]),
    },
    "arte": {
        "pintura": ("pintura", "painting", "pintura", "peinture", "Malerei", ["cria", "expressa", "mostra"], ["cor", "tela", "pincel"]),
        "escultura": ("escultura", "sculpture", "escultura", "sculpture", "Skulptur", ["esculpi", "forma", "cria"], ["pedra", "marmore", "bronze"]),
        "desenho": ("desenho", "drawing", "dibujo", "dessin", "Zeichnung", ["faz", "rabisca", "representa"], ["lápis", "papel", "linha"]),
        "fotografia": ("fotografia", "photography", "fotografia", "photographie", "Fotografie", ["captura", "mostra", "registra"], ["camera", "luz", "imagem"]),
        "arquitetura": ("arquitetura", "architecture", "arquitectura", "architecture", "Architektur", ["projeta", "constroi", "desenha"], ["edificio", "estilo", "estrutura"]),
        "museu": ("museu", "museum", "museo", "musee", "Museum", ["preserva", "exibe", "ensina"], ["arte", "historia", "cultura"]),
        "galeria": ("galeria", "gallery", "galeria", "galerie", "Galerie", ["exibe", "mostra", "contem"], ["arte", "quadro", "exposicao"]),
        "artista": ("artista", "artist", "artista", "artiste", "Kunstler", ["cria", "expressa", "imagina"], ["obra", "talento", "inspiracao"]),
        "estilo_artistico": ("estilo artistico", "artistic style", "estilo artistico", "style artistique", "Kunststil", ["identifica", "agrupa", "caracteriza"], ["movimento", "epoca", "tecnica"]),
        "obra_de_arte": ("obra de arte", "work of art", "obra de arte", "oeuvre d'art", "Kunstwerk", ["cria", "expressa", "representa"], ["artistica", "cultural", "emocional"]),
    },
    "esportes": {
        "futebol": ("futebol", "soccer", "futbol", "football", "Fussball", ["joga", "chuta", "marca"], ["gol", "time", "campo"]),
        "basquete": ("basquete", "basketball", "baloncesto", "basketball", "Basketball", ["joga", "lanca", "marca"], ["cesta", "time", "quadra"]),
        "natacao": ("natacao", "swimming", "natacion", "natation", "Schwimmen", ["nada", "compete", "treina"], ["agua", "piscina", "estilo"]),
        "atletismo": ("atletismo", "athletics", "atletismo", "athletisme", "Leichtathletik", ["corre", "pula", "lanca"], ["prova", "velocidade", "distancia"]),
        "ciclismo": ("ciclismo", "cycling", "ciclismo", "cyclisme", "Radsport", ["pedala", "corre", "compete"], ["bicicleta", "pista", "velocidade"]),
        "tênis": ("tênis", "tenis", "tenis", "tennis", "Tennis", ["joga", "bate", "compete"], ["raquete", "bola", "quadra"]),
        "volei": ("volei", "volleyball", "voleibol", "volleyball", "Volleyball", ["joga", "bate", "defende"], ["rede", "ponto", "time"]),
        "xadrez": ("xadrez", "chess", "ajedrez", "echecs", "Schach", ["joga", "move", "strategiza"], ["pecas", "tabuleiro", "estrategia"]),
        "Boxe": ("boxe", "boxing", "boxeo", "boxe", "Boxen", ["luta", "defende", "treina"], ["luva", "ringue", "golpe"]),
        "corrida": ("corrida", "running", "carrera", "course", "Lauf", ["corre", "compete", "treina"], ["velocidade", "distancia", "resistencia"]),
    },
    "programacao": {
        "algoritmo": ("algoritmo", "algorithm", "algoritmo", "algorithme", "Algorithmus", ["resolve", "executa", "sequencia"], ["passos", "eficiencia", "computacao"]),
        "variavel": ("variavel", "variable", "variable", "variable", "Variabel", ["armazena", "muda", "declara"], ["valor", "tipo", "nome"]),
        "funcao": ("funcao", "function", "funcion", "fonction", "Funktion", ["executa", "retorna", "chama"], ["parametro", "codigo", "resultado"]),
        "loop": ("loop", "loop", "bucle", "boucle", "Schleife", ["repete", "itera", "executa"], ["condicao", "contador", "iteracao"]),
        "array": ("array", "array", "arreglo", "tableau", "Array", ["contem", "indexa", "armazena"], ["elemento", "indice", "tamanho"]),
        "string": ("string", "string", "cadena", "chaine", "Zeichenkette", ["contem", "concatena", "manipula"], ["texto", "caracter", "comprimento"]),
        "classe": ("classe", "class", "clase", "classe", "Klasse", ["define", "cria", "instancia"], ["objeto", "atributo", "metodo"]),
        "objeto": ("objeto", "object", "objeto", "objet", "Objekt", ["instancia", "contem", "metodo"], ["atributo", "classe", "estado"]),
        "recursao": ("recursao", "recursion", "recursion", "recursion", "Rekursion", ["chama", "resolve", "divide"], ["base case", "chamada", "pilha"]),
        "compilador": ("compilador", "compiler", "compilador", "compilateur", "Compiler", ["compila", "transforma", "gera"], ["codigo", "otimizacao", "executavel"]),
    },
    "alimentos": {
        "chocolate": ("chocolate", "chocolate", "chocolat", "chocolat", "Schokolade", ["come", "derrete", "doce"], ["cacau", "leite", "doce"]),
        "cafe": ("cafe", "coffee", "cafe", "cafe", "Kaffee", ["bebe", "acorda", "prepara"], ["graos", "xicara", "amargo"]),
        "chá": ("cha", "tea", "te", "the", "Tee", ["bebe", "prepara", "aquece"], ["folhas", "agua quente", "relaxante"]),
        "vinho": ("vinho", "wine", "vino", "vin", "Wein", ["bebe", "envelhece", "produz"], ["uva", "garrafa", "alcool"]),
        "cevada": ("cevada", "barley", "cebada", "orge", "Gerste", ["cultiva", "usa", "fermenta"], ["cerveja", "graos", "malte"]),
        "trigo": ("trigo", "wheat", "trigo", "ble", "Weizen", ["cultiva", "colhe", "moi"], ["farinha", "pao", "graos"]),
        "milho": ("milho", "corn", "maiz", "mais", "Mais", ["cultiva", "colhe", "cozinha"], ["graos", "fubá", "pipoca"]),
        "tomate": ("tomate", "tomato", "tomate", "tomate", "Tomate", ["come", "cozinha", "corta"], ["vermelho", "salada", "molho"]),
        "queijo": ("queijo", "cheese", "queso", "fromage", "Käse", ["come", "matura", "faz"], ["leite", "fermentacao", "sabor"]),
        "arroz": ("arroz", "rice", "arroz", "riz", "Reis", ["cozinha", "come", "cultiva"], ["graos", "alimento", "base"]),
    },
    "arquitetura_construcao": {
        "edificio": ("edificio", "building", "edificio", "immeuble", "Gebäude", ["constroi", "abriga", "tem"], ["estrutura", "andar", "parede"]),
        "ponte": ("ponte", "bridge", "puente", "pont", "Brucke", ["conecta", "cruza", "sustenta"], ["rio", "estrada", "engenharia"]),
        "castelo": ("castelo", "castle", "castillo", "chateau", "Schloss", ["defende", "contem", "construiu"], ["muro", "torre", "realeza"]),
        "catedral": ("catedral", "cathedral", "catedral", "cathedrale", "Kathedrale", ["abriga", "ensina", "contem"], ["igreja", "arte", "comunidade"]),
        "casa": ("casa", "house", "casa", "maison", "Haus", ["abriga", "morar", "tem"], ["quarto", "cozinha", "jardim"]),
        "estrada": ("estrada", "road", "carretera", "route", "Strasse", ["conecta", "cruza", "leva"], ["asfalto", "trafego", "distancia"]),
        "porto": ("porto", "port", "puerto", "port", "Hafen", ["recebe", "descarrega", "conecta"], ["navio", "carga", "agua"]),
        "aeroporto": ("aeroporto", "airport", "aeropuerto", "aeroport", "Flughafen", ["recebe", "parte", "conecta"], ["avião", "pista", "terminal"]),
        "estadio": ("estadio", "stadium", "estadio", "stade", "Stadion", ["recebe", "contem", "sedia"], ["torcida", "esporte", "campo"]),
        "monumento": ("monumento", "monument", "monumento", "monument", "Denkmal", ["honra", "lembra", "representa"], ["historia", "cultura", "escultura"]),
    },
}


# ============================================================
# PARTE 2: BUSCA WIKIPEDIA 5 IDIOMAS
# ============================================================

def _buscar_extract_wiki(titulo: str, idioma: str, timeout: int = 15,
                         max_retries: int = 3) -> str:
    """Busca extract de artigo da Wikipedia via API REST com retry."""
    def _fetch(tit, retry=0):
        params = urllib.parse.urlencode({
            'action': 'query', 'titles': tit,
            'prop': 'extracts', 'explaintext': '1',
            'format': 'json', 'redirects': '1',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
                paginas = dados.get('query', {}).get('pages', {})
                for pid, pagina in paginas.items():
                    if pid == '-1':
                        return ''
                    return pagina.get('extract', '')
        except urllib.error.HTTPError as e:
            if e.code == 429 and retry < max_retries:
                time.sleep(5 * (retry + 1))
                return _fetch(tit, retry + 1)
            return ''
        except Exception:
            return ''

    result = _fetch(titulo)
    if result:
        return result

    time.sleep(0.1)
    try:
        params = urllib.parse.urlencode({
            'action': 'query', 'list': 'search',
            'srsearch': titulo, 'srlimit': '1', 'format': 'json',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            if resultados:
                titulo_real = resultados[0].get('title', '')
                if titulo_real:
                    time.sleep(0.1)
                    return _fetch(titulo_real)
    except Exception:
        pass
    return ''


def _extrair_frases(texto: str, min_pal: int = 5, max_pal: int = 50) -> list:
    """Extrai frases do texto, filtra por tamanho."""
    texto = re.sub(r'\[[^\]]*\]', '', texto)
    frases = re.split(r'[.\n;!]+', texto)
    resultado = []
    for f in frases:
        f = f.strip()
        if not f:
            continue
        palavras = f.split()
        if min_pal <= len(palavras) <= max_pal:
            resultado.append(f.lower())
    return resultado


def _cache_path(cache_dir: str, idioma: str, titulo: str) -> str:
    """Gera path de cache seguro para titulo com caracteres especiais."""
    safe = re.sub(r'[^\w\-]', '_', titulo)[:80]
    return os.path.join(cache_dir, f'{idioma}_{safe}.txt')


def _fetch_one_artigo(titulo_cid_idioma_cache):
    """Worker para buscar 1 artigo Wikipedia (sequencial, com search fallback).

    Returns: (frases_list, cid) ou (None, cid) se falhar.
    """
    titulo, cid, idioma, cache_dir = titulo_cid_idioma_cache
    if not titulo:
        return None, cid

    cache_file = _cache_path(cache_dir, idioma, titulo)

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            frases = [line.strip() for line in f if line.strip()]
        if frases:
            return frases[:500], cid

    extract = _buscar_extract_wiki(titulo, idioma)
    if not extract:
        return None, cid

    frases = _extrair_frases(extract)
    if not frases:
        return None, cid

    with open(cache_file, 'w', encoding='utf-8') as f:
        for fr in frases:
            f.write(fr + '\n')

    return frases[:500], cid


def _batch_wikipedia(titulos_cids: list, idioma: str,
                     cache_dir: str, batch_size: int = 50,
                     delay: float = 2.0) -> list:
    """Busca artigos Wikipedia — batch titles=A|B|C (50 por request).

    SEM fallback individual para evitar rate limit (HTTP 429).
    Artigos nao encontrados (pid=-1) sao simplesmente pulados.
    240 artigos / 50 = 5 batches por idioma, 2s entre batches = ~10s.

    Returns: List[(frase, cid)]
    """
    corpus = []
    total = len(titulos_cids)
    n_cache = 0
    n_batch = 0
    n_fail = 0

    # 1. Ler cache existente
    para_fetch = []
    for titulo, cid in titulos_cids:
        if not titulo:
            continue
        cache_file = _cache_path(cache_dir, idioma, titulo)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                frases = [line.strip() for line in f if line.strip()]
            if frases:
                for fr in frases[:500]:
                    corpus.append((fr, cid))
                n_cache += 1
            else:
                para_fetch.append((titulo, cid))
        else:
            para_fetch.append((titulo, cid))

    if not para_fetch:
        print(f'    {total}/{total} ({n_cache} cache, 0 fetch)')
        return corpus

    print(f'    Cache: {n_cache}, fetch: {len(para_fetch)} ({len(para_fetch) // batch_size + 1} batches)')

    # 2. Batch titles= (50 por request) — SEM fallback individual
    for start in range(0, len(para_fetch), batch_size):
        batch = para_fetch[start:start + batch_size]
        titulos_str = '|'.join(t for t, _ in batch)

        params = urllib.parse.urlencode({
            'action': 'query',
            'titles': titulos_str,
            'prop': 'extracts',
            'explaintext': '1',
            'format': 'json',
            'redirects': '1',
        })
        url = f'https://{idioma}.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f'    Rate limit (429) no batch {start//batch_size+1}, esperando 30s...')
                time.sleep(30)
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        dados = json.loads(resp.read().decode('utf-8'))
                except Exception:
                    n_fail += len(batch)
                    continue
            else:
                n_fail += len(batch)
                time.sleep(delay)
                continue
        except Exception:
            n_fail += len(batch)
            time.sleep(delay)
            continue

        pages = dados.get('query', {}).get('pages', {})
        title_to_extract = {}
        for pid, pagina in pages.items():
            if pid == '-1':
                continue
            title = pagina.get('title', '')
            extract = pagina.get('extract', '')
            if extract:
                title_to_extract[title.lower()] = extract

        for titulo, cid in batch:
            cache_file = _cache_path(cache_dir, idioma, titulo)
            extract = title_to_extract.get(titulo.lower())
            if not extract:
                for t_key in title_to_extract:
                    if titulo.lower() in t_key or t_key in titulo.lower():
                        extract = title_to_extract[t_key]
                        break

            if not extract:
                n_fail += 1
                continue

            frases = _extrair_frases(extract)
            if not frases:
                n_fail += 1
                continue

            with open(cache_file, 'w', encoding='utf-8') as f:
                for fr in frases:
                    f.write(fr + '\n')
            for fr in frases[:500]:
                corpus.append((fr, cid))
            n_batch += 1

        batch_num = start // batch_size + 1
        total_batches = (len(para_fetch) + batch_size - 1) // batch_size
        print(f'    Batch {batch_num}/{total_batches}: +{n_batch} artigos')
        time.sleep(delay)

    print(f'    {total}/{total} ({n_cache} cache, {n_batch} batch, {n_fail} fail)')
    return corpus


def buscar_wikipedia_5idiomas(conceitos_novos: dict = None,
                               idiomas: list = None,
                               max_frases_por_artigo: int = 500,
                               cache_dir: str = None,
                               cache_only: bool = False,
                               n_threads: int = 1) -> list:
    """Busca Wikipedia em 5 idiomas — batch titles= + fallback search.

    Estrategia sem ThreadPoolExecutor (evita HTTP 429):
      1. Cache existente: instantaneo
      2. Batch titles=A|B|C (50 por request, 0.5s entre batches)
      3. Search individual (1s entre cada) para os que falharam

    Returns: List[Tuple[str, str]] — (frase, cid)
    """
    from tools.corpus_multilingue import CONCEITOS

    if idiomas is None:
        idiomas = ['pt', 'en', 'es', 'fr', 'de']
    if cache_dir is None:
        cache_dir = os.path.join(CACHE_DIR, 'wiki_5')
    os.makedirs(cache_dir, exist_ok=True)

    if conceitos_novos is None:
        conceitos_novos = CONCEITOS_NOVOS

    all_concepts = []
    idioma_idx = {'pt': 0, 'en': 1, 'es': 2, 'fr': 3, 'de': 4}

    for dominio, cid_map in conceitos_novos.items():
        for cid, dados in cid_map.items():
            all_concepts.append((cid, dados))

    for dominio, cid_map in CONCEITOS.items():
        for cid, dados in cid_map.items():
            all_concepts.append((cid, dados))

    print(f'  Wikipedia batch: {len(all_concepts)} conceitos x {len(idiomas)} idiomas')
    print(f'  ~{len(all_concepts) * len(idiomas) // 50} batches de 50')

    corpus = []

    for idioma in idiomas:
        titulos_cids = []
        for cid, dados in all_concepts:
            if isinstance(dados, dict):
                titulo = dados.get(idioma, dados.get('en', ''))
            elif isinstance(dados, tuple):
                idx = idioma_idx.get(idioma, 1)
                titulo = dados[idx] if idx < len(dados) else dados[1]
            else:
                continue
            if titulo:
                titulos_cids.append((titulo, cid))

        print(f'\n  Idioma {idioma}: {len(titulos_cids)} titulos')
        t0 = time.time()
        corpus_idioma = _batch_wikipedia(
            titulos_cids, idioma, cache_dir,
            batch_size=50, delay=0.5,
        )
        elapsed = time.time() - t0
        corpus.extend(corpus_idioma)
        print(f'  {idioma}: {len(corpus_idioma)} frases em {elapsed:.1f}s')

    return corpus


# ============================================================
# PARTE 3: BUSCA ROSETTA CODE (cross-language code)
# ============================================================

ROSETTA_TASKS = [
    "Sorting algorithms/Quicksort",
    "Sorting algorithms/Bubble sort",
    "Sorting algorithms/Merge sort",
    "99 Bottles of Beer",
    "Fibonacci sequence",
    "Factorial",
    "Palindrome detection",
    "String repetition",
    "Reverse a string",
    "Sum of a series",
    "Arithmetic-geometric mean",
    "Hello world/Text",
    "Hello world/Graphical",
    "Hello world/Standard error",
    "Hello world/Standard output",
    "Hello world/CommandLine",
    "FizzBuzz",
    "Leap year",
    "Roman numerals/Encode",
    "Roman numerals/Decode",
    "Greatest common divisor",
    "Least common multiple",
    "Binary search",
    "Linear search",
    "Bubble sort",
    "Selection sort",
    "Insertion sort",
    "Sieve of Eratosthenes",
    "Abundant, deficient and perfect number",
    "Ackermann function",
    "Hailstone sequence",
    "Happy numbers",
    "Knight's tour",
    "N-queens problem",
    "Pascal's triangle",
    "Power set",
    "Pythagorean theorem",
    "Tower of Hanoi",
    "Vigenere cipher",
]

ROSETTA_LANGUAGES = ["Python", "JavaScript", "Java", "C", "C++", "Rust", "Go", "Ruby", "PHP", "Haskell", "Kotlin", "Swift"]

def buscar_rosetta_code(tasks: list = None,
                        languages: list = None,
                        cache_dir: str = None,
                        cache_only: bool = False) -> list:
    """Busca codigos de Rosetta Code em multiplas linguagens.

    Usa action=parse para buscar pagina inteira (todas linguagens juntas).
    Extrai bloco <pre> de cada linguagem via h2 id="LanguageName".
    Uma request HTTP por task — muito mais eficiente.

    Returns: List[Tuple[str, str]] — (frase_do_codigo, cid_do_algoritmo)
    """
    if tasks is None:
        tasks = ROSETTA_TASKS
    if languages is None:
        languages = ROSETTA_LANGUAGES
    if cache_dir is None:
        cache_dir = os.path.join(CACHE_DIR, 'rosetta')
    os.makedirs(cache_dir, exist_ok=True)

    lang_set = set(languages)
    corpus = []
    n_found = 0
    print(f'  Rosetta Code: {len(tasks)} tasks x {len(languages)} linguagens (action=parse)')

    for idx, task in enumerate(tasks):
        cid = re.sub(r'[^a-z0-9]+', '_', task.lower()).strip('_')

        cache_file = os.path.join(cache_dir, f'{cid}_all.json')

        if os.path.exists(cache_file) and cache_only:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            for lang, code in cache_data.items():
                if lang in lang_set and code:
                    frases = _extrair_frases(code, min_pal=3, max_pal=100)
                    for fr in frases:
                        corpus.append((fr, cid))
                        n_found += 1
            continue

        if not os.path.exists(cache_file) and not cache_only:
            params = urllib.parse.urlencode({
                'action': 'parse',
                'page': task,
                'prop': 'text',
                'format': 'json',
            })
            url = f'https://rosettacode.org/w/api.php?{params}'
            req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    dados = json.loads(resp.read().decode('utf-8'))
                    if 'error' in dados:
                        continue
                    page_text = dados.get('parse', {}).get('text', {}).get('*', '')
            except Exception:
                time.sleep(2)
                continue

            h2_pattern = re.compile(r'<h2 id="([^"]+)"')
            headers = list(h2_pattern.finditer(page_text))

            cache_data = {}
            for m in headers:
                lang_name = m.group(1).replace('_', ' ')
                chunk = page_text[m.start():m.start() + 30000]
                pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', chunk, re.DOTALL)
                if pre_match:
                    code = re.sub(r'<[^>]+>', '', pre_match.group(1))
                    code = html_mod.unescape(code).strip()
                    cache_data[lang_name] = code

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)

            time.sleep(1.5)
        elif os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        else:
            continue

        for lang, code in cache_data.items():
            if lang in lang_set and code:
                frases = _extrair_frases(code, min_pal=3, max_pal=100)
                for fr in frases:
                    corpus.append((fr, cid))
                    n_found += 1

        if (idx + 1) % 10 == 0 or idx + 1 == len(tasks):
            print(f'    {idx + 1}/{len(tasks)} tasks, {n_found} frases ate agora')

    return corpus


# ============================================================
# PARTE 4: BUSCA PROJECT GUTENBERG (livros classicos)
# ============================================================

GUTENBERG_LIVROS = [
    (1342, "Pride and Prejudice", "en"),
    (84, "Frankenstein", "en"),
    (11, "Alice's Adventures in Wonderland", "en"),
    (1661, "The Adventures of Sherlock Holmes", "en"),
    (74, "The Adventures of Tom Sawyer", "en"),
    (2701, "Moby Dick", "en"),
    (174, "The Picture of Dorian Gray", "en"),
    (98, "A Tale of Two Cities", "en"),
    (57721, "Dom Casmurro", "pt"),
    (57659, "O Cortico", "pt"),
    (57708, "Memorias Postumas de Bras Cubas", "pt"),
    (57564, "Senhora", "pt"),
    (57630, "Quincas Borba", "pt"),
    (42889, "O Alienista", "pt"),
    (57595, "A Morte e a Morte de Quincas Borba", "pt"),
    (24308, "Don Quijote de la Mancha", "es"),
    (2000, "Cien años de soledad", "es"),
    (486, "Les Miserables", "fr"),
    (2451, "Les Trois Mousquetaires", "fr"),
    (1740, "Les Aventures de Telemaque", "fr"),
    (1232, "Madame Bovary", "fr"),
    (219, "Emma", "en"),
    (345, "Dracula", "en"),
    (16328, "Beowulf", "en"),
    (1952, "The Yellow Wallpaper", "en"),
    (514, "A Christmas Carol", "en"),
    (2554, "War and Peace", "en"),
    (1184, "The Count of Monte Cristo", "en"),
    (36033, "Die Verwandlung (The Metamorphosis)", "de"),
    (1727, "Faust", "de"),
    (45833, "Romeo und Julia", "de"),
    (2544, "The Brothers Karamazov", "en"),
    (161, "Crime and Punishment", "en"),
    (2600, "The Art of War", "en"),
    (308, "The Time Machine", "en"),
    (36, "The War of the Worlds", "en"),
]

def _buscar_gutenberg_text(book_id: int, timeout: int = 30) -> str:
    """Busca texto puro de um livro do Project Gutenberg."""
    url = f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt'
    req = urllib.request.Request(url, headers={'User-Agent': 'MCR/1.0 (research)'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            text = raw.decode('utf-8', errors='replace')
            start_markers = ['*** START OF', '*** START THE', '***START']
            for marker in start_markers:
                idx = text.find(marker)
                if idx >= 0:
                    text = text[idx:]
                    lines = text.split('\n')
                    start_line = next((i for i, l in enumerate(lines)
                                       if l.strip() == '' or i > 2), 3)
                    text = '\n'.join(lines[start_line:])
                    break
            end_markers = ['*** END OF', '*** END THE', '***END']
            for marker in end_markers:
                idx = text.find(marker)
                if idx >= 0:
                    text = text[:idx]
            return text
    except Exception:
        return ''


def buscar_gutenberg(livros: list = None,
                     cache_dir: str = None,
                     cache_only: bool = False) -> list:
    """Busca livros classicos do Project Gutenberg.

    Cada livro gera centenas de frases de literatura real.
    O acao e o concept_id do titulo normalizado.

    Returns: List[Tuple[str, str]] — (frase, cid_do_livro)
    """
    if livros is None:
        livros = GUTENBERG_LIVROS
    if cache_dir is None:
        cache_dir = os.path.join(CACHE_DIR, 'gutenberg')
    os.makedirs(cache_dir, exist_ok=True)

    corpus = []
    print(f'  Gutenberg: {len(livros)} livros classicos')

    for idx, (book_id, titulo, idioma) in enumerate(livros):
        cid = re.sub(r'[^a-z0-9]+', '_', titulo.lower()).strip('_')
        cache_file = os.path.join(cache_dir, f'{cid}_{idioma}.txt')

        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                frases = [line.strip() for line in f if line.strip()]
        elif cache_only:
            continue
        else:
            text = _buscar_gutenberg_text(book_id)
            if not text or len(text) < 1000:
                print(f'    FALHA: {titulo} (id={book_id})')
                continue
            frases = _extrair_frases(text, min_pal=5, max_pal=60)
            if not frases:
                continue
            with open(cache_file, 'w', encoding='utf-8') as f:
                for fr in frases:
                    f.write(fr + '\n')
            print(f'    OK: {titulo} ({idioma}) — {len(frases)} frases')
            time.sleep(1)

        for fr in frases:
            corpus.append((fr, cid))

        if (idx + 1) % 10 == 0 or idx + 1 == len(livros):
            print(f'    {idx + 1}/{len(livros)} livros processados')

    return corpus


# ============================================================
# PARTE 5: UNIFICACAO + MAIN
# ============================================================

def buscar_tudo(cache_only: bool = False,
                expandir_wiki: bool = True,
                expandir_rosetta: bool = True,
                expandir_gutenberg: bool = True) -> list:
    """Busca corpus de todas as fontes e junta.

    Args:
        cache_only: se True, so usa artigos ja em cache
        expandir_wiki: incluir Wikipedia 5 idiomas (300+ conceitos)
        expandir_rosetta: incluir Rosetta Code (cross-language code)
        expandir_gutenberg: incluir Project Gutenberg (livros classicos)
    Returns: List[Tuple[str, str]] — corpus unificado
    """
    corpus_total = []

    if expandir_wiki:
        print('\n[1/3] Wikipedia 5 idiomas...')
        corpus_wiki = buscar_wikipedia_5idiomas(cache_only=cache_only)
        corpus_total.extend(corpus_wiki)
        print(f'  Total Wikipedia: {len(corpus_wiki)} frases')

    if expandir_rosetta:
        print('\n[2/3] Rosetta Code (cross-language code)...')
        corpus_rosetta = buscar_rosetta_code(cache_only=cache_only)
        corpus_total.extend(corpus_rosetta)
        print(f'  Total Rosetta Code: {len(corpus_rosetta)} frases')

    if expandir_gutenberg:
        print('\n[3/3] Project Gutenberg (livros classicos)...')
        corpus_gutenberg = buscar_gutenberg(cache_only=cache_only)
        corpus_total.extend(corpus_gutenberg)
        print(f'  Total Gutenberg: {len(corpus_gutenberg)} frases')

    print(f'\n{"="*60}')
    print(f'CORPUS TOTAL: {len(corpus_total)} frases')
    print(f'{"="*60}')

    return corpus_total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Corpus massivo multi-fonte')
    parser.add_argument('--cache-only', action='store_true',
                        help='So usa cache existente (sem HTTP)')
    parser.add_argument('--no-rosetta', action='store_true')
    parser.add_argument('--no-gutenberg', action='store_true')
    parser.add_argument('--no-wiki', action='store_true')
    parser.add_argument('--only-wiki', action='store_true')
    parser.add_argument('--only-rosetta', action='store_true')
    parser.add_argument('--only-gutenberg', action='store_true')
    args = parser.parse_args()

    corpus = buscar_tudo(
        cache_only=args.cache_only,
        expandir_wiki=not args.no_wiki and not args.only_rosetta and not args.only_gutenberg,
        expandir_rosetta=not args.no_rosetta and not args.only_wiki and not args.only_gutenberg,
        expandir_gutenberg=not args.no_gutenberg and not args.only_wiki and not args.only_rosetta,
    )

    print(f'\nAmostra:')
    for fr, cid in corpus[:10]:
        print(f'  [{cid}] {fr[:80]}...')
