"""mcr.bootstrap — Registra todas as tools no registry no boot.

Scaneia o projeto, encontra módulos, e popula o MCRRegistry.
Não usa if/elif — usa varredura + metadados.
"""
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mcr.registry import get_registry, MCRRegistry

# ─── Mapeamento domínio → padrão de import ─────────────────
# Cada domínio sabe quais paths scannear
_DOMINIOS = {
    # ─── Núcleo Markoviano ──────────────────────────────
    'motor': [
        'mcr.motor.engine',
        'mcr.motor.signature',
    ],
    # ─── Equação ────────────────────────────────────────
    'equacao': [
        'mcr.equacao.equacao_mcr',
    ],
    'kernel': [
        'mcr.engine',
        'mcr.decisor',
        'mcr.signature',
        'mcr.memory',
        'mcr.meta',
        'mcr.evolution',
        'mcr.feedback',
        'mcr.persistence',
        'mcr.state',
        'mcr.system',
    ],
    'modules': [
        'devia.modules.master_agent',
        'devia.modules.supervisor',
        'devia.modules.orquestrador',
        'devia.modules.task_planner',
        'devia.modules.task_executor',
        'devia.modules.intention_engine',
        'devia.modules.episodic_memory',
        'devia.modules.pattern_engine',
        'devia.modules.context_enricher',
        'devia.modules.validation_pipeline',
        'devia.modules.auto_revisor',
        'devia.modules.self_study',
        'devia.modules.pos_processamento',
        'devia.modules.sandbox_executor',
        'devia.modules.conselho',
    ],
    'mcr_core': [
        'mcr.mcr_mente_pura',
        'mcr.mcr_mente',
        'mcr.mcr_self',
        'mcr.internal_monologue',
        'mcr.mcr_autobiography',
        'mcr.mcr_conversa',
    ],
    'mcr_criativo': [
        'mcr.emergir_unificado',
        'mcr.gerador_codigo',
        'mcr.npc_criativo',
        'mcr.raciocinador',
        'mcr.generator_multinivel',
        'mcr.emergir',
    ],
    'mcr_world': [
        'mcr.mcr_world_system',
        'mcr.dialogue_trainer',
        'mcr.planejador',
        'mcr.auto_curiosidade',
    ],
    'mcr_infra': [
        'mcr.hybrid_router',
        'mcr.chain_of_verification',
        'mcr.cache_hierarquico',
        'mcr.metacognicao',
        'mcr.mcr_auto_evolution',
        'mcr.hdc_kg_memory',
        'mcr.bridge_api',
        'mcr.sse_server',
    ],
    'mcr_sprite': [
        'mcr.sprite_corpus',
        'mcr.mcr_sprite_motor',
        'mcr.mcr_sprite_universal',
        'mcr.olhos_mcr',
        'mcr.meus_olhos',
        'mcr.mcr_radar',
        'mcr.mcr_signature_cluster',
        'mcr.visual_coupling',
        'mcr.cielab',
        'mcr.template_entropico',
        'mcr.tokenizador_hierarquico',
        'mcr.regioes_anatomicas',
    ],
    'kernel_misc': [
        'devia.kernel.MarkovRouter',
        'devia.kernel.hdc_core',
        'devia.kernel.sdm_core',
        'devia.kernel.code_parser',
        'devia.kernel.log_watcher',
        'devia.kernel.rag_mcr',
        'devia.kernel.watchdog_mcr',
        'devia.kernel.rede_npcs',
        'devia.kernel.percepcao',
        'devia.kernel.Radar',
    ],
}


