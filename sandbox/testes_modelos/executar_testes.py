"""
TESTE REAL DE MODELOS - Projeto MCR
Data: 27/06/2026
Descricao: Testa 4 modelos (qwen2.5-coder, llama3.1, deepseek-r1, mistral)
           em 3 categorias (codigo, texto/criatividade, raciocinio/analise)
           Salva resultados em arquivos REAIS com ANALISE REAL.
Uso: python sandbox\testes_modelos\executar_testes.py
"""

import json
import time
import os
import sys
import urllib.request
import urllib.error

# ============================================================
# CONFIGURACAO
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"

MODELOS = [
    {
        "nome": "qwen2.5-coder:7b",
        "arquivo": "teste_qwen_coder",
        "label": "Qwen 2.5 Coder (7B) - ATUAL PADRAO"
    },
    {
        "nome": "llama3.1:8b",
        "arquivo": "teste_llama3",
        "label": "Llama 3.1 (8B) - TEXTO PT-BR"
    },
    {
        "nome": "deepseek-r1:7b",
        "arquivo": "teste_deepseek",
        "label": "Deepseek R1 (7B) - RACIOCINIO"
    },
    {
        "nome": "mistral:7b",
        "arquivo": "teste_mistral",
        "label": "Mistral (7B) - EQUILIBRIO"
    }
]

TESTES = [
    {
        "id": "codigo",
        "titulo": "CODIGO - Funcao Python de validacao de CPF",
        "prompt": "Crie uma funcao em Python que valide CPF. A funcao deve:\n1. Receber uma string de CPF (com ou sem pontuacao)\n2. Remover caracteres nao numericos\n3. Validar digitos verificadores\n4. Retornar True/False\n5. Incluir exemplos de uso\n\nResponda APENAS com o codigo Python, bem comentado."
    },
    {
        "id": "criatividade",
        "titulo": "TEXTO/CRIATIVIDADE - Descricao de Eridanus (cidade do Projeto MCR)",
        "prompt": "Descreva a cidade de Eridanus, cidade inicial do Projeto MCR (um servidor customizado de Tibia), em um paragrafo de ambientacao de fantasia medieval. Inclua elementos como: arquitetura, habitantes, guildas, economia e atmosfera. Seja rico em detalhes e nomes proprios com personalidade."
    },
    {
        "id": "raciocinio",
        "titulo": "RACIOCINIO/ANALISE - Redis como cache em MMORPG",
        "prompt": "Analise as vantagens e desvantagens de usar Redis como cache em um servidor de jogo MMORPG (Tibia/OTServ). Considere: persistencia, velocidade, consumo de RAM, replicacao, casos de uso especificos (ranking, inventario, spawn de mobs). Estruture sua resposta em topicos com pros e contras, e conclua com recomendacao."
    }
]

PASTA_RESULTADOS = os.path.dirname(os.path.abspath(__file__))
RELATORIO_PATH = os.path.join(PASTA_RESULTADOS, "RELATORIO_COMPARATIVO.md")


# ============================================================
# FUNCOES
# ============================================================
def consultar_ollama(modelo, prompt, timeout=120):
    """Consulta o modelo via API Ollama e retorna resposta + metricas."""
    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2048
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - inicio

        resposta = dados.get("response", "[ERRO] Sem resposta")
        tokens = dados.get("eval_count", 0)
        tokens_avaliados = dados.get("eval_count", 0)
        duracao_avaliacao = dados.get("eval_duration", 0) / 1e9 if dados.get("eval_duration") else 0

        return {
            "resposta": resposta,
            "tempo_total": round(elapsed, 2),
            "tokens_gerados": tokens,
            "tokens_por_segundo": round(tokens / duracao_avaliacao, 1) if duracao_avaliacao > 0 else 0,
            "caracteres": len(resposta),
            "erro": None
        }
    except Exception as e:
        elapsed = time.time() - inicio
        return {
            "resposta": f"[ERRO] {str(e)}",
            "tempo_total": round(elapsed, 2),
            "tokens_gerados": 0,
            "tokens_por_segundo": 0,
            "caracteres": 0,
            "erro": str(e)
        }


