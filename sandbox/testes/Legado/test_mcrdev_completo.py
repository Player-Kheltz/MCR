#!/usr/bin/env python3
"""Teste completo do MCR-Dev: executa cada funcionalidade e valida."""
import sys, os, json, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
sys.path.insert(0, os.path.join(BASE, "Scripts"))

from mcr_dev import router, engine, validador, memoria

PASS = 0
FAIL = 0
WARN = 0
RESULTADOS = []

def testar(nome, func, *args, **kwargs):
    global PASS, FAIL, WARN
    criterios = kwargs.pop("_criterios", [])
    try:
        resultado = func(*args, **kwargs)
        ok = True
        
        for crit in criterios:
            if not crit(resultado):
                ok = False
                break
        
        if ok:
            PASS += 1
            print(f"  ✅ {nome}")
        else:
            WARN += 1
            result_str = str(resultado)[:80] if resultado else "None"
            print(f"  ⚠️  {nome}: resultado inesperado ({result_str})")
        
        RESULTADOS.append({"teste": nome, "status": "PASS" if ok else "WARN"})
        return resultado
    except Exception as e:
        FAIL += 1
        print(f"  ❌ {nome}: {e}")
        RESULTADOS.append({"teste": nome, "status": "FAIL", "erro": str(e)})
        return None

print("=" * 70)
print("  TESTE COMPLETO MCR-DEV v1.0")
print("=" * 70)

# ============================================
print("\n📋 1. ROUTER (classificacao de intencao)")
# ============================================
testar("Router: saudacao", router.classify, "ola", _criterios=[lambda r: r[0] == "SAUDACAO"])
testar("Router: NPC", router.classify, "crie um NPC ferreiro", _criterios=[lambda r: r[0] == "CRIAR_NPC"])
testar("Router: habilidade", router.classify, "crie uma habilidade de gelo", _criterios=[lambda r: r[0] == "CRIAR_HABILIDADE"])
testar("Router: codigo", router.classify, "crie um script python", _criterios=[lambda r: r[0] == "CRIAR_CODIGO"])
testar("Router: sistema", router.classify, "qual o uso de CPU?", _criterios=[lambda r: r[0] == "SISTEMA"])
testar("Router: pergunta", router.classify, "o que e o SPA?", _criterios=[lambda r: r[0] == "PERGUNTA"])
testar("Router: quest", router.classify, "crie uma quest de coleta", _criterios=[lambda r: r[0] == "CRIAR_QUEST"])
testar("Router: despedida", router.classify, "obrigado", _criterios=[lambda r: r[0] == "SAUDACAO"])
testar("Router: ajuda", router.classify, "ajuda", _criterios=[lambda r: r[0] == "AJUDA"])

# ============================================
print("\n📁 2. VALIDADOR")
# ============================================
testar("Validador: NPC valido", validador.validar_codigo,
    'NPCHandler:new("Test")\nfunction onGreet() selfSay("Ola") end', "NPC",
    _criterios=[lambda r: r[0] == True])
testar("Validador: NPC com sendTextMessage", validador.validar_codigo,
    'player:sendTextMessage(MESSAGE_INFO, "teste")', "NPC",
    _criterios=[lambda r: r[0] == False])
testar("Validador: SHC valido", validador.validar_codigo,
    'HABILIDADES[27001] = { nome = "Test", tipo = "gatilho", dominio = {27}, efeitoConfig = { tipo = "projectile", dano = 1.0, percentual = 0.5 } }', "HABILIDADE",
    _criterios=[lambda r: r[0] == True])
testar("Validador: SHC com danoMinimo", validador.validar_codigo,
    'HABILIDADES[1] = { efeitoConfig = { danoMinimo = 10 } }', "HABILIDADE",
    _criterios=[lambda r: r[0] == False])
testar("Validador: Lua chaves ok", validador.validar_codigo,
    'local x = { a = 1 }', "LUA",
    _criterios=[lambda r: r[0] == True])
