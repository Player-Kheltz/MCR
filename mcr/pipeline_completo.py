#!/usr/bin/env python3
"""pipeline_completo.py v2 — Pipeline com Worldbuilding Continuo.

Fluxo:
  1. MarkovDecider.classificar()
  2. Cache Hierarquico (L1→L2→L3)
  3. VERIFICAR_EXISTENTE (world_state.json)
  4. INJETAR_CONTEXTO_GLOBAL (KG)
  5. Geracao (LLM simples ou Ensemble)
  6. CoVe + Validador Estrutural
  7. CANONIZAR (salvar no mundo)
"""
import time, json, os, sys, urllib.request, logging
from typing import Dict, Optional

from mcr.config_llm import MODELO

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))

_logger = logging.getLogger('mcr.pipeline')

OLLAMA_URL = "http://localhost:11434/api/generate"


def _similaridade_jaccard(a: str, b: str) -> float:
    """Similaridade Jaccard entre dois textos (tokenizado como raw_token_set)."""
    try:
        from devia.kernel.mcr_kernel.signature import raw_token_set
        ta = raw_token_set(a)
        tb = raw_token_set(b)
        if not ta or not tb:
            return 0.0
        inter = ta & tb
        uniao = ta | tb
        return len(inter) / len(uniao) if uniao else 0.0
    except Exception:
        return 0.0


def _limpar_codigo(resposta: str) -> str:
    """Remove marcacoes markdown e narrativa ao redor de codigo Lua."""
    import re
    t = resposta.strip()
    t = re.sub(r'^```lua\s*\n?', '', t)
    t = re.sub(r'\n?```\s*$', '', t)
    t = re.sub(r'^```\s*\n?', '', t)
    return t.strip()


def _verificar_existente(pergunta: str, classe: str) -> Dict:
    """Verifica se entidade similar ja existe no mundo.
    
    Usa match exato + similaridade Jaccard > 0.4 para detectar duplicatas.

    Returns:
        dict com existe, entidade, sugestao
    """
    try:
        from mcr.mcr_world_state import _carregar
        estado = _carregar()
        
        import re
        palavras = re.findall(r'\b[A-Z][a-zA-ZÀ-ÿ]{2,}\b', pergunta)
        
        # Verifica nos NPCs
        for nome, dados in estado.get('npcs', {}).items():
            if nome.lower() in pergunta.lower():
                return {'existe': True, 'tipo': 'npc', 'entidade': nome, 'dados': dados}
            for p in palavras:
                if p.lower() in nome.lower():
                    return {'existe': True, 'tipo': 'npc', 'entidade': nome, 'dados': dados}
            if _similaridade_jaccard(nome, pergunta) > 0.4:
                return {'existe': True, 'tipo': 'npc', 'entidade': nome, 'dados': dados, 'match': 'jaccard'}
        
        # Verifica nas lores
        for nome, dados in estado.get('lores', {}).items():
            if nome.lower() in pergunta.lower():
                return {'existe': True, 'tipo': 'lore', 'entidade': nome, 'dados': dados}
            if _similaridade_jaccard(nome, pergunta) > 0.4:
                return {'existe': True, 'tipo': 'lore', 'entidade': nome, 'dados': dados, 'match': 'jaccard'}
        
        return {'existe': False, 'tipo': None, 'entidade': None, 'dados': None}
    except Exception:
        return {'existe': False, 'tipo': None, 'entidade': None, 'dados': None}


