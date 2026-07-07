#!/usr/bin/env python3
"""Debug: feed just Ahmet and check if N>5 keys reach SQLite."""
import sys, os, re, sqlite3

os.chdir("E:\\MCR")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    exec(compile(f.read().split("def main():")[0], "MCR.py", "exec"))

DB_PATH = r"E:\MCR\cache\mcr_debug.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

class SQLiteMarkov:
    def __init__(self, db_path, n_max=30):
        self.db_path = db_path
        self.n_max = n_max
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=OFF")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS trans ("
            "key TEXT NOT NULL, next TEXT NOT NULL, count INTEGER DEFAULT 1, "
            "PRIMARY KEY (key, next)) WITHOUT ROWID")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS freq ("
            "key TEXT PRIMARY KEY, total INTEGER DEFAULT 0) WITHOUT ROWID")
        self.conn.commit()
        self._stats = {"trans": 0, "freq": 0}

    def alimentar(self, identity, tokens):
        nome_limpo = re.sub(r"[^\w\s\u00C0-\u00FF-]", "", identity).strip()[:30]
        if not nome_limpo or len(tokens) < 3:
            return 0

        counts = {}
        for n in range(1, self.n_max + 1):
            for i in range(len(tokens) - n):
                chave = (n,) + tuple(tokens[i:i+n])
                prox = tokens[i+n]
                if chave not in counts:
                    counts[chave] = {}
                counts[chave][prox] = counts[chave].get(prox, 0) + 1

        N_KEEP = 5
        batch_trans = []
        batch_freq = {}
        n_acima = 0
        for (n, *ctx), nexts in counts.items():
            keep = n <= N_KEEP
            if not keep:
                sufixo = tuple(ctx[1:])
                parent_key = (n-1,) + sufixo
                parent = counts.get(parent_key)
                if parent is None or set(nexts.keys()) != set(parent.keys()):
                    keep = True
            if keep:
                if n > 5:
                    n_acima += 1
                chave = nome_limpo + "|" + "|".join(ctx)
                for prox, cnt in nexts.items():
                    batch_trans.append((chave, prox))
                    batch_freq[chave] = batch_freq.get(chave, 0) + cnt

        if identity == "Ahmet":
            print(f"DEBUG: N>5 kept={n_acima}, batch={len(batch_trans)}, kept_total={len(batch_freq)}")

        self.conn.executemany(
            "INSERT INTO trans(key, next, count) VALUES (?, ?, 1) "
            "ON CONFLICT(key, next) DO UPDATE SET count = count + 1",
            batch_trans)

        for chave, delta in batch_freq.items():
            self.conn.execute(
                "INSERT INTO freq(key, total) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET total = total + ?",
                (chave, delta, delta))

        self.conn.commit()
        self._stats["trans"] += len(batch_trans)
        self._stats["freq"] += len(batch_freq)
        return len(batch_trans)


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
        if c.isalnum() or c in "._":
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] in "._"):
                j += 1
            tokens.append(texto[i:j])
            i = j
            continue
        if c in ",;:+-*/<>~|&#@%^=":
            tokens.append(c)
            i += 1
            continue
        if c in "()[]{}":
            tokens.append(c)
            i += 1
            continue
        tokens.append(c)
        i += 1
    return tokens


def extrair_identidade(texto):
    nome = ""
    for linha in texto.split("\n"):
        linha = linha.strip()
        if "internalNpcName" in linha or "Game.createNpcType" in linha or "Game.createMonsterType" in linha:
            m = re.search('"(.*?)"', linha)
            if m:
                nome = m.group(1).strip()
                break
    return nome


# Feed just Ahmet
mk = SQLiteMarkov(DB_PATH, 30)

fp = r"E:\Projeto MCR\Canary\data-otservbr-global\npc\ahmet.lua"
with open(fp, "r", encoding="utf-8", errors="replace") as fh:
    texto = fh.read()
nome = extrair_identidade(texto)
tokens = tokenizar(texto)
print(f"Ahmet: {len(tokens)} tokens, identity={repr(nome)}")
mk.alimentar(nome, tokens)

# Check DB
cur = mk.conn.execute(
    "SELECT (LENGTH(key) - LENGTH(REPLACE(key, '|', ''))) as pipes, "
    "COUNT(*) as cnt FROM trans GROUP BY pipes ORDER BY pipes")
print("\nDB distribution by pipes:")
for r in cur.fetchall():
    print(f"  Pipes={r[0]} (N={r[0]}): {r[1]} entries")

cur = mk.conn.execute("SELECT COUNT(*) as total FROM trans")
print(f"Total entries: {cur.fetchone()[0]}")

# Check specific N=10 key
test_key = "Ahmet|creatureSayCallback|(|npc|,|creature|,|type|,|message|)"
cur = mk.conn.execute("SELECT next, count FROM trans WHERE key=? ORDER BY count DESC", (test_key,))
rows = cur.fetchall()
print(f"\nN=10 key '{test_key[:60]}...':")
if rows:
    for r in rows:
        print(f"  -> {repr(r[0])} (count={r[1]})")
else:
    print("  NOT FOUND IN DB")

# Check N=9 key
key9 = "Ahmet|(|npc|,|creature|,|type|,|message|)"
cur = mk.conn.execute("SELECT next, count FROM trans WHERE key=? ORDER BY count DESC", (key9,))
rows = cur.fetchall()
print(f"\nN=9 key '{key9[:60]}...':")
if rows:
    for r in rows:
        print(f"  -> {repr(r[0])} (count={r[1]})")
else:
    print("  NOT FOUND IN DB")

mk.conn.close()
