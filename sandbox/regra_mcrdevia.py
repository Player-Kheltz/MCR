"""Salvar lesson: usar MCR-DevIA primeiro"""
import json

lesson = {
    "id": "L943",
    "erro": "Cloud estava fazendo manualmente tarefas que MCR-DevIA ja sabe fazer (45 comandos)",
    "causa": "Cloud nao consultava o MCR-DevIA antes de agir, desperdicando tokens e nao reforcando o aprendizado local",
    "solucao": "REGRA ABSOLUTA em AGENTS.md: sempre perguntar 'O MCR-DevIA sabe fazer isso?' antes de qualquer acao. Tabela de 18 comandos essenciais incluida. Cloud so faz o que MCR-DevIA NAO pode.",
    "ctx": "workflow"
}

path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(path, "r", encoding="utf-8"))
kg["licoes"].append(lesson)
json.dump(kg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"[OK] Lesson registrada ({len(kg['licoes'])} total)")
