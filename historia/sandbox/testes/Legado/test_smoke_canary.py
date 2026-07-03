"""Smoke Test do Servidor Canary.

Verifica se o servidor compila, sobe, e responde nas portas esperadas.
Uso:
    python sandbox/test_smoke_canary.py              # Teste completo
    python sandbox/test_smoke_canary.py --quick      # Só verificar portas
"""
import sys, os, subprocess, time, socket, json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CANARY_DIR = os.path.join(BASE, 'Canary')
SANDBOX = os.path.join(BASE, 'sandbox')

# Portas que o servidor Canary usa
PORTAS = {
    'game': 7171,
    'login': 7172,
    'status': 7173,
}

# Path do binário do servidor
SERVER_BIN = os.path.join(CANARY_DIR, 'build', 'bin', 'canary-sln.exe')
SERVER_ALT = os.path.join(CANARY_DIR, 'canary-sln.exe')


def check_port(port, timeout=2):
    """Verifica se uma porta TCP está ouvindo."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False


def find_server():
    """Encontra o binário do servidor."""
    for path in [SERVER_BIN, SERVER_ALT]:
        if os.path.exists(path):
            return path
    return None


def test_compilacao():
    """Testa se o servidor compila (verifica existência do binário)."""
    print("  [Compilacao] Procurando binario do servidor...")
    bin_path = find_server()
    if bin_path:
        size = os.path.getsize(bin_path)
        print(f"    OK: {bin_path} ({size/1024:.0f} KB)")
        return True
    print("    WARN: Binario nao encontrado. Servidor nao compilado?")
    return False


def test_portas():
    """Testa se as portas do servidor estao ouvindo."""
    print("  [Portas] Verificando portas do servidor...")
    todas_ok = True
    for nome, porta in PORTAS.items():
        if check_port(porta):
            print(f"    OK: {nome} ({porta}/TCP) — ouvindo")
        else:
            print(f"    FAIL: {nome} ({porta}/TCP) — nao responde")
            todas_ok = False
    return todas_ok


def test_subir_servidor(timeout=30):
    """Tenta subir o servidor e verificar se as portas abrem."""
    print(f"  [Startup] Tentando iniciar servidor (timeout={timeout}s)...")
    
    bin_path = find_server()
    if not bin_path:
        print("    FAIL: Binario nao encontrado para teste de startup")
        return False
    
    # Mata processos anteriores
    subprocess.run(['taskkill', '/f', '/im', 'canary-sln.exe'], 
                   capture_output=True)
    time.sleep(1)
    
    # Inicia servidor
    try:
        proc = subprocess.Popen(
            [bin_path],
            cwd=CANARY_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"    FAIL: Erro ao iniciar: {e}")
        return False
    
    # Aguarda portas abrirem
    for i in range(timeout):
        portas_ok = all(check_port(p) for p in PORTAS.values())
        if portas_ok:
            print(f"    OK: Servidor iniciado em {i+1}s (PID {proc.pid})")
            return True
        time.sleep(1)
    
    # Timeout
    print(f"    FAIL: Servidor nao respondeu apos {timeout}s")
    proc.kill()
    return False


def test_derrubar_servidor():
    """Derruba o servidor se estiver rodando."""
    print("  [Shutdown] Derrubando servidor...")
    r = subprocess.run(['taskkill', '/f', '/im', 'canary-sln.exe'],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("    OK: Servidor encerrado")
    else:
        print("    OK: Servidor ja estava encerrado")
    return True


def run_smoke_test(quick=False):
    """Executa todos os testes de fumaça."""
    print("=" * 60)
    print("  SMOKE TEST — Servidor Canary")
    print("=" * 60)
    
    resultados = {}
    
    # Teste 1: Compilacao
    print("\n--- 1. Compilacao ---")
    resultados['compilacao'] = test_compilacao()
    
    # Teste 2: Portas (se servidor ja estiver rodando)
    print("\n--- 2. Portas ---")
    resultados['portas'] = test_portas()
    
    # Teste 3: Startup (se nao for quick)
    if not quick:
        print("\n--- 3. Startup ---")
        resultados['startup'] = test_subir_servidor()
        
        print("\n--- 4. Shutdown ---")
        resultados['shutdown'] = test_derrubar_servidor()
    
    # Relatorio
    print("\n" + "=" * 60)
    print("  RELATORIO SMOKE TEST")
    print("=" * 60)
    for teste, resultado in resultados.items():
        status = 'OK' if resultado else 'FAIL'
        print(f"  [{status}] {teste}")
    
    total_ok = sum(1 for r in resultados.values() if r)
    total = len(resultados)
    print(f"\n  {total_ok}/{total} testes OK")
    
    # Salva relatorio
    relatorio = {
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'resultados': resultados,
    }
    path = os.path.join(SANDBOX, '.mcr_smoke_report.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(f"\n[Relatorio salvo em .mcr_smoke_report.json]")
    
    return all(resultados.values())


if __name__ == '__main__':
    quick = '--quick' in sys.argv
    success = run_smoke_test(quick=quick)
    sys.exit(0 if success else 1)
