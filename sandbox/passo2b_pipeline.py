"""Passo 2b: PipelineExecutor usa instrucao_contexto separado de contexto_extra."""
import json, subprocess, sys

BASE = "E:/Projeto MCR/scripts/mcr_devia"
path = f"{BASE}/modulos/pipeline_executor.py"

with open(path, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Mudar: params['contexto_extra'] = cr_instrucao + cr_contexto
# Para: params['instrucao_contexto'] = cr_instrucao ; params['contexto_extra'] = cr_contexto
old = "if cr_instrucao or cr_contexto:\n                params['contexto_extra'] = cr_instrucao + cr_contexto"
new = "if cr_instrucao:\n                params['instrucao_contexto'] = cr_instrucao\n            if cr_contexto:\n                params['contexto_extra'] = cr_contexto"

if old in conteudo:
    conteudo = conteudo.replace(old, new)
    print("[OK] PipelineExecutor atualizado: instrucao_contexto separado")
else:
    print("[AVISO] Padrao nao encontrado")

# Salvar via MCR-DevIA write
cmd = {
    'cmd': 'write',
    'args': ['modulos/pipeline_executor.py', conteudo]
}
with open(f'{BASE}/../sandbox/.mcr_cmd.json', 'w', encoding='utf-8') as f:
    json.dump(cmd, f, ensure_ascii=False)

r = subprocess.run([sys.executable, f'{BASE}/MCR_DevIA-Kernel.py', '--json', f'{BASE}/../sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, errors='replace', timeout=60)
print(f"[MCR] {r.stdout.strip()}")
