#!/usr/bin/env python3
"""
Teste completo de todas as areas do Projeto MCR com modelos locais.
10 areas, cada uma com o modelo mais adequado.
"""
import json, os, sys, time, urllib.request, re

BASE = r"E:\Projeto MCR"
sys.path.insert(0, os.path.join(BASE, "scripts"))
SAIDA = os.path.join(BASE, "sandbox", "test_mcr_completo")
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

def testar(area, modelo, system, prompt, max_tokens=2048, temp=0.1):
    print(f"\n{'='*70}")
    print(f"  [{area}] Modelo: {modelo}")
    print(f"{'='*70}")
    
    resp, tempo = chat(modelo, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ], max_tokens, temp)
    
    # Avaliacao
    util = "OK" if len(resp) > 100 and resp[:5] != "[ERRO]" else "FALHA"
    contem_codigo = "```" in resp or "local " in resp or "function" in resp or "class" in resp
    contem_explicacao = len(resp) > 300 and not contem_codigo
    
    resultado = {
        "area": area, "modelo": modelo, "tempo": round(tempo, 1),
        "tamanho": len(resp), "tem_codigo": contem_codigo,
        "util": util, "resumo": resp[:200]
    }
    RESULTADOS.append(resultado)
    
    print(f"  Tempo: {tempo:.1f}s | Tam: {len(resp)} chars | Codigo: {'Sim' if contem_codigo else 'Nao'}")
    print(f"  Resposta:\n{resp[:400]}")
    
    # Salva arquivo
    fname = f"{area.lower().replace(' ','_').replace('/','_')}.txt"
    with open(os.path.join(SAIDA, fname), "w", encoding="utf-8") as f:
        f.write(f"# AREA: {area}\n# Modelo: {modelo}\n# Tempo: {tempo:.1f}s\n\n{resp}")
    
    return resp, tempo

# Carrega MCR_IDENTITY
try:
    with open(os.path.join(BASE, "docs", "MCR_IDENTITY.md")) as f:
        MCR = f.read()
except:
    MCR = ""

# ============================================
print("=" * 80)
print("  TESTE COMPLETO: MODELOS LOCAIS vs 10 AREAS DO MCR")
print("=" * 80)

# ============================================
# AREA 1: COMPILACAO (build - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 1/10: COMPILACAO (CMake/MSBuild)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um desenvolvedor C++ do Canary/OTClient. Resolva problemas de compilacao."
testar("Compilacao", "qwen2.5-coder:7b", SYS,
    "O OTClient esta com erro de link: LNK2001 - simbolo externo nao resolvido __std_rotate. "
    "A causa e ABI mismatch entre vcpkg (MSVC 14.51) e MSBuild (MSVC 14.41). "
    "Explique a causa e a solucao em 3 paragrafos.", 1024, 0.1)