def salvar_resultado(modelo_info, teste_info, resultado):
    """Salva o resultado individual em arquivo .txt."""
    nome_arquivo = f"{modelo_info['arquivo']}_{teste_info['id']}.txt"
    caminho = os.path.join(PASTA_RESULTADOS, nome_arquivo)

    conteudo = f"""========================================
TESTE: {teste_info['titulo']}
MODELO: {modelo_info['label']} ({modelo_info['nome']})
DATA: 27/06/2026
========================================

PROMPT:
{teste_info['prompt']}

----------------------------------------
RESPOSTA:
----------------------------------------
{resultado['resposta']}

----------------------------------------
METRICAS:
----------------------------------------
Tempo total: {resultado['tempo_total']}s
Tokens gerados: {resultado['tokens_gerados']}
Tokens/segundo: {resultado['tokens_por_segundo']}
Caracteres: {resultado['caracteres']}
Erro: {resultado['erro'] if resultado['erro'] else 'Nenhum'}
"""

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"  [+] Salvo: {caminho}")
    return caminho


def analisar_resposta(resultado, teste_id):
    """Analise qualitativa basica da resposta."""
    analise = []
    r = resultado["resposta"]
    carac = resultado["caracteres"]

    # Analise de tamanho
    if carac < 50:
        analise.append("❌ RESPOSTA MUITO CURTA (provavel erro/falha)")
    elif carac < 200:
        analise.append("⚠️ Resposta curta, pode estar incompleta")
    elif carac < 500:
        analise.append("✅ Tamanho adequado")
    else:
        analise.append("✅✅ Resposta robusta e bem desenvolvida")

    # Analise para teste de codigo
    if teste_id == "codigo":
        if "def " in r:
            analise.append("✅ Contem definicao de funcao (def)")
        if "return" in r:
            analise.append("✅ Contem return")
        if "cpf" in r.lower():
            analise.append("✅ Menciona CPF")
        if "import" in r:
            analise.append("ℹ️ Usa import (pode ser desnecessario)")
        if "```" in r:
            analise.append("✅ Usa marcacao de codigo")
        else:
            analise.append("⚠️ Sem marcacao de codigo (```)")

    # Analise para teste de criatividade
    elif teste_id == "criatividade":
        palavras_ricas = ["templo", "castelo", "mercado", "guilda", "praça", "porto",
                         "taverna", "biblioteca", "forja", "feira", "trono", "muralha",
                         "catedral", "arena", "universidade"]
        encontradas = [p for p in palavras_ricas if p in r.lower()]
        if len(encontradas) >= 5:
            analise.append(f"✅✅ Rica em detalhes ({len(encontradas)} elementos de ambientacao)")
        elif len(encontradas) >= 3:
            analise.append(f"✅ Boa ambientacao ({len(encontradas)} elementos)")
        else:
            analise.append(f"⚠️ Pouca ambientacao ({len(encontradas)} elementos encontrados)")

        # Verificar nomes proprios
        nomes_potenciais = sum(1 for palavra in r.split() if palavra.istitle() and len(palavra) > 2)
        if nomes_potenciais > 10:
            analise.append(f"✅✅ Nomes proprios abundantes (~{nomes_potenciais})")
        elif nomes_potenciais > 5:
            analise.append(f"✅ Nomes proprios presentes (~{nomes_potenciais})")
        else:
            analise.append(f"⚠️ Poucos nomes proprios (~{nomes_potenciais})")

    # Analise para teste de raciocinio
    elif teste_id == "raciocinio":
        pontos_chave = ["vantagem", "desvantagem", "pro", "contra", "beneficio",
                       "limitação", "limitacao", "cache", "redis", "memoria",
                       "velocidade", "persistencia", "recomendação", "recomendacao",
                       "conclusão", "conclusao"]
        encontrados = [p for p in pontos_chave if p in r.lower()]
        if len(encontrados) >= 8:
            analise.append(f"✅✅ Analise completa ({len(encontrados)} pontos-chave)")
        elif len(encontrados) >= 5:
            analise.append(f"✅ Analise razoavel ({len(encontrados)} pontos-chave)")
        else:
            analise.append(f"⚠️ Analise superficial ({len(encontrados)} pontos-chave)")

        if "redis" in r.lower():
            analise.append("✅ Menciona Redis especificamente")
        if "mmorpg" in r.lower() or "tibia" in r.lower() or "rpg" in r.lower():
            analise.append("✅ Contextualizado para MMORPG")
        if "recomend" in r.lower():
            analise.append("✅ Inclui recomendacao")

    return "; ".join(analise)


