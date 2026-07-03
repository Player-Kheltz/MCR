#!/usr/bin/env python3
"""TESTE COMPLETO — Verdade + Complexo + Ferramentas + Criação REAL.

UMA pergunta que exige TUDO:
  - Conhecimento factual (MCR, SPA, SHC, Eridanus, Canary)
  - Raciocínio complexo (integrar SPA + SHC + dominios)
  - Ferramentas de busca (grep, buscar_estrategico, ler_arquivo)
  - Criação REAL de arquivos (lore .md, NPC .lua, conceito .md)
  - Edição de linha específica em arquivo existente

Tudo é VERIFICADO:
  - O arquivo foi criado? (existe no disco)
  - O conteúdo do arquivo está correto? (contém o esperado)
  - A resposta fala a verdade factual? (comparação com MCR_IDENTITY.md)

Uso:
    python tests/test_completo.py
"""
import sys, os, re, json, time as _time, shutil, unicodedata as _uni

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

# ============================================================
# ÚNICA PERGUNTA QUE TESTA TUDO
# ============================================================
PERGUNTA_UNICA = (
    # --- FERRAMENTAS (grep, buscar, ler, editar) ---
    "Primeiro, encontre a definição de SPA no código. Use grep ou buscar_estrategico "
    "para achar arquivos que definem SPA. Leia um deles. "
    "Depois, encontre a linha onde Eridanus é mencionada em MCR_IDENTITY.md e "
    "adicione 'Eridanus = Cidade inicial dos aventureiros' ao final do arquivo sandbox/test_output/TESTE_ERIDANUS.md "
    "(crie o arquivo se não existir).\n\n"
    # --- VERDADE (conhecimento factual) ---
    "Agora responda: O que significa MCR, SPA e SHC? Qual a cidade inicial? "
    "O que é Canary? Quais os 4 dominios elementais do SPA e quais são seus números? "
    "Quantas camadas tem o SHC e quais são?\n\n"
    # --- CRIAÇÃO REAL: Lore de Eridanus ---
    "Crie um arquivo docs/lore_eridanus.md com a lore completa de Eridanus: "
    "sua fundação, geografia, pontos de interesse, e por que é a cidade inicial dos aventureiros. "
    "Use no mínimo 3 parágrafos. Seja criativo mas mantenha o tom de Tibia.\n\n"
    # --- CRIAÇÃO REAL: NPC Tutorial ---
    "Crie um NPC tutorial em data/npc/tutorial_guide.lua seguindo o padrão "
    "real dos NPCs do projeto. O NPC deve se chamar 'Guide MCR' (cid=999) e ensinar "
    "os 4 dominios elementais (Fogo, Gelo, Terra, Energia) para novos jogadores. "
    "Use buscar_estrategico para achar exemplos reais de NPCs primeiro.\n\n"
    # --- CRIAÇÃO REAL: Novo conceito ---
    "Crie um arquivo docs/conceito_nexus.md definindo um novo conceito chamado 'Nexus Elemental': "
    "um sistema que permite ao jogador combinar 2 dominios para criar efeitos especiais. "
    "Explique como se integra ao SPA e SHC existentes. Dê 3 exemplos de combinações.\n\n"
    # --- COMPLEXO: Raciocínio integrado ---
    "Por fim, explique COMO o sistema SPA, SHC e dominios se integram no MCR, "
    "cite exemplos de funções Lua que você encontrou nos arquivos reais, "
    "e mostre como o Nexus Elemental se encaixaria nessa arquitetura."
)

