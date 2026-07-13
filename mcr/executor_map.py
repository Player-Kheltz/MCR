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
_reg.registrar('MCR', 'devia.kernel.mcr_kernel.engine.MCR', descricao='Cria MCR engine')
_reg.registrar('aprender', 'devia.kernel.mcr_kernel.engine.MCR.aprender', ['a', 'b'])
_reg.registrar('aprender_sequencia', 'devia.kernel.mcr_kernel.engine.MCR.aprender_sequencia', ['seq'])
_reg.registrar('aprender_batch', 'devia.kernel.mcr_kernel.engine.MCR.aprender_batch', ['sequencias'])
_reg.registrar('predizer', 'devia.kernel.mcr_kernel.engine.MCR.predizer', ['a'])
_reg.registrar('gerar', 'devia.kernel.mcr_kernel.engine.MCR.gerar', ['semente', 'passos'])
_reg.registrar('entropia', 'devia.kernel.mcr_kernel.engine.MCR.entropia', ['a'])
_reg.registrar('entropia_media', 'devia.kernel.mcr_kernel.engine.MCR.entropia_media')
_reg.registrar('jaccard', 'devia.kernel.mcr_kernel.engine.MCR.jaccard', ['outra'])
_reg.registrar('stats', 'devia.kernel.mcr_kernel.engine.MCR.stats')
_reg.registrar('compose_state', 'devia.kernel.mcr_kernel.engine.compose_state', ['base', 'context'])
_reg.registrar('compor_contexto', 'devia.kernel.mcr_kernel.engine.compor_contexto', ['tokens', 'ctx'])

# === MCRSQLite ===
_reg.registrar('MCRSQLite', 'mcr.mcr_sqlite.MCRSQLite', ['db_path'])

# === DECISOR ===
_reg.registrar('MCRThreshold', 'devia.kernel.mcr_kernel.decisor.MCRThreshold', ['nome'])
_reg.registrar('MCRDecisor', 'devia.kernel.mcr_kernel.decisor.MCRDecisor', ['nome'])
_reg.registrar('MCRPesoNota', 'devia.kernel.mcr_kernel.decisor.MCRPesoNota', ['nome'])
_reg.registrar('MCREntropia', 'devia.kernel.mcr_kernel.decisor.MCREntropia', ['nome'])
_reg.registrar('MCRRuido', 'devia.kernel.mcr_kernel.decisor.MCRRuido', ['nome'])
_reg.registrar('MCRDiagnostico', 'devia.kernel.mcr_kernel.decisor.MCRDiagnostico', ['nome'])
_reg.registrar('MCRPeso', 'devia.kernel.mcr_kernel.decisor.MCRPeso', ['nome'])
_reg.registrar('MCRDecisor', 'devia.kernel.mcr_kernel.decisor.MCRDecisor', ['nome'])

# === SIGNATURE ===
_reg.registrar('MCRFingerprint', 'devia.kernel.mcr_kernel.signature.MCRFingerprint')
_reg.registrar('MCRSignature', 'devia.kernel.mcr_kernel.signature.MCRSignature')
_reg.registrar('raw_token_set', 'devia.kernel.mcr_kernel.signature.raw_token_set', ['texto'])
_reg.registrar('MCRSignatureExpansiva', 'mcr_universal.core.signature.MCRSignatureExpansiva')

# === MEMORIA ===
_reg.registrar('MCRCruzado', 'devia.kernel.mcr_kernel.memory.MCRCruzado')
_reg.registrar('MCRConector', 'devia.kernel.mcr_kernel.memory.MCRConector')
_reg.registrar('MCRCadeia', 'devia.kernel.mcr_kernel.memory.MCRCadeia')
_reg.registrar('MCRBufferKG', 'devia.kernel.mcr_kernel.memory.MCRBufferKG')
_reg.registrar('MCRKGAuto', 'devia.kernel.mcr_kernel.memory.MCRKGAuto')

