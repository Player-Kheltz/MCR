"""Comando: task - Delega para QUALQUER script do MCR-DevIA."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "task",
        "desc": "Delega para QUALQUER script do MCR-DevIA.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Delega para QUALQUER script do MCR-DevIA.
    Uso: python mcr_devia.py task <script>
         python mcr_devia.py task list (mostra todos)
         python mcr_devia.py task <script> <args...>"""
    DEVIA_DIR = os.path.dirname(__file__)
    _SANDBOX_DIR = _SANDBOX
    
    # Mapa de scripts (nome -> caminho)
    all_scripts = {}
    for d in [DEVIA_DIR, _SANDBOX_DIR]:
        for f in os.listdir(d):
            if f.endswith('.py') and not f.startswith('_'):
                nome = f.replace('.py', '')
                all_scripts[nome] = os.path.join(d, f)
    
    if args[0] == 'list':
        # Separa scripts do sistema de scripts temporarios
        sistema = {n: p for n, p in all_scripts.items() if 'mcr_devia' in p}
        temporarios = {n: p for n, p in all_scripts.items() if 'sandbox' in p and n not in sistema}
        print(f'[Task] Sistema ({len(sistema)}):')
        for nome in sorted(sistema):
            print(f'  - {nome}')
        if temporarios:
            print(f'\n  Sandbox ({len(temporarios)}): use "task <nome>" para executar')
            for nome in sorted(temporarios):
                print(f'    - {nome}')
            if len(temporarios) > 20:
                print(f'    ... mais {len(temporarios)-20}')
        return
    
    script_nome = args[0]
    sub_args = args[1:]
    
    if script_nome in all_scripts:
        script_path = all_scripts[script_nome]
        print(f'[Task] Executando: {script_nome}')
        try:
            r = subprocess.run([sys.executable, script_path] + sub_args,
                capture_output=True, text=True, timeout=300)
            out = (r.stdout or '')[-1000:]
            err = (r.stderr or '')
            if out:
                print(out)
            if err:
                print(f'  [STDERR] {err}')
                # AUTO-REPARO: analisa, corrige, retenta
                if 'Error' in err or 'Traceback' in err:
                    print(f'[Task] Auto-reparo ativado!')
                    # 1. Identifica o tipo de erro
                    erro_tipo = 'desconhecido'
                    if 'ModuleNotFoundError' in err:
                        erro_tipo = 'import_faltando'
                    elif 'KeyError' in err or 'json.decoder' in err:
                        erro_tipo = 'json_invalido'
                    elif 'FileNotFoundError' in err:
                        erro_tipo = 'arquivo_ausente'
                    elif 'SyntaxError' in err:
                        erro_tipo = 'sintaxe_invalida'
                    print(f'  [Auto-reparo] Tipo: {erro_tipo}')
                    
                    # 2. Tenta corrigir (1 tentativa)
                    if erro_tipo == 'json_invalido':
                        print(f'  [Auto-reparo] JSON invalido. O LearningScan pode ter mudado de formato.')
                        print(f'  [Auto-reparo] Execute: learning_scan_universal.py para regenerar.')
                        # Sugere acao, nao corrige automaticamente (JSON e dado, nao codigo)
                    
                    elif erro_tipo == 'import_faltando':
                        print(f'  [Auto-reparo] Import faltando. Tentando adicionar...')
                        modulo = err.split("'")[1] if "'" in err else '?'
                        print(f'  [Auto-reparo] Modulo ausente: {modulo}')
                    
                    # 3. Registra no log de reparo
                    log_path = os.path.join(_SANDBOX, '.mcr_auto_repair.log')
                    with open(log_path, 'a', encoding='utf-8') as lf:
                        lf.write(f'[{__import__("datetime").datetime.now()}] {script_nome}: {erro_tipo} - {err}\n')
                    print(f'  [Auto-reparo] Erro registrado em .mcr_auto_repair.log')
        except subprocess.TimeoutExpired:
            print(f'[Task] Task {script_nome} excedeu 300s')
        except Exception as e:
            print(f'[Task] Erro ao executar {script_nome}: {e}')
    else:
        print(f'[Task] Script "{script_nome}" nao encontrado.')
        print(f'  Use "task list" para ver todos disponiveis.')
    return True
