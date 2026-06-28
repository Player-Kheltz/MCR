"""MCR-DevIA — SystemAware: Le o computador INTEIRO, mas NUNCA edita nada fora do sandbox.
Windows Event Log, hardware, processos, alteracoes em arquivos. Tudo vira aprendizado no KG."""
import os, json, subprocess, time, re, glob
from datetime import datetime, timedelta

SANDBOX = r"E:\Projeto MCR\sandbox"
KG_PATH = os.path.join(SANDBOX, ".mcr_devia", "knowledge.json")

# REGRA ABSOLUTA: nenhuma escrita fora daqui
ESCRITA_PERMITIDA = SANDBOX
assert ESCRITA_PERMITIDA in __file__, "VIOLACAO: este script so pode escrever no sandbox!"

class SystemAware:
    def __init__(self):
        self.log = []
    
    def log_msg(self, msg):
        self.log.append(msg)
        print(f"  [SystemAware] {msg}")
    
    def kg_add(self, entry):
        kg = {"lessons": []}
        if os.path.exists(KG_PATH):
            with open(KG_PATH, encoding="utf-8") as f:
                kg = json.load(f)
        kg.setdefault("lessons", []).append(entry)
        with open(KG_PATH, "w", encoding="utf-8") as f:
            json.dump(kg, f, indent=2, ensure_ascii=False)
    
    def scan_all(self):
        print("=" * 70)
        print("  SYSTEMAWARE — MCR-DevIA lendo o computador")
        print("  REGRA: NENHUMA alteracao fora do sandbox.")
        print("=" * 70)
        
        self._eventos_windows()
        self._hardware()
        self._processos()
        self._arquivos_recentes()
        
        print(f"\n[SystemAware] Scan concluido. Dados no KG.")
    
    # ================================================================
    # 1. EVENTOS DO WINDOWS
    # ================================================================
    
    def _eventos_windows(self):
        self.log_msg("Lendo Eventos do Windows (ultima hora)...")
        try:
            # Eventos de erro do sistema
            r = subprocess.run(
                'wevtutil qe System /c:10 /rd:true /f:text /q:"*[System[(Level=2)]]"',
                capture_output=True, text=True, timeout=30, shell=True
            )
            erros = r.stdout or ""
            for linha in erros.split("\n"):
                if any(p in linha.lower() for p in ["error", "critical", "warning", "disk", "memory", "crash"]):
                    self.kg_add({
                        "context": "system_aware_windows_event",
                        "tipo": "evento_sistema",
                        "conteudo": linha[:200],
                        "fonte": "windows_eventlog_system",
                        "timestamp": time.time()
                    })
                    self.log_msg(f"  Evento: {linha[:80]}...")
        except Exception as e:
            self.log_msg(f"  Erro ao ler eventos: {e}")
        
        # Eventos de aplicacao
        try:
            r = subprocess.run(
                'wevtutil qe Application /c:10 /rd:true /f:text /q:"*[System[(Level=2)]]"',
                capture_output=True, text=True, timeout=30, shell=True
            )
            for linha in (r.stdout or "").split("\n"):
                if any(p in linha.lower() for p in ["error", "fault", "exception", "crash"]):
                    self.kg_add({
                        "context": "system_aware_app_event",
                        "tipo": "evento_aplicacao",
                        "conteudo": linha[:200],
                        "fonte": "windows_eventlog_app",
                        "timestamp": time.time()
                    })
        except: pass
    
    # ================================================================
    # 2. HARDWARE
    # ================================================================
    
    def _hardware(self):
        self.log_msg("Lendo hardware do sistema...")
        
        # CPU
        try:
            r = subprocess.run("wmic cpu get loadpercentage", capture_output=True, text=True, timeout=15, shell=True)
            for linha in (r.stdout or "").split("\n"):
                if linha.strip().isdigit():
                    self.kg_add({
                        "context": "system_aware_hardware",
                        "tipo": "cpu",
                        "valor": int(linha.strip()),
                        "timestamp": time.time()
                    })
                    self.log_msg(f"  CPU: {linha.strip()}%")
        except: pass
        
        # Memoria
        try:
            r = subprocess.run(
                'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:csv',
                capture_output=True, text=True, timeout=15, shell=True
            )
            for linha in (r.stdout or "").split("\n"):
                partes = linha.split(",")
                if len(partes) >= 3:
                    try:
                        total = int(partes[-2]) // 1024  # KB -> MB
                        livre = int(partes[-1]) // 1024
                        uso = ((total - livre) * 100) // total if total > 0 else 0
                        self.kg_add({
                            "context": "system_aware_hardware",
                            "tipo": "memoria",
                            "total_mb": total,
                            "livre_mb": livre,
                            "uso_pct": uso,
                            "timestamp": time.time()
                        })
                        self.log_msg(f"  RAM: {uso}% usado ({total - livre}MB de {total}MB)")
                    except: pass
        except: pass
        
        # Disco
        try:
            r = subprocess.run("wmic logicaldisk where drivetype=3 get deviceid,size,freespace",
                capture_output=True, text=True, timeout=15, shell=True)
            for linha in (r.stdout or "").split("\n"):
                partes = linha.split()
                if len(partes) >= 3 and partes[0].startswith("C:"):
                    try:
                        livre = int(partes[1]) // (1024**3)
                        total = int(partes[2]) // (1024**3)
                        self.kg_add({
                            "context": "system_aware_hardware",
                            "tipo": "disco",
                            "drive": "C:",
                            "total_gb": total,
                            "livre_gb": livre,
                            "timestamp": time.time()
                        })
                        self.log_msg(f"  Disco C: {livre}GB livres de {total}GB")
                    except: pass
        except: pass
    
    # ================================================================
    # 3. PROCESSOS
    # ================================================================
    
    def _processos(self):
        self.log_msg("Lendo processos em execucao...")
        try:
            r = subprocess.run("tasklist /nh /fo csv", capture_output=True, text=True, timeout=15, shell=True)
            processos = []
            for linha in (r.stdout or "").split("\n"):
                partes = linha.split(",")
                if len(partes) >= 1:
                    nome = partes[0].strip('"')
                    if nome and nome not in processos:
                        processos.append(nome)
            
            # So registra os mais importantes
            importantes = [p for p in processos if any(k in p.lower() for k in ["python", "ollama", "node", "code", "canary", "otclient", "openai", "docker", "sql"])]
            if importantes:
                self.kg_add({
                    "context": "system_aware_processos",
                    "tipo": "processos_ativos",
                    "lista": importantes[:20],
                    "total": len(processos),
                    "timestamp": time.time()
                })
                self.log_msg(f"  {len(importantes)} processos relevantes ativos")
        except: pass
    
    # ================================================================
    # 4. ARQUIVOS RECENTES
    # ================================================================
    
    def _arquivos_recentes(self):
        self.log_msg("Verificando arquivos modificados recentemente...")
        agora = time.time()
        modificados = []
        
        # So olha dentro do projeto MCR (seguro)
        for root, dirs, files in os.walk(r"E:\Projeto MCR"):
            if any(p in root.lower() for p in ["node_modules", ".git", "__pycache__", "_backup"]):
                continue
            for f in files:
                if not f.endswith((".py", ".lua", ".ts", ".js", ".json", ".md")):
                    continue
                path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(path)
                    if agora - mtime < 3600:  # ultima hora
                        modificados.append(os.path.relpath(path, r"E:\Projeto MCR"))
                except: pass
                if len(modificados) >= 20:
                    break
            if len(modificados) >= 20:
                break
        
        if modificados:
            self.kg_add({
                "context": "system_aware_arquivos",
                "tipo": "arquivos_modificados",
                "arquivos": modificados[:20],
                "total": len(modificados),
                "timestamp": time.time()
            })
            self.log_msg(f"  {len(modificados)} arquivos modificados na ultima hora")


if __name__ == "__main__":
    sa = SystemAware()
    sa.scan_all()
    
    print(f"\n{'='*70}")
    print(f"  SYSTEMAWARE CONCLUIDO")
    print(f"  Dados registrados no KG. Nenhuma alteracao fora do sandbox.")
    print(f"{'='*70}")
