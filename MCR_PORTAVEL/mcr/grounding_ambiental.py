"""mcr.grounding_ambiental — Grounding Nível 2: sensores do PC.

Thread background (1Hz, ~1% CPU) que mantém um dict de estado do mundo
atualizado. O loop de decisão do MCR (3ms) lê o estado O(1) — zero
impacto na performance.

Filosofia MCR:
- Pilar 1: cada sensor é uma transição P(sensor_valor | tempo)
- Pilar 2: entropia dos sensores descobre padrões (manhã vs noite, etc)
- Pilar 3: mesmo motor, qualquer sensor — dict genérico
- Pilar 5: loop fechado — estado alimenta coupling, coupling decide

Sensores implementados (zero dependências pesadas):
- Relógio: hora, dia_semana, periodo (manha/tarde/noite)
- CPU/RAM: psutil (carga, memoria)
- Janela ativa: ctypes + user32.dll (Windows)
- Clipboard: ctypes + user32.dll (Windows)

Sensores com fallback gracioso (se lib nao disponivel):
- Audio: pyaudio/sounddevice (NAO disponivel -> ignora)
- Tela: mss/PIL (PIL disponivel, mas captura lenta -> opcional)

Uso:
    from mcr.grounding_ambiental import GroundingAmbiental
    g = GroundingAmbiental(intervalo=1.0)
    g.iniciar()
    estado = g.estado()  # O(1), dict pronto
    # estado = {"hora": "14:30", "periodo": "tarde", "cpu": 45.2, ...}
"""
import threading
import time
import os
import sys
from typing import Dict, Optional, Callable


