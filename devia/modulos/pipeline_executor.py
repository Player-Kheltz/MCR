"""modulos.pipeline_executor — Redireciona para mcr.adaptadores."""
try:
    from mcr.adaptadores import PipelineConectado
except ImportError:
    PipelineConectado = None
