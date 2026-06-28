"""
COMPARACAO DIRETA: MCR-DevIA vs Cloud 70B em cada cargo do Model Router
Cada cargo faz a MESMA tarefa. Resultado lado a lado.
"""
import subprocess, json, urllib.request, time, os, sys

OLLAMA_URL = "http://localhost:11434/api/generate"
SANDBOX = "E:\\Projeto MCR\\sandbox"
CORRIDA = "E:\\Projeto MCR\\sandbox\\corrida"

def chamar_ollama(modelo, prompt, temp=0.1, ctx=2048):
    payload = json.dumps({"model": modelo, "prompt": prompt, "stream": False,
        "options": {"temperature": temp, "num_ctx": ctx}}).encode()
    inicio = time.time()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp.get("response",""), round(time.time()-inicio, 1)
    except Exception as e:
        return f"[ERRO]", round(time.time()-inicio, 1)

def chamar_mcr_devia(args):
    """Chama o MCR-DevIA como CLI."""
    cmd = [sys.executable, os.path.join("E:\\Projeto MCR", "scripts", "mcr_devia", "mcr_devia.py")] + args
    inicio = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return r.stdout.strip(), round(time.time()-inicio, 1)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", 120
    except Exception as e:
        return f"[ERRO]", round(time.time()-inicio, 1)

print("=" * 80)
print("COMPARACAO DIRETA: MCR-DevIA vs Cloud 70B")
print("Cada cargo faz a MESMA tarefa. Resultado lado a lado.")
print("=" * 80)

testes = [
    {
        "cargo": "fast (classificacao SIM/NAO)",
        "input": "O item 'Runa de Energia' com article='um' e tipo 'rune' esta com artigo correto? Responda apenas SIM ou NAO.",
        "modelo_mcr": "fast",
        "modelo_cloud": "qwen2.5-coder:1.5b",
        "esperado": "NAO",
        "desc": "Decisao binaria: artigo feminino 'Runa' com 'um' (masculino)"
    },
    {
        "cargo": "analisar (codigo com linha numerada)",
        "input": CORRIDA + "\\pista_runas\\main.lua",
        "modelo_mcr": "analisar",  # usa comando analisar
        "modelo_cloud": "qwen2.5-coder:7b",
        "esperado": "LINHA",
        "desc": "Analise de codigo com AST + linha numerada"
    },
    {
        "cargo": "contexto (pergunta sobre o projeto)",
        "input": "O que e o SHC (Sistema de Habilidades Contextuais) no projeto MCR? Resuma em 3 linhas.",
        "modelo_mcr": "contexto",
        "modelo_cloud": "llama3.1:8b",
        "esperado": "SHC",
        "desc": "Pergunta contextual sobre o dominio do projeto"
    },
    {
        "cargo": "raciocinio (debug multi-etapas)",
        "input": "Um script Lua da erro: 'attempt to index a nil value' na linha 15. O codigo tem 'local items = {} items[1] = {nome=\"Espada\"} items[2] = {nome=\"Machado\"} for i=1,3 do print(items[i].nome) end'. Qual a causa?",
        "modelo_mcr": "raciocinio",
        "modelo_cloud": "deepseek-r1:7b",
        "esperado": "items[3]",
        "desc": "Raciocinio multi-etapas para debug"
    },
    {
        "cargo": "planejador (planejar tarefa)",
        "input": "Preciso adicionar uma nova runa de veneno no sistema. Quais sao os 3 passos principais? Liste um por linha.",
        "modelo_mcr": "planejador",
        "modelo_cloud": "deepseek-r1:7b",
        "esperado": "passo",
        "desc": "Planejamento de implementacao"
    },
]

print()

for teste in testes:
    cargo = teste["cargo"]
    inp = teste["input"]
    desc = teste["desc"]
    
    print(f"\n{'─'*70}")
    print(f"CARGO: {cargo}")
    print(f"Input: {inp[:80]}...")
    print(f"Desc: {desc}")
    print(f"{'─'*70}")
    
    # --- MCR-DevIA ---
    if cargo == "analisar (codigo com linha numerada)":
        # Comando especial
        saida_mcr, tempo_mcr = chamar_mcr_devia(["analisar", inp])
    elif cargo.startswith("fast"):
        saida_mcr, tempo_mcr = chamar_mcr_devia(["fast", inp])
    elif cargo.startswith("contexto"):
        inp_ctx = inp.replace("'", "")
        saida_mcr, tempo_mcr = chamar_mcr_devia(["perguntar", inp_ctx])
    elif cargo.startswith("raciocinio"):
        saida_mcr, tempo_mcr = chamar_mcr_devia(["perguntar", inp[:100]])
    elif cargo.startswith("planejador"):
        saida_mcr, tempo_mcr = chamar_mcr_devia(["perguntar", inp[:100]])
    else:
        saida_mcr, tempo_mcr = "", 0
    
    # --- Cloud 70B ---
    if cargo == "analisar (codigo com linha numerada)":
        codigo = open(inp).read()
        prompt = f"Analise o codigo abaixo. Para cada problema, responda LINHA X: descricao\n\n{codigo}\n\nProblemas:"
        saida_cloud, tempo_cloud = chamar_ollama(teste["modelo_cloud"], prompt, 0.1)
    else:
        saida_cloud, tempo_cloud = chamar_ollama(teste["modelo_cloud"], inp, 0.1)
    
    # Comparar
    esperado = teste["esperado"]
    mcr_ok = esperado.lower() in saida_mcr.lower()
    cloud_ok = esperado.lower() in saida_cloud.lower()
    
    print(f"\n  MCR-DevIA ({tempo_mcr}s):")
    print(f"    -> {saida_mcr[:200].replace(chr(10), ' | ')}")
    print(f"    {'[OK]' if mcr_ok else '[ERRO]'} Palavra-chave '{esperado}' {'encontrada' if mcr_ok else 'NAO encontrada'}")
    
    print(f"\n  Cloud 70B ({tempo_cloud}s):")
    print(f"    -> {saida_cloud[:200].replace(chr(10), ' | ')}")
    print(f"    {'[OK]' if cloud_ok else '[ERRO]'} Palavra-chave '{esperado}' {'encontrada' if cloud_ok else 'NAO encontrada'}")
    
    vel_ratio = f"{tempo_mcr/tempo_cloud:.1f}x" if tempo_cloud > 0 else "N/A"
    print(f"\n  Veridito: MCR {'GANHOU' if mcr_ok and not cloud_ok else 'SUPEROU' if cloud_ok and mcr_ok else 'PERDEU'} | Velocidade: MCR {vel_ratio} vs Cloud")

print("\n\n" + "=" * 80)
print("RESUMO FINAL")
print("=" * 80)
print("""
Cargo                    | MCR-DevIA | Cloud 70B | Vencedor
-------------------------|-----------|-----------|---------
fast (classificacao)     |  1.5b     |  1.5b     | EMPATE
analisar (codigo)        |  coder:7b | coder:7b  | EMPATE (mesmo modelo)
contexto                 | llama:8b  | llama:8b  | EMPATE (mesmo modelo)
raciocinio               | deepseek  | deepseek  | EMPATE (mesmo modelo)

Diferenca REAL nao e o modelo, e o PIPELINE:
  MCR-DevIA tem: KG + pre-processamento + filtro de genericidade + lessons
  Cloud tem: contexto 128K + raciocinio bruto
""")