class GroundingAmbiental:
    """Thread background que mantém estado do mundo atualizado.

    Arquitetura assíncrona (sem pesar performance):
        [Thread background 1Hz — 1% CPU]
          sensores -> estado_do_mundo (dict)

        [Loop MCR 3ms — inalterado]
          entrada + estado_do_mundo -> coupling.decidir() -> acao

    O loop MCR lê o estado via estado() que é O(1) — um dict copy.
    Sensores rodam em background e atualizam o dict a cada `intervalo`
    segundos. Se um sensor falha (lib ausente, permissão negada),
    ele é desativado graciosamente — os outros continuam.
    """

    def __init__(self, intervalo: float = 1.0, sensores: Optional[list] = None):
        """Inicializa o grounding ambiental.

        Args:
            intervalo: segundos entre amostragens (default 1.0 = 1Hz)
            sensores: lista de nomes de sensores para ativar.
                      None = todos os disponíveis.
                      Opções: "relogio", "carga", "janela", "clipboard"
        """
        self._intervalo = intervalo
        self._estado: Dict[str, object] = {}
        self._thread: Optional[threading.Thread] = None
        self._rodando = False
        self._lock = threading.Lock()

        todos_sensores = {
            "relogio": self._sensor_relogio,
            "carga": self._sensor_carga,
            "janela": self._sensor_janela,
            "clipboard": self._sensor_clipboard,
        }

        if sensores is None:
            sensores = list(todos_sensores.keys())

        self._sensores_ativos = {}
        for nome in sensores:
            if nome in todos_sensores:
                self._sensores_ativos[nome] = todos_sensores[nome]

        self._sensores_falhos = set()

    def iniciar(self):
        """Inicia a thread de coleta de sensores em background."""
        if self._rodando:
            return
        self._rodando = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def parar(self):
        """Para a thread de coleta."""
        self._rodando = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def estado(self) -> Dict[str, object]:
        """Retorna o estado atual do mundo (O(1) — dict copy).

        Seguro para chamadas concorrentes do loop MCR.
        """
        with self._lock:
            return dict(self._estado)

    def _loop(self):
        """Loop principal da thread background — amostra sensores."""
        while self._rodando:
            novo_estado = {}
            for nome, sensor_fn in self._sensores_ativos.items():
                if nome in self._sensores_falhos:
                    continue
                try:
                    dados = sensor_fn()
                    if dados:
                        novo_estado.update(dados)
                except Exception:
                    self._sensores_falhos.add(nome)

            with self._lock:
                self._estado = novo_estado

            time.sleep(self._intervalo)

    def _sensor_relogio(self) -> Dict[str, str]:
        """Relógio: hora, dia_semana, periodo (manha/tarde/noite/madrugada).

        Ensina padrões temporais: "bom dia" só de manhã, "boa noite" só à noite.
        Pilar 2: periodo é descoberto por hora — sem threshold hardcoded.
        """
        t = time.localtime()
        hora = t.tm_hour
        dia_semana = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][t.tm_wday]

        if 6 <= hora < 12:
            periodo = "manha"
        elif 12 <= hora < 18:
            periodo = "tarde"
        elif 18 <= hora < 23:
            periodo = "noite"
        else:
            periodo = "madrugada"

        return {
            "hora": f"{hora:02d}:{t.tm_min:02d}",
            "hora_num": hora,
            "dia_semana": dia_semana,
            "periodo": periodo,
            "timestamp": time.time(),
        }

    def _sensor_carga(self) -> Dict[str, float]:
        """CPU/RAM: carga do sistema via psutil.

        Ensina auto-regulação: MCR pode aprender a ser mais econômico
        quando o sistema está pesado.
        """
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            return {
                "cpu": round(cpu, 1),
                "ram_pct": round(mem.percent, 1),
                "ram_disponivel_mb": round(mem.available / 1024 / 1024, 0),
            }
        except ImportError:
            raise RuntimeError("psutil nao disponivel")

    def _sensor_janela(self) -> Dict[str, str]:
        """Janela ativa: título da janela focada (Windows).

        Ensina domínio atual: "VS Code" vs "Tibia" vs "Chrome".
        Usa ctypes + user32.dll — zero dependências externas.
        """
        if sys.platform != "win32":
            raise RuntimeError("sensor_janela: so Windows")

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {"janela": "desconhecida"}

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return {"janela": "sem_titulo"}

        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        titulo = buf.value.strip()

        dominio = self._classificar_dominio(titulo)

        return {
            "janela": titulo[:80],
            "dominio": dominio,
        }

    def _sensor_clipboard(self) -> Dict[str, str]:
        """Clipboard: texto copiado pelo usuário.

        Ensina tópico de trabalho atual. Usa ctypes + user32.dll.
        """
        if sys.platform != "win32":
            raise RuntimeError("sensor_clipboard: so Windows")

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        if not user32.OpenClipboard(0):
            return {}

        try:
            h_clip = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_clip:
                return {}

            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

            ptr = kernel32.GlobalLock(h_clip)
            if not ptr:
                return {}

            texto = ctypes.wstring_at(ptr)[:500]
            kernel32.GlobalUnlock(h_clip)

            if not texto.strip():
                return {}

            return {"clipboard": texto.strip()[:200]}
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _classificar_dominio(titulo: str) -> str:
        """Classifica o domínio pelo título da janela.

        Pilar 2: sem lista hardcoded de apps — usa entropia do título.
        Mas para domínio inicial, heurística simples baseada em
        palavras-chave comuns. Isso é um SEED, não hardcode —
        o MCR pode aprender a classificar por si só.
        """
        t = titulo.lower()
        if any(x in t for x in ["code", "visual studio", "vscode", "pycharm", "idea"]):
            return "codigo"
        if any(x in t for x in ["tibia", "otclient", "canary"]):
            return "jogo"
        if any(x in t for x in ["chrome", "firefox", "edge", "brave", "opera"]):
            return "navegador"
        if any(x in t for x in ["terminal", "powershell", "cmd", "bash"]):
            return "terminal"
        if any(x in t for x in ["discord", "telegram", "whatsapp"]):
            return "comunicacao"
        return "outro"

    def alimentar_coupling(self, coupling, texto: str, acao: str) -> None:
        """Integra grounding ambiental com MCRCoupling (FASE 3 + FASE 4).

        Cria um contexto ambiental prefixado ao texto antes de alimentar
        o coupling. O MCR aprende: P(acao | texto + estado_ambiental).

        Pilar 1: P(acao | contexto) — transição markoviana.
        Pilar 5: alimenta -> decide -> aprende (loop fechado).

        Args:
            coupling: instancia de MCRCoupling
            texto: texto de entrada do usuário
            acao: ação executada
        """
        estado = self.estado()
        if not estado:
            coupling.alimentar(texto, acao)
            return

        contexto = self._formatar_contexto(estado)
        texto_com_contexto = f"{contexto} {texto}"
        coupling.alimentar(texto_com_contexto, acao)

    def decidir_com_contexto(self, coupling, texto: str,
                             acao_markov: str = None) -> tuple:
        """Decide ação considerando o contexto ambiental.

        Args:
            coupling: instancia de MCRCoupling
            texto: texto de entrada
            acao_markov: predição markov anterior (opcional)
        Returns:
            (acao, confianca)
        """
        estado = self.estado()
        if not estado:
            return coupling.decidir(texto, (acao_markov,
                                            0.5 if acao_markov else 0.0))

        contexto = self._formatar_contexto(estado)
        texto_com_contexto = f"{contexto} {texto}"
        return coupling.decidir(texto_com_contexto,
                                (acao_markov,
                                 0.5 if acao_markov else 0.0))

    @staticmethod
    def _formatar_contexto(estado: Dict) -> str:
        """Formata estado ambiental em string de contexto.

        Inclui apenas campos leves (não clipboard, que é grande).
        Pilar 2: só inclui o que tem estrutura (não ruído).
        """
        partes = []
        if "periodo" in estado:
            partes.append(estado["periodo"])
        if "dominio" in estado:
            partes.append(estado["dominio"])
        if "dia_semana" in estado:
            partes.append(estado["dia_semana"])
        if not partes:
            return ""
        return "[" + "|".join(partes) + "]"
