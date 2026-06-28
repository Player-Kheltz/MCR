import sqlite3, json, os, sys

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
db.text_factory = lambda x: x.decode('utf-8', errors='replace')
cursor = db.cursor()

# Get ALL text parts from the current session (ses_10606fcccffe4ELHlHrfcy1sPn)
sid = "ses_10606fcccffe4ELHlHrfcy1sPn"
print(f"=== SESSION {sid} - ALL TEXTS ===")
cursor.execute("""
    SELECT p.data, m.data as msg_data 
    FROM part p 
    JOIN message m ON p.message_id = m.id 
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created
""", (sid,))
parts = cursor.fetchall()
print(f"Total text parts: {len(parts)}")

for i, (pdata, mdata) in enumerate(parts):
    try:
        p = json.loads(pdata)
        m = json.loads(mdata)
        text = p.get('text', '')
        role = m.get('role', '?')
        if text:
            preview = text[:300].replace('\n', ' | ')
            print(f"\n[{role}] {preview}")
            # Check for keywords
            for kw in ['specs', 'rtx', 'lives', 'c:', 'driver', 'modelo', 'qwen', 'hermes', 'deepseek', 'phi']:
                if kw in text.lower():
                    print(f"  >>> MATCH '{kw}' found!")
    except Exception as e:
        print(f"Error part {i}: {e}")

# Also check events in this session
print(f"\n\n=== SESSION {sid} - EVENTS ===")
cursor.execute("SELECT type, substr(data,1,500) FROM event WHERE aggregate_id = ? ORDER BY seq LIMIT 30", (sid,))
for r in cursor.fetchall():
    print(f"  Event type: {r[0]}")
    data_str = r[1]
    if any(kw in data_str.lower() for kw in ['specs', 'rtx', 'lives', 'modelo', 'driver c']):
        print(f"  >>> MATCH: {data_str[:200]}")

db.close()
