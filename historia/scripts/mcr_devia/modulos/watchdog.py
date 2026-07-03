"""Watchdog — Monitora conversa para ContextInfinity + indice para ContextCrew.

Funcoes:
1. Indice invertido do codigo fonte para ContextCrew (cache em arquivo)
2. Monitora .mcr_conversa.jsonl para alimentar ContextInfinity

Removido: hot-reload de comandos (kernel ja carrega lazy), auto-revisao de
sandbox (nunca disparou), healthcheck da bridge (usuario gerencia manualmente).
"""
import os, time, threading, re, json as _jj


def init_module(contexto):
    kernel = contexto.get("kernel")
    if kernel:
        w = Watchdog(kernel)
        w.start()
        contexto["watchdog"] = w
        return "watchdog", w
    return None, None


class Watchdog:
    """Monitora .mcr_conversa.jsonl + mantem indice para ContextCrew."""
    
    def __init__(self, kernel, intervalo=10.0):
        self.kernel = kernel
        self.intervalo = intervalo
        self._indice = {}
        self._rodando = False
        self._thread = None
        self._conversa_mtime = 0
        self._BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._CONVERSA_PATH = os.path.join(self._BASE, 'sandbox', '.mcr_conversa.jsonl')
        self._INDICE_PATH = os.path.join(self._BASE, 'sandbox', '.mcr_devia', 'indice_watchdog.json')
    
    def consultar_indice(self, termo, max_r=5):
        """Consulta indice invertido. Retorna arquivos que contem o termo."""
        termo_lower = termo.lower()
        resultados = []
        for palavra, arquivos in self._indice.items():
            if termo_lower in palavra:
                for arq in arquivos:
                    if arq not in resultados:
                        resultados.append(arq)
        return resultados
    
    def _atualizar_indice(self):
        """Atualiza indice invertido e salva em arquivo para ContextCrew."""
        self._indice = {}
        dirs = [
            os.path.join(self._BASE, "scripts", "mcr_devia"),
            os.path.join(self._BASE, "sandbox"),
            os.path.join(self._BASE, "docs"),
        ]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for root, dirs2, files in os.walk(d):
                dirs2[:] = [x for x in dirs2 if not x.startswith(".") and x not in ("__pycache__","node_modules","vcpkg")]
                for f in files:
                    if not f.endswith((".py",".md",".txt",".json",".lua",".cpp",".h",".hpp")):
                        continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                            conteudo = fh.read()
                        palavras = set(re.findall(r"\b[a-zA-Z_]{3,}\b", conteudo.lower()))
                        for p in palavras:
                            if p not in self._indice:
                                self._indice[p] = []
                            if fpath not in self._indice[p]:
                                self._indice[p].append(fpath)
                    except Exception:
                        pass
        try:
            os.makedirs(os.path.dirname(self._INDICE_PATH), exist_ok=True)
            with open(self._INDICE_PATH, "w", encoding="utf-8") as f:
                _jj.dump(self._indice, f, ensure_ascii=False)
        except Exception:
            pass
    
    def _monitorar_conversa(self):
        """Monitora .mcr_conversa.jsonl para alimentar ContextInfinity.
        
        Se detecta mudanca, o ContextCrew pode re-indexar.
        """
        if not os.path.exists(self._CONVERSA_PATH):
            return
        try:
            mtime = os.path.getmtime(self._CONVERSA_PATH)
            if mtime != self._conversa_mtime:
                self._conversa_mtime = mtime
                # ContextInfinity ja le o .jsonl direto, so sinalizamos
                return True
        except Exception:
            pass
        return False
    
    def start(self):
        self._rodando = True
        self._atualizar_indice()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._rodando = False
    
    def _loop(self):
        """Monitora conversa em intervalo fixo. Re-gera indice a cada 5 min."""
        _ciclo = 0
        while self._rodando:
            time.sleep(self.intervalo)
            
            # Monitora conversa
            self._monitorar_conversa()
            
            # Re-gera indice a cada 30 ciclos (~5 min)
            _ciclo += 1
            if _ciclo >= 30:
                _ciclo = 0
                self._atualizar_indice()
