"""mcr.config_llm — Configuração centralizada de LLM.

Único ponto de alteração para modelos Ollama.
Todos os outros arquivos importam daqui.

Setup:
    ollama pull qwen3.5:9b
    ollama pull gemma4:12b
"""
OLLAMA_URL = "http://localhost:11434/api/generate"

# Dois modelos especializados. Ollama troca automaticamente.
MODELO_CODIGO = "qwen3.5:9b"      # ~6GB — código, raciocínio, ferramentas
MODELO_LORE  = "gemma4:12b"        # ~7.5GB — narrativa, NPCs, criatividade

# Aliases para código legado
MODELO_PADRAO = MODELO_CODIGO
MODELO = MODELO_CODIGO
MODELO_CHAT = MODELO_LORE
MODELO_LEVE = MODELO_CODIGO

# Ensemble usa o modelo de lore (criatividade)
MODELOS = [(MODELO_LORE, "Gemma4")]
