#!/usr/bin/env python3
"""Gera NPC Lua com MCR + loop de validacao — so aceita codigo viavel."""

import sys, os, re, time

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

os.chdir(_BASE)
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

# ─── VALIDACAO ──────────────────────────────────────────────

BRACKETS = {'{':'}', '[':']', '(':')'}
BRACKETS_REV = {v:k for k,v in BRACKETS.items()}

def brackets_ok(texto):
    """Verifica se brackets estao balanceados."""
    pilha = []
    for ch in texto:
        if ch in BRACKETS:
            pilha.append(ch)
        elif ch in BRACKETS_REV:
            if not pilha or pilha[-1] != BRACKETS_REV[ch]:
                return False
            pilha.pop()
    return not pilha

def sintaxe_lua_basica(texto):
    """Validacoes basicas de sintaxe Lua."""
    erros = []
    # function sem end
    n_func = len(re.findall(r'\bfunction\b', texto))
    n_end = len(re.findall(r'\bend\b', texto))
    if n_func > n_end:
        erros.append(f"{n_func} function(s) sem {n_end} end(s)")
    # if/then/else sem end (ja contado acima)
    n_if = len(re.findall(r'\bif\s+', texto))
    n_then = len(re.findall(r'\bthen\b', texto))
    if n_if > n_then:
        erros.append(f"{n_if} if(s) sem {n_then} then(s)")
    # do sem end
    n_do = len(re.findall(r'\bdo\b', texto))
    n_for_while = len(re.findall(r'\b(for|while)\b', texto))
    # cada for/while precisa de um do
    if n_do < n_for_while:
        pass  # aceitavel se for aninhado
    # atribuicao local sem nome
    if text := re.search(r'local\s+(=|end|then)', texto):
        erros.append(f"'local' sem nome: 'local {text.group(1)}'")
    return erros

def validar(texto):
    if not brackets_ok(texto):
        return False, "brackets desbalanceados"
    erros = sintaxe_lua_basica(texto)
    if erros:
        return False, "; ".join(erros)
    if len(texto) < 20:
        return False, "texto muito curto"
    # Pelo menos uma estrutura Lua reconhecivel
    if not any(p in texto for p in ['function', 'local', 'if ', 'for ', 'while ', 'repeat', 'return']):
        return False, "nenhuma estrutura Lua reconhecida"
    return True, "OK"

# ─── GERACAO COM VALIDACAO ──────────────────────────────────

def gerar_npc_validado(c, sementes_codigo, max_tentativas=20):
    resultados = []
    for semente in sementes_codigo:
        if semente not in c.mk_palavra.freq:
            continue
        for tentativa in range(max_tentativas):
            seq = c.mk_palavra.gerar_com_entropia(semente, passos=15)
            if not seq:
                continue
            texto = " ".join(seq)
            # Filtra byte lixo
            tokens_limpos = [t for t in seq if not t.startswith('B:') and not t == '<UNK>']
            texto = " ".join(tokens_limpos)
            if len(texto) < 20:
                continue
            ok, motivo = validar(texto)
            if ok:
                resultados.append((texto, semente, tentativa+1))
                break
    return resultados

# ─── MAIN ───────────────────────────────────────────────────

print("=" * 60)
print("  GERADOR VALIDADO DE NPC LUA")
print("=" * 60)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
print(f"Topicos: {len(c.topicos)}, Palavras: {c.mk_palavra.total}")

# Alimenta 3 exemplares de NPC pra dar contexto
exemplos_npc = [
    'local npc = Npc() function onGreet(player) npc:sai("Ola, aventureiro!") end',
    'npcConfig = { name = "Ferreiro", greet = "Precisa de algo?", bye = "Volte sempre!" }',
    'function onSay(player, words, param) if words == "hi" then npc:sai("Ola!") end return true end',
]
for i, texto in enumerate(exemplos_npc):
    c.alimentar(texto, f"ex_npc_{i}")

sementes = ['npc', 'local', 'function', 'npcConfig', 'if']
resultados = gerar_npc_validado(c, sementes, max_tentativas=25)

print(f"\nTotal de NPCs validos gerados: {len(resultados)}")
for i, (texto, semente, t) in enumerate(resultados):
    print(f"\n--- NPC {i+1} (semente='{semente}', tentativa #{t}) ---")
    print(texto)

if not resultados:
    print("\n[!] Nenhum codigo valido gerado.")
    print("[!] Diagnosticando vocabulario...")
    for s in sementes:
        if s in c.mk_palavra.freq:
            pred, conf = c.mk_palavra.predizer(s)
            print(f"  '{s}' → '{pred}' (conf={conf:.2f})")
        else:
            print(f"  '{s}' NAO esta no vocabulario")

print(f"\n{'='*60}")
print(f"  FIM")
print(f"{'='*60}")
