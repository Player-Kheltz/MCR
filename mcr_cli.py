#!/usr/bin/env python
"""mcr_cli.py — CLI leve do MCR, estilo OpenCode.

Substitui o sse_server.py (HTTP+HTML+threading, quebrado).
Layout terminal:
  [header] — estado do MCR, consentimento, stats rapidas
  [conversa] — dialogo humano ↔ MCR
  [pensamento] — painel inferior ao vivo (EventoPensamento do triunvirato)
  [input] — > prompt, captura timing de teclas (se consentido)

Multiplataforma: Windows + Linux (deteccao automatica de OS).
Sem dependencia pesada: stdlib + rich (opcional, fallback texto puro).

Comandos:
  /pensamento — historico de deliberacoes
  /estado     — estatisticas do MCR
  /reset      — reinicia perfil humano
  /sair       — encerra sessao
  /ajuda      — lista comandos

Uso:
  python mcr_cli.py
"""
import sys
import os
import time
import threading
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── Rich (opcional) ────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.table import Table
    from rich import box
    _RICH = True
except ImportError:
    _RICH = False

# ─── MCR ────────────────────────────────────────────────────────
from mcr.coupling import MCRCoupling
from mcr.chat import MCRChat
from mcr.perfil_humano import PerfilHumano
from mcr.coldstart import Coldstart


