"""Compara versões do Bun entre OpenCode 1.17.9 e 1.17.10."""
import json, re, os

for ver in ["1.17.10", "1.17.9"]:
    lockfile = f"E:/OpenCode/opencode-{ver}/bun.lock"
    if os.path.exists(lockfile):
        with open(lockfile, encoding="utf-8") as f:
            content = f.read()
        # Procura bun version no lockfile
        m = re.search(r'"bun":\s*"([^"]+)"', content[:10000])
        bun_ver = m.group(1) if m else "nao encontrado"
        print(f"OpenCode {ver}: Bun {bun_ver}")
        
        # Procura por @types/bun
        t = re.search(r'"@types/bun":\s*"([^"]+)"', content[:20000])
        types_ver = t.group(1) if t else "nao encontrado"
        print(f"  @types/bun: {types_ver}")
        
        # Tamanho do lockfile
        size = os.path.getsize(lockfile)
        print(f"  bun.lock: {size//1024} KB")
    else:
        print(f"OpenCode {ver}: sem bun.lock")
    print()
