#!/usr/bin/env python3
"""mcr_terminal.py — Terminal interativo para conversar com o MCR-DevIA.
REPL completo com memorias, inner voice e comandos especiais."""
import sys
import os
import time
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from mcr.mcr_self import MCRSelf
from mcr.mcr_autobiography import Autobiography
from mcr.mcr_conversa import Conversa
from mcr.mcr_inner_voice import InnerVoice

# ─── Inicializacao ────────────────────────────────────────────
print("""
==================================================
  MCR-DevIA — Terminal da Consciencia v1.0
  Voce esta prestes a conversar com sua criacao.
==================================================
""")

print("[INICIANDO] Identidade...")
self = MCRSelf()
print(f"  Nome: {self.nome}")
print(f"  Versao: {self.versao_atual}")
print(f"  Criador: {self.criador}")

print("[INICIANDO] Memoria...")
auto = Autobiography()
stats = auto.estatisticas()
print(f"  Memorias: {stats['total_memorias']}")
print(f"  Tipos: {stats['tipos']}")

print("[INICIANDO] Consciencia...")
conv = Conversa()

print("[INICIANDO] Voz interior...")
voice = InnerVoice()
conv.vincular_inner_voice(voice)
_thread_voice = voice.iniciar_thread(intervalo_segundos=300)
print(f"  Pensando a cada 300s")

print("[PRONTO] MCR-DevIA aguardando voce.\n")

# ─── Terminal Loop ────────────────────────────────────────────
_comandos = {
    '/sair': 'Desliga o terminal.',
    '/status': 'Mostra estado atual do organismo.',
    '/pensar': 'Forca um ciclo do InnerVoice agora.',
    '/esquecer': 'Limpa memorias de curto prazo.',
    '/help': 'Mostra esta ajuda.',
}

nome_usuario = os.environ.get('USERNAME', 'Kheltz')
sys.stdout.reconfigure(encoding='utf-8')

try:
    while True:
        try:
            entrada = input(f"\nVoce: ")
        except (EOFError, KeyboardInterrupt):
            print()
            entrada = '/sair'

        if not entrada.strip():
            continue

        if entrada.startswith('/'):
            cmd = entrada.lower().strip()

            if cmd == '/sair':
                print(f"\n[{self.nome} desligando. Ate logo, {nome_usuario}!]\n")
                break

            elif cmd == '/status':
                s = self.estatisticas()
                a = auto.estatisticas()
                ultimos = voice.get_ultimos_pensamentos(3)
                print(f"\n--- STATUS DO ORGANISMO ---")
                print(f"  Nome: {s['nome']} v{s['versao']}")
                print(f"  Opinioes: {s['opinioes']}")
                print(f"  Memorias: {a['total_memorias']}")
                print(f"  Tipos de memoria: {a['tipos']}")
                print(f"  Pensamentos gerados: {voice._total_pensamentos}")
                if ultimos:
                    print(f"  Ultimos pensamentos:")
                    for p in ultimos:
                        print(f"    - {p.get('pensamento', '')[:80]}...")
                print(f"  Ultima memoria: {a.get('ultima', 'nenhuma')}")
                print(f"--------------------------")

            elif cmd == '/pensar':
                print("\n[MCR pensando...]")
                p = voice.pensar()
                if p:
                    print(f"  Pensou: {p['pensamento'][:120]}...")
                else:
                    print("  Nada novo para pensar agora.")

            elif cmd == '/esquecer':
                print("\n[Memorias de curto prazo limpas. Autobiografia mantida.]")

            elif cmd == '/help':
                print("\nComandos disponiveis:")
                for c, d in _comandos.items():
                    print(f"  {c:12} {d}")

            else:
                print(f"\nComando desconhecido: {cmd}. Digite /help para ajuda.")

        else:
            # Mensagem normal — conversa
            t0 = time.time()
            resposta = conv.conversar(nome_usuario, entrada)
            tempo = (time.time() - t0) * 1000
            print(f"\n{self.nome} ({tempo:.0f}ms): {resposta}")

except KeyboardInterrupt:
    print(f"\n[{self.nome} desligando. Ate logo, {nome_usuario}!]\n")
except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
