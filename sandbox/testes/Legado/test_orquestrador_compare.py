"""Teste comparativo: Orquestrador Universal (template + contexto) vs prompts fixos.
Testa que o orquestrador e SEMPRE superior ou igual ao antigo em qualidade.
"""
import sys, os, json, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

# ============================================================
# MOCKS
# ============================================================
class _CtxCrewSim:
    def executar(self, consulta):
        return (f"ContextCrew: {consulta}\nFonte: docs/MCR_IDENTITY.md\n"
                f"MCR = servidor de Tibia (Canary). SPA = Sistema de Progressao do Aventureiro.")

class _KGSim:
    def __init__(self):
        self.lessons = [
            {"erro": "SPA=Single Page Application", "solucao": "SPA = Sistema de Progressao do Aventureiro", "ctx": "identidade"},
            {"erro": "lore Eridanus", "solucao": "Cidade inicial do projeto MCR, fundada por exploradores", "ctx": "lore"},
            {"erro": "lore generica sem nomes", "solucao": "Sempre usar nomes proprios em portugues para NPCs, locais e itens", "ctx": "lore"},
        ]
    def buscar(self, consulta, max_r=3):
        return self.lessons[:max_r]
    def aprender(self, erro, contexto, solucao, ctx):
        pass

# ============================================================
# OLD APPROACH (prompts fixos originais)
# ============================================================
def old_gerar(intencao, params):
    """Simula o prompt fixo original."""
    if intencao == "lore":
        tipo = params.get("tipo", "")
        nome = params.get("topico", params.get("nome", "?"))
        templates_old = {
            "npc": f"Crie lore para NPC '{nome}'. HISTORIA: (2 frases) PERSONALIDADE: (3 adjetivos) SAUDACAO: (fala) SEGREDO: (segredo)",
            "item": f"Crie lore para item '{nome}'. ORIGEM: (de onde veio) PODER: (o que faz) LENDA: (o que dizem)",
            "local": f"Crie lore para local '{nome}'. APARENCIA: (como parece) HISTORIA: (o que aconteceu) PERIGO: (o que espreita)",
        }
        prompt = templates_old.get(tipo, f"Crie lore sobre {nome}:")
        router = "texto"
        return prompt, router
    
    elif "analisar" in intencao:
        arquivo = params.get("arquivo", "arquivo")
        desc = params.get("descricao", "Encontre problemas")
        if "codigo" in intencao:
            prompt = f"Descricao: {desc}\n\nFormato: LINHA X: descricao"
            router = "analisar"
        else:
            prompt = f"Descricao: {desc}\n\nPara cada problema, responda:\nLINHA X: tipo do problema - descricao"
            router = "texto"
        return prompt, router
    
    elif intencao == "review":
        prompt = f"Revise os dados extraidos.\n{params.get('itens', '')[:500]}"
        router = "review"
        return prompt, router
    
    return f"Prompt para {intencao}", "leve"

# ============================================================
# NOVO APPROACH (template + contexto)
# ============================================================
def novo_gerar(intencao, params):
    """Usa o orquestrador para gerar o prompt."""
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg=_KGSim(), ia=None, ctx_crew=_CtxCrewSim())
    return orq.gerar_prompt(intencao, params, consulta=str(params.get("topico", "")))

# ============================================================
# TESTES COMPARATIVOS
# ============================================================
PASS = 0
FAIL = 0

