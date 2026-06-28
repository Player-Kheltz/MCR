"""MCR-DevIA — Pipeline Dinâmica V2 (substitui Builder Infinito)
Detecta complexidade, extrai nome do arquivo, ContextCrew integrado.
So gera o necessario. Nada de 4 fragmentos fixos."""
import os, sys, json, re, math, urllib.request, shutil

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
OLLAMA_CTX = os.getenv('OLLAMA_CTX', '4096')
SANDBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def ia(prompt, temp=0.3, ctx=4096):
    try:
        d = json.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt,
            "stream": False, "options": {"temperature": temp, "num_ctx": ctx}}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d, headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(r, timeout=120).read()).get("response", "")
    except Exception as e:
        return f"[ERRO_IA: {e}]"

def estimar_tokens(texto):
    return len(texto) // 2

# ================================================================
# CONTEXTCREW INTEGRADO (import opcional)
# ================================================================
_contexto_cache = {}
def obter_contexto(consulta):
    """Usa ContextCrew se disponivel para enriquecer o contexto."""
    if consulta in _contexto_cache:
        return _contexto_cache[consulta]
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, 'scripts', 'mcr_devia'))
        from context_crew import ContextCrew
        crew = ContextCrew()
        ctx = crew.executar(consulta)
        _contexto_cache[consulta] = ctx
        return ctx
    except Exception:
        return None

# ================================================================
# PIPELINE DINÂMICA
# ================================================================

