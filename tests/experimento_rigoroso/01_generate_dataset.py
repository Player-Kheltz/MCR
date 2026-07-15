"""01: Gera dataset de 500 entradas anotadas para o experimento."""
import json
import random
import sys
sys.path.insert(0, 'E:/MCR')

random.seed(42)

dataset = []
idx = 0

# ─── LISTAS DE DADOS ────────────────────────────────────────
npc_profissoes = [
    "ferreiro", "mago", "guarda", "vendedor", "mercador", "padeiro",
    "taverneiro", "cavaleiro", "alquimista", "druida", "arqueiro",
    "artesao", "carpinteiro", "mendigo", "mensageiro", "bibliotecario",
    "cozinheiro", "tecelao", "minerador", "ladrao", "sacerdote",
    "mestre de armas", "instructer", "guia", "curandeiro",
]
npc_racas = ["anao", "elfico", "humano", "orc", "gnomo", "halfling", "draconiano"]
npc_items = ["espadas", "escudos", "pocoes", "armaduras", "anel", "chapeu", "botas", "varinhas"]
npc_extras = [
    "tem uma quest secreta", "conhece o rei", "ja viajou o mundo",
    "tem um passado misterioso", "odeia monstros", "ama ouro",
    "coleta ervas raras", "fabula armas unicas",
]

monstro_tipos = [
    "dragao", "lobo", "demonio", "orc", "esqueleto", "ciclope",
    "golem", "vampiro", "serpente", "elemental", "goblin", "troll",
    "aranha", "urso", "fantasma", "bruxa", "minotauro", "medusa",
    "grifo", "hidra", "phoenix", "wraith", "lich", "behemoth",
]
monstro_modificadores = [
    "de fogo", "de gelo", "sombrio", "anciao", "menor", "selvagem",
    "gigante", "pequeno", "selvagem", "corrompido", "antigo",
    "de lava", "de tempestade", "nebuloso", "venenoso",
]
monstro_perigos = ["perigoso", "mortal", "lendario", "mitico", "fraco", "medio", "forte"]

responder_topics_pt = [
    ("o que e entropia", ["entropia", "shannon", "informacao"]),
    ("como funciona o Markov", ["markov", "transicao", "probabilidade"]),
    ("o que e um NPC", ["npc", "personagem", "jogo"]),
    ("explique a equacao MCR", ["equacao", "sigmoide", "cincodimensional"]),
    ("o que e fingerprint", ["fingerprint", "hash", "64d"]),
    ("como o MCR aprende", ["aprendizado", "markov", "reforco"]),
    ("o que e cluster", ["cluster", "agrupamento", "similaridade"]),
    ("explique Shannon", ["shannon", "entropia", "bits"]),
    ("o que e PID", ["pid", "processo", "identificador"]),
    ("como funciona Lua", ["lua", "script", "codigo"]),
    ("o que e Canary", ["canary", "servidor", "tibia"]),
    ("diferenca entre Markov e LLM", ["markov", "llm", "probabilidade"]),
    ("o que e TKK", ["tkk", "servidor", "tibia"]),
    ("como criar um NPC", ["npc", "personagem", "criar"]),
    ("o que e looktype", ["looktype", "aparencia", "sprite"]),
]
responder_topics_en = [
    ("what is entropy", ["entropy", "shannon", "information"]),
    ("how does Markov work", ["markov", "transition", "probability"]),
    ("explain the MCR equation", ["equation", "sigmoid", "five"]),
    ("what is a fingerprint", ["fingerprint", "hash", "64d"]),
    ("how does MCR learn", ["learning", "markov", "reinforcement"]),
]
responder_unanswerable = [
    "qual e o preco do bitcoin hoje",
    "quem vai ganhar a copa do mundo",
    "qual e o sentido da vida",
    "qual e o melhor time do brasil",
    "quando vai acabar a pandemia",
    "qual e o numero da sorte",
    "previsao do tempo para amanha",
    "qual e a capital da mongolia",
]

sprite_items = [
    "espada", "escudo", "pocao", "armadura", "anel", "chapeu", "bota",
    "machado", "arco", "cajado", "livro", "chave", "anel", "mascara",
]
sprite_modificadores = [
    "de fogo", "de gelo", "dourada", "prateada", "envenenada",
    "lendaria", "antiga", "simples", "mágica", "escura",
]

