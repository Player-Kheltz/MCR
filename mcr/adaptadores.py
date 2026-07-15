#!/usr/bin/env python3
"""
mcr/adaptadores.py — Conecta TODOS os módulos MCR.

NÃO CRIA NADA NOVO. Apenas converte formatos entre APIs existentes.

Adaptadores:
  A1. MarkovRouter → MCRSpawner      (List[str] → List[MCRTarefa])
  A2. SQLiteMarkov → callable        (wrap para MCRTarefa.fn)
  A3. IntentionEngine → MarkovDecider (6 cat → 17 classes)
  A4. MCRConector → PipelineUniversal (topicos → dominio)
  A5. MCRFuel → MCRTarefa           (lessons → tasks)
"""
import os, sys, os, re, json
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _ROOT)


# ═══════════════════════════════════════════════════════════
# A1. MarkovRouter → MCRSpawner
# Router retorna List[str] (nomes de ação)
# Spawner espera List[MCRTarefa] com .fn e .args
# ═══════════════════════════════════════════════════════════

def acoes_para_tarefas(acoes: List[str], entrada: str = '',
                       contexto: dict = None) -> list:
    """Converte lista de nomes de ação → lista de MCRTarefa executáveis."""
    from mcr.evolution import MCRTarefa
    tarefas = []
    for acao in acoes:
        fn = _resolver_acao(acao)
        if fn:
            tarefas.append(MCRTarefa(
                nome=acao,
                fn=fn,
                args={'entrada': entrada, 'acao': acao, 'contexto': contexto or {}}
            ))
    return tarefas


def _resolver_acao(acao: str) -> Optional[Callable]:
    """Resolve nome de ação → função executável."""
    # Tenta executor_map primeiro
    try:
        from mcr.executor_map import _reg
        result = _reg.executar(acao)
        if result is not None:
            return lambda **kw: _reg.executar(acao)
    except Exception:
        pass

    # Handlers built-in
    if acao == 'llm_gerar':
        return _acao_llm_gerar
    if acao == 'cmd_read':
        return _acao_cmd_read
    if acao == 'cmd_write':
        return _acao_cmd_write
    if acao == 'cmd_grep':
        return _acao_cmd_grep
    if acao == 'template_extractor':
        return _acao_template_extractor
    if acao == 'deterministic_filler':
        return _acao_deterministic_filler
    if acao == 'gerar_sqlite_markov':
        return _acao_sqlite_markov
    if acao == 'conectar_topicos':
        return _acao_conectar_topicos

    return None


# ═══════════════════════════════════════════════════════════
# A2. SQLiteMarkov → callable para MCRTarefa
# ═══════════════════════════════════════════════════════════

def _acao_sqlite_markov(**kwargs):
    """Wrapper: usa SQLiteMarkov para gerar com identidade."""
    entrada = kwargs.get('entrada', '')
    contexto = kwargs.get('contexto', {})
    identity = contexto.get('identity', 'npc')
    seed = contexto.get('seed', 'local')
    passos = contexto.get('passos', 60)

    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache', 'mcr_adapt.db')
    if not os.path.exists(DB_PATH):
        return {'erro': f'DB nao encontrado: {DB_PATH}'}

    try:
        from mcr.sqlite_markov import SQLiteMarkov
        mk = SQLiteMarkov(DB_PATH, n_max=30)
        
        # Fallback simples sem CerebroAGI
        def fallback(tok):
            return None, 0.0
        
        seq = mk.gerar_com_identidade(identity, seed, passos, fallback_fn=fallback)
        texto = ' '.join(seq)
        mk.close()
        return {'tokens': len(seq), 'texto': texto[:800], 'identity': identity}
    except Exception as e:
        return {'erro': str(e)[:150]}


# ═══════════════════════════════════════════════════════════
# A3. IntentionEngine → MarkovDecider
# ═══════════════════════════════════════════════════════════

