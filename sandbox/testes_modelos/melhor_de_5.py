"""
MELHOR DE 5 - Mistral vs Qwen (Equilibrio + Raciocinio)
Data: 27/06/2026

5 testes comparativos entre mistral:7b e qwen2.5-coder:7b
Cada teste mede: completude, clareza, profundidade, relevancia, estrutura
"""

import json, time, os, urllib.request, urllib.error, re

OLLAMA_URL = "http://localhost:11434/api/generate"
PASTA = os.path.dirname(os.path.abspath(__file__))

MODELOS = [
    {"nome": "qwen2.5-coder:7b", "label": "Qwen 2.5 Coder (7B)"},
    {"nome": "mistral:7b",        "label": "Mistral (7B)"},
]

TESTES = [
    {
        "id": "logica_matematica",
        "titulo": "LOGICA MATEMATICA - Calculo de drop rate em MMORPG",
        "peso": 1.0,
        "prompt": """Em um servidor de Tibia, o monstro "Dragon Lord" tem:
- 35% de chance de drop de "Dragon Ham"
- 15% de chance de drop de "Dragon Scale Mail"
- 5% de chance de drop de "Dragon Lord Trophy"
- 45% de chance de drop de "Gold Coins" (quantidade: 100-500)

Um jogador mata 20 Dragon Lords. Calcule:
1. A probabilidade de obter pelo menos 1 Dragon Scale Mail
2. O valor esperado (expected value) de Gold Coins obtidas
3. A probabilidade de obter exatamente 2 Dragon Hams

Mostre os cálculos passo a passo e explique a lógica. Use Python se necessário para demonstrar."""
    },
    {
        "id": "tradeoff_tecnico",
        "titulo": "TRADE-OFF - SQLite vs MySQL para servidor de jogo",
        "peso": 1.2,
        "prompt": """Analise em profundidade: SQLite vs MySQL como banco de dados para um servidor OTServ (Tibia) com 200 jogadores simultaneos.

Para cada um, considere:
- Performance em leitura/escrita
- Concorrencia e locking
- Facilidade de setup e manutencao
- Backup e recovery
- Consumo de RAM/CPU
- Casos de uso ideais dentro do jogo (ex: guild storage vs world data)

Estrutura sua resposta em: (1) analise individual de cada um, (2) comparacao direta, (3) recomendacao final com justificativa."""
    },
    {
        "id": "diagnostico_problema",
        "titulo": "DIAGNOSTICO - Lag com 50+ jogadores na mesma area",
        "peso": 1.3,
        "prompt": """Diagnostico tecnico: O servidor OTServ comeca a apresentar lag (delay de 2-5 segundos) quando 50 ou mais jogadores estao na mesma area (ex: war ou boss fight).

Possivel hardware: CPU 8 cores, 32GB RAM, SSD NVMe. Conexao 1Gbps.

Analise:
1. Quais as 5 causas MAIS PROVAVEIS para este problema?
2. Para cada causa, proponha uma solucao pratica
3. Como diagnosticar qual causa especifica esta ocorrendo? (ferramentas, metricas, logs)
4. Qual a causa MAIS provavel e por que?
5. Sugira uma abordagem de mitigacao imediata vs solucao permanente

Seja tecnico e especifico. Nao de respostas genericas."""
    },
    {
        "id": "design_estrutura",
        "titulo": "DESIGN - Sistema de quests para MMORPG",
        "peso": 1.1,
        "prompt": """Projete a estrutura de dados para um sistema de quests em um MMORPG (Tibia/OTServ).

Requisitos:
- Quests podem ter prerequisitos (level, quests anteriores, itens)
- Quests tem multiplos objetivos (matar X monstros, coletar Y itens, falar com Z NPCs)
- Quests tem recompensas (experiencia, itens, acesso a novas areas)
- Jogador pode ter ate 25 quests ativas simultaneamente
- Historico de quests completadas precisa ser persistente

Sua resposta deve incluir:
1. Estrutura de dados (tabelas/classes/JSON schema)
2. Fluxo de progressao (como o jogador avanca na quest)
3. Como validar requisitos de forma eficiente
4. Exemplo concreto de uma quest implementada com sua estrutura

Use pseudo-codigo ou Python para exemplificar."""
    },
    {
        "id": "comparacao_arquitetura",
        "titulo": "COMPARACAO - NoSQL vs SQL para inventario de jogadores",
        "peso": 1.2,
        "prompt": """Compare NoSQL (Redis/MongoDB) vs SQL (MySQL/PostgreSQL) para armazenar inventario de jogadores em um MMORPG.

Contexto: 
- 1000 jogadores simultaneos
- Cada jogador tem 50-200 slots de inventario
- Itens tem atributos variaveis (encantamento, durabilidade, encaixes)
- Operacoes: mover item, usar item, trade entre jogadores, depositar/retirar de guild storage
- Latencia maxima aceitavel: 100ms para operacoes de inventario

Analise:
1. Modelagem de dados em cada abordagem
2. Performance em operacoes comuns (CRUD)
3. Consistencia vs disponibilidade (CAP theorem)
4. Facilidade de implementar trades (transacoes atomicas)
5. Recomendacao final com justificativa QUANTITATIVA

Estruture em topicos com PROS/CONTRA para cada abordagem."""
    }
]