# ─── GERAR NPC (175) ──────────────────────────────────────
# Simple (55)
for prof in random.sample(npc_profissoes, min(20, len(npc_profissoes))):
    dataset.append({
        "id": idx, "input": f"Crie um NPC {prof}",
        "expected_action": "gerar_npc", "language": "pt", "complexity": "simple",
        "semantic_fields": {"profession": prof, "race": None, "items": [], "has_shop": False},
    }); idx += 1
for prof in random.sample(npc_profissoes, min(15, len(npc_profissoes))):
    dataset.append({
        "id": idx, "input": f"Create an NPC {prof}",
        "expected_action": "gerar_npc", "language": "en", "complexity": "simple",
        "semantic_fields": {"profession": prof, "race": None, "items": [], "has_shop": False},
    }); idx += 1
for prof in random.sample(npc_profissoes, min(20, len(npc_profissoes))):
    dataset.append({
        "id": idx, "input": f"Gere um NPC {prof}",
        "expected_action": "gerar_npc", "language": "pt", "complexity": "simple",
        "semantic_fields": {"profession": prof, "race": None, "items": [], "has_shop": False},
    }); idx += 1

# Medium (60)
for prof in random.sample(npc_profissoes, min(20, len(npc_profissoes))):
    raca = random.choice(npc_racas)
    dataset.append({
        "id": idx, "input": f"Crie um NPC {prof} {raca}",
        "expected_action": "gerar_npc", "language": "pt", "complexity": "medium",
        "semantic_fields": {"profession": prof, "race": raca, "items": [], "has_shop": False},
    }); idx += 1
for prof in random.sample(npc_profissoes, min(20, len(npc_profissoes))):
    item = random.choice(npc_items)
    dataset.append({
        "id": idx, "input": f"Crie um NPC {prof} que vende {item}",
        "expected_action": "gerar_npc", "language": "pt", "complexity": "medium",
        "semantic_fields": {"profession": prof, "race": None, "items": [item], "has_shop": True},
    }); idx += 1
for prof in random.sample(npc_profissoes, min(20, len(npc_profissoes))):
    raca = random.choice(npc_racas)
    item = random.choice(npc_items)
    dataset.append({
        "id": idx, "input": f"Create a {raca} {prof} NPC that sells {item}",
        "expected_action": "gerar_npc", "language": "en", "complexity": "medium",
        "semantic_fields": {"profession": prof, "race": raca, "items": [item], "has_shop": True},
    }); idx += 1

# Complex (60)
for prof in random.sample(npc_profissoes, min(15, len(npc_profissoes))):
    raca = random.choice(npc_racas)
    item = random.choice(npc_items)
    extra = random.choice(npc_extras)
    dataset.append({
        "id": idx, "input": f"Crie um NPC {prof} {raca} que vende {item} e {extra}",
        "expected_action": "gerar_npc", "language": "pt", "complexity": "complex",
        "semantic_fields": {"profession": prof, "race": raca, "items": [item], "has_shop": True},
    }); idx += 1
for prof in random.sample(npc_profissoes, min(15, len(npc_profissoes))):
    raca = random.choice(npc_racas)
    item = random.choice(npc_items)
    extra = random.choice(npc_extras)
    dataset.append({
        "id": idx, "input": f"Build a {raca} {prof} NPC selling {item} who {extra}",
        "expected_action": "gerar_npc", "language": "en", "complexity": "complex",
        "semantic_fields": {"profession": prof, "race": raca, "items": [item], "has_shop": True},
    }); idx += 1
# Edge cases (30)
edge_npc = [
    "Crie um NPC", "NPC ferreiro", "faca npc", "crie um npc mago elfico que vende pocoes",
    "gere um NPC", "um npc", "npc", "ferreiro", "NPC com loja",
    "criar npc guard", "build npc", "make an npc",
    "crie um NPC dragao", "gere um NPC orc", "NPC NPC NPC",
    "crie um npc que nao existe", "npc muito legal", " npc ",
    "CRIE UM NPC FERREIRO", "create NPC", "npc npc",
    "crie um NPC que vende tudo", "NPC vende nada",
    "crie o npc ferreiro mais forte", "npc ferreiro anao velho",
    "ferreiro elfico que vende espadas lendarias e tem uma quest secreta",
    "mago orc que coleta ervas raras e conhece o rei",
    "vendedor humano misterioso com passado sombrio",
    "guarda gnomo que odeia monstros e protege a vila",
    "alquimista draconiano que fabula armas unicas",
]
for inp in edge_npc:
    dataset.append({
        "id": idx, "input": inp, "expected_action": "gerar_npc",
        "language": "pt", "complexity": "complex",
        "semantic_fields": {"profession": "unknown", "race": None, "items": [], "has_shop": False},
    }); idx += 1

