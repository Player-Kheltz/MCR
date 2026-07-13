"""Mostra e valida o NPC gerado pelo MCR + Qwen3.5."""
import sys, json, time, urllib.request, re, os
sys.path.insert(0, 'E:/MCR')
from mcr.config_llm import MODELO

OLLAMA = "http://localhost:11434/api/generate"

# Carrega golden examples
from mcr.paths import KG_DIR, CANARY_NPC_DIR

golden_npc = []
for f in sorted(KG_DIR.glob('patterns_*.json')):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            dados = json.load(fh)
        for p in dados.get('padroes', []):
            arquivo = p.get('arquivo', '')
            tipo = p.get('tipo', '')
            if tipo == 'npc' and arquivo and os.path.exists(arquivo):
                golden_npc.append(arquivo)
    except: pass

exemplo = ""
for path in golden_npc[:2]:
    try:
        with open(path, 'r', encoding='latin-1') as fh:
            code = fh.read()
        exemplo += f"\n--- EXEMPLO REAL: {os.path.basename(path)} ---\n{code[:1000]}\n"
    except: pass

prompt = f"""Voce e um gerador de scripts Lua para Tibia Canary (OTServ).

GOLDEN EXAMPLES (formato EXATO a seguir):
{exemplo[:2500]}

TAREFA: Crie um NPC ferreiro anão chamado Brunin Forjador que vende armaduras e escudos.
Siga o MESMO formato dos exemplos. NAO invente APIs."""

print('Gerando NPC...')
payload = json.dumps({
    "model": MODELO, "prompt": prompt, "stream": False,
    "options": {"temperature": 0.3, "num_ctx": 32768}
}).encode()
req = urllib.request.Request(OLLAMA, data=payload,
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=180) as r:
    data = json.loads(r.read())
codigo = data.get('response', '')

# Extrai código Lua
blocos = re.findall(r'```lua\n(.*?)```', codigo, re.DOTALL)
if blocos:
    codigo = blocos[0]

print(f'\n{"="*60}')
print(f'  NPC GERADO — {codigo.count(chr(10))+1} linhas')
print(f'{"="*60}\n')
print(codigo)

# Salvar
output = 'E:/MCR/tests/npc_gerado_fogo.lua'
with open(output, 'w', encoding='utf-8') as f:
    f.write(codigo)
print(f'\nSalvo em: {output}')

# Validar
from mcr.sanity_validator import SanityValidator
sv = SanityValidator()
val = sv.validar_codigo(codigo)
print(f'APIs conhecidas: {len(val.get("apis_conhecidas",[]))}')
desconhecidas = val.get('apis_desconhecidas', [])
print(f'APIs desconhecidas: {len(desconhecidas)} {"OK" if not desconhecidas else desconhecidas}')

# Estrutura
checks = ['internalNpcName', 'Game.createNpcType', 'npcConfig.name', 
          'npcConfig.health', 'npcConfig.outfit', 'npcType:register']
for c in checks:
    ok = c in codigo
    print(f'  {c}: {"OK" if ok else "FALTA"}')
