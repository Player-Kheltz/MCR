"""MarkovRouter — estado atual → proximo estado/acao via Markov puro.
APRENDIZADO REAL com MCR + persistencia JSON."""
import sys, os, re, json
from typing import List, Dict, Optional

_MK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "router_markov.json")

def _carregar_mk():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from MCR import MCR
        mk = MCR("router_markov")
        if os.path.exists(_MK_PATH):
            try:
                with open(_MK_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'freq' in data: mk.freq = data['freq']
                if 'total' in data: mk.total = data['total']
            except: pass
        return mk
    except Exception:
        return None

def _salvar_mk(mk):
    if mk is None: return
    try:
        os.makedirs(os.path.dirname(_MK_PATH), exist_ok=True)
        data = {'freq': mk.freq if hasattr(mk, 'freq') else {},
                'total': mk.total if hasattr(mk, 'total') else 0}
        with open(_MK_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass


class MarkovRouter:
    """Decide a SEQUENCIA de acoes baseada no estado atual + MCR real.
    Aprende com cada execucao: sucesso reforca rota, falha diminui peso.
    Persiste em JSON."""
    
    SEEDS = [
        ("classe:analisar_bug_conf:alta_cache:miss", ["cmd_read", "code_analyzer", "llm_gerar"]),
        ("classe:analisar_bug_conf:alta_cache:hit", ["cmd_review"]),
        ("classe:analisar_bug_conf:baixa", ["cmd_grep", "cmd_read", "code_analyzer", "llm_gerar"]),
        ("classe:analisar_performance_conf:alta", ["cmd_grep", "cmd_read", "code_analyzer", "cmd_review"]),
        ("classe:analisar_performance_conf:baixa", ["cmd_read", "code_analyzer", "llm_gerar"]),
        ("classe:revisar_codigo_conf:alta", ["cmd_read", "code_analyzer", "cmd_review"]),
        ("classe:revisar_codigo_conf:baixa", ["cmd_read", "code_analyzer", "llm_gerar"]),
        ("classe:criar_codigo_conf:alta", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "cmd_write"]),
        ("classe:criar_codigo_conf:baixa", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "llm_gerar", "cmd_write"]),
        ("classe:criar_habilidade_spa_conf:alta", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:criar_habilidade_spa_conf:baixa", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:criar_npc_conf:alta", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "llm_gerar", "cmd_write"]),
        ("classe:criar_npc_conf:baixa", ["cmd_grep", "cmd_read", "template_extractor", "deterministic_filler", "llm_gerar", "cmd_write"]),
        ("classe:criar_quest_conf:alta", ["context_crew", "llm_gerar", "pos_processamento"]),
        ("classe:criar_quest_conf:baixa", ["cmd_grep", "cmd_read", "context_crew", "llm_gerar", "pos_processamento"]),
        ("classe:ler_arquivo_conf:alta", ["cmd_read"]),
        ("classe:ler_arquivo_conf:baixa", ["cmd_grep", "cmd_read"]),
        ("classe:explicar_conceito_conf:alta", ["context_crew", "llm_gerar"]),
        ("classe:explicar_conceito_conf:baixa", ["llm_gerar"]),
        ("classe:busca_informacao_conf:alta", ["cmd_grep", "cmd_read"]),
        ("classe:busca_informacao_conf:baixa", ["cmd_grep", "cmd_read", "llm_gerar"]),
        ("classe:traduzir_texto_conf:alta", ["llm_gerar"]),
        ("classe:traduzir_texto_conf:baixa", ["context_crew", "llm_gerar"]),
        ("classe:criar_monster_conf:alta", ["cmd_grep", "cmd_read", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:criar_monster_conf:baixa", ["cmd_grep", "cmd_read", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:criar_sistema_conf:alta", ["context_crew", "cmd_grep", "cmd_read", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:criar_sistema_conf:baixa", ["context_crew", "cmd_grep", "cmd_read", "llm_gerar", "pos_processamento", "cmd_write"]),
        ("classe:desconhecido_conf:*", ["context_crew", "llm_gerar"]),
        ("classe:gerar_relatorio_conf:alta", ["cmd_grep", "cmd_read", "cmd_review", "llm_gerar", "cmd_write"]),
        ("classe:gerar_relatorio_conf:baixa", ["cmd_grep", "cmd_read", "pattern_engine", "llm_gerar", "cmd_write"]),
    ]
    
    FALLBACK_ACAO = ["llm_gerar"]
    
    def __init__(self):
        self.mk = _carregar_mk()  # MCR real com persistencia
        self.historico: List[str] = []
        self._reg = None
    
    def _nova_rota_aprendida(self, estado: str) -> Optional[List[str]]:
        """Consulta MCR para rotas aprendidas em execucoes anteriores bem-sucedidas."""
        if not self.mk: return None
        try:
            acao_pred, conf = self.mk.predizer(estado)
            if acao_pred and conf > 0.3:
                acoes = acao_pred.split('_')
                return acoes
        except: pass
        return None
    
    def _get_tool_registry(self):
        if self._reg is None:
            try:
                tool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "..", "Projeto MCR", "historia", "scripts", "mcr_devia", "knowledge")
                if os.path.isdir(tool_path):
                    sys.path.insert(0, tool_path)
                    from tool_registry import get_registry
                    self._reg = get_registry()
            except: pass
        return self._reg
    
    def decidir(self, classe: str, confianca: float, cache_hit: bool = False) -> List[str]:
        estado = "classe:%s_conf:%s_cache:%s" % (classe, "alta" if confianca >= 0.5 else "baixa", "hit" if cache_hit else "miss")
        self.historico.append(estado)
        
        # Match por seed estatica (prioritario)
        for seed_estado, acoes in self.SEEDS:
            if seed_estado == estado: return list(acoes)
        for seed_estado, acoes in self.SEEDS:
            if self._match_coringa(seed_estado, estado): return list(acoes)
        
        # Se confianca baixa, consulta MCR por rotas que funcionaram antes
        if confianca < 0.5:
            rota_aprendida = self._nova_rota_aprendida(estado)
            if rota_aprendida: return rota_aprendida
        
        # ToolRegistry fallback
        reg = self._get_tool_registry()
        if reg:
            tools = reg.buscar_por_palavras_chave(classe)
            if tools and tools[0].comandos:
                return list(tools[0].comandos)
        
        return list(self.FALLBACK_ACAO)
    
    def _match_coringa(self, padrao: str, estado: str) -> bool:
        partes_p = padrao.split('_')
        partes_e = estado.split('_')
        for pp, pe in zip(partes_p, partes_e):
            if pp == '*': continue
            if pp != pe: return False
        return len(partes_p) <= len(partes_e)
    
    def aprender(self, estado: str, acao_executada: List[str], sucesso: bool):
        """Aprende com resultado real. Sucesso alimenta MCR, falha registra para evitar no futuro."""
        if not self.mk: return
        acao_str = "_".join(acao_executada)
        # Reforca a rota se sucesso
        if sucesso:
            self.mk.aprender(estado, acao_str)
            # Reforco extra: aprende multiplas vezes
            for _ in range(3):
                self.mk.aprender(estado, acao_str)
        else:
            # Falha: aprende estado -> FALHA para evitar
            self.mk.aprender(estado, "FALHA__" + acao_str)
        _salvar_mk(self.mk)
    
    def ultimos_estados(self, n: int = 5) -> List[str]:
        return self.historico[-n:]
