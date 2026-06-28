#!/usr/bin/env python
"""Replace hardcoded COMANDOS_VALIDOS with dynamic version + case-insensitive paths."""
import re, os, json

path = r'E:\Projeto MCR\sandbox\mcr_auto_diagnostico.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the hardcoded COMANDOS_VALIDOS with dynamic version
old_set = """    # Comandos validos do MCR-DevIA
    COMANDOS_VALIDOS = {
        'build', 'patch', 'analisar', 'extract', 'review', 'gerar', 'lore',
        'perguntar', 'fast', 'ensinar', 'grep', 'read', 'edit', 'glob',
        'compilar', 'system', 'bugfinder', 'plan', 'debate', 'loop',
        'intencao', 'todo', 'task', 'question', 'conectar', 'estrategia',
        'builderx', 'system_scan', 'webfetch', 'proativo', 'revisar',
        'processar', 'status', 'web_learn', 'auto_diagnostico', 'auto_melhoria',
        'auditar', 'autoavaliar', 'autoconsciencia', 'auto_improve',
        'auto_reparo', 'observar', 'agente', 'chat', 'scriptbuilder',
        'ultimate', 'conhecimento', 'ambiente', 'learning_scan', 'melhorias',
        'supervisor',
        'taskkill', 'rm', 'write', 'read', 'edit', 'grep', 'glob', 'webfetch', 'question', 'skill', 'task', 'bash',  # Cloud tools
        'bugfix', 'feature', 'decisao', 'licao', 'comando', 'weblearn', 'sessao', 'api',  # KG categories
        'ddgs', 'youtube', 'searxng', 'google', 'utf8mb4', 'netstat',  # termos externos
        'sendCancelMessage', 'sendTextMessage',  # tibia protocol
        'in_progress', 'ultima_sessao', 'titulo', 'tarefa_andamento', 'decisoes', 'arquivos_alterados', 'proximos_passos',  # checkpoint fields
        'ConfirmModal', 'Modal', 'msgbox',  # UI components
        'rag_watcher', 'rag_indexer', 'doc_sync', 'validate_local',  # script names
    }"""

new_dynamic = """    # Comandos validos - DINAMICO (extrai do MCR-DevIA + KG + projeto)
    COMANDOS_VALIDOS = set()
    # 1. Comandos do MCR-DevIA (parseia elif cmd)
    try:
        with open(MCR_DEVIA_PATH, 'r', encoding='utf-8') as f_cmds:
            for linha in f_cmds:
                m = re.search(r"elif cmd == '([a-z_]+)'", linha)
                if m: COMANDOS_VALIDOS.add(m.group(1))
    except: pass
    # 2. Atalhos do sandbox
    for script in os.listdir(SANDBOX):
        nome = os.path.splitext(script)[0]
        if nome and not script.startswith(('_', '.')):
            COMANDOS_VALIDOS.add(nome)
    # 3. Categorias do KG
    try:
        with open(KG_PATH, 'r', encoding='utf-8') as f_kg:
            kg_data = json.load(f_kg)
        for l in kg_data.get('licoes', []):
            ctx = l.get('ctx', '')
            if ctx: COMANDOS_VALIDOS.add(ctx)
    except: pass
    # 4. Cloud tools e comandos de sistema
    COMANDOS_VALIDOS.update(['python', 'pip', 'git', 'cd', 'dir', 'echo',
        'cmd', 'powershell', 'opencode', 'ollama', 'taskkill', 'rm',
        'write', 'read', 'edit', 'grep', 'glob', 'webfetch', 'question',
        'skill', 'task', 'todowrite', 'bash', 'netstat', 'where'])"""

if old_set in content:
    content = content.replace(old_set, new_dynamic)
    print('1. COMANDOS_VALIDOS substituido por versao dinamica')
else:
    print('1. AVISO: old_set nao encontrado')
    # Try smaller match
    if 'taskkill' in content:
        print('   (conteudo com termos fixos encontrado, mas old_set nao bateu exato)')

# 2. Fix case-insensitive file comparison
# Change: arquivos_existentes.add(rp) -> arquivos_existentes.add(rp.lower())
content = content.replace(
    "arquivos_existentes.add(rp)",
    "arquivos_existentes.add(rp.lower())"
)
print('2. Path armazenado em lowercase')

# Change: if ref not in arquivos_existentes: -> if ref.lower() not in arquivos_existentes:
content = content.replace(
    "if ref not in arquivos_existentes:",
    "if ref.lower() not in arquivos_existentes:"
)
print('3. Comparacao case-insensitive')

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, path, 'exec')
    print('OK - sintaxe valida')
except SyntaxError as e:
    print(f'ERRO: {e}')