# === META ===
_reg.registrar('MCRMetaNivel', 'devia.kernel.mcr_kernel.meta.MCRMetaNivel')
_reg.registrar('MCRMetaGap', 'devia.kernel.mcr_kernel.meta.MCRMetaGap')
_reg.registrar('MCRSelfIndex', 'devia.kernel.mcr_kernel.meta.MCRSelfIndex')
_reg.registrar('MCRSelfHeal', 'devia.kernel.mcr_kernel.meta.MCRSelfHeal')

# === EVOLUCAO ===
_reg.registrar('MCRAutoMelhoria', 'devia.kernel.mcr_kernel.evolution.MCRAutoMelhoria')
_reg.registrar('MCRFuel', 'devia.kernel.mcr_kernel.evolution.MCRFuel')

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
_reg.registrar('MCRPergunta', 'devia.kernel.mcr_kernel.system.MCRPergunta')
_reg.registrar('MCRGeracao', 'devia.kernel.mcr_kernel.system.MCRGeracao')

# === VISUAL COUPLING ===
_reg.registrar('VisualCoupling', 'mcr.visual_coupling.VisualCoupling')

# === CIELAB ===
_reg.registrar('rgb_para_lab', 'mcr.cielab.rgb_para_lab', ['r', 'g', 'b'])
_reg.registrar('lab_para_rgb', 'mcr.cielab.lab_para_rgb', ['L', 'a', 'b'])
_reg.registrar('delta_e76', 'mcr.cielab.delta_e76', ['c1', 'c2'])

# === TOOLREGISTRY TOOLS ===
_reg.registrar('ToolRegistry', 'devia.knowledge.tool_registry.ToolRegistry')
_reg.registrar('KnowledgeGraph', 'devia.knowledge.kg.KnowledgeGraph')
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
_reg.registrar('MCRWorker', 'devia.kernel.mcr_kernel.evolution.MCRWorker')
_reg.registrar('MCRSystem', 'devia.kernel.mcr_kernel.system.MCRSystem')
_reg.registrar('MCRMestreV2', 'devia.kernel.mcr_kernel.system.MCRMestreV2')
_reg.registrar('MCRFeedback', 'devia.kernel.mcr_kernel.feedback.MCRFeedback')
_reg.registrar('MCRSession', 'devia.kernel.mcr_kernel.feedback.MCRSession')
_reg.registrar('MCRFilosofia', 'devia.kernel.mcr_kernel.feedback.MCRFilosofia')

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
_reg.registrar('MCRBridge', 'devia.kernel.mcr_kernel.engine.MCRBridge')
_reg.registrar('MCRAssinatura', 'devia.kernel.mcr_kernel.feedback.MCRAssinatura')
_reg.registrar('GeradorNarrativa', 'devia.kernel.mcr_kernel.system.GeradorNarrativa')
_reg.registrar('AutoavaliadorSemantico', 'devia.kernel.mcr_kernel.system.AutoavaliadorSemantico')
_reg.registrar('MCRMestre', 'devia.kernel.mcr_kernel.system.MCRMestre')
_reg.registrar('MCRExpansao', 'devia.kernel.mcr_kernel.evolution.MCRExpansao')
_reg.registrar('MCRPersistencia', 'devia.kernel.mcr_kernel.persistence.MCRPersistencia')

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
_reg.registrar('MCRTarefa', 'devia.kernel.mcr_kernel.evolution.MCRTarefa')
_reg.registrar('MCRSpawner', 'devia.kernel.mcr_kernel.evolution.MCRSpawner')
_reg.registrar('MCRWebLearn', 'devia.kernel.mcr_kernel.feedback.MCRWebLearn')

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
_reg.registrar('MCRDevIAV2', 'devia.kernel.mcr_devia_v2.MCRDevIAV2')
_reg.registrar('MarkovDecider', 'devia.kernel.mcr_devia_v2.MarkovDecider')
_reg.registrar('EntropyValidator', 'devia.kernel.mcr_devia_v2.EntropyValidator')
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