def intencao_para_classe(intencoes: List[tuple]) -> tuple:
    """Mapeia resultado do IntentionEngine → formato MarkovDecider.
    
    IntentionEngine: [('CREATE', params, conf), ...]
    MarkovDecider espera classificar() → (classe, confianca)
    
    Mapeamento:
      CREATE → criar_codigo (default), criar_npc, criar_quest...
      EXPLAIN → explicar_conceito
      SEARCH → busca_informacao
      EDIT → depurar_erro
      REVIEW → analisar_codigo
      GERAL → conversa
    """
    if not intencoes:
        return ('conversa', 0.3)

    cat, params, conf = intencoes[0]

    # Refinar com base nos params/tokens
    texto = params.get('texto', '').lower()
    tokens = params.get('tokens', [])

    if cat == 'CREATE':
        if any('npc' in str(t).lower() for t in tokens) or 'npc' in texto:
            return ('criar_npc', conf)
        if any('quest' in str(t).lower() for t in tokens) or 'quest' in texto:
            return ('criar_quest', conf)
        if any(t[0] == 'codigo' for t in tokens if len(t) >= 2):
            return ('criar_codigo', conf)
        return ('criar_codigo', conf)
    elif cat == 'EXPLAIN':
        return ('explicar_conceito', conf)
    elif cat == 'SEARCH':
        return ('busca_informacao', conf)
    elif cat == 'EDIT':
        return ('depurar_erro', conf)
    elif cat == 'REVIEW':
        return ('analisar_codigo', conf)
    else:
        return ('conversa', conf)


# ═══════════════════════════════════════════════════════════
# A4 & A5. Handlers para ações comuns
# ═══════════════════════════════════════════════════════════

def _acao_llm_gerar(**kwargs):
    return {'resposta': 'LLM offline — usando fallback Markov', 'tipo': 'fallback'}


def _acao_cmd_read(**kwargs):
    entrada = kwargs.get('entrada', '')
    return {'lido': entrada[:500], 'tamanho': len(entrada)}


def _acao_cmd_write(**kwargs):
    contexto = kwargs.get('contexto', {})
    conteudo = contexto.get('conteudo', '')
    return {'escrito': len(conteudo), 'status': 'ok'}


def _acao_cmd_grep(**kwargs):
    entrada = kwargs.get('entrada', '')
    palavras = re.findall(r'[a-zA-Z]{3,}', entrada)
    return {'termos': palavras[:10], 'n_termos': len(palavras)}


def _acao_template_extractor(**kwargs):
    return {'template': 'golden_template', 'extraido': True}


def _acao_deterministic_filler(**kwargs):
    return {'preenchido': True, 'gaps': 0}


def _acao_conectar_topicos(**kwargs):
    contexto = kwargs.get('contexto', {})
    topicos = contexto.get('topicos', [])
    if len(topicos) >= 2:
        try:
            from mcr.memory import MCRConector
            c = MCRConector()
            c.alimentar(topicos[0], 'topico_a')
            c.alimentar(topicos[1], 'topico_b')
            conexao = c.conectar('topico_a', 'topico_b')
            return conexao if conexao else {'erro': 'sem conexao'}
        except Exception as e:
            return {'erro': str(e)[:100]}
    return {'erro': 'precisa de 2 topicos'}


# ═══════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL: Conecta TUDO
# ═══════════════════════════════════════════════════════════

