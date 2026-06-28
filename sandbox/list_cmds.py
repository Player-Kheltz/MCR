"""Lista todos os comandos do MCR-DevIA"""
import re
code = open("E:\\Projeto MCR\\scripts\\mcr_devia\\mcr_devia.py").read()
cmds = sorted(set(re.findall(r"elif cmd == '(\w+)'", code)))
print(f"Comandos MCR-DevIA ({len(cmds)}):")
for c in cmds:
    print(f"  python mcr_devia.py {c} ...")
