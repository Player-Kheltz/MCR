"""MasterAgent — Ciclo PERCEBER->PLANEJAR->EXECUTAR->INTEGRAR->APRENDER.
Leve, usa o roteamento padrao do MarkovRouter + PipelineExecutor,
sem duplicar a pipeline linear.
"""
import os, sys, json, time, re

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from MarkovRouter import MarkovRouter
from PipelineExecutor import PipelineExecutor


class MasterAgent:
    """Agente universal para tarefas complexas.
    Ciclo: PERCEBER -> PLANEJAR -> EXECUTAR -> INTEGRAR -> APRENDER
    Usa o roteamento padrao do sistema, mas com auto-correcao em loop.
    """
    
    def __init__(self, processar_func=None, llm=None, cerebro=None, kernel=None):
        self.processar_func = processar_func
        self._llm = llm
        self._cerebro = cerebro
        self._kernel = kernel
        self._router = MarkovRouter()
        self._max_tentativas = 3
        self._passos = []
        self._historico = []
        self._memoria = None
        try:
            from episodic_memory import EpisodicMemory
            self._memoria = EpisodicMemory()
        except:
            pass
    
    def executar(self, pergunta: str, classe: str = "", confianca: float = 0.0) -> dict:
        """Ciclo completo, UMA execucao de pipeline."""
        t0 = time.time()
        self._passos = []
        self._historico = []
        
        # --- PERCEBER ---
        self._log("PERCEBER", "Classe: %s, conf: %.2f" % (classe, confianca))
        tarefas = self._perceber(pergunta, classe)
        tarefas["confianca"] = confianca  # Passa confianca real para o planejador
        
        resultado_final = {"resposta": "", "erro": None, "passos": []}
        
        for tentativa in range(self._max_tentativas):
            # --- PLANEJAR (usa router padrao) ---
            acoes = self._planejar(pergunta, classe, tarefas, tentativa)
            self._log("PLANEJAR", "Tentativa %d: %s" % (tentativa+1, acoes))
            
            # --- EXECUTAR (pipeline unica via PipelineExecutor) ---
            ctx = self._executar_pipeline(pergunta, classe, acoes)
            self._log("EXECUTAR", "Pipeline concluida")
            
            # Extrai resposta
            resposta = (ctx.get("llm_output", "") or 
                       ctx.get("preenchido", "") or
                       ctx.get("stdout", ""))
            resultado_final["resposta"] = resposta
            
            # --- INTEGRAR ---
            erros = [p for p in self._passos if p.get("erro")]
            if not erros and resposta:
                self._log("INTEGRAR", "Sucesso, %d chars" % len(resposta))
                break
            
            if tentativa < self._max_tentativas - 1:
                self._log("APRENDER", "Tentativa %d falhou, buscando RAG..." % (tentativa+1))
                try:
                    from rag_mcr import MCRRAG
                    rag = MCRRAG()
                    extra = rag.contexto_para_prompt(pergunta, k=2)
                    if extra:
                        tarefas["ctx_extra"] = extra
                except:
                    pass
        
        # --- APRENDER ---
        self._aprender(pergunta, classe, resultado_final, tentativa)
        
        resultado_final["tempo"] = round(time.time() - t0, 2)
        return resultado_final
    
    def _perceber(self, pergunta: str, classe: str) -> dict:
        tarefas = {"classe": classe, "ctx_extra": ""}
        if self._memoria:
            try:
                eps = self._memoria.buscar(pergunta, n=2)
                if eps:
                    top = eps[0]
                    if isinstance(top, dict):
                        tarefas["memoria"] = top.get("resultado", "")[:300]
            except:
                pass
        return tarefas
    
    def _planejar(self, pergunta: str, classe: str, tarefas: dict, tentativa: int) -> list:
        """Plano = router padrao + RAG extra em retentativas."""
        # Usa a confianca recebida para routing (nao hardcoded)
        conf_uso = max(tarefas.get('confianca', 0.9), 0.1)
        acoes = list(self._router.decidir(classe, conf_uso))
        if tarefas.get("memoria"):
            acoes.insert(0, "context_crew")
        # Em retentativas, busca RAG profundo
        if tentativa > 0:
            if "cmd_grep" not in acoes:
                acoes.insert(1, "cmd_grep")
            try:
                from rag_mcr import MCRRAG
                _extra = MCRRAG().contexto_para_prompt(pergunta, k=3)
                if _extra:
                    tarefas["ctx_extra"] = _extra
            except: pass
        return acoes
    
    def _executar_pipeline(self, pergunta: str, classe: str, acoes: list) -> dict:
        pipe = PipelineExecutor(kernel=self._kernel)
        pipe._llm = self._llm
        pipe._classe = classe
        pipe._cerebro = self._cerebro
        pipe._modelo = "qwen2.5-coder:7b"
        
        ctx = pipe.executar(acoes, pergunta)
        
        for a in acoes:
            res = {"comando": a, "sucesso": True, "erro": None}
            if ctx.get("erro"):
                res["erro"] = ctx["erro"]
                res["sucesso"] = False
            self._passos.append(res)
        
        return ctx
    
    def _aprender(self, pergunta: str, classe: str, resultado: dict, tentativas: int):
        sucesso = bool(resultado.get("resposta")) and not any(p.get("erro") for p in self._passos)
        if self._memoria and sucesso:
            try:
                self._memoria.registrar(pergunta, resultado.get("resposta", "")[:300], classe)
            except:
                pass
        if self._cerebro and hasattr(self._cerebro, 'kg') and sucesso:
            try:
                self._cerebro.kg.aprender(
                    erro="MasterAgent: %s em %d tentativas" % (classe, tentativas+1),
                    causa="Tarefa: %s" % pergunta[:50],
                    solucao=resultado.get("resposta", "")[:200],
                    ctx=classe
                )
            except:
                pass
    
    def _log(self, fase: str, msg: str):
        self._historico.append({"fase": fase, "msg": msg, "ts": time.time()})
        print("  [MasterAgent:%s] %s" % (fase, msg))
    
    def historico(self) -> list:
        return self._historico
