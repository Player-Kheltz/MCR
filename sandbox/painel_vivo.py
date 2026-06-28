"""MCR-DevIA V12 — Painel Vivo
====================================
Enquanto este terminal estiver aberto, o MCR-DevIA trabalha.
Escaneia, gera, testa, aprende, evolui.
Feche o terminal para pausar.
Recursos: minimos (5s entre ciclos, idle quando não há tarefas)
================================================"""
import os, sys, json, time, subprocess, threading
from datetime import datetime

# ============================================================
# CORES (ANSI — funciona no Windows Terminal e PowerShell 7+)
# ============================================================
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bg_blue": "\033[44m",
    "bg_green": "\033[42m",
    "bg_red": "\033[41m",
    "bg_yellow": "\033[43m",
}

# ============================================================
# ESTADO GLOBAL
# ============================================================
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"
SCANNER = r"E:\Projeto MCR\sandbox\scanner_mestre.py"
CONSISTENCIA = r"E:\Projeto MCR\sandbox\detector_consistencia.py"
LEARNING_SCAN = r"E:\Projeto MCR\scripts\mcr_devia\mcr_learning_scan.py"
MCR_DEVIA = r"E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py"
SANDBOX = r"E:\Projeto MCR\sandbox\autogerados"
CREW_KG_DIR = r"E:\Projeto MCR\sandbox\.mcr_devia\crews"

class EstadoMCR:
    """Estado vivo do MCR-DevIA, atualizado a cada ciclo."""
    
    def __init__(self):
        self.kg_lessons = 0
        self.kg_anteriores = 0
        self.scanner_limpos = 0
        self.scanner_total = 0
        self.scanner_pct = 0
        self.arquivos_gerados = 0
        self.arquivos_consistentes = 0
        self.arquivos_inconsistentes = 0
        self.crew_lessons_total = 0
        self.ultimo_aprendizado = ""
        self.ultimo_scan = ""
        self.ultimo_fix = ""
        self.ultima_geracao = ""
        self.status = "inicializando"
        self.ciclo = 0
        self.inicio = time.time()
        self.cores_suportadas = self._detectar_cores()
    
    def _detectar_cores(self):
        """Verifica se terminal suporta ANSI."""
        return os.environ.get("TERM_PROGRAM") == "vscode" or os.environ.get("WT_SESSION") or False
    
    def atualizar(self):
        """Atualiza todos os indicadores lendo do disco."""
        # KG
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, encoding="utf-8") as f:
                    kg = json.load(f)
                self.kg_anteriores = self.kg_lessons
                self.kg_lessons = len(kg.get("lessons", []))
            except:
                pass
        
        # Crews KGs
        total_crew = 0
        if os.path.exists(CREW_KG_DIR):
            for fname in os.listdir(CREW_KG_DIR):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(CREW_KG_DIR, fname), encoding="utf-8") as f:
                            crew = json.load(f)
                        total_crew += len(crew.get("lessons", []))
                    except:
                        pass
        self.crew_lessons_total = total_crew
        
        # Scanner (da ultima execucao)
        # (atualizado pelo ciclo)
        
        # Gerados
        if os.path.exists(SANDBOX):
            self.arquivos_gerados = len([f for f in os.listdir(SANDBOX) 
                                         if f.startswith("devia_") and f.endswith(".lua")])
        
        # Consistencia
        try:
            r = subprocess.run([sys.executable, CONSISTENCIA],
                capture_output=True, text=True, timeout=30)
            output = r.stdout or ""
            for line in output.split("\n"):
                if "Resultado:" in line:
                    partes = line.split()
                    if len(partes) >= 2:
                        nums = partes[1].split("/")
                        if len(nums) == 2:
                            try:
                                self.arquivos_consistentes = int(nums[0])
                                self.arquivos_inconsistentes = int(nums[1]) - int(nums[0])
                            except:
                                pass
                if "KG" in line and "Aprendido" in line:
                    self.ultimo_aprendizado = line.strip()
        except:
            pass
    
    def executar_ciclo(self):
        """Um ciclo completo de aprendizado."""
        self.ciclo += 1
        self.status = "trabalhando"
        
        # 1. Escaneia
        self.status = "escanendo"
        try:
            r = subprocess.run([sys.executable, SCANNER],
                capture_output=True, text=True, timeout=60)
            out = r.stdout or ""
            for line in out.split("\n"):
                if "SCAN FINAL:" in line:
                    self.ultimo_scan = line.strip()
                    partes = line.split()
                    for p in partes:
                        if "/" in p and any(c.isdigit() for c in p):
                            nums = p.split("/")
                            try:
                                self.scanner_limpos = int(nums[1]) - int(nums[0].split()[-1]) if nums[0].split()[-1].isdigit() else 0
                                self.scanner_total = int(nums[1])
                                self.scanner_pct = self.scanner_limpos * 100 // max(1, self.scanner_total)
                            except:
                                pass
        except:
            pass
        
        # 2. Aprende
        self.status = "aprendendo"
        try:
            r = subprocess.run([sys.executable, LEARNING_SCAN],
                capture_output=True, text=True, timeout=60)
            for line in (r.stdout or "").split("\n"):
                if "KG atualizado" in line:
                    self.ultimo_aprendizado = line.strip()
        except:
            pass
        
        # 3. Verifica consistencia
        self.status = "validando"
        self.atualizar()
        
        self.status = "pronto"


