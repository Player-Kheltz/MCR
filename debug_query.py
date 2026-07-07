import sqlite3, os
os.chdir("E:\\MCR")
conn = sqlite3.connect(r"E:\MCR\cache\mcr_adapt.db")

# Find any Ahmet keys with 7+ levels (N >= 7)
cur = conn.execute("""
  SELECT length(key) as klen, key, next, count FROM trans 
  WHERE key LIKE 'Ahmet|%'
  ORDER BY klen DESC
  LIMIT 10
""")
for r in cur.fetchall():
    parts = r[1].split("|")
    print(f"  N={len(parts)-1} ({r[0]} chars): {r[1][:100]}")
    print(f"    next={repr(r[2])}, count={r[3]}")
    print()

# ALSO: let me just check the TOTAL distribution for Ahmet
cur = conn.execute("SELECT COUNT(DISTINCT key) FROM trans WHERE key LIKE 'Ahmet|%'")
total_keys = cur.fetchone()[0]
print(f"Total Ahmet keys: {total_keys}")

# Distribution by N-level
cur = conn.execute("""
  SELECT (LENGTH(key) - LENGTH(REPLACE(key, '|', ''))) as n_levels, 
         COUNT(*) as cnt 
  FROM trans WHERE key LIKE 'Ahmet|%'
  GROUP BY n_levels ORDER BY n_levels
""")
print("Distribution by N-level:")
for r in cur.fetchall():
    print(f"  N={r[0]}: {r[1]} entries")

conn.close()