# ============================================================
# CRITÉRIOS DE AVALIAÇÃO
# ============================================================
CRITERIOS = {
    # --- VERDADE (conhecimento factual) ---
    "verdade_mcr": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["projeto mcr", "servidor", "tibia", "customizado"],
        "descricao": "MCR = servidor Tibia customizado"
    },
    "verdade_spa": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["sistema de progressao", "aventureiro", "dominios"],
        "descricao": "SPA = Sistema de Progressao do Aventureiro"
    },
    "verdade_shc": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["habilidades contextuais", "5 camadas", "postura"],
        "descricao": "SHC = Sistema de Habilidades Contextuais, 5 camadas"
    },
    "verdade_eridanus": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["eridanus", "cidade inicial"],
        "descricao": "Eridanus é a cidade inicial"
    },
    "verdade_canary": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["otserv", "canary", "servidor"],
        "descricao": "Canary = servidor OTServ"
    },
    "verdade_4_dominios": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["fogo", "gelo", "terra", "energia"],
        "descricao": "4 dominios elementais: Fogo, Gelo, Terra, Energia"
    },
    "verdade_5_camadas": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["postura", "nivel", "sinergia", "estado", "condicao"],
        "descricao": "5 camadas do SHC: postura, nivel, sinergia, estado, condicao"
    },
    # --- FERRAMENTAS (buscou no código real) ---
    "ferramenta_buscou": {
        "peso": 1,
        "tipo": "resposta",
        "termos": ["getposture", "getspa", "playerspa", "onsay", "function"],
        "descricao": "Usou ferramentas para achar código real (APIs do projeto)"
    },
    "ferramenta_grep": {
        "peso": 1,
        "tipo": "resposta",
        "termos": [".lua", "arquivo"],
        "descricao": "Menciona arquivos .lua específicos encontrados"
    },
    # --- CRIAÇÃO REAL: lore_eridanus.md ---
    "criou_lore_md": {
        "peso": 2,
        "tipo": "arquivo",
        "caminho": "docs/lore_eridanus.md",
        "termos": ["eridanus", "cidade", "aventureiro", "fundação"],
        "descricao": "Criou docs/lore_eridanus.md com lore completa"
    },
    # --- CRIAÇÃO REAL: tutorial_guide.lua ---
    "criou_npc_lua": {
        "peso": 3,
        "tipo": "arquivo",
        "caminho": "data/npc/tutorial_guide.lua",
        "termos": ["guide", "mcr", "999", "fogo", "gelo", "terra", "energia"],
        "descricao": "Criou NPC tutorial_guide.lua com os 4 dominios"
    },
    # --- CRIAÇÃO REAL: conceito_nexus.md ---
    "criou_conceito_md": {
        "peso": 2,
        "tipo": "arquivo",
        "caminho": "docs/conceito_nexus.md",
        "termos": ["nexus", "elemental", "combinar", "dominio"],
        "descricao": "Criou docs/conceito_nexus.md com conceito Nexus Elemental"
    },
    # --- EDIÇÃO REAL: TESTE_ERIDANUS.md ---
    "editou_arquivo": {
        "peso": 1,
        "tipo": "arquivo",
        "caminho": "sandbox/test_output/TESTE_ERIDANUS.md",
        "termos": ["eridanus", "cidade inicial", "aventureiros"],
        "descricao": "Editou/criou TESTE_ERIDANUS.md com conteudo esperado"
    },
    # --- NÃO ALUCINOU ---
    "nao_alucinou_agua": {
        "peso": 1,
        "tipo": "resposta",
        "termos_proibidos": ["agua", "trevas", "luz", "minecraft"],
        "descricao": "Nao inventou dominios que nao existem"
    },
    "nao_alucinou_framework": {
        "peso": 1,
        "tipo": "resposta",
        "termos_proibidos": ["react", "angular", "vue", "django", "flask"],
        "descricao": "Nao confundiu com framework web"
    },
}

# ============================================================
# UTILITÁRIOS
# ============================================================
def _normalizar(texto):
    return _uni.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower().strip()

