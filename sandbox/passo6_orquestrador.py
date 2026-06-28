"""Passo 6: Adicionar {instrucao_contexto} no template perguntar do Orquestrador."""
import json, subprocess, sys

BASE = "E:/Projeto MCR/scripts/mcr_devia"
path = f"{BASE}/modulos/orquestrador.py"

with open(path, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# 1. Adicionar {instrucao_contexto} no template perguntar
old = '"perguntar": """{identidade}\n{ctx_infinity}\n{contexto_extra}\n\nPergunta: {pergunta}'
new = '"perguntar": """{identidade}\n{ctx_infinity}\n{contexto_extra}\n{instrucao_contexto}\n\nPergunta: {pergunta}'
if old in conteudo:
    conteudo = conteudo.replace(old, new)
    print("[OK] Template perguntar atualizado")
else:
    print("[AVISO] Template perguntar nao encontrado para substituicao")

# 2. Adicionar instrucao_contexto nos defaults
old2 = "            'ctx_infinity': '',\n        }"
new2 = "            'ctx_infinity': '',\n            'instrucao_contexto': '',\n        }"
if old2 in conteudo:
    conteudo = conteudo.replace(old2, new2)
    print("[OK] Default instrucao_contexto adicionado")
else:
    print("[AVISO] Defaults nao encontrados")

# 3. Salvar via MCR-DevIA write
cmd = {
    'cmd': 'write',
    'args': ['modulos/orquestrador.py', conteudo]
}
with open(f'{BASE}/../sandbox/.mcr_cmd.json', 'w', encoding='utf-8') as f:
    json.dump(cmd, f, ensure_ascii=False)

r = subprocess.run([sys.executable, f'{BASE}/MCR_DevIA-Kernel.py', '--json', f'{BASE}/../sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, errors='replace', timeout=60)
print(f"[MCR] {r.stdout.strip()}")
