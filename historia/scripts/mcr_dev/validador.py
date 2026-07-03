"""validador.py — Valida saida gerada antes de entregar ao usuario."""
import re, os

def validar_codigo(codigo, tipo):
    """Valida o codigo gerado. Retorna (valido, erros, sugestao)."""
    if not codigo or len(codigo.strip()) < 10:
        return False, ["Codigo muito curto ou vazio"], "gere mais codigo"
    
    erros = []
    sugestoes = []
    
    # Valida por tipo
    if tipo == "NPC":
        _validar_npc(codigo, erros, sugestoes)
    elif tipo == "HABILIDADE":
        _validar_shc(codigo, erros, sugestoes)
    elif tipo == "OTUI":
        _validar_otui(codigo, erros, sugestoes)
    elif tipo == "SQL":
        _validar_sql(codigo, erros, sugestoes)
    elif tipo == "LUA":
        _validar_lua(codigo, erros, sugestoes)
    elif tipo == "PYTHON":
        _validar_python(codigo, erros, sugestoes)
    
    return len(erros) == 0, erros, sugestoes


def _validar_npc(codigo, erros, sugestoes):
    if "NPCHandler" not in codigo and "Npc" not in codigo and "npc" not in codigo.lower()[:200]:
        erros.append("NPC deve usar NPCHandler ou similar")
        sugestoes.append("Adicione NPCHandler:new()")
    
    if "sendTextMessage" in codigo:
        erros.append("NPC nao deve usar sendTextMessage (use selfSay)")
        sugestoes.append("Troque sendTextMessage por selfSay")
    
    if "selfSay" in codigo:
        sugestoes.append("NPC usa selfSay para falar")
    
    # Verifica se tem dialogues/basic structure
    if not any(f in codigo for f in ["onGreet", "onSay", "onSell", "dialogo", "dialog"]):
        sugestoes.append("Considere adicionar onGreet para saudacao")


def _validar_shc(codigo, erros, sugestoes):
    habs = re.findall(r'HABILIDADES\[\d+\]', codigo)
    if not habs:
        erros.append("Nenhum HABILIDADES[ID] encontrado")
        sugestoes.append("Use o formato HABILIDADES[ID] = {")
    
    if "efeitoConfig" not in codigo:
        erros.append("Falta efeitoConfig na habilidade")
        sugestoes.append("Adicione efeitoConfig = { tipo, dano, percentual, elemento }")
    
    if "danoMinimo" in codigo or "danoMaximo" in codigo:
        erros.append("Use dano + percentual em vez de danoMinimo/danoMaximo")
        sugestoes.append("Troque por dano = 1.0, percentual = 0.5")
    
    if "postura" in codigo:
        if not re.search(r'\[\d+\]', codigo[codigo.find("postura"):codigo.find("postura")+200]):
            sugestoes.append("Postura usa colchetes numericos: [1], [2], [3]")


def _validar_otui(codigo, erros, sugestoes):
    if "<" not in codigo or ">" not in codigo:
        sugestoes.append("Formato OTUI: Nome < ParentWidget")
    
    if "anchors" not in codigo.lower():
        sugestoes.append("Use anchors.top / anchors.left para posicionamento")


def _validar_sql(codigo, erros, sugestoes):
    if "CREATE TABLE" not in codigo.upper() and "INSERT" not in codigo.upper():
        sugestoes.append("Comandos SQL comuns: CREATE TABLE, SELECT, INSERT")


def _validar_lua(codigo, erros, sugestoes):
    # Verifica syntax basica
    if codigo.count("{") != codigo.count("}"):
        erros.append("Chaves desbalanceadas: { e } nao conferem")
    
    if codigo.count("[") != codigo.count("]"):
        erros.append("Colchetes desbalanceados: [ e ] nao conferem")
    
    if "local " in codigo and codigo.count("local ") > 10:
        sugestoes.append("Muitas variaveis locais, considere organizar")


def _validar_python(codigo, erros, sugestoes):
    if codigo.count("(") != codigo.count(")"):
        erros.append("Parenteses desbalanceados")
    
    if "import " not in codigo:
        sugestoes.append("Nenhum import encontrado")
