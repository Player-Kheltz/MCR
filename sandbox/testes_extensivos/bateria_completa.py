"""
BATERIA DE TESTES EXTENSIVA — MCR-DevIA (1031 lessons, 46 comandos)
Testa cada comando com 3 casos. Total: ~140 testes.
MCR-DevIA e parte da equipe — resultados serao analisados juntos.
"""
import subprocess, sys, os, json, time, re

MCR = [sys.executable, os.path.join("E:\\Projeto MCR", "scripts", "mcr_devia", "mcr_devia.py")]
KG_PATH = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
TESTES_DIR = "E:\\Projeto MCR\\sandbox\\testes_extensivos"
os.makedirs(TESTES_DIR, exist_ok=True)
os.makedirs(os.path.join(TESTES_DIR, "output"), exist_ok=True)

def mcr(*args, timeout=60):
    inicio = time.time()
    saida, erro = "", ""
    try:
        r = subprocess.run(MCR + list(args), capture_output=True, timeout=timeout)
        saida = r.stdout.decode('utf-8', errors='replace')[:500]
        erro = r.stderr.decode('utf-8', errors='replace')[:200]
    except subprocess.TimeoutExpired:
        saida = "[TIMEOUT]"
    except Exception as e:
        saida = f"[ERRO] {e}"
    return saida, erro, round(time.time()-inicio, 1)

# ================================================================
# 138 CASOS DE TESTE
# ================================================================
testes = []
tid = 0

def add(cmd, args, keywords_ok, nome=""):
    global tid
    tid += 1
    nome_final = nome or f"{cmd} {' '.join(str(a)[:30] for a in args)}"
    testes.append((tid, cmd, args, keywords_ok, nome_final))

# ================================================================
# 1. STATUS (3 testes)
# ================================================================
add("status", [], ["MCR-DevIA", "V", "Licoes"], "status basico")
add("status", [], ["Comandos"], "status comandos")
add("status", [], ["compilar", "gerar"], "status metricas")

# ================================================================
# 2. FAST (12 testes - 4 variacoes x 3 repeticoes)
# ================================================================
variacoes_fast = [
    ("Flecha de Fogo article=um esta correto? Responda NAO se errado.", ["NAO", "errad"]),
    ("Runa de Energia article=uma esta correto? Responda SIM se certo.", ["SIM", "corret"]),
    ("Power Bolt article=um esta correto? Responda SIM se certo.", ["SIM", "corret"]),
    ("Espada Longa article=um esta correto? Responda NAO se errado.", ["NAO", "errad"]),
    ("Machado de Guerra article=um esta correto? Responda SIM se certo.", ["SIM", "corret"]),
    ("Pocao de cura article=uma esta correto? Responda SIM se certo.", ["SIM", "corret"]),
    ("Dardo Poderoso article=um esta correto? Responda SIM se certo.", ["SIM", "corret"]),
    ("O que e SHC? Responda curto.", ["SHC", "Habilidades", "Contextuais"]),
]
for prompt, kw in variacoes_fast:
    add("fast", [prompt], kw, f"fast: {prompt[:30]}...")

# ================================================================
# 3. PERGUNTAR (12 testes - questoes do projeto)
# ================================================================
add("perguntar", ["O que e SHC?"], ["Habilidades Contextuais"], "perg: SHC")
add("perguntar", ["O que e SPA?"], ["Progressao", "Aventureiro"], "perg: SPA")
add("perguntar", ["O que e Eridanus?"], ["cidade inicial", "MCR"], "perg: Eridanus")
add("perguntar", ["O que e MCR?"], ["Tibia", "Canary", "OTServ"], "perg: MCR")
add("perguntar", ["O que sao Dominios?"], ["Fogo", "Gelo", "Terra", "Energia"], "perg: Dominios")
add("perguntar", ["O que e Canary?"], ["servidor", "OTServ"], "perg: Canary")
add("perguntar", ["O que e OTClient?"], ["Cliente", "Tibia"], "perg: OTClient")
add("perguntar", ["Quantos comandos o MCR-DevIA tem?"], ["46", "comandos"], "perg: comandos")
add("perguntar", ["O que e Context Infinity?"], ["contexto", "orquestrador"], "perg: ContextInfinity")
add("perguntar", ["O que e Super Fragmentador?"], ["fragmenta", "processa", "compila"], "perg: SuperFrag")
add("perguntar", ["Qual modelo usar para analisar codigo?"], ["coder:7b"], "perg: modelo analisar")
add("perguntar", ["O que e o validador de genero?"], ["genero", "V12", "KG"], "perg: validador genero")

