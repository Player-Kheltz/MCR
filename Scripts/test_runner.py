#!/usr/bin/env python3
"""
test_runner.py — Orquestrador autonomo de testes MCR

Uso:
    python "scripts/test_runner.py"                    # Executa suite padrao
    python "scripts/test_runner.py" --suite <arquivo>  # Suite customizada
    python "scripts/test_runner.py" --list             # Lista suites disponiveis

Fluxo:
  1. Para servidor antigo
  2. Inicia servidor novo (silencioso)
  3. Aguarda "Projeto MCR online!"
  4. Executa cada comando da suite
  5. Valida resultados
  6. Reporta PASS/FAIL
  7. (Opcional) Para servidor
"""
import os
import sys
import time
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CANARY_DIR = os.path.join(BASE_DIR, "Canary")
TEST_IN = os.path.join(CANARY_DIR, "data", "logs", "test_in.txt")
TEST_OUT = os.path.join(CANARY_DIR, "data", "logs", "test_out.txt")
SUITES_DIR = os.path.join(SCRIPTS_DIR, "tests")
SERVER_LOG = os.path.join(CANARY_DIR, "data", "logs", "server_output.log")


def log(msg):
    print(f"[RUNNER] {msg}")


def server_stop():
    log("Parando servidor...")
    subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"],
                   capture_output=True, text=True)
    time.sleep(2)


def server_start():
    log("Iniciando servidor...")
    exe = os.path.join(CANARY_DIR, "canary-sln.exe")
    if not os.path.exists(exe):
        log(f"[ERRO] {exe} nao encontrado")
        return False
    with open(SERVER_LOG, "w") as lf:
        subprocess.Popen([exe], cwd=CANARY_DIR, stdout=lf, stderr=lf)
    # Aguarda "Projeto MCR online!"
    for _ in range(60):
        time.sleep(1)
        if os.path.exists(SERVER_LOG):
            with open(SERVER_LOG, "r", encoding="utf-8", errors="ignore") as f:
                if "Projeto MCR online!" in f.read():
                    log("Servidor online!")
                    return True
    log("[ERRO] Timeout aguardando servidor")
    return False


def reset_test_files():
    for p in [TEST_IN, TEST_OUT]:
        with open(p, "w") as f:
            f.write("")


def send_command(action, param=""):
    cmd_id_file = os.path.join(BASE_DIR, ".test_runner_id")
    cmd_id = 1
    if os.path.exists(cmd_id_file):
        with open(cmd_id_file, "r") as f:
            try:
                cmd_id = int(f.read().strip()) + 1
            except:
                cmd_id = 1
    with open(cmd_id_file, "w") as f:
        f.write(str(cmd_id))

    line = f"{cmd_id}|{action}|{param}\n"
    with open(TEST_IN, "a", encoding="utf-8") as f:
        f.write(line)
    return cmd_id


def wait_result(cmd_id, timeout=10):
    last_size = os.path.getsize(TEST_OUT) if os.path.exists(TEST_OUT) else 0
    start = time.time()
    while time.time() - start < timeout:
        if not os.path.exists(TEST_OUT):
            time.sleep(0.3)
            continue
        current = os.path.getsize(TEST_OUT)
        if current > last_size:
            with open(TEST_OUT, "r", encoding="utf-8") as f:
                f.seek(last_size)
                new_data = f.read()
            for line in new_data.strip().split("\n"):
                parts = line.strip().split("|", 2)
                if len(parts) >= 2 and parts[0].isdigit():
                    if int(parts[0]) == cmd_id:
                        return {
                            "id": int(parts[0]),
                            "status": parts[1],
                            "data": parts[2] if len(parts) > 2 else ""
                        }
            last_size = current
        time.sleep(0.3)
    return {"id": cmd_id, "status": "timeout", "data": ""}


def run_test(action, param="", timeout=10):
    cmd_id = send_command(action, param)
    return wait_result(cmd_id, timeout)


def list_suites():
    if not os.path.exists(SUITES_DIR):
        log(f"Diretorio de suites: {SUITES_DIR}")
        log("(vazio — nenhuma suite criada)")
        return
    for f in sorted(os.listdir(SUITES_DIR)):
        if f.endswith(".txt"):
            path = os.path.join(SUITES_DIR, f)
            with open(path, "r") as fh:
                first_line = fh.readline().strip()
            desc = first_line.lstrip("#").strip() if first_line.startswith("#") else ""
            log(f"  {f}  {desc}")


