"""MCR-DevIA — Detector de Consistencia de Tipos
O sistema aprende sozinho qual API pertence a cada tipo de arquivo.
Se gerar um "item" que usa API de "monster", detecta e aprende."""
import os, re, json

KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

# Carrega padroes REAIS do LearningScan (581 arquivos do Canary)
# Se disponivel, usa dados reais em vez de TIPOS_API hardcoded
LEARNING_PATH = r"E:\Projeto MCR\sandbox\.mcr_learning_scan.json"
TIPOS_API = {}

if os.path.exists(LEARNING_PATH):
    with open(LEARNING_PATH, encoding="utf-8") as f:
        scan_data = json.load(f)
    padroes_reais = scan_data.get("padroes", {})
    
    # Converte padroes do LearningScan para regex de deteccao
    # Inclui funcoes CONFIRMADAS (2+ arquivos) e EXCLUSIVAS do tipo
    # Funcoes genericas (aparecem em varios tipos) sao IGNORADAS
    for tipo, funcoes in padroes_reais.items():
        funcoes_confirmadas = [f for f, c in funcoes.items() if c >= 2]
        if not funcoes_confirmadas:
            continue
        
        # Filtra funcoes que sao EXCLUSIVAS deste tipo
        # (nao aparecem em 2+ arquivos de outros tipos)
        funcoes_exclusivas = []
        for func in funcoes_confirmadas:
            # Verifica se aparece em outros tipos
            aparece_em_outros = False
            for outro_tipo, outras_funcoes in padroes_reais.items():
                if outro_tipo == tipo:
                    continue
                if func in outras_funcoes and outras_funcoes[func] >= 2:
                    aparece_em_outros = True
                    break
            if not aparece_em_outros:
                funcoes_exclusivas.append(func)
        
        if funcoes_exclusivas:
            construtor = tipo.title()
            regex_lista = [rf"{construtor}\("]
            regex_lista += [rf"{f}\(" for f in funcoes_exclusivas]
            TIPOS_API[tipo] = regex_lista
            print(f"  [Carregado] {tipo}: {len(funcoes_exclusivas)} funcoes exclusivas")
else:
    # Fallback: TIPOS_API hardcoded (caso LearningScan nunca tenha rodado)
    TIPOS_API = {
        "monster": [r"Monster\(|setMaxHealth|setSpeed|setOutfit|setCustomName|setMaster|setPetBehavior|setDropLoot",
                    r"addLoot|setHealth|setAttack|setDefense|setExperience"],
        "item": [r"Item\(|setAttribute|setDuration|setActionId|setType"],
        "npc": [r"NPC\(|setSaudacao|npcHandler|KeywordHandler|NpcHandler"],
        "spell": [r"Spell\(|setDamage|setManaCost|setCooldown|vocations"],
        "quest": [r"Quest\(|setDescricao|addObjetivo|addRecompensa|addCondition"],
    }

def detectar_tipo_arquivo(path):
    """Detecta o tipo esperado de um arquivo pelo nome e conteudo."""
    nome = os.path.basename(path).lower()
    
    # Tenta detectar pelo nome
    for tipo in ["npc", "monster", "spell", "item", "quest", "talkaction"]:
        if tipo in nome:
            return tipo
    
    # Tenta detectar pelo conteudo (primeiras linhas)
    try:
        with open(path, encoding="utf-8") as f:
            cabecalho = f.read(200)
    except:
        return None
    
    for tipo, padroes in TIPOS_API.items():
        for padrao in padroes:
            if re.search(padrao, cabecalho, re.IGNORECASE):
                return tipo
    return None

