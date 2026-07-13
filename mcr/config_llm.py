"""mcr.config_llm — Configuração centralizada de LLM.

Setup: ollama pull qwen3.5:9b
"""
OLLAMA_URL = "http://localhost:11434/api/generate"

MODELO = "qwen3.5:9b"
MODELO_CODIGO = MODELO
MODELO_LORE  = MODELO
MODELO_PADRAO = MODELO
MODELO_CHAT = MODELO
MODELO_LEVE = MODELO
MODELOS = [(MODELO, "Qwen3.5")]