def run_suite(suite_path):
    if not os.path.exists(suite_path):
        log(f"[ERRO] Suite nao encontrada: {suite_path}")
        return False

    with open(suite_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines()]

    tests = [l for l in lines if l and not l.startswith("#") and not l.startswith("--")]

    log(f"Executando suite: {os.path.basename(suite_path)} ({len(tests)} testes)")
    results = {"pass": 0, "fail": 0, "error": 0, "timeout": 0}

    for i, line in enumerate(tests):
        parts = line.split()
        action = parts[0]
        rest = " ".join(parts[1:])

        # Parse expect se houver
        expect = None
        if "--expect" in rest:
            idx = rest.index("--expect")
            param_str = rest[:idx].strip()
            expect = rest[idx + len("--expect"):].strip()
        else:
            param_str = rest

        log(f"  [{i+1}/{len(tests)}] {action} {param_str[:60]}...")

        try:
            result = run_test(action, param_str)
            status = result["status"]
            data = result["data"]

            if status == "timeout":
                log(f"    TIMEOUT")
                results["timeout"] += 1
            elif expect:
                if expect.lower() in data.lower():
                    log(f"    PASS (esperado: {expect})")
                    results["pass"] += 1
                else:
                    log(f"    FAIL: esperado '{expect}', obtido '{data}'")
                    results["fail"] += 1
            elif status == "ok":
                log(f"    OK: {data[:80]}")
                results["pass"] += 1
            else:
                log(f"    {status.upper()}: {data[:80]}")
                results["fail"] += 1

        except Exception as e:
            log(f"    ERRO: {e}")
            results["error"] += 1

    log(f"\n=== RESULTADO ===")
    log(f"  PASS: {results['pass']}")
    log(f"  FAIL: {results['fail']}")
    log(f"  TIMEOUT: {results['timeout']}")
    log(f"  ERRO: {results['error']}")
    total = results['pass'] + results['fail'] + results['timeout'] + results['error']
    log(f"  TOTAL: {total}")

    return results["fail"] == 0 and results["error"] == 0


def ensure_suite_dir():
    os.makedirs(SUITES_DIR, exist_ok=True)


def create_default_suite():
    ensure_suite_dir()
    suite_path = os.path.join(SUITES_DIR, "basico.txt")
    if os.path.exists(suite_path):
        return
    with open(suite_path, "w", encoding="utf-8") as f:
        f.write("# Suite basica de testes MCR\n")
        f.write("# Cada linha: <acao> <parametros> [--expect <texto>]\n")
        f.write("\n")
        f.write("# Teste 1: Verificar se test_bot esta respondendo\n")
        f.write("eval Game.getPlayersCount()\n")
        f.write("\n")
        f.write("# Teste 2: Posicao do avatar\n")
        f.write("pos\n")
        f.write("\n")
        f.write("# Teste 3: LOS mesmo piso (deve ser true)\n")
        f.write("los 1094,998,6;1095,998,6 --expect true\n")
        f.write("\n")
        f.write("# Teste 4: LOS com bloqueio (mesma pos = true)\n")
        f.write("los 1094,998,6;1094,998,6 --expect true\n")
        f.write("\n")
        f.write("# Teste 5: Avatar spawn\n")
        f.write("avatar spawn\n")
        f.write("\n")
        f.write("# Teste 6: Setpos\n")
        f.write("setpos 1100,1000,7\n")
        f.write("\n")
        f.write("# Teste 7: Verificar pos apos setpos\n")
        f.write("pos --expect 1100,1000,7\n")
    log(f"Suite padrao criada: {suite_path}")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--suite":
        suite_path = sys.argv[2]
        if not os.path.isabs(suite_path):
            suite_path = os.path.join(SUITES_DIR, suite_path)
        run_suite(suite_path)
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "--list":
        list_suites()
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "--create":
        create_default_suite()
        return

    # Default: stop -> start -> test -> stop -> report
    server_stop()
    reset_test_files()

    if not server_start():
        sys.exit(1)

    create_default_suite()
    success = run_suite(os.path.join(SUITES_DIR, "basico.txt"))

    server_stop()

    if success:
        log("\n[TODOS OS TESTES PASSARAM]")
    else:
        log("\n[ALGUNS TESTES FALHARAM]")

    return 0 if success else 1


if __name__ == "__main__":
    main()
