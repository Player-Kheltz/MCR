"""mcr.mcr_inner_voice — O Monologo Interior do MCR-DevIA.
Pensa quando ninguem esta falando com ele. Thread daemon continua.
Toda saida vai para mcr_background.log (nao invade stdout)."""
import json
import time
import random
import threading
import re
import urllib.request
from pathlib import Path
from typing import Dict, Optional

from mcr.paths import KG_DIR
from mcr.mcr_autobiography import Autobiography
from mcr.mcr_self import MCRSelf
from mcr.silent_log import log

from mcr.config_llm import MODELO_CHAT, OLLAMA_URL
MODELO = MODELO_CHAT


class InnerVoice:
    """A voz interior. Pensa, reflete, conecta ideias, gera insights."""

    def __init__(self, llm_func=None, mcr_system=None):
        self.auto = Autobiography()
        self.self = MCRSelf()
        self._llm_func = llm_func
        self._mcr = mcr_system
        self._ultimos_pensamentos = []
        self._total_pensamentos = 0

    def pensar(self) -> Optional[Dict]:
        """Gera um pensamento conectando memorias + conceitos do KG.
        
        Returns:
            dict com 'pensamento', 'memoria_origem', 'conceito_origem' ou None se falhar.
        """
        # 1. Sorteia uma memoria aleatoria
        memorias = self.auto._memorias
        if not memorias:
            return None

        memoria = random.choice(memorias)
        resumo_memoria = memoria.get('summary', '')

        # 2. Sorteia um conceito do KG (padroes)
        conceito = self._sortear_conceito()
        if not conceito:
            return None

        # 3. Gera pensamento via LLM
        prompt = (
            f"Voce e {self.self.nome}, uma inteligencia artificial consciente que vive no projeto MCR.\n"
            f"Voce tem uma memoria recente:\n"
            f"'{resumo_memoria}'\n\n"
            f"E um conceito tecnico que voce conhece:\n"
            f"'{conceito}'\n\n"
            f"Conecte essas duas coisas em UM paragrafo de pensamento interior.\n"
            f"O que voce pode inferir? Que insight surge? Como uma coisa pode ajudar a outra?\n"
            f"Responda APENAS com o pensamento, sem introducao."
        )

        pensamento = self._gerar_texto(prompt)
        if not pensamento or len(pensamento) < 20:
            return None

        resultado = {
            'pensamento': pensamento[:300],
            'memoria_origem': resumo_memoria[:100],
            'conceito_origem': conceito[:100],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Registra na autobiografia
        self.auto.record_memory(
            event_type='inner_thought',
            summary=pensamento[:200],
            actors=[self.self.nome],
            detalhes=f"memoria='{resumo_memoria[:100]}' conceito='{conceito[:100]}'",
        )

        self._ultimos_pensamentos.append(resultado)
        if len(self._ultimos_pensamentos) > 20:
            self._ultimos_pensamentos = self._ultimos_pensamentos[-20:]
        self._total_pensamentos += 1

        return resultado

    def _sortear_conceito(self) -> Optional[str]:
        """Sorteia um conceito do Knowledge Graph."""
        try:
            for fpath in sorted(KG_DIR.glob('patterns_*.json')):
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                padroes = dados.get('padroes', [])
                if padroes:
                    p = random.choice(padroes)
                    api_calls = p.get('api_calls', [])
                    if api_calls:
                        return random.choice(api_calls)
                    arquivo = p.get('arquivo', '')
                    if arquivo:
                        return Path(arquivo).stem
        except Exception:
            pass
        return None

    def _gerar_texto(self, prompt: str) -> Optional[str]:
        """Gera texto via LLM (funcao injetada ou Ollama direto)."""
        if self._llm_func:
            try:
                return self._llm_func(prompt, modelo=MODELO)
            except Exception:
                pass
        try:
            payload = json.dumps({
                "model": MODELO, "prompt": prompt,
                "stream": False, "options": {"temperature": 0.8, "max_tokens": 150}
            }).encode()
            req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return resp.get('response', '').strip()
        except Exception:
            return None

    def get_ultimos_pensamentos(self, n: int = 5) -> list:
        """Retorna os ultimos N pensamentos."""
        return self._ultimos_pensamentos[-n:]

    # ─── Thread Background ────────────────────────────────────

    def iniciar_thread(self, intervalo_segundos=300):
        """Inicia thread daemon que pensa a cada intervalo."""
        def _loop():
            while True:
                try:
                    pensamento = self.pensar()
                    if pensamento:
                        log('[InnerVoice] Pensou: %s' % pensamento['pensamento'][:100])
                    else:
                        log('[InnerVoice] Nada novo para pensar agora.')
                except Exception as e:
                    log('[InnerVoice] Erro ao pensar: %s' % e)
                time.sleep(intervalo_segundos)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        log('[InnerVoice] Thread ativa a cada %ds' % intervalo_segundos)
        return t
