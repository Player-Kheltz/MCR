import sqlite3, json, os

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
db.text_factory = lambda x: x.decode('utf-8', errors='replace')
cursor = db.cursor()

# Search ALL text parts for any model planning discussion
# Try to find "Specs confirmados" and "lives em C"
print("=== Buscando 'Specs' ===")
cursor.execute("SELECT session_id, substr(data,1,800) FROM part WHERE data LIKE '%Specs%' LIMIT 20")
for r in cursor.fetchall():
    print(f"\n--- Session: {r[0][:20]}... ---")
    print(r[1][:500])

print("\n\n=== Buscando 'lives em C' ===")
cursor.execute("SELECT session_id, substr(data,1,800) FROM part WHERE data LIKE '%lives em C%' LIMIT 20")
for r in cursor.fetchall():
    print(f"\n--- Session: {r[0][:20]}... ---")
    print(r[1][:500])

print("\n\n=== Buscando 'lives' ===")
cursor.execute("SELECT session_id, substr(data,1,800) FROM part WHERE data LIKE '%lives%' LIMIT 20")
for r in cursor.fetchall():
    print(f"\n--- Session: {r[0][:20]}... ---")
    print(r[1][:500])

# Also check event table
print("\n\n=== Buscando 'lives' nos events ===")
cursor.execute("SELECT aggregate_id, substr(data,1,800) FROM event WHERE data LIKE '%lives%' LIMIT 10")
for r in cursor.fetchall():
    print(f"\n--- Session: {r[0][:20]}... ---")
    print(r[1][:500])

print("\n\n=== Buscando 'Specs' nos events ===")
cursor.execute("SELECT aggregate_id, substr(data,1,800) FROM event WHERE data LIKE '%Specs%' LIMIT 10")
for r in cursor.fetchall():
    print(f"\n--- Session: {r[0][:20]}... ---")
    print(r[1][:500])

db.close()
