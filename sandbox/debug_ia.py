"""Debug IA response format"""
import json, urllib.request

prompt = """Crie um plano DETALHADO para um sistema de quest no jogo Tibia.

IDEIA: Dragoes ancestrais de Eridanus

Responda EXATAMENTE neste formato (sem explicacoes):

SISTEMA: nome_do_sistema

NPCS:
  npc1: NomeDoNPC | saudacao: "fala" | item_id: 101 | item_preco: 75

MONSTERS:
  monster1: Nome | hp: 300 | atk: 35 | def: 10 | loot_id: 41001 | loot_chance: 0.8

ITEMS:
  item1: Nome | id: 41001 | tipo: quest | atk: 0 | def: 0 | peso: 2

SPELLS:
  spell1: Nome | elemento: holy | dano: 150 | mana: 60 | cd: 7

Regras: Monstro comum HP 200-400. Mini-boss HP 400-800. Boss HP 800-2000."""

data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,'options':{'temperature':0.7,'num_ctx':4096}}).encode()
req = urllib.request.Request('http://localhost:11434/api/generate', data=data, headers={'Content-Type':'application/json'})
r = json.loads(urllib.request.urlopen(req, timeout=120).read())
resp = r.get('response','')
print(resp[:2000])
