import sqlite3
conn = sqlite3.connect(r"E:\MCR\cache\mcr_adapt.db")
# Check specific keys
for chave in ["Adrenius|internalNpcName|=", "Adrenius|=", "Adrenius|internalNpcName"]:
    cur = conn.execute("SELECT next, count FROM trans WHERE key=? ORDER BY count DESC", (chave,))
    rows = cur.fetchall()
    if rows:
        print(f"  '{chave}': {rows[:5]}")
    else:
        print(f"  '{chave}': NOT FOUND")
conn.close()
