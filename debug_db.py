import sqlite3, re

def tokenizar(texto):
    tokens = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c.isspace():
            i += 1
            continue
        if c in ('"', "'"):
            quote = c
            j = i + 1
            while j < len(texto) and texto[j] != quote:
                j += 1
            if j < len(texto):
                tokens.append(texto[i:j+1])
                i = j + 1
            else:
                tokens.append(texto[i:])
                i = len(texto)
            continue
        if c.isalnum() or c in '_.':
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] in '_.'):
                j += 1
            tokens.append(texto[i:j])
            i = j
            continue
        if c in ',;:+-*/<>~|&#@%^=':
            tokens.append(c)
            i += 1
            continue
        if c in '()[]{}':
            tokens.append(c)
            i += 1
            continue
        tokens.append(c)
        i += 1
    return tokens

def extrair_identidade(texto):
    nome = ""
    for linha in texto.split('\n'):
        linha = linha.strip()
        if 'internalNpcName' in linha or 'Game.createNpcType' in linha or 'Game.createMonsterType' in linha:
            m = re.search(r'"(.*?)"', linha)
            if m:
                nome = m.group(1).strip()
                break
    return nome

conn = sqlite3.connect(r"E:\MCR\cache\mcr_adapt.db")

# Check each identity prefix
for ident in ['Adrenius', 'Ahmet', 'Sapo Azul']:
    prefix = ident + '|'
    cur = conn.execute("SELECT COUNT(DISTINCT key) FROM trans WHERE key LIKE ?", (prefix + '%',))
    n_keys = cur.fetchone()[0]
    print(f"\n=== {ident}: {n_keys} keys ===")
    
    # Check 'local' prefix
    cur = conn.execute(
        "SELECT next, count FROM trans WHERE key=? ORDER BY count DESC LIMIT 10",
        (ident + '|local',))
    rows = cur.fetchall()
    if rows:
        print(f"  '{ident}|local':")
        for nxt, cnt in rows:
            print(f"    -> '{nxt}' ({cnt})")
    else:
        # Check what follows 'local' with bigger context
        print(f"  '{ident}|local': NOT FOUND")
        # Try to find what keys start with
        cur = conn.execute(
            "SELECT next, count FROM trans WHERE key LIKE ? ORDER BY count DESC LIMIT 10",
            (ident + '|%',))
        top = cur.fetchall()
        if top:
            print(f"  Top keys: {[(k, c) for k, c in top[:5]]}")

# Now read actual files to see what tokens they produce
for fp in [
    r"E:\Projeto MCR\Canary\data-otservbr-global\npc\adrenius.lua",
    r"E:\Projeto MCR\Canary\data-otservbr-global\npc\ahmet.lua",
    r"E:\Projeto MCR\Canary\data-otservbr-global\monster\amphibics\azure_frog.lua",
]:
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        texto = f.read()
    nome = extrair_identidade(texto)
    tokens = tokenizar(texto)
    print(f"\n=== {os.path.basename(fp)} (id={nome}, {len(tokens)} tokens) ===")
    print(f"  First 20: {tokens[:20]}")
    print(f"  First 5 bigrams:")
    for i in range(min(5, len(tokens)-1)):
        key = nome + '|' + tokens[i]
        cur = conn.execute("SELECT next, count FROM trans WHERE key=? ORDER BY count DESC", (key,))
        rows = cur.fetchall()
        print(f"    '{nome}|{tokens[i]}' -> {rows[:3]}")

conn.close()
