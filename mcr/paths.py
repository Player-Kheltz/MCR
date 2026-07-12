"""mcr.paths — Centraliza TODOS os caminhos do ecossistema MCR.
Nenhuma outra parte do codigo deve usar strings de caminho hardcodadas."""
from pathlib import Path

# ─── Raiz do projeto (E:\MCR) ─────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ─── Servidor (Canary) ─────────────────────────────────────────
SERVER_DIR = ROOT_DIR / "server"
CANARY_SRC_DIR = SERVER_DIR / "src"
CANARY_BUILD_DIR = SERVER_DIR / "build"
CANARY_DATA_DIR = SERVER_DIR / "data"
CANARY_SCRIPTS_DIR = CANARY_DATA_DIR / "scripts"
CANARY_NPC_DIR = SERVER_DIR / "data-otservbr-global" / "npc"
CANARY_MONSTER_DIR = SERVER_DIR / "data-otservbr-global" / "monster"
CANARY_ITEMS_XML = CANARY_DATA_DIR / "items" / "items.xml"
CANARY_CONFIG = SERVER_DIR / "config.lua"

# ─── Cliente (OTClient) ────────────────────────────────────────
CLIENT_DIR = ROOT_DIR / "client"
CLIENT_SRC_DIR = CLIENT_DIR / "src"
CLIENT_BUILD_DIR = CLIENT_DIR / "build"

# ─── DevIA ──────────────────────────────────────────────────────
DEVIA_DIR = ROOT_DIR / "devia"
DEVIA_KERNEL_DIR = DEVIA_DIR / "kernel"
DEVIA_MODULES_DIR = DEVIA_DIR / "modules"
DEVIA_COMANDOS_DIR = DEVIA_DIR / "comandos"
DEVIA_KNOWLEDGE_DIR = DEVIA_DIR / "knowledge"
DEVIA_ANALYSIS_DIR = DEVIA_DIR / "analysis"
DEVIA_TESTS_DIR = DEVIA_DIR / "tests"
DEVIA_DATA_DIR = DEVIA_DIR / "data"
MCR_PY = DEVIA_KERNEL_DIR / "MCR.py"

# ─── Knowledge Graph ────────────────────────────────────────────
KG_DIR = DEVIA_KNOWLEDGE_DIR

# ─── Dados gerados ──────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
CACHE_DIR = ROOT_DIR / "cache"
SCRIPTS_GENERATED_DIR = ROOT_DIR / ".." / "Projeto MCR" / "scripts" / "generated"
SCRIPTS_QUARANTINE_DIR = ROOT_DIR / ".." / "Projeto MCR" / "scripts" / "quarantine"

# ─── Golden Examples (templates anti-alucinacao) ────────────────
GOLDEN_EXAMPLES_DIR = ROOT_DIR / "golden_examples"

# ─── Documentacao ───────────────────────────────────────────────
DOCS_DIR = ROOT_DIR / "docs"
LORE_DIR = DOCS_DIR / "lore"

# ─── Ferramentas ────────────────────────────────────────────────
TOOLS_DIR = ROOT_DIR / "tools"
GRIMORIO_DIR = TOOLS_DIR / "grimorio"
LOGIN_SERVER_DIR = TOOLS_DIR / "login-server"
MAP_EDITOR_DIR = TOOLS_DIR / "map-editor"

# ─── Prototipos (antigo E:\Coisas) ─────────────────────────────
PROTOTYPES_DIR = ROOT_DIR / "prototypes"
SANDBOX_DIR = PROTOTYPES_DIR / "sandbox"

# ─── FASE 6: Motor de Criatividade ────────────────────────────
SANDBOX_CRIATIVO_DIR = ROOT_DIR / "sandbox_criativo"
IDEAS_DIR = ROOT_DIR / "ideas_que_funcionaram"

# ─── Scripts auxiliares ─────────────────────────────────────────
SCRIPTS_DIR = ROOT_DIR / "scripts"

# ─── Cache do MarkovRouter ─────────────────────────────────────
ROUTER_CACHE = CACHE_DIR / "router_markov.json"

# ─── POC Output ────────────────────────────────────────────────
POC_OUTPUT_DIR = ROOT_DIR / "poc_output"


def ensure_dirs():
    """Garante que os diretorios essenciais existam."""
    for d in [
        DEVIA_DIR, DEVIA_KERNEL_DIR, DEVIA_MODULES_DIR, DEVIA_COMANDOS_DIR,
        DEVIA_KNOWLEDGE_DIR, DEVIA_ANALYSIS_DIR, DEVIA_TESTS_DIR, DEVIA_DATA_DIR,
        DATA_DIR, GENERATED_DIR, CACHE_DIR, SCRIPTS_DIR, DOCS_DIR,
        LORE_DIR, PROTOTYPES_DIR, SANDBOX_DIR,
        SANDBOX_CRIATIVO_DIR, IDEAS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
