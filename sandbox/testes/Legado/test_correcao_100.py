#!/usr/bin/env python3
"""Teste de correcao: 3 areas problematicas com 'leia exemplo primeiro'."""
import json, os, sys, time, urllib.request

BASE = r"E:\Projeto MCR"
SAIDA = os.path.join(BASE, "sandbox", "test_correcao")
os.makedirs(SAIDA, exist_ok=True)
RESULTADOS = []

def chat(modelo, messages, max_tokens=2048, temp=0.1):
    payload = json.dumps({"model": modelo, "messages": messages, "stream": False,
        "options": {"temperature": temp, "max_tokens": max_tokens}}).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return data["message"]["content"], dt
    except Exception as e:
        return f"[ERRO] {e}", time.time() - t0

def testar(area, modelo, system, prompt, verificacoes, max_tokens=2048):
    print(f"\n{'='*70}")
    print(f"  [{area}]")
    print(f"{'='*70}")
    
    resp, tempo = chat(modelo, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ], max_tokens, 0.1)
    
    # Verificacoes
    erros = []
    for nome_verif, func_verif in verificacoes:
        if not func_verif(resp):
            erros.append(nome_verif)
    
    status = "✅" if not erros else "⚠️"
    print(f"  Tempo: {tempo:.1f}s | Tam: {len(resp)} chars | {status}")
    if erros:
        for e in erros:
            print(f"     ❌ {e}")
    print(f"  Resposta:\n{resp[:300]}")
    
    RESULTADOS.append({
        "area": area, "modelo": modelo,
        "tempo": round(tempo, 1), "tamanho": len(resp),
        "erros": erros, "status": status,
        "resposta": resp
    })
    
    with open(os.path.join(SAIDA, f"{area.lower().replace(' ','_')}.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {area}\n# Modelo: {modelo}\n# Tempo: {tempo:.1f}s\n\n{resp}")

# ============================================
print("=" * 80)
print("  TESTE DE CORRECAO - 3 AREAS PROBLEMATICAS")
print("  Estrategia: ler exemplo real do projeto antes de gerar")
print("=" * 80)

# Carrega exemplos reais
otui_path = os.path.join(BASE, "OTClient", "modules", "client_entergame", "characterlist.otui")
with open(otui_path, encoding="utf-8", errors="replace") as f:
    EXEMPLO_OTUI = f.read()[:800]

EXEMPLO_NPC = """local npc = NPCHandler:new("Vendedor")
function npc:onGreet(player) selfSay("Ola, " .. player:getName() .. "!") end
function npc:onSell(player, item, amount) return true end
function npc:onBuy(player, item, amount) return true end
npc:register()"""

with open(os.path.join(BASE, "Canary", "data-canary", "scripts", "MCR", "SPA", "habilidades", "fogo.lua"), encoding="utf-8", errors="replace") as f:
    EXEMPLO_SHC = f.read()[:1500]

# ============================================
# AREA 1: INTERFACE OTUI (com exemplo real)
# ============================================
print(f"\n\n{'='*80}")
print("  AREA 1/3: INTERFACE OTUI (com exemplo real)")
print(f"{'='*80}")

testar("Interface OTUI", "qwen2.5-coder:7b",
    f"Voce e um designer OTUI para o OTClient.\n\n"
    f"Formato OTUI REAL (use EXATAMENTE este formato):\n{EXEMPLO_OTUI}\n\n"
    f"REGRAS:\n"
    f"- OTUI usa anchors.top: / anchors.left: como PROPRIEDADE, nao tag <Anchor>\n"
    f"- Formato: 'anchors.top: parent.top' em vez de <Anchor>\n"
    f"- NUNCA use tags XML como <Anchor>, <Label>, <Window>\n"
    f"- Siga o formato do exemplo (WidgetName < ParentWidget com propriedades)\n",
    "Crie um layout OTUI para uma janela 'Status do Personagem' com: nome, nivel, vida, mana. "
    "Siga o formato OTUI do exemplo (anchors.top, anchors.left, etc).",
    [
        ("Usou tag XML", lambda r: "<Anchor" not in r and "<Label" not in r and "<Window" not in r),
        ("Usou anchors.top/left", lambda r: "anchors.top" in r.lower() or "anchors.left" in r.lower()),
        ("Tem nome/nivel/vida", lambda r: "nome" in r.lower() or "name" in r.lower()),
    ])

# ============================================
# AREA 2: NPC (com exemplo real)
# ============================================
print(f"\n{'='*80}")
print("  AREA 2/3: NPC (com exemplo real)")
print(f"{'='*80}")

testar("NPC", "qwen2.5-coder:7b",
    f"Voce e um criador de NPCs para Canary.\n\n"
    f"Formato NPC REAL do Canary:\n{EXEMPLO_NPC}\n\n"
    f"REGRAS ABSOLUTAS (NAO QUEBRE):\n"
    f"- PROIBIDO usar player:sendTextMessage - isso NAO existe em NPC\n"
    f"- PROIBIDO usar talkaction ou onSay\n"
    f"- OBRIGATORIO usar 'selfSay' para o NPC falar\n"
    f"- OBRIGATORIO usar NPCHandler\n"
    f"- Siga o formato do exemplo exatamente\n",
    "Crie um NPC 'Vendedor' que: diz 'Ola!' ao cumprimentar, "
    "vende pocao de vida (100g) e compra ossos (5g). "
    "Use NPCHandler, selfSay. PROIBIDO sendTextMessage.",
    [
        ("Usou sendTextMessage", lambda r: "sendTextMessage" not in r),
        ("Usou selfSay", lambda r: "selfSay" in r),
        ("Usou NPCHandler", lambda r: "NPCHandler" in r),
        ("Tem sistema de venda", lambda r: "onBuy" in r or "onSell" in r),
    ])

# ============================================
# AREA 3: HABILIDADES SHC (com exemplo real)
# ============================================
print(f"\n{'='*80}")
print("  AREA 3/3: HABILIDADES SHC (com exemplo real)")
print(f"{'='*80}")

testar("Habilidades SHC", "qwen2.5-coder:7b",
    f"Voce e um desenvolvedor SHC para o SPA do MCR.\n\n"
    f"Formato SHC REAL (copie EXATAMENTE esta estrutura):\n{EXEMPLO_SHC}\n\n"
    f"REGRAS:\n"
    f"- efeitoConfig com tipo, dano (numero), percentual (0.0-1.0), elemento\n"
    f"- postura usa [1], [2], [3] como CHAVES, NAO array\n"
    f"- niveis usa [5], [10], [15], [20]\n"
    f"- NUNCA use campos como danoMinimo/danoMaximo\n",
    "Crie 2 habilidades SHC para o dominio CRISTAL (ID 27): "
    "27001 = Lanca de Cristal (projectile), 27002 = Explosao de Cristal (area_target). "
    "Use COMBAT_ENERGYDAMAGE. Siga o formato SHC do exemplo.",
    [
        ("Usou danoMinimo/danoMaximo", lambda r: "danoMinimo" not in r and "danoMaximo" not in r),
        ("Tem efeitoConfig com tipo", lambda r: "tipo =" in r or '"tipo"' in r),
        ("Postura no formato certo", lambda r: "[1]" in r or "[2]" in r or "[3]" in r),
        ("Niveis no formato certo", lambda r: "[5]" in r or "[10]" in r),
        ("IDs 27001 e 27002", lambda r: "27001" in r and "27002" in r),
    ])

# ============================================
# RESUMO
# ============================================
print(f"\n\n{'='*80}")
print("  RESUMO DA CORRECAO")
print(f"{'='*80}")
print(f"\n  {'Area':<25} {'Status':<10} {'Erros':<10} {'Tempo':<8}")
print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*8}")
for r in RESULTADOS:
    print(f"  {r['area']:<25} {r['status']:<10} {len(r['erros']):<10} {r['tempo']:<8}s")

print(f"\n  Estrategia: fornecer exemplo REAL do formato antes de pedir geracao")
print(f"  Antes: modelo inventava sintaxe (Anchor tag, sendTextMessage, danoMinimo)")
print(f"  Depois: modelo copia o formato exato do exemplo fornecido")
print(f"\n  Resultados salvos em: sandbox/test_correcao/")
print(f"{'='*80}")

with open(os.path.join(SAIDA, "00_resumo.json"), "w", encoding="utf-8") as f:
    json.dump(RESULTADOS, f, ensure_ascii=False, indent=2)
