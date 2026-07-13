"""mcr.config_llm — Configuração centralizada de LLM.

Único ponto de alteração para modelos Ollama.
Todos os outros arquivos importam daqui.
"""
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen3.5:9b"

# Aliases para código legado
MODELO_PADRAO = MODELO
MODELO_CODIGO = MODELO
MODELO_CHAT = MODELO
MODELO_LORE = MODELO
MODELO_LEVE = MODELO

# Lista para ensemble/status (1 modelo, não 3)
MODELOS = [(MODELO, "Qwen3.5")]
