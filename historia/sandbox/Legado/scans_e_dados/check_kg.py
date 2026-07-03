"""Verificar entradas sem 'erro' no KG"""
import json

kg = json.load(open("E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json", "r", encoding="utf-8"))
for i, l in enumerate(kg["licoes"]):
    if "erro" not in l:
        print(f"IDX {i}: id={l.get('id','?')} keys={list(l.keys())}")
        print(f"  {str(l)[:200]}")
