"""mcr.mcr_world_chronicle — Cronica do Mundo (World Chronicle).
Memoria narrativa persistente do MCR. Cada evento, nascimento de NPC,
mudanca de estado, guerra ou paz fica registrado aqui."""
import json
import time
from datetime import datetime
from mcr.paths import DEVIA_DIR

CHRONICLE_FILE = DEVIA_DIR / "world_chronicle.md"


def generate_chronicle(seed: dict) -> str:
    """Gera narracao epica a partir do WorldSeed usando mistral:7b."""
    import urllib.request
    OLLAMA_CHAT = "http://localhost:11434/api/generate"
    MODELO_LORE = "mistral:7b"

    seed_json = json.dumps(seed, indent=2, ensure_ascii=False)
    prompt = (
        "Abaixo esta o WorldSeed (a fundacao de um mundo de RPG).\n"
        "Escreva um texto de cronica de mundo no estilo de um narrador epico, "
        "estruturado em secoes: Preludio, Geografia, Personagens, Conflitos, Estado Atual.\n"
        "Use Markdown. Nao invente fatos que nao estao no WorldSeed.\n\n"
        "=== WORLDSEED ===\n%s\n\n=== CRONICA ===" % seed_json
    )
    try:
        payload = json.dumps({
            "model": MODELO_LORE, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.7, "max_tokens": 1500}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        texto = resp.get('response', '').strip()
        return texto or "[Cronica nao gerada]"
    except Exception as e:
        return "[Erro ao gerar cronica: %s]" % e


def append_chronicle(text: str, metadata: dict = None):
    """Adiciona entrada ao final do arquivo de cronica."""
    CHRONICLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bloco = "\n## [%s] Evento\n%s\n" % (timestamp, text)
    if metadata:
        bloco += "\n_(Metadados: %s)_\n" % json.dumps(metadata, ensure_ascii=False)
    if CHRONICLE_FILE.exists():
        with open(CHRONICLE_FILE, 'r', encoding='utf-8') as f:
            existente = f.read()
    else:
        existente = "# Cronica do Mundo\n\n*Memoria narrativa do MCR-DevIA*\n"
    with open(CHRONICLE_FILE, 'w', encoding='utf-8') as f:
        f.write(existente + bloco)


def get_chronicle(ultimas: int = 5) -> str:
    """Retorna as ultimas N entradas da cronica."""
    if not CHRONICLE_FILE.exists():
        return "[Cronica vazia]"
    with open(CHRONICLE_FILE, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    blocos = conteudo.split("\n## [")
    if len(blocos) <= 1:
        return conteudo[:500]
    # Pega os ultimos N blocos (ignora cabecalho)
    relevantes = blocos[-(ultimas + 1):]
    return "\n## [".join(relevantes)
