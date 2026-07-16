"""mcr.config_llm — Configuração centralizada de LLM.

Setup: ollama pull mistral:7b
"""
OLLAMA_URL = "http://localhost:11434/api/generate"

MODELO = "qwen3:8b"
MODELO_CODIGO = MODELO
MODELO_LORE  = "gemma4:12b"
MODELO_PADRAO = MODELO
MODELO_CHAT = MODELO
MODELO_LEVE = "phi4-mini:latest"
MODELOS = [(MODELO, "Mistral7B"), ("gemma4:12b", "Gemma4"), ("phi4-mini:latest", "Phi4Mini")]
