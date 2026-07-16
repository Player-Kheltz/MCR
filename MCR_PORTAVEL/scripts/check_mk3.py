import os, sqlite3

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

conn = sqlite3.connect(os.path.join(_BASE, "cache", "mcr_adapt.db"))
# Check specific keys
for chave in ["Adrenius|internalNpcName|=", "Adrenius|=", "Adrenius|internalNpcName"]:
    cur = conn.execute("SELECT next, count FROM trans WHERE key=? ORDER BY count DESC", (chave,))
    rows = cur.fetchall()
    if rows:
        print(f"  '{chave}': {rows[:5]}")
    else:
        print(f"  '{chave}': NOT FOUND")
conn.close()
