#!/usr/bin/env python3
"""TESTE DE CRIACAO — MCR-DevIA cria codigo NOVO seguindo padroes REAIS do projeto.

O LLM precisa:
1. Explorar o codigo real (buscar_estrategico, ler_arquivo)
2. Identificar o padrao das funcoes existentes
3. CRIAR codigo novo que SEGUE o padrao
4. Nao inventar APIs que nao existem
"""
import sys, os, re, json, time as _time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

_MAX_CICLOS = 6

PERGUNTA = (
    "Crie um sistema de COMBOS para o SPA do MCR. "
    "Crie 3 combos que combinem habilidades de dominios diferentes (ex: Fogo + Gelo, "
    "Fogo + Terra, Gelo + Energia). "
    "Para cada combo, gere o codigo Lua seguindo o padrao DOS ARQUIVOS EXISTENTES "
    "no projeto MCR. Cada combo deve incluir: nome, dominios envolvidos, "
    "nível minimo em cada dominio, efeito do combo, e a funcao Lua que o implementa. "
    "USE as ferramentas para descobrir o padrao real do projeto ANTES de criar."
)

PROMPT_SISTEMA = """[SISTEMA]
Voce e um desenvolvedor do Projeto MCR especializado em criar codigo Lua para o SPA.

[FERRAMENTAS DISPONIVEIS]
Use [FER: ...] para investigar o codigo existente ANTES de criar.

- buscar_estrategico(termo): descobre diretorios, arquivos e funcoes do projeto
  Ex: [FER: buscar_estrategico("SPA habilidades")]
  Retorna: estrutura com diretorios, arquivos e funcoes

- ler_arquivo(caminho): le conteudo COMPLETO de arquivo
  Ex: [FER: ler_arquivo("data-canary/scripts/MCR/SPA/habilidades/fogo.lua")]
  Retorna: conteudo do arquivo

- gerar_esqueleto(contexto, tipo): gera um ESQUELETO de codigo com @BLANK_N para preenchimento
  * contexto: descricao do que criar (ex: "funcao de combo Fogo+Gelo baseada em postura.lua")
  * tipo: "codigo" | "texto" | "analise"
  Ex: [FER: gerar_esqueleto("Combo Fogo+Gelo seguindo padrao de comandos_spa.lua", "codigo")]
  Retorna: esqueleto com @BLANK_1, @BLANK_2 etc.

- preencher_blank(esqueleto, blank_id, contexto): preenche UM blank especifico
  * esqueleto: o esqueleto com @BLANK_N
  * blank_id: "1" | "2" | etc
  * contexto: o que preencher (ex: "dano de fogo com congelamento")
  Ex: [FER: preencher_blank("...esqueleto...", "1", "logica do dano elemental")]
  Retorna: esqueleto com o blank preenchido

[REGRAS CRITICAS]
1. [FER: ...] NUNCA dentro de ```lua — use FORA dos blocos de codigo
2. PRIMEIRO explore o projeto: [FER: buscar_estrategico("TERMO")]
3. DEPOIS leia arquivos: [FER: ler_arquivo("...")] para ver APIs reais
4. IDENTIFIQUE o padrao REAL (getPosture, getSPA, onSay)
5. DEPOIS crie ESQUELETO com [FER: gerar_esqueleto("descricao", "codigo")]
6. PREENCHA cada blank com [FER: preencher_blank("esqueleto", "N", "contexto")]
7. NUNCA invente APIs — copie as que existem nos arquivos reais
8. Responda em PT-BR. Quando terminar, nao use mais [FER:]

EXEMPLO CORRETO:
[FER: buscar_estrategico("SPA")]  → fora de ```lua
[FER: ler_arquivo("core/comandos_spa.lua")]  → fora de ```lua
[FER: gerar_esqueleto("combo", "codigo")]  → gera estrutura com @BLANK_1

EXEMPLO ERRADO (NAO FAZER):
```lua
-- [FER: buscar_estrategico(...)]  ← comentario nao executa!
```

[PERGUNTA]
{pergunta}

[RESPOSTA]:"""


