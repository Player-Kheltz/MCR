#!/usr/bin/env python3
"""Remove templates especificos do orquestrador.py e simplifica."""
import re

path = "E:/Projeto MCR/scripts/mcr_devia/modulos/orquestrador.py"
with open(path, "r", encoding="utf-8") as f:
    txt = f.read()

templates_to_remove = [
    "analise_melhoria",
    "mega_teste", 
    "planejamento_arquitetura",
    "diagnostico_problema",
    "explicacao_conceitual"
]

for t in templates_to_remove:
    pattern = '    "' + t + '": """'
    start = txt.find(pattern)
    if start >= 0:
        # Find the closing """, of this template
        # It's the next occurrence of """, after the template content
        search_start = start + len(pattern)
        # Find the pattern: closing triple quote followed by comma and newline
        end_marker = '""",\n\n    "'
        end = txt.find(end_marker, search_start)
        if end < 0:
            # Maybe it's the last template, closed by }\n
            end_marker2 = '""",\n}'
            end = txt.find(end_marker2, search_start)
            if end >= 0:
                end = end + len(end_marker2) - 1  # Keep the }
        else:
            end = end + len(end_marker) - 1  # Keep the opening quote of next template
        
        if end > start:
            removed = txt[start:end]
            txt = txt[:start] + txt[end:]
            print(f"Removed {t}: {len(removed)} chars")

# Also remove from _ROUTER
router_lines = [
    '    "analise_melhoria": "pesado",\n',
    '    "mega_teste": "pesado",\n',
    '    "planejamento_arquitetura": "pesado",\n',
    '    "diagnostico_problema": "pesado",\n',
    '    "explicacao_conceitual": "pesado",\n',
]
for line in router_lines:
    if line in txt:
        txt = txt.replace(line, "")
        print(f"Removed router: {line.strip()}")

# Remove from _TEMPLATES_FRAGMENTAVEIS
old_frag = '_TEMPLATES_FRAGMENTAVEIS = {"planejamento_arquitetura", "diagnostico_problema", "explicacao_conceitual", "mega_teste", "analise_melhoria"}'
new_frag = '_TEMPLATES_FRAGMENTAVEIS = {"perguntar", "analisar_codigo", "analisar_bug"}'
if old_frag in txt:
    txt = txt.replace(old_frag, new_frag)
    print("Updated _TEMPLATES_FRAGMENTAVEIS")

# Remove mega_teste-specific prompt limit
txt = txt.replace(
    '        if template_key == "mega_teste":\n            max_prompt = 20000  # Fragmentador quebra em secoes, entao pode ser grande',
    '        if template_key in ("perguntar",):\n            max_prompt = 20000  # Universal: fragmentador quebra em secoes'
)
print("Updated prompt limit to be universal")

# Remove mega_teste-specific auto_revisor config
txt = txt.replace(
    '                if template_key == "mega_teste":\n                    classes_permitidas = {"DataLake", "StreamSimulator", "ValidadorStream", "ErroStream"}',
    '                if template_key in ("perguntar",):\n                    classes_permitidas = set()  # Universal: verifica contra todo o projeto'
)
print("Updated auto_revisor config to universal")

with open(path, "w", encoding="utf-8") as f:
    f.write(txt)

print("\nDone! Simplificacao concluida.")
