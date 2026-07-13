"""MCR.py — Re-export wrapper para devia.kernel.mcr_kernel.

Este arquivo existe para compatibilidade com código legado que faz
`from MCR import MCRFingerprint, MCRByteUtils, etc.` via sys.path.
"""
try:
    from devia.kernel.mcr_kernel import *
    from devia.kernel.mcr_kernel.engine import MCR, MCRBridge
    from devia.kernel.mcr_kernel.signature import MCRFingerprint, MCRSignature, raw_token_set
    from devia.kernel.mcr_kernel.decisor import MCRPesoNota, MCREntropia, MCRRuido
    from devia.kernel.mcr_kernel.meta import MCRSelfHeal
    from devia.kernel.mcr_kernel.system import MCRPergunta, MCRGeracao
    from devia.kernel.mcr_kernel.evolution import MCRTarefa, MCRSpawner, MCRFuel, MCRAutoMelhoria, MCRExpansao
    from devia.kernel.mcr_kernel.memory import MCRConector, MCRCadeia
except ImportError:
    pass

class MCRByteUtils:
    @staticmethod
    def fingerprint(texto, dim=16):
        from mcr_kernel.signature import MCRFingerprint
        fp = MCRFingerprint.gerar(texto)
        return (fp * (dim // 8 + 1))[:dim]
    @staticmethod
    def similaridade_cosseno(a, b):
        dot = sum(x*y for x,y in zip(a,b))
        na = sum(x*x for x in a)**0.5
        nb = sum(y*y for y in b)**0.5
        return dot/(na*nb) if na*nb else 0