def _scan_module(mod_name: str, dominio: str) -> List[Tuple[str, object, dict]]:
    """Scanneia um módulo e retorna (nome, callable, meta) de classes/funções."""
    entries = []
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return entries

    # Nomes que não são tools reais
    _NOISE = {
        'Any', 'Dict', 'List', 'Optional', 'Tuple', 'Set', 'Union',
        'Callable', 'Type', 'Sequence', 'Mapping', 'Iterable',
        'os', 'sys', 're', 'time', 'json', 'math', 'hashlib',
        'Path', 'PathLike', 'Counter', 'defaultdict',
        'print', 'len', 'str', 'int', 'float', 'bool', 'type',
        'super', 'property', 'staticmethod', 'classmethod',
    }

    for nome_attr in dir(mod):
        if nome_attr in _NOISE or nome_attr.startswith('_'):
            continue
        obj = getattr(mod, nome_attr, None)
        if obj is None:
            continue
        if inspect.isclass(obj) and obj.__module__ == mod_name:
            meta = {
                'dominio': dominio,
                'descricao': (obj.__doc__ or '').strip().split('\n')[0][:100],
                'tipo': 'classe',
            }
            entries.append((nome_attr, obj, meta))
        elif callable(obj):
            meta = {
                'dominio': dominio,
                'descricao': (getattr(obj, '__doc__', '') or '').strip().split('\n')[0][:100],
                'tipo': 'funcao',
            }
            entries.append((nome_attr, obj, meta))

    return entries


def bootstrap(registry: MCRRegistry = None) -> MCRRegistry:
    """Registra todas as tools disponíveis no registry.

    Returns:
        MCRRegistry populado com todas as tools descobertas.
    """
    if registry is None:
        registry = get_registry()

    total = 0
    for dominio, modulos in _DOMINIOS.items():
        for mod_name in modulos:
            entries = _scan_module(mod_name, dominio)
            for nome, fn, meta in entries:
                if registry.selecionar(nome) is None:
                    try:
                        params = list(inspect.signature(fn).parameters.keys())
                    except Exception:
                        params = []
                    registry.registrar(
                        nome=nome,
                        fn=fn,
                        params=params,
                        dominio=dominio,
                        nivel=0,
                        descricao=meta.get('descricao', ''),
                        meta=meta,
                    )
                    total += 1

    # Tenta carregar registry salvo (metadados de uso anterior)
    registry.carregar()

    return registry


def bootstrap_desde_executor(registry: MCRRegistry = None) -> MCRRegistry:
    """Migra tokens do executor_map antigo para o novo registry.

    Usa o mapeamento token → fn_path para importar e registrar.
    """
    if registry is None:
        registry = get_registry()

    try:
        from mcr.executor_map import get_registry as get_old_registry
        old = get_old_registry()
    except Exception:
        return registry

    for token in old.listar_tokens():
        entry = old._registro.get(token)
        if not entry:
            continue
        if registry.selecionar(token) is not None:
            continue

        fn_path = entry.get('fn_path', '')
        params = entry.get('params', [])
        descricao = entry.get('descricao', '')

        # Tenta resolver o fn_path
        fn = _resolver_path(fn_path)
        if fn is None:
            continue

        dominio = fn_path.split('.')[0] if '.' in fn_path else 'migrado'
        registry.registrar(
            nome=token,
            fn=fn,
            params=params,
            dominio=dominio,
            nivel=1,
            descricao=descricao,
            meta={'migrado_de': 'executor_map', 'fn_path': fn_path},
        )

    return registry


def _resolver_path(fn_path: str):
    """Resolve 'modulo.submodulo.funcao' para callable."""
    import importlib
    partes = fn_path.split('.')
    for i in range(len(partes), 0, -1):
        module_name = '.'.join(partes[:i])
        attrs = partes[i:]
        try:
            mod = importlib.import_module(module_name)
            obj = mod
            for attr in attrs:
                obj = getattr(obj, attr)
            return obj
        except Exception:
            continue
    return None


def inicializar(registry: MCRRegistry = None) -> MCRRegistry:
    """Ponto de entrada completo: bootstrap + migração + persistência.

    Chame uma vez no startup do sistema.
    """
    if registry is None:
        registry = get_registry()

    bootstrap(registry)
    bootstrap_desde_executor(registry)
    registry.salvar()

    return registry
