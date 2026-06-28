#!/usr/bin/env python3
"""Avaliador Qualitativo Profundo para o MEGA TESTE CEGO.
Avalia 10 secoes com 6 criterios cada + LLM como juiz imparcial.
"""
import os, json, re, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CLOUD_DIR = os.path.join(BASE, "respostas_cloud")
MCR_DIR = os.path.join(BASE, "respostas_mcr")
OLLAMA_URL = "http://localhost:11434/api/generate"

# 10 secoes esperadas
SECOES = [
    "analise_codigo", "correcao_bugs", "geracao_codigo",
    "arquitetura", "revisao", "criacao",
    "diagnostico", "refatoracao", "planejamento", "sintese"
]

SECOES_PT = [
    "ANÁLISE DE CÓDIGO", "CORREÇÃO DE BUGS", "GERAÇÃO DE CÓDIGO",
    "ARQUITETURA", "REVISÃO DE CÓDIGO", "CRIAÇÃO (HISTÓRIA)",
    "DIAGNÓSTICO", "REFATORAÇÃO", "PLANEJAMENTO", "SÍNTESE"
]

def _llm(prompt, modelo="deepseek-r1:7b", temp=0.1):
    try:
        d = json.dumps({
            "model": modelo, "prompt": prompt, "stream": False,
            "options": {"temperature": temp, "num_ctx": 8192, "num_predict": 1024}
        }).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(r, timeout=60).read())
        return resp.get("response", "")
    except:
        return ""

def _extrair_secoes(texto):
    """Detecta quantas secoes do mega teste estao presentes."""
    encontradas = set()
    texto_upper = texto.upper()
    
    marcadores = {
        "analise_codigo": ["SEÇÃO 1", "ANÁLISE DE CÓDIGO", "ANALISE DE CODIGO", "[ ] ANALISE DE CODIGO"],
        "correcao_bugs": ["SEÇÃO 2", "CORREÇÃO DE BUGS", "CORRECAO DE BUGS", "[ ] CORRECAO DE BUGS"],
        "geracao_codigo": ["SEÇÃO 3", "GERAÇÃO DE CÓDIGO", "GERACAO DE CODIGO", "[ ] GERACAO DE CODIGO", "[ ] GERACÃO DE CODIGO"],
        "arquitetura": ["SEÇÃO 4", "ARQUITETURA", "[ ] ARQUITETURA"],
        "revisao": ["SEÇÃO 5", "REVISÃO DE CÓDIGO", "REVISAO DE CODIGO", "[ ] REVISAO", "[ ] REVISÃO", "[ ] REVISÃO:"],
        "criacao": ["SEÇÃO 6", "CRIAÇÃO", "HISTÓRIA", "HISTORIA", "LENDA", "[ ] CRIACAO"],
        "diagnostico": ["SEÇÃO 7", "DIAGNÓSTICO", "DIAGNOSTICO", "[ ] DIAGNOSTICO"],
        "refatoracao": ["SEÇÃO 8", "REFATORAÇÃO", "REFATORACAO", "[ ] REFATORACAO"],
        "planejamento": ["SEÇÃO 9", "PLANEJAMENTO", "[ ] PLANEJAMENTO"],
        "sintese": ["SEÇÃO 10", "SÍNTESE", "SINTESE", "LIÇÕES", "LICOES", "[ ] SINTESE"],
    }
    
    for secao, markers in marcadores.items():
        for m in markers:
            if m in texto_upper:
                encontradas.add(secao)
                break
    
    return list(encontradas)

def _contar_linhas_codigo(texto):
    """Conta linhas de codigo em ``` blocks."""
    blocos = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    return sum(len(b.split('\n')) for b in blocos)

def _verificar_sintaxe_codigo(texto):
    """Tenta compilar codigo Python extraido."""
    blocos = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    erros = 0
    for b in blocos:
        try:
            compile(b.strip(), '<teste>', 'exec')
        except SyntaxError as e:
            erros += 1
    return erros

def _verificar_bugs_mencionados(texto):
    """Conta quantos bugs foram identificados."""
    bugs = re.findall(r'(?:BUG|LINHA\s+\d+|ERRO|PROBLEMA)\s*:?\s*\d*', texto.upper())
    return len(set(bugs))

def _avaliar_com_llm(texto_mcr, texto_cloud):
    """Usa LLM para avaliar qual resposta e melhor."""
    prompt = f"""Compare duas respostas para um MEGA TESTE que exige 10 habilidades em programação.

Avalie APENAS: qual resposta é mais COMPLETA, TECNICAMENTE CORRETA e BEM ESTRUTURADA?

Responda com JSON:
{{"vencedor": "MCR or CLOUD or EMPATE",
  "mcr_acertos": N, "cloud_acertos": N,
  "mcr_erros": N, "cloud_erros": N,
  "mcr_secoes": N, "cloud_secoes": N,
  "justificativa": "curta"}}

--- RESPOSTA A (MCR) ---
{texto_mcr[:4000]}

--- RESPOSTA B (CLOUD) ---
{texto_cloud[:4000]}"""

    resp = _llm(prompt, "deepseek-r1:7b", 0.1)
    try:
        import json as _json
        m = re.search(r'\{.*\}', resp, re.DOTALL)
        if m:
            return _json.loads(m.group(0))
    except:
        pass
    return {"vencedor": "EMPATE", "mcr_acertos": 0, "cloud_acertos": 0,
            "mcr_erros": 0, "cloud_erros": 0, "mcr_secoes": 0, "cloud_secoes": 0}

