"""modulos.validation_pipeline — Redireciona para mcr.chain_of_verification."""
try:
    from mcr.chain_of_verification import ChainOfVerification as ValidationPipeline
except ImportError:
    class ValidationPipeline:
        def __init__(self, *a, **kw): pass
        def validar(self, *a, **kw): return {'valido': False}
