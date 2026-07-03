#!/usr/bin/env python3
"""
test.py — Automacao de testes no MCR

Uso:
    python scripts/test.py --setup              # Cria conta TestChar no banco
    python scripts/test.py cmd "!testesistema"   # Executa comando como TestChar
    python scripts/test.py los x1,y1,z1 x2,y2,z2 # Testa isSightClear
    python scripts/test.py walk x,y,z            # Navega ate posicao
    python scripts/test.py attack "Orc"          # Ataca criatura pelo nome
    python scripts/test.py pos                   # Mostra posicao atual
    python scripts/test.py assert "!cmd" --expect "resultado"  # Comando + assercao
    python scripts/test.py suite tests/los.txt   # Executa suite de testes
    python scripts/test.py listen                # Mostra resultados pendentes
"""

import os
import sys
import time
import json
import hashlib
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANARY_DIR = os.path.join(BASE_DIR, "Canary")
TEST_IN = os.path.join(CANARY_DIR, "data", "logs", "test_in.txt")
TEST_OUT = os.path.join(CANARY_DIR, "data", "logs", "test_out.txt")

_cmd_id = 0
_last_read_pos = 0

DB_CONFIG = {
    "host": os.environ.get("MCR_DB_HOST", "127.0.0.1"),
    "user": os.environ.get("MCR_DB_USER", "root"),
    "password": os.environ.get("MCR_DB_PASSWORD", ""),
    "database": os.environ.get("MCR_DB_NAME", "BancoServer"),
}


def ensure_dirs():
    os.makedirs(os.path.join(CANARY_DIR, "data", "logs"), exist_ok=True)
    for p in [TEST_IN, TEST_OUT]:
        if not os.path.exists(p):
            with open(p, "w") as f:
                f.write("")


def next_id():
    global _cmd_id
    _cmd_id += 1
    return _cmd_id


def send_command(action, param=""):
    """Escreve comando no test_in.txt para o servidor ler."""
    cmd_id = next_id()
    line = f"{cmd_id}|{action}|{param}\n"
    with open(TEST_IN, "a", encoding="utf-8") as f:
        f.write(line)
    return cmd_id


def wait_result(cmd_id, timeout=10):
    """Espera ate o resultado aparecer no test_out.txt."""
    global _last_read_pos
    start = time.time()
    last_size = os.path.getsize(TEST_OUT) if os.path.exists(TEST_OUT) else 0

    while time.time() - start < timeout:
        try:
            current_size = os.path.getsize(TEST_OUT)
        except OSError:
            current_size = 0

        if current_size > last_size:
            with open(TEST_OUT, "r", encoding="utf-8") as f:
                f.seek(last_size)
                new_data = f.read()
            for line in new_data.strip().split("\n"):
                parts = line.strip().split("|", 2)
                if len(parts) >= 2 and parts[0].isdigit():
                    if int(parts[0]) == cmd_id:
                        _last_read_pos += len(line) + 1
                        return {
                            "id": int(parts[0]),
                            "status": parts[1],
                            "data": parts[2] if len(parts) > 2 else ""
                        }
            last_size = current_size
        time.sleep(0.3)

    return {"id": cmd_id, "status": "timeout", "data": ""}


def setup_account():
    """Cria conta e personagem TestChar no banco."""
    try:
        import pymysql
    except ImportError:
        print("[ERRO] pymysql nao instalado. pip install pymysql")
        return False

    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Verifica se conta ja existe
    cur.execute("SELECT id FROM accounts WHERE name = 'test_account'")
    row = cur.fetchone()
    if row:
        account_id = row[0]
        print("[SETUP] Conta test_account ja existe (id=%s)" % account_id)
    else:
        password = hashlib.sha1("test123".encode()).hexdigest()
        cur.execute(
            "INSERT INTO accounts (name, password, email, type, creation, premdays) VALUES (%s, %s, %s, %s, %s, %s)",
            ("test_account", password, "test@mcr.com", 5, int(time.time()), 9999)
        )
        conn.commit()
        account_id = cur.lastrowid
        print("[SETUP] Conta test_account criada (id=%s)" % account_id)

    # Verifica se personagem existe
    cur.execute("SELECT id FROM players WHERE name = 'TestChar'")
    row = cur.fetchone()
    if row:
        print("[SETUP] Personagem TestChar ja existe (id=%s)" % row[0])
        player_id = row[0]
    else:
        cur.execute("""
            INSERT INTO players (name, account_id, group_id, level, vocation,
                health, healthmax, experience, mana, manamax,
                town_id, posx, posy, posz, sex, pronoun, cap,
                skill_fist, skill_club, skill_sword, skill_axe, skill_dist,
                skill_shielding, skill_fishing)
            VALUES (%s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s)
        """, (
            "TestChar", account_id, 6, 100, 0,  # group_id=6 (GM), level 100, vocation 0
            2000, 2000, 0, 2000, 2000,
            1, 1094, 998, 6, 0, 0, 30000,  # town_id 1, temple pos
            50, 50, 50, 50, 50, 50, 50
        ))
        conn.commit()
        player_id = cur.lastrowid
        print("[SETUP] Personagem TestChar criado (id=%s)" % player_id)

    conn.close()
    print("[SETUP] Pronto! Account: test_account / test123")
    return True