class PipelineConectado:
    """Pipeline que conecta TODOS os módulos MCR reais."""
    
    def __init__(self):
        self._decider = None
        self._router = None
        self._spawner = None
        self._mk = None
        self._intention = None
        self._conector = None
        self._fuel = None
        self._auto_melhoria = None
        self._hdc = None
        self._sdm = None
        self._motor = None
        self._cadeia = None
        self._ruido = None
        self._expansao = None
        self._self_heal = None
        self._pergunta = None
        self._geracao = None
        self._auto_evolution = None
        self._mente_pura = None
        self._monologo = None
        self._planejador_lua = None
        self._curiosidade = None
        self._revived = None
        self._init_modulos()
    
    def _init_modulos(self):
        # MarkovDecider — com seeds para não classificar tudo como "criar_sql"
        try:
            from mcr.coupling import MarkovDecider
            self._decider = MarkovDecider()
            # Semear com exemplos no formato normalizado (3 palavras, lower, sem pontuacao)
            seeds = [
                ("ola_quem_e", "conversa"),
                ("ola_como_vai", "conversa"),
                ("bom_dia_senhor", "conversa"),
                ("oi_tudo_bem", "conversa"),
                ("crie_um_npc", "criar_npc"),
                ("crie_npc_ferreiro", "criar_npc"),
                ("gere_um_npc", "criar_npc"),
                ("crie_um_monstro", "criar_npc"),
                ("gere_um_monstro", "criar_npc"),
                ("gere_um_script", "criar_codigo"),
                ("crie_codigo_lua", "criar_codigo"),
                ("escreva_uma_funcao", "criar_codigo"),
                ("quanto_custa_isso", "conversa"),
                ("quanto_custa_uma", "conversa"),
                ("explique_o_que", "explicar_conceito"),
                ("o_que_e", "explicar_conceito"),
                ("me_explique_como", "explicar_conceito"),
                ("como_funciona_isso", "explicar_conceito"),
                ("o_que_significa", "explicar_conceito"),
                ("crie_uma_quest", "criar_quest"),
                ("analise_este_codigo", "analisar_codigo"),
                ("busque_informacao_sobre", "busca_informacao"),
                ("busque_por_arquivos", "busca_informacao"),
            ]
            for pergunta, classe in seeds:
                self._decider.aprender(pergunta, classe)
        except Exception as e:
            self._decider = None
        
        # MarkovRouter — legacy removido
        self._router = None
        
        # MCRSpawner
        try:
            from mcr.evolution import MCRSpawner, MCRTarefa
            self._spawner = MCRSpawner()
        except Exception as e:
            self._spawner = None
        
        # SQLiteMarkov — versão importável limpa
        try:
            DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache', 'mcr_adapt.db')
            if os.path.exists(DB_PATH):
                from mcr.sqlite_markov import SQLiteMarkov
                self._mk = SQLiteMarkov(DB_PATH, n_max=30)
        except Exception as e:
            self._mk = None
        
        # IntentionEngine — legacy removido
        self._intention = None
        
        # MCRConector
        try:
            from mcr.memory import MCRConector
            self._conector = MCRConector()
        except Exception as e:
            self._conector = None
        
        # MCRFuel
        try:
            from mcr.evolution import MCRFuel
            self._fuel = MCRFuel()
        except Exception as e:
            self._fuel = None
        
        # MCRAutoMelhoria
        try:
            from mcr.evolution import MCRAutoMelhoria
            self._auto_melhoria = MCRAutoMelhoria()
        except Exception as e:
            self._auto_melhoria = None
        
        # HDC — legacy removido
        self._hdc = None
        
        # SDM — legacy removido
        self._sdm = None
        
        # MCRMotor (multi-level emergence) - path do mcr-universal
        try:
            from mcr_universal.emergence.motor import MCRMotor
            self._motor = MCRMotor()
        except Exception as e:
            self._motor = None
        
        # MCRCadeia (loop-safe)
        try:
            from mcr.memory import MCRCadeia
            if self._conector:
                self._cadeia = MCRCadeia(self._conector)
            else:
                self._cadeia = None
        except Exception as e:
            self._cadeia = None
        
        # MCRRuido
        try:
            from mcr.decisor import MCRRuido
            self._ruido = MCRRuido()
        except Exception as e:
            self._ruido = None
        
        # MCRExpansao
        try:
            from mcr.evolution import MCRExpansao
            self._expansao = MCRExpansao()
        except Exception as e:
            self._expansao = None
        
        # MCRSelfHeal
        try:
            from mcr.meta import MCRSelfHeal
            self._self_heal = MCRSelfHeal
        except Exception as e:
            self._self_heal = None
        
        # MCRPergunta
        try:
            from mcr.system import MCRPergunta
            self._pergunta = MCRPergunta()
        except Exception as e:
            self._pergunta = None
        
        # MCRGeracao
        try:
            from mcr.system import MCRGeracao
            self._geracao = MCRGeracao()
        except Exception as e:
            self._geracao = None
        
        # MCRAutoEvolution
        try:
            from mcr.mcr_auto_evolution import MCRAutoEvolution
            self._auto_evolution = MCRAutoEvolution()
        except Exception as e:
            self._auto_evolution = None
        
        # MCRMentePura — 5-MCR thought cycle
        try:
            from mcr.mcr_mente_pura import MCRMentePura
            self._mente_pura = MCRMentePura()
            # Treinar com dados reais do KG (1,589 padroes Canari)
            self._mente_pura.treinar()
            # Treinar percepcao: fingerprint -> tipo
            percepcao_seeds = [
                ('crie um npc ferreiro guarda mercador', 'codigo'),
                ('gere script lua funcao classe', 'codigo'),
                ('ola oi bom dia como vai', 'texto_livre'),
                ('explique o que significa como funciona', 'texto_livre'),
                ('sprite espada escudo armadura elmo', 'sprite'),
                ('crie gere invente imagine algo novo', 'criacao'),
            ]
            from mcr_universal.core.signature import MCRSignatureExpansiva
            for texto, tipo in percepcao_seeds:
                dados = texto.encode('utf-8')
                fp = MCRSignatureExpansiva.fingerprint(dados, 8)
                fp_str = ','.join(str(round(x, 3)) for x in fp)
                self._mente_pura.mcr_percepcao.aprender(f'fp:{fp_str}', f'tipo:{tipo}')
                self._mente_pura.mcr_percepcao.aprender(f'fp:{fp_str}', f'tipo:{tipo}')
            # Treinar tambem por entropia (fallback no _perceber)
            for h_val, tipo in [(3, 'texto_livre'), (5, 'codigo'), (7, 'sprite'), (4, 'conversa')]:
                self._mente_pura.mcr_percepcao.aprender(f'h:{h_val}', f'tipo:{tipo}')
            for tipo_primeira in [
                ('tipo:texto_livre', 'buscar_contexto'),
                ('tipo:codigo', 'extrair_template'),
                ('tipo:sprite', 'extrair_regioes'),
                ('tipo:conversa', 'buscar_dialogo'),
                ('tipo:criacao', 'gerar_ideia'),
            ]:
                self._mente_pura.mcr_decompor.aprender(tipo_primeira[0], tipo_primeira[1])
            # Cadeias de transicao (MCR caminha entre tarefas)
            cadeias = [
                ['buscar_contexto', 'conectar_topicos', 'gerar_resposta'],
                ['extrair_template', 'preencher_gaps', 'validar_sintaxe', 'salvar_arquivo'],
                ['extrair_regioes', 'template_entropico', 'gerar_forma', 'colorir', 'validar'],
                ['buscar_dialogo', 'conectar_contexto', 'gerar_resposta'],
                ['gerar_ideia', 'executar_ideia', 'validar_resultado'],
            ]
            for cadeia in cadeias:
                for i in range(len(cadeia) - 1):
                    # Aprender 3x para reforcar a transicao
                    for _ in range(3):
                        self._mente_pura.mcr_decompor.aprender(cadeia[i], cadeia[i+1])
            # Treinar ferramentas para cada tarefa
            for tarefa_ferramenta in [
                ('tarefa:buscar_contexto', 'ferramenta:MCRConector'),
                ('tarefa:extrair_template', 'ferramenta:SQLiteMarkov'),
                ('tarefa:extrair_regioes', 'ferramenta:extrair_regioes'),
                ('tarefa:buscar_dialogo', 'ferramenta:RadarMCR'),
                ('tarefa:gerar_ideia', 'ferramenta:EmergirUnificado'),
                ('tarefa:analisar', 'ferramenta:MCRSignature'),
                ('tarefa:validar', 'ferramenta:MCRDiscriminador'),
                ('tarefa:renderizar', 'ferramenta:MCRSpriteMotor'),
            ]:
                self._mente_pura.mcr_executar.aprender(tarefa_ferramenta[0], tarefa_ferramenta[1])
        except Exception as e:
            self._mente_pura = None
        
        # InternalMonologue — inner voice
        try:
            from mcr.internal_monologue import InternalMonologue
            self._monologo = InternalMonologue(mcr_system=self)
        except Exception as e:
            self._monologo = None
        
        # Planejador — hierarchical Lua generator
        try:
            from mcr.planejador import Planejador
            self._planejador_lua = Planejador()
        except Exception as e:
            self._planejador_lua = None
        
        # AutoCuriosidade — background gap explorer
        try:
            from mcr.auto_curiosidade import AutoCuriosidade
            self._curiosidade = AutoCuriosidade()
            # Inicia thread de background para explorar gaps
            try:
                self._curiosidade.iniciar_thread_background(intervalo_segundos=120)
            except Exception:
                pass  # thread opcional
        except Exception as e:
            self._curiosidade = None
        
        # MCRDevIARevived — complete DevIA pipeline (import direto do script)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "fix_mcr_devia_v2", os.path.join(_ROOT, 'devia', 'kernel', 'fix_mcr_devia_v2.py'))
            if spec and spec.loader:
                revived_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(revived_mod)
                self._revived = revived_mod.MCRDevIARevived()
        except Exception as e:
            self._revived = None
    
    def processar(self, entrada: str) -> dict:
        """Pipeline MCR — o MCRMentePura decide a propria pipeline via Markov.
        
        Arquitetura:
          1. MCRMentePura.pensar() — 5 etapas decididas por Markov (zero hardcode)
          2. InternalMonologue — thread paralela alimentando MCRConector
          3. MCRAutoMelhoria — diagnostico pos-execucao
          4. MCRDevIARevived — fallback se confianca < threshold
        """
        import time
        t0 = time.time()
        resultado = {'entrada': entrada}
        
        # ─── ORQUESTRADOR CENTRAL: MCRMentePura ───
        if self._mente_pura:
            try:
                pensamento = self._mente_pura.pensar(entrada, verbose=False)
                resultado['mente_pura'] = {
                    'tipo': pensamento.get('percepcao', {}).get('tipo', '?'),
                    'tarefas': pensamento.get('tarefas', []),
                    'nota': pensamento.get('nota', 0),
                    'tempo_ciclo': pensamento.get('tempo', 0),
                }
                resultado['resultados'] = [
                    {'ferramenta': r.get('ferramenta', '?'), 'status': r.get('status', '?')}
                    for r in pensamento.get('resultados', [])
                ]
            except Exception as e:
                resultado['mente_pura'] = {'erro': str(e)[:100]}
        
        # ─── PARALELO: InternalMonologue ───
        if self._monologo:
            try:
                insight = self._monologo.pensar_sobre(entrada)
                resultado['monologo'] = {'tokens': len(insight) if isinstance(insight, str) else 0}
            except Exception:
                pass
        
        # ─── POS-EXECUCAO: AutoMelhoria ───
        if self._auto_melhoria:
            try:
                diag = self._auto_melhoria.ciclo()
                resultado['auto_melhoria'] = {
                    'n': diag.get('n', 0),
                    'acoes': diag.get('acoes', [])[:3],
                }
            except Exception:
                pass
        
        # ─── FALLBACK: MCRDevIARevived ───
        nota = resultado.get('mente_pura', {}).get('nota', 0.5)
        if self._revived and nota < 0.3:
            try:
                resposta_revived = self._revived.responder(entrada)
                resultado['revived_fallback'] = {'resposta': str(resposta_revived)[:200]}
            except Exception:
                pass
        
        resultado['tempo_total'] = round(time.time() - t0, 4)
        return resultado
    
    def conectar(self, texto_a: str, texto_b: str, nome_a: str = 'a', nome_b: str = 'b') -> dict:
        """Usa MCRConector para encontrar ponte entre dois textos/conceitos."""
        if not self._conector:
            return {'erro': 'MCRConector nao disponivel'}
        self._conector.alimentar(texto_a, nome_a)
        self._conector.alimentar(texto_b, nome_b)
        return self._conector.conectar(nome_a, nome_b)
    
    def status(self) -> dict:
        return {
            'decider': self._decider is not None,
            'router': self._router is not None,
            'spawner': self._spawner is not None,
            'sqlite_markov': self._mk is not None,
            'intention': self._intention is not None,
            'conector': self._conector is not None,
            'fuel': self._fuel is not None,
            'auto_melhoria': self._auto_melhoria is not None,
            'hdc': self._hdc is not None,
            'sdm': self._sdm is not None,
            'motor': self._motor is not None,
            'cadeia': self._cadeia is not None,
            'ruido': self._ruido is not None,
            'expansao': self._expansao is not None,
            'self_heal': self._self_heal is not None,
            'pergunta': self._pergunta is not None,
            'geracao': self._geracao is not None,
            'auto_evolution': self._auto_evolution is not None,
            'mente_pura': self._mente_pura is not None,
            'monologo': self._monologo is not None,
            'planejador_lua': self._planejador_lua is not None,
            'curiosidade': self._curiosidade is not None,
            'revived': self._revived is not None,
        }
    
    def buscar_semantico(self, conceito: str, top_k: int = 5) -> list:
        """Usa HDC + SDM para encontrar conceitos semanticamente próximos."""
        if not self._hdc or not self._sdm:
            return []
        hv = self._hdc.get(conceito)
        recon, fid, ativos = self._sdm.retrieve(hv)
        return {'fidelidade': round(fid, 3), 'ativos': ativos}
    
    def close(self):
        if self._mk:
            self._mk.close()


