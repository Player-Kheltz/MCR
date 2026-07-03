"""Comando: weblearn - Aprendizado web (busca, fragmenta, salva no KG).
Chama o pipeline web_learn.py do sandbox (1367 linhas)."""
import os, sys, subprocess

WEBLEARN_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sandbox', 'web_learn.py')

def register():
    return {
        "name": "weblearn",
        "desc": "Aprendizado web: busca curada, fragmentacao, narrativa, KG. Args: <consulta> [--auto] [--dry-run] [--urls-only] [--shallow]",
        "handler": execute,
        "args": [{"name": "consulta", "type": "str", "required": True}],
        "categoria": "kg",
    }

def execute(kg, ia, args, ctx_crew=None, orquestrador_ctx=None):
    if not args:
        print('[WebLearn] Uso: weblearn <consulta> [--auto] [--dry-run] [--urls-only] [--shallow]')
        return True

    if not os.path.exists(WEBLEARN_PATH):
        print(f'[WebLearn] ERRO: {WEBLEARN_PATH} nao encontrado')
        return True

    # Monta comando: passa todos os args
    cmd = [sys.executable, WEBLEARN_PATH] + args
    print(f'[WebLearn] Executando: {" ".join(cmd[-4:])}')
    sys.stdout.flush()

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        saida = (r.stdout or '') + (r.stderr or '')
        # Mostra as ultimas linhas relevantes
        linhas = saida.split('\n')
        resumo = [l for l in linhas if any(k in l.lower() for k in
                  ['aprendizado', 'fragmento', 'narrativa', 'erro', 'sucesso',
                   'salvo', 'kg', 'concluido', 'finalizado'])]
        if resumo:
            print('\n'.join(resumo[-5:]))
        else:
            print(saida[-500:])
        return True
    except subprocess.TimeoutExpired:
        print('[WebLearn] TIMEOUT (300s)')
        return True
    except Exception as e:
        print(f'[WebLearn] ERRO: {e}')
        return True
