"""Teste final: MCR-DevIA cria NPC com exemplo real do Canary."""
import sys, os, time, urllib.request, json
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm, _decider, _validator

# 1. Classifica
pergunta = "Crie um NPC chamado Oráculo Negro que vende Ultimate Healing Rune id 2273 por 100 gold e compra Demonic Essence id 6555 por 1000 gold"
classe, conf = _decider.classificar(pergunta)
print(f'[CLASSIFICACAO] {classe} (conf={conf:.2f})')

# 2. Encontra um NPC real do Canary que vende itens
npc_dir = r'E:\Projeto MCR\Canary\data-otservbr-global\npc'
exemplos_npc = []
for f in sorted(os.listdir(npc_dir)):
    if not f.endswith('.lua'): continue
    caminho = os.path.join(npc_dir, f)
    with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
        conteudo = fh.read()
    if 'shop' in conteudo.lower() or 'addBuyableItem' in conteudo or 'addSellableItem' in conteudo:
        exemplos_npc.append((f, conteudo))

print(f'[RAG] {len(exemplos_npc)} NPCs com shop encontrados')

if not exemplos_npc:
    print('ERRO: nenhum NPC com shop encontrado')
    sys.exit(1)

nome_exemplo, codigo_exemplo = exemplos_npc[0]
print(f'[EXEMPLO] Usando: {nome_exemplo} ({len(codigo_exemplo)} chars)')

# 3. Prompt com few-shot
prompt = (
    f"Aqui esta um exemplo real de NPC do Canary (servidor Tibia):\n\n"
    f"=== EXEMPLO ({nome_exemplo}) ===\n"
    f"{codigo_exemplo[:2500]}\n=== FIM EXEMPLO ===\n\n"
    f"Baseado neste exemplo, crie um NOVO NPC chamado 'Oraculo Negro' "
    f"que vende Ultimate Healing Rune (id 2273) por 100 gold coins "
    f"e compra Demonic Essence (id 6555) por 1000 gold coins.\n\n"
    f"Use a estrutura do exemplo: npcType, npcConfig, shop table, "
    f"onBuyItem, onSellItem, creatureSayCallback.\n"
    f"Responda APENAS com o codigo Lua completo, sem explicacoes."
)

# 4. LLM gera
t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.3)
t = time.time() - t0

# 5. Valida
val = _validator.validar(prompt, resp, codigo_exemplo[:500])

print(f'\n[TEMPO] {t:.1f}s')
print(f'[VALIDACAO] sim={val["similaridade"]:.3f} valido={val["valida"]}')
print(f'\n=== CODIGO GERADO ===')
print(resp[:2000])
print(f'\n=== FIM ===')

# 6. Verifica
checks = [
    ('npcType/npcConfig', 'npcType' in resp or 'npcConfig' in resp),
    ('Shop table/items', 'shop' in resp.lower() or 'buyable' in resp.lower() or 'sellable' in resp.lower()),
    ('Callback criacao', 'onBuyItem' in resp or 'onSellItem' in resp or 'creatureSayCallback' in resp),
    ('Item ID 2273', '2273' in resp),
    ('Item ID 6555', '6555' in resp),
    ('100 gold', '100' in resp),
    ('1000 gold', '1000' in resp),
    ('Estrutura Lua valida', 'local ' in resp or 'function ' in resp or 'end' in resp),
    ('Nao contem C++', '#include' not in resp),
]
ok_count = sum(1 for _, ok in checks if ok)
print(f'\n[CHECKS] {ok_count}/{len(checks)}')
for nome, ok in checks:
    print(f'  {nome}: \t{"OK" if ok else "X"}')

if ok_count >= 7:
    print(f'\n[VEREDITO] NPC gerado com sucesso!')
else:
    print(f'\n[VEREDITO] Precisa de ajustes ({ok_count}/9)')
    if '#include' in resp:
        print(f'  - AINDA GEROU C++ (removeu {resp.count("#include")} includes)')