class PipelineDinamica:
    """Pipeline que avança so ate onde precisa.
    Etapas: extrair_nome -> ContextCrew -> detectar_complexidade -> gerar_direto -> validar.
    Nao gera 4 fragmentos fixos. Detecta se é script simples ou complexo."""
    
    def __init__(self, descricao):
        self.descricao = descricao
        self.nome_arquivo = None
        self.caminho_final = None
        self.status = {}
        self.contexto_crew = None
    
    def _extrair_nome_arquivo(self):
        """Extrai nome do arquivo da descricao (ex: 'criar foo.py com...' -> foo.py)."""
        # Procura por nomes de arquivo na descricao
        m = re.search(r'(?:chamado|criar|em|como)\s+([\w\-]+\.(?:py|md|json|xml|lua|txt|bat|ps1|sh))', self.descricao.lower())
        if m:
            self.nome_arquivo = m.group(1)
            return
        
        # Procura por qualquer palavra terminando em .py
        m = re.search(r'(\w+\.py)', self.descricao.lower())
        if m:
            self.nome_arquivo = m.group(1)
            return
        
        # Fallback: extrai palavra-chave + .py
        palavras = re.findall(r'\b([a-z]{3,20})\b', self.descricao.lower())
        # Pega a primeira palavra relevante (nao verbo)
        verbos = {'criar', 'fazer', 'gerar', 'adicionar', 'modificar', 'mudar', 'inserir', 'remover', 'deletar'}
        for p in palavras:
            if p not in verbos:
                self.nome_arquivo = f"{p}.py"
                return
        
        self.nome_arquivo = f"script_{hash(self.descricao) % 10000}.py"
    
    def _detectar_tamanho(self):
        """Estima quantas LINHAS usando heuristica Python (0 IA).
        Analisa descricao por palavras-chave de complexidade.
        Retorna: int linhas_estimadas"""
        desc = self.descricao.lower()
        
        # Se ContextCrew ja rodou, extrai dele
        if self.contexto_crew and len(self.contexto_crew) > 50:
            ctx_lower = self.contexto_crew.lower()
            if any(p in ctx_lower for p in ['simples', 'pequeno', 'curto', 'basico', 'trivial']):
                return 15
            if any(p in ctx_lower for p in ['complexo', 'grande', 'extenso', 'multi', 'varios']):
                return 150
            if any(p in ctx_lower for p in ['enorme', 'sistema', 'framework', 'arquitetura']):
                return 400
        
        # Heuristica por palavras-chave na descricao (0 IA)
        # Palavras que indicam complexidade ALTA
        complexo = ['sistema', 'framework', 'modulo completo', 'motor', 'engine',
                    'gerenciador', 'manager', 'interface completa', 'editor',
                    'compilador', 'interpretador', 'renderizador']
        if any(p in desc for p in complexo):
            return 300
        
        # Palavras que indicam complexidade MEDIA
        medio = ['classe', 'funcao', 'função', 'metodo', 'método', 'modulo', 'módulo',
                 'utilitario', 'utilitário', 'helper', 'ferramenta', 'tool',
                 'processar', 'gerenciar', 'validar', 'converter']
        if any(p in desc for p in medio):
            return 80
        
        # Palavras que indicam SIMPLES
        simples = ['script', 'funcao simples', 'função simples', 'exemplo', 'teste',
                   'hello world', 'pequeno', 'rapido', 'rápido']
        if any(p in desc for p in simples):
            return 15
        
        # Fallback: estimativa por tamanho da descricao
        # ~1 linha a cada 20 chars de descricao (media empirica)
        return max(10, min(200, len(desc) // 20))
    
    def _calcular_fragmentos(self, linhas_estimadas):
        """Calcula numero de fragmentos baseado no tamanho estimado.
        Cada fragmento gera ate 80 linhas de codigo.
        Returns: int numero_fragmentos"""
        fragmentos = max(1, math.ceil(linhas_estimadas / 80))
        return fragmentos
    
    def _gerar_direto(self):
        """Gera o codigo direto (sem fragmentacao) com ContextCrew como apoio."""
        # ContextCrew (ja obtido em executar(), reusa)
        ctx_str = f"\nContexto do projeto:\n{self.contexto_crew[:1500]}\n" if self.contexto_crew else ""
        
        prompt = (
            f"Gere um codigo Python completo para:\n{self.descricao}\n"
            f"{ctx_str}"
            f"\nRequisitos:\n"
            f"- Retorne APENAS o codigo, dentro de ```python ... ```\n"
            f"- Codigo valido e executavel\n"
            f"- Com docstrings e comentarios relevantes\n"
            f"- Nao gere mais do que o solicitado"
        )
        resp = ia(prompt, 0.3, ctx=4096)
        
        # Extrai de ``` se presente
        m = re.search(r'```(?:python)?\s*\n(.+?)```', resp, re.DOTALL)
        if m:
            return m.group(1).strip()
        
        # Fallback: remove ``` soltos
        codigo = re.sub(r'```\w*\n?', '', resp).strip()
        return codigo
    
    def _validar(self):
        """Valida compilacao e salva."""
        codigo = self.caminho_final
        if not codigo or not os.path.exists(codigo):
            return False
        
        with open(codigo, encoding='utf-8') as f:
            conteudo = f.read()
        
        if codigo.endswith('.py'):
            try:
                compile(conteudo, codigo, 'exec')
                print(f'  [OK] Compilacao valida!')
                self.status['compilacao'] = 'ok'
                return True
            except SyntaxError as e:
                print(f'  [ERRO] Erro de sintaxe: {e}')
                self.status['compilacao'] = f'erro: {e}'
                return False
        
        self.status['compilacao'] = 'ok'
        return True
    
    def executar(self):
        """Executa a pipeline completa."""
        print(f'[Pipeline] Iniciando: {self.descricao[:80]}...')
        
        # ETAPA 1: Extrair nome do arquivo
        self._extrair_nome_arquivo()
        print(f'  [Pipeline] Nome do arquivo: {self.nome_arquivo}')
        
        # ETAPA 2: ContextCrew (se disponivel, enriquece e ajuda a decidir fragmentacao)
        print(f'  [Pipeline] ContextCrew consultando...')
        ctx = obter_contexto(f"criar {self.nome_arquivo}: {self.descricao[:100]}")
        self.contexto_crew = ctx
        if ctx:
            print(f'  [Pipeline] Contexto obtido ({len(ctx)} chars)')

        # ETAPA 3: Estimar tamanho + calcular fragmentos DINAMICAMENTE (0 IA, heuristicas Python)
        linhas_est = self._detectar_tamanho()
        num_fragmentos = self._calcular_fragmentos(linhas_est)
        print(f'  [Pipeline] Tamanho estimado: ~{linhas_est} linhas -> {num_fragmentos} fragmento(s)')
        
        # ETAPA 4: Gerar codigo
        print(f'  [Pipeline] Gerando codigo ({num_fragmentos} fragmentos)...')
        
        if num_fragmentos == 1:
            # SIMPLES: gera direto, sem fragmentacao
            codigo = self._gerar_direto()
        else:
            # MULTIPLOS FRAGMENTOS: gera incrementalmente
            fragmentos_gerados = []
            for i in range(num_fragmentos):
                prefixo = f"BLOCO {i+1}/{num_fragmentos}"
                prompt = (
                    f"Gere codigo Python para: {self.descricao[:300]}\n"
                    f"{'Contexto:\n' + ctx[:1000] if ctx else ''}\n"
                    f"{'Fragmentos anteriores:\n' + '\n'.join(fragmentos_gerados) if fragmentos_gerados else ''}\n\n"
                    f"Este e o {prefixo}. Retorne APENAS este bloco de codigo, "
                    f"completo e compilavel individualmente. Use ```python ... ```"
                )
                resp = ia(prompt, 0.3, ctx=4096)
                m = re.search(r'```(?:python)?\s*\n(.+?)```', resp, re.DOTALL)
                bloco = m.group(1).strip() if m else re.sub(r'```\w*\n?', '', resp).strip()
                if bloco:
                    fragmentos_gerados.append(bloco)
                    print(f'  [Pipeline] Fragmento {i+1}: {len(bloco.splitlines())} linhas')
            
            codigo = '\n\n'.join(fragmentos_gerados) if fragmentos_gerados else self._gerar_direto()
        
        # Remove marcacoes residuais
        codigo = re.sub(r'```\w*\n?', '', codigo).strip()
        
        # Salva arquivo
        caminho = os.path.join(SANDBOX_DIR, self.nome_arquivo)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(codigo)
        
        self.caminho_final = caminho
        print(f'  [Pipeline] Codigo gerado: {len(codigo.splitlines())} linhas')
        
        # ETAPA 5: Validar
        if not self._validar():
            print(f'  [Pipeline] [FALHA] Validacao reprovada.')
            return None
        
        print(f'  [Pipeline] [OK] Concluido: {caminho}')
        return caminho
    
    def _executar_legado(self):
        """Fallback: usa o builder_infinito original para casos complexos."""
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        try:
            import builder_infinito_legacy
        except ImportError:
            pass
        os.chdir(old_cwd)


if __name__ == "__main__":
    descricao = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "gerar script padrao"
    
    print("=" * 60)
    print("  PIPELINE DINÂMICA V2")
    print("  Avança só até onde precisa. ContextCrew integrado.")
    print("=" * 60)
    
    pipeline = PipelineDinamica(descricao)
    caminho = pipeline.executar()
    
    if caminho:
        print(f"\n  Arquivo: {caminho}")
        print(f"  Status: {pipeline.status}")
    else:
        print(f"\n  [FALHA] Pipeline nao concluiu.")
