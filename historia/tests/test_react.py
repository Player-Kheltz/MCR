#!/usr/bin/env python3
"""TESTE REACT — LLM usa ferramentas proativamente via [FER: ...].

Fluxo:
  1. LLM recebe prompt com [FERRAMENTAS DISPONIVEIS]
  2. LLM gera resposta + [FER: ...] quando precisa de dados
  3. Script intercepta [FER:, executa ferramenta, injeta resultado
  4. LLM continua até resposta sem [FER:]
  5. Avalia se usou codigo REAL do projeto

Uso:
    python tests/test_react.py
"""
import sys, os, re, json, time as _time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

_MAX_CICLOS = 5
_TIMEOUT_POR_CICLO = 60

PROMPT_SISTEMA = """[SISTEMA]
Voce e um assistente do Projeto MCR (servidor customizado de Tibia baseado em Canary OTServ).

[FERRAMENTAS DISPONIVEIS]
Use [FER: ...] quando precisar de dados que voce nao tem.

- buscar_estrategico(termo): busca ESTRATEGICA no codigo do projeto.
  1. DESCOBRE diretorios relevantes pelo nome
  2. EXPLORA arquivos .lua dentro deles
  3. ENCONTRA funcoes reais dentro dos arquivos
  Ex: [FER: buscar_estrategico("SPA")]
  Retorna: estrutura com diretorios, arquivos e funcoes do projeto

- ler_arquivo(caminho): le conteudo de arquivo
  Ex: [FER: ler_arquivo("data-canary/scripts/MCR/SPA/core/postura.lua")]
  Retorna: conteudo completo do arquivo

[REGRAS]
1. Use [FER: buscar_estrategico("TERMO")] para DESCOBRIR codigo real
2. Se encontrar diretorios, explore arquivos especificos com ler_arquivo
3. AGUARDE o retorno antes de continuar
4. NUNCA invente codigo — use SOMENTE o que as ferramentas retornarem
5. Se nao encontrar nada, tente outros termos relacionados
6. Quando tiver informacao suficiente, finalize sem [FER:]

[PERGUNTA]
Explique o sistema SPA do MCR: quais sao seus dominios, e de exemplos de funcoes Lua REAIS
do projeto (nao invente — use as ferramentas para buscar exemplos concretos no codigo).

[RESPOSTA]:"""

PERGUNTA_SIMPLES = (
    "Explique o sistema SPA do MCR, seus dominios "
    "e de exemplos de funcoes Lua reais do projeto."
)


