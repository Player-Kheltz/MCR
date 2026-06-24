"""Teste rapido do Hermes 3."""
import json, urllib.request, time

for model in ["hermes3:8b", "phi3.5:3.8b"]:
    t0 = time.time()
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "Responda em 1 frase em portugues."},
            {"role": "user", "content": "Ola! Quem e voce e o que voce pode fazer?"}
        ],
        "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 100}
    }).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        content = data["message"]["content"]
        print(f"✅ {model} ({dt:.1f}s): {content[:120]}")
    except Exception as e:
        print(f"❌ {model}: {e}")
