#!/usr/bin/env python3
"""MCR estuda LLM files autonomamente."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t0 = __import__('time').time()

print('=== MCR ESTUDANDO LLM ===', flush=True)
print(f'[{__import__("time").time()-t0:.1f}s] Iniciando...', flush=True)

# 1. MCRBridge descobre o que existe
from modulos.MCR import MCRBridge
bridge = MCRBridge()
bridge.descobrir()
stats = bridge.stats()
print(f'[{__import__("time").time()-t0:.1f}s] Bridge: {stats["modulos"]} modulos, {stats["comandos"]} comandos, {stats.get("ferramentas",0)} ferramentas', flush=True)

# 2. MCRPreCache estuda GGUF (modelos LLM)
from modulos.MCR import MCRPreCache
cache = MCRPreCache()

# Procura arquivos .gguf no projeto
ggufs = []
base_dir = os.path.join(os.path.dirname(__file__), '..')
for root, dirs, files in os.walk(base_dir):
    # Pula diretorios grandes
    skip_dirs = ['.git', 'vcpkg', 'node_modules', '__pycache__', 'build', '.opencode']
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for f in files:
        if f.endswith('.gguf'):
            ggufs.append(os.path.join(root, f))
            if len(ggufs) >= 3:
                break
    if len(ggufs) >= 3:
        break

print(f'[{__import__("time").time()-t0:.1f}s] Encontrados {len(ggufs)} .gguf', flush=True)

for g in ggufs:
    print(f'  Estudando: {os.path.relpath(g, base_dir)} ({os.path.getsize(g)/1024/1024:.0f} MB)', flush=True)
    try:
        n = cache.estudar(g, max_tokens_kg=30)
        print(f'    -> {n} tokens aprendidos no KG', flush=True)
    except Exception as e:
        print(f'    -> Erro: {e}', flush=True)

# 3. MCRFuel abastece com o que aprendeu
from modulos.MCR import MCRFuel
kg_used = cache.kg if cache.kg else None
fuel = MCRFuel(kg=kg_used, bridge=bridge)
n_fuel = fuel.abastecer_se_precisar(min_uteis=100)
print(f'[{__import__("time").time()-t0:.1f}s] Fuel: {"abasteceu" if n_fuel else "ja tem dados"}', flush=True)

# 4. Verifica lessons sobre LLM/tokenizador
if kg_used:
    licoes = kg_used._get_licoes()
    llm_lessons = [l for l in licoes if 'llm' in l.get('ctx','').lower() or 'token' in l.get('ctx','').lower()]
    print(f'[{__import__("time").time()-t0:.1f}s] Lessons LLM/token: {len(llm_lessons)}', flush=True)
    print(f'[{__import__("time").time()-t0:.1f}s] KG total: {len(licoes)} lessons', flush=True)
    if llm_lessons:
        for l in llm_lessons[:5]:
            print(f'  -> ctx={l.get("ctx","?")} sol={l.get("solucao","")[:60]}', flush=True)

# 5. Relatorio final
print(f'[{__import__("time").time()-t0:.1f}s] MCR concluiu o estudo LLM.', flush=True)
