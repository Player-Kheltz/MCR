#!/usr/bin/env python3
import re
import sys
from pathlib import Path

TARGET_EXTS = {'.cpp', '.otui'}   # removido '.lua'

# Regex para capturar strings entre aspas duplas
STRING_RE = re.compile(r'"([^"]*)"')

# PROTEÇÃO DE BANCO DE DADOS
SQL_PROTECTED = {
    'id', 'name', 'password', 'email', 'premdays', 'type', 'group_id',
    'level', 'vocation', 'health', 'mana', 'lookbody', 'lookfeet',
    'lookhead', 'looklegs', 'lookaddons', 'lookmount', 'lastlogin',
    'lastip', 'save', 'skill_fist', 'skill_club', 'skill_sword',
    'skill_axe', 'skill_dist', 'skill_shielding', 'skill_fishing', 'maglevel',
    'experience', 'manaspent', 'rank_id', 'guild_id', 'motd', 'description',
    'posx', 'posy', 'posz', 'data', 'value', 'key', 'sid', 'pid', 'itemtype',
    'count', 'attributes', 'pronoun', 'sex', 'raceid', 'boostname'
}

# PROTEÇÃO DE CÓDIGO FONTE
CODE_PROTECTED = {
    'core', 'game', 'player', 'monster', 'npc', 'house', 'item', 'container',
    'position', 'condition', 'combat', 'config', 'database', 'storage', 'amount'
}

# Arquivos que JAMAIS devem ser traduzidos
FORBIDDEN_FILES = {
    'titles.lua', 'achievements.lua', 'badges.lua',
    'title_data.lua', 'achievement_data.lua',
    'player_titles.lua', 'mount_titles.lua'
}

def is_safe_to_translate(text, line_content):
    t = text.strip()
    clean_line = line_content.strip()

    # 1. Inclusão / define / using
    if clean_line.startswith(('#include', '#define', 'using namespace', 'std::')):
        return False

    # Nova proteção: ignora linhas que registam métodos/bindings Lua
    if any(kw in clean_line for kw in ['registerMethod', 'registerClass', 'registerFunction', 'setGlobal', 'lua_register', 'registerEnum']):
        return False

    # 2. Títulos e Highscores
    if 'addTitle' in clean_line or 'PlayerTitle' in clean_line:
        return False
    if 'Highscore' in clean_line or 'Highscores' in clean_line:
        return False
    if any(kw in clean_line for kw in ['checkOther', 'm_maleName', 'm_femaleName', 'getTitleByName']):
        return False

    # 3. Ignora strings muito curtas
    if len(t) < 2:
        return False

    t_lower = t.lower()

    # 4. Coluna/palavra protegida exata
    if t_lower in SQL_PROTECTED or t_lower in CODE_PROTECTED:
        return False

    # 5. Normalização de espaços → underscores (ex.: "skill shielding")
    if t_lower.replace(' ', '_') in SQL_PROTECTED:
        return False

    # 6. Sem espaços e curto = provável identificador
    if ' ' not in t and len(t) < 15:
        return False

    # 7. Bloqueia queries SQL
    if re.search(r'\b(SELECT|UPDATE|SET|WHERE|INSERT|DELETE|FROM|VALUES|ORDER BY)\b', t, re.IGNORECASE):
        return False

    # 8. Caminhos de arquivo
    if re.search(r'\.(hpp|cpp|h|lua|otui|xml|otbm|png|ogg|json|dat|sql|pem)$', t, re.IGNORECASE):
        return False

    return True

def extract_from_file(filepath: Path):
    # Ignorar qualquer ficheiro dentro da pasta lua
    if '/lua/' in str(filepath).replace('\\', '/'):
        return []

    if filepath.name in FORBIDDEN_FILES or 'titles' in filepath.stem or 'achievement' in filepath.stem:
        return []

    entries = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('//', '--', '/*')):
                continue

            for m in STRING_RE.finditer(line):
                text = m.group(1)
                if is_safe_to_translate(text, line):
                    entries.append((f"{i}_{m.start()}", text))
    except Exception as e:
        print(f"Erro ao processar {filepath}: {e}")
    return entries

def main():
    if len(sys.argv) < 3:
        print("Uso: python 1_extrator.py <pasta_src> extraido.txt")
        return

    src_dir, out_file = Path(sys.argv[1]), sys.argv[2]
    all_entries = []

    print(f"🔍 Escaneando diretório: {src_dir} ...")
    for fp in [f for f in src_dir.rglob('*') if f.suffix.lower() in TARGET_EXTS]:
        res = extract_from_file(fp)
        if res:
            all_entries.append((str(fp), res))

    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        for path, subs in all_entries:
            f.write(f"[{path}]\n")
            for k, txt in subs:
                f.write(f"{k}={txt}\n")
            f.write("\n")

    print(f"✅ Extração cirúrgica concluída! Ficheiro: {out_file}")

if __name__ == '__main__':
    main()