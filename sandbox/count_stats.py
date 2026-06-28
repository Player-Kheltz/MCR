"""Contar lessons e comandos"""
import json, re
kg = json.load(open("E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json", "r", encoding="utf-8"))
code = open("E:\\Projeto MCR\\scripts\\mcr_devia\\mcr_devia.py", "r", encoding="utf-8").read()
cmds = sorted(set(re.findall(r"elif cmd == '(\w+)'", code)))
print(f"Lessons: {len(kg['licoes'])}")
print(f"Comandos: {len(cmds)}")
ctxs = set()
for l in kg["licoes"]:
    if l.get("ctx"):
        ctxs.add(l["ctx"])
print(f"Contextos: {len(ctxs)}")