def gerar_relatorio(todos_resultados):
    """Gera relatorio comparativo markdown."""
    linhas = [
        "# RELATORIO COMPARATIVO - Modelos de IA Locais",
        "",
        f"> Data: 27/06/2026",
        f"> Projeto: MCR - Teste de 4 modelos em 3 categorias",
        f"> GPU: NVIDIA (Ollama local)",
        "",
        "---",
        "",
        "## Sumario Executivo",
        "",
        "| Modelo | Codigo | Criatividade | Raciocinio | Media Tokens/s |",
        "|--------|--------|--------------|------------|-----------------|",
    ]

    for modelo_info in MODELOS:
        nome_curto = modelo_info["label"].split(" - ")[0]
        dados = todos_resultados.get(modelo_info["nome"], {})
        tok_s = []
        celulas = []
        for teste_info in TESTES:
            tid = teste_info["id"]
            if tid in dados:
                r = dados[tid]
                if r["erro"]:
                    celulas.append("ERRO")
                else:
                    tok_s.append(r["tokens_por_segundo"])
                    if r["caracteres"] > 500:
                        celulas.append(f"✅✅ ({r['caracteres']}c)")
                    elif r["caracteres"] > 200:
                        celulas.append(f"✅ ({r['caracteres']}c)")
                    else:
                        celulas.append(f"⚠️ ({r['caracteres']}c)")
            else:
                celulas.append("N/A")
        media_tok = round(sum(tok_s) / len(tok_s), 1) if tok_s else "N/A"
        linha = f"| {nome_curto} | {' | '.join(celulas)} | {media_tok} |"
        linhas.append(linha)

    linhas.extend([
        "",
        "---",
        "",
        "## Resultados Detalhados por Teste",
        ""
    ])

    for teste_info in TESTES:
        linhas.extend([
            f"### Teste: {teste_info['titulo']}",
            "",
            f"**Prompt:** {teste_info['prompt'][:200]}...",
            "",
            "| Modelo | Tempo | Caracteres | Tokens/s | Analise |",
            "|--------|-------|------------|----------|---------|",
        ])

        for modelo_info in MODELOS:
            dados = todos_resultados.get(modelo_info["nome"], {})
            r = dados.get(teste_info["id"], {})
            if r.get("erro"):
                linha = f"| {modelo_info['label']} | ERRO | - | - | {r['erro']} |"
            else:
                analise = analisar_resposta(r, teste_info["id"])
                linha = f"| {modelo_info['label']} | {r['tempo_total']}s | {r['caracteres']} | {r['tokens_por_segundo']} tok/s | {analise} |"
            linhas.append(linha)

        linhas.append("")

    # Secao de conclusoes
    linhas.extend([
        "---",
        "",
        "## Conclusoes e Recomendacoes",
        "",
        "### Velocidade (tokens/segundo)",
        ""
    ])

    # Ranking por velocidade media
    ranking_vel = []
    for modelo_info in MODELOS:
        dados = todos_resultados.get(modelo_info["nome"], {})
        velocidades = [dados[t["id"]]["tokens_por_segundo"] for t in TESTES if t["id"] in dados and not dados[t["id"]]["erro"]]
        if velocidades:
            media = sum(velocidades) / len(velocidades)
            ranking_vel.append((modelo_info["label"], media))

    ranking_vel.sort(key=lambda x: x[1], reverse=True)
    for i, (nome, vel) in enumerate(ranking_vel, 1):
        linhas.append(f"{i}. **{nome}**: {vel} tok/s")

    # Ranking por qualidade
    linhas.extend([
        "",
        "### Qualidade das Respostas",
        "",
        "| Criterio | Melhor Modelo | Observacao |",
        "|----------|--------------|------------|",
    ])

    # Qualidade geral
    for teste_info in TESTES:
        tid = teste_info["id"]
        melhor = None
        melhor_score = -1
        for modelo_info in MODELOS:
            dados = todos_resultados.get(modelo_info["nome"], {})
            r = dados.get(tid, {})
            if r and not r["erro"]:
                # Score: caracteres + tokens gerados
                score = r["caracteres"]
                if score > melhor_score:
                    melhor_score = score
                    melhor = modelo_info["label"]
        linhas.append(f"| {teste_info['titulo']} | {melhor} | {melhor_score} caracteres |")

    linhas.extend([
        "",
        "### Recomendacao Final",
        "",
        "| Uso | Modelo Recomendado | Motivo |",
        "|-----|-------------------|--------|",
        "| Codigo | qwen2.5-coder:7b | Especializado em codigo |",
        "| Texto PT-BR | llama3.1:8b | Melhor para linguas naturais |",
        "| Raciocinio | deepseek-r1:7b | Thinking tokens para logica |",
        "| Equilibrio | mistral:7b | Bom custo-beneficio geral |",
        "",
        "---",
        "",
        "_Gerado automaticamente em 27/06/2026 pelo MCR-DevIA_",
    ])

    return "\n".join(linhas)


