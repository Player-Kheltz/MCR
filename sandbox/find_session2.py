import sqlite3, json, os, sys

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
cursor = db.cursor()

# The session we want: "Onde paramos?" - ses_10606fcccffe4ELHlHrfcy1sPn
# Also check ses_1040245fbffe22CHhfFHRadIWc (another "Onde paramos?" from jun 24)
# And ses_10501adfbffeDwCC... (Research Hermes/local assistant models)

target_sessions = [
    "ses_10606fcccffe4ELHlHrfcy1sPn",  # Most recent "Onde paramos?"
    "ses_1040245fbffe22CHhfFHRadIWc",  # Earlier "Onde paramos?" from jun 24
    "ses_10501adfbffeDwCCxVezM5jhQU",  # Research Hermes/local assistant models  
    "ses_105027ee0ffeLOJb63Se1PFwZd",  # Explore Ollama setup in MCR
    "ses_10522998bffeCRAqtbL2lNFI7W",  # Stop point clarification
    "ses_10506dfddffegia6iWmHKi44i58",  # Retomar de onde paramos
    "ses_105065b19ffeVALnLjTNULFck6",  # Planned intro
    "ses_1052aa6c3ffeWCbr8IqntlCQ8I",  # Benchmark local model hardware
    "ses_0fedf4e97ffeXKvPm26t1lEuhu",  # Retomada de conversa (very recent)
]

for sid in target_sessions:
    print(f"\n{'='*60}")
    print(f"SESSION: {sid}")
    print(f"{'='*60}")
    # Get the session info
    cursor.execute("SELECT title, slug, time_created, time_updated FROM session WHERE id=?", (sid,))
    srow = cursor.fetchone()
    if srow:
        from datetime import datetime
        created = datetime.fromtimestamp(srow[2]/1000) if srow[2] else "?"
        updated = datetime.fromtimestamp(srow[3]/1000) if srow[3] else "?"
        print(f"Title: {srow[0]}, Slug: {srow[1]}, Created: {created}, Updated: {updated}")
    
    # Get all parts with text for this session
    cursor.execute("""
        SELECT p.data, m.data as msg_data 
        FROM part p 
        JOIN message m ON p.message_id = m.id 
        WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
        ORDER BY p.time_created
        LIMIT 50
    """, (sid,))
    parts = cursor.fetchall()
    
    for i, (pdata, mdata) in enumerate(parts):
        try:
            p = json.loads(pdata)
            m = json.loads(mdata)
            text = p.get('text', '')
            role = m.get('role', '?')
            if text and len(text) > 10:
                if any(kw in text.lower() for kw in ['specs', 'rtx', 'modelo', 'model', 'llama', 'qwen', 'hermes', 'deepseek', 'phi', 'sabia', 'baixar', 'download', 'gpu', 'vram', 'c:', 'driver c', 'disco c', 'lives']):
                    preview = text[:500].replace('\n', ' | ')
                    print(f"\n[{role}] {preview}")
        except:
            pass

db.close()
