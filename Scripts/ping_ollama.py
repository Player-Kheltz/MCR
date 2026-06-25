#!/usr/bin/env python3
import json, urllib.request
payload = json.dumps({"model": "qwen2.5-coder:1.5b", "prompt": "Responda apenas: OK", "stream": False}).encode()
req = urllib.request.Request("http://localhost:11434/api/generate", data=payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
print(data.get("response", "").strip())
