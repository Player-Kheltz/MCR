"""Verifica config do OpenCode."""
import json
with open(r"E:\Projeto MCR\opencode.local.json") as f:
    c = json.load(f)
print("AGENTES CONFIGURADOS:")
for a, d in c.get("agent", {}).items():
    print(f"  {a}: {d['model']}")
print(f"\nMODELOS DISPONIVEIS NO PROVIDER:")
for m, info in c.get("provider", {}).get("ollama", {}).get("models", {}).items():
    print(f"  {m}: {info.get('name','?')}")
