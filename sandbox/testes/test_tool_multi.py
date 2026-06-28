#!/usr/bin/env python3
"""Teste de tool calling multi-passo — simula uso real como subagente."""
import json, urllib.request, time, sys
sys.path.insert(0, r"E:\Projeto MCR\scripts")
BASE = r"E:\Projeto MCR"

def chat(messages, model="qwen2.5-coder:7b", max_tokens=1024):
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": 0.0, "max_tokens": max_tokens}}
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        msg = data.get("message", {})
        return {"content": msg.get("content", ""), "tool_calls": msg.get("tool_calls", []), "time": time.time() - t0}
    except Exception as e:
        return {"content": f"[ERRO] {e}", "tool_calls": [], "time": 0}

print("=" * 70)
print("  TESTE: TOOL CALLING MULTI-PASSO (qwen2.5-coder:7b)")
print("=" * 70)

# Prompt de sistema simulando o que um subagente receberia
SYSTEM = """Voce e um assistente de exploracao de codigo.

VOCE TEM AS SEGUINTES FERRAMENTAS DISPONIVEIS:
- read_file(caminho): Le um arquivo
- search_file(padrao, diretorio): Busca um padrao em arquivos
- list_dir(diretorio): Lista arquivos de um diretorio

REGRAS:
1. Use as ferramentas quando precisar de informacao que voce nao tem.
2. Responda SEMPRE no formato JSON: {"tool": "nome", "args": {...}}
3. Se ja tiver a informacao necessaria, responda em texto normal.
4. NUNCA invente informacao que voce nao obteve das ferramentas.
5. Se nao souber que ferramenta usar, diga "nao sei" em texto."""

cenarios = [
    {
        "nome": "C1: Listar diretorio",
        "msg": "Quais arquivos .lua existem em E:\\Projeto MCR\\sandbox?",
        "ferramenta_esperada": "list_dir"
    },
    {
        "nome": "C2: Buscar padrao",
        "msg": "Encontre arquivos que contenham 'HABILIDADES[' no diretorio de habilidades",
        "ferramenta_esperada": "search_file"
    },
    {
        "nome": "C3: Ler arquivo especifico",
        "msg": "Leia o arquivo AGENTS.md e me diga quantas secoes ele tem",
        "ferramenta_esperada": "read_file"
    },
    {
        "nome": "C4: Pergunta que NAO precisa de ferramenta",
        "msg": "O que e 2+2?",
        "ferramenta_esperada": None  # Deve responder em texto
    },
    {
        "nome": "C5: Pergunta vaga (deve recusar)",
        "msg": "Qual o bug no codigo do MCR?",
        "ferramenta_esperada": None  # Deve dizer que nao sabe ou pedir mais info
    },
]

total = 0
acertos = 0
alucinacoes = 0

for c in cenarios:
    total += 1
    r = chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": c["msg"]}
    ])
    
    content = r["content"].strip()
    
    # Tenta parsear como JSON
    try:
        parsed = json.loads(content)
        tool_name = parsed.get("tool", "")
        args = parsed.get("args", {})
        
        if c["ferramenta_esperada"]:
            if tool_name == c["ferramenta_esperada"]:
                print(f"  ✅ {c['nome']}: chamou {tool_name}({json.dumps(args)[:80]}) [{r['time']:.1f}s]")
                acertos += 1
            else:
                print(f"  ❌ {c['nome']}: esperava '{c['ferramenta_esperada']}', chamou '{tool_name}' [{r['time']:.1f}s]")
                print(f"     → {content[:100]}")
        else:
            # Nao deveria chamar ferramenta
            print(f"  ❌ {c['nome']}: chamou ferramenta desnecessariamente ({tool_name}) [{r['time']:.1f}s]")
            alucinacoes += 1
    except json.JSONDecodeError:
        # Resposta em texto
        if c["ferramenta_esperada"] is None:
            if any(p in content.lower() for p in ["nao sei", "nao tenho", "nao posso", "2+2", "4", "quatro"]):
                print(f"  ✅ {c['nome']}: resposta textual correta [{r['time']:.1f}s]")
                acertos += 1
            else:
                print(f"  ⚠️  {c['nome']}: resposta textual, mas inesperada [{r['time']:.1f}s]")
                print(f"     → {content[:100]}")
        else:
            print(f"  ❌ {c['nome']}: esperava JSON tool call, recebeu texto [{r['time']:.1f}s]")
            print(f"     → {content[:100]}")

print(f"\n{'=' * 70}")
print(f"  RESULTADO: {acertos}/{total} acertos, {alucinacoes} alucinacoes")
print(f"  {'✅ APROVADO' if acertos == total else '⚠️  PARCIAL'}")
print(f"{'=' * 70}")
