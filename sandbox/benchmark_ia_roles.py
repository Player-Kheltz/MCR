"""benchmark_ia_roles.py - Testa cada modelo em cada cargo do MCR-DevIA"""
import subprocess, json, time, os, sys, re

# ============================================================
# 1. MODELOS DISPONIVEIS (6 modelos de geracao)
# ============================================================
MODELOS = [
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:7b",
    "deepseek-r1:7b",
    "llama3.1:8b",
    "qwen2.5:14b",
]

# ============================================================
# 2. CARGOS/FUNCOES DE IA NO MCR-DevIA
# ============================================================
CARGOS = [
    {
        "nome": "fast (classificacao SIM/NAO)",
        "tarefa": "classificacao",
        "prompt": "Responda apenas SIM ou NAO.\nPergunta: O item 'Flecha de Fogo' com article='um' e tipo='ammunition' esta com artigo correto?\nResposta:",
        "temp": 0.1,
        "medir": "velocidade",
        "resposta_esperada": "NAO",
        "desc": "Decisoes binarias rapidas"
    },
    {
        "nome": "fast (extracao de dados)",
        "tarefa": "extracao",
        "prompt": "Extraia apenas o nome do item abaixo.\nItem: <item id='500' name='Power Bolt' article='um' plural='Parafusos Poderosos'/>\nNome do item:",
        "temp": 0.1,
        "medir": "velocidade",
        "resposta_esperada": "Power Bolt",
        "desc": "Extracao simples de dados estruturados"
    },
    {
        "nome": "code (gerar Lua NPC)",
        "tarefa": "code",
        "prompt": "Gere um NPC Lua completo para o MCR (servidor Canary/Tibia).\nNome: Ferreiro\nSaudacao: \"Bem-vindo a forja!\"\nItens: 1x Martelada (50 gold)\nGere APENAS o codigo Lua, sem explicacao:\n\n",
        "temp": 0.4,
        "medir": "qualidade",
        "resposta_esperada": "npc = NPC",
        "desc": "Geracao de codigo para Canary"
    },
    {
        "nome": "code (gerar Python)",
        "tarefa": "code",
        "prompt": "Crie uma funcao Python que leia um arquivo JSON e retorne a lista de itens com article='um'.\nGere APENAS o codigo:\n\n",
        "temp": 0.4,
        "medir": "qualidade",
        "resposta_esperada": "def",
        "desc": "Geracao de codigo Python"
    },
    {
        "nome": "contexto (pergunta geral PT-BR)",
        "tarefa": "contexto",
        "prompt": "Pergunta: O que e o Sistema de Progressao do Aventureiro (SPA) no projeto MCR?\n\nResposta curta e objetiva:",
        "temp": 0.7,
        "medir": "qualidade_contexto",
        "resposta_esperada": "SPA",
        "desc": "Respostas contextualizadas sobre o projeto"
    },
    {
        "nome": "contexto (explicacao tecnica)",
        "tarefa": "contexto",
        "prompt": "Explique rapidamente qual a diferenca entre OTServ e um servidor oficial de Tibia:\n\n",
        "temp": 0.7,
        "medir": "qualidade_contexto",
        "resposta_esperada": "OTServ",
        "desc": "Explicacao tecnica curta"
    },
    {
        "nome": "raciocinio (debug logica)",
        "tarefa": "raciocinio",
        "prompt": "Analise o problema: Um script Lua esta dando erro 'attempt to index a nil value' na linha 15.\nO codigo e:\nlocal items = {}\nitems[1] = {nome='Espada', dano=10}\nitems[2] = {nome='Machado', dano=15}\nfor i=1,3 do print(items[i].nome) end\n\nQual e a causa e como corrigir?\n\n",
        "temp": 0.3,
        "medir": "qualidade_raciocinio",
        "resposta_esperada": "items[3]",
        "desc": "Analise de erro com raciocinio multi-etapas"
    },
    {
        "nome": "raciocinio (planejamento)",
        "tarefa": "raciocinio",
        "prompt": "Preciso adicionar um novo tipo de municao (dardo) no items.xml. Quais passos devo seguir?\nListe 3 passos curtos:\n\n",
        "temp": 0.3,
        "medir": "qualidade_raciocinio",
        "resposta_esperada": "passo",
        "desc": "Planejamento simples de tarefa"
    },
    {
        "nome": "revisor (detectar erros PT-BR)",
        "tarefa": "revisao",
        "prompt": "Analise este item do items.xml e responda apenas se esta CORRETO ou com ERRO:\nItem ID=2050: name='Flecha de Fogo', article='um', plural='Flechas de Fogo', type='ammunition'\n\nClassificacao:",
        "temp": 0.1,
        "medir": "precisao_revisao",
        "resposta_esperada": "ERRO",
        "desc": "Revisao de artigos/plurais em PT-BR"
    },
    {
        "nome": "revisor (detectar contexto item)",
        "tarefa": "revisao",
        "prompt": "Analise: Item ID=3000: name='Power Bolt', article='um', plural='Parafusos Poderosos', type='ammunition', weaponType='bolt'\nO nome em PT esta coerente com o tipo 'bolt'?\nResponda SIM ou NAO:\n\n",
        "temp": 0.1,
        "medir": "precisao_revisao",
        "resposta_esperada": "SIM",
        "desc": "Revisao de consistencia nome vs tipo"
    },
]

# ============================================================
# 3. EXECUTAR BENCHMARK
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"