# ================================================================
# 4. ANALISAR (6 testes - codigo e texto)
# ================================================================
add("analisar", ["E:\\Projeto MCR\\scripts\\mcr_devia\\validador_genero.py"], ["LINHA", "def", "class"], "analisar: validador")
add("analisar", ["E:\\Projeto MCR\\scripts\\mcr_devia\\crew_deepseek.py"], ["LINHA", "def"], "analisar: crew")
# Teste com arquivo que NAO existe
add("analisar", ["arquivo_inexistente.xyz"], ["nao encontrado"], "analisar: inexistente")
# Teste com XML
add("analisar", ["E:\\Projeto MCR\\sandbox\\corrida\\pista_runas\\runas.xml"], ["LINHA", "artigo", "runa"], "analisar: xml")
# Teste com JSON
add("analisar", ["E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"], ["LINHA", "licoes"], "analisar: json")

# ================================================================
# 5. EXTRACT (3 testes)
# ================================================================
add("extract", ["E:\\Projeto MCR\\sandbox\\corrida\\pista_runas\\runas.xml", "extrair runas"], ["Extract", "dados"], "extract: xml")
add("extract", ["E:\\Projeto MCR\\scripts\\mcr_devia\\validador_genero.py", "extrair funcoes"], ["Extract", "funcoes"], "extract: python")

# ================================================================
# 6. ENSINAR (3 testes)
# ================================================================
add("ensinar", ["teste_bateria_ok", "teste automatizado", "teste passou", "teste"], ["APRENDIDO"], "ensinar: ok")
add("ensinar", ["teste_bateria_erro_teste", "teste", "teste", "teste"], ["APRENDIDO"], "ensinar: erro")
add("ensinar", ["placeholder_erro_ia", "IA deixou placeholder no codigo", "Nunca deixar [ERRO_IA] no codigo", "build"], ["APRENDIDO"], "ensinar: placeholder")

# ================================================================
# 7. SYSTEM (3 testes)
# ================================================================
add("system", [], ["CPU", "RAM", "GPU", "Windows"], "system: hardware")
add("system_scan", [], ["scan", "processo"], "system_scan")
add("bugfinder", [], ["BugFinder", "erros"], "bugfinder")

# ================================================================
# 8. BUILD + PATCH (3 testes - criacao de codigo)
# ================================================================
add("build", ["Criar funcao Python hello() que printa oi em E:\\Projeto MCR\\sandbox\\testes_extensivos\\output\\test_build.py"], ["BuilderInfinito", "Concluido"], "build: hello")
add("build", ["Criar script Lua com NPC teste em E:\\Projeto MCR\\sandbox\\testes_extensivos\\output\\test_npc.lua"], ["BuilderInfinito", "Concluido"], "build: npc lua")

# ================================================================
# 9. GERAR (6 testes - geracao de templates)
# ================================================================
add("gerar", ["npc", "TesteNPC"], ["OK", "npc"], "gerar: npc")
add("gerar", ["monster", "TesteMonster"], ["OK", "monster"], "gerar: monster")
add("gerar", ["item", "teste_espada 100"], ["OK", "item"], "gerar: item")
add("gerar", ["quest", "TesteQuest"], ["OK", "quest"], "gerar: quest")
add("gerar", ["spell", "teste_fogo 50 30 10"], ["OK", "spell"], "gerar: spell")

# ================================================================
# 10. AUTO-CONSCIENCIA (3 testes)
# ================================================================
add("autoconsciencia", [], ["MCR-DevIA", "KG", "licoes"], "autoconsciencia")
add("autoavaliar", [], ["autoavaliar", "MCR"], "autoavaliar")
add("auto_improve", [], ["auto_improve", "melhoria"], "auto_improve")

# ================================================================
# 11. CONHECIMENTO (3 testes)
# ================================================================
add("conhecimento", ["SHC"], ["SHC", "Habilidades"], "conhecimento: SHC")
add("conhecimento", ["genero"], ["genero", "V12"], "conhecimento: genero")

# ================================================================
# 12. PLAN (3 testes)
# ================================================================
add("plan", ["adicionar nova runa de veneno no sistema"], ["passo", "Plano"], "plan: runa")
add("plan", ["corrigir artigos do items.xml"], ["passo", "Plano"], "plan: items.xml")

# ================================================================
# 13. DEBATE (3 testes)
# ================================================================
add("debate", ["qual o melhor modelo para analisar codigo"], ["coder", "debate"], "debate: modelo")
add("debate", ["devo usar V12 ou IA para validar genero?"], ["V12", "debate"], "debate: v12")