# ─── GERAR MONSTRO (150) ─────────────────────────────────
# Simple (50)
for tipo in random.sample(monstro_tipos, min(25, len(monstro_tipos))):
    dataset.append({
        "id": idx, "input": f"Gere um monstro {tipo}",
        "expected_action": "gerar_monstro", "language": "pt", "complexity": "simple",
        "semantic_fields": {"creature_type": tipo, "modifier": None, "danger": "medium"},
    }); idx += 1
for tipo in random.sample(monstro_tipos, min(15, len(monstro_tipos))):
    dataset.append({
        "id": idx, "input": f"Generate a {tipo} monster",
        "expected_action": "gerar_monstro", "language": "en", "complexity": "simple",
        "semantic_fields": {"creature_type": tipo, "modifier": None, "danger": "medium"},
    }); idx += 1
for tipo in random.sample(monstro_tipos, min(10, len(monstro_tipos))):
    dataset.append({
        "id": idx, "input": f"Crie um monstro {tipo}",
        "expected_action": "gerar_monstro", "language": "pt", "complexity": "simple",
        "semantic_fields": {"creature_type": tipo, "modifier": None, "danger": "medium"},
    }); idx += 1

# Medium (50)
for tipo in random.sample(monstro_tipos, min(25, len(monstro_tipos))):
    mod = random.choice(monstro_modificadores)
    dataset.append({
        "id": idx, "input": f"Gere um monstro {tipo} {mod}",
        "expected_action": "gerar_monstro", "language": "pt", "complexity": "medium",
        "semantic_fields": {"creature_type": tipo, "modifier": mod, "danger": "medium"},
    }); idx += 1
for tipo in random.sample(monstro_tipos, min(15, len(monstro_tipos))):
    mod = random.choice(monstro_modificadores)
    dataset.append({
        "id": idx, "input": f"Generate a {mod} {tipo}",
        "expected_action": "gerar_monstro", "language": "en", "complexity": "medium",
        "semantic_fields": {"creature_type": tipo, "modifier": mod, "danger": "medium"},
    }); idx += 1
for tipo in random.sample(monstro_tipos, min(10, len(monstro_tipos))):
    perigo = random.choice(monstro_perigos)
    dataset.append({
        "id": idx, "input": f"Gere um monstro {tipo} {perigo}",
        "expected_action": "gerar_monstro", "language": "pt", "complexity": "medium",
        "semantic_fields": {"creature_type": tipo, "modifier": None, "danger": perigo},
    }); idx += 1

# Complex (50)
for tipo in random.sample(monstro_tipos, min(20, len(monstro_tipos))):
    mod = random.choice(monstro_modificadores)
    perigo = random.choice(monstro_perigos)
    dataset.append({
        "id": idx, "input": f"Gere um monstro {tipo} {mod} {perigo} com habilidades especiais",
        "expected_action": "gerar_monstro", "language": "pt", "complexity": "complex",
        "semantic_fields": {"creature_type": tipo, "modifier": mod, "danger": perigo},
    }); idx += 1
for tipo in random.sample(monstro_tipos, min(15, len(monstro_tipos))):
    mod = random.choice(monstro_modificadores)
    dataset.append({
        "id": idx, "input": f"Generate an ancient {mod} {tipo} that drops rare items",
        "expected_action": "gerar_monstro", "language": "en", "complexity": "complex",
        "semantic_fields": {"creature_type": tipo, "modifier": mod, "danger": "legendary"},
    }); idx += 1
# Edge cases (15)
edge_monstro = [
    "Gere um monstro", "monstro", "dragao", "gere um monstro que dropa ouro",
    "monstro perigoso", "crie um monstro", "generate monster",
    "um monstro muito forte", "monstro NPC", "gere monstro orc",
    "dragao de gelo anciao gigante", "lobo sombrio venenoso",
    "elemental de fogo menor", "demonio corrompido antigo",
    "fantasma wraith lich behemoth",
]
for inp in edge_monstro:
    dataset.append({
        "id": idx, "input": inp, "expected_action": "gerar_monstro",
        "language": "pt", "complexity": "complex",
        "semantic_fields": {"creature_type": "unknown", "modifier": None, "danger": "medium"},
    }); idx += 1

