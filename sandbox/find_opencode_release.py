#!/usr/bin/env python3
"""Encontra URL de download do OpenCode v1.17.9."""
import json, urllib.request

url = "https://api.github.com/repos/opencode-ai/opencode/releases"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.github.v3+json"
})

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        releases = json.loads(r.read())
    
    targets = ["1.17.9", "1.17.8", "1.17.7"]
    for rel in releases:
        tag = rel.get("tag_name", "")
        for t in targets:
            if t in tag:
                print(f"=== OpenCode {tag} ===")
                for asset in rel.get("assets", []):
                    name = asset.get("name", "")
                    if "win" in name and "x64" in name:
                        url_dl = asset["browser_download_url"]
                        size = asset.get("size", 0)
                        print(f"  {name} ({size//1024//1024} MB)")
                        print(f"  Download: {url_dl}")
                        print()
                break
except json.JSONDecodeError:
    print("Resposta nao é JSON - limite de API atingido?")
    print("Tentando URL direta...")
    print("https://github.com/opencode-ai/opencode/releases/tag/v1.17.9")
except Exception as e:
    print(f"Erro: {e}")
