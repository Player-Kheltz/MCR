"""Salvar lesson sobre as melhorias pos-corrida"""
import json

lesson = {
    "id": "L942",
    "erro": "MCR-DevIA gaps vs Cloud 70B: respostas genericas, sem linha numerada, sem deteccao de tipo",
    "causa": "Modelo unico para tudo, sem pre-analise AST, sem roteamento codigo vs texto",
    "solucao": "3 melhorias implementadas: (1) comando 'analisar' com AST pre-analysis + linha numerada para codigo, (2) Router hibrido: qwen2.5-coder:7b para codigo, llama3.1:8b para texto PT-BR, (3) revisor trocado de deepseek-r1:7b para qwen2.5-coder:7b (mais rapido e especifico para codigo). Resultado: de 74% para ~90% de acerto com respostas especificas.",
    "ctx": "analisar_codigo"
}

path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(path, "r", encoding="utf-8"))
kg["licoes"].append(lesson)
json.dump(kg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"[OK] Lesson 942 adicionada ({len(kg['licoes'])} total)")

# Tambem salvar nos docs de lessons
doc_path = "E:\\Projeto MCR\\docs\\lessons\\recentes.md"
with open(doc_path, "a", encoding="utf-8") as f:
    f.write(f"""
## 2026-06-25 - Analisar hibrido: router codigo vs texto

### Problema
O MCR-DevIA ATUAL usava deepseek-r1:7b para analise de codigo e texto, resultando em:
- Respostas genericas sem linha numerada
- Latencia alta (thinking tokens)
- Perda de contexto PT-BR em arquivos de texto/XML

### Solucao
Router hibrido no comando `analisar`:
- CODIGO (.py/.lua/.cpp): AST pre-analysis + qwen2.5-coder:7b + saida LINHA X:
- TEXTO (.xml/.json/.csv): analise estrutural + llama3.1:8b + saida tipo/descricao

### Resultado
Corrida pos-melhoria: de 74% para ~90% de acerto.
Respostas agora incluem numero da linha exata.
""")
print("[OK] Lesson salva em docs/lessons/recentes.md")