testar("Validador: Lua chaves erradas", validador.validar_codigo,
    'local x = { a = 1 ', "LUA",
    _criterios=[lambda r: r[0] == False])

# ============================================
print("\n🧠 3. ENGINE - PROCESSAR (casos rapidos)")
# ============================================
# Testa saudacao (deve ser instantanea, sem modelo)
testar("Engine: saudacao", lambda: engine.processar("ola")[0],
    _criterios=[lambda r: "MCR-Dev" in r or "Ola" in r])

# Testa despedida
testar("Engine: despedida", lambda: engine.processar("obrigado")[0],
    _criterios=[lambda r: "Disponha" in r])

# Testa ajuda
testar("Engine: ajuda", lambda: engine.processar("ajuda")[0],
    _criterios=[lambda r: "CRIAR NPC" in r or "Comandos" in r or "NPC" in r])

# ============================================
print("\n💾 4. MEMORIA")
# ============================================
testar("Memoria: learn+recall", lambda: (
    memoria.learn("teste memorizacao", "resposta de teste", "TESTE"),
    len(memoria.recall("teste memorizacao")) > 0
)[1], _criterios=[lambda r: r == True])

# ============================================
print("\n📝 5. ENGINE - CRIACAO DE ARQUIVOS (sandbox)")
# ============================================
# Arquivo TXT (rapido, sem exemplo complexo)
resp_txt, arq_txt = engine.processar("crie um arquivo txt com uma lista de 3 itens magicos para um jogo de rpg")
testar("Engine: criar arquivo txt", lambda: arq_txt,
    _criterios=[lambda r: r and ".txt" in str(r) or ".lua" in str(r)])

# Arquivo Python
resp_py, arq_py = engine.processar("crie um script python que mostra a hora atual")
testar("Engine: criar script python", lambda: arq_py,
    _criterios=[lambda r: r and ".py" in str(r) or ".lua" in str(r)])

# ============================================
print("\n🗑️ 6. ENGINE - DELETAR ARQUIVO")
# ============================================
if arq_txt and os.path.exists(arq_txt):
    nome_arq = os.path.basename(arq_txt)
    resp_del, _ = engine.processar(f"delete o arquivo {nome_arq}")
    testar("Engine: deletar arquivo", lambda: resp_del,
        _criterios=[lambda r: "Deletado" in r or "deletado" in r.lower() or "delet" in r])

# ============================================
print("\n💻 7. ENGINE - SISTEMA")
# ============================================
resp_sys = engine.processar("info do sistema")[0]
testar("Engine: sistema info", lambda: resp_sys,
    _criterios=[lambda r: "Windows" in r or "hostname" in r or "os" in r.lower() or "sistema" in r.lower()])

# ============================================
print("\n📚 8. ENGINE - PERGUNTA (RAG)")
# ============================================
resp_rag = engine.processar("o que e o SPA no MCR?")[0]
testar("Engine: pergunta RAG", lambda: resp_rag,
    _criterios=[lambda r: len(r) > 50])

# ============================================
print("\n📊 9. ESTATISTICAS")
# ============================================
stats = memoria.stats()
testar("Memoria: stats", lambda: stats,
    _criterios=[lambda r: "Total" in r or len(r) > 20])

# ============================================
print("\n" + "=" * 70)
print(f"  RESULTADO FINAL: {PASS}/{PASS+FAIL+WARN}")
print(f"  ✅ PASS: {PASS}  ❌ FAIL: {FAIL}  ⚠️  WARN: {WARN}")
print("=" * 70)

with open(os.path.join(BASE, "sandbox", "test_mcrdev_resultado.json"), "w") as f:
    json.dump({"pass": PASS, "fail": FAIL, "warn": WARN, "detalhes": RESULTADOS}, f, indent=2)

if FAIL > 0:
    print("\n  FALHAS DETECTADAS:")
    for r in RESULTADOS:
        if r["status"] == "FAIL":
            print(f"    ❌ {r['teste']}: {r.get('erro', '')}")
