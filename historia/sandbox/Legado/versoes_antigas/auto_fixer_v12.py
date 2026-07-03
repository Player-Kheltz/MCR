"""MCR-DevIA Auto-Fixer V12.3 — IA com validacao, fallback deterministico e KG"""
import os, re, json, urllib.request, shutil

OLLAMA_URL = "http://localhost:11434/api/generate"

class AutoFixerV12:
    def __init__(self, sandbox_path):
        self.sandbox = sandbox_path
        self.kg_path = os.path.join(os.path.dirname(sandbox_path), ".mcr_devia", "knowledge.json")
        self.kg = self._load_kg()
        self.ia_calls = 0
        self.kg_hits = 0
        self.fallback_count = 0
        self.log = []
    
    def _load_kg(self):
        if os.path.exists(self.kg_path):
            try:
                with open(self.kg_path, encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"lessons": []}
    
    def _save_kg(self):
        os.makedirs(os.path.dirname(self.kg_path), exist_ok=True)
        with open(self.kg_path, "w", encoding="utf-8") as f:
            json.dump(self.kg, f, indent=2, ensure_ascii=False)
    
    def _ia(self, prompt):
        """Chama Qwen 2.5 Coder 7B com timeout."""
        self.ia_calls += 1
        try:
            d = json.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt,
                "stream": False, "options": {"temperature": 0.2, "num_ctx": 4096}}).encode()
            r = urllib.request.Request(OLLAMA_URL, data=d,
                headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(r, timeout=120).read())
            return resp.get("response", "").strip()
        except Exception as e:
            return None
    
    def _kg_buscar(self, problema, conteudo):
        """Busca fix similar na KG. Retorna (linha_corrigida, confianca) ou None."""
        conteudo_clean = conteudo.strip()[:200]
        for lesson in self.kg.get("lessons", []):
            if lesson.get("context", "").startswith(f"fix_{problema}"):
                antes = lesson.get("antes", "")[:200]
                if antes == conteudo_clean or conteudo_clean in antes or antes in conteudo_clean:
                    return lesson.get("depois", ""), 0.95
        return None, 0.0
    
    def _kg_registrar(self, problema, arquivo, antes, depois):
        """Registra fix na KG. Armazena SEM indentacao para ser reutilizavel."""
        antes_clean = antes.strip()[:200]
        depois_clean = depois.strip()[:200]
        for l in self.kg.get("lessons", []):
            if l.get("antes", "").strip()[:200] == antes_clean:
                return  # Ja existe
        self.kg.setdefault("lessons", []).append({
            "context": f"fix_{problema}",
            "arquivo": arquivo,
            "antes": antes_clean,
            "depois": depois_clean
        })
        self._save_kg()
    
    def _extrair_linha_problema(self, texto, padrao_regex, grupo_contexto=1):
        """Extrai a linha exata do problema + contexto (3 antes, 3 depois).
        Retorna (linha_idx, snippet_contexto, linha_problema) ou None."""
        linhas = texto.split("\n")
        for m in re.finditer(padrao_regex, texto):
            # Encontra a linha do match
            linha_idx = texto[:m.start()].count("\n")
            ini = max(0, linha_idx - 3)
            fim = min(len(linhas), linha_idx + 4)
            contexto = "\n".join(
                f"{'>' if i == linha_idx else ' '} L{i+1}: {linhas[i]}"
                for i in range(ini, fim)
            )
            return linha_idx, contexto, linhas[linha_idx].strip()
        return None, None, None
    
    def _validar_resposta_ia(self, original, resposta, problemas_permitidos=None):
        """4 camadas de validacao. Retorna True/False e motivo."""
        if not resposta or len(resposta) < 3:
            return False, "vazia ou curta demais"
        if resposta.startswith("[ERRO_IA") or "não consigo" in resposta.lower():
            return False, "IA recusou ou erro"
        # Camada 1: nao pode ser muito maior que o original
        if len(resposta) > len(original) * 3:
            return False, f"resposta {len(resposta)}x maior que original {len(original)}"
        # Camada 2: nao pode ser muito menor
        if len(resposta) < len(original) * 0.3:
            return False, f"resposta muito menor ({len(resposta)} vs {len(original)})"
        # Camada 3: palavras-chave do original devem aparecer
        palavras_orig = set(re.findall(r'\b[a-zA-Z_]\w+\b', original))
        palavras_resp = set(re.findall(r'\b[a-zA-Z_]\w+\b', resposta))
        if problemas_permitidos:
            palavras_orig -= problemas_permitidos
        if palavras_orig and len(palavras_orig & palavras_resp) < len(palavras_orig) * 0.3:
            return False, f"poucas palavras-chave preservadas ({len(palavras_orig & palavras_resp)}/{len(palavras_orig)})"
        # Camada 4: nao contem erros obvios
        if '�' in resposta or '??' in resposta:
            return False, "caracteres invalidos na resposta"
        return True, "ok"
    
    def _aplicar_fix_linha(self, texto, linha_idx, nova_linha):
        """Substitui APENAS a linha especifica por indice. Preserva indentacao."""
        linhas = texto.split("\n")
        if 0 <= linha_idx < len(linhas):
            indent = re.match(r'^(\s*)', linhas[linha_idx]).group(1)
            linhas[linha_idx] = indent + nova_linha.strip()
            return "\n".join(linhas)
        return texto
    
    # ==================== SQL INJECTION FIXER ====================
    
    def fix_sql_injection(self, texto, rel):
        """Corrige SQL injection: .. var -> .. db.escapeString(var) com IA validada."""
        padrao = re.compile(r'db\.\w+\s*\(\s*"[^"]*"\s*\.\.\s*(\w+(?:\:\w+\([^)]*\))?)')
        if not padrao.search(texto):
            return None
        
        modificado = False
        linhas = texto.split("\n")
        visitados = set()
        
        for m in padrao.finditer(texto):
            linha_idx = texto[:m.start()].count("\n")
            if linha_idx in visitados: continue
            visitados.add(linha_idx)
            
            linha_original = linhas[linha_idx].strip()
            var = m.group(1)
            
            # Pula se ja usa escapeString
            if "escapeString" in linha_original:
                continue
            # Pula se for numero
            if re.match(r"^\d", var):
                continue
            if var == "db":
                continue
            
            # --- TENTA KG PRIMEIRO ---
            fix_kg, conf = self._kg_buscar("sql_injection", linha_original.strip())
            if fix_kg:
                indent = re.match(r'^(\s*)', linhas[linha_idx]).group(1)
                linhas[linha_idx] = indent + fix_kg.strip()
                modificado = True
                self.kg_hits += 1
                self.log.append(f"  KG: SQL injection {rel} L{linha_idx+1}")
                continue
            
            # --- PREPARA CONTEXTO PARA IA ---
            ini = max(0, linha_idx - 3)
            fim = min(len(linhas), linha_idx + 4)
            contexto = "\n".join(linhas[ini:fim])
            
            prompt = (
                "You are a Lua/OTServ security expert. Fix the SQL injection on the marked line.\n"
                "Replace `.. var` with `.. db.escapeString(var)`.\n"
                "Return ONLY the corrected line, with the EXACT SAME indentation.\n"
                "Rules:\n"
                "- Keep the exact same leading whitespace\n"
                "- Only change the concatenation to use db.escapeString()\n"
                "- Do NOT change anything else\n\n"
                f"File: {rel}\n"
                f"Code context (-> marks the line to fix):\n{contexto}\n\n"
                "The line with -> is:\n"
                f"{linhas[linha_idx]}\n\n"
                "Fixed line (ONLY the line, same indentation):"
            )
            
            # --- TENTA IA (ate 3x) ---
            resposta = None
            for tentativa in range(3):
                resp = self._ia(prompt)
                valido, motivo = self._validar_resposta_ia(linhas[linha_idx], resp or "")
                if valido:
                    resposta = resp
                    break
                self.log.append(f"  IA tentativa {tentativa+1}: {motivo}")
            
            if resposta:
                # Preserva indentacao
                indent = re.match(r'^(\s*)', linhas[linha_idx]).group(1)
                if not resposta.startswith(indent):
                    resposta = indent + resposta.lstrip()
                linhas[linha_idx] = resposta
                self._kg_registrar("sql_injection", rel, linha_original, resposta)
                self.log.append(f"  IA: SQL injection {rel} L{linha_idx+1}")
                modificado = True
            else:
                # --- FALLBACK DETERMINISTICO ---
                self.fallback_count += 1
                indent = re.match(r'^(\s*)', linhas[linha_idx]).group(1)
                nova = re.sub(
                    r'(\.\.\s*)(\w+(?::\w+\([^)]*\))?)',
                    r'\1db.escapeString(\2)',
                    linhas[linha_idx],
                    count=1
                )
                if nova != linhas[linha_idx]:
                    linhas[linha_idx] = nova
                    self.log.append(f"  FALLBACK: SQL injection {rel} L{linha_idx+1}")
                    modificado = True
        
        return "\n".join(linhas) if modificado else None
    
    # ==================== SINTAXE PYTHON FIXER ====================
    
    def fix_sintaxe_python(self, texto, rel):
        """Comenta blocos Python com IA validada ou fallback."""
        # Primeiro detecta se tem Python
        tem_python = False
        for linha in texto.split("\n"):
            if re.match(r"^\s*(def |class |import )(?!\w)", linha):
                tem_python = True
                break
        if not tem_python:
            return None
        
        linhas = texto.split("\n")
        modificado = False
        novas = []
        dentro = False
        
        for linha in linhas:
            if re.match(r"^\s*(def |class |import )(?!\w)", linha) and not dentro:
                # --- TENTA KG ---
                fix_kg, _ = self._kg_buscar("sintaxe_python", linha)
                if fix_kg:
                    novas.append(fix_kg)
                    self.kg_hits += 1
                    dentro = True
                    modificado = True
                    continue
                
                # --- IA ---
                prompt = (
                    "This Lua file has Python code mixed in. Comment the Python line.\n"
                    "Return the line with `-- ` prepended (preserve indentation).\n\n"
                    f"Line: {linha}\n\nCommented line:"
                )
                resp = None
                for t in range(3):
                    r = self._ia(prompt)
                    valido, motivo = self._validar_resposta_ia(linha, r or "")
                    if valido and r.startswith("--"):
                        resp = r
                        break
                
                if resp:
                    novas.append(resp)
                    self._kg_registrar("sintaxe_python", rel, linha, resp)
                    dentro = True
                    modificado = True
                else:
                    # --- FALLBACK: comenta manualmente ---
                    novas.append("-- " + linha)
                    dentro = True
                    modificado = True
                    self.fallback_count += 1
                continue
            
            if dentro:
                if re.match(r"^\s*--", linha) or linha.strip() == "":
                    novas.append(linha)
                    continue
                # Python continua
                novas.append("-- " + linha)
                continue
            novas.append(linha)
        
        return "\n".join(novas) if modificado else None
    
    # ==================== CODIGO MORTO FIXER (DESABILITADO) ====================
    
    def fix_dead_code(self, texto, rel):
        """DESABILITADO: detector de codigo morto produz muitos falsos positivos."""
        return None
    
    # ==================== NIL (DESABILITADO) ====================
    
    def fix_nil(self, texto, rel):
        return None
    
    # ==================== ORQUESTRADOR ====================
    
    def fix_file(self, path, rel):
        with open(path, "rb") as f:
            raw = f.read()
        try:
            texto = raw.decode("utf-8")
        except:
            return False
        original = texto
        
        for fixer in [self.fix_sql_injection, self.fix_sintaxe_python]:
            try:
                res = fixer(texto, rel)
                if res:
                    texto = res
            except Exception as e:
                self.log.append(f"  [ERRO] {fixer.__name__}: {e}")
        
        if texto != original:
            bak = path + ".bak_v12"
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
            with open(path, "wb") as f:
                f.write(texto.encode("utf-8"))
            self.log.append(f"  -> MODIFICADO")
            return True
        return False
    
    def run(self):
        print("=" * 70)
        print("  MCR-DevIA AUTO-FIXER V12.3 — IA validada + KG + fallback")
        print(f"  Sandbox: {self.sandbox}")
        print(f"  KG: {len(self.kg.get('lessons', []))} lessons")
        print("=" * 70)
        
        arquivos = []
        for root, dirs, files in os.walk(self.sandbox):
            for f in files:
                if f.endswith(".lua") and ".bak" not in f and f != "fix_log.txt":
                    arquivos.append(os.path.join(root, f))
        
        modificados = 0
        for path in sorted(arquivos):
            rel = os.path.relpath(path, self.sandbox)
            print(f"\n[{rel}]", end="")
            try:
                if self.fix_file(path, rel):
                    modificados += 1
                    print(" MODIFICADO")
                else:
                    print(" OK")
            except Exception as e:
                self.log.append(f"  [ERRO] {e}")
                print(f" [ERRO]")
        
        print(f"\n{'='*70}")
        print(f"  IA calls: {self.ia_calls}")
        print(f"  KG hits: {self.kg_hits}")
        print(f"  Fallbacks: {self.fallback_count}")
        print(f"  Modificados: {modificados}/{len(arquivos)}")
        print(f"  KG lessons: {len(self.kg.get('lessons', []))}")
        print(f"{'='*70}")
        
        with open(os.path.join(self.sandbox, "fix_log.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(self.log))

if __name__ == "__main__":
    sandbox = r"E:\Projeto MCR\sandbox\auto_fix_test"
    # Se o sandbox estiver vazio, roda o preparador
    if not os.listdir(sandbox) or all(f.endswith('.txt') for f in os.listdir(sandbox)):
        print("Sandbox vazio. Execute preparar_sandbox.py primeiro.")
    else:
        fixer = AutoFixerV12(sandbox)
        fixer.run()