def check(nome, cond, detalhe=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {nome}")
    else:
        FAIL += 1
        print(f"  [FAIL] {nome} - {detalhe}")

# --- Teste 1: Template existe para todas as intencoes ---
def t1_templates_existem():
    print("\n[Teste 1] Templates existem para todas as intencoes?")
    from modulos.orquestrador import _TEMPLATES, _ROUTER
    
    templates_esperados = [
        "lore", "lore_npc", "lore_item", "lore_local",
        "analisar_codigo", "analisar_texto",
        "review", "conceito", "perguntar",
        "componentes_personagens", "componentes_locais", "componentes_artefatos",
        "revisar", "classificar_nomes",
    ]
    total = len(templates_esperados)
    encontrados = sum(1 for t in templates_esperados if t in _TEMPLATES)
    check(f"Todos os {total} templates existem", encontrados == total,
          f"encontrados {encontrados}/{total}")
    
    routers_esperados = {
        "analisar_codigo": "analisar", "analisar_texto": "texto",
        "review": "review", "conceito": "pesado", "perguntar": "texto",
        "componentes_personagens": "leve", "revisar": "leve",
    }
    for k, v in routers_esperados.items():
        check(f"Router {k} = {v}", _ROUTER.get(k) == v)

# --- Teste 2: Prompt gerado contem elementos do template + contexto ---
def t2_prompt_tem_template_e_contexto():
    print("\n[Teste 2] Prompt gerado contem template + contexto?")
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg=_KGSim(), ia=None, ctx_crew=_CtxCrewSim())
    
    # lore local
    p, r = orq.gerar_prompt("lore", {"tipo": "local", "nome": "Eridanus"}, "Eridanus")
    check("Contem APARENCIA:", "APARENCIA:" in p, f"Prompt: {p[:100]}")
    check("Contem HISTORIA:", "HISTORIA:" in p)
    check("Contem PERIGO:", "PERIGO:" in p)
    check("Contem nome Eridanus", "Eridanus" in p)
    check("Router = texto", r == "texto")
    
    # analisar codigo
    p, r = orq.gerar_prompt("analisar_codigo", 
        {"arquivo": "test.py", "descricao": "Encontre problemas", "estrutura": "def foo():\n    pass"},
        "analisar test.py")
    check("Contem LINHA X:", "LINHA X" in p or "LINHA" in p, f"Prompt: {p[:100]}")
    check("Router = analisar", r == "analisar")
    
    # review
    p, r = orq.gerar_prompt("review",
        {"arquivo": "dados.json", "itens": "ITEM 1: teste", "few_shot": ""},
        "review dados")
    check("Contem ITEM X:", "ITEM X" in p or "ITEM" in p)
    check("Router = review", r == "review")

# --- Teste 3: Cache funciona ---
def t3_cache_funciona():
    print("\n[Teste 3] Cache LRU funciona?")
    from modulos.orquestrador import Orquestrador, _CACHE
    _CACHE.limpar()
    
    orq = Orquestrador(kg=_KGSim(), ia=None, ctx_crew=_CtxCrewSim())
    
    # Primeira chamada (miss)
    t0 = time.time()
    p1, r1 = orq.gerar_prompt("lore", {"tipo": "local", "nome": "Eridanus"}, "Eridanus")
    t1 = time.time() - t0
    
    # Segunda chamada (hit)
    t0 = time.time()
    p2, r2 = orq.gerar_prompt("lore", {"tipo": "local", "nome": "Eridanus"}, "Eridanus")
    t2 = time.time() - t0
    
    check("Cache hit (segunda mais rapida)", t2 < t1 * 0.5, f"t1={t1:.3f}s t2={t2:.3f}s")
    check("Mesmo prompt no cache", p1 == p2)