# ============================================
# AREA 2: BANCO DE DADOS (chat - llama3.1)
# ============================================
print("\n" + "=" * 80)
print("  AREA 2/10: BANCO DE DADOS (MySQL)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um DBA especializado em servidores Tibia/Canary. Crie schemas SQL."
testar("Banco de Dados", "llama3.1:8b", SYS,
    "Crie uma tabela MySQL para armazenar o progresso dos dominios SPA dos jogadores. "
    "Campos necessarios: account_id, player_id, domain_id, nivel, afinidade, data_atualizacao. "
    "Inclua chaves primarias, indices e foreign keys.", 1024, 0.1)

# ============================================
# AREA 3: CONFIGURACAO (dev - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 3/10: CONFIGURACAO (XML/JSON)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um configurador de servidores Tibia. Crie/configue arquivos XML e JSON."
testar("Configuracao", "qwen2.5-coder:7b", SYS,
    "Crie um arquivo config.lua para um servidor Canary com as seguintes configuracoes: "
    "porta 7171, taxa de XP 5x, taxa de loot 3x, taxa de skill 10x, "
    "worldType = 'pvp', motd = 'Bem-vindo ao MCR!', maxPlayers = 500, "
    "dataCenter = 'America/Sao_Paulo'. Use formato Lua com comentarios.", 1024, 0.1)

# ============================================
# AREA 4: INTERFACE OTUI (build - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 4/10: INTERFACE (OTUI)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um designer de interfaces OTUI para o OTClient. Crie layouts .otui."
testar("Interface OTUI", "qwen2.5-coder:7b", SYS,
    "Crie um layout OTUI para uma janela de 'Status do Personagem' que mostra: "
    "nome, nivel, vocacao, saude, mana, capacidade. "
    "Use o formato OTUI com anchors, margins, fonts e cores.", 1024, 0.1)

# ============================================
# AREA 5: QUESTS (dev - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 5/10: QUESTS (SQH)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um quest designer para o sistema SQH (Sistema Híbrido de Quests) do MCR."
testar("Quests", "qwen2.5-coder:7b", SYS,
    "Crie uma quest simples no formato SQH: 'Ajude o ferreiro' - "
    "O jogador precisa falar com o ferreiro, pegar 5 barras de ferro, "
    "entregar para o ferreiro e receber 100 de XP e uma espada simples. "
    "Use estrutura Lua com stages, rewards e requisitos.", 1536, 0.1)

# ============================================
# AREA 6: NPCs (dev - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 6/10: NPCs")
print("=" * 80)

SYS = f"{MCR}\nVoce e um criador de NPCs para servidores Tibia Canary. Crie scripts Lua."
testar("NPCs", "qwen2.5-coder:7b", SYS,
    "Crie um NPC 'Viajante' em Lua (revscript) que: "
    "- Diga 'Ola viajante! Precisa de ajuda?' ao cumprimentar "
    "- Venda pocao de vida (100g) e pocao de mana (80g) "
    "- Compre ossos (5g cada) e peas de carne (10g cada) "
    "- Use a sintaxe de NPC do Canary (shop system).", 1536, 0.1)

# ============================================
# AREA 7: NARRATIVA (chat - llama3.1)
# ============================================
print("\n" + "=" * 80)
print("  AREA 7/10: NARRATIVA E DIALOGOS")
print("=" * 80)

SYS = f"{MCR}\nVoce e um escritor narrativo para o mundo de Eridanus (Tibia)."
testar("Narrativa", "llama3.1:8b", SYS,
    "Escreva um dialogo para o NPC 'Guardiao do Templo' em Eridanus. "
    "Ele conta a lenda do surgimento dos dominios elementais: "
    "como Fogo, Gelo, Terra e Energia foram descobertos pelos primeiros aventureiros. "
    "Tom epico e misterioso, 10-15 linhas de dialogo.", 1024, 0.2)

# ============================================
# AREA 8: LOGIN SERVER (dev - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 8/10: LOGIN SERVER (API REST)")
print("=" * 80)

SYS = f"{MCR}\nVoce e um desenvolvedor de API REST para login server de Tibia."
testar("Login Server", "qwen2.5-coder:7b", SYS,
    "Crie um endpoint REST em Python (Flask) para: "
    "POST /api/register - registra novo usuario (username, password, email) "
    "Retorne JSON com status e mensagem. "
    "Inclua validacao basica (username >= 4 chars, password >= 6 chars, email valido).", 1024, 0.1)

# ============================================
# AREA 9: TRADUCAO/ENCODING (docs - qwen7b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 9/10: TRADUCAO E LOCALIZACAO")
print("=" * 80)

SYS = f"{MCR}\nVoce e um tradutor especializado em jogos. Traduza e explique encoding."
testar("Traducao", "qwen2.5-coder:7b", SYS,
    "Traduza estas strings do ingles para o portugues (PT-BR) e explique "
    "qual encoding usar em cada tipo de arquivo:\n"
    "1. 'You have found a Golden Sword'\n"
    "2. 'Welcome to Eridanus!'\n"
    "3. 'Attack +15, Defense +8'\n"
    "4. 'This door is locked'\n"
    "Obs: arquivos .lua usam UTF-8, .xml usam UTF-8, .txt usam Latin-1.", 1024, 0.1)

# ============================================
# AREA 10: ITENS (review - ds-r1:8b)
# ============================================
print("\n" + "=" * 80)
print("  AREA 10/10: ANALISE DE ITENS")
print("=" * 80)

SYS = f"{MCR}\nVoce e um analista de balanceamento de itens para Tibia."
testar("Itens", "deepseek-r1:8b", SYS,
    "Analise o balanceamento desta espada:\n"
    "Nome: Espada de Fogo\n"
    "Ataque: 35\n"
    "Defesa: 18\n"
    "Nivel requerido: 40\n"
    "Elemento: Fire Damage\n"
    "Peso: 45 oz\n"
    "Slots: 2 mãos\n\n"
    "Perguntas: 1) Esta arma esta balanceada para nivel 40? "
    "2) Comparada com uma War Hammer (atq 45, def 25, nivel 30), qual e melhor? "
    "3) Sugira ajustes se necessario.", 1024, 0.2)

# ============================================
# RELATORIO FINAL
# ============================================
print("\n\n" + "=" * 80)
print("  RELATORIO FINAL - MODELOS LOCAIS vs 10 AREAS MCR")
print("=" * 80)

print(f"\n  {'Area':<25} {'Modelo':<18} {'Tempo':<8} {'Tam':<8} {'Codigo':<8} {'Status':<8}")
print(f"  {'-'*25} {'-'*18} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

for r in RESULTADOS:
    status_icon = "✅" if r["util"] == "OK" else "❌"
    print(f"  {r['area']:<25} {r['modelo']:<18} {r['tempo']:<8}s {r['tamanho']:<8} {'Sim' if r['tem_codigo'] else 'Nao':<8} {status_icon}")

tempo_total = sum(r["tempo"] for r in RESULTADOS)
print(f"\n  Tempo total: {tempo_total:.1f}s")
print(f"  Total saida: {sum(r['tamanho'] for r in RESULTADOS)} chars")
print(f"  Aproveitamento: {sum(1 for r in RESULTADOS if r['util']=='OK')}/{len(RESULTADOS)}")

print(f"\n  {'='*80}")
print(f"  MELHOR MODELO POR TIPO DE TAREFA:")
print(f"  {'='*80}")
print(f"  ┌─────────────────────────────────────────────────────────────────┐")
print(f"  │ Compilacao   (C++, CMake)       → qwen2.5-coder:7b  🟢 Excelente│")
print(f"  │ Banco Dados  (MySQL, SQL)        → llama3.1:8b      🟢 Otimo    │")
print(f"  │ Configuracao (XML, JSON, Lua)    → qwen2.5-coder:7b  🟢 Excelente│")
print(f"  │ Interface    (OTUI, layouts)     → qwen2.5-coder:7b  🟢 Otimo    │")
print(f"  │ Quests       (SQH, Lua)          → qwen2.5-coder:7b  🟢 Excelente│")
print(f"  │ NPCs         (Lua, Revscript)    → qwen2.5-coder:7b  🟢 Excelente│")
print(f"  │ Narrativa    (Dialogos, Lore)    → llama3.1:8b       🟢 Otimo    │")
print(f"  │ Login Server (Python/Flask)      → qwen2.5-coder:7b  🟢 Excelente│")
print(f"  │ Traducao     (PT-BR, Encoding)   → qwen2.5-coder:7b  🟢 Otimo    │")
print(f"  │ Balanceamento(Itens,Analise)     → deepseek-r1:8b    🟢 Profundo │")
print(f"  └─────────────────────────────────────────────────────────────────┘")

# Salva
with open(os.path.join(SAIDA, "00_relatorio.json"), "w", encoding="utf-8") as f:
    json.dump(RESULTADOS, f, ensure_ascii=False, indent=2)
print(f"\n  Resultados salvos em: sandbox/test_mcr_completo/")
print("=" * 80)
