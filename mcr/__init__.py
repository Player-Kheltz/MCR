# mcr — Pacote fundamental do ecossistema MCR-DevIA
from mcr.paths import (
    ROOT_DIR, SERVER_DIR, CANARY_SRC_DIR, CANARY_SCRIPTS_DIR,
    CANARY_DATA_DIR, CANARY_NPC_DIR, CANARY_MONSTER_DIR, CANARY_ITEMS_XML,
    CLIENT_DIR, DEVIA_DIR, DEVIA_KERNEL_DIR, DEVIA_MODULES_DIR,
    DEVIA_COMANDOS_DIR, DEVIA_KNOWLEDGE_DIR,
    KG_DIR, DATA_DIR, GENERATED_DIR, CACHE_DIR,
    SCRIPTS_GENERATED_DIR, SCRIPTS_QUARANTINE_DIR,
    GOLDEN_EXAMPLES_DIR, DOCS_DIR, LORE_DIR,
    TOOLS_DIR, GRIMORIO_DIR, LOGIN_SERVER_DIR, MAP_EDITOR_DIR,
    PROTOTYPES_DIR, SANDBOX_DIR, SCRIPTS_DIR,
    SANDBOX_CRIATIVO_DIR, IDEAS_DIR,
    ROUTER_CACHE, MCR_PY,
    ensure_dirs,
)
from mcr.encoding import read_file, write_file, read_lines, write_lines

# ─── Backends Markov ───────────────────────────────────────
from mcr.mcr_sqlite import MCRSQLite
from mcr.sqlite_markov import SQLiteMarkov

# ─── Pipeline Conectado ────────────────────────────────────
from mcr.adaptadores import PipelineConectado, acoes_para_tarefas, intencao_para_classe

# ─── Criatividade ──────────────────────────────────────────
from mcr.emergir_unificado import EmergirUnificado

# ─── Geração ───────────────────────────────────────────────
from mcr.gerador_codigo import GeradorCodigo
from mcr.npc_criativo import NPCCriativo
from mcr.raciocinador import Raciocinador
from mcr.generator_multinivel import GeradorMultinivel

# ─── Mente / Consciência ───────────────────────────────────
from mcr.mcr_mente_pura import MCRMentePura
from mcr.mcr_mente import MCRMente
from mcr.internal_monologue import InternalMonologue
from mcr.mcr_self import MCRSelf
from mcr.mcr_autobiography import Autobiography

# ─── Auto-Análise / Evolução ───────────────────────────────
from mcr.metacognicao import Metacognicao
from mcr.mcr_auto_evolution import MCRAutoEvolution
from mcr.auto_curiosidade import AutoCuriosidade
from mcr.cache_hierarquico import CacheHierarquico

# ─── Mundo / Diálogo ───────────────────────────────────────
from mcr.mcr_world_system import MCRWorldSystem
from mcr.dialogue_trainer import DialogueTrainer
from mcr.planejador import Planejador

# ─── COGNIÇÃO UNIFICADA (PRINCIPAL) ─────────────────────────
from mcr.mcr import MCR, get_mcr

# ─── Pipeline Unificado (legado) ────────────────────────────
# Usar diretamente: from mcr.registry import get_registry
