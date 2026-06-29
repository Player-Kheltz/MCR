"""Limpeza do Sandbox: move versoes antigas, copias e lixo para Legado/.
Preserva: .mcr_devia/, thought_dashboard.html, _teste_*.py, output/
"""
import os, sys, shutil

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__)))
LEGADO = os.path.join(SANDBOX, 'Legado')

# Pastas de projetos gerados para mover
PASTAS_PARA_MOVER = [
    'simulador_jogos_tabuleiro_online',
    'jogo_python_tkinter',
    'app_gerenciamento_financeiro',
    'projeto_api_rest',
    'relatorio_canary_novidades',
    'projeto_jogo_python',
    'Temp',
]

# Arquivos para mover (versoes antigas, copias, lixo)
ARQUIVOS_PARA_MOVER = [
    # Multiplas versoes de crews
    'mcr_crew.py', 'mcr_crew_v7.py', 'mcr_crew_v8.py', 'mcr_crew_v9.py',
    'mcr_crew_v10.py', 'mcr_crew_v11.py', 'mcr_crew_v13.py',
    'mcr_crew_v14.py', 'mcr_crew_v15.py',
    # Multiplas versoes de SHC
    'gerador_shc_v2.py', 'gerador_shc_v3.py', 'gerador_shc_v4.py',
    'gerador_shc_v6.py',  # v5 nao existe, v1 e o original
    'gerar_habilidades_shc.py', 'regenerate_abilities.py',
    # Copias standalone
    'context_crew.py', 'mcr_devia.py', 'mcr_chat.py',
    'gerador_npc_otbr.py',
    # Scripts avulsos
    'web_learn.py', 'estudo_loop.py', 'auto_fixer_v12.py',
    'integrar_cr_tudo.py',
    # Geradores diversos
    'gerador_npc_otbr.py',
    'web_learn.py',
]

def mover(path, destino_sub):
    """Move arquivo/pasta para Legado/{destino_sub}/."""
    if not os.path.exists(path):
        return
    dest_dir = os.path.join(LEGADO, destino_sub)
    os.makedirs(dest_dir, exist_ok=True)
    nome = os.path.basename(path)
    dest = os.path.join(dest_dir, nome)
    if os.path.exists(dest):
        print(f'  [PULOU] {nome} ja existe em {dest_dir}')
        return
    shutil.move(path, dest)
    print(f'  [MOVido] {nome} -> Legado/{destino_sub}/')

print('=== Limpeza do Sandbox ===')
print()

# 1. Move pastas de projetos gerados
print('1. Pastas de projetos gerados:')
for pasta in PASTAS_PARA_MOVER:
    mover(os.path.join(SANDBOX, pasta), 'projetos_gerados')

# 2. Move scans de codigo (arquivos grandes gerados por ferramentas)
print()
print('2. Arquivos de scan e dados gerados:')
for fname in os.listdir(SANDBOX):
    if fname.endswith('.json') and not fname.startswith('.') and fname not in ('canary_index.json',):
        mover(os.path.join(SANDBOX, fname), 'scans_e_dados')
    # Gera arquivos .py temporarios de scans
    if fname.endswith('.py') and ('scan' in fname.lower() or 'diagnostico' in fname.lower() or 'check' in fname.lower()):
        if fname not in ['_migrar_kg.py', '_teste_self_study.py', '_teste_api_clean.py', '_teste_api_completo.py',
                         '_teste_api.py', '_diag_emergir_v3.py', '_diagnostico_emergir_v3.py',
                         '_rodar_sse.py', '_ver_self_study.py']:
            mover(os.path.join(SANDBOX, fname), 'scans_e_dados')

# 3. Move versoes antigas
print()
print('3. Versoes antigas e copias:')
for fname in ARQUIVOS_PARA_MOVER:
    mover(os.path.join(SANDBOX, fname), 'versoes_antigas')

# 4. Move pastas de projetos de jogos gerados (se ainda nao foram movidos)
print()
print('4. Pastas de projetos restantes:')
for item in os.listdir(SANDBOX):
    item_path = os.path.join(SANDBOX, item)
    if not os.path.isdir(item_path):
        continue
    # Ignora pastas do sistema e importantes
    if item.startswith('.') or item in ('Legado', 'output', '.mcr_devia', 'temp'):
        continue
    # Se tem run.bat dentro, e projeto gerado
    if os.path.exists(os.path.join(item_path, 'run.bat')):
        mover(item_path, 'projetos_gerados')

print()
print('Limpeza concluida!')
print(f'Verifique sandbox/Legado/ para confirmar.')
