"""MCR-DevIA Thinker V3 — com seguranca integrada
3 mecanismos: MAX_RETRIES, VALIDACAO pos-edit, ROLLBACK via backup"""
import os, sys, json, subprocess, re, shutil, time

MCR = r"E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py"
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

MAX_RETRIES = 3
BACKUP_EXT = ".thinker_bak"

class ThinkerV3:
    def __init__(self):
        self.log = []
        self.retries = 0
        self.last_backup = None
    
    def log_msg(self, msg):
        self.log.append(msg)
        print(f"  [Thinker] {msg}")
    
    def processar(self, task):
        print(f"\n  {'='*60}")
        print(f"  THINKER V3 — com seguranca")
        print(f"  Task: {task[:80]}...")
        print(f"  MAX_RETRIES: {MAX_RETRIES}")
        print(f"  {'='*60}")
        
        resultado = self._executar_plano(task)
        return resultado
    
    # ================================================================
    # BACKUP E ROLLBACK
    # ================================================================
    
    def _backup(self, path):
        """Faz backup antes de editar."""
        bak = path + BACKUP_EXT
        shutil.copy2(path, bak)
        self.last_backup = bak
        self.log_msg(f"  Backup: {bak}")
        return bak
    
    def _rollback(self, path):
        """Restaura backup se a edicao falhar."""
        bak = path + BACKUP_EXT
        if os.path.exists(bak):
            shutil.copy2(bak, path)
            os.remove(bak)
            self.log_msg(f"  Rollback: {path} restaurado")
            return True
        return False
    
    # ================================================================
    # VALIDACAO POS-EDIT
    # ================================================================
    
    def _validar_compilacao(self, path):
        """Valida se o arquivo compila depois da edicao."""
        try:
            with open(path, encoding="utf-8") as f:
                codigo = f.read()
            compile(codigo, path, "exec")
            return True
        except SyntaxError as e:
            self.log_msg(f"  Erro de compilacao: {e}")
            return False
    
    def _validar_funcionalidade(self, path, ferramenta):
        """Valida se a ferramenta realmente funciona apos edicao."""
        # Executa o Thinker com um comando simples e ve se nao crasha
        try:
            r = subprocess.run(
                [sys.executable, path, "testar_ferramenta", ferramenta],
                capture_output=True, text=True, timeout=30
            )
            # Se retornou sem crash, a ferramenta existe
            return "implementado" not in (r.stdout or "").lower()
        except:
            return False
    
    # ================================================================
    # EXECUCAO DO PLANO
    # ================================================================
    
    def _executar_plano(self, task):
        """Executa o plano de acao com seguranca."""
        # Passo 1: Estudar
        self.log_msg("Fase 1: Estudando...")
        self._executar_mcr(["grep", "class.*Corrida|def correr", r"E:\Projeto MCR\sandbox"])
        
        # Passo 2: Criar (com seguranca)
        self.log_msg("Fase 2: Criando nova corrida...")
        self.retries = 0
        while self.retries < MAX_RETRIES:
            self.retries += 1
            self.log_msg(f"  Tentativa {self.retries}/{MAX_RETRIES}")
            
            # Backup
            origem = r"E:\Projeto MCR\sandbox\grande_corrida.py"
            destino = r"E:\Projeto MCR\sandbox\corrida_thinker_v3.py"
            self._backup(destino) if os.path.exists(destino) else None
            
            # Cria nova versao
            try:
                with open(origem, encoding="utf-8") as f:
                    template = f.read()
                
                # Modifica
                novo = template.replace("V12.3", "V12_THINKER")
                novo = novo.replace("Sujeira igual pra todos", "Criada pelo Thinker V3")
                
                with open(destino, "w", encoding="utf-8") as f:
                    f.write(novo)
                
                self.log_msg(f"  Nova corrida: {destino}")
            except Exception as e:
                self.log_msg(f"  Erro ao criar: {e}")
                continue
            
            # Validacao
            if self._validar_compilacao(destino):
                self.log_msg(f"  [OK] Compilacao valida!")
                break
            else:
                self.log_msg(f"  [FALHA] Compilacao invalida. Tentando de novo...")
                self._rollback(destino)
                continue
        else:
            self.log_msg(f"  [ERRO] Todas as {MAX_RETRIES} tentativas falharam.")
            return {"status": "falha", "motivo": "max_retries_excedido"}
        
        # Passo 3: Executar
        self.log_msg("Fase 3: Executando nova corrida...")
        try:
            r = subprocess.run([sys.executable, destino],
                capture_output=True, text=True, timeout=300)
            out = (r.stdout or "")[-1500:]
            self.log_msg(f"  Resultado: {out[:200]}")
            return {"status": "ok", "resultado": out, "script": destino}
        except Exception as e:
            self.log_msg(f"  Erro ao executar: {e}")
            return {"status": "erro", "motivo": str(e)}
    
    def _executar_mcr(self, args):
        """Executa comando do MCR-DevIA."""
        try:
            r = subprocess.run([sys.executable, MCR] + args,
                capture_output=True, text=True, timeout=120)
            self.log_msg(f"  {r.stdout[:200]}")
            return r.stdout
        except Exception as e:
            self.log_msg(f"  Erro: {e}")
            return None


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Criar nova corrida"
    
    thinker = ThinkerV3()
    resultado = thinker.processar(task)
    
    print(f"\n{'='*60}")
    print(f"  RESULTADO DO THINKER V3")
    print(f"{'='*60}")
    print(f"  Status: {resultado.get('status', '?')}")
    if resultado.get('script'):
        print(f"  Script criado: {resultado['script']}")
    if resultado.get('resultado'):
        print(f"  Output: {resultado['resultado'][:300]}")
    print(f"  Tentativas: {thinker.retries}")
    print(f"{'='*60}")
