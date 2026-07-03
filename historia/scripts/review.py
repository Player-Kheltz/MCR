#!/usr/bin/env python3
"""
review.py — Revisao extensiva e autonoma do sistema MCR.
Verifica bridge, RAG, auto.py, seguranca, docs, testes.
Uso: python scripts/review.py
"""
import os, sys, json, time, subprocess

BASE_DIR = "E:/Projeto MCR"
PASS = 0
FAIL = 0
WARN = 0

def check(name, passed, detail=""):
    global PASS, FAIL, WARN
    if passed:
        PASS += 1
        s = "PASS"
    elif detail.startswith("WARN"):
        WARN += 1
        s = "WARN"
    else:
        FAIL += 1
        s = "FAIL"
    print(f"  [{s:4s}] {name:35s} {detail}")
    return passed

def file_exists(path):
    return os.path.exists(os.path.join(BASE_DIR, path))

def file_contains(path, pattern):
    fp = os.path.join(BASE_DIR, path)
    if not os.path.exists(fp):
        return False
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        return pattern in f.read()


# ==================== REVISAO ====================

def section(title):
    print(f"\n--- {title} ---")

# === 1. BRIDGE ===
section("BRIDGE")

# Bridge v4 existe
check("bridge_auto.py existe", file_exists("scripts/bridge_auto.py"))
check("bridge_watchdog.py existe", file_exists("scripts/bridge_watchdog.py"))

# Bridge usa modelo 7b
check("Modelo 7b configurado", file_contains("scripts/bridge_auto.py", "qwen2.5-coder:7b"))
# Bridge tem fallback 1.5b
check("Fallback 1.5b", file_contains("scripts/bridge_auto.py", "OLLAMA_MODEL_FALLBACK"))
# Bridge tem anti-hallucination
check("Anti-hallucination", file_contains("scripts/bridge_auto.py", "NUNCA invente"))
# Bridge tem encoding Latin-1
check("Encoding Latin-1", file_contains("scripts/bridge_auto.py", 'encoding="latin-1"'))
# Bridge tem fallback Ollama offline
check("Fallback Ollama offline", file_contains("scripts/bridge_auto.py", "Assistente indisponivel"))
# Watchdog usa PID file
check("Watchdog PID file", file_contains("scripts/bridge_watchdog.py", ".bridge_pid"))
# Bridge tem cache quente
check("Cache quente", file_contains("scripts/bridge_auto.py", ".rag_hot.json"))

# Verifica se o PID do bridge existe
bridge_pid = os.path.join(BASE_DIR, ".bridge_pid")
if os.path.exists(bridge_pid):
    with open(bridge_pid) as f:
        pid = f.read().strip()
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
    check("Bridge rodando", str(pid) in r.stdout, f"PID {pid}")
else:
    check("Bridge rodando", False, "sem PID file")

# === 2. CANAL ASSISTENTE (500) ===
section("CANAL 500")

check("chatchannels.xml tem canal 500", file_contains("Canary/data/chatchannels/chatchannels.xml", 'id="500"'))
check("assistente.lua existe", file_exists("Canary/data/chatchannels/scripts/assistente.lua"))
check("assistente.lua tem onSpeak", file_contains("Canary/data/chatchannels/scripts/assistente.lua", "function onSpeak"))
check("assistente.lua loginEvent", file_contains("Canary/data/chatchannels/scripts/assistente.lua", "openChannel"))
check("assistente.lua polling chat_out", file_contains("Canary/data/chatchannels/scripts/assistente.lua", "chat_out.txt"))
check("console.lua tem aba Assistente", file_contains("OTClient/modules/game_console/console.lua", "Assistente"))

# === 3. RAG ===
section("RAG")

rag_idx = os.path.join(BASE_DIR, ".rag_db", "index.json")
rag_emb = os.path.join(BASE_DIR, ".rag_db", "embeddings.npy")

if os.path.exists(rag_idx):
    with open(rag_idx, "r", encoding="utf-8") as f:
        idx = json.load(f)
    n_chunks = len(idx.get("chunks", []))
    n_src = len(set(c.get("source","?") for c in idx.get("chunks", [])))
    check("Indice RAG existe", True, f"{n_chunks} chunks, {n_src} fontes")
    check("Tem chunks suficientes", n_chunks > 1000, f"{n_chunks}")
