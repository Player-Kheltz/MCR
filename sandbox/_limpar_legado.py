"""Move arquivos do sistema V12 (legado) para /Legado.

Organiza o que e passado vs o que e atual.
Nada e deletado — tudo vai para Legado/.
"""
import os, shutil, sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LEGADO = os.path.join(BASE, 'Legado')

def move_file(origem, destino_sub):
    """Move um arquivo para Legado/destino_sub/, criando pastas se necessario."""
    dest_dir = os.path.join(LEGADO, destino_sub)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(origem))
    if os.path.exists(dest_path):
        print(f"  JA EXISTE: {origem} -> {dest_path}")
        return False
    shutil.move(origem, dest_path)
    print(f"  Moveu: {origem} -> {dest_path}")
    return True

def move_dir(origem, destino_sub):
    """Move um diretorio inteiro para Legado/."""
    dest_dir = os.path.join(LEGADO, destino_sub)
    if os.path.exists(dest_dir):
        print(f"  JA EXISTE: {origem}")
        return False
    shutil.move(origem, dest_dir)
    print(f"  Moveu: {origem} -> {dest_dir}")
    return True

print("=" * 60)
print("  LIMPEZA DE LEGADO — Movendo arquivos V12 para /Legado")
print("=" * 60)
print()

total = 0

# 1. Scripts antigos da raiz
print("--- 1. Scripts V12 (raiz) ---")
scripts_v12 = [
    'mcr_agent.py', 'mcr_autobuild.py', 'mcr_autoconsciencia.py',
    'mcr_loop.py', 'mcr_observatory_v2.py', 'mcr_ultimate.py',
    'crew_pattern.py', 'diretorio_analyzer.py', 'validador_genero.py',
    'pista_a.py', 'pista_b.py',
]
for nome in scripts_v12:
    path = os.path.join(BASE, 'Scripts', 'mcr_devia', nome)
    if os.path.exists(path):
        move_file(path, 'scripts_antigos')
        total += 1

# 2. Modulos antigos
print("\n--- 2. Modulos V12 (substituidos) ---")
modulos_v12 = [
    'orquestrador.py', 'supervisor.py',
    'context_enricher.py', 'dashboard.py',
    'super_fragmentador.py', 'context_reinforcer.py',
    'toolkit.py', 'memoria.py', 'pipeline.py',
    'fragmentador.py', 'diagnostico.py',
    'compilador.py', 'serve.py',
]
for nome in modulos_v12:
    path = os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos', nome)
    if os.path.exists(path):
        move_file(path, 'modulos_antigos')
        total += 1

# 3. NPCs antigos (stubs com sintaxe invalida)
print("\n--- 3. NPCs antigos (stubs V12) ---")
npc_dir = os.path.join(BASE, 'sandbox', 'npcs_gerados')

# Prefixos de NPCs gerados pelo sistema V12 (stubs < 500 bytes)
prefixos_antigos = ['devia_', 'ult_', 'v12_', 'v13_', 'v15_', 'v18_', 'corrida_', 'cristal_tentativa_']
# Nomes especificos de stubs
nomes_stubs = [
    'item_espada.lua', 'item_espadalonga.lua',
    'monster_goblin.lua', 'monster_goblinselvagem.lua',
    'spell_boladefogo.lua',
    'quest_aventura.lua', 'quest_aventurainicial.lua',
    'npc_ferreiro.lua',
]

if os.path.exists(npc_dir):
    for nome in os.listdir(npc_dir):
        if not nome.endswith('.lua'):
            continue
        # Verifica se comeca com prefixo antigo
        if any(nome.startswith(p) for p in prefixos_antigos):
            move_file(os.path.join(npc_dir, nome), 'npcs_antigos')
            total += 1
        # Verifica se e nome conhecido de stub
        elif nome in nomes_stubs:
            path = os.path.join(npc_dir, nome)
            if os.path.getsize(path) < 800:  # Stub mesmo
                move_file(path, 'npcs_antigos')
                total += 1

# 4. Relatorios antigos
print("\n--- 4. Relatorios antigos ---")
relatorios = [
    'RELATORIO_FINAL.md',
]
for nome in relatorios:
    path = os.path.join(BASE, 'sandbox', nome)
    if os.path.exists(path):
        move_file(path, 'relatorios_antigos')
        total += 1

# 5. Planos antigos (docs)
print("\n--- 5. Planos antigos (docs) ---")
planos_antigos = [
    'ARQUITETURA_UNIVERSAL.md', 'PLANO_IMPLEMENTACAO_UNIVERSAL.md',
    'PLANO_ACAO_CONSOLIDADO.md', 'PLANO_REFATORACAO.md',
    'PLANO_TESTES_SISTEMA.md', 'PLANO_TESTES_UNIVERSAL.md',
    'PLANO_APRENDIZADO_MASSIVO.md', 'PLANO_CONTEXT_REINFORCER.md',
    'CHECKPOINT_SESSAO_2026-06-25.md', 'CHECKPOINT_SESSAO_2026-06-26.md',
    'COMPARATIVO_CLOUD_vs_MCRDEVIA.md', 'COMPARATIVO_FINAL_POS_MELHORIAS.md',
    'FLUXOGRAMA_MCR_DEVIA.md', 'MCR_DEVIA_DOCUMENTACAO_REAL.md',
    'OBSERVACOES_FINAIS.md', 'RELATORIO_FINAL_COMPARATIVO.md',
]
docs_dir = os.path.join(BASE, 'docs')
for nome in planos_antigos:
    path = os.path.join(docs_dir, nome)
    if os.path.exists(path):
        move_file(path, 'planos_antigos')
        total += 1

# 6. Lessons antigas (lessons de sessoes passadas)
print("\n--- 6. Lessons antigas ---")
lessons_antigas = [
    '2026-06-25-arquitetura-final-meta-crew-v12.md',
    '2026-06-25-autofixer-v12-sandbox.md',
    '2026-06-25-scanner-encoding-fixes.md',
]
lessons_dir = os.path.join(docs_dir, 'lessons')
for nome in lessons_antigas:
    path = os.path.join(lessons_dir, nome)
    if os.path.exists(path):
        move_file(path, 'lessons_antigas')
        total += 1

# 7. Rules antigas
print("\n--- 7. Rules antigas ---")
rules_antigas = ['equipe.md']
rules_dir = os.path.join(docs_dir, 'rules')
for nome in rules_antigas:
    path = os.path.join(rules_dir, nome)
    if os.path.exists(path):
        move_file(path, 'rules_antigas')
        total += 1

print(f"\n{'=' * 60}")
print(f"  Total: {total} arquivos movidos para /Legado")
print(f"  Nada foi deletado — tudo preservado em /Legado")
print(f"{'=' * 60}")
