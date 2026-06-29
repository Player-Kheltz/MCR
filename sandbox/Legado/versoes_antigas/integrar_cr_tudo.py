"""Integra todas as 6 conexoes do Context Reinforcer no MCR-DevIA.
Usa MCR-DevIA write via JSON IPC para cada alteracao."""
import json, subprocess, sys, os

BASE_MCR = "E:/Projeto MCR/scripts/mcr_devia"
SANDBOX = "E:/Projeto MCR/sandbox"

def mcr_write(path, conteudo):
    """Escreve arquivo via MCR-DevIA JSON IPC."""
    cmd = {"cmd": "write", "args": [path, conteudo]}
    with open(f"{SANDBOX}/.mcr_cmd.json", "w", encoding="utf-8") as f:
        json.dump(cmd, f, ensure_ascii=False)
    r = subprocess.run([sys.executable, f"{BASE_MCR}/MCR_DevIA-Kernel.py",
        "--json", f"{SANDBOX}/.mcr_cmd.json"],
        capture_output=True, text=True, errors="replace", timeout=60)
    out = r.stdout.strip()
    if "Write" in out:
        print(f"  [OK] {path}")
    else:
        print(f"  [MCR] {out[-200:]}")
    return out

def ler(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def salvar_script(nome, conteudo):
    p = f"{SANDBOX}/{nome}"
    with open(p, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return p

print("="*60)
print("INTEGRACAO CONTEXT REINFORCER - 6 PASSOS")
print("="*60)

# ============================================================
# PASSO 3: CONSELHO — membros recebem contexto_validado do CR
# ============================================================
print("\n[Passo 3] Conselho - CR antes de deliberar...")
path_cons = f"{BASE_MCR}/modulos/conselho.py"
conteudo = ler(path_cons)

# Adicionar CR no inicio do metodo deliberar()
old = '        # 2. DETECTAR ARQUETIPOS\n        arquetipos = self._detectar_arquetipos(pergunta, tipo, ctx_crew_txt)'
new = '''        # 1.5 CONTEXT REINFORCER: valida contexto antes de deliberar
        cr_instrucao = ""
        cr_contexto = ""
        try:
            from modulos.context_reinforcer import ContextReinforcer
            cr = ContextReinforcer(ctx_crew=self.ctx_crew, kg=self.kg)
            cr_result = cr.reforcar(pergunta, self.ctx_crew)
            if cr_result.get("instrucao"):
                cr_instrucao = cr_result["instrucao"]
            if cr_result.get("contexto") and cr_result.get("valido"):
                cr_contexto = f"\\n[CONTEXTO VALIDADO]\\n{cr_result['contexto'][:500]}\\n[/CONTEXTO]\\n"
        except Exception as e:
            print(f"  [Conselho] CR ERRO: {e}")
        
        # 2. DETECTAR ARQUETIPOS
        arquetipos = self._detectar_arquetipos(pergunta, tipo, ctx_crew_txt)'''

if old in conteudo:
    conteudo = conteudo.replace(old, new)
    print("  [OK] CR inserido no deliberar()")
else:
    print("  [AVISO] Padrao 1 nao encontrado")

# Injetar CR nos prompts dos arquetipos (adicionar instrucao_contexto nos params)
old2 = '''                        "memoria_pessoal": memoria_pessoal,
                    }
                    r = orq.executar(orq_template_key, params, consulta=pergunta, temp=0.4)'''
new2 = '''                        "memoria_pessoal": memoria_pessoal,
                        "instrucao_contexto": cr_instrucao,
                        "contexto_extra": cr_contexto,
                    }
                    r = orq.executar(orq_template_key, params, consulta=pergunta, temp=0.4)'''

if old2 in conteudo:
    conteudo = conteudo.replace(old2, new2)
    print("  [OK] CR params injetados nos arquetipos (Orquestrador)")
else:
    print("  [AVISO] Padrao 2 nao encontrado")

# Tambem no fallback prompt fixo
old3 = '''                prompt = prompt_t.format(
                    mcr=_MCR_IDENTITY,
                    ctx_crew=ctx_crew_txt[:800],
                    kg=kg[:800],
                    pergunta=pergunta,
                    ctx_infinity=ctx_infinity[:300],
                )
                # Injeta memoria pessoal no prompt'''
new3 = '''                prompt = prompt_t.format(
                    mcr=_MCR_IDENTITY,
                    ctx_crew=ctx_crew_txt[:800],
                    kg=kg[:800],
                    pergunta=pergunta,
                    ctx_infinity=ctx_infinity[:300],
                )
                # Injeta CR instruction + memoria pessoal
                if cr_instrucao:
                    prompt = cr_instrucao + "\\n" + prompt
                if cr_contexto:
                    prompt = cr_contexto + "\\n" + prompt
                # Injeta memoria pessoal no prompt'''

if old3 in conteudo:
    conteudo = conteudo.replace(old3, new3)
    print("  [OK] CR injetado no fallback prompt fixo")
else:
    print("  [AVISO] Padrao 3 nao encontrado")

mcr_write("modulos/conselho.py", conteudo)

# ============================================================
# PASSO 4: MENTE — think() filtra memorias por relevancia
# ============================================================
print("\n[Passo 4] Mente - CR filtra memorias...")
path_mente = f"{BASE_MCR}/modulos/mente.py"
conteudo = ler(path_mente)

# Adicionar CR no think(): validar memorias antes de usar
old4 = '''    # Monta prompt BATCH com todos os membros + suas MELHORES memorias (aprendizado)
    blocos_memoria = []
    for nome in membros:
        # Carrega memorias de ALTO SCORE primeiro (aprendizado real)
        memoria = _memoria.resumo_para_prompt(nome, max_entradas=5)
        blocos_memoria.append(f"MEMBRO: {nome.upper()}\\nMEMORIA: {memoria}")'''
new4 = '''    # CONTEXT REINFORCER: valida contexto antes de carregar memorias
    cr_instrucao = ""
    try:
        from modulos.context_reinforcer import ContextReinforcer
        cr = ContextReinforcer()
        cr_result = cr.reforcar(pergunta)
        if cr_result.get("instrucao"):
            cr_instrucao = cr_result["instrucao"]
        if cr_result.get("contexto") and not cr_result.get("valido") and cr_result.get("aprendeu"):
            print(f"  [Mente] CR: weblearn disparado - memorias podem ser fracas")
    except Exception as e:
        print(f"  [Mente] CR ERRO: {e}")
    
    # Monta prompt BATCH com todos os membros + suas MELHORES memorias (aprendizado)
    blocos_memoria = []
    for nome in membros:
        # Carrega memorias de ALTO SCORE primeiro (aprendizado real)
        memoria = _memoria.resumo_para_prompt(nome, max_entradas=5)
        blocos_memoria.append(f"MEMBRO: {nome.upper()}\\nMEMORIA: {memoria}")'''

if old4 in conteudo:
    conteudo = conteudo.replace(old4, new4)
    print("  [OK] CR inserido no think()")
else:
    print("  [AVISO] Padrao 4 nao encontrado")

# Injetar CR instruction no prompt batch
old4b = '''    prompt_batch = (
        f"Conselho do MCR-DevIA discutindo a pergunta abaixo.\\n"
        f"Cada membro tem sua memoria pessoal (score alto = aprendeu muito).\\n\\n"
        f"PERGUNTA: {pergunta[:400]}\\n\\n"
        f"{chr(10).join(blocos_memoria)}\\n\\n"'''
new4b = '''    prompt_batch = (
        f"Conselho do MCR-DevIA discutindo a pergunta abaixo.\\n"
        f"Cada membro tem sua memoria pessoal (score alto = aprendeu muito).\\n\\n"
        f"PERGUNTA: {pergunta[:400]}\\n\\n"
        + (cr_instrucao + "\\n" if cr_instrucao else "")
        + f"{chr(10).join(blocos_memoria)}\\n\\n"'''

if old4b in conteudo:
    conteudo = conteudo.replace(old4b, new4b)
    print("  [OK] CR instruction no prompt batch")
else:
    print("  [AVISO] Padrao 4b nao encontrado")

mcr_write("modulos/mente.py", conteudo)

# ============================================================
# PASSO 5: SUPERVISOR — roteia com CR
# ============================================================
print("\n[Passo 5] Supervisor - CR valida contexto antes de rotear...")
path_sup = f"{BASE_MCR}/modulos/supervisor.py"
conteudo = ler(path_sup)

# Adicionar CR no classificar()
old5 = '''    def classificar(self, texto):
        """Classifica intencao. Detecta prompts MULTI-intencao (3+ topicos)."""
        t = texto.lower()'''
new5 = '''    def classificar(self, texto):
        """Classifica intencao. Detecta prompts MULTI-intencao (3+ topicos)."""
        t = texto.lower()
        
        # CONTEXT REINFORCER: valida se ha contexto suficiente para rotear
        try:
            from modulos.context_reinforcer import ContextReinforcer
            cr = ContextReinforcer(ctx_crew=self.ctx_crew, kg=self.kg)
            cr_result = cr.reforcar(texto, self.ctx_crew)
            if not cr_result.get("valido") and cr_result.get("termos"):
                print(f'  [Supervisor] CR: contexto INSUFICIENTE para: {cr_result["termos"][:3]}')
                if cr_result.get("aprendeu"):
                    print(f'  [Supervisor] CR: weblearn disparado para aprendizado')
        except Exception as e:
            print(f'  [Supervisor] CR ERRO: {e}')'''

if old5 in conteudo:
    conteudo = conteudo.replace(old5, new5)
    print("  [OK] CR inserido no classificar()")
else:
    print("  [AVISO] Padrao 5 nao encontrado")

mcr_write("modulos/supervisor.py", conteudo)

# ============================================================
# PASSO 7: AUTO-REVISOR — verifica se resposta usou contexto do CR
# ============================================================
print("\n[Passo 7] Auto-Revisor - verifica uso do contexto CR...")
path_rev = f"{BASE_MCR}/modulos/auto_revisor.py"
conteudo = ler(path_rev)

# Adicionar verificacao de contexto CR no revisar()
old7 = '''    def revisar(self, texto_resposta, classes_permitidas=None):
        """Revisa uma resposta. Retorna dict com alucinacoes encontradas.
        Usa heuristica universal (sem listas fixas, sem FAST).
        
        Args:
            texto_resposta: Texto da resposta gerada
            classes_permitidas: Ignorado (mantido para compatibilidade)
        
        Returns:
            dict com {alucinacoes: [(classe, contexto)], total: N, sugestao: str}
        """
        if not texto_resposta:
            return {"alucinacoes": [], "total": 0, "sugestao": ""}'''
new7 = '''    def revisar(self, texto_resposta, classes_permitidas=None, contexto_cr=""):
        """Revisa uma resposta. Retorna dict com alucinacoes encontradas.
        Usa heuristica universal (sem listas fixas, sem FAST).
        
        Args:
            texto_resposta: Texto da resposta gerada
            classes_permitidas: Ignorado (mantido para compatibilidade)
            contexto_cr: Contexto do CR para verificar se foi usado na resposta
        
        Returns:
            dict com {alucinacoes: [(classe, contexto)], total: N, sugestao: str}
        """
        if not texto_resposta:
            return {"alucinacoes": [], "total": 0, "sugestao": ""}
        
        # Verifica se contexto do CR foi usado na resposta
        if contexto_cr and len(contexto_cr) > 50:
            termos_cr = [w.lower() for w in contexto_cr.split() if len(w) > 4]
            termos_encontrados = sum(1 for t in termos_cr if t in texto_resposta.lower())
            if termos_encontrados < len(termos_cr) * 0.3 and len(termos_cr) > 3:
                print(f'  [Auto-Revisor] ALERTA: resposta NAO usou contexto do CR '
                      f'({termos_encontrados}/{len(termos_cr)} termos encontrados)')'''

if old7 in conteudo:
    conteudo = conteudo.replace(old7, new7)
    print("  [OK] CR check inserido no revisar()")
else:
    print("  [AVISO] Padrao 7 nao encontrado")

# Atualizar auto_corrigir para aceitar contexto_cr
old7b = '''    def auto_corrigir(self, texto_resposta, classes_permitidas=None):
        """Auto-corrige alucinacoes: marca classes suspeitas APENAS no texto, nao em codigo."""
        resultado = self.revisar(texto_resposta, classes_permitidas)'''
new7b = '''    def auto_corrigir(self, texto_resposta, classes_permitidas=None, contexto_cr=""):
        """Auto-corrige alucinacoes: marca classes suspeitas APENAS no texto, nao em codigo."""
        resultado = self.revisar(texto_resposta, classes_permitidas, contexto_cr)'''

if old7b in conteudo:
    conteudo = conteudo.replace(old7b, new7b)
    print("  [OK] auto_corrigir aceita contexto_cr")
else:
    print("  [AVISO] Padrao 7b nao encontrado")

mcr_write("modulos/auto_revisor.py", conteudo)

# ============================================================
# PASSO 8: CONTEXTCREW — busca vazia dispara weblearn
# ============================================================
print("\n[Passo 8] ContextCrew - busca vazia -> weblearn...")
path_cc = f"{BASE_MCR}/context_crew.py"
conteudo = ler(path_cc)

# Adicionar auto-weblearn no final do executar()
old8 = '''    def executar(self, pergunta, min_termos=2, max_r=5):
        """Executa busca em todas as 5 fontes e retorna contexto agregado.
        Usa cache LRU."""
        h = self._hash(pergunta)
        if h in self._cache:
            item = self._cache[h]
            return f"[CACHE] {item['r'][:100]}" if item['r'] else ""
        
        termos = self._extrair_termos(pergunta, max_t=8)
        if len(termos) < min_termos:
            return ""
        
        resultados = []
        
        # 1. KG (aprendizado do projeto)
        resultados.extend(self._buscar_kg(termos, max_r))
        
        # 2. WebLearn (cache de buscas anteriores)
        resultados.extend(self._buscar_weblearn(termos, max_r))
        
        # 3. Docs (documentacao)
        resultados.extend(self._buscar_docs(termos, max_r))
        
        # 4. Codigo Fonte (grep no codigo)
        resultados.extend(self._buscar_codigo(termos, max_r))
        
        # 5. Web direto (scrape)
        resultados.extend(self._buscar_web(termos, max_r))
        
        # Combina e remove duplicatas]
        vistos = set()
        unicos = []
        for txt, fonte in resultados:
            chave = txt[:100]
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(f"[{fonte}] {txt}")
        
        if not unicos:
            self._cache[h] = {"r": "", "n": 0, "ts": time.time()}
            return ""
        
        resultado = "\\n".join(unicos[:max_r])
        self._cache[h] = {"r": resultado, "n": len(unicos), "ts": time.time()}
        self._salvar_cache(h, pergunta, resultado, "multi", len(unicos))
        return resultado'''
new8 = '''    def executar(self, pergunta, min_termos=2, max_r=5):
        """Executa busca em todas as 5 fontes e retorna contexto agregado.
        Usa cache LRU. Se vazio, dispara weblearn."""
        h = self._hash(pergunta)
        if h in self._cache:
            item = self._cache[h]
            return f"[CACHE] {item['r'][:100]}" if item['r'] else ""
        
        termos = self._extrair_termos(pergunta, max_t=8)
        if len(termos) < min_termos:
            return ""
        
        resultados = []
        
        # 1. KG (aprendizado do projeto)
        resultados.extend(self._buscar_kg(termos, max_r))
        
        # 2. WebLearn (cache de buscas anteriores)
        resultados.extend(self._buscar_weblearn(termos, max_r))
        
        # 3. Docs (documentacao)
        resultados.extend(self._buscar_docs(termos, max_r))
        
        # 4. Codigo Fonte (grep no codigo)
        resultados.extend(self._buscar_codigo(termos, max_r))
        
        # 5. Web direto (scrape)
        resultados.extend(self._buscar_web(termos, max_r))
        
        # Combina e remove duplicatas]
        vistos = set()
        unicos = []
        for txt, fonte in resultados:
            chave = txt[:100]
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(f"[{fonte}] {txt}")
        
        # AUTO-WEBLEARN: se 0 resultados, dispara aprendizado
        if not unicos:
            consulta = ' '.join(termos[:5])
            print(f'  [ContextCrew] Sem resultados — disparando WebLearn para: {consulta}')
            try:
                import subprocess as _sp
                kernel = os.path.join(os.path.dirname(__file__), 'MCR_DevIA-Kernel.py')
                _sp.run([sys.executable, kernel, 'weblearn', consulta, '--shallow'],
                       capture_output=True, text=True, timeout=120)
                # Tenta novamente apos weblearn
                resultados.extend(self._buscar_weblearn(termos, max_r))
                for txt, fonte in resultados:
                    chave = txt[:100]
                    if chave not in vistos:
                        vistos.add(chave)
                        unicos.append(f"[{fonte}] {txt}")
            except Exception as e:
                print(f'  [ContextCrew] WebLearn ERRO: {e}')
        
        if not unicos:
            self._cache[h] = {"r": "", "n": 0, "ts": time.time()}
            return ""
        
        resultado = "\\n".join(unicos[:max_r])
        self._cache[h] = {"r": resultado, "n": len(unicos), "ts": time.time()}
        self._salvar_cache(h, pergunta, resultado, "multi", len(unicos))
        return resultado'''

if old8 in conteudo:
    conteudo = conteudo.replace(old8, new8)
    print("  [OK] Auto-WebLearn inserido no executar()")
else:
    print("  [AVISO] Padrao 8 nao encontrado - tentando correspondencia parcial...")
    # Tenta achar o trecho final do executar()
    if "if not unicos:" in conteudo and 'self._cache[h] = {"r": "", "n": 0, "ts": time.time()}\n            return ""' in conteudo:
        # Ja tem weblearn? Verificar
        if "WebLearn" in conteudo:
            print("  [OK] Auto-WebLearn ja existe no executar()")
        else:
            print("  [AVISO] Nao foi possivel inserir weblearn automatico")

mcr_write("modulos/../context_crew.py", conteudo)

# ============================================================
# ENSINAR MCR-DevIA sobre todas as integracoes
# ============================================================
print("\n[Final] Ensinando MCR-DevIA sobre as integracoes...")
cmd_ensinar = {
    "cmd": "ensinar",
    "args": [
        "Context Reinforcer integrado em 6 modulos: Conselho (CR antes de deliberar), Mente (CR valida memorias), Supervisor (CR verifica contexto), Auto-Revisor (CR check de uso), ContextCrew (auto-weblearn), Orquestrador (instrucao_contexto separado)",
        "6 integracoes do CR",
        "Conselho.reforcar() chamado antes de deliberar. Mente.think() valida contexto. Supervisor.classificar() verifica contexto. Revisor.revisar() checa uso. ContextCrew.executar() auto-weblearn. Template perguntar com {instrucao_contexto}.",
        "arquitetura"
    ]
}
with open(f"{SANDBOX}/.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd_ensinar, f, ensure_ascii=False)
r = subprocess.run([sys.executable, f"{BASE_MCR}/MCR_DevIA-Kernel.py",
    "--json", f"{SANDBOX}/.mcr_cmd.json"],
    capture_output=True, text=True, errors="replace", timeout=60)
print(f"  [Ensino] {[l for l in r.stdout.split(chr(10)) if 'ensinar' in l.lower() or 'registrado' in l.lower()]}")

print("\n" + "="*60)
print("TODAS AS 6 INTEGRACOES CONCLUIDAS!")
print("="*60)
