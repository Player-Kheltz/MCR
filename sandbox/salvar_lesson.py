"""Salva lesson sobre Model Router e 14B no KG"""
import json, os

lesson = """## 2026-06-25 — Model Router V2 + 14B nao cabe na RTX 3080 10GB

### Problema
O Model Router do MCR-DevIA referenciava modelos inexistentes (hermes3:8b, phi3:3.8b) e
nao usava os modelos realmente disponiveis. O qwen2.5:14b (Q4_K_M 9GB e Q3_K_M 7.3GB)
nao cabe na RTX 3080 10GB mesmo com offloading parcial (num_gpu).

### Causa Raiz
1. _melhor_modelo() tinha modelos que nunca foram instalados (hermes3:8b, phi3:3.8b)
2. Modelo 14B precisa de ~9GB VRAM + desquantizacao FP16 + KV cache = >10GB
3. Mesmo Q3_K_M (7.3GB) nao cabe porque Ollama desquantiza parcialmente para FP16
4. Criar modelo de GGUF customizado (Modelfile) funciona, mas nao resolve VRAM insuficiente

### Solucao
1. Model Router corrigido com modelos REAIS:
   - fast/leve: qwen2.5-coder:1.5b (ctx=2048/1024)
   - code: qwen2.5-coder:7b (ctx=2048)
   - contexto: llama3.1:8b (ctx=2048) — substituto do hermes3:8b
   - raciocinio/revisor/planejador: deepseek-r1:7b (ctx=2048)
   - embedding: nomic-embed-text (ctx=2048)
2. num_ctx agora varia por modelo (14b usaria 1024, removido por VRAM)
3. Super Fragmentador criado em scripts/mcr_devia/super_fragmentador.py
4. Modelos 14B removidos (liberaram ~16GB de disco)

### Licao
- RTX 3080 10GB VRAM = maximo 8B params viavel. 14B nao cabe em nenhuma quantizacao.
- Para GGUF customizado no Ollama: baixar GGUF, criar Modelfile, ollama create
- num_gpu (offloading) existe como opcao mas nao resolve VRAM insuficiente
- Model Router deve SEMPRE ser verificado contra modelos realmente instalados
"""

kg_path = os.path.join("E:\\Projeto MCR", "sandbox", ".mcr_devia", "knowledge.json")
if os.path.exists(kg_path):
    with open(kg_path, "r", encoding="utf-8") as f:
        kg = json.load(f)
else:
    kg = {"licoes": []}

kg.setdefault("licoes", []).append({
    "data": "2026-06-25",
    "titulo": "Model Router V2 + 14B nao cabe na RTX 3080 10GB",
    "contexto": "model_router, vram, modelos",
    "solucao": lesson.strip(),
    "tags": ["model_router", "vram", "14b", "q3_k_m", "rtx3080"]
})

with open(kg_path, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

total = len(kg["licoes"])
print(f"[OK] Lesson registrada no KG ({total} lessons)")
print(f"[OK] Resumo: {lesson[:80]}...")
