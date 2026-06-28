"""Modulo: Watchdog - Monitora comandos/ + sandbox/ para auto-revisao.
- Hot-reload de comandos quando comandos/ muda
- Auto-revisao de respostas quando sandbox/ muda
"""
import os, time, threading

def init_module(contexto):
    kernel = contexto.get('kernel')
    if kernel:
        w = Watchdog(kernel)
        w.start()
        contexto['watchdog'] = w
        return 'watchdog', w
    return None, None


class Watchdog:
    """Monitora comandos/ + sandbox/. Auto-revisa respostas no sandbox."""
    
    def __init__(self, kernel, intervalo=5.0):
        self.kernel = kernel
        self.intervalo = intervalo
        self._dir_mtime = 0
        self._sandbox_mtime = {}
        self._auto_revisor = None
        self._indice = {}  # Indice invertido para ContextCrew
        self._rodando = False
        self._thread = None
        # Tenta carregar auto_revisor
        try:
            from modulos.auto_revisor import AutoRevisor
            kg = kernel.contexto.get('kg') if kernel else None
            self._auto_revisor = AutoRevisor(kg=kg)
        except:
            pass
    
    def start(self):
        self._rodando = True
        self._dir_mtime = self._get_dir_mtime()
        self._scan_sandbox()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f'[Watchdog] Monitorando comandos/ + sandbox/ ({self.intervalo:.0f}s)')
    
    def stop(self):
        self._rodando = False
    
    def _get_dir_mtime(self):
        cmd_dir = self.kernel.loader.cmd_dir if self.kernel else None
        if not cmd_dir or not os.path.isdir(cmd_dir):
            return 0
        try:
            return os.path.getmtime(cmd_dir)
        except:
            return 0
    
    def _scan_sandbox(self):
        """Escaneia sandbox/ e registra mtimes de arquivos .txt (respostas)."""
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        sandbox_dir = os.path.join(base, 'sandbox')
        if not os.path.isdir(sandbox_dir):
            return
        for root, dirs, files in os.walk(sandbox_dir):
            for f in files:
                if f.endswith('.txt') and 'resposta' in root.lower() or 'mega' in f:
                    fpath = os.path.join(root, f)
                    try:
                        self._sandbox_mtime[fpath] = os.path.getmtime(fpath)
                    except:
                        pass
    
    def _revisar_arquivo(self, fpath):
        """Revisa um arquivo de resposta em busca de alucinacoes."""
        if not self._auto_revisor:
            return
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                texto = f.read()
            if len(texto) < 100:
                return
            resultado = self._auto_revisor.revisar(texto)
            if resultado["total"] > 0:
                print(f'[Watchdog] Auto-revisao de {os.path.basename(fpath)}: {resultado["total"]} alucinacoes')
        except:
            pass
    
    def _loop(self):
        """Monitora comandos/ + sandbox/ em paralelo."""
        while self._rodando:
            if not self._indice:
                self._atualizar_indice()
            time.sleep(self.intervalo)
            
            # 1. Hot-reload de comandos
            novo_mtime = self._get_dir_mtime()
            if novo_mtime != self._dir_mtime:
                self._dir_mtime = novo_mtime
                if self.kernel:
                    n = self.kernel.loader.refresh()
                    if n > 0:
                        print(f'[Watchdog] Hot-reload: {n} comandos')
            
            # 2. Auto-revisao de respostas no sandbox
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            sandbox_dir = os.path.join(base, 'sandbox')
            if os.path.isdir(sandbox_dir):
                for root, dirs, files in os.walk(sandbox_dir):
                    for f in files:
                        if f.endswith('.txt') and ('resposta' in root.lower() or 'mega' in f):
                            fpath = os.path.join(root, f)
                            try:
                                mtime_atual = os.path.getmtime(fpath)
                                if fpath not in self._sandbox_mtime:
                                    self._sandbox_mtime[fpath] = mtime_atual
                                    self._revisar_arquivo(fpath)
                                elif mtime_atual != self._sandbox_mtime[fpath]:
                                    self._sandbox_mtime[fpath] = mtime_atual
                                    self._revisar_arquivo(fpath)
                            except:
                                pass
