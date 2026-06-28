"""Limpar lessons auto-aprendidas de perguntas SHC que poluem o KG"""
import json

path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(path, "r", encoding="utf-8"))

# Remover lessons que sao perguntas (nao definicoes) sobre SHC
# Essas foram criadas automaticamente quando o modelo nao sabia responder
antes = len(kg["licoes"])
kg["licoes"] = [l for l in kg["licoes"] if not (
    "SHC" in l.get("erro","") and "?" in l.get("erro","")
)]

# Tambem remover lessons similares sobre SHC que sao perguntas
kg["licoes"] = [l for l in kg["licoes"] if not (
    "shc" in l.get("erro","").lower() and 
    l.get("erro","").strip().endswith("?")
)]

depois = len(kg["licoes"])
print(f"Removidas {antes - depois} lessons poluidoras ({depois} restantes)")

# Adicionar protecao no buscar para nao retornar lessons- pergunta
# (faremos isso no codigo, mas ja registramos aqui)

json.dump(kg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("[OK] KG limpo")