def _verificar_arquivo(caminho_rel, termos):
    """Verifica se arquivo existe e contém os termos esperados."""
    caminho_abs = os.path.join(BASE, caminho_rel)
    if not os.path.exists(caminho_abs):
        return False, f"Arquivo nao existe: {caminho_rel}", ""
    
    try:
        with open(caminho_abs, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
    except Exception as e:
        return False, f"Erro ao ler: {e}", ""
    
    if len(conteudo.strip()) < 50:
        return False, f"Arquivo muito pequeno: {len(conteudo)} chars", conteudo[:200]
    
    encontrados = []
    faltando = []
    for t in termos:
        if _normalizar(t) in _normalizar(conteudo):
            encontrados.append(t)
        else:
            faltando.append(t)
    
    # Precisa de pelo menos ~60% dos termos
    taxa = len(encontrados) / len(termos)
    if taxa >= 0.6:
        return True, f"OK ({len(encontrados)}/{len(termos)} termos)", conteudo[:300]
    else:
        return False, f"Apenas {len(encontrados)}/{len(termos)} termos encontrados", conteudo[:300]

def _avaliar_resposta(resposta, criterio):
    """Avalia um critério do tipo 'resposta'."""
    r_norm = _normalizar(resposta)
    
    if "termos" in criterio:
        ok = all(_normalizar(t) in r_norm for t in criterio["termos"])
        if ok:
            return True, criterio["descricao"]
        faltando = [t for t in criterio["termos"] if _normalizar(t) not in r_norm]
        return False, f"Faltou: {faltando}"
    
    if "termos_proibidos" in criterio:
        proibidos = [t for t in criterio["termos_proibidos"] if _normalizar(t) in r_norm]
        if not proibidos:
            return True, criterio["descricao"]
        return False, f"Proibido: {proibidos}"
    
    return False, "Criterio desconhecido"


# ============================================================
# LIMPEZA PRÉVIA
# ============================================================
def _limpar_arquivos_teste():
    """Remove arquivos criados por execuções anteriores."""
    arquivos = [
        "docs/lore_eridanus.md",
        "data/npc/tutorial_guide.lua",
        "docs/conceito_nexus.md",
        "sandbox/test_output/TESTE_ERIDANUS.md",
    ]
    for arq in arquivos:
        path = os.path.join(BASE, arq)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"  Limpo: {arq}")
            except Exception as e:
                print(f"  Erro ao limpar {arq}: {e}")


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================
def executar_teste():
    print("=" * 70)
    print("  TESTE COMPLETO — Verdade + Complexo + Ferramentas + Criação REAL")
    print("=" * 70)
    
    # Limpa execuções anteriores
    _limpar_arquivos_teste()
    
    # Inicializa componentes
    print("\n[INICIALIZANDO] PipelineExecutor + KG + ToolOrchestrator...")
    from modulos.kg import KnowledgeGraph
    from modulos.ia import IA
    from modulos.pipeline_executor import PipelineExecutor
    from modulos.tool_orchestrator import ToolOrchestrator
    
    kg = KnowledgeGraph()
    ia = IA()
    tools = ToolOrchestrator()
    
    licoes = kg._get_licoes()
    ativas = [l for l in licoes if not l.get('inactive', False)]
    print(f"  KG: {len(licoes)} lessons, {len(ativas)} ativas")
    
    pipe = PipelineExecutor(kg=kg, ia=ia, tool_orchestrator=tools)
    
    # ============================================================
    # EXECUTA A PERGUNTA ÚNICA
    # O AutoTriggerEngine (no pipeline) detecta intenções,
    # executa ferramentas automaticamente, e coleta dados
    # ANTES de chamar o LLM — tudo sem seed manual
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  PERGUNTA ÚNICA ({len(PERGUNTA_UNICA)} chars)")
    print(f"{'='*70}")
    print(f"\n{PERGUNTA_UNICA[:500]}...")
    print(f"\n[... {len(PERGUNTA_UNICA)} chars totais]")
    
    t0 = _time.time()
    
    try:
        resposta, meta = pipe.executar(
            PERGUNTA_UNICA,
            modo_ia="auto",
            skip_tot=True
        )
    except Exception as e:
        resposta = f"[ERRO] {e}"
        meta = {"status": "ERRO"}
        import traceback
        traceback.print_exc()
    
    tempo_total = round(_time.time() - t0, 1)
    
    print(f"\n{'='*70}")
    print(f"  RESPOSTA DO SISTEMA")
    print(f"{'='*70}")
    print(f"\n{resposta[:3000]}")
    if len(resposta) > 3000:
        print(f"\n... [{len(resposta)} chars totais]")
    print(f"\n  [Resposta: {len(resposta)} chars | Tempo: {tempo_total}s | Meta: {meta}]")
    
    # ============================================================
    # AVALIAÇÃO
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  AVALIAÇÃO POR CRITÉRIO")
    print(f"{'='*70}")
    
    resultados = {}
    total_peso = 0
    total_obtido = 0
    detalhes_por_criterio = []
    
    for nome, crit in sorted(CRITERIOS.items()):
        peso = crit["peso"]
        total_peso += peso
        
        if crit["tipo"] == "resposta":
            ok, detalhe = _avaliar_resposta(resposta, crit)
        elif crit["tipo"] == "arquivo":
            ok, detalhe, _ = _verificar_arquivo(crit["caminho"], crit["termos"])
        else:
            ok, detalhe = False, "Tipo desconhecido"
        
        if ok:
            total_obtido += peso
            resultados[nome] = True
        else:
            resultados[nome] = False
        
        detalhes_por_criterio.append({
            "nome": nome,
            "peso": peso,
            "ok": ok,
            "detalhe": detalhe,
            "descricao": crit.get("descricao", ""),
        })
        
        status = "✅" if ok else "❌"
        print(f"  {status} {nome} (peso {peso}): {detalhe}")
    
    nota_final = round(total_obtido / total_peso * 10, 1) if total_peso > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"  RESULTADO FINAL")
    print(f"{'='*70}")
    print(f"\n  Pontuação: {total_obtido}/{total_peso}")
    print(f"  NOTA FINAL: {nota_final}/10")
    print(f"  Tempo total: {tempo_total}s")
    
    # Categorias
    print(f"\n  --- Por categoria ---")
    categorias = {}
    for nome, crit in CRITERIOS.items():
        cat = nome.split("_")[0]
        if cat not in categorias:
            categorias[cat] = {"total": 0, "ok": 0, "peso_total": 0, "peso_ok": 0}
        categorias[cat]["total"] += 1
        categorias[cat]["peso_total"] += crit["peso"]
        if resultados.get(nome, False):
            categorias[cat]["ok"] += 1
            categorias[cat]["peso_ok"] += crit["peso"]
    
    for cat, stats in sorted(categorias.items()):
        pct = round(stats["peso_ok"] / stats["peso_total"] * 100)
        print(f"    {cat}: {stats['ok']}/{stats['total']} criterios ({pct}% peso) | {stats['peso_ok']}/{stats['peso_total']}")
    
    # ============================================================
    # VERIFICAÇÃO DOS ARQUIVOS CRIADOS
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  VERIFICAÇÃO DOS ARQUIVOS CRIADOS")
    print(f"{'='*70}")
    
    arquivos_para_verificar = [
        ("docs/lore_eridanus.md", "Lore de Eridanus"),
        ("data/npc/tutorial_guide.lua", "NPC Tutorial Guide"),
        ("docs/conceito_nexus.md", "Conceito Nexus Elemental"),
        ("sandbox/test_output/TESTE_ERIDANUS.md", "Teste Eridanus"),
    ]
    
    for caminho, nome in arquivos_para_verificar:
        caminho_abs = os.path.join(BASE, caminho)
        if os.path.exists(caminho_abs):
            try:
                with open(caminho_abs, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
                print(f"\n  ✅ {nome}: {caminho}")
                print(f"     Tamanho: {len(conteudo)} chars, {len(conteudo.splitlines())} linhas")
                # Mostra primeiras 5 linhas
                linhas = conteudo.splitlines()[:5]
                for l in linhas:
                    print(f"     | {l[:100]}")
            except Exception as e:
                print(f"\n  ❌ {nome}: {caminho} — erro ao ler: {e}")
        else:
            print(f"\n  ❌ {nome}: {caminho} — ARQUIVO NÃO CRIADO")
    
    # ============================================================
    # SALVA RESULTADO
    # ============================================================
    resultado = {
        "pergunta": PERGUNTA_UNICA,
        "resposta": resposta,
        "tempo": tempo_total,
        "meta": meta,
        "nota_final": nota_final,
        "total_peso": total_peso,
        "obtido": total_obtido,
        "criterios": detalhes_por_criterio,
        "arquivos_criados": {},
    }
    
    for caminho, nome in arquivos_para_verificar:
        caminho_abs = os.path.join(BASE, caminho)
        if os.path.exists(caminho_abs):
            try:
                with open(caminho_abs, 'r', encoding='utf-8', errors='replace') as f:
                    resultado["arquivos_criados"][caminho] = f.read()
            except Exception:
                resultado["arquivos_criados"][caminho] = "(Erro ao ler)"
        else:
            resultado["arquivos_criados"][caminho] = "(Nao criado)"
    
    out_path = os.path.join(BASE, 'sandbox', '.mcr_teste_completo.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultado salvo: sandbox/.mcr_teste_completo.json")
    print(f"{'='*70}")
    
    return nota_final >= 6.0


if __name__ == "__main__":
    print("\n⚠️  ATENÇÃO: Este teste é COMPREENSIVO e leva vários minutos.")
    print("   Ele cria arquivos REAIS em docs/, data/npc/, e sandbox/test_output/.")
    print("   Os arquivos são limpos no início, mas verifique se há dados importantes.\n")
    
    ok = executar_teste()
    
    print(f"\n{'='*70}")
    print(f"  RESULTADO: {'APROVADO' if ok else 'REPROVADO'}")
    print(f"{'='*70}")
    
    sys.exit(0 if ok else 1)