def _injetar_contexto(pergunta: str, classe: str,
                       hdc_memory=None) -> str:
    """Busca entidades relacionadas no mundo para enriquecer o prompt.

    Args:
        pergunta: texto do usuario
        classe: classe MarkovDecider
        hdc_memory: HDCKGMemory opcional para contexto semantico

    Returns:
        string com contexto global para injetar no prompt
    """
    try:
        from mcr.mcr_world_state import _carregar
        estado = _carregar()
        partes = []

        # Busca NPCs relacionados
        npcs = list(estado.get('npcs', {}).keys())[:5]
        if npcs:
            partes.append('NPCs existentes no mundo: ' + ', '.join(npcs))

        # Busca lores relacionados
        lores = list(estado.get('lores', {}).keys())[:3]
        if lores:
            partes.append('Lores do mundo: ' + ', '.join(lores))

        # Onda 3: contexto semantico via HDC+SDM
        if hdc_memory:
            try:
                similares = hdc_memory.query_similar_por_texto(pergunta, top_k=3)
                nomes_hdc = [n for n, s in similares if s > 0.001]
                if nomes_hdc:
                    partes.append('Entidades no mundo: ' +
                                  ', '.join(nomes_hdc))
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)

        # Onda 5: dados reais do Canary
        try:
            from mcr.data_injector import DataInjector
            _di = DataInjector()
            dados_reais = _di.enriquecer_contexto(pergunta, classe)
            if dados_reais:
                partes.append('[Dados reais do jogo]: ' + dados_reais)
        except Exception as _e:
            _logger.debug("pipeline step: %s", _e)

        if partes:
            return '\n'.join(partes)
        return ''
    except Exception:
        return ''


def _canonizar(pergunta: str, resposta: str, classe: str, modelo: str):
    """Salva entidade gerada no mundo (world_state + chronicle)."""
    try:
        import re
        from mcr.mcr_world_state import registrar_entidade

        # Extrai nome da entidade gerada
        nome_match = re.search(r'NOME:\s*(.+)', resposta)
        if nome_match:
            nome = nome_match.group(1).strip()
            if classe == 'criar_npc':
                registrar_entidade('npc', nome, {
                    'file': f'npc_{nome.lower().replace(" ", "_")}.lua',
                    'role': 'gerado_por_pipeline',
                    'tier': 'rascunho',
                })
                # Registra na cronica
                try:
                    from mcr.mcr_world_chronicle import append_chronicle
                    append_chronicle(
                        f'{nome} chegou ao mundo. {resposta[:200]}',
                        {'type': 'npc_arrival', 'entity': nome, 'classe': classe}
                    )
                except Exception as _e:
                    _logger.debug("pipeline step: %s", _e)
            elif classe == 'criar_lore' or classe == 'explicar_conceito':
                # Extrai titulo da lore (primeira linha substantiva)
                linhas = resposta.strip().split('\n')
                titulo = linhas[0][:80] if linhas else 'Lore Sem Titulo'
                registrar_entidade('lore', titulo, {
                    'tipo': 'gerado_por_pipeline',
                    'resumo': resposta[:300],
                    'tier': 'rascunho',
                })
    except Exception as _e:
        _logger.debug("pipeline step: %s", _e)