def verificar_consistencia(path):
    """Verifica se o arquivo USA a API certa para o tipo dele.
    Adapta-se a disponibilidade de dados: se nao tem padroes para o tipo,
    so verifica o construtor."""
    tipo_esperado = detectar_tipo_arquivo(path)
    if not tipo_esperado:
        return True, ["tipo nao identificado"]
    
    with open(path, encoding="utf-8") as f:
        conteudo = f.read()
    
    problemas = []
    
    # Se tem padroes carregados para este tipo, verifica normalmente
    tem_padroes_tipo = tipo_esperado in TIPOS_API and TIPOS_API[tipo_esperado]
    
    if tem_padroes_tipo:
        # Verifica se USA API de outros tipos
        for outro_tipo, padroes in TIPOS_API.items():
            if outro_tipo == tipo_esperado:
                continue
            for padrao in padroes:
                if re.search(padrao, conteudo, re.IGNORECASE):
                    m = re.search(padrao, conteudo, re.IGNORECASE)
                    trecho = conteudo[max(0, m.start()-10):m.end()+20]
                    problemas.append(f"USA API de {outro_tipo}: ...{trecho.strip()[:60]}...")
        
        if problemas:
            return False, problemas
        
        # Verifica se USA a API correta
        tem_api_certa = False
        for padrao in TIPOS_API.get(tipo_esperado, []):
            if re.search(padrao, conteudo, re.IGNORECASE):
                tem_api_certa = True
                break
        
        if not tem_api_certa:
            problemas.append(f"NAO usa API de {tipo_esperado}")
            return False, problemas
    else:
        # SEM DADOS do LearningScan para este tipo
        # So verifica o construtor (Item/NPC/Monster/Spell/Quest)
        construtores = {"npc": "NPC", "monster": "Monster", "item": "Item",
                       "spell": "Spell", "quest": "Quest"}
        construtor_esperado = construtores.get(tipo_esperado, tipo_esperado.title())
        
        # Verifica se TEM o construtor do tipo esperado
        if construtor_esperado + "(" not in conteudo:
            problemas.append(f"NAO usa construtor {construtor_esperado}")
            return False, problemas
        
        # Verifica se NAO tem construtor de OUTRO tipo
        for tipo_outro, construtor_outro in construtores.items():
            if tipo_outro == tipo_esperado:
                continue
            if construtor_outro + "(" in conteudo:
                problemas.append(f"USA construtor de {tipo_outro}: {construtor_outro}")
                return False, problemas
    
    return True, []

def aprender_com_erro(tipo_gerado, tipo_api_usada, trecho, path_arquivo):
    """Registra no KG que 'tipo_gerado' NAO deve usar API de 'tipo_api_usada'."""
    kg = {"lessons": []}
    if os.path.exists(KG_PATH):
        with open(KG_PATH, encoding="utf-8") as f:
            kg = json.load(f)
    
    lesson = {
        "context": f"consistencia_tipos",
        "tipo_gerado": tipo_gerado,
        "api_proibida": tipo_api_usada,
        "trecho": trecho[:200],
        "arquivo": path_arquivo,
        "tipo_aprendizado": "contra_exemplo"
    }
    
    # Evita duplicatas
    for l in kg.get("lessons", []):
        if (l.get("tipo_gerado") == tipo_gerado and 
            l.get("api_proibida") == tipo_api_usada):
            return  # Ja aprendeu
    
    kg.setdefault("lessons", []).append(lesson)
    with open(KG_PATH, "w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    print(f"  [KG] Aprendido: {tipo_gerado} nao deve usar API de {tipo_api_usada}")

if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("  MCR-DevIA — DETECTOR DE CONSISTENCIA DE TIPOS")
    print("  Verifica se cada arquivo usa a API correta pro tipo")
    print("=" * 60)
    
    # Escaneia arquivos gerados
    sandbox = r"E:\Projeto MCR\sandbox"
    gerados = [f for f in os.listdir(sandbox) if f.startswith("devia_") and f.endswith(".lua")]
    
    if not gerados:
        print("Nenhum arquivo gerado encontrado.")
        sys.exit(0)
    
    print(f"\nVerificando {len(gerados)} arquivos gerados...")
    erros = 0
    
    for fname in sorted(gerados):
        path = os.path.join(sandbox, fname)
        tipo = detectar_tipo_arquivo(path)
        consistente, problemas = verificar_consistencia(path)
        
        if consistente:
            print(f"  [OK] {fname} ({tipo})")
        else:
            erros += 1
            print(f"  [INCONSISTENTE] {fname} (tipo detectado: {tipo})")
            for p in problemas:
                print(f"    -> {p}")
                # Aprende com o erro
                if "USA API de" in p:
                    partes = p.split("USA API de")
                    if len(partes) > 1:
                        tipo_api = partes[1].split(":")[0].strip()
                        trecho = p.split("...")[-1][:100]
                        aprender_com_erro(tipo, tipo_api, trecho, path)
    
    print(f"\nResultado: {len(gerados) - erros}/{len(gerados)} consistentes")
    if erros > 0:
        print(f"{erros} arquivos inconsistentes — KG atualizado com contra-exemplos")
    else:
        print("Todos consistentes!")
