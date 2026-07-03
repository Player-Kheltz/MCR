#!/usr/bin/env python3
import json, urllib.request
payload = json.dumps({"model": "nomic-embed-text:latest", "input": "teste de embedding"}).encode()
req = urllib.request.Request("http://localhost:11434/api/embed", data=payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read())
print(f"Dimensao: {len(data['embeddings'][0])}")
print(f"Primeiros 5: {data['embeddings'][0][:5]}")
