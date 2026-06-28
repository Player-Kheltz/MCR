import sqlite3, json, os, sys

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
cursor = db.cursor()

# Get ALL text parts from the Research Hermes/local assistant models session
sid = "ses_10501adfbffeDwCCxVezM5jhQU"
cursor.execute("""
    SELECT p.data, m.data as msg_data 
    FROM part p 
    JOIN message m ON p.message_id = m.id 
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created
""", (sid,))
parts = cursor.fetchall()

for i, (pdata, mdata) in enumerate(parts):
    try:
        p = json.loads(pdata)
        m = json.loads(mdata)
        text = p.get('text', '')
        role = m.get('role', '?')
        if text and len(text) > 50:
            print(f"\n{'='*60}")
            print(f"[{role.upper()}] Part {i}")
            print(f"{'='*60}")
            print(text[:2000])
    except Exception as e:
        print(f"Error: {e}")

db.close()
