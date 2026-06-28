import subprocess, sys, os, json, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE, "backend")
MOBILE_DIR = os.path.join(BASE, "mobile")

# ── Helpers ──────────────────────────────────────────

def _get_pid_on_port(port=3000):
    try:
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5
        ).stdout
        for line in out.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit():
                    return int(pid)
    except:
        pass
    return None

def _run(cmd, cwd=None, timeout=120):
    # Use npx.cmd instead of npx for Windows subprocess compatibility
    cmd = ["npx.cmd" if a == "npx" else a for a in cmd]
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "TIMEOUT", "code": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "code": -1}

# ── Ações ────────────────────────────────────────────

def action_start():
    pid = _get_pid_on_port()
    if pid:
        return {"ok": True, "pids": {"backend": pid}, "note": "already running"}

    try:
        p = subprocess.Popen(
            ["node", "dist\\server.js"],
            cwd=BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(2)
        pid2 = _get_pid_on_port()
        ok = pid2 is not None
        return {"ok": ok, "pids": {"backend": pid2 or p.pid}, "errors": [] if ok else ["health failed"]}
    except Exception as e:
        return {"ok": False, "pids": {}, "errors": [str(e)]}

def action_stop():
    pid = _get_pid_on_port()
    if not pid:
        return {"ok": True, "note": "not running"}
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
        time.sleep(1)
        still = _get_pid_on_port()
        return {"ok": still is None, "killed": [pid]}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

def action_status():
    pid = _get_pid_on_port()
    return {"backend": pid is not None, "pid": pid}

def action_typecheck():
    r1 = _run(["npx", "tsc", "--noEmit"], cwd=BACKEND_DIR)
    r2 = _run(["npx", "tsc", "--noEmit"], cwd=MOBILE_DIR)

    errors = []
    if not r1["ok"]:
        errors.append({"project": "backend", "lines": [l for l in r1["stderr"].splitlines() if l.strip()]})
    if not r2["ok"]:
        errors.append({"project": "mobile", "lines": [l for l in r2["stderr"].splitlines() if l.strip()]})

    return {"ok": len(errors) == 0, "errors": errors}

def action_build():
    r = _run(["npx", "tsc"], cwd=BACKEND_DIR)
    if not r["ok"]:
        return {"ok": False, "errors": [l for l in r["stderr"].splitlines() if l.strip()]}
    return {"ok": True}

def action_migrate():
    r = _run(["npx", "prisma", "migrate", "dev"], cwd=BACKEND_DIR)
    if not r["ok"]:
        return {"ok": False, "errors": [l for l in r["stderr"].splitlines() if l.strip()]}
    return {"ok": True, "output": r["stdout"]}

def action_verify():
    status = action_status()
    tc = action_typecheck()
    lines = []
    lines.append(f"Servidor: {'[ON]' if status['backend'] else '[OFF]'}")
    lines.append(f"Typecheck: {'[OK]' if tc['ok'] else '[ERROR]'}")
    if not tc["ok"]:
        for e in tc["errors"]:
            for line in e["lines"]:
                lines.append(f"  {line}")
    return {"ok": tc["ok"], "status": status, "typecheck": tc, "summary": "\n".join(lines)}

def action_checkpoint():
    args = sys.argv[2:] if len(sys.argv) > 2 else ["show"]
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "checkpoint.py")] + args,
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
        return {"ok": False, "error": r.stderr}
    except json.JSONDecodeError:
        return {"ok": False, "error": "resposta invalida do checkpoint"}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

def action_rag():
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    if not args:
        return {"ok": False, "error": "Uso: python server.py rag <consulta>"}
    query = " ".join(args)
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "rag_query.py"), query],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(r.stdout) if r.returncode == 0 else {"ok": False, "error": r.stderr}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

def action_reindex():
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "rag_indexer.py")],
            capture_output=True, text=True, timeout=300
        )
        return json.loads(r.stdout) if r.returncode == 0 else {"ok": False, "error": r.stderr}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

def action_doctor():
    report = {"ollama": False, "models": {}, "validation": None, "backend": False}

    # Check Ollama
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
        data = json.loads(r.read())
        report["ollama"] = True
        for m in data.get("models", []):
            report["models"][m["name"]] = "available"
    except:
        report["ollama"] = False

    # Check backend
    try:
        r = urllib.request.urlopen("http://localhost:3000/api/health", timeout=3)
        report["backend"] = r.status == 200
    except:
        report["backend"] = False

    # Run validation if Ollama is up
    if report["ollama"]:
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "validate_local.py"), "truth"],
                capture_output=True, text=True, timeout=120
            )
            report["validation"] = r.stdout[:500] if r.returncode == 0 else r.stderr[:500]
        except:
            report["validation"] = "falhou ao executar"

    lines = []
    lines.append(f"Ollama:      {'[OK]' if report['ollama'] else '[OFF]'}")
    if report["ollama"]:
        for name, status in report["models"].items():
            lines.append(f"  {name}: {status}")
    else:
        lines.append("  (instalado mas nao rodando)")
    lines.append(f"Backend:     {'[OK]' if report['backend'] else '[OFF]'}")
    lines.append(f"Validacao:   {'rodou' if report.get('validation') else 'nao rodou'}")
    report["summary"] = "\n".join(lines)
    return report

def action_sync():
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "doc_sync.py")],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(r.stdout) if r.returncode == 0 else {"ok": False, "error": r.stderr}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

def action_session():
    cp = action_checkpoint()
    lessons = action_lesson(["list"])
    info = {
        "checkpoint": cp,
        "lessons": lessons.get("lessons", []) if lessons.get("ok") else [],
    }
    return info

def action_lesson(args=None):
    args = args or sys.argv[2:] if len(sys.argv) > 2 else ["list"]
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "lesson.py")] + args,
            capture_output=True, text=True, timeout=15
        )
        return json.loads(r.stdout) if r.returncode == 0 else {"ok": False, "error": r.stderr}
    except json.JSONDecodeError:
        return {"ok": False, "error": "resposta invalida"}
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}

# ── Main ─────────────────────────────────────────────

COMMANDS = {
    "start": action_start,
    "stop": action_stop,
    "status": action_status,
    "typecheck": action_typecheck,
    "build": action_build,
    "migrate": action_migrate,
    "verify": action_verify,
    "checkpoint": action_checkpoint,
    "doctor": action_doctor,
    "rag": action_rag,
    "reindex": action_reindex,
    "sync": action_sync,
    "session": action_session,
    "lesson": action_lesson,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = COMMANDS.get(cmd)
    if not fn:
        print(json.dumps({"error": f"unknown: {cmd}"}))
        sys.exit(1)
    out = fn()
    text = json.dumps(out, ensure_ascii=False)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('cp1252', errors='replace'))
