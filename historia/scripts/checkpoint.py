#!/usr/bin/env python3
"""
checkpoint.py — Sistema de Checkpoint de Sessão

Gerencia o arquivo .session_checkpoint.json para preservar contexto entre
conversas do assistente. Se o usuário fechar a janela acidentalmente,
na próxima conversa o assistente detecta o checkpoint e oferece continuar.

Uso:
    python scripts/checkpoint.py                 # Mostra estado atual
    python scripts/checkpoint.py save             # Salva checkpoint (modo prompt)
    python scripts/checkpoint.py save --auto      # Salva checkpoint com valores auto
    python scripts/checkpoint.py clear            # Marca como completado
    python scripts/checkpoint.py recover          # Tenta recuperar sessão (opencode)
    python scripts/checkpoint.py path             # Mostra caminho do arquivo
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta

# Brasil timezone (UTC-3)
BRT = timezone(timedelta(hours=-3))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKPOINT_PATH = os.path.join(
    BASE_DIR, "docs", "MCR - Instruções", "DevLog", ".session_checkpoint.json"
)

CHECKPOINT_DIR = os.path.dirname(CHECKPOINT_PATH)


def _ensure_dir():
    """Garante que o diretório do checkpoint existe."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def _now_brt():
    """Retorna timestamp ISO com fuso BRT."""
    return datetime.now(BRT).isoformat()


def load():
    """Carrega o checkpoint atual. Retorna dict vazio se não existir."""
    if not os.path.exists(CHECKPOINT_PATH):
        return {"status": "not_found"}
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"status": "corrupted"}