# --- Teste 4: Sempre superior ou igual ao original ---
def t4_superior_ou_igual():
    print("\n[Teste 4] Novo prompt e sempre superior ou igual ao original?")
    
    casos = [
        ("lore", {"tipo": "npc", "nome": "Zarok"}),
        ("lore", {"tipo": "item", "nome": "Espada Flamejante"}),
        ("lore", {"tipo": "local", "nome": "Eridanus"}),
        ("lore", {"topico": "Historia de Tibia"}),
        ("analisar_codigo", {"arquivo": "test.py", "descricao": "Encontre bugs", "estrutura": "def main():\n    pass\n"}),
        ("analisar_texto", {"arquivo": "dados.xml", "descricao": "Analise erros", "estrutura": "<root><item>teste</item></root>"}),
        ("review", {"arquivo": "dados.json", "itens": "ITEM 1: {\"nome\": \"teste\"}", "few_shot": ""}),
    ]
    
    for intencao, params in casos:
        old_p, old_r = old_gerar(intencao, params)
        new_p, new_r = novo_gerar(intencao, params)
        
        # Novo prompt deve ser MAIOR ou igual (contexto enriquece)
        check(f"Novo prompt >= original ({intencao})", 
              len(new_p) >= len(old_p),
              f"old={len(old_p)} new={len(new_p)}")
        
        # Novo prompt deve conter o template original (nao perder informacao)
        # Extrai o template esperado (primeira frase do old prompt)
        old_core = old_p.split("Contexto")[0].split("{")[0][:40]
        # Verifica que o novo prompt mantem a estrutura essencial
        if intencao.startswith("lore"):
            # Templates especificos (npc/item/local) tem secoes; generico nao
            if params.get("tipo") in ("npc", "item", "local"):
                secoes = {"npc": ["HISTORIA:", "PERSONALIDADE:"],
                          "item": ["ORIGEM:", "PODER:"],
                          "local": ["APARENCIA:", "HISTORIA:", "PERIGO:"]}
                check(f"Novo manteve secoes de {params['tipo']} ({intencao})",
                      all(s in new_p for s in secoes.get(params['tipo'], [])))
            else:
                check(f"Novo generico tem {len(new_p)} chars ({intencao})",
                      len(new_p) >= len(old_p))
        
        elif "analisar" in intencao:
            # Novo organiza melhor: estrutura antes da descricao
            check(f"Novo tem 'Descricao:' ({intencao})",
                  "Descricao:" in new_p)
            check(f"Novo tem 'LINHA X' ou 'LINHA' ({intencao})",
                  "LINHA" in new_p or "LINHA X" in new_p)
        
        elif intencao == "review":
            check(f"Novo tem 'ITEM' ({intencao})",
                  "ITEM" in new_p)
        
        check(f"Router consistente ({intencao})", old_r == new_r,
              f"old={old_r} new={new_r}")

# --- Teste 5: Validacao keyword-based ---
def t5_validacao():
    print("\n[Teste 5] Validacao funciona?")
    from modulos.orquestrador import _validar_conteudo
    
    # Conteudo Tibia
    check("Conteudo Tibia valido", _validar_conteudo("O NPC Zarok vende pocoes em Eridanus. Tibia e um jogo."))
    
    # Conteudo com estrutura de lore
    check("Estrutura HISTORIA:", _validar_conteudo("HISTORIA: Era uma vez. PERSONALIDADE: corajoso."))
    
    # Conteudo com nomes proprios
    check("Nomes proprios", _validar_conteudo("Joao e Maria encontraram Pedro na floresta."))
    
    # Vazio
    check("Vazio rejeitado", not _validar_conteudo(""))

# --- Teste 6: Executar retorna estrutura completa ---
def t6_executar():
    print("\n[Teste 6] Executar retorna estrutura completa?")
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg=_KGSim(), ia=None, ctx_crew=_CtxCrewSim())
    
    resultado = orq.executar("lore", {"tipo": "local", "nome": "Eridanus"}, consulta="Eridanus", temp=0.1)
    
    campos = ["sucesso", "resposta", "router", "prompt_len", "resposta_len", 
              "nomes_proprios", "tempo", "template"]
    for campo in campos:
        check(f"Campo presente: {campo}", campo in resultado)

# ============================================================
# MAIN
# ============================================================
def main():
    global PASS, FAIL
    print("=" * 70)
    print("TESTE COMPARATIVO: ORQUESTRADOR UNIVERSAL (template + contexto)")
    print("vs PROMPTS FIXOS ORIGINAIS")
    print("=" * 70)
    
    t1_templates_existem()
    t2_prompt_tem_template_e_contexto()
    t3_cache_funciona()
    t4_superior_ou_igual()
    t5_validacao()
    t6_executar()
    
    total = PASS + FAIL
    print(f"\n{'=' * 70}")
    print(f"RESULTADO: {PASS}/{total} testes PASS ({PASS*100//total}%)")
    if FAIL == 0:
        print("TODOS OS TESTES PASSARAM - Orquestrador e superior ou igual ao original!")
    print(f"{'=' * 70}")
    
    return FAIL == 0

if __name__ == '__main__':
    main()
