"""MCR-DevIA — Debate Protocol v3: aceita orquestrador para prompts enriquecidos com contexto.
Sub-agentes: Propositor, Critico, Conector.
Se orquestrador disponivel, usa prompts com contexto; senao, fallback para fixos."""
import os, json, re, sys, time
import tempfile

DEBATE_DIR = os.path.join(tempfile.gettempdir(), "_mcr_debate")
os.makedirs(DEBATE_DIR, exist_ok=True)

class Debate:
    """Protocolo de debate entre sub-agentes via arquivos.
    Aceita orquestrador para prompts enriquecidos com contexto."""
    
    def __init__(self, tema, gerar=None, orquestrador=None):
        self.tema = tema
        self.gerar = gerar or self._gerar_padrao
        self.orquestrador = orquestrador
        self.rondas = 0
        self.historico = []
        self.conclusao = None
        self._limpar()
    
    def _gerar_padrao(self, prompt, temp=0.5):
        try:
            import urllib.request, json as _json
            OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
            d = _json.dumps({'model': 'qwen2.5-coder:7b', 'prompt': prompt,
                'stream': False, 'options': {'temperature': temp, 'num_ctx': 4096}}).encode()
            r = urllib.request.Request(OLLAMA_URL, data=d,
                headers={'Content-Type': 'application/json'})
            return _json.loads(urllib.request.urlopen(r, timeout=60).read()).get('response', '')
        except Exception as e:
            return f"[ERRO_IA: {e}]"
    
    def _limpar(self):
        for f in os.listdir(DEBATE_DIR):
            try: os.remove(os.path.join(DEBATE_DIR, f))
            except: pass
    
    def _escrever(self, arquivo, conteudo):
        with open(os.path.join(DEBATE_DIR, arquivo), "w", encoding="utf-8") as f:
            f.write(conteudo)
    
    def _ler(self, arquivo):
        path = os.path.join(DEBATE_DIR, arquivo)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
        return ""
    
    def _ia(self, prompt, temp=0.5):
        try:
            resp = self.gerar(prompt, temp)
            return (resp or "")[:1000]
        except:
            return "[ERRO]"
    
    def _via_orq(self, intencao, params, consulta=""):
        """Tenta usar orquestrador. Se nao disponivel, retorna None."""
        if not self.orquestrador:
            return None
        try:
            r = self.orquestrador.executar(intencao, params, consulta=consulta, temp=0.4)
            if r and r.get("sucesso"):
                return r.get("resposta", "")
        except:
            pass
        return None
    
    def propositor(self, tarefa):
        """Propoe uma solucao inicial (com orquestrador se disponivel)."""
        print(f"  [Propositor] Pensando em: {tarefa[:60]}...")
        resp = self._via_orq("conselho_estrategista", {
            "mcr": "MCR = servidor de Tibia baseado em Canary.",
            "ctx_crew": f"Contexto do projeto: MCR = servidor de Tibia baseado em Canary. Tarefa: {tarefa}",
            "kg": "", "pergunta": tarefa, "ctx_infinity": "",
        }, consulta=tarefa)
        
        if not resp:
            resp = self._ia(
                f"Contexto do projeto: MCR = servidor de Tibia baseado em Canary.\n"
                f"Proponha uma solucao para: {tarefa}. Seja especifico e tecnico.", 0.6)
        self._escrever("proposta.txt", resp)
        self.historico.append(("propositor", resp[:200]))
        return resp
    
    def critico(self):
        """Critica a proposta e sugere melhorias."""
        proposta = self._ler("proposta.txt")
        if not proposta: return
        print(f"  [Critico] Analisando proposta...")
        resp = self._via_orq("conselho_critico", {
            "mcr": "MCR = servidor de Tibia baseado em Canary.",
            "ctx_crew": f"Proposta: {proposta[:300]}", "kg": "",
            "pergunta": f"Critique esta proposta: {proposta[:200]}", "ctx_infinity": "",
        }, consulta="criticar proposta")
        
        if not resp:
            resp = self._ia(
                f"Contexto: MCR = servidor de Tibia baseado em Canary.\n"
                f"Critique esta proposta e sugira melhorias especificas:\n{proposta[:500]}", 0.7)
        self._escrever("critica.txt", resp)
        self.historico.append(("critico", resp[:200]))
        return resp
    
    def refinar(self):
        """Refina a proposta baseado na critica."""
        critica = self._ler("critica.txt")
        proposta = self._ler("proposta.txt")
        if not critica or not proposta: return
        print(f"  [Propositor] Refinando proposta...")
        
        resp = self._ia(
            f"Contexto: MCR = servidor de Tibia baseado em Canary.\n"
            f"Proposta original:\n{proposta[:300]}\n\nCritica:\n{critica[:300]}\n\n"
            f"Versao final refinada (incorpore a critica):", 0.5)
        self._escrever("proposta_final.txt", resp)
        self.historico.append(("refinado", resp[:200]))
        return resp
    
    def conector(self):
        """Tenta conectar esta solucao com outras areas do KG."""
        print(f"  [Conector] Buscando conexoes com outros dominios...")
        final = self._ler("proposta_final.txt") or self._ler("proposta.txt")
        
        resp = self._ia(
            f"Contexto: MCR = servidor de Tibia baseado em Canary.\n"
            f"Esta solucao se conecta com outras areas do projeto?\n"
            f"Busque similaridades com SPA, SHC, dominios, etc:\n{final[:300]}", 0.6)
        self._escrever("conexoes.txt", resp)
        self.historico.append(("conector", resp[:200]))
        return resp
    
    def executar(self, tarefa, rodadas=2):
        """Ciclo completo: propor -> criticar -> refinar -> conectar."""
        print(f"\n{'='*60}")
        print(f"  DEBATE: {tarefa[:60]}...")
        print(f"  Rodadas: {rodadas}")
        print(f"{'='*60}")
        
        self.propositor(tarefa)
        for r in range(rodadas):
            print(f"\n  --- Rodada {r+1} ---")
            self.critico()
            self.refinar()
        self.conector()
        
        print(f"\n  [Executor] Executando solucao final...")
        proposta_final = self._ler("proposta_final.txt")
        print(f"\n  RESULTADO DO DEBATE:")
        print(f"  {proposta_final[:500]}")
        
        return proposta_final


if __name__ == "__main__":
    tarefa = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "melhorar o scanner mestre"
    
    debate = Debate(tarefa)
    resultado = debate.executar(tarefa)
    
    print(f"\n{'='*60}")
    print(f"  DEBATE CONCLUIDO - {len(debate.historico)} interacoes")
    for papel, msg in debate.historico:
        print(f"  [{papel}] {msg[:80]}")
    print(f"{'='*60}")
