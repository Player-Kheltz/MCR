"""Context Reinforcer — Reforco de contexto universal para o MCR-DevIA.
Usa FAST para:
1. Extrair termos criticos da solicitacao (incluindo curtos como .lua, Oz)
2. Validar se o contexto do ContextCrew e relevante
3. Disparar weblearn se contexto insuficiente
4. Gerar instrucao de desambiguacao para o LLM

Integrado com: PipelineExecutor, Conselho, Mente, Supervisor, Orquestrador, Revisor.
"""
import os, sys, json, time, re, subprocess

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

def _fast(prompt, temp=0.15):
    """Chamada rapida ao modelo leve 1.5b."""
    try:
        import urllib.request as _ur
        OLLAMA = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
        d = json.dumps({'model': 'qwen2.5-coder:1.5b', 'prompt': prompt, 'stream': False,
            'options': {'temperature': temp, 'num_ctx': 2048, 'num_predict': 512}}).encode()
        r = _ur.Request(OLLAMA, data=d, headers={'Content-Type': 'application/json'})
        return (json.loads(_ur.urlopen(r, timeout=30).read()).get('response') or "").strip()
    except:
        return ""

class ContextReinforcer:
    """Reforca contexto usando FAST para extrair, validar, aprender e desambiguar."""
    
    def __init__(self, ctx_crew=None, kg=None):
        self.ctx_crew = ctx_crew
        self.kg = kg
    
    def extrair_termos(self, solicitacao: str) -> list:
        """Extrai termos combinando FAST + regex (garante cobertura total)."""
        # FAST: tenta extrair termos (pode alucinar, entao filtra)
        termos_fast = set()
        prompt = (
            "Quais os termos MAIS IMPORTANTES para buscar contexto?\n"
            "Retorne APENAS os termos separados por espaco:\n"
            f"Solicitacao: {solicitacao[:400]}"
        )
        resp = _fast(prompt, 0.15)
        if resp and len(resp) > 3:
            for t in resp.split():
                t = t.strip().strip(',.!?')
                if len(t) >= 2 and t.lower() in solicitacao.lower():
                    termos_fast.add(t)
        
        # Fallback/reforso: REGEX captura TUDO com 2+ chars
        termos_regex = set()
        for w in re.findall(r'[a-zA-Z.]{2,}', solicitacao):
            wl = w.lower()
            if wl not in ('de','para','que','com','uma','era','mais','como',
                          'por','seu','sua','tem','ela','ele','voce','me','te',
                          'se','nos','lhe','das','dos','nas','nem','mas'):
                termos_regex.add(w)
        
        # Combina FAST + regex
        termos = list(termos_fast | termos_regex)
        return termos[:8]
    
    def validar_contexto(self, solicitacao: str, contexto: str) -> bool:
        """FAST valida se o contexto do ContextCrew e relevante."""
        if not contexto or len(contexto) < 30:
            return False
        prompt = (
            "O contexto abaixo e RELEVANTE para responder a solicitacao?\n"
            "Responda APENAS: SIM ou NAO\n\n"
            f"Solicitacao: {solicitacao[:300]}\n\n"
            f"Contexto: {contexto[:500]}"
        )
        resp = _fast(prompt, 0.1)
        if resp:
            r = resp.strip().upper()
            if 'SIM' in r and 'NAO' not in r:
                return True
        return False
    
    def aprender(self, termos: list) -> bool:
        """Dispara weblearn se contexto insuficiente."""
        if not termos:
            return False
        consulta = ' '.join(termos[:5])
        print(f'  [CR] WebLearn para: {consulta[:60]}...')
        try:
            kernel = os.path.join(os.path.dirname(__file__), '..', 'MCR_DevIA-Kernel.py')
            r = subprocess.run(
                [sys.executable, kernel, 'weblearn', consulta, '--shallow'],
                capture_output=True, text=True, timeout=120
            )
            return 'APRENDIZADO' in (r.stdout or '') or 'registrado' in (r.stdout or '').lower()
        except:
            return False
    
    def _carregar_identidade(self) -> str:
        """Carrega MCR_IDENTITY.md para contexto."""
        try:
            id_path = os.path.join(BASE, 'docs', 'MCR_IDENTITY.md')
            if os.path.exists(id_path):
                with open(id_path, 'r', encoding='utf-8') as f:
                    return f.read()[:600]
        except:
            pass
        return ""
    
    def gerar_instrucao(self, solicitacao: str) -> str:
        """Gera instrucao de desambiguacao para o LLM.
        Usa identidade do projeto para evitar alucinacao de siglas.
        Usa SEMPRE framing POSITIVO — nunca menciona termos errados.
        Ex: '.lua refere-se a linguagem de programacao Lua'"""
        identidade = self._carregar_identidade()
        prompt = (
            "Contexto do PROJETO:\n"
            f"{identidade[:400]}\n\n"
            "A solicitacao abaixo pode ter termos que precisam de contexto.\n"
            "Gere UMA FRASE CURTA explicando APENAS o significado CORRETO dos termos.\n"
            "USE SEMPRE afirmacoes positivas. NUNCA mencione o que algo NAO e.\n"
            "Ex: '.lua e a linguagem de script Lua usada no OTClient.'\n"
            "Ex: 'MCR e um servidor customizado de Tibia baseado em Canary.'\n\n"
            f"Solicitacao: {solicitacao[:400]}\n\n"
            "Instrucao (uma frase, apenas afirmacoes positivas):"
        )
        resp = _fast(prompt, 0.2)
        if resp and len(resp) > 10:
            return f"\n[INSTRUCAO] {resp.strip()}\n"
        return ""
    
    def reforcar(self, solicitacao: str, ctx_crew_obj=None) -> dict:
        """Ciclo completo de reforco de contexto para uma solicitacao.
        Retorna {termos, contexto, valido, instrucao, aprendeu}."""
        resultado = {
            'termos': [],
            'contexto': '',
            'valido': False,
            'instrucao': '',
            'aprendeu': False,
        }
        
        # 1. Extrai termos
        termos = self.extrair_termos(solicitacao)
        resultado['termos'] = termos
        print(f'  [CR] Termos extraidos: {termos}')
        if not termos:
            print(f'  [CR] Sem termos para buscar')
            return resultado
        
        # 2. Busca contexto
        cc = ctx_crew_obj or self.ctx_crew
        if cc:
            try:
                ctx = cc.executar(' '.join(termos))
                resultado['contexto'] = ctx or ''
            except:
                pass
        
        # 3. Valida contexto
        resultado['valido'] = self.validar_contexto(solicitacao, resultado['contexto'])
        
        # 4. Se invalido, tenta weblearn
        if not resultado['valido'] and termos:
            aprendido = self.aprender(termos)
            resultado['aprendeu'] = aprendido
            if aprendido and cc:
                try:
                    ctx = cc.executar(' '.join(termos))
                    resultado['contexto'] = ctx or ''
                    resultado['valido'] = self.validar_contexto(solicitacao, resultado['contexto'])
                except:
                    pass
        
        # 5. Gera instrucao de desambiguacao
        resultado['instrucao'] = self.gerar_instrucao(solicitacao)
        if resultado['instrucao']:
            print(f'  [CR] Instrucao gerada: {resultado["instrucao"][:80].strip()}')
        
        return resultado


# Funcao de conveniencia para uso externo
def reforcar_contexto(solicitacao, ctx_crew=None, kg=None):
    cr = ContextReinforcer(ctx_crew=ctx_crew, kg=kg)
    return cr.reforcar(solicitacao, ctx_crew)
