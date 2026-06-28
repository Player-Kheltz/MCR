"""Corrigir formato da lesson recem-adicionada"""
import json

path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(path, "r", encoding="utf-8"))

# Corrigir a ultima entrada (idx 940) para o formato correto
for i, l in enumerate(kg["licoes"]):
    if "titulo" in l and "erro" not in l:
        kg["licoes"][i] = {
            "id": f"L{len(kg['licoes']):03d}",
            "erro": l.get("titulo", "Model Router desatualizado"),
            "causa": l.get("contexto", l.get("contexto", "Modelos errados configurados")),
            "solucao": l["solucao"],
            "ctx": "model_router",
        }
        print(f"Corrigido idx {i}: {kg['licoes'][i]['erro'][:60]}...")
        break

json.dump(kg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"[OK] KG atualizado, {len(kg['licoes'])} lessons")