# ─── RESPONDER (125) ──────────────────────────────────────
# KG-answerable (55)
for topic, keywords in random.sample(responder_topics_pt, min(15, len(responder_topics_pt))):
    dataset.append({
        "id": idx, "input": topic,
        "expected_action": "responder", "language": "pt", "complexity": "simple",
        "semantic_fields": {"answerable": True, "topic": topic, "expected_keywords": keywords},
    }); idx += 1
for topic, keywords in random.sample(responder_topics_en, min(5, len(responder_topics_en))):
    dataset.append({
        "id": idx, "input": topic,
        "expected_action": "responder", "language": "en", "complexity": "simple",
        "semantic_fields": {"answerable": True, "topic": topic, "expected_keywords": keywords},
    }); idx += 1
for topic, keywords in random.sample(responder_topics_pt, min(15, len(responder_topics_pt))):
    dataset.append({
        "id": idx, "input": f"Explique {topic}",
        "expected_action": "responder", "language": "pt", "complexity": "medium",
        "semantic_fields": {"answerable": True, "topic": topic, "expected_keywords": keywords},
    }); idx += 1
for topic, keywords in random.sample(responder_topics_pt, min(10, len(responder_topics_pt))):
    dataset.append({
        "id": idx, "input": f"Como funciona {topic}",
        "expected_action": "responder", "language": "pt", "complexity": "medium",
        "semantic_fields": {"answerable": True, "topic": topic, "expected_keywords": keywords},
    }); idx += 1
for topic, keywords in random.sample(responder_topics_en, min(10, len(responder_topics_en))):
    dataset.append({
        "id": idx, "input": f"Explain {topic}",
        "expected_action": "responder", "language": "en", "complexity": "medium",
        "semantic_fields": {"answerable": True, "topic": topic, "expected_keywords": keywords},
    }); idx += 1

# Unanswerable (20)
for inp in random.sample(responder_unanswerable, min(10, len(responder_unanswerable))):
    dataset.append({
        "id": idx, "input": inp,
        "expected_action": "responder", "language": "pt", "complexity": "simple",
        "semantic_fields": {"answerable": False, "topic": "unknown", "expected_keywords": []},
    }); idx += 1
for inp in random.sample(responder_unanswerable, min(10, len(responder_unanswerable))):
    dataset.append({
        "id": idx, "input": f"Voce sabe {inp}",
        "expected_action": "responder", "language": "pt", "complexity": "medium",
        "semantic_fields": {"answerable": False, "topic": "unknown", "expected_keywords": []},
    }); idx += 1

# Complex reasoning (25)
complex_resp = [
    ("por que entropia diminui quando Markov aprende", ["entropia", "markov", "aprendizado"]),
    ("qual a diferenca entre entropia de Shannon e entropia de Tsallis", ["shannon", "tsallis", "diferenca"]),
    ("como o MCR decide qual ferramenta usar", ["mcr", "decidir", "ferramenta", "markov"]),
    ("por que a equacao usa sigmoide e nao linear", ["sigmoide", "equacao", "linear"]),
    ("como o fingerprint de 64 dimensoes funciona", ["fingerprint", "64", "dimensoes", "hash"]),
    ("qual a vantagem do Markov sobre LLM", ["markov", "llm", "vantagem", "rapido"]),
    ("como o KG e populado automaticamente", ["kg", "padroes", "mineracao"]),
    ("o que e clusterizacao e como funciona no MCR", ["cluster", "mcr", "similaridade"]),
    ("por que o MCR nao precisa de GPU", ["gpu", "mcr", "economico"]),
    ("como o observador universal aprende padroes", ["observador", "padroes", "aprendizado"]),
    ("qual a diferenca entre Markov de 1a e 2a ordem", ["markov", "ordem", "transicao"]),
    ("como o ShadowCanary evita erros", ["shadow", "canary", "erros", "penalidade"]),
    ("o que e auto-evolucao no MCR", ["auto-evolucao", "mcr", "mutacao"]),
    ("como o MCR valida codigo gerado", ["validacao", "codigo", "lua", "sanity"]),
    ("por que entropia e importante para cognicao", ["entropia", "cognicao", "informacao"]),
    ("como o DescobridorUniversal funciona", ["descobridor", "frequencia", "ancoras"]),
    ("qual a formula da equacao MCR", ["equacao", "formula", "sigmoide"]),
    ("como o MCR lida com dados que nunca viu", ["dados", "novos", "generalizacao"]),
    ("o que e Markov e por que funciona para decisoes", ["markov", "decisoes", "transicao"]),
    ("como o PatternMiner extrai padroes de codigo", ["pattern", "miner", "codigo", "ast"]),
    ("qual a diferenca entre Markov e Rede Neural", ["markov", "neural", "diferenca"]),
    ("como o MCR decide quando nao sabe", ["incerteza", "decisao", "fallback"]),
    ("por que o MCR e melhor que LLM para tarefas estruturadas", ["mcr", "llm", "estruturado"]),
    ("como o ExtratorFeatures descobre clusters", ["extrator", "clusters", "entropia"]),
    ("o que e auto-calibracao da equacao", ["auto-calibracao", "equacao", "pesos"]),
]
for inp, keywords in complex_resp:
    dataset.append({
        "id": idx, "input": inp,
        "expected_action": "responder", "language": "pt", "complexity": "complex",
        "semantic_fields": {"answerable": True, "topic": inp, "expected_keywords": keywords},
    }); idx += 1

