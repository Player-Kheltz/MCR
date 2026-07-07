#!/usr/bin/env python3
"""Prototipo: MCR gera NPC Lua usando padroes aprendidos do Projeto MCR."""

import sys, os, time, json, re

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

print("=" * 60)
print("  PROTOTIPO: MCR GERA NPC LUA")
print("  Usando padroes aprendidos de 26.732 arquivos do Projeto MCR")
print("=" * 60)

# Carrega o cerebro alimentado
c = CerebroAGI()
cerebro_path = os.path.join(CACHE_DIR, "cerebro.json")
c.carregar(cerebro_path)
print(f"Conhecimento: {len(c.topicos)} topicos, {c.mk_palavra.total} transicoes palavra")

# ─── 1. SUPERVISOR: classifica intencao ──────────────────────
intent = c.supervisor.classificar("criar um NPC ferreiro")
print(f"\n[1] Intencao: {intent}")

# ─── 2. APRENDE PADRAO DE ARQUIVOS EXISTENTES ──────────────
print("\n[2] Aprendendo padrao de NPCs Lua existentes...")
c.genesis.aprender_de_arquivos(r"E:\Projeto MCR\OTClient\modules", max_arquivos=30)

# ─── 3. GERA USANDO MARKOV COM TEMPERATURA ──────────────────
print("\n[3] Gerando NPC Ferreiro (temperatura entropica)...")

seeds = [
    "local npc = {",
    "npcConfig = {",
    "local ferreiro = {",
]

resultados = []
for seed in seeds:
    seq = c.mk_byte.gerar_com_entropia("B:6C", passos=30)  # 'l' de 'local'
    if len(seq) >= 5:
        texto_bytes = bytes(int(t.split(':')[1], 16) for t in seq if t.startswith('B:'))
        try:
            texto = texto_bytes.decode('utf-8', errors='replace')
            if len(texto) > 10:
                resultados.append(texto)
        except: pass

print(f"\n[4] Resultados ({len(resultados)} fragmentos):")
for i, r in enumerate(resultados[:3]):
    print(f"\n--- Fragmento {i+1} ---")
    print(r[:200])

# ─── 4. CADEIA DE PENSAMENTO GUIADA ────────────────────────
print("\n[5] Gerando com cadeia de pensamento (intencao=CRIAR_NPC)...")
for prompt in ["local npc = {} function onSay", "criar npc ferreiro itens", "npc ferreiro dialogos"]:
    resultado = c._cadeia_pensamento(prompt, intencao="CRIAR_NPC", passos=5)
    if resultado and resultado != prompt:
        print(f"\n  Prompt: {prompt}")
        print(f"  Gerado: {resultado[:150]}")

# ─── 5. PIPELINE COMPLETA ───────────────────────────────────
print("\n[6] Pipeline completa:")
try:
    from nichos.tibia.mcr_pipeline import MCRPipeline
    pipe = MCRPipeline(c)
    
    # Alimenta exemplos de NPCs reais
    for i, texto in enumerate([
        'npcConfig = { name = "Ferreiro", say = { "Precisa de algo?" } }',
        'local npc = Game.createNpc("Ferreiro") npc:setSpeech({})',
        'function onSay(player, words, param) return true end',
    ]):
        c.alimentar(texto, f"npc_exemplo_{i}")
    
    resultado = pipe.executar("criar um npc ferreiro com itens e dialogos", max_passos=8)
    print(f"\n  Resultado: {resultado[:300]}")
except Exception as e:
    print(f"  Pipeline: {e}")

print(f"\n{'='*60}")
print(f"  FIM DO PROTOTIPO")
print(f"  O MCR gerou fragmentos baseados em 26.732 arquivos de codigo.")
print(f"  Os resultados sao brutos — refinamento exige loop de validacao.")
print(f"{'='*60}")
