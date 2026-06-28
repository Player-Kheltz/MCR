#!/usr/bin/env python3
"""Remove remaining specific templates from orquestrador.py."""
path = "E:/Projeto MCR/scripts/mcr_devia/modulos/orquestrador.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove mega_teste template
start = content.find('"mega_teste": """{identidade}')
if start >= 0:
    # Find the closing """, of this template - look for the pattern after the template content
    search_start = start + 20
    # Find next template start or end of _TEMPLATES
    end_marker = '""",\n\n"diagnostico_problema"'
    end = content.find(end_marker, search_start)
    if end >= 0:
        end = end + 5  # Include the closing """
        removed = content[start:end]
        content = content[:start] + content[end:]
        print(f"Removed mega_teste: {len(removed)} chars")

# Remove diagnostico_problema template  
start = content.find('"diagnostico_problema": """{identidade}')
if start >= 0:
    end_marker = '""",\n\n"explicacao_conceitual"'
    end = content.find(end_marker, start)
    if end >= 0:
        end = end + 5
        removed = content[start:end]
        content = content[:start] + content[end:]
        print(f"Removed diagnostico_problema: {len(removed)} chars")

# Remove explicacao_conceitual template
start = content.find('"explicacao_conceitual": """{identidade}')
if start >= 0:
    end_marker = '""",\n\n"conselho_analista"'
    end = content.find(end_marker, start)
    if end >= 0:
        end = end + 5
        removed = content[start:end]
        content = content[:start] + content[end:]
        print(f"Removed explicacao_conceitual: {len(removed)} chars")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