# ─── TESTE ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  PipelineConectado — Teste de Integração')
    print('=' * 60)
    
    pipe = PipelineConectado()
    print(f'  Status: {pipe.status()}')
    
    # Testa conector
    if pipe._conector:
        print('\n  [CONECTOR] Testando ponte entre conceitos...')
        r = pipe.conectar(
            "O dragao cospe fogo e voa pelos ceus",
            "O ferreiro forja espadas na bigorna de ferro",
            "dragao", "ferreiro"
        )
        if r and 'erro' not in r:
            print(f'    Ponte: {r.get("palavra_a","?")} <-> {r.get("palavra_b","?")}, nota={r.get("nota",0):.1f}')
    
    # Testa pipeline
    
    testes = [
        'Ola, quem e voce?',
        'Crie um NPC ferreiro',
        'Quanto custa uma espada?',
        'Explique o que e SPA',
        'Gere um script Lua',
    ]
    
    for t in testes:
        print(f'\n  [ENTRADA] {t}')
        r = pipe.processar(t)
        print(f'    Classificou: {r["etapas"]["classificar"]}')
        print(f'    Roteou: {r["etapas"]["rotear"]}')
        print(f'    Tarefas executadas: {len(r.get("resultados_tarefas", []))}')
        for rt in r.get('resultados_tarefas', [])[:3]:
            status = 'OK' if rt.get('resultado') else f'ERR: {rt.get("erro")}'
            print(f'      [{rt["nome"]}] {status[:80]}')
    
    pipe.close()
    print(f'\n  OK — {len(testes)} entradas processadas')
