#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR-DevIA Revived — Entry Point
================================
Unifica:
- MCRConversa + MCRAutoEvolution + MCRCodex (de MCR.py)
- MarkovDecider + EntropyValidator (de mcr_devia_v2.py)
- 52 comandos (do DevIA original kernel)
- MarkovRouter + Radar (novos)
- CommandCapture + AutorevisaoTracker (novos)
- TemplateExtractor + DeterministicFiller (novos)
- SeedLoader (treina com PERSONALIDADE.md)
- EncodingDetector (encoding correto por extensão)

Uso:
    python fix_mcr_devia_v2.py
    python fix_mcr_devia_v2.py "crie uma habilidade de gelo"
    python fix_mcr_devia_v2.py --status
"""
import sys, os, json, time, threading

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── Importa MCR.py (engine completo) ─────────────────────────────
sys.path.insert(0, BASE)
try:
    from MCR import MCR, MCRThreshold, MCRByteUtils, MCRConversa
    from MCR import MCRAutoEvolution, MCRCodex, MCRGenesis
    _MCR_OK = True
except ImportError as e:
    print(f"[Bridge] AVISO: MCR.py parcial: {e}")
    _MCR_OK = False

# ─── Importa mcr_devia_v2.py (MarkovDecider, EntropyValidator, LLM) ──
sys.path.insert(0, BASE)
# Corrige o import: em vez de ler MCR_AGI.py, importa direto do MCR.py
if _MCR_OK:
    # Já temos MCR, MCRThreshold, MCRByteUtils
    pass

from mcr_devia_v2 import MarkovDecider, EntropyValidator, LLM, MCRDevIAV2

# ─── Importa módulos novos ─────────────────────────────────────────
from MarkovRouter import MarkovRouter
from Radar import Radar
from CommandCapture import CommandCapture
from PipelineExecutor import PipelineExecutor
from AutorevisaoTracker import AutorevisaoTracker
from SeedLoader import carregar_tudo
from TemplateExtractor import extrair_template
from DeterministicFiller import preencher_template, preencher_gap
from EncodingDetector import detectar_encoding
from FeedbackFilter import FeedbackFilter

# ─── Importa Kernel do DevIA original (52 comandos) ────────────────
DEVIA_DIR = os.path.join(BASE, "..", "Projeto MCR", "historia", "scripts", "mcr_devia")
sys.path.insert(0, DEVIA_DIR)
sys.path.insert(0, os.path.join(DEVIA_DIR, "modulos"))

try:
    from kernel import MCRKernel
    _KERNEL_OK = True
except ImportError as e:
    print(f"[Bridge] AVISO: Kernel DevIA nao carregado: {e}")
    MCRKernel = None
    _KERNEL_OK = False


class MCRDevIARevived:
    """MCR-DevIA Revived — Markov decide, LLM gera, sistema aprende."""
    
    def __init__(self):
        # Núcleo Markov
        self.decider = MarkovDecider()
        self.validator = EntropyValidator()
        self.llm = LLM()
        
        # Router + Radar
        self.router = MarkovRouter()
        self.radar = Radar()
        
        # Captura + Pipeline + Revisão
        self.capture = CommandCapture()
        self.pipeline = None  # lazy init
        self.autorevisao = AutorevisaoTracker()
        
        # Filtro de qualidade
        self.filter = FeedbackFilter()
        
        # Template + Preenchimento
        self.template_extractor = extrair_template
        self.deterministic_filler = preencher_template
        
        # Kernel (52 comandos) — lazy init
        self._kernel = None
        self._kernel_inicializado = False
        
        # Cache do DevIA v2
        self.dev = MCRDevIAV2()
        
        # Auto-evolução (se MCR.py disponível)
        if _MCR_OK:
            self.auto_evol = MCRAutoEvolution(cerebro=None)
        else:
            self.auto_evol = None
    
    def _get_kernel(self):
        if not _KERNEL_OK or not MCRKernel:
            return None
        if not self._kernel_inicializado:
            try:
                self._kernel = MCRKernel()
                # Inicializacao simplificada: so carrega comandos, sem modulos
                self._kernel.loader.scan()
                self._kernel_inicializado = True
            except Exception as e:
                print(f"[Bridge] Kernel simplificado: {e}")
                self._kernel = None
        return self._kernel
        
        # Carrega seeds do PERSONALIDADE.md
        stats = carregar_tudo(self.decider)
        
        # Seeds de propósito geral (não específicas MCR)
        _seeds_gerais = [
            ("crie uma ", "criar_codigo"),
            ("cria um ", "criar_codigo"),
            ("faça um ", "criar_codigo"),
            ("implemente ", "criar_codigo"),
            ("gere um ", "criar_codigo"),
            ("crie um npc", "criar_npc"),
            ("crie uma habilidade", "criar_habilidade_spa"),
            ("crie uma quest", "criar_quest"),
            ("explique o que", "explicar_conceito"),
            ("o que e ", "explicar_conceito"),
            ("como funciona", "explicar_conceito"),
            ("defina ", "explicar_conceito"),
            ("descreva ", "explicar_conceito"),
            ("encontre ", "busca_informacao"),
            ("busque ", "busca_informacao"),
            ("procure ", "busca_informacao"),
            ("localize ", "busca_informacao"),
            ("onde esta ", "busca_informacao"),
            ("liste ", "busca_informacao"),
            ("leia ", "ler_arquivo"),
            ("mostre ", "ler_arquivo"),
            ("exiba ", "ler_arquivo"),
            ("abra ", "ler_arquivo"),
            ("traduza ", "traduzir_texto"),
            ("tradus ", "traduzir_texto"),
            ("verta para ", "traduzir_texto"),
            ("analise ", "analisar_bug"),
            ("revise ", "revisar_codigo"),
            ("audite ", "revisar_codigo"),
            ("encontre bugs", "analisar_bug"),
            ("encontre erros", "analisar_bug"),
            ("corrija ", "analisar_bug"),
            ("diagnostique ", "analisar_bug"),
            ("qual a diferenca", "explicar_conceito"),
            ("compare ", "explicar_conceito"),
            ("resuma ", "explicar_conceito"),
            ("crie um relatorio", "gerar_relatorio"),
            ("relatorio sobre", "gerar_relatorio"),
            ("compile ", "comando_sistema"),
            ("rode o build", "comando_sistema"),
            ("execute ", "comando_sistema"),
        ]
        for pergunta, classe in _seeds_gerais:
            self.decider.aprender(pergunta, classe)
        
        print(f"[Bridge] Seeds carregadas: {stats} + {len(_seeds_gerais)} gerais")
    
    def processar(self, entrada, forcar_llm=False):
        """Processa entrada e retorna resposta.
        
        Pipeline:
        1. MarkovDecider → classe
        2. MarkovRouter → pipeline de ações
        3. Executa pipeline (comandos + LLM)
        4. EntropyValidator → valida
        5. AutorevisaoTracker → gera seção
        6. Aprende (KG)
        """
        t0 = time.time()
        entrada = entrada.strip()
        
        if not entrada:
            return {"resposta": "", "tempo": 0}
        
        # 1. MarkovDecider classifica
        classe, conf = self.decider.classificar(entrada)
        tempo_markov = time.time() - t0
        
        # 2. MarkovRouter decide pipeline
        acoes = self.router.decidir(classe, conf)
        
        # Radar: verifica loop
        for acao in acoes:
            self.radar.alimentar(acao)
            if self.radar.em_loop():
                alt = self.radar.forcar_alternativa(["cmd_grep", "cmd_read", "llm_gerar"])
                if alt:
                    acoes.append(alt)
                    break
        
        # 3. Executa pipeline via PipelineExecutor
        if self.pipeline is None:
            from PipelineExecutor import PipelineExecutor
            self.pipeline = PipelineExecutor(kernel=self._get_kernel())
            # Registra LLM no pipeline
            self.pipeline._llm = self.llm
        
        contexto = self.pipeline.executar(acoes, entrada)
        stdout_acumulado = contexto.get("stdout", "")
        
        # Se LLM foi usado, pega resultado
        if contexto.get("llm_output"):
            stdout_acumulado += "\n" + contexto["llm_output"]
            resultado = {"resposta": contexto["llm_output"]}
        else:
            resultado = None
        
        # Se preenchimento deterministico foi feito, inclui
        if contexto.get("preenchido"):
            stdout_acumulado += "\n--- Template preenchido ---\n" + contexto["preenchido"][:200]
        
        # 4. Cache
        self.dev.cache_respostas[hash(entrada)] = (entrada, stdout_acumulado, classe)
        
        # 5. EntropyValidator
        validacao = self.validator.validar(entrada, stdout_acumulado[:1000])
        
        # 6. FeedbackFilter
        if self.filter.filtrar(entrada, stdout_acumulado, conf):
            self.decider.aprender(entrada, classe)
        
        # 7. Autorevisao
        self.autorevisao.registrar_doc("PERSONALIDADE.md")
        self.autorevisao.registrar_doc("mcr_devia_v2.py")
        
        tempo_total = time.time() - t0
        
        return {
            "resposta": stdout_acumulado or f"[{classe} conf={conf:.2f}]",
            "classe": classe,
            "confianca": round(conf, 3),
            "tempo": round(tempo_total, 4),
            "tempo_markov": round(tempo_markov, 6),
            "fonte": "llm" if isinstance(resultado, dict) and resultado.get('llm_usado') else "markov",
            "llm_usado": isinstance(resultado, dict) and resultado.get('llm_usado', False),
            "validacao": validacao,
            "acoes": acoes,
            "autorevisao": self.autorevisao.gerar() if self.autorevisao.arquivos_modificados else "",
        }
    
    def stats(self):
        return {
            "decider": self.decider.stats(),
            "validator": self.validator.stats(),
            "llm": self.llm.stats(),
            "filter": self.filter.stats(),
            "radar": self.radar.estado(),
        }


# ─── CLI ──────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    if "--status" in args:
        dev = MCRDevIARevived()
        print(json.dumps(dev.stats(), indent=2))
        return
    
    forcar_llm = "--llm" in args
    perguntas = [a for a in args if not a.startswith("--")]
    
    if perguntas:
        revived = MCRDevIARevived()
        for p in perguntas:
            r = revived.processar(p, forcar_llm=forcar_llm)
            if isinstance(r, dict):
                print(f"[revived] {r['classe']} conf={r['confianca']} "
                      f"acoes={r['acoes']} tempo={r['tempo']}s")
                print(f"  Resposta: {r['resposta'][:300]}")
            else:
                print(str(r)[:300])
        return
    
    # Modo interativo
    print("MCR-DevIA Revived — Markov decide, LLM gera, sistema aprende")
    print(f"MCR.py: {'OK' if _MCR_OK else 'parcial'} | Kernel: {'OK' if _KERNEL_OK else 'NOK'}")
    print("Digite 'sair' para encerrar. /status para estatisticas.")
    print()
    
    revived = MCRDevIARevived()
    
    while True:
        try:
            e = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAte logo!")
            break
        
        if not e:
            continue
        if e.lower() in ("sair", "exit", "quit"):
            break
        if e == "/status":
            print(json.dumps(revived.stats(), indent=2))
            continue
        
        r = revived.processar(e)
        if isinstance(r, dict):
            classe = r['classe']
            conf = r['confianca']
            tempo = r['tempo']
            llm = " [LLM]" if r.get('llm_usado') else ""
            val = r.get('validacao', {})
            val_tag = f" val={val.get('valida', '?')}" if val else ""
            print(f"  [{classe} conf={conf} {tempo:.2f}s{llm}{val_tag}]")
            print(f"  {r['resposta'][:500]}")
        else:
            print(f"  {str(r)[:500]}")


if __name__ == "__main__":
    main()
