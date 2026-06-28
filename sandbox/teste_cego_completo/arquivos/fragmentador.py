"""Modulo: Fragmentador - Pipeline de geracao de codigo sob medida."""
import os, re, math, json, urllib.request

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')

def init_module(contexto):
    return 'fragmentador', Fragmentador()

class Fragmentador:
    """Pipeline de geracao de codigo com fragmentos dinamicos."""
    
    def executar(self, descricao):
        nome_arquivo = self._extrair_nome(descricao)
        linhas_est = self._detectar_tamanho(descricao)
        num_frag = max(1, math.ceil(linhas_est / 80))
        
        print(f'[Fragmentador] {nome_arquivo} | ~{linhas_est} linhas | {num_frag} fragmento(s)')
        
        if num_frag == 1:
            codigo = self._gerar_direto(descricao)
        else:
            codigo = self._gerar_fragmentado(descricao, num_frag)
        
        if codigo:
            caminho = os.path.join(SANDBOX, nome_arquivo)
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(codigo)
            print(f'[Fragmentador] OK: {caminho} ({len(codigo.splitlines())} linhas)')
            return caminho
        return None
    
    def _extrair_nome(self, desc):
        nome = re.search(r'(?:chamado|criar|em|como)\s+([\w\-]+\.(?:py|md|json|xml|lua|txt))', desc.lower())
        if nome: return nome.group(1)
        nome = re.search(r'(\w+\.py)', desc.lower())
        if nome: return nome.group(1)
        return f'script_{hash(desc) % 10000}.py'
    
    def _detectar_tamanho(self, desc):
        desc_lower = desc.lower()
        if any(p in desc_lower for p in ['sistema', 'framework', 'modulo completo', 'motor', 'engine']):
            return 300
        if any(p in desc_lower for p in ['classe', 'funcao', 'modulo', 'utilitario', 'ferramenta']):
            return 80
        if any(p in desc_lower for p in ['script', 'exemplo', 'teste', 'hello world', 'pequeno']):
            return 15
        return max(10, min(200, len(desc) // 20))
    
    def _gerar_direto(self, desc):
        prompt = f"Gere codigo Python completo para:\n{desc}\n\nRetorne APENAS o codigo em ```python ... ```"
        resp = self._ia(prompt, 0.3)
        m = re.search(r'```(?:python)?\s*\n(.+?)```', resp, re.DOTALL)
        return m.group(1).strip() if m else re.sub(r'```\w*\n?', '', resp).strip()
    
    def _gerar_fragmentado(self, desc, num_frag):
        fragmentos = []
        for i in range(num_frag):
            ctx = '\n'.join(fragmentos) if fragmentos else ''
            prompt = f"Gere codigo Python para:\n{desc}\n\nBloco {i+1}/{num_frag}.\n{'Contexto:\n' + ctx if ctx else ''}\nRetorne em ```python ... ```"
            resp = self._ia(prompt, 0.3)
            m = re.search(r'```(?:python)?\s*\n(.+?)```', resp, re.DOTALL)
            bloco = m.group(1).strip() if m else re.sub(r'```\w*\n?', '', resp).strip()
            if bloco: fragmentos.append(bloco)
        return '\n\n'.join(fragmentos) if fragmentos else None
    
    def _ia(self, prompt, temp=0.3):
        d = json.dumps({'model': 'qwen2.5-coder:7b', 'prompt': prompt, 'stream': False,
            'options': {'temperature': temp, 'num_ctx': 4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(r, timeout=120).read()).get('response', '')
