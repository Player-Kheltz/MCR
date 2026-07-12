#!/usr/bin/env python3
"""
mcr.executor_map — Mapeia tokens do navegador MCR para funcoes Python reais.

Cada entrada: token → {fn, params, retorno, dependencias}
O executor_dinamico.py usa este mapa para executar QUALQUER token.
"""
import sys
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')


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
_reg.registrar('MCRSpriteConector', 'mcr.mcr_conector_sprite.MCRSpriteConector')

# === OIHOS MCR ===
_reg.registrar('sprite_para_ascii_rich', 'mcr.olhos_mcr.sprite_para_ascii_rich', ['grid_papel', 'grid_cor'])
_reg.registrar('sprite_para_ascii_compacto', 'mcr.olhos_mcr.sprite_para_ascii_compacto', ['grid_papel', 'grid_cor'])

# === VALIDACAO ===
_reg.registrar('MCRDiscriminador', 'mcr.meus_olhos.MCRDiscriminador')
_reg.registrar('RadarMCR', 'mcr.mcr_radar.RadarMCR')

# === SIGNATURE CLUSTER ===
_reg.registrar('SignatureAnalyzer', 'mcr.mcr_signature_cluster.SignatureAnalyzer')
_reg.registrar('SignatureCluster', 'mcr.mcr_signature_cluster.SignatureCluster')

# === RAW MINER ===
_reg.registrar('raw_miner.computar_raw_fingerprints', 'mcr.raw_miner.computar_raw_fingerprints', ['clusters'])
_reg.registrar('raw_miner.classificar_sem_parser', 'mcr.raw_miner.classificar_sem_parser', ['arquivo', 'clusters'])

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
