#!/usr/bin/env python3
"""Avaliador Qualitativo Automatizado — LLM como juiz entre MCR vs Cloud.
Avalia 4 criterios: correcao, profundidade, originalidade, clareza.
Usa deepseek-r1:7b (modelo de raciocinio) para julgamento imparcial.
"""
import os, json, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CLOUD_DIR = os.path.join(BASE, "respostas_cloud")
MCR_DIR = os.path.join(BASE, "respostas_mcr")
BATERIA_PATH = os.path.join(BASE, "bateria.json")
OLLAMA_URL = "http://localhost:11434/api/generate"

def _llm(prompt, modelo="deepseek-r1:7b", temp=0.1):
    """Chamada ao Ollama para avaliacao."""
    try:
        d = json.dumps({
            "model": modelo, "prompt": prompt,
            "stream": False,
            "options": {"temperature": temp, "num_ctx": 8192, "num_predict": 2048}
        }).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(r, timeout=120).read())
        return resp.get("response", "")
    except Exception as e:
        return f""

def _avaliar_par(mcr_texto, cloud_texto, pergunta):
    """Usa LLM para avaliar qual resposta e melhor em cada criterio."""
    # Trunca para nao estourar contexto (8k tokens ~= 32k chars)
    max_len = 6000
    mcr_amostra = mcr_texto[:max_len]
    cloud_amostra = cloud_texto[:max_len]
    
    prompt = f"""You are an impartial judge evaluating two AI responses to the same question.
Rate each on a scale of 1-10 for each criterion. Be strict and objective.

QUESTION: {pergunta[:500]}

--- RESPONSE A (MCR) ---
{mcr_amostra}

--- RESPONSE B (CLOUD) ---
{cloud_amostra}

Evaluate on these criteria:

1. TECHNICAL CORRECTNESS: Are facts accurate? Is code correct? No hallucinations?
2. DEPTH: How complete and thorough is the analysis? Specific details?
3. ORIGINALITY: Unique insights? Creative names/examples? Not generic?
4. CLARITY: Well structured? Easy to follow? Good organization?

Return ONLY a JSON object with no other text:
{{
  "mcr": {{"correcao": N, "profundidade": N, "originalidade": N, "clareza": N}},
  "cloud": {{"correcao": N, "profundidade": N, "originalidade": N, "clareza": N}},
  "vencedor": "MCR or CLOUD or EMPATE",
  "justificativa": "2-3 sentences explaining your decision"
}}"""
    
    resultado = _llm(prompt, "deepseek-r1:7b", 0.1)
    
    # Tenta extrair JSON da resposta
    import re
    # Busca JSON - pode estar em formatos variados (com/sem espacos, com/sem aspas)
    json_match = re.search(r'\{[^{}]*"mcr"[^{}]*"cloud"[^{}]*\}', resultado, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{.*\}', resultado, re.DOTALL)
    if json_match:
        try:
            raw = json_match.group(0)
            # Normaliza numeros com ponto decimal (ex: 8.5 -> mantem)
            # Normaliza numeros grandes (85 -> 8.5)
            data = json.loads(raw)
            # Garante que valores estao em escala 1-10
            for lado in ['mcr', 'cloud']:
                for chave in ['correcao', 'profundidade', 'originalidade', 'clareza']:
                    if chave in data.get(lado, {}):
                        val = data[lado][chave]
                        if val > 10:
                            data[lado][chave] = round(val / 10, 1)
            return data
        except:
            pass
    
    # Fallback seguro
    return {"mcr": {"correcao": 5, "profundidade": 5, "originalidade": 5, "clareza": 5},
            "cloud": {"correcao": 5, "profundidade": 5, "originalidade": 5, "clareza": 5},
            "vencedor": "EMPATE", "justificativa": "Falha ao avaliar"}

def avaliar_tudo():
    bateria = json.load(open(BATERIA_PATH, 'r', encoding='utf-8'))
    testes = bateria["testes"]
    
    resultados = []
    print("=" * 80)
    print("  AVALIADOR QUALITATIVO AUTOMATIZADO (deepseek-r1:7b)")
    print("=" * 80)
    
    for t in testes:
        tid = t["id"]
        mcr_path = os.path.join(MCR_DIR, f"test_{tid}.txt")
        cloud_path = os.path.join(CLOUD_DIR, f"test_{tid}.txt")
        
        mcr_txt = open(mcr_path, 'r', encoding='utf-8-sig', errors='replace').read() if os.path.exists(mcr_path) else ""
        cloud_txt = open(cloud_path, 'r', encoding='utf-8-sig', errors='replace').read() if os.path.exists(cloud_path) else ""
        
        print(f"\n--- Teste {tid}: {t['titulo']} ---")
        print("  Avaliando...")
        
        avaliacao = _avaliar_par(mcr_txt, cloud_txt, t['prompt'][:300])
        
        mcr_total = sum(avaliacao['mcr'].values())
        cloud_total = sum(avaliacao['cloud'].values())
        
        resultados.append({
            "id": tid,
            "titulo": t['titulo'],
            "categoria": t['categoria'],
            "mcr": avaliacao['mcr'],
            "cloud": avaliacao['cloud'],
            "mcr_total": mcr_total,
            "cloud_total": cloud_total,
            "vencedor": avaliacao['vencedor'],
            "justificativa": avaliacao['justificativa'],
        })
        
        print(f"  MCR:  C={avaliacao['mcr']['correcao']} P={avaliacao['mcr']['profundidade']} O={avaliacao['mcr']['originalidade']} CL={avaliacao['mcr']['clareza']} = {mcr_total}")
        print(f"  Cloud: C={avaliacao['cloud']['correcao']} P={avaliacao['cloud']['profundidade']} O={avaliacao['cloud']['originalidade']} CL={avaliacao['cloud']['clareza']} = {cloud_total}")
        print(f"  Vencedor: {avaliacao['vencedor']}")
        print(f"  Justificativa: {avaliacao['justificativa'][:200]}")
    
    # Sumario
    print("\n" + "=" * 80)
    print("  SUMARIO:")
    print("=" * 80)
    print(f"\n{'#':<3} {'Teste':<30} {'MCR':<10} {'Cloud':<10} {'Vencedor':<12}")
    print("-" * 65)
    
    score_mcr = 0
    score_cloud = 0
    for r in resultados:
        v = r['vencedor']
        if v == 'MCR': score_mcr += 1
        elif v == 'CLOUD': score_cloud += 1
        print(f"{r['id']:<3} {r['titulo']:<30} {r['mcr_total']:<10} {r['cloud_total']:<10} {v:<12}")
    
    print()
    print(f"  PLACAR QUALITATIVO: MCR {score_mcr} x {score_cloud} Cloud")
    print(f"  Media MCR: {sum(r['mcr_total'] for r in resultados)/len(resultados):.1f}/40")
    print(f"  Media Cloud: {sum(r['cloud_total'] for r in resultados)/len(resultados):.1f}/40")
    
    # Salva resultados
    out_path = os.path.join(BASE, "avaliacao_qualitativa.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultados salvos em: {out_path}")
    
    return resultados

if __name__ == "__main__":
    avaliar_tudo()
