import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r"E:\MCR\mcr\knowledge\dialogos_npc.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

npcs = data["npcs"]
print(f"TOTAL NPCs: {len(npcs)}")

rows = []
for n in npcs:
    ds = n.get("dialogos", [])
    total_chars = sum(len(d.get("response","")) for d in ds)
    rows.append((n["npc_name"], len(ds), total_chars))

rows.sort(key=lambda x: -x[2])
print("\nTOP 25 NPCs por total de caracteres de resposta:")
print(f"{'NPC':35s} {'#Dialogos':>10s} {'TotalChars':>10s}")
for nome, nd, tc in rows[:25]:
    print(f"{nome[:35]:35s} {nd:>10d} {tc:>10d}")

print("\nTOTAL dialogos:", sum(r[1] for r in rows))
print("TOTAL chars:", sum(r[2] for r in rows))