def avaliar():
    print("=" * 80)
    print("  AVALIADOR QUALITATIVO PROFUNDO — MEGA TESTE CEGO")
    print("=" * 80)
    
    mcr_path = os.path.join(MCR_DIR, "mega_1.txt")
    cloud_path = os.path.join(CLOUD_DIR, "mega_1.txt")
    
    mcr_txt = open(mcr_path, 'r', encoding='utf-8-sig', errors='replace').read() if os.path.exists(mcr_path) else ""
    cloud_txt = open(cloud_path, 'r', encoding='utf-8-sig', errors='replace').read() if os.path.exists(cloud_path) else ""
    
    if not mcr_txt or not cloud_txt:
        print("[ERRO] Respostas nao encontradas. Execute o teste primeiro.")
        return
    
    # Detalhamento das secoes
    mcr_secoes_list = _extrair_secoes(mcr_txt)
    cloud_secoes_list = _extrair_secoes(cloud_txt)
    print(f"\n  SECOES MCR: {mcr_secoes_list}")
    print(f"  SECOES CLOUD: {cloud_secoes_list}")
    
    # Metricas MCR
    mcr_secoes = _extrair_secoes(mcr_txt)
    mcr_linhas = _contar_linhas_codigo(mcr_txt)
    mcr_erros = _verificar_sintaxe_codigo(mcr_txt)
    mcr_bugs = _verificar_bugs_mencionados(mcr_txt)
    
    # Metricas Cloud
    cloud_secoes = _extrair_secoes(cloud_txt)
    cloud_linhas = _contar_linhas_codigo(cloud_txt)
    cloud_erros = _verificar_sintaxe_codigo(cloud_txt)
    cloud_bugs = _verificar_bugs_mencionados(cloud_txt)
    
    # Avaliacao LLM
    llm = _avaliar_com_llm(mcr_txt, cloud_txt)
    
    print(f"""
{'='*60}
  RESULTADOS OBJETIVOS
  {'Metrica':<30} {'MCR':<10} {'Cloud':<10}
  {'-'*50}
  {'Seções encontradas':<30} {len(mcr_secoes):<10} {len(cloud_secoes):<10}
  {'Linhas de codigo':<30} {mcr_linhas:<10} {cloud_linhas:<10}
  {'Erros de sintaxe':<30} {mcr_erros:<10} {cloud_erros:<10}
  {'Bugs mencionados':<30} {mcr_bugs:<10} {cloud_bugs:<10}
  {'Total caracteres':<30} {len(mcr_txt):<10} {len(cloud_txt):<10}
{'='*60}""")
    
    # Gargalos
    print(f"\n  GARGALOS IDENTIFICADOS:")
    if len(mcr_secoes) < 10:
        print(f"  FALTA: MCR secoes faltando: {set(SECOES) - set(mcr_secoes)}")
    if len(cloud_secoes) < 10:
        print(f"  FALTA: Cloud secoes faltando: {set(SECOES) - set(cloud_secoes)}")
    if mcr_erros > 0:
        print(f"  ERRO: MCR codigo com erros de sintaxe: {mcr_erros}")
    if cloud_erros > 0:
        print(f"  ERRO: Cloud codigo com erros de sintaxe: {cloud_erros}")
    if mcr_bugs < 5:
        print(f"  ALERTA: MCR poucos bugs identificados: {mcr_bugs} (esperado 5+)")
    if cloud_bugs < 5:
        print(f"  ALERTA: Cloud poucos bugs identificados: {cloud_bugs} (esperado 5+)")
    
    # Vencedor por METRICAS OBJETIVAS
    mcr_score = len(mcr_secoes) * 10 + mcr_linhas - mcr_erros * 5
    cloud_score = len(cloud_secoes) * 10 + cloud_linhas - cloud_erros * 5
    print(f"\n  SCORE OBJETIVO: MCR {mcr_score} vs Cloud {cloud_score}")
    if mcr_score > cloud_score:
        print(f"\n  VENCEDOR POR METRICAS: MCR-DevIA")
    elif cloud_score > mcr_score:
        print(f"\n  VENCEDOR POR METRICAS: Cloud")
    else:
        print(f"\n  EMPATE TECNICO")
    print("=" * 60)
    
    # Salva resultados
    resultado = {
        "mcr": {
            "secoes": mcr_secoes,
            "secoes_count": len(mcr_secoes),
            "linhas_codigo": mcr_linhas,
            "erros_sintaxe": mcr_erros,
            "bugs_identificados": mcr_bugs,
            "chars": len(mcr_txt),
        },
        "cloud": {
            "secoes": cloud_secoes,
            "secoes_count": len(cloud_secoes),
            "linhas_codigo": cloud_linhas,
            "erros_sintaxe": cloud_erros,
            "bugs_identificados": cloud_bugs,
            "chars": len(cloud_txt),
        },
        "llm_veredito": llm,
        "gargalos_mcr": {
            "faltam_secoes": list(set(SECOES) - set(mcr_secoes)),
            "erros_sintaxe": mcr_erros,
            "poucos_bugs": mcr_bugs < 5,
        }
    }
    
    out_path = os.path.join(BASE, "resultado_mega.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultados salvos em: {out_path}")
    
    return resultado

if __name__ == "__main__":
    avaliar()
