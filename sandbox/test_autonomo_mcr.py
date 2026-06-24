#!/usr/bin/env python3
"""
Teste autonomo extensivo dos modelos locais com tarefas REAIS do MCR.
Simula o que cada agente faria no dia-a-dia do projeto.
"""
import json, os, sys, time, urllib.request

BASE = r"E:\Projeto MCR"
sys.path.insert(0, os.path.join(BASE, "scripts"))
HISTORICO = []  # [(agente, modelo, prompt, resposta, tempo, status)]

def chat(modelo, messages, max_tokens=300, temp=0.1):
    payload = json.dumps({"model": modelo, "messages": messages, "stream": False,
        "options": {"temperature": temp, "max_tokens": max_tokens}}).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return data["message"]["content"], dt
    except Exception as e:
        return f"[ERRO] {e}", time.time() - t0

def testar(agente, modelo, system, prompt, max_tokens=300, temp=0.1):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    resp, tempo = chat(modelo, messages, max_tokens, temp)
    
    # Avaliacao basica da resposta
    tem_conteudo = len(resp) > 20 and resp[:5] != "[ERRO]"
    parece_inventado = any(p in resp.lower() for p in ["não encontrei", "nao encontrei", "nao sei"]) if tem_conteudo else False
    status = "✅" if tem_conteudo and not parece_inventado else ("⚠️ Recusou" if parece_inventado else "❌")
    
    HISTORICO.append({
        "agente": agente, "modelo": modelo, "system": system,
        "prompt": prompt, "resposta": resp, "tempo": round(tempo, 1),
        "tamanho": len(resp), "status": status
    })
    
    return resp, tempo

# ============================================
print("=" * 90)
print("  TESTE AUTONOMO EXTENSIVO - MODELOS LOCAIS vs TAREFAS REAIS DO MCR")
print("=" * 90)

# ============================================
# CENARIO 1: EXPLORAR CODIGO (agente explore - phi3.5)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 1: EXPLORAR CODIGO (agente explore)")
print("  Modelo: phi3.5:3.8b")
print("=" * 90)

SYS_EXPLORE = "Voce e um assistente de exploracao de codigo. Use read, grep e glob para buscar informacoes. Responda APENAS com dados reais. NUNCA invente."

# Leitura real de arquivo (vou fornecer o conteudo pra ele)
with open(os.path.join(BASE, "AGENTS.md"), "r", encoding="utf-8") as f:
    agents_content = f.read()[:2000]

r1, t1 = testar("explore", "phi3.5:3.8b", SYS_EXPLORE,
    f"Resuma as principais regras deste arquivo AGENTS.md:\n\n{agents_content[:1500]}", 400)
print(f"\n  >>> Prompt: Resuma as principais regras do AGENTS.md\n  >>> Tempo: {t1}s\n  >>> Resposta: {r1[:300]}")

# ============================================
# CENARIO 2: DEV - CRIAR SCRIPT (agente dev - qwen7b)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 2: CRIAR SCRIPT SIMPLES (agente dev)")
print("  Modelo: qwen2.5-coder:7b")
print("=" * 90)

SYS_DEV = "Voce e um assistente de desenvolvimento. Crie codigo Lua simples. Use recursos que existem no Canary/TFS. NUNCA invente APIs."

r2, t2 = testar("dev", "qwen2.5-coder:7b", SYS_DEV,
    "Crie uma TalkAction !horas em Lua que mostra a hora atual do servidor para o jogador. Use a sintaxe do Canary (revscript).", 500)
print(f"\n  >>> Prompt: Crie TalkAction !horas em Lua\n  >>> Tempo: {t2}s\n  >>> Resposta:\n{r2[:500]}")
print(f"\n  ---> Codigo gerado: {'function' in r2.lower() or 'TalkAction' in r2 or 'onSay' in r2}")

# ============================================
# CENARIO 3: CHAT - ANALISE (agente chat - llama3.1)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 3: ANALISE DE REQUISITOS (agente chat)")
print("  Modelo: llama3.1:8b")
print("=" * 90)

SYS_CHAT = "Voce e um assistente de analise de projetos. Analise requisitos e de sugestoes. Responda em portugues."

r3, t3 = testar("chat", "llama3.1:8b", SYS_CHAT,
    "Preciso adicionar um novo dominio elemental 'Vento' ao SPA. Quais sao os passos necessarios? "
    "Considere: constantes.lua, init_dominios.lua, criacao de habilidades, documentacao.", 500)
print(f"\n  >>> Prompt: Analise para adicionar dominio Vento ao SPA\n  >>> Tempo: {t3}s\n  >>> Resposta: {r3[:400]}")

# ============================================
# CENARIO 4: PLAN - ARQUITETURA (agente plan - deepseek-r1:8b)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 4: PLANEJAR ARQUITETURA (agente plan)")
print("  Modelo: deepseek-r1:8b")
print("=" * 90)

SYS_PLAN = "Analise problemas de arquitetura profundamente. Pense passo a passo antes de responder."

r4, t4 = testar("plan", "deepseek-r1:8b", SYS_PLAN,
    "Precisamos decidir entre 2 abordagens para o sistema de crafting no MCR:\n"
    "A) Sistema baseado em receitas Lua (como o SPA)\n"
    "B) Sistema baseado em banco de dados MySQL\n\n"
    "Analise prós e contras de cada e recomende uma.", 600, 0.2)