def cmd_cmd(params):
    """Envia comando de fala como TestChar."""
    cmd_text = " ".join(params)
    cmd_id = send_command("cmd", cmd_text)
    print("[CMD] Enviando: %s (id=%d)" % (cmd_text, cmd_id))
    result = wait_result(cmd_id)
    print("[RESULT] %s: %s" % (result["status"], result["data"]))


def cmd_los(params):
    """Testa isSightClear entre duas posicoes."""
    if len(params) < 2:
        print("[ERRO] Uso: test.py los x1,y1,z1 x2,y2,z2")
        return
    param = params[0] + ";" + params[1]
    cmd_id = send_command("los", param)
    print("[LOS] %s -> %s (id=%d)" % (params[0], params[1], cmd_id))
    result = wait_result(cmd_id)
    status = result["data"]
    print("[RESULT] isSightClear = %s" % status)
    if status == "true":
        print("  -> Visivel")
    else:
        print("  -> BLOQUEADO")


def cmd_walk(params):
    """Navega ate uma posicao."""
    if not params:
        print("[ERRO] Uso: test.py walk x,y,z")
        return
    cmd_id = send_command("walk", params[0])
    print("[WALK] Indo para %s (id=%d)" % (params[0], cmd_id))
    result = wait_result(cmd_id, timeout=15)
    print("[RESULT] %s: %s" % (result["status"], result["data"]))


def cmd_attack(params):
    """Ataca criatura pelo nome."""
    if not params:
        print("[ERRO] Uso: test.py attack \"Nome da Criatura\"")
        return
    target = " ".join(params)
    cmd_id = send_command("attack", target)
    print("[ATTACK] Atacando %s (id=%d)" % (target, cmd_id))
    result = wait_result(cmd_id)
    print("[RESULT] %s: %s" % (result["status"], result["data"]))


def cmd_pos():
    """Mostra posicao atual."""
    cmd_id = send_command("pos", "")
    result = wait_result(cmd_id)
    print("[POS] %s" % result["data"])


def cmd_assert(params):
    """Executa comando e verifica se resultado contem texto esperado."""
    if "--expect" not in params:
        print("[ERRO] Uso: test.py assert \"!comando\" --expect \"texto\"")
        return
    idx = params.index("--expect")
    cmd_text = " ".join(params[:idx])
    expected = " ".join(params[idx + 1:])

    cmd_id = send_command("cmd", cmd_text)
    print("[ASSERT] Comando: %s" % cmd_text)
    print("[ASSERT] Esperado: %s" % expected)
    result = wait_result(cmd_id)
    passed = expected.lower() in result["data"].lower()
    status = "PASS" if passed else "FAIL"
    print("[%s] Obtido: %s" % (status, result["data"]))
    return passed


def cmd_suite(params):
    """Executa suite de testes de um arquivo."""
    if not params:
        print("[ERRO] Uso: test.py suite tests/arquivo.txt")
        return
    suite_path = params[0]
    if not os.path.isabs(suite_path):
        suite_path = os.path.join(BASE_DIR, "scripts", suite_path)
    if not os.path.exists(suite_path):
        print("[ERRO] Suite nao encontrada: %s" % suite_path)
        return

    with open(suite_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("[SUITE] Executando %s (%d comandos)" % (suite_path, len(lines)))
    passed = 0
    failed = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        parts = line.split()
        if not parts:
            continue
        action = parts[0]
        rest = parts[1:]
        print("\n[TEST %d/%d] %s" % (i + 1, len([l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("--")]), line))
        try:
            if action == "cmd":
                cmd_cmd(rest)
            elif action == "los":
                cmd_los(rest)
            elif action == "walk":
                cmd_walk(rest)
            elif action == "assert":
                rest_str = " ".join(rest)
                assert_parts = rest_str.split(" --expect ")
                if len(assert_parts) == 2:
                    if cmd_assert(assert_parts[0].split() + ["--expect"] + assert_parts[1].split()):
                        passed += 1
                    else:
                        failed += 1
            elif action == "pos":
                cmd_pos()
        except Exception as e:
            print("[ERRO] %s" % e)
            failed += 1

    print("\n[SUITE] Resultado: %d passed, %d failed" % (passed, failed))


def cmd_listen():
    """Mostra resultados recentes."""
    if not os.path.exists(TEST_OUT):
        print("(vazio)")
        return
    with open(TEST_OUT, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.strip().split("\n")
    for line in lines[-10:]:
        if line.strip():
            parts = line.split("|", 2)
            print("  #%s [%s] %s" % (parts[0], parts[1], parts[2] if len(parts) > 2 else ""))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    ensure_dirs()
    cmd = sys.argv[1]

    if cmd == "--setup":
        setup_account()
    elif cmd == "cmd":
        cmd_cmd(sys.argv[2:])
    elif cmd == "los":
        cmd_los(sys.argv[2:])
    elif cmd == "walk":
        cmd_walk(sys.argv[2:])
    elif cmd == "attack":
        cmd_attack(sys.argv[2:])
    elif cmd == "pos":
        cmd_pos()
    elif cmd == "assert":
        cmd_assert(sys.argv[2:])
    elif cmd == "suite":
        cmd_suite(sys.argv[2:])
    elif cmd == "listen":
        cmd_listen()
    else:
        print("[ERRO] Comando desconhecido: %s" % cmd)
        print(__doc__)


if __name__ == "__main__":
    main()