else:
    check("Indice RAG existe", False)

check("rag_indexer.py existe", file_exists("scripts/rag_indexer.py"))
check("rag_query.py existe", file_exists("scripts/rag_query.py"))
check("rag_watcher.py existe", file_exists("scripts/rag_watcher.py"))
check("EXCLUDE_DIRS tem docs/assets", file_contains("scripts/rag_indexer.py", "docs/assets"))
check("EXCLUDE_FILES tem Ordem.txt", file_contains("scripts/rag_indexer.py", "Ordem.txt"))
check("EXCLUDE_FILE_PATTERNS tem nomes_monstros", file_contains("scripts/rag_indexer.py", "nomes_monstros"))
check("sanitize_text remove senhas", file_contains("scripts/rag_indexer.py", "SENSITIVE_LINE_PATTERNS"))
check("Threshold RAG 0.55", file_contains("scripts/rag_query.py", "0.55"))
check("mcr_knowledge.txt existe", file_exists("scripts/mcr_knowledge.txt"))

# === 4. AUTO.PY ===
section("AUTO.PY")

check("auto.py existe", file_exists("scripts/auto.py"))
check("auto.py up", file_contains("scripts/auto.py", "cmd_up"))
check("auto.py status", file_contains("scripts/auto.py", "cmd_status_all"))
check("auto.py doctor", file_contains("scripts/auto.py", "cmd_doctor"))
check("auto.py watchdog", file_contains("scripts/auto.py", "bridge_watchdog"))
check("auto.py reindex", file_contains("scripts/auto.py", "rag_indexer"))
check("auto.py usa canary-sln.exe", file_contains("scripts/auto.py", "canary-sln.exe"))

# === 5. OC-DEV ===
section("OC-DEV")

check("opencode.local.json existe", file_exists("opencode.local.json"))
check("opencode.local.json tem permission", file_contains("opencode.local.json", "permission"))
check("opencode.local.json sandbox allow", file_contains("opencode.local.json", "sandbox/**"))
check("opencode.local.json tool_call true", file_contains("opencode.local.json", "tool_call"))
check("oc-dev.ps1 existe", file_exists("oc-dev.ps1"))
check("sandbox/testes/ existe", os.path.isdir(os.path.join(BASE_DIR, "sandbox", "testes")))
check("sandbox/bugs/ existe", os.path.isdir(os.path.join(BASE_DIR, "sandbox", "bugs")))
check("test_ocdev.py existe", file_exists("scripts/test_ocdev.py"))
check("test_ocdev.py tem execute_bash", file_contains("scripts/test_ocdev.py", "execute_bash"))

# Profile alias
profile = r"C:\Users\Kheltz\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
if os.path.exists(profile):
    check("Profile ps1 existe", True)
    check("oc-dev alias no profile", file_contains(profile, "oc-dev"))
else:
    check("Profile ps1 existe", False, "nao encontrado")

# === 6. SEGURANCA ===
section("SEGURANCA")

check(".gitignore existe", file_exists(".gitignore"))
check(".gitignore cobre .rag_db", file_contains(".gitignore", ".rag_db"))
check(".gitignore cobre bridge_", file_contains(".gitignore", "bridge_"))
check(".gitignore cobre chat_", file_contains(".gitignore", "chat_"))
check(".gitignore cobre config.lua", file_contains(".gitignore", "config.lua"))
check(".gitignore cobre senhas", file_contains(".gitignore", "*senha*"))
check("bridge_auto.py bloqueia senha", file_contains("scripts/bridge_auto.py", "senha"))
check("bridge_auto.py blocked flag", file_contains("scripts/bridge_auto.py", "blocked"))

# Verifica se arquivos sensiveis estao no gitignore
sensitive_files = ["bridge_pending.txt", "bridge_debug.log", "bridge_response.txt"]
for sf in sensitive_files:
    fp = os.path.join(BASE_DIR, sf)
    if os.path.exists(fp):
        r = subprocess.run(["git", "check-ignore", "-q", fp], capture_output=True, cwd=BASE_DIR)
        check(f"gitignore cobre {sf}", r.returncode == 0)