class MCRCLI:
    """CLI leve do MCR — terminal interativo."""

    def __init__(self):
        self._coupling = MCRCoupling()
        self._coupling.load()
        self._perfil = PerfilHumano()
        self._coldstart = Coldstart()
        self._coldstart.vincular_perfil(self._perfil)
        self._chat = MCRChat(self._coupling, self._perfil, self._coldstart)

        # Fix 5: carregar sessao anterior
        import os
        base = os.path.dirname(os.path.abspath(__file__))
        self._sessao_dir = os.path.join(base, 'cache')
        self._caminho_perfil = os.path.join(self._sessao_dir, 'mcr_perfil.json')
        self._caminho_coldstart = os.path.join(self._sessao_dir, 'mcr_coldstart.json')
        self._caminho_sessao = os.path.join(self._sessao_dir, 'mcr_sessao.json')
        self._carregar_sessao()

        self._running = True
        self._ultima_tecla_ts = time.time()
        self._input_buffer = ""

        if _RICH:
            self._console = Console()
        else:
            self._console = None

    def _carregar_sessao(self):
        """Fix 5: carrega perfil e coldstart de sessao anterior."""
        carregou = False
        if self._perfil.load(self._caminho_perfil):
            carregou = True
        if self._coldstart.load(self._caminho_coldstart):
            carregou = True
        if self._chat.carregar(self._caminho_sessao):
            carregou = True
        return carregou

    def _salvar_sessao(self):
        """Fix 5: salva perfil e coldstart ao encerrar."""
        self._perfil.save(self._caminho_perfil)
        self._coldstart.save(self._caminho_coldstart)
        self._chat.salvar(self._caminho_sessao)

    # ─── Loop principal ─────────────────────────────────────────

    def run(self):
        self._mostrar_header()

        # Se coldstart ja completo (sessao anterior), inicializar conhecimento
        if not self._chat.em_coldstart:
            n_fatos = self._chat.inicializar_conhecimento()
            if n_fatos > 0 and _RICH:
                self._console.print(f"[dim]conhecimento base: {n_fatos} fatos ingeridos[/]")

        # Iniciar coldstart
        msg = self._chat.iniciar()
        self._print_mcr(msg)

        while self._running:
            try:
                entrada = self._ler_entrada()
                if entrada is None:
                    continue
                if not entrada.strip():
                    continue

                # Comandos
                if entrada.startswith('/'):
                    self._processar_comando(entrada)
                    continue

                # Registrar timing no perfil
                delta = time.time() - self._ultima_tecla_ts
                if self._perfil.consentido():
                    self._perfil.registrar_resposta(entrada, self._chat._complexidade_contexto())
                    self._perfil.registrar_decisao(entrada)
                self._ultima_tecla_ts = time.time()

                # Interagir
                t0 = time.time()
                estava_coldstart = self._chat.em_coldstart
                resposta = self._chat.interagir(entrada)
                dt = time.time() - t0
                self._print_mcr(resposta, dt)

                # Detectar transicao coldstart → chat
                if estava_coldstart and not self._chat.em_coldstart:
                    n_fatos = self._chat.inicializar_conhecimento()
                    if n_fatos > 0:
                        self._print_mcr(f"(conhecimento base ingerido: {n_fatos} fatos)")

                self._mostrar_pensamento()

            except KeyboardInterrupt:
                self._print_mcr("ate logo! (Ctrl+C)")
                break
            except EOFError:
                break

        self._encerrar()

    # ─── Input ──────────────────────────────────────────────────

    def _ler_entrada(self) -> Optional[str]:
        if _RICH:
            self._console.print("", end="")
        try:
            return input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

    # ─── Comandos ───────────────────────────────────────────────

    def _processar_comando(self, cmd: str):
        c = cmd.lower().strip()
        if c == '/sair':
            self._print_mcr("encerrando sessao...")
            self._running = False
        elif c == '/estado':
            est = self._chat.estado()
            self._mostrar_estado(est)
        elif c == '/pensamento':
            self._mostrar_pensamento()
        elif c == '/reset':
            self._perfil = PerfilHumano()
            self._coldstart = Coldstart()
            self._coldstart.vincular_perfil(self._perfil)
            self._chat = MCRChat(self._coupling, self._perfil, self._coldstart)
            self._print_mcr("perfil reiniciado. nova sessao.")
        elif c in ('/ajuda', '/help'):
            self._print_mcr(
                "comandos: /pensamento /estado /reset /sair /ajuda"
            )
        else:
            self._print_mcr(f"comando desconhecido: {c}")

    # ─── Exibicao ───────────────────────────────────────────────

    def _mostrar_header(self):
        est = self._chat.estado()
        obs = est.get('observacoes', 0)
        pal = est.get('palavras', 0)
        cons = est.get('consentido', False)
        l = 'LGPD:OK' if cons else 'LGPD:---'

        if _RICH:
            t = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            t.add_column(style="bold cyan")
            t.add_column()
            t.add_column(style="dim")
            t.add_row(
                "MCR", f"obs={obs} palavras={pal}",
                f"{l}",
            )
            self._console.print(t)
        else:
            print(f"[MCR] obs={obs} palavras={pal} {l}")
            print()

    def _print_mcr(self, texto: str, latencia: float = 0.0):
        lat = f" [{latencia:.0f}ms]" if latencia > 1 else ""
        if _RICH:
            self._console.print(f"[bold green]MCR{lat}[/] {texto}")
        else:
            print(f"MCR{lat}: {texto}")

    def _mostrar_pensamento(self):
        delib = self._coupling._deliberacao
        if not delib:
            return
        eventos = delib.eventos_recentes(5)
        if not eventos:
            return

        if _RICH:
            t = Table(title="pensamento", show_header=True,
                      box=box.SIMPLE, padding=(0, 1),
                      title_style="dim")
            t.add_column("fonte", style="yellow")
            t.add_column("contribuicao", style="dim")
            t.add_column("score", justify="right")
            t.add_column("ms", justify="right", style="dim")
            for e in eventos[-3:]:
                t.add_row(
                    e.fonte,
                    e.contribuicao[:40],
                    f"{e.score:.2f}",
                    f"{e.duracao_ms:.0f}",
                )
            self._console.print(t)
        else:
            print("  [pensamento]")
            for e in eventos[-3:]:
                print(f"    {e.fonte}: {e.contribuicao[:50]} "
                      f"(score={e.score:.2f}, {e.duracao_ms:.0f}ms)")

    def _mostrar_estado(self, est: dict):
        if _RICH:
            t = Table(title="estado MCR", box=box.SIMPLE, padding=(0, 1),
                      title_style="bold cyan")
            t.add_column("chave", style="bold")
            t.add_column("valor")
            for k, v in est.items():
                t.add_row(k, str(v))
            self._console.print(t)
        else:
            print("[estado]")
            for k, v in est.items():
                print(f"  {k}: {v}")

    # ─── Encerramento ───────────────────────────────────────────

    def _encerrar(self):
        # Fix 5: salvar sessao
        self._salvar_sessao()
        if self._perfil.consentido():
            perfil = self._perfil.to_dict()
            if _RICH:
                self._console.print(
                    f"\n[dim]sessao encerrada e salva. "
                    f"obs={perfil['total_observacoes']} "
                    f"H_teclas={perfil['entropia_teclas']} "
                    f"teto={perfil['teto_paciencia']}s[/]"
                )
            else:
                print(f"\nsessao encerrada e salva. obs={perfil['total_observacoes']} "
                      f"H_teclas={perfil['entropia_teclas']} "
                      f"teto={perfil['teto_paciencia']}s")
        else:
            if _RICH:
                self._console.print("\n[dim]sessao encerrada.[/]")
            else:
                print("\nsessao encerrada.")


def main():
    cli = MCRCLI()
    cli.run()


if __name__ == '__main__':
    main()
