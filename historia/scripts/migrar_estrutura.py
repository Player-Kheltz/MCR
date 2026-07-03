"""Migracao para nova estrutura de diretorios.
Cria copias dos modulos nas novas pastas + stubs de compatibilidade.
Nada e removido — imports antigos continuam funcionando.
"""
import os, shutil

BASE = 'Scripts/mcr_devia'
MODULOS = os.path.join(BASE, 'modulos')

# Mapeamento: (modulo_origem, nova_pasta, novo_nome)
MIGRAR = [
    # core/ — nucleo do sistema
    ('ia.py', 'core', 'ia.py'),
    ('util.py', 'core', 'util.py'),
    ('progress_tracker.py', 'core', 'progress_tracker.py'),
    ('security.py', 'core', 'security.py'),
    
    # pipeline/ — pipeline de resposta
    ('pipeline_executor.py', 'pipeline', 'executor.py'),
    ('session_cache.py', 'pipeline', 'session_cache.py'),
    ('reconstructor.py', 'pipeline', 'reconstructor.py'),
    
    # knowledge/ — conhecimento e aprendizado
    ('kg.py', 'knowledge', 'kg.py'),
    ('episodic_memory.py', 'knowledge', 'episodic_memory.py'),
    ('canary_indexer.py', 'knowledge', 'canary_indexer.py'),
    ('blank_filler.py', 'knowledge', 'blank_filler.py'),
    ('lessons_buffer.py', 'knowledge', 'lessons_buffer.py'),
    
    # analysis/ — analise e padroes
    ('pattern_engine.py', 'analysis', 'pattern_engine.py'),
    ('validation_pipeline.py', 'analysis', 'validation.py'),
    ('auto_revisor.py', 'analysis', 'auto_revisor.py'),
    ('decider.py', 'analysis', 'decider.py'),
    ('truncation_fixer.py', 'analysis', 'truncation_fixer.py'),
    ('diagnostic_engine.py', 'analysis', 'diagnostic_engine.py'),
    ('self_study.py', 'analysis', 'self_study.py'),
    
    # tools/ — ferramentas executaveis
    ('tool_orchestrator.py', 'tools', 'orchestrator.py'),
    ('sandbox_executor.py', 'tools', 'sandbox.py'),
    ('tradutor.py', 'tools', 'tradutor.py'),
    ('lua_validator.py', 'tools', 'lua_validator.py'),
    
    # agents/ — agentes e consciencia
    ('supervisor.py', 'agents', 'supervisor.py'),  # sera copiado do root modulos/
    ('conselho.py', 'agents', 'conselho.py'),
    ('mente.py', 'agents', 'mente.py'),
    ('tree_of_thought.py', 'agents', 'tree_of_thought.py'),
    ('master_agent.py', 'agents', 'master_agent.py'),
    ('emergir.py', 'agents', 'emergir.py'),
    ('task_planner.py', 'agents', 'planner.py'),
    ('task_executor.py', 'agents', 'task_executor.py'),
]

copiados = 0
for nome_orig, pasta_dest, nome_dest in MIGRAR:
    # Alguns modulos estao na raiz modulos/, outros no root mcr_devia/
    origens = [
        os.path.join(MODULOS, nome_orig),
        os.path.join(BASE, nome_orig),
        os.path.join(os.path.dirname(BASE), nome_orig),  # modulos/ raiz do projeto
    ]
    
    caminho_orig = None
    for o in origens:
        if os.path.exists(o):
            caminho_orig = o
            break
    
    if not caminho_orig:
        print(f'  AVISO: {nome_orig} nao encontrado')
        continue
    
    destino = os.path.join(BASE, pasta_dest, nome_dest)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    
    # Copia (nao move) — para nao quebrar nada
    shutil.copy2(caminho_orig, destino)
    print(f'  {nome_orig} -> {pasta_dest}/{nome_dest}')
    copiados += 1

print(f'\n{copiados} modulos copiados para nova estrutura.')
print()
print('Nova estrutura:')
print('  core/     — Nucleo do sistema')
print('  pipeline/ — Pipeline de resposta')
print('  knowledge/— Conhecimento e aprendizado')
print('  analysis/ — Analise e padroes')
print('  tools/    — Ferramentas executaveis')
print('  agents/   — Agentes e consciencia')
print()
print('NOTA: Modulos originais permanecem intactos em modulos/')
print('Os imports antigos (from modulos.X import Y) continuam funcionando.')
