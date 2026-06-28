"""Modulo: Watchdog - Monitora comandos/ + sandbox/ para auto-revisao.
- Hot-reload de comandos quando comandos/ muda
- Auto-revisao de respostas quando sandbox/ muda
- Indice invertido para ContextCrew (cache em arquivo)
"""
import os, time, threading, re, json as _jj, socket

def init_module(contexto):
    kernel = contexto.get("kernel")
    if kernel:
        w = Watchdog(kernel)
        w.start()
        contexto["watchdog"] = w
        return "watchdog", w
    return None, None


class Watchdog:
    """Monitora comandos/ + sandbox/. Auto-revisa respostas no sandbox.
    Mantem indice invertido para consulta pelo ContextCrew."""
    
    def __init__(self, kernel, intervalo=5.0):
        self.kernel = kernel
        self.intervalo = intervalo
        self._dir_mtime = 0
        self._sandbox_mtime = {}
        self._auto_revisor = None
        self._indice = {}
        self._rodando = False
        self._thread = None
        self._bridge_pid = None  # PID do processo bridge
        self._bridge_portas = [7171, 7172, 7173]  # portas do servidor
    
    def _check_porta(self, porta, timeout=2):
        """Verifica se uma porta TCP esta ouvindo."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            r = s.connect_ex(('127.0.0.1', porta))
            s.close()
            return r == 0
        except:
            return False
    
    def _healthcheck_bridge(self):
        """Verifica se a bridge/servidor esta rodando e reinicia se necessario."""
        if not hasattr(self.kernel, 'contexto'):
            return
        ctx = self.kernel.contexto
        
        # Verifica portas do servidor
        portas_ok = all(self._check_porta(p) for p in self._bridge_portas)
        if portas_ok:
            return  # tudo ok
        
        # Verifica se tem bridge_pid
        bridge_pid_path = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
            ".bridge_pid"
        )
        if os.path.exists(bridge_pid_path):
            try:
                with open(bridge_pid_path) as f:
                    pid = int(f.read().strip())
                # Verifica se processo ainda existe
                import subprocess
                r = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                 capture_output=True, text=True, timeout=5)
                if str(pid) in r.stdout:
                    print(f"[Watchdog] Bridge PID {pid} existe mas portas fechadas. Reiniciando...")
            except:
                pass
        
        # Tenta reiniciar servidor
        print(f"[Watchdog] Bridge/Servidor offline. Tentando reiniciar...")
        try:
            canary_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Canary"))
            bin_path = os.path.join(canary_dir, "canary-sln.exe")
            alt_path = os.path.join(canary_dir, "build", "bin", "canary-sln.exe")
            for bp in [bin_path, alt_path]:
                if os.path.exists(bp):
                    subprocess.Popen([bp], cwd=os.path.dirname(bp),
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"[Watchdog] Servidor reiniciado: {bp}")
                    break
        except Exception as e:
            print(f"[Watchdog] Erro ao reiniciar servidor: {e}")
        try:
            from modulos.auto_revisor import AutoRevisor
            kg = kernel.contexto.get("kg") if kernel else None
            self._auto_revisor = AutoRevisor(kg=kg)
        except:
            pass
    
    def consultar_indice(self, termo, max_r=5):
        """Consulta indice invertido. Retorna arquivos que contem o termo."""
        termo_lower = termo.lower()
        resultados = []
        for palavra, arquivos in self._indice.items():
            if termo_lower in palavra:
                for arq in arquivos[:3]:
                    if arq not in resultados:
                        resultados.append(arq)
        return resultados[:max_r]
    
    def _atualizar_indice(self):
        """Atualiza indice invertido e salva em arquivo para ContextCrew."""
        self._indice = {}
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        dirs = [
            os.path.join(base, "scripts", "mcr_devia"),
            os.path.join(base, "sandbox"),
            os.path.join(base, "docs"),
            os.path.join(base, "Canary", "src"),
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
                    except:
                        pass
        # Salva em arquivo para ContextCrew
        indice_path = os.path.join(base, "sandbox", ".mcr_devia", "indice_watchdog.json")
        try:
            os.makedirs(os.path.dirname(indice_path), exist_ok=True)
            with open(indice_path, "w", encoding="utf-8") as f:
                _jj.dump(self._indice, f, ensure_ascii=False)
        except:
            pass
        print(f"[Watchdog] Indice: {len(self._indice)} palavras, {sum(len(v) for v in self._indice.values())} ocorrencias")
    
    def start(self):
        self._rodando = True
        self._dir_mtime = self._get_dir_mtime()
        self._scan_sandbox()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[Watchdog] Monitorando comandos/ + sandbox/ ({self.intervalo:.0f}s)")
    
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
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        sandbox_dir = os.path.join(base, "sandbox")
        if not os.path.isdir(sandbox_dir):
            return
        for root, dirs, files in os.walk(sandbox_dir):
            for f in files:
                if f.endswith(".txt") and "resposta" in root.lower() or "mega" in f:
                    fpath = os.path.join(root, f)
                    try:
                        self._sandbox_mtime[fpath] = os.path.getmtime(fpath)
                    except:
                        pass
    
    def _revisar_arquivo(self, fpath):
        if not self._auto_revisor:
            return
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                texto = f.read()
            if len(texto) < 100:
                return
            resultado = self._auto_revisor.revisar(texto)
            if resultado["total"] > 0:
                print(f"[Watchdog] Auto-revisao de {os.path.basename(fpath)}: {resultado['total']} alucinacoes")
        except:
            pass
    
    def _loop(self):
        """Monitora comandos/ + sandbox/ em paralelo. Atualiza indice na inicializacao."""
        if not self._indice:
            self._atualizar_indice()
        # Contador para health-check (a cada 5 ciclos, ~25s)
        _hc_count = 0
        while self._rodando:
            time.sleep(self.intervalo)
            
            # Health-check da bridge (a cada 5 ciclos)
            _hc_count += 1
            if _hc_count >= 5:
                _hc_count = 0
                self._healthcheck_bridge()
            
            novo_mtime = self._get_dir_mtime()
            if novo_mtime != self._dir_mtime:
                self._dir_mtime = novo_mtime
                if self.kernel:
                    n = self.kernel.loader.refresh()
                    if n > 0:
                        print(f"[Watchdog] Hot-reload: {n} comandos")
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            sandbox_dir = os.path.join(base, "sandbox")
            if os.path.isdir(sandbox_dir):
                for root, dirs, files in os.walk(sandbox_dir):
                    for f in files:
                        if f.endswith(".txt") and ("resposta" in root.lower() or "mega" in f):
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
