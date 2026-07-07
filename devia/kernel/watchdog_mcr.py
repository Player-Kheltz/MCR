"""watchdog_mcr.py — monitora mudancas no projeto em background."""
import os, time, threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROJETO = r"E:\Projeto MCR"

class MCRFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.ultimas_mudancas = []
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if any(p in event.src_path for p in ['__pycache__', '.git', 'vcpkg', 'node_modules', 'bin', 'obj']):
            return
        self.ultimas_mudancas.append({
            'path': event.src_path,
            'tipo': 'modified',
            'time': time.time(),
        })
        # Mantem so as ultimas 50
        if len(self.ultimas_mudancas) > 50:
            self.ultimas_mudancas = self.ultimas_mudancas[-50:]
    
    def on_created(self, event):
        self.on_modified(event)
    
    def on_deleted(self, event):
        self.on_modified(event)
    
    def ultimos_eventos(self, n=5):
        return self.ultimas_mudancas[-n:][::-1]

class WatchdogMCR:
    """Monitora projeto em background. Dispara callbacks em mudancas."""
    
    def __init__(self, diretorio=PROJETO, on_change=None):
        self.diretorio = diretorio
        self.on_change = on_change
        self.handler = MCRFileHandler()
        self.observer = Observer()
        self._rodando = False
    
    def iniciar(self):
        if self._rodando:
            return
        self.observer.schedule(self.handler, self.diretorio, recursive=True)
        self.observer.start()
        self._rodando = True
        print(f'[Watchdog] Monitorando: {self.diretorio}')
        
        if self.on_change:
            def _loop():
                while self._rodando:
                    eventos = self.handler.ultimos_eventos()
                    if eventos:
                        self.on_change(eventos)
                    time.sleep(5)
            t = threading.Thread(target=_loop, daemon=True)
            t.start()
    
    def parar(self):
        self._rodando = False
        self.observer.stop()
        self.observer.join()
    
    def ultimos_eventos(self, n=5):
        return self.handler.ultimos_eventos(n)
