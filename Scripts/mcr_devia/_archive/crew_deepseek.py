"""
DeepSeek Crew Validator: deepseek-r1:7b + validador Python
Se deepseek alucinar, Python detecta e fallback para coder:7b

Fluxo:
  1. deepseek-r1:7b gera resposta (com thinking tokens)
  2. Validador Python verifica:
     - Se é código: tenta compilar (AST para Python, regex para Lua)
     - Se é texto: verifica se termos inventados existem no KG
  3. Se validação falhar → fallback coder:7b
  4. Se validação passar → usa resposta do deepseek
"""
import urllib.request, json, time, re, sys, os, ast

OLLAMA_URL = "http://localhost:11434/api/generate"

def chamar(modelo, prompt, temp=0.1, ctx=2048, timeout=120):
    payload = json.dumps({"model": modelo, "prompt": prompt, "stream": False,
        "options": {"temperature": temp, "num_ctx": ctx}}).encode()
    inicio = time.time()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(resp).get("response",""), round(time.time()-inicio, 1)
    except Exception as e:
        return f"[ERRO] {e}", round(time.time()-inicio, 1)


def validar_codigo_python(codigo):
    """Valida código Python com AST. Retorna (valido, erro)."""
    try:
        ast.parse(codigo)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"


def validar_codigo_lua(codigo):
    """Valida código Lua com regras básicas (sem compilador nativo)."""
    # Verifica estrutura básica: function, end, then, etc.
    problemas = []
    if codigo.count("function") != codigo.count("end"):
        problemas.append("function/end mismatch")
    if codigo.count("if") != codigo.count("end"):
        # Lua usa end para if também
        ends = codigo.count("end")
        functions = codigo.count("function")
        ifs = codigo.count("if")
        if ends < functions + ifs:
            problemas.append(f"if/function sem end")
    if codigo.count("(") != codigo.count(")"):
        problemas.append("parentheses mismatch")
    return len(problemas) == 0, "; ".join(problemas) if problemas else ""


def validar_contra_kg(resposta, kg_path=None):
    """Valida resposta de texto contra o KG (verifica se inventou termos)."""
    if not kg_path or not os.path.exists(kg_path):
        return True, ""
    
    with open(kg_path, "r", encoding="utf-8") as f:
        kg = json.load(f)
    
    termos_compostos = set(re.findall(r"[A-Z][a-z]+\s+[A-Z][a-z]+", resposta))
    suspeitos = []
    for termo in termos_compostos:
        tl = termo.lower().strip()
        existe = False
        for l in kg.get("licoes", []):
            texto = (l.get("erro","")+" "+l.get("solucao","")+" "+l.get("causa","")+" "+l.get("ctx","")).lower()
            if tl in texto:
                existe = True
                break
        if not existe:
            suspeitos.append(termo)
    
    if suspeitos:
        return False, f"Termos inventados: {suspeitos}"
    return True, ""


def crew_deepseek(prompt, tarefa="code", kg_path=None):
    """
    deepseek-r1:7b + validador Python.
    Se validacao falhar, fallback para qwen2.5-coder:7b.
    
    Retorna (resposta, modelo_usado, tempo, status)
    """
    print(f"  [Crew] deepseek-r1:7b processando...")
    resp_ds, tempo_ds = chamar("deepseek-r1:7b", prompt, 0.1, 2048)
    
    if resp_ds.startswith("[ERRO]"):
        print(f"  [Crew] deepseek falhou ({tempo_ds}s). Fallback coder:7b...")
        resp_coder, tempo_coder = chamar("qwen2.5-coder:7b", prompt, 0.1, 2048)
        return resp_coder, "qwen2.5-coder:7b", tempo_coder, "fallback_erro"
    
    # Validar conforme o tipo de tarefa
    valido = True
    motivo = ""
    
    if tarefa == "code":
        # Detecta se e Python ou Lua
        if "def " in resp_ds or "import " in resp_ds or "class " in resp_ds:
            valido, motivo = validar_codigo_python(resp_ds)
        elif "function " in resp_ds or "local " in resp_ds:
            valido, motivo = validar_codigo_lua(resp_ds)
        else:
            # Codigo generico - verifica se parece codigo
            if not any(c in resp_ds for c in ['(', ')', '=', '{', '}']):
                valido = False
                motivo = "Nao parece codigo"
    
    elif tarefa == "texto":
        valido, motivo = validar_contra_kg(resp_ds, kg_path)
    
    if valido:
        return resp_ds, "deepseek-r1:7b", tempo_ds, "validado"
    else:
        print(f"  [Crew] deepseek INVALIDO: {motivo}. Fallback coder:7b...")
        resp_coder, tempo_coder = chamar("qwen2.5-coder:7b", prompt, 0.1, 2048)
        return resp_coder, "qwen2.5-coder:7b (fallback)", tempo_ds + tempo_coder, f"fallback_{motivo[:30]}"


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    print("=== DEEPSEEK CREW VALIDATOR ===\n")
    
    kg_path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
    
    testes = [
        ("Codigo Python", "code", "def soma(a, b): return a + b\n\ndef main():\n    x = soma(5, 3)\n    print(x)"),
        ("Codigo Lua invalido", "code", "function hello() print('oi')"),
        ("Pergunta SHC", "texto", "O que e SHC no projeto MCR?"),
        ("Pergunta inventada", "texto", "Qual o Sistema de Habitação Conjunta no MCR?"),
    ]
    
    for nome, tarefa, prompt in testes:
        print(f"\n{'─'*50}")
        print(f"Teste: {nome}")
        print(f"{'─'*50}")
        
        resp, modelo, tempo, status = crew_deepseek(prompt, tarefa, kg_path)
        print(f"  Modelo: {modelo}")
        print(f"  Tempo: {tempo}s")
        print(f"  Status: {status}")
        print(f"  Resposta: {resp[:200]}")
