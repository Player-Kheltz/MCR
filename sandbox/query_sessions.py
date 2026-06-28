import sqlite3, json, os, sys

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
print(f"DB: {db_path} ({os.path.getsize(db_path)} bytes)")

db = sqlite3.connect(db_path)
cursor = db.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("\nTabelas:", [t[0] for t in tables])

# Explore each table
for table in tables:
    tname = table[0]
    try:
        cursor.execute(f'SELECT * FROM "{tname}" LIMIT 5')
        cols = [d[0] for d in cursor.description]
        print(f'\n=== {tname} ===')
        print('Colunas:', cols)
        rows = cursor.fetchall()
        for row in rows:
            for i, col in enumerate(cols):
                val = row[i]
                if isinstance(val, str) and len(val) > 200:
                    val = val[:200] + "..."
                print(f"  {col}: {val}")
            print("  ---")
    except Exception as e:
        print(f'{tname}: {e}')

db.close()