def save(session_id="", titulo="", ultimo_prompt="", tarefa="",
         decisoes=None, arquivos=None, proximos=None, auto=False):
    """Salva checkpoint. Se auto=True, usa valores automáticos."""
    _ensure_dir()
    now = datetime.now(BRT)

    data = load()
    if data.get("status") in ("not_found", "corrupted", "completed", "abandoned"):
        data = {
            "version": 1,
            "ultima_sessao": "",
            "status": "in_progress",
            "titulo": "",
            "ultimo_prompt": "",
            "tarefa_andamento": "",
            "decisoes": [],
            "arquivos_alterados": [],
            "proximos_passos": [],
            "ultima_atualizacao": now.isoformat()
        }

    # Se auto, tenta extrair informações do ambiente
    if auto:
        # Tenta pegar session_id de variável de ambiente ou git
        session_id = session_id or os.environ.get("OPENCODE_SESSION_ID", "")
        if not session_id:
            try:
                result = subprocess.run(
                    ["opencode", "session", "list"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    # Primeira linha após cabeçalho é a mais recente
                    parts = lines[1].split()
                    if parts:
                        session_id = parts[0]
            except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
                pass

        if not titulo:
            # Tenta extrair do último checkout de mensagem
            titulo = f"Sessão autônoma - {now.strftime('%d/%m/%Y %H:%M')}"

        if not ultimo_prompt:
            ultimo_prompt = "(salvamento automático)"

        # Tenta pegar arquivos alterados do git
        if not arquivos:
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--cached"],
                    capture_output=True, text=True, cwd=BASE_DIR, timeout=5
                )
                if result.stdout.strip():
                    arquivos = result.stdout.strip().split("\n")
                else:
                    result = subprocess.run(
                        ["git", "diff", "--name-only"],
                        capture_output=True, text=True, cwd=BASE_DIR, timeout=5
                    )
                    if result.stdout.strip():
                        arquivos = result.stdout.strip().split("\n")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    # Atualiza campos fornecidos
    if session_id:
        data["ultima_sessao"] = session_id
    if titulo:
        data["titulo"] = titulo
    if ultimo_prompt:
        data["ultimo_prompt"] = ultimo_prompt
    if tarefa:
        data["tarefa_andamento"] = tarefa
    if decisoes:
        data["decisoes"] = decisoes
    if arquivos:
        # Deduplica mantendo ordem
        vistos = set()
        unicos = []
        for a in arquivos:
            if a not in vistos:
                vistos.add(a)
                unicos.append(a)
        data["arquivos_alterados"] = unicos
    if proximos:
        data["proximos_passos"] = proximos

    data["ultima_atualizacao"] = now.isoformat()
    data["status"] = "in_progress"

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[CHECKPOINT] Salvo em {CHECKPOINT_PATH}")
    return data


def clear():
    """Marca checkpoint como completado."""
    _ensure_dir()
    data = load()
    if data.get("status") in ("not_found", "corrupted"):
        print("[CHECKPOINT] Nenhum checkpoint ativo para limpar.")
        return

    data["status"] = "completed"
    data["tarefa_andamento"] = ""
    data["ultima_atualizacao"] = _now_brt()

    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[CHECKPOINT] Marcado como concluído.")
    print(f"  Última sessão: {data.get('ultima_sessao', 'N/A')}")
    print(f"  Título: {data.get('titulo', 'N/A')}")


def recover():
    """Tenta abrir a sessão do checkpoint no OpenCode."""
    data = load()
    status = data.get("status", "not_found")

    if status == "not_found":
        print("[CHECKPOINT] Nenhum checkpoint encontrado.")
        return

    if status == "completed":
        print("[CHECKPOINT] Última sessão já foi concluída:")
        print(f"  Título: {data.get('titulo', 'N/A')}")
        print(f"  Sessão: {data.get('ultima_sessao', 'N/A')}")
        print(f"  (use 'opencode -s {data.get('ultima_sessao', '')}' para reabrir)")
        return

    if status == "in_progress":
        session_id = data.get("ultima_sessao", "")
        titulo = data.get("titulo", "(sem título)")
        tarefa = data.get("tarefa_andamento", "")
        proximos = data.get("proximos_passos", [])

        print("=" * 60)
        print("  CHECKPOINT DE SESSÃO ENCONTRADO!")
        print("=" * 60)
        print(f"  Título: {titulo}")
        print(f"  Sessão: {session_id}")
        if tarefa:
            print(f"  Tarefa em andamento: {tarefa}")
        if proximos:
            print(f"  Próximos passos: {' | '.join(proximos[:3])}")
        if data.get("decisoes"):
            print(f"  Decisões tomadas: {len(data['decisoes'])}")
        print(f"  Última atualização: {data.get('ultima_atualizacao', 'N/A')}")
        print("=" * 60)

        if session_id:
            print(f"\n  Para continuar, execute:")
            print(f"    opencode -s {session_id}")
            print()
            try:
                answer = input("  Abrir automaticamente? [s/N] ").strip().lower()
                if answer in ("s", "sim"):
                    subprocess.run(["opencode", "-s", session_id], cwd=BASE_DIR)
            except (KeyboardInterrupt, EOFError):
                print()
                pass

        return data

    if status == "corrupted":
        print("[CHECKPOINT] Arquivo de checkpoint corrompido.")
        print(f"  Caminho: {CHECKPOINT_PATH}")
        print("  Delete ou edite manualmente para corrigir.")
        return


def cmd_abandon():
    """Marca checkpoint como abandonado."""
    _ensure_dir()
    data = load()
    if data.get("status") in ("not_found", "corrupted"):
        print("[CHECKPOINT] Nenhum checkpoint ativo.")
        return

    data["status"] = "abandoned"
    data["ultima_atualizacao"] = _now_brt()
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[CHECKPOINT] Marcado como abandonado.")
    print(f"  Sessão: {data.get('ultima_sessao', 'N/A')}")


def show():
    """Mostra o estado atual do checkpoint."""
    data = load()
    status = data.get("status", "not_found")

    print("=" * 50)
    print("  SESSION CHECKPOINT")
    print("=" * 50)

    if status == "not_found":
        print("  Nenhum checkpoint salvo.")
    elif status == "corrupted":
        print("  [AVISO] Arquivo corrompido!")
    else:
        icons = {
            "in_progress": "[Em andamento]",
            "completed": "[Concluido]",
            "abandoned": "[Abandonado]",
        }
        print(f"  Status: {icons.get(status, status)}")
        print(f"  Título: {data.get('titulo', 'N/A')}")
        print(f"  Sessão ID: {data.get('ultima_sessao', 'N/A')}")
        if data.get("tarefa_andamento"):
            print(f"  Tarefa: {data['tarefa_andamento']}")
        if data.get("ultimo_prompt"):
            p = data["ultimo_prompt"][:80]
            print(f"  Último prompt: {p}{'...' if len(data['ultimo_prompt']) > 80 else ''}")
        if data.get("decisoes"):
            print(f"  Decisões ({len(data['decisoes'])}):")
            for d in data["decisoes"][:3]:
                print(f"    • {d[:80]}")
        if data.get("arquivos_alterados"):
            print(f"  Arquivos alterados ({len(data['arquivos_alterados'])}):")
            for a in data["arquivos_alterados"][:5]:
                print(f"    • {a}")
        if data.get("proximos_passos"):
            print(f"  Próximos passos:")
            for p in data["proximos_passos"][:3]:
                print(f"    • {p}")
        print(f"  Última atualização: {data.get('ultima_atualizacao', 'N/A')}")

    print(f"\n  Arquivo: {CHECKPOINT_PATH}")
    print("=" * 50)
    return data


def main():
    if len(sys.argv) < 2:
        show()
        return

    command = sys.argv[1]

    if command == "save":
        auto = "--auto" in sys.argv
        if auto:
            # Extrai session_id da posicao depois de --auto
            session_id = ""
            for i, arg in enumerate(sys.argv):
                if arg == "--auto" and i + 1 < len(sys.argv) and not sys.argv[i+1].startswith("--"):
                    session_id = sys.argv[i+1]
                    break
            save(
                session_id=session_id,
                auto=True
            )
        else:
            # Modo interativo
            print("[CHECKPOINT] Salvando checkpoint interativo...")
            print("  (deixe em branco para pular)")
            try:
                session_id = input("  Session ID: ").strip()
                titulo = input("  Título: ").strip()
                tarefa = input("  Tarefa em andamento: ").strip()
                save(
                    session_id=session_id,
                    titulo=titulo or None,
                    tarefa=tarefa or None,
                )
            except (KeyboardInterrupt, EOFError):
                print("\n[CHECKPOINT] Cancelado.")

    elif command == "clear":
        clear()

    elif command == "recover":
        recover()

    elif command == "abandon":
        cmd_abandon()

    elif command == "path":
        print(CHECKPOINT_PATH)

    elif command == "show":
        show()

    else:
        print(f"[ERRO] Comando desconhecido: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