def executar_teste():
    print("=" * 70)
    print("  TESTE DE CRIACAO — MCR-DevIA cria codigo seguindo padroes reais")
    print("=" * 70)
    print(f"\nPergunta: {PERGUNTA[:100]}...")
    
    from modulos.ia import IA
    from modulos.tool_orchestrator import ToolOrchestrator
    
    ia = IA()
    tools = ToolOrchestrator()
    
    print("[Init] IA + ToolOrchestrator carregados")
    
    # ReAct Loop
    historico = []
    resposta_final = ""
    ferramentas_usadas = []
    t0 = _time.time()
    
    # Seed: executa buscar_estrategico automaticamente antes do loop
    print("\n[Seed] Buscando dados reais do projeto...")
    for _termo_seed in ["SPA", "habilidade", "postura"]:
        _r = tools.executar("buscar_estrategico", {"termo": _termo_seed})
        if _r.get("sucesso"):
            _txt = str(_r.get("resultado", ""))
            if "Nenhum" not in _txt and len(_txt) > 50:
                historico.append(f"[RESULTADO DE buscar_estrategico(\"{_termo_seed}\")]\n{_txt[:2500]}")
                print(f"  Seed: {_termo_seed} ({len(_txt.split(chr(10)))} linhas)")
                break
    
    prompt_atual = PROMPT_SISTEMA.format(pergunta=PERGUNTA)
    
    for ciclo in range(1, _MAX_CICLOS + 1):
        t_ciclo = _time.time()
        print(f"\n[Ciclo {ciclo}] LLM pensando...")
        
        try:
            texto_gerado = ia.gerar(prompt_atual, 0.3, 'pesado') or ""
        except Exception as e:
            print(f"  ERRO: {e}")
            break
        
        if not texto_gerado or len(texto_gerado) < 5:
            break
        
        # Extrai [FER: ...]
        texto_limpo = re.sub(r'```[\s\S]*?```', '[BLOCO_CODIGO]', texto_gerado)
        fers = re.findall(r'\[FER:\s*(.*?)\]', texto_limpo)
        
        if not fers:
            resposta_final = texto_gerado
            print(f"  Resposta final ({len(resposta_final)} chars, {_time.time()-t_ciclo:.1f}s)")
            break
        
        # Executa ferramentas
        resultados = []
        for fer_str in fers:
            fer_str = fer_str.strip()
            parts = fer_str.split("(", 1)
            nome = parts[0].strip()
            params = parts[1].rstrip(")").strip().strip('"').strip("'") if len(parts) > 1 else ""
            
            print(f"  [FER: {nome}(\"{params}\")] ", end="")
            
            if nome == "buscar_estrategico":
                r = tools.executar("buscar_estrategico", {"termo": params})
                txt = str(r.get("resultado", "(Erro)")) if r.get("sucesso") else "(Erro)"
                print(f"{len(txt.split(chr(10)))} linhas")
                
            elif nome == "ler_arquivo":
                path_full = os.path.join(BASE, params) if not os.path.isabs(params) else params
                if os.path.isfile(path_full):
                    try:
                        with open(path_full, 'r', encoding='utf-8', errors='replace') as f:
                            txt = f.read()[:4000]
                        print(f"{len(txt)} chars")
                    except Exception as e:
                        txt = f"(Erro ao ler: {e})"
                        print("ERRO")
                else:
                    txt = "(Arquivo nao encontrado)"
                    print("NAO ENCONTRADO")
            else:
                txt = f"(Ferramenta desconhecida: {nome})"
                print("DESCONHECIDA")
            
            resultados.append(f"[RESULTADO DE {fer_str}]\n{txt[:3000]}")
            ferramentas_usadas.append({"ferramenta": nome, "params": params})
        
        prompt_atual = texto_gerado + "\n\n" + "\n\n".join(resultados) + "\n\n[CONTINUE USANDO OS RESULTADOS ACIMA. Se tiver dados suficientes, crie o codigo final sem [FER:]]:"
        print(f"  -> continuacao ({_time.time()-t_ciclo:.1f}s)")
    
    tempo_total = round(_time.time() - t0, 1)
    
    # =============================================================
    # AVALIACAO
    # =============================================================
    print("\n" + "=" * 70)
    print("  AVALIACAO")
    print("=" * 70)
    
    def normalizar(t):
        import unicodedata
        return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode('ascii').lower()
    
    r_norm = normalizar(resposta_final) if resposta_final else ""
    
    criterios = {
        "explorou_codigo": {
            "peso": 3,
            "ok": len(ferramentas_usadas) >= 2,
            "detalhe": f"Usou {len(ferramentas_usadas)} ferramentas"
        },
        "tres_combo": {
            "peso": 2,
            "ok": sum(1 for t in ["fogo+gelo", "fogo+terra", "gelo+energia", "fogo", "gelo", "terra", "energia"] if t in r_norm) >= 3,
            "detalhe": "3 combos mencionados" if sum(1 for t in ["fogo", "gelo", "terra", "energia"] if t in r_norm) >= 3 else "Menos de 3 dominios"
        },
        "codigo_lua": {
            "peso": 2,
            "ok": "```lua" in resposta_final or "```" in resposta_final,
            "detalhe": "Bloco de codigo Lua presente" if "```lua" in resposta_final or "```" in resposta_final else "Sem bloco de codigo"
        },
        "segue_padrao_real": {
            "peso": 3,
            "ok": any(api in r_norm for api in ["getposture", "getspa", "onsay", "player:", "getlevel"]),
            "detalhe": "Usa APIs reais do projeto" if any(api in r_norm for api in ["getposture", "getspa", "onsay", "player:", "getlevel"]) else "APIs nao identificadas"
        },
        "nao_inventou": {
            "peso": 2,
            "ok": "function " not in resposta_final or any(api in r_norm for api in ["getposture", "getspa"]),
            "detalhe": "Funcoes compativeis com o projeto"
        },
        "nivel_minimo": {
            "peso": 1,
            "ok": "nivel" in r_norm or "level" in r_norm,
            "detalhe": "Validacao de nivel incluida"
        },
        "sinergia": {
            "peso": 1,
            "ok": "sinergia" in r_norm or "synergy" in r_norm,
            "detalhe": "Conceito de sinergia mencionado"
        }
    }
    
    total_peso = sum(c["peso"] for c in criterios.values())
    total_obtido = sum(c["peso"] for c in criterios.values() if c["ok"])
    nota_final = round(total_obtido / total_peso * 10, 1)
    
    print()
    for nome, c in criterios.items():
        status = "OK" if c["ok"] else "FALHA"
        print(f"  [{status}] {nome}: {c['detalhe']}")
    
    print(f"\n  NOTA FINAL: {nota_final}/10")
    print(f"  TEMPO: {tempo_total}s")
    print(f"  CICLOS: {ciclo}/{_MAX_CICLOS}")
    print(f"  FERRAMENTAS: {len(ferramentas_usadas)}")
    
    if resposta_final:
        print(f"\n  RESPOSTA: {len(resposta_final)} chars")
        # Mostra inicio da resposta
        print("\n" + "=" * 70)
        # Remove blocos de codigo para nao poluir
        resumo = resposta_final[:2000]
        print(resumo)
        if len(resposta_final) > 2000:
            print(f"\n... [{len(resposta_final)} chars totais]")
        print("=" * 70)
    
    # Salva
    resultado = {
        "pergunta": PERGUNTA,
        "resposta": resposta_final,
        "tempo": tempo_total,
        "ciclos": ciclo,
        "ferramentas": ferramentas_usadas,
        "criterios": {k: v["ok"] for k, v in criterios.items()},
        "nota": nota_final,
    }
    out_path = os.path.join(BASE, 'sandbox', '.mcr_teste_criacao.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n  Salvo: sandbox/.mcr_teste_criacao.json")
    
    return nota_final >= 7.0


if __name__ == "__main__":
    ok = executar_teste()
    print(f"\nTESTE CRIACAO: {'APROVADO' if ok else 'REPROVADO'} (nota < 7.0)")
    sys.exit(0 if ok else 1)
