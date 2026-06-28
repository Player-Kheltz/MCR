"""MCR-DevIA Auto-Fixer — Corrige problemas automaticamente em ambiente fechado"""
import os, re, shutil, json
from datetime import datetime

class AutoFixer:
    def __init__(self, sandbox_root):
        self.root = sandbox_root
        self.log = []
        self.fixes_aplicados = 0
    
    def log_msg(self, msg):
        self.log.append(msg)
        print(f"  {msg}")
    
    def debug_show(self, path, texto_linhas, label="TEXTO"):
        """Mostra trecho do arquivo para debug (opcional)"""
        pass
    
    # ============ FIXERS ============
    
    def fix_dead_code(self, path, texto):
        """Comenta codigo inacessivel apos return (antes do end)."""
        linhas = texto.split('\n')
        modificado = False
        novas_linhas = []
        i = 0
        
        while i < len(linhas):
            linha = linhas[i]
            # Procura por 'return' que NAO e guard clause
            m = re.match(r'^(\s*)return\b', linha)
            if m and 'end' not in linha.split('--')[0]:
                indent = m.group(1)
                # Verifica se depois deste return, antes do end, tem codigo
                # Junta linhas ate encontrar 'end' no inicio
                j = i + 1
                codigo_morto = []
                escopo = 0
                while j < len(linhas):
                    if escopo <= 0 and re.match(r'^\s*end\b', linhas[j]):
                        break
                    abre = len(re.findall(r'\b(?:then|do|function|repeat)\b', linhas[j]))
                    fecha = len(re.findall(r'\b(?:end|until)\b', linhas[j]))
                    escopo += abre - fecha
                    codigo_morto.append(linhas[j])
                    j += 1
                
                if codigo_morto and any(l.strip() and not l.strip().startswith('--') for l in codigo_morto):
                    # Codigo morto encontrado! Comenta
                    modificado = True
                    novas_linhas.append(linha)
                    for cl in codigo_morto:
                        if cl.strip() and not cl.strip().startswith('--'):
                            novas_linhas.append(indent + '--[[DEAD CODE]] ' + cl.strip())
                        else:
                            novas_linhas.append(cl)
                    i = j
                    self.log_msg(f"  Codigo morto comentado ({len(codigo_morto)} linhas)")
                    continue
            novas_linhas.append(linha)
            i += 1
        
        return '\n'.join(novas_linhas) if modificado else None
    
    def fix_nil_desnecessario(self, path, texto):
        """Remove atribuicoes =. = nil (campos nil desnecessarios)."""
        linhas = texto.split('\n')
        modificado = False
        novas_linhas = []
        
        for linha in linhas:
            # So processa linhas com = nil
            if re.search(r'\.\w+\s*=\s*nil', linha) and '--' not in linha.split('=')[0]:
                # So remove se for a unica coisa na linha
                if linha.strip().endswith('nil') and 'local' not in linha:
                    self.log_msg(f"  nil removido: {linha.strip()[:50]}")
                    modificado = True
                    novas_linhas.append('--' + linha + '  --[[nil desnecessario removido]]')
                    continue
            novas_linhas.append(linha)
        
        return '\n'.join(novas_linhas) if modificado else None
    
    def fix_sql_injection(self, path, texto):
        """Converte string.format('SELECT...%s', var) para query parametrizada (?).
        
        Em Canary/OTServ, db.query aceita ? como placeholder.
        string.format(\"SELECT * FROM X WHERE y = '%s'\", var)
        -> db.query(\"SELECT * FROM X WHERE y = ?\", var)  (ja usa string.format entao so trocar)
        
        Mas o padrao real em Canary e: db.storeQuery, Result, etc.
        Vamos usar abordagem segura: substituir '%s' por ? e remover string.format.
        """
        # Detecta padrao: string.format("...'%s'...", var)
        padrao = re.compile(r"string\.format\(\s*\"([^\"]*'%s'[^\"]*)\"\s*,\s*(\w+)\s*\)")
        modificado = False
        
        def substituir(m):
            nonlocal modificado
            query = m.group(1)
            var = m.group(2)
            # Troca '%s' por ?
            query_fixed = query.replace("'%s'", "?")
            self.log_msg(f"  SQL injection fix: {m.group()[:60]}... -> db.query(\"{query_fixed}\", {var})")
            modificado = True
            return f'db.query("{query_fixed}", {var})'
        
        texto = padrao.sub(substituir, texto)
        return texto if modificado else None
    
    def fix_sintaxe_python(self, path, texto):
        """Isola codigo Python em bloco de comentario."""
        linhas = texto.split('\n')
        modificado = False
        novas_linhas = []
        dentro_python = False
        
        for linha in linhas:
            # Detecta inicio de codigo Python (def, import, class no inicio da linha)
            if re.match(r'^\s*(def |import |from |class |print\()', linha) and '--' not in linha[:5]:
                if not dentro_python:
                    novas_linhas.append('--[[ BLOCO PYTHON (nao-Lua) ---')
                    dentro_python = True
                    modificado = True
                novas_linhas.append('-- ' + linha)
                continue
            else:
                if dentro_python:
                    # Verifica se voltou a ser Lua
                    if re.match(r'^\s*--', linha) or linha.strip() == '':
                        novas_linhas.append(linha)
                        continue
                    elif not re.match(r'^\s+\w', linha):  # Saiu do bloco Python
                        novas_linhas.append('--]]')
                        dentro_python = False
                        modificado = True
                        novas_linhas.append(linha)
                        continue
                    novas_linhas.append('-- ' + linha)
                    continue
            novas_linhas.append(linha)
        
        if dentro_python:
            novas_linhas.append('--]]')
        
        return '\n'.join(novas_linhas) if modificado else None
    
    # ============ ORQUESTRADOR ============
    
    def fix_file(self, path):
        """Aplica todos os fixers em um arquivo. Retorna True se modificou."""
        with open(path, 'rb') as f:
            raw = f.read()
        try:
            texto = raw.decode('utf-8')
        except:
            texto = raw.decode('latin-1', errors='replace')
        
        nome = os.path.basename(path)
        
        # Backup
        bak = path + '.bak_autofix'
        shutil.copy2(path, bak)
        
        # Aplica cada fixer
        for fixer in [self.fix_dead_code, self.fix_nil_desnecessario, 
                      self.fix_sql_injection, self.fix_sintaxe_python]:
            try:
                resultado = fixer(path, texto)
                if resultado:
                    self.fixes_aplicados += 1
                    texto = resultado
            except Exception as e:
                self.log_msg(f"  [ERRO] Fixer {fixer.__name__}: {e}")
        
        if texto != raw.decode('utf-8', errors='replace'):
            with open(path, 'wb') as f:
                f.write(texto.encode('utf-8'))
            return True
        return False
    
    def run(self):
        """Executa em todos os .lua do sandbox."""
        print("=" * 60)
        print("  MCR-DevIA — AUTO-FIXER (modo sandbox)")
        print("=" * 60)
        
        arquivos = []
        for root, dirs, files in os.walk(self.root):
            for f in files:
                if f.endswith('.lua') and '.bak' not in f:
                    arquivos.append(os.path.join(root, f))
        
        print(f"\nArquivos encontrados: {len(arquivos)}")
        
        for path in sorted(arquivos):
            rel = os.path.relpath(path, self.root)
            print(f"\n[{rel}]")
            try:
                if self.fix_file(path):
                    self.log_msg(f"  -> MODIFICADO")
                else:
                    print(f"  -> Nenhuma correcao necessaria")
            except Exception as e:
                self.log_msg(f"  [ERRO] {e}")
        
        print(f"\n{'='*60}")
        print(f"  Total de correcoes aplicadas: {self.fixes_aplicados}")
        print(f"  Log salvo em: {os.path.join(self.root, 'fix_log.txt')}")
        print(f"{'='*60}")
        
        # Salva log
        with open(os.path.join(self.root, 'fix_log.txt'), 'w') as f:
            f.write('\n'.join(self.log))

if __name__ == '__main__':
    fixer = AutoFixer(r"E:\Projeto MCR\sandbox\auto_fix_test")
    fixer.run()