class PipelineCompleto:
    """Pipeline completo com worldbuilding continuo."""

    def __init__(self):
        self._stats = {
            'total': 0, 'cache_hit': 0, 'llm_simples': 0,
            'ensemble': 0, 'mcr': 0, 'cove_falhas': 0, 'canonizados': 0,
            'anomalias_detectadas': 0, 'regeracoes': 0, 'guardrail_rejeitadas': 0,
            'tempo_total': 0.0,
        }
        # Detector de anomalias (corpus = dialogo NPC PT + world_state, nao codigo Lua)
        self._detector = None
        try:
            from mcr.world_anomaly_detector import WorldAnomalyDetector
            from mcr.paths import CANARY_NPC_DIR, KG_DIR
            from mcr.mcr_world_state import WORLD_STATE_FILE
            scripts = str(CANARY_NPC_DIR) if CANARY_NPC_DIR and CANARY_NPC_DIR.exists() else None
            ws_path = str(WORLD_STATE_FILE) if WORLD_STATE_FILE and WORLD_STATE_FILE.exists() else None
            kg_dir = str(KG_DIR)
            self._detector = WorldAnomalyDetector()
            self._detector.carregar(scripts_dir=scripts, world_state_path=ws_path,
                                    chronicle_path=None, kg_dir=kg_dir)
        except Exception as e:
            print(f'[Pipeline] Detector nao carregado: {e}')

        # HybridRouter (Onda 1): decisao MCR vs LLM + guardrail
        self._hybrid_router = None
        try:
            from mcr.hybrid_router import HybridRouter
            from mcr.mcr_world_state import _carregar, obter_entidade
            self._hybrid_router = HybridRouter()
            ws = _carregar()
            for nome in list(ws.get('npcs', {}).keys())[:50]:
                dados = obter_entidade('npc', nome)
                if dados:
                    import json
                    texto = f'{nome} e um NPC. {json.dumps(dados, ensure_ascii=False)}'
                    self._hybrid_router.alimentar_motor(texto, f'ws_{nome}')
            from mcr.paths import CANARY_NPC_DIR
            self._hybrid_router.alimentar_de_arquivos_lua(CANARY_NPC_DIR, max_n=200)
            print(f'[HybridRouter] Motor populado: {len(self._hybrid_router.motor.topicos)} topicos')
        except Exception as e:
            print(f'[Pipeline] HybridRouter nao carregado: {e}')

        # HDC+SDM Memory (Onda 3): memoria semantica via hiperdimensional computing
        self._hdc_memory = None
        try:
            from mcr.hdc_kg_memory import HDCKGMemory
            self._hdc_memory = HDCKGMemory(n_enderecos=1000, raio=0.05)
            ws = _carregar()
            for nome in list(ws.get('npcs', {}).keys())[:100]:
                dados = obter_entidade('npc', nome)
                if dados:
                    self._hdc_memory.store_entity(nome, dados)
            print(f'[HDC Memory] {len(self._hdc_memory.entidades)} entidades carregadas')
        except Exception as e:
            print(f'[Pipeline] HDC Memory nao carregado: {e}')

        # FeedbackFilter (Onda 4): qualidade antes de canonizar
        self._feedback_filter = None
        self._lessons_buffer = []
        try:
            import os, sys as _sys
            _sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
            from FeedbackFilter import FeedbackFilter
            self._feedback_filter = FeedbackFilter()
            print('[FeedbackFilter] Ativo')
        except Exception as e:
            print(f'[Pipeline] FeedbackFilter nao carregado: {e}')

        # AutoLoop (Onda 4): thread de auto-aprimoramento em background
        self._auto_loop_thread = None
        self._iniciar_auto_loop()

        # Onda 8: cache TTL para checkpoint de sessoes
        self._cache_ttl = None

    def _alimentar_motor(self, resposta: str, pergunta: str, classe: str = ''):
        if hasattr(self, '_hybrid_router') and self._hybrid_router:
            try:
                self._hybrid_router.motor.alimentar(resposta[:5000], pergunta[:60])
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)
        # Onda 8: armazenar interacao no HDC
        if hasattr(self, '_hdc_memory') and self._hdc_memory:
            try:
                self._hdc_memory.store_interaction(pergunta, resposta,
                                                   {'classe': classe})
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)

    def _deve_canonizar(self, pergunta: str, resposta: str, confianca: float = 0.3) -> bool:
        """Verifica se a resposta passa no FeedbackFilter."""
        if not self._feedback_filter:
            return True
        if not self._feedback_filter.filtrar(pergunta, resposta, confianca):
            self._stats['regeracoes'] += 1
            self._lessons_buffer.append({
                'pergunta': pergunta,
                'resposta': resposta[:200],
                'motivo': 'feedback_filter',
                'timestamp': time.time(),
            })
            print(f'[FeedbackFilter] Resposta rejeitada — {len(resposta)} chars')
            return False
        return True

    def _cached_return(self, pergunta: str, resultado: dict) -> dict:
        """Salva resultado no cache TTL antes de retornar."""
        if self._cache_ttl:
            try:
                _, setter = self._cache_ttl
                setter(f'pipe:{pergunta[:80]}', resultado)
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)
        return resultado

    def _iniciar_auto_loop(self):
        """Thread de auto-aprimoramento: gaps + insights + otimizacao em background."""
        import threading
        def _loop():
            time.sleep(10)
            ciclo = 0
            while True:
                try:
                    if not self._hybrid_router:
                        time.sleep(60)
                        continue
                    motor = self._hybrid_router.motor
                    topicos = list(motor.topicos.keys())
                    entropia = motor.mk_palavra.entropia_media()

                    # Detectar entropia alta = possivel gap
                    if entropia > 0.8 and len(topicos) >= 4:
                        a, b = topicos[0], topicos[len(topicos)//2]
                        from mcr_universal.emergence.auto_loop import MCRAutoLoop
                        al = MCRAutoLoop(motor=motor)
                        res = al.loop(a, b, max_iter=3)
                        if res.get('melhor_nota', 0) > 5:
                            print(f'[AutoLoop] Conexao {a} + {b}: nota={res["melhor_nota"]:.1f}')

                    # Onda 8: radar de saude
                    try:
                        from mcr_universal.intelligence.radar import MCRRadar
                        radar = MCRRadar(motor)
                        rv = radar.varrer(' '.join(topicos[:50]), max_pulsos=5)
                        if rv.get('gaps'):
                            print(f'[Radar] Gaps: {[g["termo"] for g in rv["gaps"][:3]]}')
                    except Exception as _e:
                        _logger.debug("pipeline step: %s", _e)

                    # Onda 7: otimizacao de pesos a cada ~30 min (6 ciclos de 300s)
                    ciclo += 1
                    if ciclo % 6 == 0 and len(topicos) >= 4:
                        try:
                            from mcr_universal.feedback.peso_nota import MCRPesoNota
                            otimizador = MCRPesoNota(motor)
                            res_pesos = otimizador.testar_pesos()
                            if 'melhores_pesos' in res_pesos:
                                print(f'[PesoNota] Otimizados: {res_pesos["melhores_pesos"]} (nota={res_pesos["melhor_nota"]:.2f})')
                        except Exception as e_opt:
                            print(f'[PesoNota] Falha: {e_opt}')

                except Exception as e:
                    print(f'[AutoLoop] Erro: {e}')
                time.sleep(300)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        self._auto_loop_thread = t
        print('[AutoLoop] Thread iniciada')

    def processar(self, pergunta: str, contexto: str = "") -> Dict:
        t0 = time.time()
        self._stats['total'] += 1

        # Onda 8: checkpoint de sessao (cache TTL)
        if self._cache_ttl:
            try:
                getter, _ = self._cache_ttl
                hit = getter(f'pipe:{pergunta[:80]}')
                if hit:
                    self._stats['cache_hit'] += 1
                    return hit
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)

        # 1. MarkovDecider
        from mcr_devia_v2 import MarkovDecider
        md = MarkovDecider()
        classe, conf = md.classificar(pergunta)

        # 1.b Onda 1 — Decisao MCR vs LLM via HybridRouter
        rota = 'llm_simples'
        if self._hybrid_router:
            decisao = self._hybrid_router.decidir_rota(pergunta)
            if decisao['decisao'] == 'mcr' and decisao['confianca'] >= 0.6:
                resposta_mcr = self._hybrid_router.gerar_por_classe(classe, pergunta) or self._hybrid_router.gerar_mcr(pergunta)
                if resposta_mcr:
                    self._stats['mcr'] += 1
                    rota = 'mcr'

        # Se rota MCR ja resolveu, pula geracao via LLM
        if rota == 'mcr':
            existente = _verificar_existente(pergunta, classe)

            # Guardrail na rota MCR
            guardrail_resultado = None
            if self._hybrid_router:
                guarda = self._hybrid_router.validar_resposta(resposta_mcr, pergunta)
                guardrail_resultado = guarda
                if not guarda.get('valida', True):
                    self._stats['guardrail_rejeitadas'] += 1
                    # Onda 7: tentar auto-cura antes de fallback
                    try:
                        from mcr_universal.feedback.self_heal import MCRSelfHeal
                        curado = MCRSelfHeal(self._hybrid_router.motor).curar(resposta_mcr, pergunta)
                        if curado and len(curado) > len(resposta_mcr):
                            resposta_mcr = curado
                            guardrail_resultado = self._hybrid_router.validar_resposta(resposta_mcr, pergunta)
                    except Exception as _e:
                        _logger.debug("pipeline step: %s", _e)
                    if not guardrail_resultado.get('valida', True):
                        resposta_mcr = ''

            if not resposta_mcr:
                rota = 'llm_simples'
            else:
                validacao_codigo = self._validar_codigo_gerado(resposta_mcr, classe)
                if self._deve_canonizar(pergunta, resposta_mcr, conf):
                    _canonizar(pergunta, resposta_mcr, classe, 'mcr')
                    self._stats['canonizados'] += 1
                    self._alimentar_motor(resposta_mcr, pergunta, classe)
                return self._cached_return(pergunta, {
                    'resposta': resposta_mcr, 'rota': 'mcr',
                    'classe': classe, 'confianca': conf,
                    'tempo': round(time.time() - t0, 3),
                    'existente': existente,
                    'validacao_codigo': validacao_codigo,
                    'guardrail': guardrail_resultado,
                })

        # 2. Cache
        if conf > 0.3:
            from mcr.cache_hierarquico import CacheHierarquico
            cache = CacheHierarquico()
            resposta_cache = cache.buscar(pergunta)
            if resposta_cache:
                self._stats['cache_hit'] += 1
                return {
                    'resposta': resposta_cache, 'rota': 'cache',
                    'classe': classe, 'confianca': conf,
                    'tempo': round(time.time() - t0, 3),
                }

        # 3. VERIFICAR_EXISTENTE
        existente = _verificar_existente(pergunta, classe)
        if existente['existe']:
            print(f'[Worldbuilding] Entidade existente encontrada: {existente["entidade"]}')

        # 4. INJETAR_CONTEXTO_GLOBAL (Onda 3: + HDC semantico)
        contexto_global = _injetar_contexto(pergunta, classe,
                                            hdc_memory=self._hdc_memory)
        if contexto_global:
            print(f'[Worldbuilding] Contexto global injetado')

        # 5. Monta prompt
        from mcr.prompts_criativos import obter_prompt, obter_modelo
        prompt = obter_prompt(classe, pergunta, tipo=classe, npc='NPC', resumo=pergunta)
        if contexto_global:
            prompt = prompt.replace('Comece agora.',
                f'Contexto do mundo:\n{contexto_global}\n\nComece agora.')
        modelo = obter_modelo(classe)

        # 6. Gera
        classes_complexas = ['criar_sistema',
                             'criar_habilidade_spa']
        is_complexa = classe in classes_complexas or conf < 0.15

        if is_complexa:
            from mcr.ensemble_7b import Ensemble7B
            ens = Ensemble7B()
            resultado_ens = ens.gerar(prompt)
            resposta = resultado_ens['resposta']
            self._stats['ensemble'] += 1

            # ─── World Anomaly Detector ─────────────────────────
            self._validar_anomalias_e_regerar(prompt, resposta, classe, modelo,
                                               lambda r, m: self._llm_gerar(r, m))

            from mcr.chain_of_verification import ChainOfVerification
            cov = ChainOfVerification()
            verificacao = cov.verificar(pergunta, resposta)
            if not verificacao['valida']:
                self._stats['cove_falhas'] += 1
                resposta = cov.corrigir(pergunta, resposta)

            # ─── Cascata de validacao de codigo ────────────────
            validacao_codigo = self._validar_codigo_gerado(resposta, classe)

            # ─── Guardrail (Onda 1) — rejeita respostas de baixa qualidade
            guardrail_resultado = None
            if self._hybrid_router:
                guarda = self._hybrid_router.validar_resposta(resposta, pergunta)
                guardrail_resultado = guarda
                if not guarda.get('valida', True):
                    self._stats['guardrail_rejeitadas'] += 1
                    for _ in range(2):
                        resultado_ens = ens.gerar(prompt + '\n[NOTA: resposta anterior rejeitada. Seja mais coerente.]')
                        resposta = resultado_ens['resposta']
                        guarda = self._hybrid_router.validar_resposta(resposta, pergunta)
                        guardrail_resultado = guarda
                        if guarda.get('valida', False):
                            break
                    # Onda 7: auto-cura se todas as tentativas falharam
                    if not guardrail_resultado.get('valida', True):
                        try:
                            from mcr_universal.feedback.self_heal import MCRSelfHeal
                            curado = MCRSelfHeal(self._hybrid_router.motor).curar(resposta, pergunta)
                            if curado:
                                resposta = curado
                                guardrail_resultado = self._hybrid_router.validar_resposta(resposta, pergunta)
                        except Exception as _e:
                            _logger.debug("pipeline step: %s", _e)

            # 7. CANONIZAR (Onda 4: com FeedbackFilter)
            if self._deve_canonizar(pergunta, resposta, conf):
                _canonizar(pergunta, resposta, classe, modelo)
                self._stats['canonizados'] += 1
                self._alimentar_motor(resposta, pergunta)

            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(pergunta, resposta, classe)
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)

            return self._cached_return(pergunta, {
                'resposta': resposta, 'rota': 'ensemble',
                'classe': classe, 'confianca': conf, 'modelo': modelo,
                'tempo': round(time.time() - t0, 3),
                'verificacao': verificacao,
                'existente': existente,
                'ensemble_detalhes': resultado_ens.get('detalhes', []),
                'validacao_codigo': validacao_codigo,
                'guardrail': guardrail_resultado,
            })
        else:
            resposta = self._llm_gerar(prompt, modelo)
            self._stats['llm_simples'] += 1

            # ─── World Anomaly Detector ─────────────────────────
            resposta = self._validar_anomalias_e_regerar(prompt, resposta, classe, modelo,
                                                         lambda r, m: self._llm_gerar(r, m))

            from mcr.chain_of_verification import ChainOfVerification
            cov = ChainOfVerification()
            verificacao = cov.verificar(pergunta, resposta)

            # ─── Cascata de validacao de codigo ────────────────
            validacao_codigo = self._validar_codigo_gerado(resposta, classe)

            # ─── Guardrail (Onda 1) — rejeita respostas de baixa qualidade
            guardrail_resultado = None
            if self._hybrid_router:
                guarda = self._hybrid_router.validar_resposta(resposta, pergunta)
                guardrail_resultado = guarda
                if not guarda.get('valida', True):
                    self._stats['guardrail_rejeitadas'] += 1
                    for _ in range(2):
                        resposta = self._llm_gerar(prompt + '\n[NOTA: resposta anterior rejeitada. Seja mais coerente com o tema.]', modelo)
                        guarda = self._hybrid_router.validar_resposta(resposta, pergunta)
                        guardrail_resultado = guarda
                        if guarda.get('valida', False):
                            break
                    # Onda 7: auto-cura se todas as tentativas falharam
                    if not guardrail_resultado.get('valida', True):
                        try:
                            from mcr_universal.feedback.self_heal import MCRSelfHeal
                            curado = MCRSelfHeal(self._hybrid_router.motor).curar(resposta, pergunta)
                            if curado:
                                resposta = curado
                                guardrail_resultado = self._hybrid_router.validar_resposta(resposta, pergunta)
                        except Exception as _e:
                            _logger.debug("pipeline step: %s", _e)

            # 7. CANONIZAR (Onda 4: com FeedbackFilter)
            if self._deve_canonizar(pergunta, resposta, conf):
                _canonizar(pergunta, resposta, classe, modelo)
                self._stats['canonizados'] += 1
                self._alimentar_motor(resposta, pergunta)

            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(pergunta, resposta, classe)
            except Exception as _e:
                _logger.debug("pipeline step: %s", _e)

            return self._cached_return(pergunta, {
                'resposta': resposta, 'rota': rota,
                'classe': classe, 'confianca': conf, 'modelo': modelo,
                'tempo': round(time.time() - t0, 3),
                'verificacao': verificacao,
                'existente': existente,
                'validacao_codigo': validacao_codigo,
                'guardrail': guardrail_resultado,
            })

    def _validar_anomalias_e_regerar(
        self, prompt: str, resposta: str, classe: str, modelo: str,
        gerador: callable, max_tentativas: int = 0,
    ) -> str:
        """Valida resposta contra o detector de anomalias.
        
        So ativo para classes de geracao de codigo (criar_codigo, etc).
        Conteudo narrativo PT nao passa pelo detector — validado por
        SanityValidator + _verificar_existente (entidades e duplicatas).
        
        Nao regenera — detector em modo passivo.
        O corpus cresce organicamente via atualizar().
        
        Returns:
            resposta original (sempre aceita)
        """
        classes_narrativas = ('criar_npc', 'criar_quest', 'criar_lore',
                              'explicar_conceito', 'criar_sql')
        if not self._detector or classe in classes_narrativas:
            return resposta

        resultado = self._detector.validar(resposta)
        if resultado['exige_regeneracao']:
            termos = [a['token'] for a in resultado['anomalias'][:3]]
            self._stats['anomalias_detectadas'] += 1
            print(f'[Detector] Anomalias (aceitas): {termos}')

        self._detector.atualizar(resposta)
        return resposta

    def _validar_codigo_gerado(self, resposta: str, classe: str) -> Dict:
        """Cascata de validacao para codigo gerado.

        SanityValidator → ShadowCanary → LuaValidator (Onda 2).
        Apenas para classes de geracao de codigo (criar_codigo, etc).
        Nenhum codigo novo — so orquestra componentes existentes.

        Returns:
            dict com 'valido', 'validacoes'
        """
        codigo = _limpar_codigo(resposta)
        validacoes = []

        # 1. SanityValidator: APIs chamadas existem no KG?
        if classe in ('criar_codigo', 'criar_habilidade_spa', 'criar_sistema'):
            try:
                from mcr.sanity_validator import SanityValidator
                sv = SanityValidator()
                v = sv.validar_codigo(codigo)
                desconhecidas = v.get('apis_desconhecidas', [])
                valido_sv = v.get('valido', True) or len(desconhecidas) == 0
                validacoes.append({
                    'etapa': 'SanityValidator',
                    'valido': valido_sv,
                    'chamadas_conhecidas': len(v.get('apis_conhecidas', [])),
                    'chamadas_desconhecidas': desconhecidas[:5],
                })
                if not valido_sv:
                    print(f'[Guardiao] SanityValidator: APIs desconhecidas: {desconhecidas[:3]}')
            except Exception as e:
                validacoes.append({'etapa': 'SanityValidator', 'erro': str(e)[:60]})

        # 2. ShadowCanary: executa Lua sem crash?
        if classe == 'criar_codigo':
            try:
                from mcr.shadow_canary import executar_shadow_codigo
                shadow = executar_shadow_codigo(codigo)
                crashou = shadow.get('status') == 'crash'
                validacoes.append({
                    'etapa': 'ShadowCanary',
                    'valido': not crashou,
                    'status': shadow.get('status', '?'),
                    'erro': shadow.get('erro', '')[:100],
                })
                if crashou:
                    print(f'[Guardiao] ShadowCanary: crash — {shadow.get("erro", "")[:80]}')
            except Exception as e:
                validacoes.append({'etapa': 'ShadowCanary', 'erro': str(e)[:60]})

        # 3. LuaValidator (Onda 2): SQL injection + boas praticas Canary + estrutura
        if classe in ('criar_codigo', 'criar_npc', 'criar_habilidade_spa', 'criar_sistema'):
            try:
                from mcr.lua_validator import LuaValidator
                lv = LuaValidator()
                v_lua = lv.validar(codigo)
                validacoes.append({
                    'etapa': 'LuaValidator',
                    'valido': v_lua['valido'],
                    'erros': v_lua['erros'][:3],
                    'avisos': v_lua['avisos'][:3],
                    'sql_injection': len(v_lua['sql_injection']),
                    'boas_praticas': v_lua['boas_praticas'],
                    'estrutura': [e for e in v_lua['estrutura'] if 'FALTANDO' in e],
                })
                if not v_lua['valido']:
                    print(f'[Guardiao] LuaValidator: {len(v_lua["erros"])} erros, estruturas faltando: {len([e for e in v_lua["estrutura"] if "FALTANDO" in e])}')
            except Exception as e:
                validacoes.append({'etapa': 'LuaValidator', 'erro': str(e)[:60]})

        valido = all(v.get('valido', True) for v in validacoes)
        return {'valido': valido, 'validacoes': validacoes}

    def _llm_gerar(self, prompt: str, modelo: str = None) -> str:
        modelo_atual = modelo or MODELO
        try:
            payload = json.dumps({
                "model": modelo_atual, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.7, "num_ctx": 32768}
            }).encode()
            req = urllib.request.Request(OLLAMA_URL, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read()).get("response", "")
        except Exception as e:
            return f"[Erro LLM: {e}]"

    def expandir(self, nome_entidade: str,
                 prompt_adicional: str = "expanda a historia deste personagem") -> Dict:
        """Expande uma entidade existente no mundo.
        
        Args:
            nome_entidade: nome da entidade a expandir
            prompt_adicional: instrucao adicional para a expansao
        
        Returns:
            dict com resposta expandida, entidade, tipo
        """
        from mcr.mcr_world_state import obter_entidade, _carregar

        # Tenta encontrar nos NPCs
        dados = obter_entidade('npc', nome_entidade)
        tipo = 'npc'
        if not dados:
            dados = obter_entidade('lore', nome_entidade)
            tipo = 'lore'

        if not dados:
            return {'erro': f'Entidade "{nome_entidade}" nao encontrada no mundo',
                    'sugestao': 'Use processar() para criar uma nova'}

        t0 = time.time()
        prompt = (
            f'Expanda a historia de {nome_entidade}.\n\n'
            f'Dados atuais:\n{json.dumps(dados, ensure_ascii=False, indent=2)}\n\n'
            f'Instrucao: {prompt_adicional}\n\n'
            f'Escreva um paragrafo expandindo a historia, mantendo coerencia '
            f'com o que ja foi estabelecido. Nao contradiga os dados existentes.'
        )

        from mcr.prompts_criativos import obter_modelo
        modelo = obter_modelo('criar_npc')
        resposta = self._llm_gerar(prompt, modelo)
        tempo = round(time.time() - t0, 3)

        # Atualiza no mundo
        from mcr.mcr_world_state import registrar_entidade
        from mcr.mcr_world_chronicle import append_chronicle

        if tipo == 'npc':
            dados.setdefault('expansoes', [])
            dados['expansoes'].append(resposta[:500])
            registrar_entidade('npc', nome_entidade, {'expansoes': dados['expansoes']})
        else:
            dados.setdefault('expansoes', [])
            dados['expansoes'].append(resposta[:500])
            registrar_entidade('lore', nome_entidade, {'expansoes': dados['expansoes']})

        append_chronicle(
            f'A historia de {nome_entidade} foi expandida: {resposta[:200]}',
            {'type': 'expansion', 'entity': nome_entidade, 'entity_type': tipo}
        )

        return {
            'resposta': resposta,
            'entidade': nome_entidade,
            'tipo': tipo,
            'modelo': modelo,
            'tempo': tempo,
        }

    def estatisticas(self) -> Dict:
        total = max(self._stats['total'], 1)
        return {**self._stats,
                'taxa_cache': round(self._stats['cache_hit'] / total * 100, 1),
                'tempo_medio': round(self._stats['tempo_total'] / total, 1)}