CRITERIOS = {
    "completude": "Respondeu todos os pontos solicitados? (0-10)",
    "clareza": "A resposta e clara, bem estruturada e facil de entender? (0-10)",
    "profundidade": "A analise e superficial ou vai alem do basico? (0-10)",
    "relevancia": "Responde especificamente ao contexto do MCR/Tibia? (0-10)",
    "precisao_tecnica": "O conteudo tecnico esta correto e preciso? (0-10)"
}

def consultar(modelo, prompt, timeout=180):
    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 4096
        }
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - inicio
        resposta = dados.get("response", "")
        tokens = dados.get("eval_count", 0)
        eval_dur = dados.get("eval_duration", 0) / 1e9
        tok_s = round(tokens / eval_dur, 1) if eval_dur > 0 else 0
        return {
            "resposta": resposta,
            "tempo": round(elapsed, 1),
            "tokens": tokens,
            "tok_s": tok_s,
            "caracteres": len(resposta),
            "erro": None
        }
    except Exception as e:
        return {"resposta": "", "tempo": round(time.time()-inicio, 1),
                "tokens": 0, "tok_s": 0, "caracteres": 0, "erro": str(e)}

def analisar_qualidade(resposta, teste_id):
    """Analise qualitativa manual (via heurísticas)."""
    r = resposta.lower()
    carac = len(resposta)
    linhas = resposta.count("\n") + 1
    palavras = len(resposta.split())
    
    scores = {}
    
    # Completude: quantos topicos/requisitos foram cobertos
    marcadores = 0
    for mark in ["1.", "2.", "3.", "4.", "5.", "**", "###", "- ", "* "]:
        marcadores += resposta.count(mark)
    scores["completude"] = min(10, max(2, marcadores // 2))
    
    # Clareza: estrutura, paragrafos, lista
    if linhas > 15 and palavras > 200:
        scores["clareza"] = 8
    elif linhas > 10:
        scores["clareza"] = 6
    else:
        scores["clareza"] = 4
    if "**" in resposta and ("1." in resposta or "-" in resposta):
        scores["clareza"] = min(10, scores["clareza"] + 2)
    
    # Profundidade: palavras-chave tecnicas
    termos_tecnicos = ["porque", "portanto", "conclusao", "entretanto", "entanto",
                       "especifico", "exemplo", "implementacao", "arquitetura",
                       "performance", "latencia", "concorrencia", "cache",
                       "sharding", "replicacao", "indice", "query", "transacao",
                       "atomico", "consistencia", "disponibilidade"]
    encontrados = sum(1 for t in termos_tecnicos if t in r)
    scores["profundidade"] = min(10, max(2, encontrados))
    
    # Relevancia: menciona contexto Tibia/OTServ
    termos_contexto = ["tibia", "otserv", "servidor", "jogador", "jogo",
                       "mmorpg", "monstro", "drop", "inventario", "quest",
                       "npc", "guild", "server", "player", "game"]
    encontrados_ctx = sum(1 for t in termos_contexto if t in r)
    scores["relevancia"] = min(10, max(1, encontrados_ctx))
    
    # Precisao tecnica: codigo, exemplos, numeros
    if "```" in resposta:
        scores["precisao_tecnica"] = 8
    elif any(c.isdigit() for c in resposta[:100]):
        scores["precisao_tecnica"] = 6
    else:
        scores["precisao_tecnica"] = 4
    # Bonus para codigo com funcao
    if "def " in resposta or "function " in resposta:
        scores["precisao_tecnica"] = min(10, scores["precisao_tecnica"] + 2)
    
    return scores

def salvar_teste(modelo_info, teste_info, resultado, scores):
    nome = f"m5_{modelo_info['nome'].split(':')[0]}_{teste_info['id']}.txt"
    caminho = os.path.join(PASTA, nome)
    media = round(sum(scores.values()) / len(scores), 1)
    
    conteudo = f"""========================================
MELHOR DE 5 - {teste_info['titulo']}
MODELO: {modelo_info['label']}
DATA: 27/06/2026
========================================

PROMPT:
{teste_info['prompt']}

----------------------------------------
RESPOSTA ({resultado['caracteres']}c, {resultado['tempo']}s, {resultado['tok_s']} tok/s):
----------------------------------------
{resultado['resposta']}

----------------------------------------
ANALISE QUALITATIVA:
----------------------------------------
"""
    for crit, score in scores.items():
        desc = CRITERIOS[crit]
        barra = "█" * score + "░" * (10 - score)
        conteudo += f"{crit.upper()}: {barra} {score}/10  ({desc})\n"
    
    conteudo += f"\nMEDIA GERAL: {media}/10\n"
    conteudo += f"CARACTERES: {resultado['caracteres']}\n"
    conteudo += f"TEMPO: {resultado['tempo']}s\n"
    conteudo += f"TOKENS: {resultado['tokens']}\n"
    conteudo += f"TOKENS/S: {resultado['tok_s']}\n"
    if resultado['erro']:
        conteudo += f"ERRO: {resultado['erro']}\n"
    
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho

def main():
    print("=" * 70)
    print(" MELHOR DE 5: Mistral vs Qwen")
    print(" Equilibrio + Raciocinio")
    print("=" * 70)
    print(f"\nModelos: {len(MODELOS)}")
    print(f"Testes: {len(TESTES)}")
    print(f"Total chamadas: {len(MODELOS) * len(TESTES)}")
    
    todos = {}
    
    for mod in MODELOS:
        print(f"\n{'='*70}")
        print(f" MODELO: {mod['label']}")
        print(f"{'='*70}")
        todos[mod['nome']] = {"testes": {}, "somas": {}, "total_peso": 0}
        
        for test in TESTES:
            print(f"\n  --- {test['titulo']} ---")
            print(f"  Consultando...")
            
            resultado = consultar(mod["nome"], test["prompt"])
            
            if resultado["erro"]:
                print(f"  [ERRO] {resultado['erro']}")
                scores = {c: 0 for c in CRITERIOS}
            else:
                print(f"  [OK] {resultado['caracteres']}c em {resultado['tempo']}s ({resultado['tok_s']} tok/s)")
                scores = analisar_qualidade(resultado["resposta"], test["id"])
            
            salvar_teste(mod, test, resultado, scores)
            
            # Acumula para media ponderada
            peso = test["peso"]
            for crit, score in scores.items():
                todos[mod['nome']]["somas"][crit] = todos[mod['nome']]["somas"].get(crit, 0) + score * peso
            todos[mod['nome']]["total_peso"] += peso
            todos[mod['nome']]["testes"][test['id']] = {
                "resultado": resultado,
                "scores": scores,
                "peso": peso
            }
            
            # Preview
            preview = resultado["resposta"][:150].replace("\n", " ")
            try:
                print(f"  Preview: {preview}...")
            except:
                print(f"  Preview: [unicode]...")
    
    # ===== RELATORIO FINAL =====
    print(f"\n\n{'='*70}")
    print(" RELATORIO FINAL - MELHOR DE 5")
    print(f"{'='*70}")
    
    for mod in MODELOS:
        nome = mod['nome']
        data = todos[nome]
        print(f"\n--- {mod['label']} ---")
        media_geral = 0
        for crit in CRITERIOS:
            media = round(data["somas"].get(crit, 0) / data["total_peso"], 1)
            print(f"  {crit}: {media}/10")
            media_geral += media
        media_final = round(media_geral / len(CRITERIOS), 1)
        print(f"  >>> MEDIA FINAL: {media_final}/10")
        
        # Tempo e caracteres totais
        total_c = sum(t["resultado"]["caracteres"] for t in data["testes"].values())
        total_t = sum(t["resultado"]["tempo"] for t in data["testes"].values())
        print(f"  Total caracteres: {total_c}")
        print(f"  Total tempo: {total_t}s")
    
    # Comparacao direta
    print(f"\n{'='*70}")
    print(" COMPARACAO DIRETA (ponderada por peso dos testes)")
    print(f"{'='*70}")
    
    print(f"\n{'Critério':<20} {'Qwen':>10} {'Mistral':>10} {'Vencedor':>12}")
    print(f"{'-'*20} {'-'*10} {'-'*10} {'-'*12}")
    
    qwen_data = todos[MODELOS[0]['nome']]
    mistral_data = todos[MODELOS[1]['nome']]
    
    qwen_media_final = 0
    mistral_media_final = 0
    
    for crit in CRITERIOS:
        q = round(qwen_data["somas"].get(crit, 0) / qwen_data["total_peso"], 1)
        m = round(mistral_data["somas"].get(crit, 0) / mistral_data["total_peso"], 1)
        v = "Qwen" if q > m else ("Mistral" if m > q else "Empate")
        try:
            print(f"{crit:<20} {q:>10} {m:>10} {v:>12}")
        except UnicodeEncodeError:
            print(f"{crit:<20} {q:>10} {m:>10} {v:>12}".encode('ascii', 'replace').decode())
        qwen_media_final += q
        mistral_media_final += m
    
    qm = round(qwen_media_final / len(CRITERIOS), 1)
    mm = round(mistral_media_final / len(CRITERIOS), 1)
    vencedor = "QWEN 2.5 CODER" if qm > mm else "MISTRAL"
    
    try:
        print(f"{'MEDIA FINAL':<20} {qm:>10} {mm:>10} {vencedor:>12}")
    except UnicodeEncodeError:
        print(f"{'MEDIA FINAL':<20} {qm:>10} {mm:>10} {vencedor:>12}")
    
    # Por teste
    print(f"\n{'='*70}")
    print(" RESULTADO POR TESTE")
    print(f"{'='*70}")
    
    for test in TESTES:
        q = qwen_data["testes"][test['id']]
        m = mistral_data["testes"][test['id']]
        
        q_media = round(sum(q["scores"].values()) / len(q["scores"]), 1)
        m_media = round(sum(m["scores"].values()) / len(m["scores"]), 1)
        v = "Qwen" if q_media > m_media else ("Mistral" if m_media > q_media else "Empate")
        
        print(f"\n  {test['titulo']}")
        print(f"    Qwen:    {q_media}/10 ({q['resultado']['caracteres']}c, {q['resultado']['tempo']}s)")
        print(f"    Mistral: {m_media}/10 ({m['resultado']['caracteres']}c, {m['resultado']['tempo']}s)")
        print(f"    Vencedor: {v}")
    
    # Salva relatorio
    relatorio = f"""# MELHOR DE 5 - Mistral vs Qwen

> Data: 27/06/2026
> 5 testes de Equilibrio + Raciocinio
> Temperatura: 0.2 | Max tokens: 4096

## Resultado Final

| Modelo | Media Final | Total chars | Total tempo |
|--------|-------------|-------------|-------------|
| Qwen 2.5 Coder (7B) | {qm}/10 | {sum(t['resultado']['caracteres'] for t in qwen_data['testes'].values())} | {sum(t['resultado']['tempo'] for t in qwen_data['testes'].values())}s |
| Mistral (7B) | {mm}/10 | {sum(t['resultado']['caracteres'] for t in mistral_data['testes'].values())} | {sum(t['resultado']['tempo'] for t in mistral_data['testes'].values())}s |

**VENCEDOR: {vencedor}**

## Detalhamento por Criterio

| Criterio | Qwen | Mistral | Vencedor |
|----------|------|---------|----------|"""
    for crit in CRITERIOS:
        q = round(qwen_data["somas"].get(crit, 0) / qwen_data["total_peso"], 1)
        m = round(mistral_data["somas"].get(crit, 0) / mistral_data["total_peso"], 1)
        v = "Qwen" if q > m else ("Mistral" if m > q else "Empate")
        relatorio += f"\n| {crit} | {q}/10 | {m}/10 | {v} |"
    
    relatorio += f"\n\n## Resultado por Teste\n"
    for test in TESTES:
        q = qwen_data["testes"][test['id']]
        m = mistral_data["testes"][test['id']]
        q_media = round(sum(q["scores"].values()) / len(q["scores"]), 1)
        m_media = round(sum(m["scores"].values()) / len(m["scores"]), 1)
        v = "Qwen" if q_media > m_media else ("Mistral" if m_media > q_media else "Empate")
        relatorio += f"\n### {test['titulo']}\n"
        relatorio += f"- Qwen: {q_media}/10 ({q['resultado']['caracteres']}c, {q['resultado']['tempo']}s)\n"
        relatorio += f"- Mistral: {m_media}/10 ({m['resultado']['caracteres']}c, {m['resultado']['tempo']}s)\n"
        relatorio += f"- Vencedor: **{v}**\n"
    
    relatorio += f"\n\n---\n_Gerado em 27/06/2026_"
    
    relatorio_path = os.path.join(PASTA, "MELHOR_DE_5_RESULTADO.md")
    with open(relatorio_path, "w", encoding="utf-8") as f:
        f.write(relatorio)
    print(f"\n[+] Relatorio salvo: {relatorio_path}")
    
    # JSON completo
    json_path = os.path.join(PASTA, "melhor_de_5_completo.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"[+] JSON salvo: {json_path}")
    
    print(f"\n{'='*70}")
    print(f" VENCEDOR: {vencedor}")
    print(f" Qwen: {qm}/10 vs Mistral: {mm}/10")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
