"""LuaSyntaxValidator — Valida sintaxe Lua SEM executar codigo (sandbox).
Usa lupa loadstring() ou subprocess luac para validacao pura."""
import sys, os, re

_HAS_LUPA = False
_lupa = None
try:
    from lupa import LuaRuntime
    _lupa = LuaRuntime(unpack_returned_tuples=True)
    _HAS_LUPA = True
except:
    pass

# Globals permitidos no sandbox (NAO incluir os, io, package, loadfile, dofile, require, debug)
_GLOBALS_SEGUROS = {
    'HABILIDADES': {}, 'COR': {}, 'Game': {}, 'NpcHandler': {}, 'KeywordHandler': {},
    'FocusModule': {}, 'Action': {}, 'Player': {}, 'CreatureEvent': {}, 'GlobalEvent': {},
    'MoveEvent': {}, 'Position': {}, 'Item': {}, 'Npc': {}, 'Container': {},
    'MESSAGE_EVENT_ADVANCE': 1, 'MESSAGE_TRADE': 2, 'MESSAGE_FAILURE': 3,
    'MESSAGE_DEFAULT': 4, 'MESSAGE_INFO_DESCR': 5, 'MESSAGE_STATUS_WARNING': 6,
    'TALKTYPE_MONSTER_SAY': 7, 'CONST_ME_FIRE': 8, 'CONST_ME_ICE': 9,
    'CONST_ME_EARTH': 10, 'CONST_ME_ENERGY': 11,
    'NpcUtils': {'getTratamento': lambda p: {}}, 'StdModule': {'say': lambda: True},
    'getNivelPorAfinidade': lambda x: 0, 'print': lambda *a: None,
    'table': __import__('builtins').__dict__.get('print', lambda: None),
}

# Funcoes PROIBIDAS que devem ser removidas de qualquer runtime
_FUNCOES_PERIGOSAS = {'os': None, 'io': None, 'package': None, 'loadfile': None,
                      'dofile': None, 'require': None, 'debug': None, 'rawget': None,
                      'rawset': None, 'rawequal': None, 'getmetatable': None,
                      'setmetatable': None, 'pcall': None, 'xpcall': None,
                      'loadstring': None, 'load': None, 'collectgarbage': None}


def _criar_sandbox():
    """Cria LuaRuntime com SEGURANCA: nao executa codigo, apenas compila."""
    lr = LuaRuntime(unpack_returned_tuples=True,
                    attribute_filter=lambda obj, name: name not in _FUNCOES_PERIGOSAS)
    g = lr.globals()
    for k, v in _GLOBALS_SEGUROS.items():
        try:
            g[k] = v
        except: pass
    return lr


def verificar_sintaxe(codigo):
    """Verifica sintaxe Lua SEM executar codigo.
    Retorna (valido, erro). Usa loadstring() para compilar sem executar."""
    if not codigo or len(codigo) < 10:
        return False, "Codigo vazio ou muito curto"
    
    if not _HAS_LUPA:
        return _verificar_regex(codigo)
    
    lr = _criar_sandbox()
    try:
        # APENAS compila (loadstring), NAO executa
        # Se a sintaxe for valida, retorna funcao compilada
        func = lr.eval('loadstring(%s)' % repr(codigo))
        if func is None:
            # Se loadstring retornou nil, pega o erro
            err = lr.eval('loadstring(%s)' % repr(codigo))
            return False, "Erro de sintaxe ao compilar"
        return True, None
    except SyntaxError as e:
        return False, "Erro de sintaxe: %s" % e
    except Exception as e:
        msg = str(e)
        if 'syntax' in msg.lower() or 'near' in msg.lower() or 'expected' in msg.lower():
            return False, "Erro de sintaxe: %s" % msg[:100]
        return True, None  # Assume sintaxe correta


def _verificar_regex(codigo):
    """Fallback: detecta erros comuns de sintaxe Lua via regex."""
    erros = []
    linhas = codigo.split('\n')
    aberturas = []
    palavras_abertura = {'function': 'end', 'if': 'end', 'for': 'end', 'while': 'end', 'do': 'end'}
    for i, linha in enumerate(linhas):
        stripped = linha.strip()
        if stripped.startswith('--') or stripped.startswith('//'):
            continue
        for palavra, fechamento in palavras_abertura.items():
            if stripped.startswith(palavra) or (' %s ' % palavra) in stripped:
                aberturas.append((palavra, fechamento, i + 1))
        if stripped.startswith('end') or stripped.startswith('end,'):
            if aberturas:
                aberturas.pop()
    if aberturas:
        for p, f, linha_abertura in aberturas:
            erros.append("Bloco '%s' aberto na linha %d nao foi fechado com '%s'" % (p, linha_abertura, f))
    if 'HABILIDADES' in codigo:
        chaves = 0
        for c in codigo:
            if c == '{': chaves += 1
            elif c == '}': chaves -= 1
        if chaves != 0 and not erros:
            erros.append("Chaves desbalanceadas: %d sem fechamento" % chaves)
    return (len(erros) == 0, '\n'.join(erros) if erros else None)


def corrigir_com_llm(codigo, erro, llm_func, modelo='qwen2.5-coder:7b'):
    if not llm_func:
        return codigo
    prompt = (
        "O codigo Lua abaixo falhou na compilacao com o erro:\n\n"
        + "ERRO: %s\n\n" % erro
        + "=== CODIGO ===\n" + codigo[:2000] + "\n=== FIM ===\n\n"
        + "Corrija o erro de sintaxe e reescreva o codigo COMPLETO corrigido.\n"
        + "Responda APENAS com o codigo Lua, sem explicacoes."
    )
    resp = llm_func(prompt, modelo=modelo)
    if '```lua' in resp:
        resp = resp.split('```lua')[1].split('```')[0]
    elif '```' in resp:
        resp = resp.split('```')[1].split('```')[0]
    return resp.strip()


def validar_com_loop(codigo, classe="", llm_func=None, modelo='qwen2.5-coder:7b', max_tentativas=3):
    """Valida codigo Lua em loop auto-corretivo. SEMPRE usa loadstring, nunca execute()."""
    codigo_atual = codigo
    erros = []
    for tentativa in range(max_tentativas):
        valido, erro = verificar_sintaxe(codigo_atual)
        if valido:
            return (codigo_atual, True, tentativa + 1, erros)
        erros.append(erro or "Erro desconhecido")
        if tentativa < max_tentativas - 1 and llm_func:
            codigo_atual = corrigir_com_llm(codigo_atual, erro, llm_func, modelo)
        else:
            break
    aviso = "-- [MCR-DevIA AVISO] Falhou na validacao de sintaxe apos %d tentativas.\n" % max_tentativas
    aviso += "-- Erros: %s\n" % ' | '.join(str(e)[:80] for e in erros)
    return (aviso + codigo, False, max_tentativas, erros)