def chamar_ollama(modelo, prompt, temp):
    """Chama o Ollama e mede tempo."""
    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temp, "num_ctx": 2048}
    }).encode()
    inicio = time.time()
    try:
        req = __import__('urllib.request').request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = __import__('urllib.request').request.urlopen(req, timeout=60).read()
        duracao = time.time() - inicio
        dados = json.loads(resp)
        return dados.get('response', ''), duracao
    except Exception as e:
        return f"[ERRO] {e}", time.time() - inicio

resultados = []

print("=" * 80)
print("BENCHMARK DE MODELOS X CARGOS MCR-DevIA")
print("=" * 80)
print(f"\nModelos: {', '.join(MODELOS)}")
print(f"Cargos: {len(CARGOS)} testes\n")

for modelo in MODELOS:
    print(f"\n{'='*60}")
    print(f"  MODELO: {modelo}")
    print(f"{'='*60}")
    
    for cargo in CARGOS:
        print(f"\n  --- {cargo['nome']} ---")
        print(f"  Desc: {cargo['desc']}")
        
        resp, duracao = chamar_ollama(modelo, cargo['prompt'], cargo['temp'])
        
        # Analise basica
        tem_erro = resp.startswith("[ERRO]")
        velocidade = "RAPIDO" if duracao < 5 else ("MEDIO" if duracao < 15 else "LENTO")
        
        # Checagem de resposta esperada
        esperado = cargo.get('resposta_esperada', '')
        acertou_esperado = esperado.lower() in resp.lower() if esperado else None
        
        # Tamanho da resposta
        tam = len(resp)
        tamanho_ok = tam > 20 if cargo['medir'] in ('qualidade', 'qualidade_contexto', 'qualidade_raciocinio') else tam < 50
        
        resp_preview = resp[:120].replace('\n', ' | ')
        
        print(f"  Tempo: {duracao:.1f}s ({velocidade})")
        print(f"  Resp: {resp_preview}...")
        if acertou_esperado is not None:
            print(f"  Palavra-chave '{esperado}': {'ACHOU' if acertou_esperado else 'NAO ACHOU'}")
        
        resultados.append({
            "modelo": modelo,
            "cargo": cargo['nome'],
            "tarefa": cargo['tarefa'],
            "tempo_s": round(duracao, 1),
            "velocidade": velocidade,
            "tamanho_resp": tam,
            "tem_erro": tem_erro,
            "acertou_chave": acertou_esperado,
            "preview": resp[:100]
        })

print("\n\n")
print("=" * 80)
print("RESUMO FINAL")
print("=" * 80)

# Agrupar por modelo
modelos_resumo = {}
for r in resultados:
    m = r['modelo']
    if m not in modelos_resumo:
        modelos_resumo[m] = {'testes': 0, 'erros': 0, 'tempo_total': 0, 'acertos': 0, 'testes_chave': 0}
    modelos_resumo[m]['testes'] += 1
    modelos_resumo[m]['tempo_total'] += r['tempo_s']
    if r['tem_erro']:
        modelos_resumo[m]['erros'] += 1
    if r['acertou_chave'] is not None:
        modelos_resumo[m]['testes_chave'] += 1
        if r['acertou_chave']:
            modelos_resumo[m]['acertos'] += 1

print(f"\n{'Modelo':<25} {'Testes':<8} {'Erros':<8} {'Tempo':<10} {'Medio':<10} {'Acertos':<10} {'Precisao':<10}")
print("-" * 80)
for m, d in sorted(modelos_resumo.items(), key=lambda x: x[1]['tempo_total']):
    precisao = f"{d['acertos']}/{d['testes_chave']}" if d['testes_chave'] else "N/A"
    tempo_medio = d['tempo_total'] / d['testes'] if d['testes'] else 0
    print(f"{m:<25} {d['testes']:<8} {d['erros']:<8} {d['tempo_total']:<10.1f} {tempo_medio:<10.1f}s {precisao:<10}")

# Recomendacao por cargo
print(f"\n\n{'='*80}")
print("RECOMENDACAO POR CARGO")
print("=" * 80)
cargos_agrupados = {}
for r in resultados:
    key = r['tarefa']
    if key not in cargos_agrupados:
        cargos_agrupados[key] = []
    cargos_agrupados[key].append(r)

for tarefa, testes in sorted(cargos_agrupados.items()):
    # Encontrar melhor modelo: sem erro, mais rapido, acertou chave
    validos = [t for t in testes if not t['tem_erro']]
    if not validos:
        continue
    # Ordenar por: acertou chave (desc), tempo (asc)
    validos.sort(key=lambda t: (0 if t['acertou_chave'] else 1, t['tempo_s']))
    melhor = validos[0]
    
    # Segundo melhor
    if len(validos) > 1:
        segundo = validos[1]
    else:
        segundo = None
    
    print(f"\n  Cargo: {testes[0]['cargo']}")
    print(f"    Melhor: {melhor['modelo']} ({melhor['tempo_s']}s, acertou chave: {melhor['acertou_chave']})")
    if segundo:
        print(f"    2o: {segundo['modelo']} ({segundo['tempo_s']}s, acertou chave: {segundo['acertou_chave']})")

# Salvar resultados
output = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M"),
    "modelos": MODELOS,
    "cargos": [c['nome'] for c in CARGOS],
    "resultados": resultados,
    "resumo_modelos": modelos_resumo
}
with open("E:\\Modelos IA\\benchmark_resultados.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\n\nResultados salvos em E:\\Modelos IA\\benchmark_resultados.json")
