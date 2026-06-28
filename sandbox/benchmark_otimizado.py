"""benchmark_otimizado.py - Com fragmentacao forçada para caber na VRAM"""
import urllib.request, json, time, os, sys

OLLAMA_URL = "http://localhost:11434/api/generate"

# Modelos com contexto reduzido via fragmentador (2048 em vez de 4096 para 14b)
MODELOS = [
    ("qwen2.5-coder:1.5b", 2048, "Leve, rapido"),
    ("qwen2.5-coder:7b", 2048, "Codigo principal"),
    ("deepseek-r1:7b", 2048, "Raciocinio (thinking)"),
    ("llama3.1:8b", 2048, "Contexto 131K"),
    ("qwen2.5:14b", 1024, "Pesado, fragmentado"),  # contexto reduzido!
]

# Testes ultra enxutos (prompts < 200 chars para caber em 1024 ctx)
TESTES = [
    # (nome, prompt, temp, palavra_chave, timeout)
    ("classificacao", "Flecha de Fogo article=um. Correto? SIM/NAO:", 0.1, "NAO", 15),
    ("extracao", "Extraia nome: <item name='Power Bolt'/>\nNome:", 0.1, "Power", 15),
    ("codigo", "NPC Lua: npc = NPC(\"Ferreiro\")", 0.3, "NPC", 30),
    ("contexto", "O que e SPA no projeto MCR? Resposta curta:", 0.5, "SPA", 30),
    ("raciocinio", "items[1]={dano=10} items[2]={dano=15} for i=1,3 do print() end\nPor que erro? Curto:", 0.3, "nil", 30),
    ("revisao", "Item: Flecha de Fogo article='um'. Responda SIM ou NAO:", 0.1, "NAO", 15),
]

def chamar(modelo, ctx, prompt, temp, timeout_s):
    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temp, "num_ctx": ctx}
    }).encode()
    try:
        inicio = time.time()
        req = urllib.request.Request(OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=timeout_s).read()
        dados = json.loads(resp)
        return dados.get('response',''), round(time.time() - inicio, 1)
    except Exception as e:
        return f"[{type(e).__name__}]", timeout_s

print("=" * 70)
print("BENCHMARK OTIMIZADO (fragmentador ativo)")
print("=" * 70)
print(f"VRAM: RTX 3080 10GB | Contexto reduzido via fragmentador\n")

tabela = {}

for modelo, ctx, desc in MODELOS:
    print(f"\n  >> {modelo} ({desc}) ctx={ctx}")
    tabela[modelo] = {}
    for nome, prompt, temp, chave, to in TESTES:
        resp, tempo = chamar(modelo, ctx, prompt, temp, to)
        
        if resp.startswith("[Timeout") or resp.startswith("[urllib"):
            status = "TIMEOUT"
            ok = "?"
        else:
            ok = chave.lower() in resp.lower() if chave else None
            status = "OK" if ok else "FALHOU"
        
        preview = resp[:60].replace('\n', ' | ')
        print(f"    {nome:<15} {str(tempo):>6}s [{status}] {preview}")
        tabela[modelo][nome] = {"tempo": tempo, "ok": ok, "status": status}

print("\n\n" + "=" * 70)
print("MATRIZ COMPARATIVA")
print("=" * 70)
print(f"\n{'Modelo':<22} {'Tempo':<8} {'OK':<8} {'Classif':<10} {'Extra':<10} {'Codigo':<10} {'Ctx':<10} {'Rac':<10} {'Rev':<10}")
print("-" * 80)
for modelo, _ in MODELOS:
    m = modelo.split(':')[0]
    # Calcular metricas
    tempos = []
    oks = []
    for t in TESTES:
        n = t[0]
        if n in tabela[modelo]:
            tempos.append(tabela[modelo][n]['tempo'])
            oks.append(tabela[modelo][n]['ok'] if tabela[modelo][n]['ok'] is not None else False)
    
    total_t = sum(tempos)
    total_ok = sum(1 for o in oks if o)
    
    # Resultados por teste
    def _r(n):
        if n in tabela[modelo]:
            d = tabela[modelo][n]
            return f"{'✓' if d['ok'] else '✗'}{d['tempo']:.0f}s"
        return "N/A"
    
    print(f"{modelo:<22} {total_t:<8.0f}s {total_ok}/{len(oks):<5} "
          f"{_r('classificacao'):<10} {_r('extracao'):<10} {_r('codigo'):<10} "
          f"{_r('contexto'):<10} {_r('raciocinio'):<10} {_r('revisao'):<10}")

# Recomendacao final
print("\n\n" + "=" * 70)
print("RECOMENDACAO FINAL")
print("=" * 70)
recs = {
    "fast (classificacao/extracao)": "qwen2.5-coder:1.5b (986MB, ~2s, mais rapido)",
    "code (geracao codigo)": "qwen2.5-coder:7b (4.7GB, melhor para codigo)",
    "contexto (perguntas gerais)": "llama3.1:8b (4.9GB, contexto 131K, tool calls)",
    "raciocinio (debug/planejamento)": "deepseek-r1:7b (4.7GB, pensa antes de responder)",
    "revisor (analise items.xml)": "qwen2.5:14b (9GB ctx=1024, maior precisao disponivel)",
    "leve (fallback rapido)": "qwen2.5-coder:1.5b (mesmo do fast)",
}
for cargo, modelo in recs.items():
    print(f"  {cargo:<40} => {modelo}")

# Salvar
with open("E:\\Modelos IA\\benchmark_final.json", "w", encoding="utf-8") as f:
    json.dump({"resultados": tabela, "recomendacoes": recs,
               "timestamp": time.strftime("%Y-%m-%d %H:%M")},
              f, indent=2, ensure_ascii=False)
print(f"\nSalvo em E:\\Modelos IA\\benchmark_final.json")
