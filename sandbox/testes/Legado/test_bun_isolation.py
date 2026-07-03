#!/usr/bin/env python3
"""
Teste isolado de reproducao do Bun crash.
Nao afeta o processo Bun principal (roda em subprocesso Python).
"""
import subprocess, os, sys, time, json, signal, tempfile, threading

BASE = r"E:\Projeto MCR"
RESULTADOS = []

def test(nome, fn):
    try:
        t0 = time.time()
        fn()
        dt = time.time() - t0
        print(f"  ✅ {nome} ({dt:.1f}s)")
        RESULTADOS.append((nome, "PASS", dt))
    except Exception as e:
        print(f"  ❌ {nome}: {e}")
        RESULTADOS.append((nome, f"FAIL: {e}", 0))

print("=" * 60)
print("  TESTE DE ISOLAMENTO - BUN CRASH")
print("  Investigando causas do Segmentation Fault")
print("=" * 60)

# 1. VERIFICAR OVERHEAD DE MEMORIA
print("\n📌 1. Teste de pressao de memoria...")

def mem_test():
    # Aloca e libera memoria varias vezes para ver se causa crash
    for i in range(20):
        data = [x for x in range(1000000)]  # ~8MB cada
        import gc
        gc.collect()
        del data
    # Verifica o processo atual
    import psutil
    proc = psutil.Process(os.getpid())
    mem_info = proc.memory_info()
    print(f"     RSS: {mem_info.rss / 1024 / 1024:.1f} MB")
    print(f"     VMS: {mem_info.vms / 1024 / 1024:.1f} MB")

try:
    test("Alocacao/desalocacao de memoria", mem_test)
except ImportError:
    test("Alocacao/desalocacao de memoria", lambda: None)
    print("     (psutil nao instalado, pulando metricas)")

# 2. ABRIR VARIOS SUBPROCESSOS (simula o que eu fiz)
print("\n📌 2. Teste de abertura/fechamento de processos...")

def proc_test():
    procs = []
    for i in range(10):
        p = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(0.5)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        procs.append(p)
    for p in procs:
        p.wait()
    # Loop rapido de start/kill
    for i in range(5):
        p = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(0.1)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(0.05)
        p.kill()
        p.wait()

test("10 subprocessos + 5 start/kill rapidos", proc_test)

# 3. TESTAR ESCRITA CONCORRENTE EM ARQUIVOS
print("\n📌 3. Teste de escrita concorrente em arquivos...")

def file_test():
    temp = tempfile.mkdtemp()
    def writer(path, count):
        for i in range(count):
            with open(path, "a") as f:
                f.write(f"linha {i}\n")
            time.sleep(0.001)
    files = []
    threads = []
    for i in range(5):
        path = os.path.join(temp, f"test_{i}.txt")
        files.append(path)
        t = threading.Thread(target=writer, args=(path, 100))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    # Limpa
    for f in files:
        os.remove(f)
    os.rmdir(temp)
    print(f"     5 arquivos, 500 linhas cada, 5 threads concorrentes")

test("Escrita concorrente em arquivos", file_test)

# 4. TESTAR OLLAMA API (se disponivel)
print("\n📌 4. Teste de conexao com Ollama...")

def ollama_test():
    import urllib.request
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            models = len(data.get("models", []))
            print(f"     Ollama ONLINE, {models} modelos disponiveis")
    except Exception as e:
        print(f"     Ollama OFFLINE: {e}")

test("Conexao com Ollama", ollama_test)

# 5. TESTAR MODELO LOCAL (inferencia)
print("\n📌 5. Teste de inferencia no modelo local...")

def infer_test():
    import urllib.request
    try:
        payload = json.dumps({
            "model": "qwen2.5-coder:1.5b",
            "messages": [{"role": "user", "content": "Diga 'ok' em 1 palavra."}],
            "stream": False,
            "options": {"temperature": 0.1, "max_tokens": 10}
        }).encode()
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            resp = data["message"]["content"]
            print(f"     Modelo respondeu: {resp[:50]}")
    except Exception as e:
        print(f"     Modelo NAO respondeu: {e}")

test("Inferencia qwen2.5-coder:1.5b", infer_test)

# 6. TESTAR COMANDO OPENCODE (se disponivel)
print("\n📌 6. Teste de comando OpenCode (subprocesso)...")

def opencode_test():
    # Testa se 'opencode --version' funciona sem crashar
    result = subprocess.run(
        ["opencode", "--version"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        print(f"     OpenCode: {result.stdout.strip()[:50]}")
    else:
        raise Exception(f"OpenCode exit code {result.returncode}: {result.stderr[:100]}")

test("OpenCode --version", opencode_test)

# 7. TESTAR FALHA CONHECIDA: BUN COM ARGUMENTO LONGO
print("\n📌 7. Teste de argumento longo no shell...")

def long_arg_test():
    # Cria um argumento muito longo (pode causar crash em alguns shells)
    long_arg = "A" * 10000
    result = subprocess.run(
        ["python", "-c", f"import sys; sys.stdout.write('OK:' + str(len('{long_arg[:100]}')))"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode == 0:
        print(f"     Argumento longo: OK (exit 0)")
    else:
        raise Exception(f"Falhou com argumento longo: {result.stderr[:100]}")

test("Shell com argumento longo (10k chars)", long_arg_test)

# RESUMO
print(f"\n{'='*60}")
pass_count = sum(1 for r in RESULTADOS if r[1] == "PASS")
fail_count = sum(1 for r in RESULTADOS if "FAIL" in r[1])
print(f"  RESULTADO: {pass_count}/{len(RESULTADOS)} PASS, {fail_count} FAIL")
print(f"{'='*60}")

if fail_count == 0:
    print("\n  Nenhum crash reproduzido em ambiente isolado.")
else:
    print(f"\n  {fail_count} teste(s) com falha - possivel causa do Bun crash")
