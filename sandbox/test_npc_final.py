"""Teste final de NPC."""
import json, time, urllib.request

payload = json.dumps({"model":"qwen2.5-coder:7b","messages":[
    {"role":"system","content":"""Voce e um criador de NPCs para Canary.

EXEMPLO REAL DE NPC NO CANARY:
local npc = NPCHandler:new("Vendedor")
function npc:onGreet(player) selfSay("Ola!") end
function npc:onSell(player, item, amount) return true end
npc:register()

REGRAS ABSOLUTAS:
1. PROIBIDO usar player:sendTextMessage
2. PROIBIDO usar talkaction ou onSay
3. OBRIGATORIO usar selfSay para falar
4. OBRIGATORIO usar NPCHandler"""},
    {"role":"user","content":"Crie NPC Vendedor: diz Ola!, vende pocao vida (100g), compra ossos (5g). Use NPCHandler. PROIBIDO sendTextMessage."}
],"stream":False,"options":{"temperature":0.1,"max_tokens":1024}}).encode()

t0 = time.time()
req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
    headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read())
resp = data["message"]["content"]
tempo = time.time() - t0

print(f"Tempo: {tempo:.1f}s")
print(f"sendTextMessage: {'NAO' if 'sendTextMessage' not in resp else 'SIM'}")
print(f"selfSay: {'SIM' if 'selfSay' in resp else 'NAO'}")
print(f"NPCHandler: {'SIM' if 'NPCHandler' in resp else 'NAO'}")
print(f"onSell/onBuy: {'SIM' if 'onSell' in resp or 'onBuy' in resp else 'NAO'}")
print(f"\nResposta:\n{resp[:500]}")
print(f"\n{'NPC OK' if 'sendTextMessage' not in resp and 'selfSay' in resp else 'AINDA COM ERRO'}")
