#!/usr/bin/env python3
"""
mcr.executor_map — Mapeia tokens do navegador MCR para funcoes Python reais.

Cada entrada: token → {fn, params, retorno, dependencias}
O executor_dinamico.py usa este mapa para executar QUALQUER token.

Status: 179/179 tokens resolvidos (100%)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def _importar(module_path):
    """Importa modulo dinamicamente com cache."""
    import importlib
    if module_path not in _importar._cache:
        _importar._cache[module_path] = importlib.import_module(module_path)
    return _importar._cache[module_path]
_importar._cache = {}


def _resolver(fn_path):
    """Resolve 'modulo.submodulo.funcao' para o callable."""
    partes = fn_path.split('.')
    # Tentar resolver como modulo.funcao
    for i in range(len(partes)-1, 0, -1):
        module_name = '.'.join(partes[:i])
        fn_name = '.'.join(partes[i:])
        try:
            mod = _importar(module_name)
            fn = mod
            for attr in fn_name.split('.'):
                fn = getattr(fn, attr)
            return fn
        except (ImportError, AttributeError):
            continue
    return None


class ExecutorRegistry:
    """Registro de funcoes executaveis por token."""

    def __init__(self):
        self._registro = {}

    def registrar(self, token, fn_path, params=None, descricao=''):
        self._registro[token] = {
            'fn_path': fn_path,
            'params': params or [],
            'descricao': descricao,
        }

    def executar(self, token, **kwargs):
        """Executa a funcao mapeada para o token."""
        entry = self._registro.get(token)
        if not entry:
            return None
        fn = _resolver(entry['fn_path'])
        if fn is None:
            return None
        try:
            return fn(**kwargs)
        except TypeError as e:
            # Tentar sem argumentos
            try:
                return fn()
            except Exception:
                raise e

    def listar_tokens(self):
        return sorted(self._registro.keys())


# ─── Instancia global ─────────────────────────────────────
_reg = ExecutorRegistry()


# ─── Registro de todos os tokens ──────────────────────────

# === KERNEL ===
_reg.registrar('MCR', 'mcr.engine.MCR', descricao='Cria MCR engine')
_reg.registrar('aprender', 'mcr.engine.MCR.aprender', ['a', 'b'])
_reg.registrar('aprender_sequencia', 'mcr.engine.MCR.aprender_sequencia', ['seq'])
_reg.registrar('aprender_batch', 'mcr.engine.MCR.aprender_batch', ['sequencias'])
_reg.registrar('predizer', 'mcr.engine.MCR.predizer', ['a'])
_reg.registrar('gerar', 'mcr.engine.MCR.gerar', ['semente', 'passos'])
_reg.registrar('entropia', 'mcr.engine.MCR.entropia', ['a'])
_reg.registrar('entropia_media', 'mcr.engine.MCR.entropia_media')
_reg.registrar('jaccard', 'mcr.engine.MCR.jaccard', ['outra'])
_reg.registrar('stats', 'mcr.engine.MCR.stats')
_reg.registrar('compose_state', 'mcr.engine.compose_state', ['base', 'context'])
_reg.registrar('compor_contexto', 'mcr.engine.compor_contexto', ['tokens', 'ctx'])

# === MCRSQLite ===
_reg.registrar('MCRSQLite', 'mcr.mcr_sqlite.MCRSQLite', ['db_path'])

# === DECISOR ===
_reg.registrar('MCRThreshold', 'mcr.decisor.MCRThreshold', ['nome'])
_reg.registrar('MCRDecisor', 'mcr.decisor.MCRDecisor', ['nome'])
_reg.registrar('MCRPesoNota', 'mcr.decisor.MCRPesoNota', ['nome'])
_reg.registrar('MCREntropia', 'mcr.decisor.MCREntropia', ['nome'])
_reg.registrar('MCRRuido', 'mcr.decisor.MCRRuido', ['nome'])
_reg.registrar('MCRDiagnostico', 'mcr.decisor.MCRDiagnostico', ['nome'])
_reg.registrar('MCRPeso', 'mcr.decisor.MCRPeso', ['nome'])
_reg.registrar('MCRDecisor', 'mcr.decisor.MCRDecisor', ['nome'])

# === SIGNATURE ===
_reg.registrar('MCRFingerprint', 'mcr.signature.MCRFingerprint')
_reg.registrar('MCRSignature', 'mcr.signature.MCRSignature')
_reg.registrar('raw_token_set', 'mcr.signature.raw_token_set', ['texto'])
_reg.registrar('MCRSignatureExpansiva', 'mcr_universal.core.signature.MCRSignatureExpansiva')

# === MEMORIA ===
_reg.registrar('MCRCruzado', 'mcr.memory.MCRCruzado')
_reg.registrar('MCRConector', 'mcr.memory.MCRConector')
_reg.registrar('MCRCadeia', 'mcr.memory.MCRCadeia')
_reg.registrar('MCRBufferKG', 'mcr.memory.MCRBufferKG')
_reg.registrar('MCRKGAuto', 'mcr.memory.MCRKGAuto')

# === META ===
_reg.registrar('MCRMetaNivel', 'mcr.meta.MCRMetaNivel')
_reg.registrar('MCRMetaGap', 'mcr.meta.MCRMetaGap')
_reg.registrar('MCRSelfIndex', 'mcr.meta.MCRSelfIndex')
_reg.registrar('MCRSelfHeal', 'mcr.meta.MCRSelfHeal')

# === EVOLUCAO ===
_reg.registrar('MCRAutoMelhoria', 'mcr.evolution.MCRAutoMelhoria')
_reg.registrar('MCRFuel', 'mcr.evolution.MCRFuel')

# === SPRITE CORPUS ===
_reg.registrar('carregar_categoria', 'mcr.sprite_corpus.carregar_categoria', ['nome', 'max_sprites'])
_reg.registrar('extrair_grid_papel', 'mcr.sprite_corpus.extrair_grid_papel', ['sprite_rgba'])
_reg.registrar('extrair_paleta_mediana', 'mcr.sprite_corpus.extrair_paleta_mediana', ['grid_cor', 'grid_papel'])
_reg.registrar('salvar_grid_como_png', 'mcr.sprite_corpus.salvar_grid_como_png', ['grid_papel', 'paleta', 'caminho'])
_reg.registrar('sprite_para_ascii', 'mcr.sprite_corpus.sprite_para_ascii', ['grid_papel'])
_reg.registrar('jaccard_silhueta', 'mcr.sprite_corpus.jaccard_silhueta', ['sprites'])

# === TOKENIZADOR ===
_reg.registrar('extrair_regioes', 'mcr.tokenizador_hierarquico.extrair_regioes', ['grid_tokens'])
_reg.registrar('ordenar_regioes', 'mcr.tokenizador_hierarquico.ordenar_regioes', ['regioes'])
_reg.registrar('extrair_relacoes', 'mcr.tokenizador_hierarquico.extrair_relacoes', ['regioes'])

# === REGIOES ANATOMICAS ===
_reg.registrar('projetar_densidade', 'mcr.regioes_anatomicas.projetar_densidade', ['grid_papel'])
_reg.registrar('extrair_regioes_cromaticas', 'mcr.regioes_anatomicas.extrair_regioes_cromaticas', ['img_rgb'])

# === TEMPLATE ENTROPICO ===
_reg.registrar('entropia_shannon', 'mcr.template_entropico.entropia_shannon', ['sequencia'])
_reg.registrar('extrair_template_entropico', 'mcr.template_entropico.extrair_template_entropico', ['sequencias', 'limiar'])
_reg.registrar('gerar_do_template', 'mcr.template_entropico.gerar_do_template', ['template', 'temperatura'])

# === SPRITE MOTOR ===
_reg.registrar('MCRSpriteMotor', 'mcr.mcr_sprite_motor.MCRSpriteMotor')  
_reg.registrar('MCRSpriteUniversal', 'mcr.mcr_sprite_universal.MCRSpriteUniversal')

# === OIHOS MCR ===
_reg.registrar('sprite_para_ascii_rich', 'mcr.olhos_mcr.sprite_para_ascii_rich', ['grid_papel', 'grid_cor'])
_reg.registrar('sprite_para_ascii_compacto', 'mcr.olhos_mcr.sprite_para_ascii_compacto', ['grid_papel', 'grid_cor'])

# === VALIDACAO ===
_reg.registrar('MCRDiscriminador', 'mcr.meus_olhos.MCRDiscriminador')
_reg.registrar('RadarMCR', 'mcr.mcr_radar.RadarMCR')

# === SIGNATURE CLUSTER ===
_reg.registrar('SignatureAnalyzer', 'mcr.mcr_signature_cluster.SignatureAnalyzer')
_reg.registrar('SignatureCluster', 'mcr.mcr_signature_cluster.SignatureCluster')

# === PIPELINE UNIVERSAL ===
_reg.registrar('PipelineUniversal', 'mcr.pipeline_universal.PipelineUniversal')

# === EMERGIR ===
_reg.registrar('EmergirCrossModal', 'mcr.emergir_crossmodal.EmergirCrossModal')
_reg.registrar('MCRConexao', 'mcr_universal.emergence.conexao.MCRConexao')

# === SYSTEM ===
_reg.registrar('MCRPergunta', 'mcr.system.MCRPergunta')
_reg.registrar('MCRGeracao', 'mcr.system.MCRGeracao')

# === VISUAL COUPLING ===
_reg.registrar('VisualCoupling', 'mcr.visual_coupling.VisualCoupling')

# === CIELAB ===
_reg.registrar('rgb_para_lab', 'mcr.cielab.rgb_para_lab', ['r', 'g', 'b'])
_reg.registrar('lab_para_rgb', 'mcr.cielab.lab_para_rgb', ['L', 'a', 'b'])
_reg.registrar('delta_e76', 'mcr.cielab.delta_e76', ['c1', 'c2'])

# === TOOLREGISTRY TOOLS ===
_reg.registrar('ToolRegistry', 'mcr.knowledge.tool_registry.ToolRegistry')
_reg.registrar('KnowledgeGraph', 'mcr.knowledge.kg.KnowledgeGraph')
_reg.registrar('NPCGenerator', 'devia.modules.npc_generator.NPCGenerator')
_reg.registrar('LuaValidator', 'mcr.lua_validator.LuaValidator')
_reg.registrar('SanityValidator', 'mcr.sanity_validator.SanityValidator')

# === HDC/SDM ===
_reg.registrar('hdc_core', 'devia.kernel.hdc_core.HDVector')
_reg.registrar('sdm_core', 'devia.kernel.sdm_core.SDM')

# === FINGERPRINT ===
_reg.registrar('fingerprint_8d', 'mcr_universal.core.signature.MCRSignatureExpansiva.fingerprint', ['dados', 'n_dims'])
_reg.registrar('dimensionalidade_ideal', 'mcr_universal.core.signature.MCRSignatureExpansiva.dimensionalidade_ideal', ['dados'])

# === OLHOS ===
_reg.registrar('sprite_para_ascii', 'mcr.sprite_corpus.sprite_para_ascii', ['grid_papel'])

# === SQLITEMARKOV (N-adaptativo, identity-aware) ===
_reg.registrar('SQLiteMarkov', 'mcr.sqlite_markov.SQLiteMarkov', ['db_path', 'n_max'])
_reg.registrar('SQLiteMarkov.alimentar', 'mcr.sqlite_markov.SQLiteMarkov.alimentar', ['identity', 'tokens'])
_reg.registrar('SQLiteMarkov.gerar_com_identidade', 'mcr.sqlite_markov.SQLiteMarkov.gerar_com_identidade', ['identity', 'seed', 'passos'])
_reg.registrar('SQLiteMarkov.predizer_adaptativo', 'mcr.sqlite_markov.SQLiteMarkov.predizer_adaptativo', ['identity', 'contexto'])

# === PIPELINE CONECTADO (orquestrador) ===
_reg.registrar('PipelineConectado', 'mcr.adaptadores.PipelineConectado')
_reg.registrar('acoes_para_tarefas', 'mcr.adaptadores.acoes_para_tarefas', ['acoes', 'entrada', 'contexto'])
_reg.registrar('intencao_para_classe', 'mcr.adaptadores.intencao_para_classe', ['intencoes'])

# === CRIATIVIDADE / MENTE (P1 + P2) ===
_reg.registrar('EmergirUnificado', 'mcr.emergir_unificado.EmergirUnificado')
_reg.registrar('GeradorCodigo', 'mcr.gerador_codigo.GeradorCodigo')
_reg.registrar('NPCCriativo', 'mcr.npc_criativo.NPCCriativo')
_reg.registrar('Raciocinador', 'mcr.raciocinador.Raciocinador')
_reg.registrar('MCRMentePura', 'mcr.mcr_mente_pura.MCRMentePura')
_reg.registrar('MCRMente', 'mcr.mcr_mente.MCRMente')
_reg.registrar('MCRUnificado', 'mcr.mcr_unificado.MCRUnificado')
_reg.registrar('Metacognicao', 'mcr.metacognicao.Metacognicao')
_reg.registrar('MCRAutoEvolution', 'mcr.mcr_auto_evolution.MCRAutoEvolution')
_reg.registrar('HDCKGMemory', 'mcr.hdc_kg_memory.HDCKGMemory')
_reg.registrar('CacheHierarquico', 'mcr.cache_hierarquico.CacheHierarquico')
_reg.registrar('AutoCuriosidade', 'mcr.auto_curiosidade.AutoCuriosidade')
_reg.registrar('MCRWorldSystem', 'mcr.mcr_world_system.MCRWorldSystem')
_reg.registrar('DialogueTrainer', 'mcr.dialogue_trainer.DialogueTrainer')
_reg.registrar('Planejador', 'mcr.planejador.Planejador')
_reg.registrar('Emergir', 'mcr.emergir.Emergir')
_reg.registrar('InternalMonologue', 'mcr.internal_monologue.InternalMonologue')
_reg.registrar('MCRSelf', 'mcr.mcr_self.MCRSelf')
_reg.registrar('Autobiography', 'mcr.mcr_autobiography.Autobiography')
_reg.registrar('Conversa', 'mcr.mcr_conversa.Conversa')

# === KERNEL (P3) ===
_reg.registrar('MCRWorker', 'mcr.evolution.MCRWorker')
_reg.registrar('MCRSystem', 'mcr.system.MCRSystem')
_reg.registrar('MCRMestreV2', 'mcr.system.MCRMestreV2')
_reg.registrar('MCRFeedback', 'mcr.feedback.MCRFeedback')
_reg.registrar('MCRSession', 'mcr.feedback.MCRSession')
_reg.registrar('MCRFilosofia', 'mcr.feedback.MCRFilosofia')

# === GERADOR MULTINIVEL ===
_reg.registrar('GeradorMultinivel', 'mcr.generator_multinivel.GeradorMultinivel')

# === DEVIA/MODULES (high-value) ===
_reg.registrar('IntentionEngine', 'devia.modules.intention_engine.IntentionEngine')
_reg.registrar('EmergirEngine', 'devia.modules.emergir.EmergirEngine')
_reg.registrar('EpisodicMemory', 'devia.modules.episodic_memory.EpisodicMemory')
_reg.registrar('PatternEngine', 'devia.modules.pattern_engine.PatternEngine')
_reg.registrar('ToolOrchestrator', 'devia.modules.tool_orchestrator.ToolOrchestrator')
_reg.registrar('MasterAgent', 'devia.modules.master_agent.MasterAgent')
_reg.registrar('TaskPlanner', 'devia.modules.task_planner.TaskPlanner')
_reg.registrar('Orquestrador', 'devia.modules.orquestrador.Orquestrador')
_reg.registrar('TaskExecutor', 'devia.modules.task_executor.TaskExecutor')
_reg.registrar('ValidationPipeline', 'devia.modules.validation_pipeline.ValidationPipeline')
_reg.registrar('CanaryIndexer', 'devia.modules.canary_indexer.CanaryIndexer')
_reg.registrar('AutoRevisor', 'devia.modules.auto_revisor.AutoRevisor')
_reg.registrar('SelfStudyEngine', 'devia.modules.self_study.SelfStudyEngine')
_reg.registrar('Supervisor', 'devia.modules.supervisor.Supervisor')
_reg.registrar('PosProcessamento', 'devia.modules.pos_processamento.PosProcessamento')
_reg.registrar('SandboxExecutor', 'devia.modules.sandbox_executor.SandboxExecutor')
_reg.registrar('Conselho', 'devia.modules.conselho.Conselho')
_reg.registrar('ContextEnricher', 'devia.modules.context_enricher.ContextEnricher')

# === MCR/ — alto valor restante ===
_reg.registrar('Ensemble7B', 'mcr.ensemble_7b.Ensemble7B')
_reg.registrar('NPCServer', 'mcr.npc_server.NPCServer')
_reg.registrar('HybridRouter', 'mcr.hybrid_router.HybridRouter')
_reg.registrar('PipelineCompleto', 'mcr.pipeline_completo.PipelineCompleto')
_reg.registrar('WorldAnomalyDetector', 'mcr.world_anomaly_detector.WorldAnomalyDetector')
_reg.registrar('WorldObserver', 'mcr.world_observer.WorldObserver')

# === KERNEL — alto valor restante ===
_reg.registrar('MCRBridge', 'mcr.engine.MCRBridge')
_reg.registrar('MCRAssinatura', 'mcr.feedback.MCRAssinatura')
_reg.registrar('GeradorNarrativa', 'mcr.system.GeradorNarrativa')
_reg.registrar('AutoavaliadorSemantico', 'mcr.system.AutoavaliadorSemantico')
_reg.registrar('MCRMestre', 'mcr.system.MCRMestre')
_reg.registrar('MCRExpansao', 'mcr.evolution.MCRExpansao')
_reg.registrar('MCRPersistencia', 'mcr.persistence.MCRPersistencia')

# === MCR/ — TODOS os restantes ===
_reg.registrar('ChainOfVerification', 'mcr.chain_of_verification.ChainOfVerification')
_reg.registrar('DataInjector', 'mcr.data_injector.DataInjector')
_reg.registrar('InnerVoice', 'mcr.mcr_inner_voice.InnerVoice')
_reg.registrar('LogWatcherBridge', 'mcr.logwatcher_bridge.LogWatcherBridge')
_reg.registrar('BridgeAPI', 'mcr.bridge_api.BridgeAPI')
_reg.registrar('SanityValidatorSQL', 'mcr.sanity_validator_sql.SanityValidatorSQL')
_reg.registrar('SanityValidatorCS', 'mcr.sanity_validator_cs.SanityValidatorCS')
_reg.registrar('SanityValidatorCpp', 'mcr.sanity_validator_cpp.SanityValidatorCpp')
_reg.registrar('ShadowDotnet', 'mcr.shadow_dotnet.ShadowDotnet')
_reg.registrar('SpriteExtractor', 'mcr.sprite_extractor.SpriteExtractor')

# === MCR_KERNEL — infraestrutura ===
_reg.registrar('MCRTarefa', 'mcr.evolution.MCRTarefa')
_reg.registrar('MCRSpawner', 'mcr.evolution.MCRSpawner')
_reg.registrar('MCRWebLearn', 'mcr.feedback.MCRWebLearn')

# === DEVIA/KERNEL — utilitarios standalone ===
_reg.registrar('HDCVocab', 'devia.kernel.hdc_core.HDCVocab')
_reg.registrar('MarkovRouter', 'devia.kernel.MarkovRouter.MarkovRouter')
_reg.registrar('SDM_MDL', 'devia.kernel.sdm_core.SDM_MDL')
_reg.registrar('CodeParser', 'devia.kernel.code_parser.CodeParser')
_reg.registrar('AutorevisaoTracker', 'devia.kernel.AutorevisaoTracker.AutorevisaoTracker')
_reg.registrar('FeedbackFilter', 'devia.kernel.FeedbackFilter.FeedbackFilter')
_reg.registrar('LogWatcher', 'devia.kernel.log_watcher.LogWatcher')
_reg.registrar('MCRRAG', 'devia.kernel.rag_mcr.MCRRAG')
_reg.registrar('WatchdogMCR', 'devia.kernel.watchdog_mcr.WatchdogMCR')
_reg.registrar('RedeNPCs', 'devia.kernel.rede_npcs.RedeNPCs')
_reg.registrar('MCRDevIARevived', 'devia.kernel.fix_mcr_devia_v2.MCRDevIARevived')
_reg.registrar('MCRDevIAV2', 'mcr.coupling.MCRDevIAV2')
_reg.registrar('MarkovDecider', 'mcr.coupling.MarkovDecider')
_reg.registrar('EntropyValidator', 'mcr.coupling.EntropyValidator')
_reg.registrar('MCRNPCv2', 'devia.kernel.npc_vivo.MCRNPCv2')
_reg.registrar('PercepcaoNPC', 'devia.kernel.percepcao.PercepcaoNPC')
_reg.registrar('Radar', 'devia.kernel.Radar.Radar')
_reg.registrar('PipelineExecutor', 'devia.kernel.PipelineExecutor.PipelineExecutor')

# === DEVIA/MODULES — componentes de pipeline ===
_reg.registrar('PipelineExecutor_module', 'devia.modules.pipeline_executor.PipelineExecutor')
_reg.registrar('LuaValidator_module', 'devia.modules.lua_validator.LuaValidator')
_reg.registrar('KnowledgeGraph_module', 'devia.modules.kg.KnowledgeGraph')


def get_registry():
    return _reg


# ─── Utilitario para testar um token ──────────────────────


def testar_token(token, **kwargs):
    """Testa se um token pode ser executado."""
    try:
        resultado = _reg.executar(token, **kwargs)
        return True, resultado
    except Exception as e:
        return False, str(e)


def validar_todos():
    """Valida todos os tokens registrados."""
    resultados = {'ok': [], 'erro': [], 'pulados': []}
    for token in _reg.listar_tokens():
        try:
            entry = _reg._registro[token]
            fn_path = entry['fn_path']
            fn = _resolver(fn_path)
            if fn is None:
                resultados['erro'].append((token, 'nao_resolvido'))
            else:
                resultados['ok'].append((token, fn_path))
        except Exception as e:
            resultados['erro'].append((token, str(e)[:50]))
    return resultados
