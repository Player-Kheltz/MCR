import sqlite3, json, os, sys

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
cursor = db.cursor()

# Search for the session "Onde paramos?"
cursor.execute("SELECT id, title, slug, time_updated FROM session WHERE title LIKE '%paramos%' OR title LIKE '%' OR slug LIKE '%paramos%'")
rows = cursor.fetchall()
print("=== Sessoes com 'paramos' ===")
for r in rows:
    print(f"  ID: {r[0]}, Title: {r[1]}, Slug: {r[2]}, Updated: {r[3]}")

# List all session titles ordered by time
print("\n=== TODAS AS SESSOES (ordenadas por data) ===")
cursor.execute("SELECT id, title, slug, time_created, time_updated FROM session ORDER BY time_created DESC LIMIT 30")
rows = cursor.fetchall()
for r in rows:
    from datetime import datetime
    created = datetime.fromtimestamp(r[3]/1000) if r[3] else "?"
    print(f"  {r[0][:20]}... | {r[1]} | {r[2]} | {created}")

# Search parts for "Specs confirmados" or "lives em C" or "RTX 3080"
print("\n=== Buscando 'Specs confirmados' nas parts ===")
cursor.execute("SELECT session_id, data FROM part WHERE data LIKE '%Specs%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    text = data.get('text', '')
    print(f"  Session: {r[0][:20]}... | Text: {text[:300]}")

print("\n=== Buscando 'lives em C' nas parts ===")
cursor.execute("SELECT session_id, data FROM part WHERE data LIKE '%lives%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    text = data.get('text', '')
    print(f"  Session: {r[0][:20]}... | Text: {text[:300]}")

print("\n=== Buscando 'RTX 3080' nas parts ===")
cursor.execute("SELECT session_id, data FROM part WHERE data LIKE '%RTX 3080%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    text = data.get('text', '')
    print(f"  Session: {r[0][:20]}... | Text: {text[:300]}")

# Search events for the discussion
print("\n=== Buscando 'Specs confirmados' nos events ===")
cursor.execute("SELECT aggregate_id, data FROM event WHERE data LIKE '%Specs confirmados%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    print(f"  Session: {r[0][:20]}...")

print("\n=== Buscando 'lives em C' nos events ===")
cursor.execute("SELECT aggregate_id, data FROM event WHERE data LIKE '%lives em C%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    print(f"  Session: {r[0][:20]}...")

print("\n=== Buscando 'RTX 3080' nos events ===")
cursor.execute("SELECT aggregate_id, data FROM event WHERE data LIKE '%RTX 3080%' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    data = json.loads(r[1])
    print(f"  Session: {r[0][:20]}...")

db.close()
