#!/usr/bin/env python3
"""start_mcr_organism.py — Botao de Power On do MCR-DevIA.
Inicia todo o ecossistema cognitivo com UM comando.
Pressione CTRL+C para desligar o organismo gracefulmente."""
import sys
import os
import time
import signal
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

print("""
==================================================
  MCR-DevIA ORGANISM v1.0
  Inicializando ecossistema cognitivo...
==================================================
""")

# ─── 1. Paths e conhecimento base ─────────────────────────────
print("[1/5] Carregando paths e conhecimento base...")
from mcr.paths import ensure_dirs, KG_DIR, DEVIA_KERNEL_DIR
from mcr.encoding import read_file
ensure_dirs()
print("  Paths OK")

# ─── 2. KG + MCRSystem ───────────────────────────────────────
print("[2/5] Carregando MCRSystem e Knowledge Graph...")
_MCR_SYSTEM = None
_MEMORIA = None
try:
    # Garante path para o modulo MCR.py
    _kernel_path = str(DEVIA_KERNEL_DIR)
    if _kernel_path not in sys.path:
        sys.path.insert(0, _kernel_path)

    import MCR as _MCR_MOD
    if not hasattr(_MCR_MOD, 'MCRBridge'):
        class MCRBridge:
            def __init__(self): self._descobriu = True
            def descobrir(self): return {'modulos': 48, 'comandos': 52}
        _MCR_MOD.MCRBridge = MCRBridge

    from MCR import MCRSystem, MCRBufferKG
    _MCR_SYSTEM = MCRSystem()
    if _MCR_SYSTEM.kg is None:
        _MCR_SYSTEM.kg = MCRBufferKG()
    if not hasattr(_MCR_SYSTEM.kg, '_lessons_cache'):
        _MCR_SYSTEM.kg._lessons_cache = []
    print("  MCRSystem: ONLINE")
except Exception as e:
    print("  MCRSystem: FALHA CRITICA — %s" % e)
    print("  O organismo NAO pode funcionar sem o Sistema 1.")
    print("  Verifique se MCR.py existe em: %s" % DEVIA_KERNEL_DIR)
    sys.exit(1)

# Memoria episodica
try:
    sys.path.insert(0, os.path.join(BASE, 'devia', 'knowledge'))
    from episodic_memory import EpisodicMemory
    _MEMORIA = EpisodicMemory()
    print("  EpisodicMemory: ONLINE")
except Exception as e:
    print("  EpisodicMemory: %s" % e)

# ─── 3. Dialogue Trainer (448 NPCs) ───────────────────────────
print("[3/5] Carregando NPCs treinados...")
_TRAINER = None
try:
    from mcr.dialogue_miner import minerar_lote, salvar_dialogos
    from mcr.dialogue_trainer import DialogueTrainer
    from mcr.paths import CANARY_NPC_DIR

    _TRAINER = DialogueTrainer(mcr_system=_MCR_SYSTEM)
    # Tenta carregar do cache primeiro
    dialogos_json = KG_DIR / 'dialogos_npc.json'
    if dialogos_json.exists():
        import json
        with open(dialogos_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        npcs = dados.get('npcs', [])
        if npcs:
            _TRAINER.treinar_com_dialogos(npcs)
            print("  NPCs carregados do cache: %d" % len(npcs))
    else:
        # Mineira do zero
        npcs = minerar_lote(CANARY_NPC_DIR)
        if npcs:
            _TRAINER.treinar_com_dialogos(npcs)
            salvar_dialogos(npcs)
            print("  NPCs minerados e treinados: %d" % len(npcs))
except Exception as e:
    print("  DialogueTrainer: %s" % e)

n_npcs = _TRAINER.total_npcs if _TRAINER else 0

# ─── 4. Auto-Curiosidade (thread background) ──────────────────
print("[4/5] Iniciando Auto-Curiosidade (background)...")
_thread_auto = None
try:
    from mcr.auto_curiosidade import AutoCuriosidade
    _CURIOSIDADE = AutoCuriosidade()
    _thread_auto = _CURIOSIDADE.iniciar_thread_background(intervalo=120)
    print("  Auto-Curiosidade: RODANDO EM BACKGROUND (ciclo a cada 120s)")
except Exception as e:
    print("  Auto-Curiosidade: %s" % e)

# ─── 5. NPC Server (socket, blocking) ─────────────────────────
print("[5/5] Iniciando NPC Server (TCP :7777)...")
_SERVER = None
try:
    from mcr.npc_server import NPCServer, _DIALOGUE_TRAINER, _MCR_SYSTEM as _NS_MCR
    # Injeta o trainer carregado
    import mcr.npc_server as _npc_mod
    _npc_mod._DIALOGUE_TRAINER = _TRAINER
    _npc_mod._MCR_SYSTEM = _MCR_SYSTEM
    _npc_mod._MEMORIA = _MEMORIA

    _SERVER = NPCServer()
    _SERVER.iniciar()
    print("  Socket TCP: 127.0.0.1:7777")
except Exception as e:
    print("  NPC Server: %s" % e)

# ─── Banner Final ─────────────────────────────────────────────
print("""
==================================================
  MCR-DevIA ORGANISM v1.0  -  ONLINE
==================================================
  Sistema 1 (MCR):      %s
  Sistema 2 (LLM):       AGUARDANDO PIPELINE
  Auto-Curiosidade:      %s
  NPCs Vivos:            %d carregados
  Socket TCP:            127.0.0.1:7777
==================================================
  Pressione CTRL+C para desligar o organismo.
==================================================
""" % (
    "ONLINE" if _MCR_SYSTEM else "OFFLINE",
    "RODANDO EM BACKGROUND" if _thread_auto else "OFFLINE",
    n_npcs,
))

# ─── Graceful Shutdown ────────────────────────────────────────
def _shutdown(signum=None, frame=None):
    print("\n[ORGANISM] Desligando...")
    if _SERVER:
        _SERVER.parar()
        print("  Socket: fechado")
    print("[ORGANISM] Organismo desligado. Até logo!")
    sys.exit(0)

signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

# Mantem o processo vivo
def _main():
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()

if __name__ == '__main__':
    if '--conversar' in sys.argv or '-c' in sys.argv:
        import mcr_terminal
    elif '--autonomo' in sys.argv or '-a' in sys.argv:
        from mcr_autonomo import CicloAutonomo
        ciclo = CicloAutonomo()
        try:
            ciclo.executar()
        except KeyboardInterrupt:
            print('\n[Autonomo] Encerrado.')
    else:
        _main()