print(f"\n  >>> Prompt: Pro/Contras sistemas de crafting\n  >>> Tempo: {t4}s\n  >>> Resposta: {r4[:500]}")

# ============================================
# CENARIO 5: REVIEW - REVISAO (agente review - deepseek-r1:8b)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 5: REVISAO DE CODIGO (agente review)")
print("  Modelo: deepseek-r1:8b")
print("=" * 90)

SYS_REVIEW = "Revise codigo buscando bugs, problemas de seguranca e boas praticas. Seja criterioso."

codigo_revisar = """local function onUse(player, item, fromPosition, target, toPosition, isHotkey)
    if item:getId() == 1234 then
        player:addItem(5678, 1)
        player:sendTextMessage(MESSAGE_INFO_DESCR, "Voce ganhou um item!")
        return true
    end
    if target then
        if target:isPlayer() then
            target:addHealth(-100)
        end
    end
    return false
end"""

r5, t5 = testar("review", "deepseek-r1:8b", SYS_REVIEW,
    f"Revise este codigo Lua do Canary e aponte problemas:\n\n{codigo_revisar}", 500, 0.2)
print(f"\n  >>> Prompt: Revise codigo onUse\n  >>> Tempo: {t5}s\n  >>> Resposta: {r5[:400]}")

# ============================================
# CENARIO 6: DOCS - DOCUMENTACAO (agente docs - qwen7b)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 6: CRIAR DOCUMENTACAO (agente docs)")
print("  Modelo: qwen2.5-coder:7b")
print("=" * 90)

SYS_DOCS = "Crie documentacao clara e concisa em portugues. Inclua exemplos."

r6, t6 = testar("docs", "qwen2.5-coder:7b", SYS_DOCS,
    "Documente esta funcao Lua para outros desenvolvedores:\n\n"
    "function getNivelEfetivo(player, domainId)\n"
    "    local nivel = getNivelDominio(player, domainId)\n"
    "    local bonusSinergia = getBonusSinergia(player, domainId)\n"
    "    return math.min(20, nivel + bonusSinergia)\n"
    "end", 400)
print(f"\n  >>> Prompt: Documente funcao getNivelEfetivo\n  >>> Tempo: {t6}s\n  >>> Resposta: {r6[:400]}")

# ============================================
# CENARIO 7: BUILD - GERAR CODIGO (agente build - qwen7b)
# ============================================
print("\n" + "=" * 90)
print("  CENARIO 7: GERAR CODIGO COMPLETO (agente build)")
print("  Modelo: qwen2.5-coder:7b")
print("=" * 90)

SYS_BUILD = "Implemente codigo funcional seguindo as especificacoes. Use APIs reais do Canary. NUNCA invente."

r7, t7 = testar("build", "qwen2.5-coder:7b", SYS_BUILD,
    "Crie um sistema simples de boost de XP em Lua (revscript) para o Canary:\n"
    "- Command: !boost <quantos_minutos>\n"
    "- Aplica 2x XP para o jogador durante X minutos\n"
    "- Usa storage value para controlar tempo restante\n"
    "- Mostra mensagem ao jogador quando terminar\n", 700)
print(f"\n  >>> Prompt: Sistema boost XP\n  >>> Tempo: {t7}s\n  >>> Resposta:\n{r7[:600]}")

# ============================================
# RELATORIO FINAL
# ============================================
print("\n" + "=" * 90)
print("  RELATORIO FINAL - TESTE AUTONOMO MCR")
print("=" * 90)

print(f"\n  {'Agente':<12} {'Modelo':<20} {'Status':<16} {'Tempo':<8} {'Tam':<6}")
print(f"  {'-'*12} {'-'*20} {'-'*16} {'-'*8} {'-'*6}")

for h in HISTORICO:
    print(f"  {h['agente']:<12} {h['modelo']:<20} {h['status']:<16} {h['tempo']:<8}s {h['tamanho']:<6}")

print(f"\n  {'='*90}")
print(f"  AVALIACAO POR AGENTE:")
print(f"  {'='*90}")

for h in HISTORICO:
    util = "✅" if h['status'] == "✅" else "❌"
    print(f"\n  {util} {h['agente'].upper()} ({h['modelo']}) - {h['tempo']}s - {h['tamanho']} chars")
    print(f"     Prompt: {h['prompt'][:80]}...")
    print(f"     Resposta: {h['resposta'][:150]}...")

# Salva tudo
with open(os.path.join(BASE, "sandbox", "teste_autonomo_mcr_resultado.json"), "w", encoding="utf-8") as f:
    json.dump(HISTORICO, f, ensure_ascii=False, indent=2)
print(f"\n\n  Resultado completo salvo em: sandbox/teste_autonomo_mcr_resultado.json")
print(f"  Total de cenarios: {len(HISTORICO)}")
print(f"  Aprovados: {sum(1 for h in HISTORICO if h['status'] == '✅')}")
print(f"  Recusas (seguro): {sum(1 for h in HISTORICO if 'Recusou' in h['status'])}")
print(f"  Erros: {sum(1 for h in HISTORICO if '❌' in h['status'])}")
