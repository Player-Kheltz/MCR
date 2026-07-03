#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path

FORBIDDEN_DIRS = {'lib', 'libs', 'migrations', 'vcproj', 'tests', 'src', 'cmake',
                  '.github', 'docker', 'docs', 'metrics', 'npclib', 'scripts/lib',
                  'MCR Scripts', 'modules', 'json', 'reports', 'logs', 'XML'}
FORBIDDEN_FILES = {'config.lua', 'global.lua', 'core.lua', 'stages.lua', 'update.lua',
                   'titles.lua', 'achievements.lua', 'badges.lua',
                   'register_npc_type.lua', 'register_monster_type.lua'}

FUNC_PATTERNS = [
    re.compile(pattern) for pattern in [
        r'npcHandler:say\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'self:say\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'doCreatureSay\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'doPlayerSendTextMessage\s*\([^,]+,\s*[^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'player:sendTextMessage\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'creature:say\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'doPlayerSendCancel\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'doBroadcastMessage\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'Game\.broadcastMessage\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'doSendAnimatedText\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'setDefaultCancel\s*\(\s*"((?:[^"\\]|\\.)*)"',
        r'sendChannelMessage\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'addBuyableItem\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'addSellableItem\s*\([^,]+,\s*"((?:[^"\\]|\\.)*)"',
        r'createShopEntry\s*\(\s*"((?:[^"\\]|\\.)*)"',
    ]
]
DESC_RE = re.compile(r'monster\.description\s*=\s*"((?:[^"\\]|\\.)*)"')
VOICE_TEXT_RE = re.compile(r'text\s*=\s*"((?:[^"\\]|\\.)*)"')

# Padrão para detectar nomes de spells: spell:name("...")
SPELL_NAME_RE = re.compile(r'spell:name\s*\(\s*"((?:[^"\\]|\\.)*)"\s*\)')

def is_allowed(filepath):
    parts = filepath.parts
    for part in parts:
        if part in FORBIDDEN_DIRS:
            return False
    return filepath.name not in FORBIDDEN_FILES and filepath.suffix in ('.lua', '.xml')

def extract_spell_names(content):
    """Retorna um conjunto com todos os nomes de spells encontrados no conteúdo."""
    return {m.group(1) for m in SPELL_NAME_RE.finditer(content)}

def extract_from_lua(filepath):
    entries = []
    try:
        with open(filepath, 'r', encoding='iso-8859-1') as f:
            content = f.read()
    except:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return entries

    # --- NOVA PROTEÇÃO: recolher nomes de spells presentes no ficheiro ---
    protected_spell_names = extract_spell_names(content)

    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pat in FUNC_PATTERNS:
            for m in pat.finditer(line):
                text = m.group(1).strip()
                # Ignorar strings que sejam nomes de spells
                if text in protected_spell_names:
                    continue
                if len(text) >= 2 and not text.startswith('$') and not text.isdigit():
                    entries.append((f"{i}_{m.start()}_say", text))
        if 'monster.description' in line:
            for m in DESC_RE.finditer(line):
                text = m.group(1).strip()
                if len(text) >= 2:
                    entries.append((f"{i}_{m.start()}_desc", text))
        if 'monster.voices' in line:
            for m in VOICE_TEXT_RE.finditer(line):
                text = m.group(1).strip()
                if len(text) >= 2:
                    entries.append((f"{i}_{m.start()}_voice", text))
    return entries

def main():
    if len(sys.argv) < 3:
        print("Uso: python 1-extrair.py <raiz_servidor> extraido.txt")
        return
    root = Path(sys.argv[1])
    out = sys.argv[2]
    all_entries = []

    for fp in root.rglob('*.lua'):
        if not is_allowed(fp):
            continue
        res = extract_from_lua(fp)
        if res:
            all_entries.append((str(fp), res))

    with open(out, 'w', encoding='utf-8') as f:
        for path, subs in all_entries:
            f.write(f"[{path}]\n")
            for k, v in subs:
                f.write(f"{k}={v}\n")
            f.write("\n")
    print(f"Extração concluída: {len(all_entries)} ficheiros.")

if __name__ == '__main__':
    main()