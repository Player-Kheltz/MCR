import sys, os, re, sqlite3
os.chdir("E:\\MCR")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    exec(compile(f.read().split("def main():")[0], "MCR.py", "exec"))

# Force the exact same DB that was just created
DB_PATH = r"E:\MCR\cache\mcr_adapt.db"
conn = sqlite3.connect(DB_PATH)

# Check: any Ahmet keys with 6+ pipes?
cur = conn.execute("""
  SELECT (LENGTH(key) - LENGTH(REPLACE(key, '|', ''))) as pipes,
         COUNT(*) as cnt
  FROM trans 
  WHERE key LIKE 'Ahmet|%'
  GROUP BY pipes
  ORDER BY pipes
""")
print("Ahmet key distribution by pipes:")
for r in cur.fetchall():
    print(f"  {r[0]} pipes (N={r[0]}): {r[1]} keys")

# Also: total stored
cur = conn.execute("SELECT COUNT(*) FROM trans WHERE key LIKE 'Ahmet|%'")
total = cur.fetchone()[0]
print(f"\nTotal Ahmet entries: {total}")

# Now let me test: can I INSERT a key with N=10 and find it?
test_key = "Ahmet|creatureSayCallback|(|npc|,|creature|,|type|,|message|)"
conn.execute("INSERT OR IGNORE INTO trans(key, next, count) VALUES (?, ?, 1)",
             (test_key, "TEST_MARKER"))
conn.commit()
cur = conn.execute("SELECT next, count FROM trans WHERE key=?", (test_key,))
print(f"\nTest insert: {cur.fetchall()}")

# Now check with LIKE query
cur = conn.execute("SELECT COUNT(*) FROM trans WHERE key LIKE 'Ahmet|%|%|%|%|%|%|%|%|%|%'")  # at least 10 pipes
n10plus = cur.fetchone()[0]
print(f"\nAhmet keys with 10+ pipes: {n10plus}")

# Cleanup test
conn.execute("DELETE FROM trans WHERE key=? AND next='TEST_MARKER'", (test_key,))
conn.commit()
conn.close()