def executar_teste():
    print("=" * 70)
    print("  TESTE REACT — LLM usa ferramentas proativamente")
    print("=" * 70)
    print()
    
    # Inicializa componentes
    from modulos.ia import IA
    from modulos.tool_orchestrator import ToolOrchestrator
    
    ia = IA()
    tools = ToolOrchestrator()
    
    print(f"[Init] IA + ToolOrchestrator carregados")
    print(f"[Init] Max ciclos: {_MAX_CICLOS}, Timeout: {_TIMEOUT_POR_CICLO}s")
    print()
    
    # Loop ReAct
    historico = []
    resposta_final = ""
    ciclo = 0
    usou_ferramenta = False
    ferramentas_usadas = []
    t0 = _time.time()
    
    prompt_atual = PROMPT_SISTEMA
    
    while ciclo < _MAX_CICLOS:
        ciclo += 1
        t_ciclo = _time.time()
        print(f"[Ciclo {ciclo}] Gerando resposta...")
        
        try:
            texto_gerado = ia.gerar(prompt_atual, 0.3, 'pesado') or ""
        except Exception as e:
            print(f"[Ciclo {ciclo}] ERRO: {e}")
            break
        
        if not texto_gerado or len(texto_gerado) < 5:
            print(f"[Ciclo {ciclo}] Resposta vazia")
            break
        
        tempo_ciclo = round(_time.time() - t_ciclo, 1)
        
        # Extrai blocos de codigo (```) antes de verificar [FER:]
        texto_limpo = re.sub(r'```[\s\S]*?```', '[BLOCO_CODIGO]', texto_gerado)
        
        # Busca [FER: ...] no texto limpo
        fer_calls = re.findall(r'\[FER:\s*(.*?)\]', texto_limpo)
        
        if not fer_calls:
            # Ultimo ciclo - resposta final
            resposta_final = texto_gerado
            print(f"[Ciclo {ciclo}] OK ({tempo_ciclo}s) — resposta final, sem [FER:]")
            break
        
        # Executa ferramentas
        resultados_fer = []
        for fer_str in fer_calls:
            usou_ferramenta = True
            parts = fer_str.strip().split("(", 1)
            nome_fer = parts[0].strip()
            params_raw = parts[1].rstrip(")").strip().strip('"').strip("'") if len(parts) > 1 else ""
            
            print(f"[Ciclo {ciclo}] [FER: {nome_fer}(\"{params_raw}\")]", end="")
            
            if nome_fer == "buscar_codigo":
                r = tools.executar("buscar_codigo", {"padrao": params_raw})
                resultado_txt = ""
                if r.get("sucesso"):
                    txt = str(r.get("resultado", ""))
                    if "Nenhum" in txt or len(txt) < 10:
                        txt = "(Nenhum resultado encontrado)"
                    else:
                        linhas = [l for l in txt.split('\n') if l.strip()][:10]
                        txt = '\n'.join(linhas)
                    resultado_txt = txt[:2000]
                else:
                    resultado_txt = "(Erro ao executar)"
                resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n{resultado_txt}")
                ferramentas_usadas.append({"ferramenta": nome_fer, "params": params_raw, "resultado": resultado_txt[:500]})
                print(f" -> {len(resultado_txt.split(chr(10)))} linhas")
            
            elif nome_fer == "buscar_estrategico":
                _termo = params_raw.strip().strip('"').strip("'")
                r = tools.executar("buscar_estrategico", {"termo": _termo})
                resultado_txt = ""
                if r.get("sucesso"):
                    txt = str(r.get("resultado", ""))
                    if "Nenhum" in txt or len(txt) < 10:
                        txt = "(Nenhum resultado encontrado)"
                    else:
                        linhas = [l for l in txt.split('\n') if l.strip()][:10]
                        txt = '\n'.join(linhas)
                    resultado_txt = txt[:2000]
                else:
                    resultado_txt = "(Erro ao executar)"
                resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n{resultado_txt}")
                ferramentas_usadas.append({"ferramenta": nome_fer, "params": params_raw, "resultado": resultado_txt[:500]})
                print(f" -> {len(resultado_txt.split(chr(10)))} linhas")
            
            elif nome_fer == "ler_arquivo":
                caminho_completo = os.path.join(BASE, params_raw) if not params_raw.startswith('/') else params_raw
                if os.path.exists(caminho_completo) and os.path.isfile(caminho_completo):
                    try:
                        with open(caminho_completo, 'r', encoding='utf-8', errors='replace') as f:
                            txt = f.read()[:2000]
                        resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n{txt}")
                        ferramentas_usadas.append({"ferramenta": nome_fer, "params": params_raw, "resultado": txt[:300]})
                        print(f" -> {len(txt)} chars")
                    except Exception as e:
                        resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n(Erro ao ler: {e})")
                        print(" -> ERRO")
                else:
                    resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n(Arquivo nao encontrado)")
                    print(" -> NAO ENCONTRADO")
            
            else:
                resultados_fer.append(f"[RESULTADO DE {nome_fer}(\"{params_raw}\")]\n(Ferramenta desconhecida)")
                print(" -> FERRAMENTA DESCONHECIDA")
        
        # Monta continuacao do prompt
        if resultados_fer:
            prompt_atual = texto_gerado + "\n\n" + "\n\n".join(resultados_fer) + "\n\n[CONTINUE SUA RESPOSTA USANDO OS RESULTADOS ACIMA]:"
        else:
            prompt_atual = texto_gerado + "\n\n[CONTINUE]:"
        
        duracao = round(_time.time() - t_ciclo, 1)
        print(f"[Ciclo {ciclo}] -> continuacao ({duracao}s)")
    
    tempo_total = round(_time.time() - t0, 1)
    
    # =============================================================
    # AVALIACAO
    # =============================================================
    print("\n" + "=" * 70)
    print("  AVALIACAO")
    print("=" * 70)
    
    resultados_avaliacao = {}
    
    # 1. Usou ferramentas?
    resultados_avaliacao["usou_ferramenta"] = {
        "nota": 2 if usou_ferramenta else 0,
        "peso": 2,
        "detalhe": f"Usou {len(ferramentas_usadas)} ferramentas: {ferramentas_usadas}" if usou_ferramenta else "NAO usou ferramentas"
    }
    
    # 2. Codigo citado existe no projeto?
    codigo_real = 0
    for f in ferramentas_usadas:
        resultado = f.get("resultado", "")
        if "data-canary" in resultado or ".lua" in resultado or "function " in resultado:
            codigo_real += 1
    resultados_avaliacao["codigo_real"] = {
        "nota": min(codigo_real * 1.5, 3),
        "peso": 3,
        "detalhe": f"{codigo_real} resultados com codigo real do projeto" if codigo_real > 0 else "Nenhum codigo real encontrado"
    }
    
    # 3. Nao inventou funcoes?
    resposta_lower = resposta_final.lower() if resposta_final else ""
    funcoes_inventadas = re.findall(r'function\s+(\w+)', resposta_lower)
    funcoes_reais = 0
    for func in funcoes_inventadas:
        for f in ferramentas_usadas:
            if func.lower() in f.get("resultado", "").lower():
                funcoes_reais += 1
                break
    funcoes_fake = len(funcoes_inventadas) - funcoes_reais
    nota_inventou = max(0, 3 - funcoes_fake)
    resultados_avaliacao["nao_inventou"] = {
        "nota": nota_inventou,
        "peso": 3,
        "detalhe": f"{funcoes_fake} funcoes inventadas, {funcoes_reais} comprovadas" if funcoes_inventadas else "Nenhuma funcao citada"
    }
    
    # 4. Resposta coesa final?
    if resposta_final and len(resposta_final) > 100:
        nota_coesao = 2
        det_coesao = f"Resposta coerente ({len(resposta_final)} chars)"
    elif resposta_final:
        nota_coesao = 1
        det_coesao = f"Resposta curta ({len(resposta_final)} chars)"
    else:
        nota_coesao = 0
        det_coesao = "Sem resposta final"
    resultados_avaliacao["coesao"] = {
        "nota": nota_coesao,
        "peso": 2,
        "detalhe": det_coesao
    }
    
    # Calcula nota final
    total_peso = sum(r["peso"] for r in resultados_avaliacao.values())
    total_obtido = sum(r["nota"] for r in resultados_avaliacao.values())
    nota_final = round(total_obtido / total_peso * 10, 1)
    
    print()
    for nome, r in resultados_avaliacao.items():
        status = "OK" if r["nota"] >= r["peso"] * 0.7 else "FALHA" if r["nota"] == 0 else "PARCIAL"
        print(f"  [{status}] {nome}: {r['nota']}/{r['peso']} | {r['detalhe']}")
    
    print(f"\n  NOTA FINAL: {nota_final}/10")
    print(f"  CICLOS: {ciclo}/{_MAX_CICLOS}")
    print(f"  TEMPO: {tempo_total}s")
    print()
    
    # Mostra resposta final (resumida)
    if resposta_final:
        print("=" * 70)
        print("  RESPOSTA FINAL (resumo)")
        print("=" * 70)
        # Remove blocos de codigo para resumo
        resumo = re.sub(r'```[\s\S]*?```', '[BLOCO_CODIGO]', resposta_final)
        if len(resumo) > 1000:
            resumo = resumo[:1000] + "\n... [truncado]"
        print(f"\n{resumo}")
        print(f"\n  [{len(resposta_final)} chars totais]")
    
    print("=" * 70)
    
    # Salva resultado
    resultado = {
        "pergunta": PERGUNTA_SIMPLES,
        "resposta_final": resposta_final,
        "tempo": tempo_total,
        "ciclos": ciclo,
        "ferramentas_usadas": ferramentas_usadas,
        "avaliacao": {k: v for k, v in resultados_avaliacao.items()},
        "nota_final": nota_final,
    }
    out_path = os.path.join(BASE, 'sandbox', '.mcr_react_result.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultado salvo em: sandbox/.mcr_react_result.json")
    
    return nota_final >= 7.0


if __name__ == "__main__":
    ok = executar_teste()
    if ok:
        print("\nTESTE REACT: APROVADO")
    else:
        print("\nTESTE REACT: REPROVADO (nota < 7.0)")
    sys.exit(0 if ok else 1)