# Ambiguous (25)
ambiguous = [
    "me fale sobre NPC", "NPC ferreiro", "dragao de fogo",
    "o que e um monstro", "como criar espada", "sprite de escudo",
    "explique monstro", "me conte sobre entropia", "ferreiro",
    "mago elfico", "monstro perigoso", "npc com loja",
    "criar codigo", "gerar texto", "responder pergunta",
    "espada dourada", "escudo de prata", "armadura de dragao",
    "pocao de vida", "anel magico", "chapeu de mago",
    "botas de velocidade", "machado de guerra", "arco encantado",
    "cajado druidico",
]
for inp in ambiguous:
    dataset.append({
        "id": idx, "input": inp,
        "expected_action": "responder", "language": "pt", "complexity": "medium",
        "semantic_fields": {"answerable": True, "topic": inp, "expected_keywords": []},
    }); idx += 1

# ─── GERAR SPRITE (50) ────────────────────────────────────
for item in random.sample(sprite_items, min(15, len(sprite_items))):
    dataset.append({
        "id": idx, "input": f"Crie um sprite de {item}",
        "expected_action": "gerar_sprite", "language": "pt", "complexity": "simple",
        "semantic_fields": {"item_type": item, "modifier": None},
    }); idx += 1
for item in random.sample(sprite_items, min(15, len(sprite_items))):
    mod = random.choice(sprite_modificadores)
    dataset.append({
        "id": idx, "input": f"Crie um sprite de {item} {mod}",
        "expected_action": "gerar_sprite", "language": "pt", "complexity": "medium",
        "semantic_fields": {"item_type": item, "modifier": mod},
    }); idx += 1
for item in random.sample(sprite_items, min(10, len(sprite_items))):
    mod = random.choice(sprite_modificadores)
    dataset.append({
        "id": idx, "input": f"Create a {mod} {item} sprite",
        "expected_action": "gerar_sprite", "language": "en", "complexity": "medium",
        "semantic_fields": {"item_type": item, "modifier": mod},
    }); idx += 1
edge_sprite = [
    "sprite", "crie um sprite", "sprite de espada dourada magica",
    "crie um sprite de NPC", "um sprite", "gerar sprite",
    "sprite armor", "criar sprite de escudo", "sprite pocao",
    "crie sprite de machado de guerra antigo",
]
for inp in edge_sprite:
    dataset.append({
        "id": idx, "input": inp, "expected_action": "gerar_sprite",
        "language": "pt", "complexity": "complex",
        "semantic_fields": {"item_type": "unknown", "modifier": None},
    }); idx += 1

# ─── EMBARALHAR ────────────────────────────────────────────
random.shuffle(dataset)
for i, entry in enumerate(dataset):
    entry['id'] = i + 1

# Remove duplicatas de input
seen = set()
unicos = []
for e in dataset:
    inp = e['input'].strip().lower()
    if inp not in seen:
        seen.add(inp)
        unicos.append(e)
dataset = unicos
for i, entry in enumerate(dataset):
    entry['id'] = i + 1

# ─── SALVAR ────────────────────────────────────────────────
output_path = 'E:/MCR/tests/experimento_rigoroso/dataset_500.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

# ─── STATS ─────────────────────────────────────────────────
from collections import Counter
actions = Counter(e['expected_action'] for e in dataset)
langs = Counter(e['language'] for e in dataset)
complexities = Counter(e['complexity'] for e in dataset)

print(f'Dataset gerado: {len(dataset)} entradas')
print(f'  Por acao: {dict(actions)}')
print(f'  Por idioma: {dict(langs)}')
print(f'  Por complexidade: {dict(complexities)}')
print(f'Salvo em: {output_path}')