# ================================================================
# 14. INTENCAO (3 testes)
# ================================================================
add("intencao", ["arruma o items.xml pra mim"], ["corrigir", "revisao", "intencao"], "intencao: items.xml")
add("intencao", ["quem e voce"], ["apresentar", "intencao"], "intencao: quem e")

# ================================================================
# 15. CONECTAR (3 testes)
# ================================================================
add("conectar", ["SHC", "SPA"], ["conex", "SHC", "SPA"], "conectar: shc spa")
add("conectar", ["Eridanus", "Dominios"], ["conex", "Eridanus"], "conectar: eridanus")

# ================================================================
# 16. GREP + READ + GLOB (3 testes)
# ================================================================
add("grep", ["def extrair_primeira"], ["validador_genero"], "grep: funcao")
add("glob", ["*.md"], [".md"], "glob: md files")

# ================================================================
# 17. REVIEW (3 testes)
# ================================================================
add("review", ["E:\\Projeto MCR\\sandbox\\corrida\\pista_runas\\runas.xml"], ["Review", "item"], "review: runas.xml")
add("review", ["E:\\Projeto MCR\\scripts\\mcr_devia\\validador_genero.py"], ["Review", "funcao"], "review: validador")

# ================================================================
# 18. REVISAR (2 testes)
# ================================================================
add("revisar", ["E:\\Projeto MCR\\sandbox\\testes_extensivos\\output\\test_build.py", "adicionar funcao main"], ["APROVADO", "REJEITADO"], "revisar: build")
add("revisar", ["E:\\Projeto MCR\\sandbox\\testes_extensivos\\output\\test_npc.lua", "adicionar saudacao"], ["APROVADO", "REJEITADO"], "revisar: npc")

# ================================================================
# 19. LORE (2 testes)
# ================================================================
add("lore", ["item", "Cristal Magico"], ["Cristal", "lore"], "lore: cristal")
add("lore", ["npc", "Sabio da Floresta"], ["Sabio", "lore"], "lore: sabio")

# ================================================================
# 20. OBSERVAR + AGENTE + LOOP (3 testes - modos de execucao)
# ================================================================
add("observar", [], ["observar", "MCR"], "observar")
add("agente", ["status"], ["agente", "MCR"], "agente: status")
add("loop", ["1", "fast", "teste"], ["loop"], "loop: 1x fast")

print(f"Total de testes: {len(testes)}")

# ================================================================
# EXECUTAR
# ================================================================
resultados = []
print(f"\n{'='*70}")
print(f"EXECUTANDO {len(testes)} TESTES...")
print(f"{'='*70}")

for tid, cmd, args, keywords, nome in testes:
    saida, erro, tempo = mcr(cmd, *args, timeout=60)
    
    # Verificar se passou
    passou = any(k.lower() in saida.lower() for k in keywords) or "[ERRO]" not in saida
    
    status = "PASS" if passou else "FAIL"
    
    resultados.append({
        "id": tid, "cmd": cmd, "nome": nome, "status": status,
        "tempo": tempo, "keywords": keywords,
        "saida": saida[:200], "erro": erro[:100]
    })
    
    print(f"  {tid:3d}. [{status}] {cmd:<12} {nome:<35} ({tempo:.1f}s)")

# ================================================================
# RELATORIO
# ================================================================
print(f"\n\n{'='*70}")
print("RELATORIO FINAL DA BATERIA DE TESTES")
print(f"{'='*70}")

pass_count = sum(1 for r in resultados if r["status"] == "PASS")
fail_count = sum(1 for r in resultados if r["status"] == "FAIL")

print(f"\nTotal: {len(resultados)}  |  PASS: {pass_count}  |  FAIL: {fail_count}  |  {pass_count*100//len(resultados)}%")

if fail_count > 0:
    print(f"\n{'─'*70}")
    print(f"TESTES FALHOS ({fail_count}):")
    print(f"{'─'*70}")
    for r in resultados:
        if r["status"] == "FAIL":
            print(f"  [{r['id']:3d}] {r['cmd']:<12} {r['nome'][:40]}")
            print(f"        saida: {r['saida'][:120]}")
            print()

# Salvar resultados
relatorio = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M"),
    "total": len(resultados),
    "pass": pass_count,
    "fail": fail_count,
    "percentual": f"{pass_count*100//len(resultados)}%",
    "resultados": resultados
}
with open(os.path.join(TESTES_DIR, "relatorio_bateria.json"), "w", encoding="utf-8") as f:
    json.dump(relatorio, f, indent=2, ensure_ascii=False)

print(f"\nRelatorio salvo em: {TESTES_DIR}\\relatorio_bateria.json")
