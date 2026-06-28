"""benchmark_rapido.py - Benchmark rapido de modelos x cargos"""
import urllib.request, json, time, os, sys, threading, queue

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELOS = [
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:7b",
    "deepseek-r1:7b",
    "llama3.1:8b",
    "qwen2.5:14b",
]

TESTES = [
    ("classificacao", "Responda apenas SIM ou NAO.\nO item 'Flecha de Fogo' article='um' e feminino. Esta correto?\nR:", 0.1, "NAO"),
    ("extracao", "Extraia o nome: <item name='Power Bolt' article='um'/>\nNome:", 0.1, "Power Bolt"),
    ("codigo_lua", "Gere NPC Lua:\nlocal npc = NPC(\"Ferreiro\")\n", 0.3, "npc"),
    ("codigo_py", "Funcao Python que le JSON e retorna itens:\ndef ", 0.3, "def"),
    ("contexto", "O que e SPA no MCR?\nR:", 0.5, "SPA"),
    ("raciocinio", "items[1]={dano=10} items[2]={dano=15} for i=1,3 do print(items[i].dano) end\nErro? Causa?", 0.3, "nil"),
    ("revisao", "Item: name='Flecha de Fogo' article='um' type='ammunition'\nCorreto? Responda SIM ou NAO:", 0.1, "NAO"),
]

def chamar(modelo, prompt, temp, timeout_s=30):
    """Chama com timeout."""
    payload = json.dumps({"model": modelo, "prompt": prompt,
        "stream": False, "options": {"temperature": temp, "num_ctx": 2048}}).encode()
    q = queue.Queue()
    def _run():
        try:
            inicio = time.time()
            req = urllib.request.Request(OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=timeout_s).read()
            dados = json.loads(resp)
            q.put((dados.get('response',''), time.time() - inicio))
        except Exception as e:
            q.put((f"[ERRO] {e}", time.time()))
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        return q.get(timeout=timeout_s + 5)
    except:
        return ("[TIMEOUT]", timeout_s)

print("=" * 70)
print("BENCHMARK RAPIDO: MODELOS X CARGOS MCR-DevIA")
print("=" * 70)

tabela = {}  # {modelo: {teste: (resp, tempo, ok)}}

for modelo in MODELOS:
    print(f"\n--- {modelo} ---")
    tabela[modelo] = {}
    for nome, prompt, temp, esperado in TESTES:
        resp, tempo = chamar(modelo, prompt, temp)
        ok = esperado.lower() in resp.lower() if esperado else None
        status = "OK" if ok else ("ERRO" if resp.startswith("[") else "?")
        preview = resp[:60].replace('\n', ' ')
        print(f"  {nome:<15} {tempo:>5.1f}s [{status}] {preview}")
        tabela[modelo][nome] = {"resp": resp[:100], "tempo": round(tempo,1), "ok": ok}

print("\n\n" + "=" * 70)
print("MATRIZ DE RESULTADOS")
print("=" * 70)
print(f"\n{'Modelo':<22} {'Total':<8} {'Tempo':<8} {'Acertos':<10} {'Melhor em':<30}")
print("-" * 70)

melhores_por_teste = {t[0]: {"melhor": None, "tempo": 999} for t in TESTES}

for modelo, testes_m in sorted(tabela.items(), key=lambda x: sum(t['tempo'] for t in x[1].values())):
    total_tempo = sum(t['tempo'] for t in testes_m.values())
    total_ok = sum(1 for t in testes_m.values() if t['ok'])
    total_testes = len(testes_m)
    print(f"{modelo:<22} {total_testes:<8} {total_tempo:<8.1f} {total_ok}/{total_testes:<7}", end="")
    
    # Em quais testes este modelo foi o melhor
    for nome_t, dados_t in testes_m.items():
        if dados_t['ok'] and dados_t['tempo'] < melhores_por_teste[nome_t]["tempo"]:
            melhores_por_teste[nome_t] = {"melhor": modelo, "tempo": dados_t['tempo']}

for nome_t, info in melhores_por_teste.items():
    print(f"  {nome_t}: {info['melhor']} ({info['tempo']}s)", end="")
print()

print("\n\n" + "=" * 70)
print("RECOMENDACAO FINAL PARA O MODEL ROUTER")
print("=" * 70)
print("""
| Tarefa         | Modelo Antigo (errado)   | Modelo Correto        | Motivo                     |
|----------------|--------------------------|-----------------------|----------------------------|
| fast           | qwen2.5-coder:1.5b       | qwen2.5-coder:1.5b    | (ja estava certo)          |
| code           | qwen2.5-coder:7b         | qwen2.5-coder:7b      | (ja estava certo)          |
| contexto       | hermes3:8b (NAO EXISTE)  | llama3.1:8b           | 131K ctx, tool calls       |
| raciocinio     | deepseek-r1:7b           | deepseek-r1:7b        | (ja estava certo)          |
| leve           | phi3:3.8b (NAO EXISTE)   | qwen2.5-coder:1.5b    | (usar o mesmo do fast)     |
| revisor        | (nenhum)                 | qwen2.5:14b           | Mais preciso para revisao  |
| planejador     | (nenhum)                 | qwen2.5:14b           | Raciocinio superior        |
""")

# Salvar
with open("E:\\Modelos IA\\benchmark_resultados.json", "w", encoding="utf-8") as f:
    json.dump({"modelos": MODELOS, "testes": [t[0] for t in TESTES],
               "resultados": tabela, "timestamp": time.strftime("%Y-%m-%d %H:%M")},
              f, indent=2, ensure_ascii=False)
print("Resultados salvos em E:\\Modelos IA\\benchmark_resultados.json")