class Painel:
    """Desenha o terminal bonito."""
    
    def __init__(self, estado):
        self.estado = estado
        self.tela = ""
    
    def limpar(self):
        """Limpa terminal (so funciona em terminais reais)."""
        os.system("cls" if os.name == "nt" else "clear")
    
    def barra(self, pct, largura=20, cor_cheio="green", cor_vazio="dim"):
        """Desenha barra de progresso."""
        cheios = int(pct * largura / 100)
        bar = ""
        bar = "[" + "#" * cheios + "." * (largura - cheios) + "]"
        return bar
    
    def cabecalho(self):
        """Topo do painel."""
        c = self.estado
        tempo = time.time() - c.inicio
        h = int(tempo // 3600)
        m = int((tempo % 3600) // 60)
        
        linhas = []
        linhas.append("")
        linhas.append(f"  +=============================================================+")
        linhas.append(f"  |     MCR-DevIA  V12  —  PAINEL VIVO                        |")
        linhas.append(f"  |     Ciclo #{c.ciclo}  |  Online: {h}h{m}m               |")
        linhas.append(f"  +=============================================================+")
        return "\n".join(linhas)
    
    def secao_kg(self):
        """Seção do Knowledge Graph."""
        c = self.estado
        delta = c.kg_lessons - c.kg_anteriores
        
        return (
            f"\n  +--- [KG] Knowledge Graph ---------------------------------+"
            f"\n  |  Lessons: {c.kg_lessons:>4}  {'+' + str(delta) if delta > 0 else '   '}  |  Crew: {c.crew_lessons_total:<4}               |"
            f"\n  |  Crescimento: {self.barra(min(c.kg_lessons, 250) * 100 // 250, 15)}  {c.kg_lessons}/250        |"
            f"\n  |  Ultimo: {c.ultimo_aprendizado[:60]:<60}|"
            f"\n  +----------------------------------------------------------+"
        )
    
    def secao_scanner(self):
        """Seção do Scanner."""
        c = self.estado
        pct = c.scanner_pct
        cor = "green" if pct >= 95 else ("yellow" if pct >= 80 else "red")
        
        return (
            f"\n  +--- [SCANNER] Projeto MCR ------------------------------+"
            f"\n  |  {c.ultimo_scan:<70}|"
            f"\n  |  Saude: {self.barra(pct, 20, cor)}  {pct}%               |"
            f"\n  +----------------------------------------------------------+"
        )
    
    def secao_geracao(self):
        """Seção de Geração."""
        c = self.estado
        
        total_arq = c.arquivos_consistentes + c.arquivos_inconsistentes
        qual_pct = c.arquivos_consistentes * 100 // max(1, total_arq)
        return (
            f"\n  +--- [GERACAO] Conteudo Criado ---------------------------+"
            f"\n  |  Arquivos: {c.arquivos_gerados:<4}  |  Consistentes: {c.arquivos_consistentes:<4}  |  Inconsistentes: {c.arquivos_inconsistentes:<4} |"
            f"\n  |  Qualidade: {self.barra(qual_pct, 15)}  {qual_pct}%     |"
            f"\n  +----------------------------------------------------------+"
        )
    
    def secao_status(self):
        """Status atual."""
        c = self.estado
        status_icone = {
            "pronto": "[PRONTO]",
            "trabalhando": "[TRAB]",
            "escanendo": "[SCAN]",
            "aprendendo": "[APREND]",
            "validando": "[VAL]",
            "inicializando": "[INIT]",
        }
        
        return (
            f"\n  +--- [STATUS] Ciclo Atual --------------------------------+"
            f"\n  |  [{c.status.upper():<12}]  Ciclo: #{c.ciclo:<4}  Tick: 5s                  |"
            f"\n  |  {c.ultimo_scan[:65]:<65}|"
            f"\n  +----------------------------------------------------------+"
        )
    
    def secao_crews(self):
        """Status das Crews V12."""
        c = self.estado
        
        crews_status = []
        if os.path.exists(CREW_KG_DIR):
            for fname in sorted(os.listdir(CREW_KG_DIR)):
                if fname.endswith(".json"):
                    nome = fname.replace(".json", "")
                    try:
                        with open(os.path.join(CREW_KG_DIR, fname), encoding="utf-8") as f:
                            crew = json.load(f)
                        n_lessons = len(crew.get("lessons", []))
                        n_bench = len(crew.get("benchmarks", []))
                        crews_status.append(f"{nome}: {n_lessons}L/{n_bench}B")
                    except:
                        crews_status.append(f"{nome}: ?")
        
        linhas = " | ".join(crews_status) if crews_status else "(nenhuma crew ativa)"
        return (
            f"\n  +--- [CREWS V12] Agentes Ativos --------------------------+"
            f"\n  |  {linhas:<65}|"
            f"\n  +----------------------------------------------------------+"
        )
    
    def rodape(self):
        """Instrucoes."""
        return (
            f"\n  +=============================================================+"
            f"\n  |  Painel vivo — Feche este terminal para pausar            |"
            f"\n  |  Atualiza a cada 5s | Recursos minimos em idle            |"
            f"\n  +=============================================================+"
            f"\n"
        )
    
    def renderizar(self):
        """Renderiza painel completo."""
        self.limpar()
        for secao in [self.cabecalho(), self.secao_kg(), self.secao_scanner(),
                      self.secao_geracao(), self.secao_crews(), self.secao_status(),
                      self.rodape()]:
            linha = secao.encode("ascii", "replace").decode("ascii")
            print(linha)


# ============================================================
# MAIN LOOP
# ============================================================
if __name__ == "__main__":
    print("Inicializando MCR-DevIA Painel Vivo...")
    
    estado = EstadoMCR()
    painel = Painel(estado)
    
    # Primeira atualizacao
    estado.atualizar()
    painel.renderizar()
    
    # Loop principal (5s entre ciclos)
    try:
        while True:
            time.sleep(5)
            estado.executar_ciclo()
            painel.renderizar()
    except KeyboardInterrupt:
        print("\n  MCR-DevIA pausado. Até a próxima!")
