import sqlite3, json, os

db_path = os.path.expanduser("~/.local/share/opencode/opencode.db")
db = sqlite3.connect(db_path)
db.text_factory = lambda x: x.decode('utf-8', errors='replace') 
cursor = db.cursor()

# Get the text parts where model recommendations were discussed
# Looking at the session flow around the "que modelos baixar" part
sid = "ses_10606fcccffe4ELHlHrfcy1sPn"

# Get ALL text parts from user and assistant
cursor.execute("""
    SELECT p.data, m.data as msg_data, p.time_created
    FROM part p 
    JOIN message m ON p.message_id = m.id 
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text' 
    AND json_extract(p.data, '$.text') IS NOT NULL
    ORDER BY p.time_created
""", (sid,))
parts = cursor.fetchall()

# Find the discussion about model recommendations
# The user asked about better models, assistant recommended downloads
capture = False
for i, (pdata, mdata, tc) in enumerate(parts):
    try:
        p = json.loads(pdata)
        m = json.loads(mdata)
        text = p.get('text', '')
        role = m.get('role', '?')
        
        # Look for the recommendation section
        if 'Recomendações de download' in text or 'Recomenda��es de download' in text:
            capture = True
            print(f"\n{'='*60}")
            print(f"RECOMENDACOES DE DOWNLOAD ({role})")
            print(f"{'='*60}")
            print(text[:3000])
            print("...")
            
        if capture and ('modelo' in text.lower() or 'model' in text.lower() or 'Specs' in text or 'RTX' in text):
            if len(text) > 30:
                print(f"\n--- Related message ({role}) ---")
                print(text[:500])
    except:
        pass

# Also get the session where assistant listed installed models and made recommendations
sid2 = "ses_10501adfbffeDwCCxVezM5jhQU"
print(f"\n\n{'='*60}")
print(f"SESSION DE PESQUISA DE MODELOS")
print(f"{'='*60}")
cursor.execute("""
    SELECT p.data, m.data as msg_data
    FROM part p 
    JOIN message m ON p.message_id = m.id 
    WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created DESC LIMIT 1
""", (sid2,))
for pdata, mdata in cursor.fetchall():
    try:
        p = json.loads(pdata)
        text = p.get('text', '')
        if 'RELATORIO' in text:
            # Print the last part which has the recommendations
            print(text[3000:5000])
    except:
        pass

db.close()
