#!/usr/bin/env python3
"""
win_tools.py — Ferramentas Windows seguras para o assistente local.
Todas as operacoes sao READ-ONLY por padrao. Operacoes de escrita requerem confirmacao.

Uso: python scripts/win_tools.py <comando> [args]
"""
import os, sys, json, subprocess, platform, re

# Operacoes permitidas (whitelist)
ALLOWED_READ = {
    "process_list", "service_list", "disk_usage", "memory_info",
    "env_vars", "registry_read", "file_list", "event_log",
    "network_stats", "whoami", "system_info", "path_exists"
}

ALLOWED_WRITE = {
    "env_set", "file_create", "file_delete", "registry_write",
    "process_kill", "service_start", "service_stop"
}  # Todas requerem --force


def cmd_process_list():
    result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    processes = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split(",")
        if len(parts) >= 2:
            processes.append({
                "name": parts[0].strip('"'),
                "pid": parts[1].strip('"'),
                "session": parts[2].strip('"') if len(parts) > 2 else "",
            })
    return {"total": len(processes), "processes": processes[:50]}


def cmd_service_list():
    result = subprocess.run(["sc", "query", "state=", "all"], capture_output=True, text=True)
    services = []
    current = {}
    for line in result.stdout.split("\n"):
        line = line.strip()
        if not line:
            if current.get("name"):
                services.append(current)
                current = {}
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key == "SERVICE_NAME":
                current["name"] = val
            elif key == "DISPLAY_NAME":
                current["display"] = val
            elif key == "STATE":
                m = re.search(r"(\d+)", val)
                current["state"] = {"1": "STOPPED", "2": "START_PENDING", "3": "STOP_PENDING",
                                    "4": "RUNNING"}.get(m.group(1) if m else "", val)
    if current.get("name"):
        services.append(current)
    return {"total": len(services), "services": services[:30]}


def cmd_disk_usage():
    drives = []
    for d in range(65, 91):
        drive = f"{chr(d)}:\\"
        if os.path.exists(drive):
            try:
                usage = subprocess.run(["wmic", "logicaldisk", "where", f"DeviceID='{drive}'",
                                        "get", "Size,FreeSpace", "/format:csv"],
                                       capture_output=True, text=True, timeout=5)
                lines = usage.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split(",")
                    if len(parts) >= 3:
                        total = int(parts[2]) if parts[2] else 0
                        free = int(parts[1]) if parts[1] else 0
                        drives.append({
                            "drive": drive,
                            "total_gb": round(total / 1e9, 1),
                            "free_gb": round(free / 1e9, 1),
                            "used_pct": round((1 - free / total) * 100, 1) if total > 0 else 0
                        })
            except:
                pass
    return {"drives": drives}


def cmd_system_info():
    info = {
        "os": platform.system() + " " + platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }
    try:
        mem = subprocess.run(["wmic", "computersystem", "get", "TotalPhysicalMemory", "/format:csv"],
                             capture_output=True, text=True, timeout=5)
        lines = mem.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split(",")
            if len(parts) >= 1 and parts[0].isdigit():
                info["ram_gb"] = round(int(parts[0]) / 1e9, 1)
    except:
        pass
    
    return info


def cmd_whoami():
    result = subprocess.run(["whoami"], capture_output=True, text=True)
    return {"user": result.stdout.strip()}


def cmd_env_vars(var=None):
    if var:
        return {var: os.environ.get(var, "(not set)")}
    # Retorna apenas vars nao-sensiveis
    safe = {k: v for k, v in sorted(os.environ.items())
            if not any(s in k.lower() for s in ["key", "token", "secret", "password", "credential", "auth"])}
    return safe


def cmd_file_list(path=".", max_files=30):
    if not os.path.exists(path):
        return {"error": f"Path not found: {path}"}
    items = []
    try:
        for entry in os.scandir(path):
            items.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified": entry.stat().st_mtime
            })
            if len(items) >= max_files:
                break
    except PermissionError:
        return {"error": "Permission denied"}
    return {"path": path, "total": len(items), "items": items}


def cmd_path_exists(path):
    return {"path": path, "exists": os.path.exists(path), "type": "dir" if os.path.isdir(path) else ("file" if os.path.isfile(path) else "other") if os.path.exists(path) else None}


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/win_tools.py <comando> [args]")
        print(f"Comandos READ: {', '.join(sorted(ALLOWED_READ))}")
        print(f"Comandos WRITE: {', '.join(sorted(ALLOWED_WRITE))} (requer --force)")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    force = "--force" in args
    
    if cmd in ALLOWED_WRITE and not force:
        print(f"AVISO: '{cmd}' e uma operacao de escrita. Use --force para confirmar.")
        sys.exit(1)
    
    # Remove --force dos args
    args = [a for a in args if a != "--force"]
    
    func_name = f"cmd_{cmd}"
    if func_name not in globals():
        print(f"Comando desconhecido: {cmd}")
        sys.exit(1)
    
    try:
        result = globals()[func_name](*args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # Aviso de seguranca
    if len(sys.argv) > 1 and sys.argv[1] in ALLOWED_WRITE and "--force" not in sys.argv:
        print(f"⚠️  Operacao de escrita detectada: {sys.argv[1]}")
        print(f"   Use --force para confirmar que deseja alterar o sistema.")
        sys.exit(1)
    main()