# === 7. DOCUMENTACAO ===
section("DOCS")

check("AGENTS.md existe", file_exists("AGENTS.md"))
check("AGENTS.md tem autonomia", file_contains("AGENTS.md", "Autonomia"))
check("README_AUTONOMY.md existe", file_exists("scripts/README_AUTONOMY.md"))
check("docs/lessons/README.md existe", file_exists("docs/lessons/README.md"))
check("docs/lessons/recentes.md existe", file_exists("docs/lessons/recentes.md"))
check("lesson.py existe", file_exists("scripts/lesson.py"))
check("lesson.py create_lesson", file_contains("scripts/lesson.py", "create_lesson"))

# Lessons criadas
lessons = os.path.join(BASE_DIR, "docs", "lessons")
if os.path.exists(lessons):
    n_lessons = len([f for f in os.listdir(lessons) if f.endswith(".md") and f not in ("README.md", "recentes.md")])
    check("Lessons criadas", n_lessons >= 4, f"{n_lessons} lessons")

check("Pendencias.md atualizado", file_contains("docs/MCR - Instruções/DevLog/Pendências.md", "Autonomia"))

# === 8. RESTRUCTURE ===
section("RESTRUCTURE")

check("restructure.py existe", file_exists("scripts/restructure.py"))
check("restructure.py usa git mv", file_contains("scripts/restructure.py", "git mv"))

# Verifica se docs antigos seriam movidos
if file_exists("docs/restructure.py"):
    check("restructure.py dry-run seguro", file_contains("scripts/restructure.py", "DRY_RUN"))

# === 9. SERVER ===
section("SERVER")

r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq canary-sln.exe"], capture_output=True, text=True)
if "canary-sln.exe" in r.stdout:
    check("Servidor rodando", True)
else:
    check("Servidor rodando", False, "PARADO")

# Testa se a config existe
check("canary-sln.exe existe", os.path.exists(os.path.join(BASE_DIR, "Canary", "canary-sln.exe")))

# === 10. COMPILACAO ===
section("COMPILACAO")

check("auto.py compile --server", file_contains("scripts/auto.py", "compile_server"))
check("VS2022 referencia", file_contains("scripts/auto.py", "vs2022"))
check("vcpkg_installed existe", os.path.isdir(os.path.join(BASE_DIR, "Canary", "vcpkg_installed")))

# Verifica se tem DLLs do vcpkg
dlls = os.path.join(BASE_DIR, "Canary", "vcpkg_installed", "x64-windows", "bin")
if os.path.exists(dlls):
    n_dlls = len([f for f in os.listdir(dlls) if f.endswith(".dll")])
    check("DLLs vcpkg instaladas", n_dlls > 5, f"{n_dlls} DLLs")
else:
    check("DLLs vcpkg instaladas", False)

# === 11. BANCO ===
section("BANCO")

# Verifica se o banco responde
try:
    import pymysql
    conn = pymysql.connect(host="127.0.0.1", user="root", password="", database="BancoServer", connect_timeout=3)
    conn.close()
    check("Banco MySQL conecta", True)
except Exception as e:
    check("Banco MySQL conecta", False, str(e)[:50])

# === 12. TESTES ===
section("TESTES")

check("test.py existe", file_exists("scripts/test.py"))
check("test_runner.py existe", file_exists("scripts/test_runner.py"))
check("test_bot.lua existe", file_exists("Canary/data-canary/scripts/MCR/core/test_bot.lua"))
check("test_ocdev.py runs OC-Dev tests", file_contains("scripts/test_ocdev.py", "test_t1_write"))

# ==================== RESUMO ====================
print(f"\n{'='*60}")
print(f"REVISAO CONCLUIDA")
print(f"{'='*60}")
print(f"  PASS: {PASS}")
print(f"  WARN: {WARN}")
print(f"  FAIL: {FAIL}")
print(f"  TOTAL: {PASS + WARN + FAIL}")
print(f"{'='*60}")

if FAIL > 0:
    print(f"\n[REVISAO] {FAIL} falha(s) encontrada(s). Execute as correcoes.")
else:
    print(f"\n[REVISAO] Todas as verificacoes passaram!")

print(f"\nPara ver detalhes: python scripts/review.py")
