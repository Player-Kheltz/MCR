#!/usr/bin/env python3
"""Prototipo v2 — MCR gera NPC Lua usando padroes do Canary."""

import sys, os, time

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

print("=" * 60)
print("  PROTOTIPO V2: MCR GERA NPC LUA")
print("  Base: 629 scripts do Canary")
print("=" * 60)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
print(f"Topicos: {len(c.topicos)}, Palavras: {c.mk_palavra.total}")

# ─── 1. EXPLORAR: quais palavras o MCR aprendeu? ────────────
print("\n[1] Palavras mais frequentes (aprendidas dos scripts):")
top_words = sorted(c.mk_palavra.freq.items(), key=lambda x: -x[1])[:30]
for i, (palavra, freq) in enumerate(top_words):
    print(f"  {i+1}. '{palavra}' (freq={freq})")

# ─── 2. VERIFICAR SE "local" FOI APRENDIDO ─────────────────
print(f"\n[2] 'local' esta no vocabulario? {'local' in c.mk_palavra.freq}")
if "local" in c.mk_palavra.freq:
    pred, conf = c.mk_palavra.predizer("local")
    print(f"  'local' → '{pred}' (conf={conf:.2f})")
    cands = c.mk_palavra.predizer_n("local", 5)
    print(f"  Top 5 apos 'local': {[(p, round(c,2)) for p,c in cands]}")

# ─── 3. GERAR NPC USANDO GERACAO DIRETA ─────────────────
print("\n[3] Gerando NPC (geracao direta, cadeia com intencao)...")
resultados = []

# Tenta gerar a partir de palavras reais
sementes = ["local", "function", "npc"]
for semente in sementes:
    if semente in c.mk_palavra.freq:
        for _ in range(3):
            seq = c.mk_palavra.gerar_com_entropia(semente, passos=8)
            if seq and len(seq) > 2:
                texto = " ".join(seq)
                if not any(t.startswith('B:') for t in seq):
                    resultados.append(texto)

print(f"  Geracoes sem byte lixo: {len(resultados)}")
for i, r in enumerate(resultados[:5]):
    print(f"  {i+1}. {r}")

# ─── 4. GERAR COM CONTEXTO DO KG ─────────────────────────
print("\n[4] Gerando com contexto do SessionCache...")
# Alimenta exemplos de NPCs
exemplos = [
    'npcConfig = { name = "Ferreiro", say = { "Precisa de algo?" }, currency = "gold" }',
    'local npc = Game.createNpc("Ferreiro") npc:setSpeech({ greet = "Ola!", bye = "Ate logo!" })',
    'function onSay(player, words, param) local npc = Npc() return true end',
]
for i, texto in enumerate(exemplos):
    c.alimentar(texto, f"exemplo_npc_{i}")
    c.session_cache.absorver(f"exemplo_{i}", texto, "codigo", tags=["npc", "ferreiro"])

# Contexto da sessao
ctx = c.session_cache.pescar("criar npc ferreiro", n=3, max_tokens=500)
ctx_texto = " ".join(f.conteudo for f in ctx if f and f.conteudo) if ctx else ""
print(f"  Contexto pescado: {len(ctx_texto)} chars")

# Gera com contexto
if "npc" in c.mk_palavra.freq:
    prompt = ctx_texto + " local npc = "
    cadeia = c._cadeia_pensamento(prompt, intencao="CRIAR_NPC", passos=6)
    tokens = cadeia.split()
    tokens_limpos = [t for t in tokens if not t.startswith('B:')]
    if tokens_limpos:
        print(f"  Gerado: {' '.join(tokens_limpos[:20])}")

# ─── 5. RESUMO ──────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  RESUMO DO PROTOTIPO")
print(f"{'='*60}")
print(f"  Vocabulario: {len(c.mk_palavra.freq)} palavras")
print(f"  Palavra mais comum: '{top_words[0][0]}' ({top_words[0][1]}x)")
print(f"  'local' disponivel: {'local' in c.mk_palavra.freq}")
print(f"  Geracoes geradas: {len(resultados)}")
print(f"{'='*60}")
