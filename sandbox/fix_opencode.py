#!/usr/bin/env python3
"""Tenta baixar OpenCode 1.17.9 e substituir o atual."""
import urllib.request, os, sys, json, zipfile, tempfile, shutil

# URLs do OpenCode no GitHub
RELEASES = "https://api.github.com/repos/opencode-ai/opencode/releases"
CURRENT = "C:/Users/Kheltz/opencode/opencode.exe"
BACKUP = CURRENT + ".bak"

# Primeiro faz backup do atual
if os.path.exists(CURRENT) and not os.path.exists(BACKUP):
    shutil.copy2(CURRENT, BACKUP)
    print(f"Backup criado: {BACKUP}")

# Tenta buscar releases
try:
    req = urllib.request.Request(RELEASES, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    versions = [r["tag_name"] for r in data if "1.17" in r["tag_name"] or "1.17.9" in r["tag_name"]]
    print(f"Versoes encontradas: {versions[:5]}")
except Exception as e:
    print(f"Erro ao buscar GitHub: {e}")
    print("Tentando winget...")
    os.system("winget install opencode --version 1.17.9 2>&1 | findstr /i 'sucesso'")