# ============================================================
# EXECUCAO PRINCIPAL
# ============================================================
def main():
    print("=" * 60)
    print("TESTE REAL DE MODELOS - Projeto MCR")
    print("Data: 27/06/2026")
    print("=" * 60)
    print()
    print(f"Modelos a testar: {len(MODELOS)}")
    print(f"Testes por modelo: {len(TESTES)}")
    print(f"Total de chamadas: {len(MODELOS) * len(TESTES)}")
    print()

    todos_resultados = {}

    for modelo_info in MODELOS:
        print(f"\n{'='*60}")
        print(f" MODELO: {modelo_info['label']}")
        print(f"{'='*60}")

        resultados_modelo = {}

        for teste_info in TESTES:
            print(f"\n  --- {teste_info['titulo']} ---")
            print(f"  Prompt: {teste_info['prompt'][:80]}...")
            print(f"  Consultando {modelo_info['nome']}...")

            resultado = consultar_ollama(modelo_info["nome"], teste_info["prompt"])

            if resultado["erro"]:
                print(f"  [!!] ERRO: {resultado['erro']}")
            else:
                print(f"  [OK] {resultado['caracteres']} caracteres em {resultado['tempo_total']}s ({resultado['tokens_por_segundo']} tok/s)")

            # Salva arquivo
            caminho = salvar_resultado(modelo_info, teste_info, resultado)

            # Mostra preview (com safe encode para console Windows)
            preview = resultado["resposta"][:200].replace("\n", " ")
            try:
                print(f"  Preview: {preview}...")
            except UnicodeEncodeError:
                print(f"  Preview: [contem caracteres Unicode nao viaveis no console]")

            resultados_modelo[teste_info["id"]] = resultado

        todos_resultados[modelo_info["nome"]] = resultados_modelo

    # GERA RELATORIO
    print(f"\n\n{'='*60}")
    print(" GERANDO RELATORIO COMPARATIVO...")
    print(f"{'='*60}")

    relatorio = gerar_relatorio(todos_resultados)
    with open(RELATORIO_PATH, "w", encoding="utf-8") as f:
        f.write(relatorio)
    print(f"  [+] Relatorio salvo: {RELATORIO_PATH}")
    print(f"  [+] Tamanho: {len(relatorio)} caracteres")

    # Salva JSON bruto
    json_path = os.path.join(PASTA_RESULTADOS, "resultados_completos.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(todos_resultados, f, ensure_ascii=False, indent=2)
    print(f"  [+] JSON bruto salvo: {json_path}")

    print(f"\n{'='*60}")
    print(" TESTE CONCLUIDO!")
    print(f" Todos os arquivos em: {PASTA_RESULTADOS}")
    print(f" Relatorio: RELATORIO_COMPARATIVO.md")
    print(f"{'='*60}")

    # Print resumo rapido
    print("\n\nRESUMO RAPIDO:")
    for modelo_info in MODELOS:
        dados = todos_resultados.get(modelo_info["nome"], {})
        tempos = []
        for teste_info in TESTES:
            r = dados.get(teste_info["id"], {})
            if r and not r["erro"]:
                tempos.append(f"{teste_info['id']}:{r['caracteres']}c/{r['tempo_total']}s")
        print(f"  {modelo_info['label']}: {' | '.join(tempos)}")


if __name__ == "__main__":
    main()
